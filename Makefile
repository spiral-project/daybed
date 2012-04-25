setup_venv:
	virtualenv .
	bin/pip install -r dev-requirements.txt
	bin/python setup.py develop

functional_tests: setup_venv
	bin/lettuce daybed/tests/features

unit_tests: setup_venv
	bin/python setup.py test

tests: functional_tests unit_tests

serve: setup_venv
	bin/pserve development.ini --reload
