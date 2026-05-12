import os
import shutil

def clean_cache(root_dir):
    for root, dirs, files in os.walk(root_dir):
        # ✅ Skip virtual environment
        if ".venv" in root:
            continue

        # Copy dirs list to modify safely
        for d in list(dirs):
            if d == "__pycache__":
                dir_path = os.path.join(root, d)
                try:
                    shutil.rmtree(dir_path)
                    print(f"Deleted directory: {dir_path}")
                except PermissionError:
                    print(f"Skipped (permission denied): {dir_path}")

        for f in files:
            if f.endswith(".pyc"):
                file_path = os.path.join(root, f)
                try:
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")
                except PermissionError:
                    print(f"Skipped (permission denied): {file_path}")

if __name__ == "__main__":
    clean_cache(os.getcwd())
    print("\n✅ Cache cleanup completed!")
