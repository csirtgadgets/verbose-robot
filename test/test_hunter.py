# import os
# import pytest
# from zmq import Context
# from faker import Faker
# from pprint import pprint
# import dns
#
# from csirtg_indicator import Indicator
#
# import cif.hunter
# from cif.hunter import Hunter
#
# from cifsdk.utils import load_plugins
#
# fake = Faker()
# DISABLE_FAST_TESTS = os.getenv('DISABLE_NETWORK_TESTS', False)
#
#
# def test_hunter():
#     with Hunter(Context.instance()) as h:
#         assert isinstance(h, Hunter)
#
#
# @pytest.mark.skipif(DISABLE_FAST_TESTS, reason='network test disabled')
# def test_hunter_plugins():
#     plugins = load_plugins(cif.hunter.__path__)
#     count = 0
#     indicators = []
#     for d in range(0, 1):
#         i = Indicator(indicator=fake.domain_name(), tags=['malware'])
#         indicators.append(i)
#
#     indicators.append(Indicator('csirtgadgets.com', tags=['botnet']))
#     indicators.append(Indicator('gfycat.com', tags=['exploit']))
#     indicators.append(Indicator('http://csirtgadgets.com', tags=['botnet']))
#
#     for p in plugins:
#         rv = p.process(next(i for i in indicators))
#
#         try:
#             rv = list(r for r in rv)
#
#         except dns.resolver.NoNameservers:
#             pass
#
#         if not rv or len(rv) == 0:
#             continue
#
#         rv = [i.__dict__() for i in rv]
#         count += len(rv)
