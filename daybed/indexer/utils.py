# -*- coding: utf-8 -*-
from six.moves.urllib.parse import urlparse


def build_elasticsearch_hosts(hosts):
    """Take a list of hosts and build an Elasticsearch parameter list.

    >>> build_elasticsearch_hosts(['https://admin:password@localhost'])
    [{'use_ssl': True, 'host': 'localhost', 'http_auth': 'admin:password', 'port': 443}]

    """
    built_hosts = []

    for host in hosts:
        arguments = urlparse(host)

        # If the argument is not an URL, let it go.
        if not arguments.netloc:
            built_hosts.append(host)
            continue

        http_auth = None
        use_ssl = False
        port = 80

        netloc = arguments.netloc.split('@')

        if len(netloc) == 2:
            http_auth = netloc[0]
            netloc = netloc[1]
        else:
            netloc = arguments.netloc

        if ':' in netloc:
            hostname, port = netloc.split(':')
            if arguments.scheme == 'https':
                use_ssl = True
        else:
            hostname = netloc
            if arguments.scheme == 'https':
                use_ssl = True
                port = 443

        built_hosts.append({
            'host': hostname,
            'port': int(port),
            'use_ssl': use_ssl,
            'http_auth': http_auth
        })

    return built_hosts
