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
#  Runtime variables
#...
ENV BACKEND_ENGINE daybed.backends.couchdb.CouchDBBackend
ENV BACKEND_HOST couchdb
ENV BACKEND_PORT 5984
ENV BACKEND_DB_NAME daybed
ENV ELASTICSEARCH_HOSTS elasticsearch:9200
ENV ELASTICSEARCH_INDICES_PREFIX docker_daybed

ENV DAYBED_MODEL_CREATORS Authenticated
ENV DAYBED_TOKEN_HMAC_KEY c0ad28e15492f999c31f0befa11d37ab

ENV UWSGI_NB_PROCESS 4

ENV PERSONA_SECRET THIS IS SUPER SECRET.
ENV PERSONA_AUDIENCE http://localhost:8000 http://0.0.0.0:8000 http://127.0.0.1:8000

#
#  Run !
#...
EXPOSE 8000
CMD ["/opt/apps/daybed/.venv/bin/uwsgi", "/opt/apps/daybed/conf/docker.ini"]
