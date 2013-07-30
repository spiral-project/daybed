VIRTUALENV=virtualenv
DEV_STAMP=.dev_env_installed.stamp
VENV_STAMP=.venv_installed.stamp
INSTALL_STAMP=.install.stamp

.IGNORE: clean
.PHONY: functional_tests unit_tests tests

OBJECTS = bin/ lib/ local/ include/ man/ .coverage d2to1-0.2.7-py2.7.egg \
	.coverage daybed.egg-info

all: install
install: $(INSTALL_STAMP)

install-dev: $(DEV_STAMP)

$(INSTALL_STAMP): $(VENV_STAMP)
	bin/python setup.py develop
	touch $(INSTALL_STAMP)

$(DEV_STAMP): $(VENV_STAMP) dev-requirements.txt
	bin/pip install -r dev-requirements.txt --use-mirrors
	touch $(DEV_STAMP)

$(VENV_STAMP):
	$(VIRTUALENV) .
	touch $(VENV_STAMP)

clean:
	rm -fr $(OBJECTS) $(DEV_STAMP) $(VENV_STAMP) $(INSTALL_STAMP)

tests: $(INSTALL_STAMP) install-dev
	bin/nosetests --with-coverage --cover-package=daybed -s

serve: install-dev
	bin/pserve development.ini --reload
