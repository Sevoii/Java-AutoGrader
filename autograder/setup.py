import os
import shutil


def cleanup_folder(projects_dir: str, delete_existing: bool = True) -> None:
    """
    Cleans up the directory
    :param projects_dir: Directory to clean up
    :param delete_existing: Whether to delete existing files or not
    :return: None
    """
    os.makedirs(projects_dir, exist_ok=True)  # Lazy to check :>

    if delete_existing:
        for p in os.listdir(projects_dir):
            if p != "tests":
                shutil.rmtree(f"{projects_dir}/{p}", ignore_errors=True)


def in_replit() -> bool:
    """
    Checks for precense of .replit file
    :return: If in replit or not
    """
    return os.path.exists(os.path.abspath(os.path.join(__file__, "../../.replit")))
