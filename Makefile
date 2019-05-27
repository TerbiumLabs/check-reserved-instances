
DIR := ${CURDIR}

#if make is typed with no further arguments, then show a list of available targets
default:
	@awk -F\: '/^[a-z_]+:/ && !/default/ {printf "- %-20s %s\n", $$1, $$2}' Makefile

help:
	@echo ""

run:
	check-reserved-instances --config config.ini

install:
	python setup.py install

%:
	@:
