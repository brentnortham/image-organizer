"""Name generator module - preserves meaningful filenames or generates date-time based names."""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import logging

from src.analyzer import PhotoMetadata

logger = logging.getLogger(__name__)

# Patterns that indicate non-meaningful (camera-generated) filenames
NON_MEANINGFUL_PATTERNS = [
    r'^IMG_\d+',           # IMG_1234, IMG_0001
    r'^DSC\d+',            # DSC01234, DSC1234
    r'^DSC_\d+',           # DSC_01234
    r'^DSCN\d+',           # DSCN1234
    r'^P\d{8}',            # P12345678
    r'^VID_\d+',           # VID_1234
    r'^SAM_\d+',           # SAM_1234
    r'^Screenshot',        # Screenshot 2024-01-15
    r'^Photo\s*\d+',       # Photo 1, Photo 2
    r'^Image\s*\d+',       # Image 1
    r'^pic\.\d+',          # pic.1
    r'^Picture\s*\d+',     # Picture 1
]


def is_meaningful_filename(filename: str) -> bool:
    """
    Determine if a filename is meaningful (preserve it) or camera-generated (rename it).

    Args:
        filename: Filename without extension

    Returns:
        True if filename should be preserved, False if it should be renamed
    """
    filename_lower = filename.lower()

    # Check against non-meaningful patterns
    for pattern in NON_MEANINGFUL_PATTERNS:
        if re.match(pattern, filename_lower):
            return False

    # Filenames that are very short (less than 5 chars) are likely not meaningful
    if len(filename) < 5:
        return False

    # If filename contains descriptive words, it's likely meaningful
    # This is a simple heuristic - could be improved
    descriptive_words = ['photo', 'picture', 'image', 'event', 'trip', 'vacation', 'birthday', 'wedding']
    filename_lower = filename_lower.replace('_', ' ').replace('-', ' ')

    # Check if it's just a date pattern (not meaningful on its own)
    if re.match(r'^\d{4}[-_]?\d{2}[-_]?\d{2}', filename_lower):
        return False

    # If it matches a descriptive pattern, it's meaningful
    for word in descriptive_words:
        if word in filename_lower:
            return True

    # Default: assume meaningful if it doesn't match camera patterns
    # This is conservative - better to preserve than lose meaningful names
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to be filesystem-safe.

    Removes or replaces invalid characters.

    Args:
        filename: Original filename (without extension)

    Returns:
        Sanitized filename
    """
    # Replace invalid characters with underscore
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)

    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')

    # Limit length (keep reasonable)
    if len(sanitized) > 200:
        sanitized = sanitized[:200]

    return sanitized


def generate_datetime_name(metadata: PhotoMetadata, extension: str) -> str:
    """
    Generate filename based on EXIF date-time.

    Format: YYYY-MM-DD_HH-MM-SS.ext

    Args:
        metadata: PhotoMetadata object
        extension: File extension (with dot, e.g., '.jpg')

    Returns:
        Generated filename
    """
    date = metadata.date_taken or datetime.fromtimestamp(metadata.mtime)
    return date.strftime("%Y-%m-%d_%H-%M-%S") + extension


def ensure_unique_filename(base_path: Path, metadata: PhotoMetadata, used_names: set) -> Path:
    """
    Ensure filename is unique by adding suffix if needed.

    Args:
        base_path: Desired base path (folder + filename)
        metadata: PhotoMetadata object (for fallback naming)
        used_names: Set of already-used full paths (as strings)

    Returns:
        Path that is guaranteed to be unique
    """
    if str(base_path) not in used_names:
        return base_path

    # Add suffix to make it unique
    stem = base_path.stem
    extension = base_path.suffix
    parent = base_path.parent
    counter = 1

    while True:
        new_name = f"{stem}_{counter:03d}{extension}"
        new_path = parent / new_name

        if str(new_path) not in used_names:
            logger.debug(f"Made filename unique: {base_path.name} -> {new_name}")
            return new_path

        counter += 1

        # Safety limit
        if counter > 9999:
            # Fallback to timestamp-based name
            timestamp_name = generate_datetime_name(metadata, extension)
            new_path = parent / timestamp_name
            if str(new_path) not in used_names:
                return new_path
            # Last resort: add counter to timestamp
            timestamp_stem = Path(timestamp_name).stem
            counter = 1
            while True:
                new_name = f"{timestamp_stem}_{counter:03d}{extension}"
                new_path = parent / new_name
                if str(new_path) not in used_names:
                    return new_path
                counter += 1


def generate_names(
    photos_to_paths: Dict[PhotoMetadata, Path],
    destination_root: Path
) -> Dict[PhotoMetadata, Path]:
    """
    Generate meaningful filenames for photos.

    Preserves meaningful filenames, generates date-time names for others.
    Ensures all filenames are unique.

    Args:
        photos_to_paths: Dictionary mapping PhotoMetadata to destination paths (from organizer)
        destination_root: Root destination folder

    Returns:
        Dictionary mapping PhotoMetadata to final destination Path (with proper filenames)
    """
    named_photos = {}
    used_names = set()

    for metadata, date_path in photos_to_paths.items():
        original_filename = metadata.file_path.name
        stem = Path(original_filename).stem
        extension = Path(original_filename).suffix.lower()

        # Determine if filename is meaningful
        if is_meaningful_filename(stem):
            # Preserve original filename (sanitized)
            new_stem = sanitize_filename(stem)
            new_filename = new_stem + extension
        else:
            # Generate date-time based name
            new_filename = generate_datetime_name(metadata, extension)

        # Build full path
        # date_path is already relative (YYYY/MM/DD/filename), so join with destination_root
        date_folder = date_path.parent
        new_path = destination_root / date_folder / new_filename

        # Ensure uniqueness
        final_path = ensure_unique_filename(new_path, metadata, used_names)
        used_names.add(str(final_path))

        named_photos[metadata] = final_path

        if final_path.name != original_filename:
            logger.debug(f"Renamed: {original_filename} -> {final_path.name}")

    logger.info(f"Generated names for {len(named_photos)} photos")
    return named_photos
