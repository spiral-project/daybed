DEV_STAMP=.dev_env_installed.stamp
INSTALL_STAMP=.install.stamp

.PHONY: all docs install virtualenv tests clean

OBJECTS = .coverage daybed.egg-info

all: install
install: $(INSTALL_STAMP)
$(INSTALL_STAMP):
	python setup.py develop
	touch $(INSTALL_STAMP)

install-dev: $(DEV_STAMP)
$(DEV_STAMP):
	pip install -r dev-requirements.txt
	touch $(DEV_STAMP)

clean:
	rm -fr $(OBJECTS) $(DEV_STAMP) $(INSTALL_STAMP)
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete

docs:
	sphinx-build -b html ./docs/source docs/_build

tests: install-dev
	tox

tests-failfast:
	nosetests --with-coverage --cover-package=daybed -x -s

serve: install install-dev
	pserve development.ini --reload
