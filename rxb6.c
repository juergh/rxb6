/*
 * A simple kernel module that measures pulse widths from an RXB6 RF receiver.
 *
 * Copyright (C) 2018 Juerg Haefliger <juergh@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License version 2 as published by
 * the Free Software Foundation.
 */

#include <linux/device.h>
#include <linux/fs.h>
#include <linux/gpio.h>
#include <linux/interrupt.h>
#include <linux/kfifo.h>
#include <linux/module.h>
#include <linux/uaccess.h>
#include <linux/sched/clock.h>

#define DEVNAME			"rxb6"

#undef pr_fmt
#define pr_fmt(fmt)		DEVNAME ": " fmt

#define GPIO_PIN 		6

#define PULSE_MIN_LEN		500
#define SYNC_PULSE_MIN_LEN	8000
#define SYNC_PULSE_MAX_LEN	10000
#define END_PULSE_MIN_LEN       10000

static int rxb6_major;
static struct class *rxb6_class = NULL;
static struct device *rxb6_dev = NULL;

DEFINE_KFIFO(rxb6_fifo, char, 128);
DECLARE_WAIT_QUEUE_HEAD(rxb6_fifo_wq);
static atomic_t rxb6_available = ATOMIC_INIT(1);

static void vprintk_fifo(u64 ts, const char *fmt, ...)
{
	va_list args;
	char buf[64];
	int len;

	/* Prefix the line with the timestamp */
	len = snprintf(buf, sizeof(buf), "%llu ", ts);

	va_start(args, fmt);
	len += vsnprintf(buf + len, sizeof(buf) - len, fmt, args);
	va_end(args);

	/* Put the data into the FIFO and wake up the reader */
	kfifo_in(&rxb6_fifo, buf, len);
	wake_up_interruptible(&rxb6_fifo_wq);
}

static irqreturn_t rxb6_irq_handler(int irq, void *data)
{
	static u64 prev_usec = 0;
	static bool record = false;
	static int prev_val = -1;
	u64 now_usec;
	u64 pulse_len;
	int now_val;

	/* Runtime since boot in microseconds */
	now_usec = local_clock();
	do_div(now_usec, 1000);

	/* First time init */
	if (unlikely(!prev_usec)) {
		goto out;
	}

	/* The length of the pulse in microseconds */
	pulse_len = now_usec - prev_usec;

	/* Ignore short pulses and abort recording */
	if (pulse_len < PULSE_MIN_LEN) {
		if (record) {
			record = false;
			vprintk_fifo(now_usec, "ERR_LEN\n");
		}
		goto out;
	}

	/* Start recording if this is a sync pulse */
	if (pulse_len < SYNC_PULSE_MAX_LEN &&
	    pulse_len > SYNC_PULSE_MIN_LEN) {
		record = true;
		prev_val = -1;
		vprintk_fifo(now_usec, "SYNC\n");
	}

	if (record) {
		now_val = gpio_get_value(GPIO_PIN) & 1;

		/* Record the data */
		vprintk_fifo(now_usec, "%u %llu\n", now_val, pulse_len);

		/* Stop recording if this is an end pulse */
		if (pulse_len > END_PULSE_MIN_LEN) {
			record = false;
			vprintk_fifo(now_usec, "END\n");
		}

		/* Abort recording if the level didn't toggle */
		if (now_val == prev_val) {
			record = false;
			vprintk_fifo(now_usec, "ERR_LEVEL\n");
		}

		prev_val = now_val;
	}

out:
	prev_usec = now_usec;
	return IRQ_HANDLED;
}

static int rxb6_open(struct inode *inode, struct file *file)
{
	/* Check if the device is already opened */
	if (!atomic_dec_and_test(&rxb6_available)) {
		atomic_set(&rxb6_available, 0);
		return -EBUSY;
	}

	/* Reset the FIFO */
	kfifo_reset(&rxb6_fifo);

	/* Register our interrupt handler */
	if (request_irq(gpio_to_irq(GPIO_PIN), rxb6_irq_handler, IRQF_SHARED |
			IRQF_TRIGGER_RISING | IRQF_TRIGGER_FALLING,
			DEVNAME, &rxb6_dev)) {
		pr_err("Failed to request IRQ for GPIO %d\n", GPIO_PIN);
		return -EIO;
	}

	return 0;
}

static int rxb6_release(struct inode *inode,  struct file *file)
{
	free_irq(gpio_to_irq(GPIO_PIN), &rxb6_dev);
	atomic_set(&rxb6_available, 1);

	return 0;
}

static ssize_t rxb6_read(struct file *file, char __user *buf, size_t count,
			 loff_t *ppos)
{
	int err;
	unsigned int copied;

	/* Wait for new FIFO data */
	if (wait_event_interruptible(rxb6_fifo_wq,
				     !kfifo_is_empty(&rxb6_fifo))) {
		return -ERESTARTSYS;
	}

	/* Copy the FIFO data to userspace */
	err = kfifo_to_user(&rxb6_fifo, buf, count, &copied);

	return err ? err : copied;
}

static struct file_operations rxb6_fops =
{
	.owner          = THIS_MODULE,
	.open           = rxb6_open,
	.release        = rxb6_release,
	.read           = rxb6_read,
};

static int __init rxb6_init (void)
{
	int err = 0;

	rxb6_major = register_chrdev(0, DEVNAME, &rxb6_fops);
	if (rxb6_major < 0){
		pr_err("Failed to register device\n");
		return rxb6_major;
	}

	rxb6_class = class_create(THIS_MODULE, DEVNAME);
	if (IS_ERR(rxb6_class)) {
		pr_err("Failed to create device class\n");
		err = PTR_ERR(rxb6_class);
		goto err_unregister_chrdev;
	}

	rxb6_dev = device_create(rxb6_class, NULL, MKDEV(rxb6_major, 0), NULL,
				 DEVNAME);
	if (IS_ERR(rxb6_dev)) {
		pr_err("Failed to create device\n");
		err = PTR_ERR(rxb6_dev);
		goto err_class_destroy;
	}

	err = gpio_request(GPIO_PIN, DEVNAME);
	if (err) {
		pr_err("Failed to reserve GPIO %d\n", GPIO_PIN);
		goto err_device_destroy;
	}

	err = gpio_direction_input(GPIO_PIN);
	if (err) {
		pr_err("Failed to set GPIO %d as input\n", GPIO_PIN);
		goto err_gpio_free;
	}

	return 0;

err_gpio_free:
	gpio_free(GPIO_PIN);
err_device_destroy:
	device_destroy(rxb6_class, MKDEV(rxb6_major, 0));
err_class_destroy:
	class_destroy(rxb6_class);
err_unregister_chrdev:
	unregister_chrdev(rxb6_major, DEVNAME);
	return err;
}

static void __exit rxb6_exit (void)
{
	gpio_free(GPIO_PIN);
	device_destroy(rxb6_class, MKDEV(rxb6_major, 0));
	class_destroy(rxb6_class);
	unregister_chrdev(rxb6_major, DEVNAME);
}

module_init(rxb6_init);
module_exit(rxb6_exit);

MODULE_AUTHOR("Juerg Haefliger <juergh@gmail.com>");
MODULE_DESCRIPTION("RXB6 RF Receiver");
MODULE_LICENSE("GPL");
