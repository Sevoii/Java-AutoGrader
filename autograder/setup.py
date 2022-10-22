import requests
import platform
import zipfile
import os
import shutil


def install_chrome_driver() -> bool:
    """
    Installs Chrome Driver For Selenium
    :return: True if successfully installed, False if not -> do not proceed if False
    """

    if has_chrome_driver():  # Don't download if already installed
        return True

    # Get correct url
    if platform.system() == "Windows":
        url = "https://chromedriver.storage.googleapis.com/106.0.5249.61/chromedriver_win32.zip"
    elif platform.system() == "Darwin":
        url = "https://chromedriver.storage.googleapis.com/106.0.5249.61/chromedriver_mac64.zip"
    else:
        url = "https://chromedriver.storage.googleapis.com/106.0.5249.61/chromedriver_linux64.zip"

    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:  # Make sure 200 code
        return False

    with open(__file__ + "/../../chrome.zip", "wb") as f:  # Write zip file
        f.write(resp.content)

    with zipfile.ZipFile(__file__ + "/../../chrome.zip", "r") as f:  # Unzip zip file
        f.extractall(__file__ + "/../../chromedriver")

    os.remove(__file__ + "/../../chrome.zip")  # Delete zip file
    return True


def has_chrome_driver() -> bool:
    """
    Checks to see if the Chrome Driver is installed
    :return: If driver is there or not
    """
    return os.path.isfile(__file__ + "/../../chromedriver/chromedriver.exe")


def cleanup_folder(delete_existing=True, projects_dir: str = "") -> None:
    """
    Cleans up the directory
    :param delete_existing: Whether to delete existing files or not
    :param projects_dir: Directory to clean up, default `__file__ + "/../../projects"`
    :return: None
    """
    if not projects_dir:  # Default value
        projects_dir = __file__ + "/../../projects"

    os.makedirs(projects_dir, exist_ok=True)  # Creates folder :>

    if delete_existing:
        for p in os.listdir(projects_dir):
            if p != "tests":
                shutil.rmtree(f"{projects_dir}/{p}", ignore_errors=True)
