import os
import sys
import argparse
import hashlib
from collections import defaultdict
import shutil

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
    scanned_count = 0   #  must be initialized BEFORE the loop
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for name in filenames:
            filepath = os.path.join(dirpath, name)
            try:
                size = os.path.getsize(filepath)
            except OSError:
                continue
            if size >= min_size:
                size_map[size].append(filepath)

            scanned_count += 1
            if scanned_count % 100 == 0:
                sys.stdout.write(f"\rScanning... {scanned_count} files found")
                sys.stdout.flush()

    sys.stdout.write(f"\rScanning complete — {scanned_count} files found.\n")   # outside both for-loops now

    # Step 2: only hash files that share a size with another file
    hash_map = defaultdict(list)
    candidates = [f for files in size_map.values() if len(files) > 1 for f in files]
    total_candidates = len(candidates)

    print(f"Hashing {total_candidates} candidate files...")

    for i, filepath in enumerate(candidates, start=1):   # needs enumerate() to give you `i`
        file_hash = compute_file_hash(filepath, algo)
        hash_map[file_hash].append(filepath)

        if i % 10 == 0 or i == total_candidates:
            sys.stdout.write(f"\rHashing... {i}/{total_candidates}")
            sys.stdout.flush()

    if total_candidates > 0:   # outside the for-loop now, runs once after hashing finishes
        sys.stdout.write("\n")

    return {h: paths for h, paths in hash_map.items() if len(paths) > 1}

def format_size(num_bytes):
    """Convert raw byte count into human-readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}" # :.1f rounds to 1 decimal place
        num_bytes /= 1024
    return f"{num_bytes:.1f} PB"

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
