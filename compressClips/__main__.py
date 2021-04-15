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


def _compressFiles(files: Deque['Path'], compression: int, outDir: str, overwrite: bool, deleteAfter: bool, hwaccel: bool) -> None:
    enc = 'h264_nvenc' if hwaccel else 'libx264'
    while files:
        current = files.pop()
        post = Path(outDir, current.name)

        logger.log(2, f'[+] Compressing {current.name}.')
        try:
            _, err = (
                    ffmpeg.input(str(current.resolve()))
                    .output(str(post), vcodec=enc, crf=str(compression), format=current.suffix[1:], movflags='use_metadata_tags', map_metadata='0')
            ).run(quiet=True, overwrite_output=overwrite)

            currSize = current.stat().st_size
            postSize = post.stat().st_size

            if deleteAfter:
                logger.log(2, f'[+] Deleting original {current.name}.')
                current.unlink()

            logger.log(2, f'[~] {current.name} completed ({(100 * currSize / postSize):.2f}% compression).')
        except ffmpeg._run.Error:
            logger.log(3, f'[-] Could not compress {current.name}.')



@click.command()
@click.option('-f', '--filetypes', multiple=True, default=['.mp4'], type=str, show_default=True)
@click.option('-o', '--output-directory', 'outputDirectory', default='compressed', type=click.Path(file_okay=False), required=True)
@click.option('-t', '--threads', 'threadCount', type=click.IntRange(min=1), default=1, required=True, show_default=True)
@click.option('--minimum-size', 'minimumSize', type=FILESIZETYPE, default='1MB', show_default=True)
@click.option('-c', '--compression', type=click.IntRange(min=24, max=30), default=24, required=True, show_default=True)
@click.option('--overwrite/--no-overwrite', default=True)
@click.option('--delete-after/--no-delete-after', 'deleteAfter', default=False)
@click.option('-v', '--verbose', count=True)
@click.option('-gpu', '--use-gpu', 'hwaccel', is_flag=True, default=False)
def compressClips(filetypes: List[str], outputDirectory: str, threadCount: int, minimumSize: int, compression: int, overwrite: bool, verbose: int, deleteAfter: bool, hwaccel: bool) -> None:
    logLevel = max(4 - verbose, 1)

    logger.setLevel(logLevel)
    consoleHandler.setLevel(logLevel)

    if hwaccel and threadCount > 1:
        logger.log(4, f'[-] Sadly multi-threaded GPU enabled compression is not supported. Please use one or the other.')
        return

    for i, ft in enumerate(filetypes):
        if ft[0] != '.':
            logger.log(2, f'[~] Appended "." to file type "{ft}".')
            filetypes[i] = f'.{ft}'

    outDir = Path('.', outputDirectory)
    outDir.mkdir(parents=True, exist_ok=True)
    outDir = str(outDir.resolve())

    logger.log(3, '[+] Discovering files.')
    files = deque(Discoverer(fileTypes=filetypes, minimumSize=minimumSize).discover())

    if threadCount > len(files):
        threadCount = len(files)

    threads = []

    logger.log(3, '[+] Initializing threads.')
    for _ in range(threadCount):
        t = threading.Thread(target=_compressFiles, args=(files, compression, outDir, overwrite, deleteAfter, hwaccel), daemon=True)
        threads.append(t)

        if hwaccel:
            hwaccel = False

    logger.log(3, '[+] Starting threads.')
    for t in threads:
        t.start()

    logger.log(3, '[~] Waiting for threads to finish.')
    for t in threads:
        t.join()


if __name__ == '__main__':
    compressClips()
