import os
import sys
import argparse
import hashlib
from collections import defaultdict


def compute_file_hash(filepath, algo="md5", chunk_size=8192):
    """Return the content hash of a file, reading it in chunks."""
    hasher = hashlib.new(algo)
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def find_duplicates(root_dir, algo="md5", min_size=0):
    """Find duplicate files by grouping by size first, then hashing only likely matches."""
    size_map = defaultdict(list)

    # Step 1: group files by size (cheap — no reading file contents)
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for name in filenames:
            filepath = os.path.join(dirpath, name)
            try:
                size = os.path.getsize(filepath)
            except OSError:
                continue
            if size >= min_size:
                size_map[size].append(filepath)

    # Step 2: only hash files that share a size with another file
    hash_map = defaultdict(list)
    candidates = [f for files in size_map.values() if len(files) > 1 for f in files]

    for filepath in candidates:
        file_hash = compute_file_hash(filepath, algo)
        hash_map[file_hash].append(filepath)

    return {h: paths for h, paths in hash_map.items() if len(paths) > 1}  #at function level, after the loop

def format_size(num_bytes):
    """Convert raw byte count into human-readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024:
            return f"{num_bytes} {unit}"
        num_bytes /= 1024
    return f"{num_bytes} PB"

def report(duplicates):
    """Print a report of duplicate files and total wasted space"""
    total_wasted = 0
    group_num = 1

    for file_hash, paths in duplicates.items():
        size = os.path.getsize(paths[0])
        wasted = size * (len(paths) - 1)
        total_wasted += wasted

        print(f"Group #{group_num} - {format_size(size)} each")
        for i, path in enumerate(paths):
            tag = "[KEEP]" if i == 0 else "DUPLICATE"
            print(f" {tag} {path}")
        print()
        group_num += 1

    print(f"Total space wasted by duplicates: {format_size(total_wasted)}")

def clean_duplicates(duplicates):
    """Delete all duplicate files in each group, keeping only the first one."""
    total_deleted = 0

    for file_hash, paths in duplicates.items():
        size = os.path.getsize(paths[0])
        for path in paths[1:]:
            try:
                os.remove(path)
                total_deleted += size
                print(f"Deleted {path}")
            except OSError as e:
                print(f"Error deleting {path}: {e}")

    print(f"\nTotal space freed: {format_size(total_deleted)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find and remove duplicate files in a directory.")
    parser.add_argument("directory", help="Folder to scan for duplicates")
    parser.add_argument("--hash", default="md5", choices=["md5", "sha1", "sha256"],
                         help="Hashing algorithm to use (default: md5)")
    parser.add_argument("--min-size", type=int, default=0,
                         help="Ignore files smaller than this size in bytes")
    parser.add_argument("--delete", action="store_true",
                         help="Delete duplicates after showing the report")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory.")
        sys.exit(1)

    dupes = find_duplicates(args.directory, algo=args.hash, min_size=args.min_size)

    if not dupes:
        print("No duplicate files found.")
        sys.exit(0)

    report(dupes)

    if args.delete:
        confirm = input("\nDelete all duplicate files listed above? (yes/no): ")
        if confirm.strip().lower() == "yes":
            clean_duplicates(dupes)
        else:
            print("Cancelled — no files deleted.")
    else:
        print("\nRun again with --delete to remove these files.")