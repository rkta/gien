CFLAGS += $(shell pkg-config --cflags python3)
LDFLAGS += $(shell pkg-config --libs python3)
PREFIX ?= /usr

all: gien

gien.c: gien.py
	cython -3 -o $@ $< --embed

gien: gien.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)
	strip $@

clean:
	rm -f gien.c gien
	rm -rf src/ pkg/ *.tar

install: gien
	install -Dm755 gien $(DESTDIR)$(PREFIX)/bin/gien

.PHONY: all clean check install
