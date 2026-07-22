import os
import hashlib


def compute_file_hash(filepath, algo="md5", chunk_size=8192):
    """Compute the hash of a file's contents in chunks (memory-safe for large files)."""
    hasher = hashlib.new(algo)
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except(OSError, PermissionError) as e:
        print(f" [!] Could not read {filepath}: {e}")
        return None

print(compute_file_hash("D:\\PycharmProjects\\website-uptime-monitor\\uptime_log.txt"))
print(compute_file_hash("D:\\PycharmProjects\\website-uptime-monitor\\uptime_log.txt"))

def scan_directory(rooot_dir):
    """walk through root_dir and print every file path found"""
    for dirpath, dirnames, filenames in os.walk(rooot_dir):
        for name in filenames:
            filepath = os.path.join(dirpath, name)
            print(filepath)

if __name__ == "__main__":
    scan_directory("C:\\Users\\\\Documents\\GitHub")

