import os

ENABLED = os.getenv('CIF_HUNTER_ADVANCED', False)


def process(i):
    if not ENABLED:
        return

    if i.provider == 'spamhaus.org':
        return

    i2 = i.spamhaus()
    if not i2:
        return

    i2.tlp = i.tlp
    yield i2
