# Duplicate File Finder & Storage Cleanup Tool

A Python command-line tool that scans directories for duplicate files using
content hashing, reports how much storage is being wasted, and safely removes
redundant copies freeing up disk space with a single command.

Files are compared by actual content (via MD5/SHA1/SHA256 hashing), not just filename, so it catches duplicates even when they've been renamed or copied into different folders.

The tool uses a two-phase detection strategy first grouping files by size, then only hashing files that share a size with another file to avoid unnecessarily hashing every single file in large directories, keeping scans fast even across tens of thousands of files.



