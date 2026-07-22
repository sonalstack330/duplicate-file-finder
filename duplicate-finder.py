import os
import hashlib
from collections import defaultdict

def compute_file_hash(filepath, algo="md5", chunk_size=8192):
    """Compute the hash of a file's contents in chunks (memory-safe for large files)."""
    hasher = hashlib.new(algo)
    hasher = hashlib.new(algo)
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()

def find_duplicates_basic(root_dir, algo="md5"):
    hash_map = defaultdict(list)

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for name in filenames:
            filepath = os.path.join(dirpath, name)
            file_hash = compute_file_hash(filepath, algo)
            hash_map[file_hash].append(filepath)

    # keep only groups with more than one file
    duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}
    return duplicates

if __name__ == "__main__":
    # replace/update your test call here to use the new function
    dupes = find_duplicates_basic(r"D:\PycharmProjects\duplicate-file-finder\test_folder")
    for h, paths in dupes.items():
        print(h, "->", paths)

