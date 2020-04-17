FAMILY = pic14
DEVICE = 12f1572

CC = sdcc
CFLAGS = --use-non-free -m$(FAMILY) -p$(DEVICE)

all: rxb6.hex

%.hex: %.c
	$(CC) $(CFLAGS) $<

prog: rxb6.hex
	cd $(HOME)/Projects/tools/pk2cmd/bin && \
		sudo ./pk2cmd -PPIC$(DEVICE) -F$(PWD)/$< -M

clean:
	rm -f *.asm *.cod *.hex *.lst *.o
