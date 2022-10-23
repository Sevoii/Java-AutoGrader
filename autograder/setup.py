import requests
import platform
import zipfile
import os
import shutil
from typing import Optional


def install_chrome_driver() -> bool:
    """
    Installs Chrome Driver For Selenium
    :return: True if successfully installed, False if not -> do not proceed if False
    """

    if get_chrome_driver():  # Don't download if already installed
        return True

    if in_replit():  # Replit automatically installs chrome driver for us
        return True

    # Get correct url
    if platform.system() == "Windows":
        url = "https://chromedriver.storage.googleapis.com/106.0.5249.61/chromedriver_win32.zip"
    elif platform.system() == "Darwin":
        url = "https://chromedriver.storage.googleapis.com/106.0.5249.61/chromedriver_mac64.zip"
        raise RuntimeError("MAC is not supported yet, message me if you want to help")
    else:
        url = "https://chromedriver.storage.googleapis.com/106.0.5249.61/chromedriver_linux64.zip"
        raise RuntimeError("Linux is not supported yet, message me if you want to help")

    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:  # Make sure 200 code
        return False

    with open(os.path.normpath(__file__ + "/../../chrome.zip"), "wb") as f:  # Write zip file
        f.write(resp.content)

    with zipfile.ZipFile(os.path.normpath(__file__ + "/../../chrome.zip"), "r") as f:  # Unzip zip file
        f.extractall(os.path.normpath(__file__ + "/../../chromedriver"))

    os.remove(os.path.normpath(__file__ + "/../../chrome.zip"))  # Delete zip file
    return True


def get_chrome_driver() -> Optional[str]:
    if in_replit():  # Replit automatically installs chrome driver for us
        return None

    path = __file__ + "/../../chromedriver/chromedriver"
    if platform.system() == "Windows":
        path += ".exe"

    if os.path.isfile(os.path.normpath(path)):
        return os.path.normpath(path)
    return None


# def has_chrome_driver() -> bool:
#     """
#     Checks to see if the Chrome Driver is installed
#     :return: If driver is there or not
#     """
#     return os.path.isfile(os.path.normpath(__file__ + "/../../chromedriver/chromedriver.exe"))


def cleanup_folder(delete_existing=True, projects_dir: str = "") -> None:
    """
    Cleans up the directory
    :param delete_existing: Whether to delete existing files or not
    :param projects_dir: Directory to clean up, default `__file__ + "/../../projects"`
    :return: None
    """
    if not projects_dir:  # Default value
        projects_dir = os.path.normpath(__file__ + "/../../projects")

    os.makedirs(projects_dir, exist_ok=True)  # Creates folder :>

    if delete_existing:
        for p in os.listdir(projects_dir):
            if p != "tests":
                shutil.rmtree(f"{projects_dir}/{p}", ignore_errors=True)


def in_replit():
    return os.path.exists(os.path.normpath(__file__ + "/../../.replit"))
