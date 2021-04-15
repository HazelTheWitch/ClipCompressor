from logging import getLogger, StreamHandler
from compressClips import *
import sys
import click


logger = getLogger('compressClips')
logger.setLevel(1)

consoleHandler = StreamHandler(sys.stdout)
consoleHandler.setLevel(1)

logger.addHandler(consoleHandler)


@click.command()
def compressClips():
    ...


if __name__ == '__main__':
    compressClips()
