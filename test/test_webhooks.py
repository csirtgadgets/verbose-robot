from cif.webhooks import Webhooks


def test_webhooks():
    with Webhooks(test=True) as r:
        pass
