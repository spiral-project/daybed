PYTHON2 = `which python2 python2.7 python2.6 | head -1`
DAYBED_EGG=lib/$(PYTHON2)/site-packages/daybed.egg-link
DEV_STAMP=dev_env_installed.stamp
VENV_STAMP=venv_installed.stamp

.IGNORE: clean
.PHONY: functional_tests unit_tests tests

all: $(DAYBED_EGG)
install: all

install-dev: $(DEV_STAMP)

$(DAYBED_EGG): $(VENV_STAMP)
	bin/python setup.py develop

$(DEV_STAMP): $(VENV_STAMP) dev-requirements.txt
	bin/pip install -r dev-requirements.txt --use-mirrors
	touch $(DEV_STAMP)

$(VENV_STAMP):
	virtualenv --python=$(PYTHON2) .
	touch $(VENV_STAMP)
clean:
	rm -rf bin/ lib/ local/ include/ $(DEV_STAMP) $(VENV_STAMP)

functional_tests: install-dev
	bin/lettuce daybed/tests/features

unit_tests: install-dev
	bin/nosetests --with-coverage --cover-package=daybed

tests: $(DAYBED_EGG) functional_tests unit_tests

serve: install-dev
	bin/pserve development.ini --reload
