VIRTUALENV=virtualenv
VENV := $(shell echo $${VIRTUAL_ENV-.venv})
PYTHON=$(VENV)/bin/python
DEV_STAMP=$(VENV)/.dev_env_installed.stamp
INSTALL_STAMP=$(VENV)/.install.stamp

.IGNORE: clean
.PHONY: all docs install virtualenv tests

OBJECTS = .venv .coverage

all: install
install: $(INSTALL_STAMP)
$(INSTALL_STAMP): $(PYTHON)
	$(PYTHON) setup.py develop
	touch $(INSTALL_STAMP)

install-dev: $(DEV_STAMP)
$(DEV_STAMP): $(PYTHON)
	$(VENV)/bin/pip install -r dev-requirements.txt
	touch $(DEV_STAMP)

virtualenv: $(PYTHON)
$(PYTHON):
	virtualenv $(VENV)

docs:
	sphinx-build -b html ./docs/source docs/_build

clean:
	rm -fr $(OBJECTS) $(DEV_STAMP) $(INSTALL_STAMP)
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete

tests: install-dev
	$(VENV)/bin/tox

tests-failfast: install-dev
	$(VENV)/bin/nosetests --with-coverage --cover-package=daybed -x -s

serve: install install-dev
	$(VENV)/bin/pserve development.ini --reload
