import pytest
import multiprocessing as mp
from cif.router import Router
import tempfile

from time import sleep
from pprint import pprint


def test_router():
    with Router(test=True) as r:
        pass


def test_router_advanced():
    dbfile = tempfile.mktemp()
    # p = mp.Process(target=Router, args=[{'test2': True, 'store_nodes': dbfile}])
    # p.start()
    #
    # sleep(2)
    #
    # p.terminate()
    #
    # sleep(5)
    # p.join()