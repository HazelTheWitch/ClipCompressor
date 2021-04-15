from logging import getLogger, StreamHandler
from compressClips import *
import sys
import click
from pathlib import Path
import re
from typing import List, Deque
import threading
from collections import deque
import ffmpeg


logger = getLogger('compressClips')

consoleHandler = StreamHandler(sys.stdout)

logger.addHandler(consoleHandler)


class FileSizeType(click.ParamType):
    regexPattern = re.compile(r'(\d+)\s*([kmg])?b$')

    prefixes = {None: 1, 'k': 1024, 'm': 1048576, 'g': 1073741824}

    name = 'filesize'

    def convert(self, value, param, ctx):
        t = type(value)
        if t == int:
            return value

        if t != str:
            self.fail(f'expected string for filesize conversion, got {t}.', param, ctx)

        match = FileSizeType.regexPattern.match(value.lower())

        if match is None:
            self.fail(f'{value} is not a valid file size')

        return int(match.group(1)) * FileSizeType.prefixes[match.group(2)]


FILESIZETYPE = FileSizeType()


def _compressFiles(files: Deque['Path'], compression: int, outDir: str, overwrite: bool) -> None:
    while files:
        current = files.pop()
        post = Path(outDir, current.name)

        logger.log(2, f'[+] Compressing {current.name}.')
        _, err = (
                ffmpeg.input(str(current.resolve()))
                .output(str(post), vcodec='libx265', crf=str(compression))
        ).run(quiet=True, overwrite_output=overwrite)

        currSize = current.stat().st_size
        postSize = post.stat().st_size

        logger.log(2, f'[~] {current.name} completed ({(100*currSize/postSize):.2f}% compression).')


@click.command()
@click.option('-f', '--filetypes', multiple=True, default=['.mp4'], type=str, show_default=True)
@click.option('-o', '--output-directory', 'outputDirectory', default='compressed', type=click.Path(file_okay=False), required=True)
@click.option('-t', '--threads', 'threadCount', type=click.IntRange(min=1), default=1, required=True)
@click.option('--minimum-size', 'minimumSize', type=FILESIZETYPE, default='0B')
@click.option('-c', '--compression', type=click.IntRange(min=24, max=30), default=24, required=True)
@click.option('--overwrite/--no-overwrite', default=True)
@click.option('-v', '--verbose', count=True)
def compressClips(filetypes: List[str], outputDirectory: str, threadCount: int, minimumSize: int, compression: int, overwrite: bool, verbose: int) -> None:
    logLevel = max(4 - verbose, 1)

    logger.setLevel(logLevel)
    consoleHandler.setLevel(logLevel)

    for i, ft in enumerate(filetypes):
        if ft[0] != '.':
            logger.log(2, f'[~] Appended "." to file type "{ft}".')
            filetypes[i] = f'.{ft}'

    outDir = Path('.', outputDirectory)
    outDir.mkdir(parents=True, exist_ok=True)
    outDir = str(outDir.resolve())

    logger.log(3, '[+] Discovering files.')
    files = deque(Discoverer(fileTypes=filetypes, minimumSize=minimumSize).discover())

    threads = []

    logger.log(3, '[+] Initializing threads.')
    for _ in range(threadCount):
        t = threading.Thread(target=_compressFiles, args=(files, compression, outDir, overwrite), daemon=True)
        threads.append(t)

    logger.log(3, '[+] Starting threads.')
    for t in threads:
        t.start()

    logger.log(3, '[~] Waiting for threads to finish.')
    for t in threads:
        t.join()


if __name__ == '__main__':
    compressClips()
