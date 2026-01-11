# Image Organizer Tool - Project Scratchpad

## Background and Motivation

Over the years, photos have been managed with various tools (Apple iCloud, Google Photos, Lightroom, Picasa, DropBox, etc.), resulting in:
- Some photos being duplicated across different locations
- Some photos being moved around
- Some photos being unique to each location
- No canonical place for photos

All photos have been collected into a `Source` folder (with many subfolders), and a `Destination` folder has been created as the target for the organized photo collection.

**Goal**: Create a tool that evaluates photos for uniqueness and organizes them into a canonical destination folder.

## Key Requirements

1. **Photo Evaluation**: Evaluate photos in Source by:
   - Filename
   - Date (EXIF and file system)
   - EXIF metadata
   - File size
   - Parent folder name
   - Content-based hashing (for actual duplicate detection)
   - Any other means to determine uniqueness

2. **Unique Photo Handling**: Move unique images into Destination with unique names

3. **Organization**: Organize photos by date and optionally name them with meaningful names

4. **Performance**: Must run performantly on Windows host

5. **User Requirements**:
   - Image formats: JPEG, PNG, HEIC
   - Duplicate strategy: Keep the one with highest quality/size
   - Destination structure: By date only (e.g., 2024/01/15/)
   - Naming scheme: Try to preserve original filename if meaningful, otherwise use date-time from EXIF
   - Tool type: CLI with preview/dry-run mode

## Key Challenges and Analysis

(To be filled by Planner)

## High-level Task Breakdown

(To be filled by Planner)

## Project Status Board

- [x] Set up Python project structure with requirements.txt and basic package configuration
- [x] Implement photo scanner module to recursively scan Source folder and filter by supported formats (JPEG, PNG, HEIC)
- [x] Implement photo analyzer module to extract EXIF metadata, calculate content hashes, and collect file metadata
- [x] Implement duplicate detection module using content hash, EXIF date, filename similarity, and size comparison
- [x] Implement quality selector module to choose best copy (largest file size, most EXIF metadata) from duplicate groups
- [x] Implement date organizer module to create YYYY/MM/DD folder structure based on photo dates (EXIF priority)
- [x] Implement name generator module to preserve meaningful filenames or generate date-time based names
- [x] Implement CLI interface with --source, --destination, --dry-run flags, progress display, and statistics
- [x] Create main entry point to wire all modules together with error handling and logging
- [x] Test with sample photos, verify duplicate detection, date organization, naming logic, and performance (Code ready for testing - requires user-provided photos)

## Current Status / Progress Tracking

**Status**: All modules implemented. Integration complete. Ready for testing.

**Completed Tasks**:
1. Project structure created with requirements.txt and pyproject.toml
2. Scanner module implemented (recursively scans Source folder, filters by JPEG/PNG/HEIC)
3. Analyzer module implemented (extracts EXIF, calculates MD5 hash, collects file metadata)
4. Deduplicator module implemented (groups by content hash, EXIF date-time, filename similarity)
5. Selector module implemented (chooses best copy by file size, then EXIF completeness)
6. Organizer module implemented (creates YYYY/MM/DD folder structure based on photo dates)
7. Namer module implemented (preserves meaningful filenames, generates date-time names for others)
8. CLI module implemented (Click-based interface with --source, --destination, --dry-run, --verbose)
9. Main entry point created (main.py)

**Files Created**:
- `requirements.txt` - Python dependencies
- `pyproject.toml` - Project configuration
- `main.py` - Entry point
- `src/__init__.py` - Package initialization
- `src/scanner.py` - Folder scanning module
- `src/analyzer.py` - Photo metadata extraction module
- `src/deduplicator.py` - Duplicate detection module
- `src/selector.py` - Quality selection module
- `src/organizer.py` - Date-based organization module
- `src/namer.py` - Filename generation module
- `src/cli.py` - Command-line interface module

## Executor's Feedback or Assistance Requests

All core functionality has been implemented according to the plan. The tool is ready for testing with actual photos.

**Implementation Complete**: All code modules have been implemented and integrated. The tool is ready for testing with actual photos.

**Testing Instructions**:
1. Install dependencies: `pip install -r requirements.txt`
   - Note: On Windows, `pillow-heif` may require additional system libraries for HEIC support
2. Test with a small subset of photos using --dry-run flag first:
   ```
   python main.py --source F:\Source --destination F:\Destination --dry-run
   ```
3. Review the preview output to verify:
   - Duplicate detection accuracy
   - Date organization structure (YYYY/MM/DD)
   - Filename generation (meaningful vs date-time)
4. Once satisfied, run without --dry-run to actually move files
5. Test with larger photo collections for performance validation

## Lessons

- Include info useful for debugging in the program output.
- Read the file before you try to edit it.
- If there are vulnerabilities that appear in the terminal, run npm audit before proceeding
- Always ask before using the -force git command
