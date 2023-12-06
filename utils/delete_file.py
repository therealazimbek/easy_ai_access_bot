import os


def delete_file_if_exists(path: str):
    if os.path.exists(path):
        os.remove(path)
