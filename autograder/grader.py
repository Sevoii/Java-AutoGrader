import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import os
import time
import zipfile
from typing import Optional, List, Dict, Tuple
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
from autograder.setup import get_chrome_driver


# I literally have no clue what this does
def _read_cookies() -> List[Dict]:
    """
    Reads cookies from cookie file and returns a dict
    :return: List of cookies
    """
    cookies = []
    with open(os.path.normpath(__file__ + "/../../config/cookies.txt"), 'r') as f:  # Cookie file
        for e in f:
            e = e.strip()
            if e.startswith('#'):
                continue
            k = e.split('\t')
            if len(k) < 3:
                continue  # not enough data
            # with expiry
            cookies.append({'name': k[-2], 'value': k[-1], 'expiry': int(k[-3])})
    return cookies


def _get_valid_projects(input_projects: Tuple[str]) -> List[str]:
    """
    Returns the list of valid projects formatted correctly
    :param input_projects: List of inputted projects
    :return: List of valid projects
    """
    # Filters for good projects
    projects = [temp[0] for p in input_projects if (temp := re.findall(r"https://replit\.com/@\w+/[^#?]+", p))]

    # Throw an error if a bad url
    if len(input_projects) != len(projects):
        proj_diff = (p for p in input_projects if not re.findall(r"https://replit\.com/@\w+/[^#?]+", p))
        print(f"Projects that didn't match regex: - {', '.join(proj_diff)}")
    print(f"Accepted Projects: {', '.join(projects)}")

    return projects


def _unzip_and_clean(zip_path: str, folder_path: str) -> None:
    """
    Unzips the file at zip_path to folder_path and cleans up every non .java file
    :param zip_path: Path to zip file
    :param folder_path: Path to folder
    :return: None
    """
    print(f"Unzipping project {folder_path}")

    # Busy waiting for file to finish :p
    while not os.path.isfile(zip_path):
        time.sleep(1)

    with zipfile.ZipFile(zip_path) as f:  # Unzip zip file
        f.extractall(folder_path)

    os.remove(zip_path)  # Delete zip file

    # Walking through directory, getting rid of anything not .java
    walk = list(os.walk(folder_path))
    for path, dirs, files in walk[::-1]:
        flag = False  # If java files or not
        for file in files:
            if not file.endswith(".java"):
                os.remove(f"{path}/{file}")
            else:
                flag = True

        # no .java files and no files = empty folder :>
        if len(os.listdir(path)) == 0 and not flag:
            os.rmdir(path)

    print(f"Finished unzipping project {folder_path}")


def download_projects(*input_projects: str, download_dir: str = "") -> None:
    """
    Given Input Projects Download, Unzip, & Delete unnecessary files :>
    :param input_projects: List of inputted projects
    :param download_dir: Directory to download to, default `__file__ + "/../../projects"`
    :return: None
    """
    if not download_dir:  # Default value
        download_dir = os.path.normpath(__file__ + "/../../projects")

    projects = _get_valid_projects(input_projects)

    # Selenium requires absolute paths for download
    chrome_options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": download_dir}
    chrome_options.add_experimental_option('prefs', prefs)

    # headless
    chrome_options.headless = True

    # Setting driver location
    ser = Service(os.path.normpath(get_chrome_driver()))
    driver = webdriver.Chrome(service=ser, options=chrome_options)
    driver.get("https://replit.com/")

    # Loading cookies
    for c in _read_cookies():
        driver.add_cookie(c)

    # Getting it again cause replit is DUMB >:(
    driver.get("https://replit.com/~")

    # It'll go to login page if cookies don't work
    if driver.current_url == "https://replit.com/login":
        driver.quit()
        raise RuntimeError("Reset the cookies so you actually log in")

    success = []
    failed = []
    for proj in projects:
        driver.get(f"{proj}.zip")

        # It will go to this url if it fails to download
        if driver.current_url == f"{proj}.zip":
            failed.append(proj)
        else:
            temp = proj.split('/')
            # project_name.zip, username-project_name.zip
            success.append([f"{temp[-1]}.zip", f"{temp[-2]}-{temp[-1]}"])

    for proj in success:
        _unzip_and_clean(f"{download_dir}/{proj[0]}", f"{download_dir}/{proj[1]}")

    # Cleaning up
    driver.quit()


def _get_main_file(path: str) -> Optional[str]:
    """
    Gets the first instance of public static void main(String[] args)
    :param path: Path of he directory
    :return: Path to file of main class
    """
    # So many \s cause you can put new lines/spaces like in so many places .-.
    # We are only checking if there's a public static void main(String[] args), not if it's commented out or not
    # I will fail you if you just have it commented though cause I'm mean like that
    pattern = r"public\s+static\s+void\s+main\s*\(((String\s*\[\s*]\s*args)|(String\s+args\s*\[\s*]))\)"

    files = []
    for path, _, files1 in os.walk(path):
        for file in files1:
            if file == "Main.java":  # We are prioritizing Main.java for lesser file reads (hopefully) :>
                with open(os.path.join(path, file)) as f:
                    if re.findall(pattern, f.read()):
                        return os.path.join(path, file)
            files.append(os.path.join(path, file))

    for file in files:
        with open(file) as f:
            if re.findall(pattern, f.read()):
                return file

    return None


