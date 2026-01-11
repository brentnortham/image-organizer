"""CLI interface module - command-line arguments and user interaction."""

import sys
import os
import shutil
from pathlib import Path
from typing import Optional
import logging
from multiprocessing import Pool, cpu_count

import click
from tqdm import tqdm

from src.scanner import scan_folder
from src.analyzer import analyze_photo
from src.deduplicator import detect_duplicates
from src.selector import select_unique_photos
from src.organizer import organize_by_date
from src.namer import generate_names

logger = logging.getLogger(__name__)


def _analyze_photo_wrapper(file_path: Path):
    """
    Wrapper function for analyze_photo to handle errors in multiprocessing.

    Returns None if analysis fails, otherwise returns PhotoMetadata object.
    """
    try:
        return analyze_photo(file_path)
    except Exception as e:
        logger.error(f"Failed to analyze {file_path}: {e}")
        return None


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


def preview_changes(photos_to_paths: dict, source_root: Path, destination_root: Path, max_preview: int = 50, audit_file: Optional[Path] = None):
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

    # Write audit file if requested
    if audit_file:
        try:
            with open(audit_file, 'w', encoding='utf-8') as f:
                f.write(f"Image Organizer Audit Log\n")
                f.write(f"{'='*60}\n")
                f.write(f"Total files: {len(photos_to_paths):,}\n")
                f.write(f"{'='*60}\n\n")

                # Write all files
                for metadata, dest_path in photos_to_paths.items():
                    source_rel = metadata.file_path.relative_to(source_root)
                    dest_rel = dest_path.relative_to(destination_root)
                    f.write(f"{source_rel}  ->  {dest_rel}\n")

            print(f"\n  Full file list saved to: {audit_file}")
        except Exception as e:
            logger.warning(f"Failed to write audit file: {e}")

    print("="*60 + "\n")


def write_preview_file(photos_to_paths: dict, source_root: Path, destination_root: Path, preview_file: Path, operation: str):
    """Write preview file showing what will happen."""
    try:
        with open(preview_file, 'w', encoding='utf-8') as f:
            f.write(f"Image Organizer Preview - Files to be {operation}d\n")
            f.write(f"{'='*60}\n")
            f.write(f"Total files: {len(photos_to_paths):,}\n")
            f.write(f"Operation: {operation}\n")
            f.write(f"{'='*60}\n\n")

            # Write all files
            for metadata, dest_path in photos_to_paths.items():
                source_rel = metadata.file_path.relative_to(source_root)
                dest_rel = dest_path.relative_to(destination_root)
                f.write(f"{source_rel}  ->  {dest_rel}\n")

        return True
    except Exception as e:
        logger.error(f"Failed to write preview file: {e}")
        return False


def confirm_proceed(preview_file: Path, copy_mode: bool) -> bool:
    """Prompt user to confirm before proceeding."""
    print("\n" + "="*60)
    print("CONFIRMATION REQUIRED")
    print("="*60)
    print(f"A preview file has been generated: {preview_file}")
    print(f"Please review the file to see what will happen.")
    operation = "COPY" if copy_mode else "MOVE"
    print(f"\nThis will {operation} files from source to destination.")
    print("="*60)

    while True:
        response = input("\nDo you want to proceed? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please enter 'yes' or 'no'")


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
@click.option(
    '--skip-filename-similarity',
    is_flag=True,
    default=False,
    help='Skip filename similarity detection (much faster for large datasets, but may miss some duplicates)'
)
@click.option(
    '--workers',
    type=int,
    default=None,
    help='Number of parallel workers for photo analysis (default: number of CPU cores)'
)
@click.option(
    '--copy',
    is_flag=True,
    default=False,
    help='Copy files instead of moving them (preserves originals in source folder)'
)
@click.option(
    '--audit-file',
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help='Save full file list to specified file (useful for dry-run audit)'
)
def main(source: Path, destination: Path, dry_run: bool, verbose: bool, skip_filename_similarity: bool, workers: Optional[int], copy: bool, audit_file: Optional[Path]):
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
    if dry_run:
        print(f"Mode:        DRY-RUN (preview only)")
    else:
        print(f"Mode:        LIVE ({'copy' if copy else 'move'} files)")
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

        # Determine number of workers
        if workers is None:
            workers = cpu_count()

        # Use multiprocessing for parallel analysis
        photos = []
        if workers > 1 and len(image_files) > 10:  # Only use multiprocessing for larger datasets
            print(f"  Using {workers} parallel workers...")
            with Pool(processes=workers) as pool:
                # Use imap for progress bar support
                results = list(tqdm(
                    pool.imap(_analyze_photo_wrapper, image_files),
                    total=len(image_files),
                    desc="Analyzing",
                    unit="photo"
                ))
            # Filter out None results (failed analyses)
            photos = [r for r in results if r is not None]
        else:
            # Sequential processing for small datasets or single worker
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
        # Auto-skip filename similarity for very large datasets (>5000 photos) for performance
        if not skip_filename_similarity and len(photos) > 5000:
            print(f"  Large dataset detected ({len(photos):,} photos). Skipping filename similarity detection for performance.")
            skip_filename_similarity = True
        duplicate_groups = detect_duplicates(photos, skip_filename_similarity=skip_filename_similarity)
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
            preview_changes(photos_to_paths, source, destination, audit_file=audit_file)
            print("Dry-run complete. Use without --dry-run to actually move/copy files.")
        else:
            # Generate preview file and wait for user confirmation
            operation = "copied" if copy else "moved"
            # Create preview file in destination directory (create directory if needed)
            destination.mkdir(parents=True, exist_ok=True)
            preview_file = destination / "PREVIEW_FILE.txt"

            print(f"\nGenerating preview file: {preview_file}")
            if not write_preview_file(photos_to_paths, source, destination, preview_file, operation):
                print("ERROR: Failed to generate preview file. Aborting.")
                sys.exit(1)

            if not confirm_proceed(preview_file, copy):
                print("\nOperation cancelled by user.")
                sys.exit(0)

            print("\nProceeding with file operation...\n")
            # Step 7: Move or copy files
            operation = "copying" if copy else "moving"
            print(f"Step 7: {operation.capitalize()} files to destination...")

            # Create destination directories
            directories_to_create = set()
            for dest_path in photos_to_paths.values():
                directories_to_create.add(dest_path.parent)

            for dir_path in tqdm(directories_to_create, desc="Creating directories", unit="dir"):
                dir_path.mkdir(parents=True, exist_ok=True)

            # Move or copy files
            processed_count = 0
            error_count = 0

            for metadata, dest_path in tqdm(photos_to_paths.items(), desc=f"{operation.capitalize()} files", unit="file"):
                try:
                    # Create parent directory if needed
                    dest_path.parent.mkdir(parents=True, exist_ok=True)

                    # Copy or move file
                    if copy:
                        shutil.copy2(metadata.file_path, dest_path)
                    else:
                        metadata.file_path.replace(dest_path)
                    processed_count += 1

                except Exception as e:
                    logger.error(f"Failed to {operation} {metadata.file_path} to {dest_path}: {e}")
                    error_count += 1

            operation_past = "copied" if copy else "moved"
            print(f"\nCompleted: {processed_count:,} files {operation_past}, {error_count:,} errors")
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
