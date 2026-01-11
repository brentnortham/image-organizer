"""Date organizer module - creates date-based folder structure (YYYY/MM/DD)."""

from datetime import datetime
from pathlib import Path
from typing import Dict
import logging

from src.analyzer import PhotoMetadata

logger = logging.getLogger(__name__)


def get_photo_date(metadata: PhotoMetadata) -> datetime:
    """
    Get the date for organizing a photo.

    Priority: EXIF date taken → file modification date

    Args:
        metadata: PhotoMetadata object

    Returns:
        datetime object for the photo
    """
    if metadata.date_taken:
        return metadata.date_taken

    # Fallback to file modification time
    return datetime.fromtimestamp(metadata.mtime)


def get_date_folder(date: datetime) -> Path:
    """
    Generate folder path based on date (YYYY/MM/DD format).

    Args:
        date: datetime object

    Returns:
        Path object representing the folder (YYYY/MM/DD)
    """
    return Path(f"{date.year:04d}") / f"{date.month:02d}" / f"{date.day:02d}"


def organize_by_date(photos) -> Dict[PhotoMetadata, Path]:
    """
    Organize photos by date, returning mapping of photo to destination folder.

    Args:
        photos: Iterable of PhotoMetadata objects or dict mapping PhotoMetadata to values

    Returns:
        Dictionary mapping PhotoMetadata to destination Path (folder + filename)
        Uses original filename - will be updated by namer module
    """
    organized = {}

    # Handle both set/list and dict inputs
    if isinstance(photos, dict):
        photo_list = photos.keys()
    else:
        photo_list = photos

    for metadata in photo_list:
        date = get_photo_date(metadata)
        date_folder = get_date_folder(date)

        # For now, use original filename - will be updated by namer module
        filename = metadata.file_path.name
        destination_path = date_folder / filename

        organized[metadata] = destination_path

        logger.debug(f"Organized {metadata.file_path.name} -> {destination_path}")

    logger.info(f"Organized {len(organized)} photos by date")
    return organized