def _get_file_name(path: str) -> str:
    """
    Gets the file name w/o extension
    :param path: Path to file
    :return: Name of file
    """

    # C:\something\filename.ext -> filename.ext -> filename
    # split("/") for linux support
    return os.path.normpath(path).split("\\")[-1].split("/")[-1].rsplit(".", 1)[0]


def _compile_project(path: str) -> [bool, str]:
    """
    Compile a single project (internal)
    :param path: Path to project
    :return: True if successful False if not, path
    """
    main_file = _get_main_file(path)

    if not main_file:
        return False, path
    else:
        subprocess.run(["javac", f"{_get_file_name(main_file)}.java"], cwd=path)  # Another hack :p
        return True, path


def _get_projects(project_dir: str) -> str:
    """
    Generator for all the projects in a directory, literally only used to iterate over tests
    :param project_dir: Path of project>s< directory
    :return: List of projects
    """

    for path in os.listdir(project_dir):
        if path == "tests":
            continue
        yield f"{project_dir}/{path}"


def compile_projects(projects_dir: str = "") -> None:
    """
    Compiles all the projects in the project directory
    :param projects_dir: Directory to projects, default `__file__ + "/../../projects"`
    :return: None
    """
    if not projects_dir:  # Default value
        projects_dir = os.path.normpath(__file__ + "/../../projects")

    executor = ThreadPoolExecutor(20)  # Only 20 threads cause :>
    futures = []

    for proj in _get_projects(projects_dir):
        futures.append(executor.submit(_compile_project, proj))

    # Wait as all the futures get completed
    for f in as_completed(futures):
        success, path = f.result()

        if not success:
            print(f"Unsuccessful compilation of {path}")
            shutil.rmtree(path, ignore_errors=True)  # Deletes entire folder :skull:

    executor.shutdown()


def _test_project(project_path: str, std_input: str, std_output: str) -> (bool, int):
    """
    Tests a project with an input and an output
    :param project_path: Path to project
    :param std_input: Input to supply
    :param std_output: Output Expected
    :return: Test successful or not, exit code
    """
    main_class = _get_main_file(project_path)
    if not main_class:  # Returns false if main class isn't found
        return False, -1

    file_name = _get_file_name(main_class)

    # A bunch of weird stuff with subprocess
    proc = subprocess.run(["java", file_name], cwd=project_path, input=std_input, text=True, capture_output=True,
                          timeout=3)

    # Just normalizing the output
    resp = proc.stdout.strip().replace("\r\n", "\n")
    return std_output == resp, proc.returncode


def _get_tests(project_dir: str = os.path.normpath(__file__ + "/../../projects")) -> List[Tuple[str, str]]:
    """
    Gets all of the tests in directory
    :param project_dir: Project Directory, default `__file__ + "/../../projects"`
    :return: List of Tests & Outputs
    """
    tests = []

    # Make sure there's actually a test dir :>
    if not os.path.exists(f"{project_dir}/tests"):
        return tests

    for file in os.listdir(f"{project_dir}/tests"):
        # Just skip over everything that isn't an .in :>
        if not file.endswith(".in"):
            continue

        # Just a bunch of random stuff
        test_name = _get_file_name(file)
        temp_path = f"{project_dir}/tests/{test_name}"  # _get_file_name not meant to be used here but :>
        if not os.path.exists(f"{temp_path}.in") or not os.path.exists(f"{temp_path}.out"):
            print(f"Test `{test_name}` did not have a .in and .out file, please fix!")
            continue

        # Reading files
        with open(f"{temp_path}.in", "r") as f:
            temp_input = f.read().strip()

        with open(f"{temp_path}.out", "r") as f:
            temp_output = f.read().strip()

        tests.append((temp_input, temp_output))
    return tests


def test_projects(projects_dir: str = "") -> Dict[str, List[Tuple[str, str]]]:
    """
    Tests all projects in a directory
    :param projects_dir: Project Directory, default `__file__ + "/../../projects"`
    :return: dict - project_name: [(success, exit_code)]
    """
    if not projects_dir:  # Default value
        projects_dir = os.path.normpath(__file__ + "/../../projects")

    executor = ThreadPoolExecutor(20)  # Only 30 threads cause why not :>

    tests = _get_tests(projects_dir)  # Grabbing all the tests

    # _get_file_name also not meant to be used here (works tho) :p
    # Ugly ass list comprehension, basically just creates an
    # project_name: [(success, exit_code), ...]
    to_return = {_get_file_name(proj): [executor.submit(_test_project, proj, *t) for t in tests] for proj in
                 _get_projects(projects_dir)}

    # Wait for everything to finish .-.
    for t in to_return.values():
        for i, f in enumerate(as_completed(t)):
            t[i] = f.result()  # Just setting result instead of a future obj

    return to_return
