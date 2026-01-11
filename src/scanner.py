"""Photo scanner module - recursively scans folders and filters by supported image formats."""

import os
from pathlib import Path
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

# Supported image extensions (case-insensitive)
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic', '.heif'}


def scan_folder(source_path: Path) -> List[Path]:
    """
    Recursively scan a folder for supported image files.

    Args:
        source_path: Path to the source folder to scan

    Returns:
        List of Path objects for supported image files

    Raises:
        FileNotFoundError: If source_path doesn't exist
        PermissionError: If access to source_path is denied
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Source folder does not exist: {source_path}")

    if not source_path.is_dir():
        raise ValueError(f"Source path is not a directory: {source_path}")

    image_files = []

    try:
        for root, dirs, files in os.walk(source_path):
            # Skip hidden directories (like .git, .DS_Store, etc.)
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for file in files:
                # Skip hidden files
                if file.startswith('.'):
                    continue

                file_path = Path(root) / file
                ext = file_path.suffix.lower()

                if ext in SUPPORTED_EXTENSIONS:
                    image_files.append(file_path)
                    logger.debug(f"Found image: {file_path}")

    except PermissionError as e:
        logger.error(f"Permission denied while scanning {source_path}: {e}")
        raise

    logger.info(f"Scanned {source_path}: found {len(image_files)} image files")
    return image_files


def get_file_metadata(file_path: Path) -> dict:
    """
    Get basic file metadata (size, modification time).

    Args:
        file_path: Path to the file

    Returns:
        Dictionary with 'size' (bytes) and 'mtime' (timestamp) keys
    """
    stat = file_path.stat()
    return {
        'size': stat.st_size,
        'mtime': stat.st_mtime,
        'path': file_path,
    }
