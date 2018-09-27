# -*- coding: utf-8 -*-
from faker import Faker
from random import sample
from pprint import pprint
import arrow

from cif.utils.predict import predict_fqdns, predict_ips, predict_urls
from csirtg_indicator import Indicator
import pytest
import os

fake = Faker()
DISABLE_PREDICT_IPV4 = os.getenv('DISABLE_PREDICT_IPV4', False)


def test_predict_ipv4():
    indicators = []
    for d in range(0, 25):
        indicators.append(Indicator(str(fake.ipv4()), reported_at=arrow.utcnow(), resolve_geo=True))

    pprint(indicators)
    indicators = predict_ips(indicators)
    probs = [i.probability for i in indicators]
    avg = (sum(probs) / len(probs))
    print(avg)
    if DISABLE_PREDICT_IPV4:
        # for tests when we're not pre-loading maxmind/geoip libs
        assert 16 < avg < 98
    else:
        assert 16 < avg < 93


def test_predict_url():
    indicators = []
    for d in range(0, 25):
        indicators.append(Indicator(str(fake.url()), resolve_geo=True))

    pprint(indicators)
    indicators = predict_urls(indicators)
    probs = [i.probability for i in indicators]
    avg = (sum(probs) / len(probs))
    print(avg)
    assert 16 < avg < 93


def test_predict_fqdn():
    indicators = []
    for d in range(0, 25):
        indicators.append(Indicator(str(fake.domain_name(2)), resolve_geo=True))

    indicators = predict_fqdns(indicators)
    pprint(indicators)
    probs = [i.probability for i in indicators]
    avg = (sum(probs) / len(probs))
    print(avg)
    assert 16 < avg < 93
