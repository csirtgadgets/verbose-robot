

def process(i):
    if not i.is_ip():
        return

    if 'whitelist' not in i.tags:
        return

    if i.indicator.endswith('/24'):
        return

    i2 = i.copy(**{
        'indicator': i.ipv4_to_prefix(),
        'tags': ['whitelist'],
        'confidence': 2
    })

    yield i2
