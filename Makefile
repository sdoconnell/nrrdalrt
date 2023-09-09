PREFIX = /usr/local
BINDIR = $(PREFIX)/bin
MANDIR = $(PREFIX)/share/man/man1
DOCDIR = $(PREFIX)/share/doc/nrrdalrt
BSHDIR = /etc/bash_completion.d

.PHONY: all install uninstall

all:

install:
	install -m755 -d $(BINDIR)
	install -m755 -d $(MANDIR)
	install -m755 -d $(DOCDIR)
	install -m755 -d $(BSHDIR)
	gzip -c doc/nrrdalrt.1 > nrrdalrt.1.gz
	install -m755 nrrdalrt/nrrdalrt.py $(BINDIR)/nrrdalrt
	install -m644 nrrdalrt.1.gz $(MANDIR)
	install -m644 README.md $(DOCDIR)
	install -m644 LICENSE $(DOCDIR)
	install -m644 CHANGES $(DOCDIR)
	install -m644 CONTRIBUTING.md $(DOCDIR)
	install -m644 auto-completion/bash/nrrdalrt-completion.bash $(BSHDIR)
	rm -f nrrdalrt.1.gz

uninstall:
	rm -f $(BINDIR)/nrrdalrt
	rm -f $(MANDIR)/nrrdalrt.1.gz
	rm -f $(BSHDIR)/nrrdalrt-completion.bash
	rm -rf $(DOCDIR)

