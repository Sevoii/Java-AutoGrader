from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import platform
import re
import shutil
import subprocess
import time
from typing import Optional, List, Dict, Tuple
import zipfile

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from autograder.setup import in_replit


# I literally have no clue what this does
def _read_cookies() -> List[Dict]:
    """
    Reads cookies from cookie file and returns a dict
    :return: List of cookies
    """
    cookies = []
    with open(os.path.abspath(os.path.join(__file__, "../../config/cookies.txt")), 'r') as f:  # Cookie file
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


def _sanitize_url(link: str) -> Optional[str]:
    """
    Extracted this function out b/c need to sanitize another url
    :param link: Link to sanitize
    :return: Repl.it link w/o weird stuff messing with dl
    """
    pattern = r"https://(?:(?:replit\.com)|(?:repl\.it))/(?:(?:@\w+/[^#?\s]+)|(?:join/[^#?\s]+))"

    if temp := re.findall(pattern, link):
        return temp[0]


def _get_valid_projects(input_projects: Tuple[str]) -> List[str]:
    """
    Returns the list of valid projects formatted correctly
    :param input_projects: List of inputted projects
    :return: List of valid projects
    """
    success = []
    fail = []

    for i in input_projects:
        # We can just append `i` because we are sanitizing it later
        if _sanitize_url(i):
            success.append(i)
        else:
            fail.append(i)

    print(f"Rejected Projects: {', '.join(fail)}")
    print(f"Accepted Projects: {', '.join(success)}")

    return success


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


def download_projects(*input_projects: str, download_dir: str) -> None:
    """
    Given Input Projects Download, Unzip, & Delete unnecessary files :>
    :param input_projects: List of inputted projects
    :param download_dir: Directory to download to
    :return: None
    """
    projects = _get_valid_projects(input_projects)

    # Selenium requires absolute paths for download
    chrome_options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": download_dir}
    chrome_options.add_experimental_option('prefs', prefs)

    # headless
    chrome_options.headless = True

    if in_replit():  # We need these settings if we're running in replit
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

    if in_replit():  # Don't specify path if we're not in replit
        driver = webdriver.Chrome(options=chrome_options)
    else:
        # I'm not sure if repl.it can use ChromeDriverManager but it works w/o
        ser = Service(os.path.abspath(ChromeDriverManager().install()))
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

    temp_index = len(os.listdir(download_dir))  # Making so this is sorted by order you put this in :>

    for proj in projects:
        driver.get(proj)

        if "404" in driver.title:  # Actually checking if link works
            print(f"Could not get replit for project {proj}")
            continue

        formatted = _sanitize_url(f"{driver.current_url}")
        if not formatted:  # This really shouldn't happen but it'll be fine
            print(f"This should not occur! Could not sanitize url {driver.current_url}?")
            continue

        new_url = f"{formatted}.zip"  # Zipped url :>
        driver.get(new_url)

        if driver.current_url != new_url:  # It won't redirect if it's downloading
            *_, user, name = formatted.split("/")

            # Doing this now so we can limit how fast we download
            _unzip_and_clean(os.path.abspath(f"{download_dir}/{name}.zip"),
                             os.path.abspath(f"{download_dir}/{temp_index}-{user}-{name}"))
            temp_index += 1
        else:
            print(f"Could not get download zip for project {proj}")

    # Cleaning up
    driver.quit()


def _load_mixins() -> List[str]:
    """
    Loads the mixins found in mixins/mixins.json
    :return: Mixins
    """
    with open(os.path.join(__file__, "../../mixins/mixins.json")) as f:
        return json.load(f)


def _inject_mixins(file_path: str, mixins: Dict[str, List[Dict[str, str]]]) -> bool:
    """
    Injects mixins into a file
    :param file_path: Path of file to inject
    :param mixins: Mixins
    :return: Successful or not
    """
    if not os.path.exists(file_path):
        return False

    with open(file_path) as f:
        contents = f.read()

    imports = "\n".join(x for i in mixins if (x := f"import {i};") not in contents)
    if m := re.search(r"\s*package\s+.+;\n", contents):  # looking for package at start of file b/c imports after
        contents = contents[:m.end()] + imports + contents[m.end():]
    else:
        contents = imports + contents

    for lst in mixins.values():
        for v in lst:
            contents = re.sub(v["regex"], v["replace"], contents)

    with open(file_path, "w") as f:
        f.write(contents)

    return True


def _get_main_file(path: str) -> Optional[str]:
    """
    Gets the first instance of public static void main(String[] args)
    :param path: Path of he directory
    :return: Path to file of main class
    """
    # So many \s cause you can put new lines/spaces like in so many places .-.
    # We are only checking if there's a public static void main(String[] args), not if it's commented out or not
    # I will fail you if you just have it commented though cause I'm mean like that
    pattern = r"public\s+static\s+void\s+main\s*\(((String\s*\[\s*]\s*[A-Za-z_]\w*)|(String\s+[A-Za-z_]\w*\s*\[\s*]))\)"

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
    return os.path.abspath(path).split("\\")[-1].split("/")[-1].rsplit(".", 1)[0]


