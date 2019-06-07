
DIR := ${CURDIR}

#if make is typed with no further arguments, then show a list of available targets
default:
	@awk -F\: '/^[a-z_]+:/ && !/default/ {printf "- %-20s %s\n", $$1, $$2}' Makefile

help:
	@echo ""

make bootstrap:
	pip install 'awscli==1.14.61'

run:
	check-reserved-instances --config config.ini

install:
	python setup.py install

test:
	tox

pip_install:
	pip install -r requirements.txt

pip_install_test:
	pip install -r test_requirements.txt

pip_install_all: pip_install pip_install_test
	@echo "Done"

%:
	@:
