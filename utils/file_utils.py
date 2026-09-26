import os
import hashlib

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def file_hash(filepath: str) -> str:
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def save_uploaded_file(uploaded_file, directory: str) -> str:
    ensure_dir(directory)
    dest = os.path.join(directory, uploaded_file.name)
    with open(dest, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return dest
