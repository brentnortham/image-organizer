"""CLI interface module - command-line arguments and user interaction."""

import sys
from pathlib import Path
from typing import Optional
import logging

import click
from tqdm import tqdm

from src.scanner import scan_folder
from src.analyzer import analyze_photo
from src.deduplicator import detect_duplicates
from src.selector import select_unique_photos
from src.organizer import organize_by_date
from src.namer import generate_names

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def print_statistics(
    total_photos: int,
    duplicate_groups: dict,
    photos_to_keep: set,
    photos_to_paths: dict
):
    """Print statistics about the organization process."""
    total_duplicates = sum(len(group) - 1 for group in duplicate_groups.values())
    unique_photos = len(photos_to_keep)

    print("\n" + "="*60)
    print("ORGANIZATION STATISTICS")
    print("="*60)
    print(f"Total photos scanned:     {total_photos:,}")
    print(f"Duplicate groups found:   {len(duplicate_groups):,}")
    print(f"Total duplicate photos:   {total_duplicates:,}")
    print(f"Unique photos to keep:    {unique_photos:,}")
    print(f"Photos to be excluded:    {total_duplicates:,}")
    print("="*60 + "\n")


def preview_changes(photos_to_paths: dict, source_root: Path, destination_root: Path, max_preview: int = 50):
    """Preview what changes would be made (for dry-run mode)."""
    print("\n" + "="*60)
    print("PREVIEW (DRY-RUN MODE - No files will be moved)")
    print("="*60)

    count = 0
    for metadata, dest_path in list(photos_to_paths.items())[:max_preview]:
        source_rel = metadata.file_path.relative_to(source_root)
        dest_rel = dest_path.relative_to(destination_root)
        print(f"  {source_rel}  ->  {dest_rel}")
        count += 1

    if len(photos_to_paths) > max_preview:
        remaining = len(photos_to_paths) - max_preview
        print(f"\n  ... and {remaining:,} more files")

    print("="*60 + "\n")


@click.command()
@click.option(
    '--source',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help='Source folder containing photos to organize'
)
@click.option(
    '--destination',
    type=click.Path(exists=False, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help='Destination folder for organized photos'
)
@click.option(
    '--dry-run',
    is_flag=True,
    default=False,
    help='Preview changes without moving files'
)
@click.option(
    '--verbose',
    '-v',
    is_flag=True,
    default=False,
    help='Enable verbose output'
)
def main(source: Path, destination: Path, dry_run: bool, verbose: bool):
    """
    Image Organizer Tool - Organize photos by detecting duplicates and organizing by date.

    This tool scans photos in the source folder, detects duplicates using multiple
    methods (content hash, EXIF date, filename similarity), keeps the best quality
    copies, and organizes them by date in the destination folder.
    """
    setup_logging(verbose)

    print("Image Organizer Tool")
    print("="*60)
    print(f"Source:      {source}")
    print(f"Destination: {destination}")
    print(f"Mode:        {'DRY-RUN (preview only)' if dry_run else 'LIVE (will move files)'}")
    print("="*60 + "\n")

    try:
        # Step 1: Scan folder
        print("Step 1: Scanning source folder...")
        image_files = scan_folder(source)
        print(f"Found {len(image_files):,} image files\n")

        if not image_files:
            print("No image files found. Exiting.")
            return

        # Step 2: Analyze photos
        print("Step 2: Analyzing photos (extracting metadata, calculating hashes)...")
        photos = []
        for file_path in tqdm(image_files, desc="Analyzing", unit="photo"):
            try:
                metadata = analyze_photo(file_path)
                photos.append(metadata)
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
                continue
        print(f"Successfully analyzed {len(photos):,} photos\n")

        # Step 3: Detect duplicates
        print("Step 3: Detecting duplicates...")
        duplicate_groups = detect_duplicates(photos)
        print(f"Found {len(duplicate_groups):,} duplicate groups\n")

        # Step 4: Select unique photos
        print("Step 4: Selecting best copies from duplicate groups...")
        photos_to_keep = select_unique_photos(photos, duplicate_groups)
        print(f"Selected {len(photos_to_keep):,} unique photos to keep\n")

        # Step 5: Organize by date
        print("Step 5: Organizing photos by date...")
        # Create temporary mapping for organizer (will be updated by namer)
        temp_mapping = {p: None for p in photos_to_keep}
        organized = organize_by_date(temp_mapping)

        # Step 6: Generate meaningful names
        print("Step 6: Generating filenames...")
        photos_to_paths = generate_names(organized, destination)
        print(f"Generated names for {len(photos_to_paths):,} photos\n")

        # Print statistics
        print_statistics(len(photos), duplicate_groups, photos_to_keep, photos_to_paths)

        # Preview or execute
        if dry_run:
            preview_changes(photos_to_paths, source, destination)
            print("Dry-run complete. Use without --dry-run to actually move files.")
        else:
            # Step 7: Move files
            print("Step 7: Moving files to destination...")

            # Create destination directories
            directories_to_create = set()
            for dest_path in photos_to_paths.values():
                directories_to_create.add(dest_path.parent)

            for dir_path in tqdm(directories_to_create, desc="Creating directories", unit="dir"):
                dir_path.mkdir(parents=True, exist_ok=True)

            # Move files
            moved_count = 0
            error_count = 0

            for metadata, dest_path in tqdm(photos_to_paths.items(), desc="Moving files", unit="file"):
                try:
                    # Create parent directory if needed
                    dest_path.parent.mkdir(parents=True, exist_ok=True)

                    # Move file
                    metadata.file_path.replace(dest_path)
                    moved_count += 1

                except Exception as e:
                    logger.error(f"Failed to move {metadata.file_path} to {dest_path}: {e}")
                    error_count += 1

            print(f"\nCompleted: {moved_count:,} files moved, {error_count:,} errors")
            if error_count > 0:
                print("Check the log for details on errors.")

        print("\nDone!")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
