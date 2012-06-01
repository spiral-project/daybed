bin/ lib/:
	virtualenv .
	bin/pip install -r dev-requirements.txt --use-mirrors
	bin/python setup.py develop

install: bin/

clean:
	rm -rf bin/ lib/ local/ include/

functional_tests: bin/
	bin/lettuce daybed/tests/features

unit_tests: bin/
	bin/python setup.py test

tests: functional_tests unit_tests

serve: bin/
	bin/pserve development.ini --reload
