from typing import Optional, List
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path

__all__ = [
    'Discoverer',
]

logger = getLogger('compressClips')


@dataclass(frozen=True)
class Discoverer:
    """A representation of parameters used to discover files."""

    fileTypes: Optional[List[str]] = None
    minimumSize: Optional[int] = None

    def discover(self, directory: Optional[str] = None) -> List[str]:
        """
        Iterate through the files in a given directory and returns all valid files.

        If directory is None then uses the current working directory.
        """
        if directory is not None:
            path = Path(directory)
            logger.log(2, f'[~] Created path at {directory}.')
        else:
            path = Path.cwd()
            logger.log(2, f'[~] Created path in current working directory.')

        if not path.exists() or path.is_file():  # if the directory path given is invalid
            return []

        files = []

        for child in path.iterdir():
            if child.is_file():
                # File type check
                if self.fileTypes is not None and child.suffix not in self.fileTypes:
                    logger.log(1, f'[-] Disqualified "{child.name}" ({child.suffix} != [{", ".join(self.fileTypes)}]).')
                    continue

                stat = child.stat()

                # Minimum size check
                if self.minimumSize is not None and stat.st_size < self.minimumSize:
                    logger.log(1, f'[-] Disqualified "{child.name}" ({stat.st_size} < {self.minimumSize}).')
                    continue

                logger.log(1, f'[+] Discovered "{child.name}".')
                files.append(str(child.resolve()))

        return files
