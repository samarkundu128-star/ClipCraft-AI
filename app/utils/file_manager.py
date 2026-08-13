import os

def cleanup_files(*file_paths):
    for path in file_paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"Error deleting file {path}: {e}")
              
