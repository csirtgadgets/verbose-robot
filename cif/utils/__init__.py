from cifsdk.constants import RUNTIME_PATH
from cif.constants import VERSION
from argparse import ArgumentParser


def get_argument_parser():
    BasicArgs = ArgumentParser(add_help=False)
    BasicArgs.add_argument('-d', '--debug', dest='debug', action="store_true")
    BasicArgs.add_argument('-v', '--verbose', action='store_true')
    BasicArgs.add_argument('-V', '--version', action='version', version=VERSION)
    BasicArgs.add_argument(
        "--runtime-path", help="specify the runtime path [default %(default)s]", default=RUNTIME_PATH
    )
    return ArgumentParser(parents=[BasicArgs], add_help=False)