def _compile_project(path: str, mixins: Dict[str, List[Dict[str, str]]]) -> Tuple[bool, str]:
    """
    Compile a single project (internal)
    :param path: Path to project
    :param mixins: Mixins to inject
    :return: True if successful False if not, path
    """
    main_file = _get_main_file(path)

    if not main_file:
        return False, path
    else:
        # Injecting mixins
        for path, _, files1 in os.walk(path):
            for file in files1:
                if file.endswith(".java"):
                    if not _inject_mixins(os.path.join(path, file), mixins):
                        return False, path

        subprocess.run(["javac", "-cp", os.path.abspath(os.path.join(__file__, "../../mixins/*")),
                        f"{_get_file_name(main_file)}.java"], cwd=path)  # Another hack :p
        return True, path


def _get_projects(project_dir: str) -> str:
    """
    Generator for all the projects in a directory, literally only used to iterate over tests
    :param project_dir: Path of project>s< directory
    :return: List of projects
    """

    for path in sorted(os.listdir(project_dir), key=lambda x: int(x.split("-")[0])):
        yield f"{project_dir}/{path}"


def compile_projects(projects_dir: str) -> None:
    """
    Compiles all the projects in the project directory
    :param projects_dir: Directory to projects
    :return: None
    """
    mixins = _load_mixins()

    executor = ThreadPoolExecutor(20)  # Only 20 threads cause :>
    futures = []

    for proj in _get_projects(projects_dir):
        futures.append(executor.submit(_compile_project, proj, mixins))

    # Wait as all the futures get completed
    for f in as_completed(futures):
        success, path = f.result()

        if not success:
            print(f"Unsuccessful compilation of {path}")
            shutil.rmtree(path, ignore_errors=True)  # Deletes entire folder :skull:

    executor.shutdown()


def _test_project(project_path: str, std_input: str, std_output: str, tries_left=3) -> Tuple[bool, int]:
    """
    Tests a project with an input and an output
    :param project_path: Path to project
    :param std_input: Input to supply
    :param std_output: Output Expected
    :param tries_left: Runs program this many tries before just returning a failure
    :return: Test successful or not, exit code
    """
    main_class = _get_main_file(project_path)
    if not main_class:  # Returns false if main class isn't found
        return False, -1

    file_name = _get_file_name(main_class)

    try:
        # Defining this here b/c very long
        classpath = f"{os.path.abspath(project_path)}{';' if platform.system() == 'Windows' else ':'}{os.path.abspath(os.path.join(__file__, '../../mixins/*'))}"

        # A bunch of weird stuff with subprocess
        proc = subprocess.run(f"java -cp \"{classpath}\" {file_name}", cwd=os.path.abspath(project_path),
                              input=std_input, text=True, capture_output=True, timeout=10)

        # Just normalizing the output
        resp = proc.stdout.strip().replace("\r\n", "\n")
        return std_output == resp, proc.returncode
    except subprocess.TimeoutExpired:
        # Catching timeout error - retrying as necessary
        if tries_left > 0:
            return _test_project(project_path, std_input, std_output, tries_left=tries_left - 1)
        else:
            return False, 1


def _get_tests(test_path: str) -> List[Dict[str, str]]:
    """
    Loads all the tests given a project name
    :param test_path: Path to json file containing tests
    :return: [{"input": "", "output": ""}]
    """
    if not os.path.exists(test_path):
        raise RuntimeError("Test path not valid")  # Should be checked before, we are just going to check again

    with open(test_path) as f:
        return json.load(f)


def test_projects(proj_path: str, test_path: str) -> Dict[str, List[Tuple[bool, int]]]:
    """
    Tests all projects in a directory
    :param projects_dir: Project Directory
    :return: dict - project_name: [(success, exit_code)]
    """
    executor = ThreadPoolExecutor(20)  # Only 30 threads cause why not :>

    tests = _get_tests(test_path)  # Grabbing all the tests

    # _get_file_name also not meant to be used here (works tho) :p
    # Ugly ass list comprehension, basically just creates an
    # project_name: [(success, exit_code), ...]
    to_return = {_get_file_name(proj): [executor.submit(_test_project, proj, t["input"], t["output"]) for t in tests]
                 for proj in _get_projects(proj_path)}

    # Wait for everything to finish .-.
    for t in to_return.values():
        for i, f in enumerate(as_completed(t)):
            t[i] = f.result()  # Just setting result instead of a future obj

    return to_return
