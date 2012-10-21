DAYBED_EGG=$(wildcard lib/python*/site-packages/daybed.egg-link)
DEV_STAMP=.dev_env_installed.stamp
VENV_STAMP=.venv_installed.stamp

.IGNORE: clean
.PHONY: functional_tests unit_tests tests
.INTERMEDIATE: $(VENV_DIRS) $(DEV_STAMP) $(VENV_STAMP)

OBJECTS = bin/ lib/ local/ include/ man/ .coverage d2to1-0.2.7-py2.7.egg \
	.coverage daybed.egg-info


all: $(DAYBED_EGG)
install: all

install-dev: $(DEV_STAMP)

$(DAYBED_EGG): $(VENV_STAMP)
	# Monkey patch since distutils2
	bin/pip install https://github.com/mozilla-services/cornice/tarball/spore-support#egg=cornice
	bin/python setup.py develop

$(DEV_STAMP): $(VENV_STAMP) dev-requirements.txt
	bin/pip install -r dev-requirements.txt --use-mirrors
	touch $(DEV_STAMP)

$(VENV_STAMP):
	virtualenv .
	touch $(VENV_STAMP)
clean:
	rm -fr $(OBJECTS)

functional_tests: install-dev
	bin/lettuce daybed/tests/features

unit_tests: install-dev
	bin/nosetests --with-coverage --cover-package=daybed

tests: $(DAYBED_EGG) functional_tests unit_tests

serve: install-dev
	bin/pserve development.ini --reload
