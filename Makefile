VIRTUALENV=virtualenv
VENV=.
PYTHON=$(VENV)/bin/python
DEV_STAMP=.dev_env_installed.stamp
INSTALL_STAMP=.install.stamp

.IGNORE: clean
.PHONY: all install virtualenv tests

OBJECTS = bin/ lib/ local/ include/ man/ .coverage d2to1-0.2.7-py2.7.egg \
	.coverage daybed.egg-info

all: install
install: $(INSTALL_STAMP)
$(INSTALL_STAMP): $(PYTHON)
	$(PYTHON) setup.py develop
	touch $(INSTALL_STAMP)

$(DEV_STAMP): $(VENV_STAMP) dev-requirements.txt
	bin/pip install pip==1.4.1 setuptools==1.1.6
	bin/pip install -r dev-requirements.txt --use-mirrors
	touch $(DEV_STAMP)

$(VENV_STAMP):
	virtualenv -p python2.7 .
	touch $(VENV_STAMP)

clean:
	rm -fr $(OBJECTS) $(DEV_STAMP) $(INSTALL_STAMP)

tests: $(DEV_STAMP)
	$(VENV)/bin/nosetests --with-coverage --cover-package=daybed -s

serve: $(DEV_STAMP)
	$(VENV)/bin/pserve development.ini --reload
