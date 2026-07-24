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




