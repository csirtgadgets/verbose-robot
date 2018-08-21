from cif.router import Router
import tempfile


def test_router():
    r = Router(test=True, hunter_threads=2)
    r.start()
    r.stop()
