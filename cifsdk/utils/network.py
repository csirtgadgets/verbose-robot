import os, socket
import dns.resolver
from dns.resolver import NoAnswer, NXDOMAIN, NoNameservers, Timeout
from dns.name import EmptyLabel


TIMEOUT = os.getenv('CIF_RESOLVENS_TIMEOUT', 5)


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


def resolve_ns(data, t='A', timeout=TIMEOUT):
    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = timeout
    resolver.search = []
    try:
        answers = resolver.query(data, t)
        resp = []
        for rdata in answers:
            resp.append(rdata)
    except (NoAnswer, NXDOMAIN, EmptyLabel, NoNameservers, Timeout) as e:
        if str(e).startswith('The DNS operation timed out after'):
            return

        if not str(e).startswith('The DNS response does not contain an answer to the question'):
            if not str(e).startswith('None of DNS query names exist'):
                return

        return

    return resp
