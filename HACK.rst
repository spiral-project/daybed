Daybed
######

virtualenv --no-site-packages env
source env/bin/activate


python setup.py develop

python setup.py test -q

pserve development.ini --reload
