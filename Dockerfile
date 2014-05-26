FROM dockerfile/python
MAINTAINER Spiral Project "daybed.dev@librelist.com"

#
#  Daybed
#...
# Recursive copy of repository
ADD . /opt/apps/daybed

#
# Install
#...
RUN (cd /opt/apps/daybed && make install)
RUN /opt/apps/daybed/.venv/bin/pip install uwsgi

#
#  Run !
#...
EXPOSE 8000
CMD ["/opt/apps/daybed/.venv/bin/uwsgi", "--ini-paste", "/opt/apps/daybed/conf/production.ini"]
