
def process(i):
    if not i.is_fqdn() or not i.is_subdomain():
        return

    i2 = i.copy(**{
        'indicator': i.is_subdomain(),
        'confidence': 0
    })
    i2.fqdn_resolve()

    yield i2
