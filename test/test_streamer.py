from cif.streamer import Streamer


def test_streamer():
    with Streamer(test=True) as r:
        pass
