kernel ?= $(shell uname -r)
kdir ?= /lib/modules/$(kernel)/build

obj-m = rxb6.o

rxb6.ko: rxb6.c
	$(MAKE) -C $(kdir) M=$$(pwd)

clean:
	rm -f rxb6.o rxb6.ko

unload:
	rmmod rxb6

load:
	insmod ./rxb6.ko
	sleep 1
	chmod 666 /dev/rxb6
	raspi-gpio set 6 pn
