import os
import argparse
import hashlib
from collections import defaultdict
import shutil
import csv
from datetime import datetime
import sys

#core logic

def compute_file_hash(filepath, algo="md5", chunk_size=8192):
    """Compute hash of a file using specified algorithm."""
    hasher = hashlib.new(algo)
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, IOError):
        return None

def find_duplicates(root_dir, algo="md5", min_size=0, progress_callback=None):
    """Scan a directory tree and return a dict of {hash: [list of file paths]}."""
    hash_map = defaultdict(list)

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)

            # Skip symlinks and check file size
            if os.path.islink(filepath):
                continue
            try:
                if os.path.getsize(filepath) < min_size:
                    continue
            except OSError:
                continue

            # Compute hash
            file_hash = compute_file_hash(filepath, algo=algo)
            if file_hash:
                hash_map[file_hash].append(filepath)

            # Call progress callback if provided (for GUI)
            if progress_callback:
                progress_callback(filepath)

    # Return only groups with duplicates (2+ files)
    return {h: paths for h, paths in hash_map.items() if len(paths) > 1}

def format_size(num_bytes):
    """Convert bytes to human-readable format (KB, MB, GB, etc.)."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.2f} PB"

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

def recycle_duplicates(duplicates, recycle_dir="recyclebin"):
    """Move duplicate files into a local recyclebin folder instead of deleting them."""
    os.makedirs(recycle_dir, exist_ok=True)

    total_moved = 0

    for file_hash, paths in duplicates.items():
        size = os.path.getsize(paths[0])
        for path in paths[1:]:
            filename = os.path.basename(path)
            destination = os.path.join(recycle_dir, filename)

            counter = 1
            while os.path.exists(destination):
                name, ext = os.path.splitext(filename)
                destination = os.path.join(recycle_dir, f"{name}_{counter}{ext}")
                counter += 1

            try:
                shutil.move(path, destination)
                total_moved += size
                print(f"Moved to recyclebin: {path} -> {destination}")
            except OSError as e:
                print(f"Failed to move {path}: {e}")

    print(f"\nTotal space moved to recyclebin: {format_size(total_moved)}")
    print(f"(Review '{recycle_dir}' and delete it manually once you're confident.)")

def write_log(duplicates, root_dir, log_format="csv", log_dir="logs"):
    """Write scan results to a timestamped .csv or .txt log file."""
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"scan_{timestamp}.{log_format}"
    filepath = os.path.join(log_dir, filename)

    if log_format == "csv":
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Group", "Status", "FileSize", "Path"])   # header row

            for group_num, (file_hash, paths) in enumerate(duplicates.items(), start=1):
                size = os.path.getsize(paths[0])
                for i, path in enumerate(paths):
                    status = "KEEP" if i == 0 else "DUPLICATE"
                    writer.writerow([group_num, status, format_size(size), path])

    else:  # txt format
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Duplicate File Scan Report\n")
            f.write(f"Scanned folder: {root_dir}\n")
            f.write(f"Date: {timestamp}\n")
            f.write("=" * 60 + "\n\n")

            for group_num, (file_hash, paths) in enumerate(duplicates.items(), start=1):
                size = os.path.getsize(paths[0])
                f.write(f"Group #{group_num} - {format_size(size)} each\n")
                for i, path in enumerate(paths):
                    tag = "[KEEP]" if i == 0 else "[DUPLICATE]"
                    f.write(f"   {tag} {path}\n")
                f.write("\n")

    print(f"Log written to: {filepath}")
    return filepath

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find and remove duplicate files in a directory.")
    parser.add_argument("directory", help="Folder to scan for duplicates")
    parser.add_argument("--hash", default="md5", choices=["md5", "sha1", "sha256"],
                         help="Hashing algorithm to use (default: md5)")
    parser.add_argument("--min-size", type=int, default=0,
                         help="Ignore files smaller than this size in bytes")
    parser.add_argument("--delete", action="store_true",
                         help="Delete duplicates after showing the report")
    parser.add_argument("--recycle", action="store_true",
                         help="Move duplicates to a local 'recyclebin' folder instead of deleting")
    parser.add_argument("--log", choices=["csv", "txt"], default=None,
                        help="Save scan results to a log file (csv or txt)")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory.")
        sys.exit(1)

    dupes = find_duplicates(args.directory, algo=args.hash, min_size=args.min_size)

    if not dupes:
        print("No duplicate files found.")
        sys.exit(0)

    report(dupes)

    if args.log:
        write_log(dupes, args.directory, log_format=args.log)

    if args.delete:
        confirm = input("\nPermanently delete all duplicate files listed above? (yes/no): ")
        if confirm.strip().lower() == "yes":
            clean_duplicates(dupes)
        else:
            print("Cancelled — no files deleted.")

    elif args.recycle:
        confirm = input("\nMove all duplicate files listed above to 'recyclebin'? (yes/no): ")
        if confirm.strip().lower() == "yes":
            recycle_duplicates(dupes)
        else:
            print("Cancelled — no files moved.")

    else:
        print("\nRun again with --delete to permanently remove these files,")
        print("or --recycle to move them to a 'recyclebin' folder instead.")
