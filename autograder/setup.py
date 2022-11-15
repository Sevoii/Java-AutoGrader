import os
import shutil


def cleanup_folder(delete_existing=True, projects_dir: str = "") -> None:
    """
    Cleans up the directory
    :param delete_existing: Whether to delete existing files or not
    :param projects_dir: Directory to clean up, default `__file__ + "/../../projects"`
    :return: None
    """
    if not projects_dir:  # Default value
        projects_dir = os.path.abspath(__file__ + "/../../projects")

    os.makedirs(projects_dir, exist_ok=True)  # Creates folder :>

    if delete_existing:
        for p in os.listdir(projects_dir):
            if p != "tests":
                shutil.rmtree(f"{projects_dir}/{p}", ignore_errors=True)


def in_replit():
    return os.path.exists(os.path.abspath(__file__ + "/../../.replit"))
