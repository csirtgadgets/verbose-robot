import logging, os
from argparse import ArgumentParser

from .constants import LOG_FORMAT, RUNTIME_PATH, LOGLEVEL, VERSION


def setup_logging(args):
    loglevel = logging.getLevelName(LOGLEVEL)

    if args.debug:
        loglevel = logging.DEBUG

    console = logging.StreamHandler()
    logging.getLogger('').setLevel(loglevel)
    console.setFormatter(logging.Formatter(LOG_FORMAT))
    logging.getLogger('').addHandler(console)


def get_argument_parser():
    BasicArgs = ArgumentParser(add_help=False)
    BasicArgs.add_argument('-d', '--debug', dest='debug', action="store_true")
    BasicArgs.add_argument('-V', '--version', action='version', version=VERSION)
    BasicArgs.add_argument(
        "--runtime-path", help="specify the runtime path [default %(default)s]", default=RUNTIME_PATH
    )
    return ArgumentParser(parents=[BasicArgs], add_help=False)


def setup_runtime_path(path):
    if not os.path.isdir(path):
        os.mkdir(path)