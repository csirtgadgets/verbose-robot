from cif.router import Router


def test_router():
    with Router(test=True) as r:
        pass
