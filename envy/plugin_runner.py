import sys
import os

from envy import api


def parse_args() -> api.Plugin:
    print(sys.argv)


if __name__ == '__main__':
    parse_args()
