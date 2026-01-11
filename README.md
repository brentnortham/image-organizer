# Image Organizer Tool

A Python CLI tool that intelligently organizes photos by detecting duplicates, preserving the best quality copies, and organizing them by date with meaningful filenames.

## Features

- **Duplicate Detection**: Uses multiple methods to detect duplicates:
  - Content hash (MD5) for exact duplicates
  - EXIF date-time and camera info for same photo with different processing
  - Filename similarity for renamed copies
- **Quality Selection**: Keeps the best quality copy (largest file size, most EXIF metadata)
- **Date Organization**: Organizes photos by date in `YYYY/MM/DD` folder structure
- **Smart Naming**: Preserves meaningful filenames, generates date-time names for camera-generated filenames
- **Dry-Run Mode**: Preview changes before actually moving files
- **Format Support**: JPEG, PNG, HEIC

## Requirements

- Python 3.9+
- Windows, Linux (including WSL), or macOS

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python main.py --source F:\Source --destination F:\Destination
```

### Dry-Run (Preview Mode)

Preview what changes would be made without actually moving files:

```bash
python main.py --source F:\Source --destination F:\Destination --dry-run
```

### Verbose Output

Enable detailed logging:

```bash
python main.py --source F:\Source --destination F:\Destination --verbose
```

### Command-Line Options

- `--source` (required): Source folder containing photos to organize
- `--destination` (required): Destination folder for organized photos
- `--dry-run` (flag): Preview changes without moving files
- `--verbose` / `-v` (flag): Enable verbose output
- `--workers` (optional): Number of parallel workers for photo analysis (default: number of CPU cores)
- `--skip-filename-similarity` (flag): Skip filename similarity detection (faster for large datasets, may miss some duplicates)

## How It Works

1. **Scan**: Recursively scans the source folder for image files (JPEG, PNG, HEIC)
2. **Analyze**: Extracts EXIF metadata, calculates content hashes, collects file metadata
3. **Detect Duplicates**: Groups photos using content hash, EXIF date-time, and filename similarity
4. **Select Best**: Chooses the best quality copy from each duplicate group (largest file size)
5. **Organize**: Creates date-based folder structure (`YYYY/MM/DD`)
6. **Rename**: Preserves meaningful filenames or generates date-time based names
7. **Move**: Moves unique photos to the destination folder

## Destination Structure

Photos are organized in the destination folder as:

```
Destination/
├── 2024/
│   ├── 01/
│   │   ├── 15/
│   │   │   ├── 2024-01-15_14-30-25.jpg
│   │   │   └── meaningful-photo-name.jpg
│   │   └── 20/
│   │       └── ...
```

## Notes

- **HEIC Support**: Requires `pillow-heif`. On Linux, install `libheif-dev` system library. On Windows, additional system libraries may be needed.
- **Performance**:
  - Uses multiprocessing for parallel photo analysis (defaults to number of CPU cores)
  - Content hashing is memory-efficient (processes files in chunks)
  - Filename similarity detection is automatically skipped for large datasets (>5000 photos)
- **Error Handling**: Corrupted files or files without EXIF data are handled gracefully
- **Uniqueness**: Filenames are automatically made unique if conflicts occur (adds `_001`, `_002`, etc.)
- **Platform Support**: Tested on Windows and Linux (WSL). Works on macOS as well.

## Example Output

```
Image Organizer Tool
============================================================
Source:      F:\Source
Destination: F:\Destination
Mode:        DRY-RUN (preview only)
============================================================

Step 1: Scanning source folder...
Found 1,234 image files

Step 2: Analyzing photos (extracting metadata, calculating hashes)...
Successfully analyzed 1,234 photos

Step 3: Detecting duplicates...
Found 45 duplicate groups

Step 4: Selecting best copies from duplicate groups...
Selected 1,145 unique photos to keep

Step 5: Organizing photos by date...
Step 6: Generating filenames...

============================================================
ORGANIZATION STATISTICS
============================================================
Total photos scanned:     1,234
Duplicate groups found:   45
Total duplicate photos:   89
Unique photos to keep:    1,145
Photos to be excluded:    89
============================================================
```
