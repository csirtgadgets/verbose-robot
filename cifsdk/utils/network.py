import socket

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


def resolve_fqdn(host):
    try:
        host = socket.gethostbyname(host)
        return host
    except:
        return


def resolve_url(url):
    u = urlparse(url)
    return u.hostname
