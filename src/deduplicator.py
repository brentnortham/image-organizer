"""Duplicate detection module - groups photos by content hash, EXIF date, filename similarity, etc."""

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import logging
import re

from src.analyzer import PhotoMetadata

logger = logging.getLogger(__name__)

# Time window for considering photos as potential duplicates (seconds)
# Photos taken within this window with same camera are likely duplicates
TIME_WINDOW_SECONDS = 2


def group_by_content_hash(photos: List[PhotoMetadata]) -> Dict[str, List[PhotoMetadata]]:
    """
    Group photos by content hash (exact duplicates).

    Args:
        photos: List of PhotoMetadata objects

    Returns:
        Dictionary mapping hash to list of photos with that hash
    """
    groups = defaultdict(list)

    for photo in photos:
        if photo.content_hash:
            groups[photo.content_hash].append(photo)

    return dict(groups)


def group_by_exif_datetime(photos: List[PhotoMetadata]) -> Dict[Tuple[datetime, Optional[str], Optional[str]], List[PhotoMetadata]]:
    """
    Group photos by EXIF date-time and camera info.

    Photos with same date-time and camera are likely the same photo
    (even if file size differs due to compression/processing).

    Args:
        photos: List of PhotoMetadata objects

    Returns:
        Dictionary mapping (datetime, make, model) to list of photos
    """
    groups = defaultdict(list)

    for photo in photos:
        if photo.date_taken:
            # Round to nearest second for grouping
            key = (
                photo.date_taken.replace(microsecond=0),
                photo.camera_make,
                photo.camera_model,
            )
            groups[key].append(photo)

    return dict(groups)


def is_similar_filename(name1: str, name2: str) -> bool:
    """
    Check if two filenames are likely the same photo (with different names).

    Looks for patterns like:
    - IMG_1234.jpg vs IMG_1234_edited.jpg
    - DSC01234.jpg vs DSC01234-2.jpg
    - photo.jpg vs photo (1).jpg

    Args:
        name1: First filename (without extension)
        name2: Second filename (without extension)

    Returns:
        True if filenames appear similar
    """
    # Remove common suffixes/prefixes
    suffixes_to_remove = ['_edited', '_copy', '_1', '_2', '-1', '-2', ' (1)', ' (2)']

    base1 = name1.lower()
    base2 = name2.lower()

    for suffix in suffixes_to_remove:
        if base1.endswith(suffix):
            base1 = base1[:-len(suffix)]
        if base2.endswith(suffix):
            base2 = base2[:-len(suffix)]

    # Extract potential base names (numbers after common prefixes)
    pattern = r'^(img_|dsc|photo|pic|image|img)(\d+)'
    match1 = re.match(pattern, base1)
    match2 = re.match(pattern, base2)

    if match1 and match2:
        # Same prefix and number -> likely same photo
        return match1.group(2) == match2.group(2)

    # Check if base names are similar (one contains the other)
    if base1 in base2 or base2 in base1:
        if len(base1) > 5 and len(base2) > 5:  # Avoid matching very short names
            return True

    return False


def group_by_filename_similarity(photos: List[PhotoMetadata]) -> Dict[str, List[PhotoMetadata]]:
    """
    Group photos with similar filenames.

    Args:
        photos: List of PhotoMetadata objects

    Returns:
        Dictionary mapping a representative filename to list of similar photos
    """
    groups = defaultdict(list)
    processed = set()

    for i, photo1 in enumerate(photos):
        if i in processed:
            continue

        # Use first photo's stem as group key
        group_key = photo1.file_path.stem
        groups[group_key].append(photo1)
        processed.add(i)

        # Find similar filenames
        name1 = photo1.file_path.stem
        for j, photo2 in enumerate(photos[i+1:], start=i+1):
            if j in processed:
                continue

            name2 = photo2.file_path.stem
            if is_similar_filename(name1, name2):
                groups[group_key].append(photo2)
                processed.add(j)

    # Only return groups with multiple photos (potential duplicates)
    return {k: v for k, v in groups.items() if len(v) > 1}


def detect_duplicates(photos: List[PhotoMetadata], skip_filename_similarity: bool = False) -> Dict[str, List[PhotoMetadata]]:
    """
    Detect duplicate photos using multiple methods.

    Combines content hash, EXIF date-time, and filename similarity
    to find groups of duplicate photos.

    Args:
        photos: List of PhotoMetadata objects
        skip_filename_similarity: If True, skip filename similarity detection (much faster for large datasets)

    Returns:
        Dictionary mapping group IDs to lists of duplicate photos
        Each group ID is based on the detection method used
    """
    duplicate_groups = {}
    group_id_counter = 0

    # Method 1: Group by content hash (exact duplicates)
    hash_groups = group_by_content_hash(photos)
    for hash_val, group in hash_groups.items():
        if len(group) > 1:
            duplicate_groups[f"hash_{hash_val[:8]}"] = group
            logger.debug(f"Found {len(group)} exact duplicates by hash: {hash_val[:8]}")

    # Method 2: Group by EXIF date-time and camera
    exif_groups = group_by_exif_datetime(photos)
    for key, group in exif_groups.items():
        if len(group) > 1:
            # Filter out already grouped photos (by content hash)
            # Only consider if they're likely different files
            already_grouped = set()
            for existing_group in duplicate_groups.values():
                already_grouped.update(p.file_path for p in existing_group)

            ungrouped = [p for p in group if p.file_path not in already_grouped]
            if len(ungrouped) > 1:
                group_id_counter += 1
                duplicate_groups[f"exif_{group_id_counter}"] = ungrouped
                logger.debug(f"Found {len(ungrouped)} potential duplicates by EXIF date-time")

    # Method 3: Group by filename similarity (skip if requested or dataset is very large)
    if not skip_filename_similarity:
        # Only for photos not already grouped
        already_grouped_paths = set()
        for group in duplicate_groups.values():
            already_grouped_paths.update(p.file_path for p in group)

        ungrouped_photos = [p for p in photos if p.file_path not in already_grouped_paths]
        filename_groups = group_by_filename_similarity(ungrouped_photos)
        for key, group in filename_groups.items():
            if len(group) > 1:
                group_id_counter += 1
                duplicate_groups[f"filename_{group_id_counter}"] = group
                logger.debug(f"Found {len(group)} potential duplicates by filename similarity")
    else:
        logger.info("Skipping filename similarity detection for performance")

    logger.info(f"Detected {len(duplicate_groups)} duplicate groups")
    return duplicate_groups
