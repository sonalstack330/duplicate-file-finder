# Duplicate File Finder & Storage Cleanup Tool

A Python command-line tool that scans directories for duplicate files using
content hashing, reports how much storage is being wasted, and safely removes
redundant copies freeing up disk space with a single command.

Files are compared by actual content (via MD5/SHA1/SHA256 hashing), not just filename, so it catches duplicates even when they've been renamed or copied into different folders.

The tool uses a two-phase detection strategy first grouping files by size, then only hashing files that share a size with another
file to avoid unnecessarily hashing every single file in large directories, keeping scans fast even across tens of thousands of files.

Cleanup can be done two ways: permanently deleting duplicates, or moving them to a local recycle bin folder first, so nothing is lost if the tool ever flags something unexpectedly. Every scan can also be logged to a .csv or .txt file for a persistent record of what was found and cleaned.

The command-line version (`duplicate_finder.py`) is built for automation and
scripting — usable in scheduled jobs or piped into other tools. The GUI
version (`duplicate_finder_gui.py`) wraps the same core logic in a Tkinter
desktop app with a folder picker, sortable results (biggest space-wasters
first), and single-click file selection with a detail panel — designed for
anyone who'd rather not touch a terminal. Both share one core detection
engine, so there's a single source of truth for the actual duplicate-finding
logic.

## Features

- **Recursive directory scanning** — finds duplicates in nested subfolders too
- **Content-based detection** — uses MD5/SHA1/SHA256 hashing, so it catches
  duplicates even if filenames differ
- **Size pre-filtering** — skips hashing files that couldn't possibly match,
  making large scans much faster
- **Human-readable reports** — shows duplicate groups sorted by wasted
  space, biggest first
- **Two safe cleanup modes** — permanently delete, or move to a local
  `recyclebin` folder for easy recovery
- **Scan logging** — save results to `.csv` or `.txt` for a record of every
  scan
- **CLI tool** — built with `argparse`, ideal for scripting and automation
- **GUI app** — Tkinter desktop app with folder picker, sortable results,
  and a detail panel showing full file paths on click
- **Single core engine** — both CLI and GUI import their duplicate-finding
  logic from the same source, so there's no duplicated code between them

## Tech Stack

- Python 3
- `os` — directory traversal and file system operations
- `hashlib` — file content hashing (MD5 / SHA1 / SHA256)
- `argparse` — command-line interface
- `shutil` — safely moving files to the recycle bin folder
- `csv` / `datetime` — scan logging with timestamps
- `tkinter` — graphical desktop interface
- `collections.defaultdict` — grouping files efficiently

## Project Structure

duplicate_finder.py # Core detection logic + CLI tool
duplicate_finder_gui.py # Tkinter GUI, imports core logic from duplicate_finder.py

No external dependencies — everything runs with a standard Python 3
installation.

## Installation

```bash
git clone https://github.com/sonalstack330/duplicate-file-finder.git
cd duplicate-file-finder
```

## Usage — Command Line

**Scan a folder and see a report (no files touched):**
```bash
python duplicate_finder.py "C:/path/to/folder"
```

**Scan and permanently delete duplicates:**
```bash
python duplicate_finder.py "C:/path/to/folder" --delete
```

**Scan and move duplicates to a local recycle bin instead:**
```bash
python duplicate_finder.py "C:/path/to/folder" --recycle
```

**Use a stronger hash algorithm:**
```bash
python duplicate_finder.py "C:/path/to/folder" --hash sha256
```

**Ignore small files (e.g., skip anything under 1KB):**
```bash
python duplicate_finder.py "C:/path/to/folder" --min-size 1024
```

**Save scan results to a log file:**
```bash
python duplicate_finder.py "C:/path/to/folder" --log csv
```

**See all available options:**
```bash
python duplicate_finder.py --help
```

## Usage — GUI

```bash
python duplicate_finder_gui.py
```

1. Click **Browse...** and select a folder to scan
2. Click **Scan** — duplicate groups appear sorted by wasted space, biggest first
3. Click any file to see its full path in the detail panel below the list
4. Select a duplicate and choose **Move Selected to Recyclebin** (safe, reversible)
   or **Delete Selected Permanently** (irreversible)

## Example Output (CLI)

Scanning complete — 466 files found.
Hashing 287 candidate files...

Group #1 - 110.6 MB each, 110.6 MB wasted
[KEEP] OpenJDK25U-jdk_x64_windows_hotspot_25.0.3_9 (1).msi
DUPLICATE OpenJDK25U-jdk_x64_windows_hotspot_25.0.3_9.msi

Total space wasted by duplicates: 123.3 MB

Move all duplicate files listed above to 'recyclebin'? (yes/no): yes
Moved to recyclebin: OpenJDK25U-jdk_x64_windows_hotspot_25.0.3_9.msi -> recyclebin...
Total space moved to recyclebin: 123.3 MB


## How It Works

1. Walks the target directory recursively, grouping files by size
2. Only files sharing a size with another file get hashed (avoids unnecessary
   hashing of clearly-unique files)
3. Files with identical hashes are grouped as duplicates
4. Groups are sorted by wasted space, so the biggest storage wins show up first
5. One file per group is kept; the rest are flagged as redundant
6. On confirmation, redundant files are deleted or moved to `recyclebin`, and
   space freed is reported

## Disclaimer

Permanent deletion (`--delete`) is irreversible. The recycle bin mode
(`--recycle`) is the safer default — files are moved, not destroyed, and can
be manually restored. Always review the report before confirming any
cleanup action.

## License

MIT

Want me to walk you through updating this in PyCharm and committing it, or do you have it from here?




