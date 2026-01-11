"""Quality selector module - chooses best copy from duplicate groups based on size and EXIF completeness."""

from typing import List, Set
import logging

from src.analyzer import PhotoMetadata

logger = logging.getLogger(__name__)


def count_exif_fields(metadata: PhotoMetadata) -> int:
    """
    Count number of EXIF fields present in metadata.

    Used as tie-breaker when file sizes are similar.

    Args:
        metadata: PhotoMetadata object

    Returns:
        Number of EXIF fields
    """
    return len(metadata.exif_data)


def select_best_photo(photos: List[PhotoMetadata]) -> PhotoMetadata:
    """
    Select the best quality photo from a list of duplicates.

    Selection criteria (in order):
    1. Largest file size (primary - indicates higher quality/less compression)
    2. Most EXIF metadata (tie-breaker - indicates original vs processed copy)

    Args:
        photos: List of PhotoMetadata objects (duplicate photos)

    Returns:
        PhotoMetadata object for the best photo to keep
    """
    if not photos:
        raise ValueError("Cannot select from empty list")

    if len(photos) == 1:
        return photos[0]

    # Sort by size (descending), then by EXIF field count (descending)
    sorted_photos = sorted(
        photos,
        key=lambda p: (p.size, count_exif_fields(p)),
        reverse=True
    )

    best = sorted_photos[0]

    logger.debug(
        f"Selected best photo from {len(photos)} duplicates: "
        f"{best.file_path.name} (size={best.size}, exif_fields={count_exif_fields(best)})"
    )

    return best


def select_unique_photos(
    all_photos: List[PhotoMetadata],
    duplicate_groups: dict
) -> Set[PhotoMetadata]:
    """
    Select unique photos to keep, choosing the best from each duplicate group.

    Args:
        all_photos: All PhotoMetadata objects
        duplicate_groups: Dictionary mapping group IDs to lists of duplicate photos

    Returns:
        Set of PhotoMetadata objects to keep (unique photos + best from each duplicate group)
    """
    photos_to_keep = set()
    photos_to_exclude = set()

    # For each duplicate group, select the best one
    for group_id, group in duplicate_groups.items():
        best_photo = select_best_photo(group)
        photos_to_keep.add(best_photo)

        # Mark others for exclusion
        for photo in group:
            if photo != best_photo:
                photos_to_exclude.add(photo)

    # Add all photos that are not in any duplicate group
    for photo in all_photos:
        if photo not in photos_to_exclude:
            photos_to_keep.add(photo)

    logger.info(
        f"Selected {len(photos_to_keep)} unique photos from {len(all_photos)} total "
        f"({len(photos_to_exclude)} duplicates to exclude)"
    )

    return photos_to_keep
