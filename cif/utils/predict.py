from csirtg_urlsml_tf import predict as predict_url
from csirtg_domainsml_tf import predict as predict_fqdn
from csirtg_ipsml_tf import predict as predict_ip
from csirtg_ipsml_tf.utils import extract_features as extract_features_ip
from types import GeneratorType


def _filter_indicators(indicators, itype):
    if isinstance(indicators, GeneratorType):
        indicators = list(indicators)

    return [(i.indicator, idx) for idx, i in enumerate(indicators) if i.itype == itype and not i.probability]


def _normalize_predictions(indicators, things, predictions):
    for idx, u in enumerate(things):
        indicators[u[1]].probability = round((predictions[idx][0] * 100), 2)

    return indicators


def predict_urls(indicators):
    urls = _filter_indicators(indicators, 'url')

    if len(urls) == 0:
        return indicators

    predictions = predict_url([u[0] for u in urls])

    return _normalize_predictions(indicators, urls, predictions)


def predict_fqdns(indicators):
    domains = _filter_indicators(indicators, 'fqdn')

    if len(domains) == 0:
        return indicators

    predictions = predict_fqdn([u[0] for u in domains])

    return _normalize_predictions(indicators, domains, predictions)


def predict_ips(indicators):
    ips = _filter_indicators(indicators, 'ipv4')

    if len(ips) == 0:
        return indicators

    ips_feats = []
    from pprint import pprint
    pprint(ips)
    for i in ips:
        f = list(extract_features_ip(i[0], i[1]))
        ips_feats.append(f[0])

    predictions = predict_ip([ips_feats])

    return _normalize_predictions(indicators, ips, predictions)
