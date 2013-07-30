VIRTUALENV=virtualenv
VENV=.
PYTHON=$(VENV)/bin/python
DEV_STAMP=.dev_env_installed.stamp
INSTALL_STAMP=.install.stamp

.IGNORE: clean
.PHONY: functional_tests unit_tests tests

OBJECTS = bin/ lib/ local/ include/ man/ .coverage d2to1-0.2.7-py2.7.egg \
	.coverage daybed.egg-info

all: install
install: $(INSTALL_STAMP)
$(INSTALL_STAMP): virtualenv
	$(PYTHON) setup.py develop
	touch $(INSTALL_STAMP)

install-dev: $(DEV_STAMP)
$(DEV_STAMP): virtualenv dev-requirements.txt
	$(VENV)/bin/pip install -r dev-requirements.txt --use-mirrors
	touch $(DEV_STAMP)

virtualenv: $(PYTHON)
$(PYTHON):
	$(VIRTUALENV) $(VENV)

clean:
	rm -fr $(OBJECTS) $(DEV_STAMP) $(INSTALL_STAMP)

tests: $(INSTALL_STAMP) install-dev
	$(VENV)/bin/nosetests --with-coverage --cover-package=daybed -s

serve: install-dev
	$(VENV)/bin/pserve development.ini --reload
