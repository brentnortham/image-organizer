"""Photo analyzer module - extracts EXIF metadata, calculates content hashes, and collects file metadata."""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import logging

from PIL import Image
from PIL.ExifTags import TAGS, DATETIME
import pillow_heif

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()

logger = logging.getLogger(__name__)


class PhotoMetadata:
    """Container for photo metadata."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.size = file_path.stat().st_size
        self.mtime = file_path.stat().st_mtime
        self.content_hash: Optional[str] = None
        self.exif_data: Dict[str, Any] = {}
        self.date_taken: Optional[datetime] = None
        self.camera_make: Optional[str] = None
        self.camera_model: Optional[str] = None
        self.exif_date_keys = [
            'DateTimeOriginal',
            'DateTimeDigitized',
            'DateTime',
        ]

    def __repr__(self):
        return f"PhotoMetadata(path={self.file_path}, size={self.size}, date={self.date_taken})"


def calculate_content_hash(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Calculate MD5 hash of file content for duplicate detection.

    Args:
        file_path: Path to the file
        chunk_size: Size of chunks to read at a time (for memory efficiency)

    Returns:
        Hexadecimal MD5 hash string
    """
    md5_hash = hashlib.md5()

    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5_hash.update(chunk)
    except IOError as e:
        logger.error(f"Error reading file for hashing {file_path}: {e}")
        raise

    return md5_hash.hexdigest()


def extract_exif_metadata(image: Image.Image) -> Dict[str, Any]:
    """
    Extract EXIF metadata from PIL Image object.

    Args:
        image: PIL Image object with EXIF data

    Returns:
        Dictionary of EXIF tags with human-readable keys
    """
    exif_data = {}

    try:
        exif = image.getexif()
        if not exif:
            return exif_data

        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            exif_data[tag] = value

    except Exception as e:
        logger.debug(f"Error extracting EXIF data: {e}")

    return exif_data


def parse_exif_date(date_str: str) -> Optional[datetime]:
    """
    Parse EXIF date string to datetime object.

    EXIF dates are typically in format: "YYYY:MM:DD HH:MM:SS"

    Args:
        date_str: Date string from EXIF

    Returns:
        datetime object or None if parsing fails
    """
    if not date_str:
        return None

    # Try common EXIF date formats
    date_formats = [
        "%Y:%m:%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y:%m:%d",
        "%Y-%m-%d",
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(str(date_str), fmt)
        except (ValueError, TypeError):
            continue

    logger.debug(f"Could not parse EXIF date: {date_str}")
    return None


def analyze_photo(file_path: Path) -> PhotoMetadata:
    """
    Analyze a photo file and extract all metadata.

    Args:
        file_path: Path to the photo file

    Returns:
        PhotoMetadata object with all extracted information

    Raises:
        IOError: If file cannot be read
        Exception: For corrupted or unsupported image files
    """
    metadata = PhotoMetadata(file_path)

    # Calculate content hash
    try:
        metadata.content_hash = calculate_content_hash(file_path)
    except Exception as e:
        logger.warning(f"Failed to calculate hash for {file_path}: {e}")
        # Continue without hash - this photo won't be detected as duplicate by content

    # Extract EXIF metadata
    try:
        with Image.open(file_path) as image:
            # Get EXIF data
            metadata.exif_data = extract_exif_metadata(image)

            # Extract date taken (try multiple EXIF date fields)
            for date_key in metadata.exif_date_keys:
                if date_key in metadata.exif_data:
                    date_str = metadata.exif_data[date_key]
                    parsed_date = parse_exif_date(date_str)
                    if parsed_date:
                        metadata.date_taken = parsed_date
                        break

            # Extract camera info
            metadata.camera_make = metadata.exif_data.get('Make')
            metadata.camera_model = metadata.exif_data.get('Model')

    except Exception as e:
        logger.warning(f"Error analyzing image {file_path}: {e}")
        # Continue with basic metadata (size, mtime)

    # If no EXIF date, use file modification time
    if not metadata.date_taken:
        metadata.date_taken = datetime.fromtimestamp(metadata.mtime)
        logger.debug(f"No EXIF date found for {file_path}, using file mtime")

    return metadata
