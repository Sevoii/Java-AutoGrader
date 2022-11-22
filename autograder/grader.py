from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import platform
import re
import shutil
import subprocess
import zipfile

import requests

from autograder.setup import in_replit


def _sanitize_url(link: str) -> str | None:
    """
    Extracted this function out b/c need to sanitize another url
    :param link: Link to sanitize
    :return: Repl.it link w/o weird stuff messing with dl
    """
    # pattern = r"https://(?:(?:replit\.com)|(?:repl\.it))/(?:(?:@\w+/[^#?\s]+)|(?:join/[^#?\s]+))"
    pattern = r"https://(?:replit\.com|repl\.it)/@\w+/[^#?\s]+"

    if temp := re.search(pattern, link):
        return temp.group()


def _get_valid_projects(input_projects: tuple[str]) -> list[str]:
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


def _unzip_and_clean(zip_path: str) -> None:
    """
    Unzips the file at zip_path to folder_path and cleans up every non .java file
    :param zip_path: Path to zip file
    :return: None
    """
    print(f"Unzipping project {zip_path}")

    with zipfile.ZipFile(zip_path) as f:  # Unzip zip file
        f.extractall(zip_path[:-4])

    os.remove(zip_path)  # Delete zip file

    # Walking through directory, getting rid of anything not .java
    walk = list(os.walk(zip_path[:-4]))
    for path, dirs, files in walk[::-1]:
        flag = False  # If java files or not
        for file in files:
            if not file.endswith(".java"):
                os.remove(f"{path}/{file}")
            else:
                flag = True

        # no .java files and no files = empty folder :>
        if not os.listdir(path) and not flag:
            os.rmdir(path)

    print(f"Finished unzipping project {zip_path}")


def download_projects(*input_projects: str, download_dir: str) -> None:
    """
    Given Input Projects Download, Unzip, & Delete unnecessary files :>
    :param input_projects: List of inputted projects
    :param download_dir: Directory to download to
    :return: None
    """
    projects = _get_valid_projects(input_projects)
    temp_index = len(os.listdir(download_dir))  # Making so this is sorted by order you put this in :>

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
                  "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "sec-ch-ua": '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": ''"Windows"'',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "service-worker-navigation-preload": "true",
        "upgrade-insecure-requests": "1",
        "cookie": f"connect.sid={os.environ.get('CONNECT_SID')}"
    }

    for proj in projects:
        if formatted_url := _sanitize_url(proj):
            resp = requests.get(f"{formatted_url}.zip", headers=headers)

            if resp.status_code == 200:
                *_, user, name = formatted_url.split("/")
                download_path = os.path.abspath(f"{download_dir}/{temp_index}-{user}-{name}.zip")

                with open(download_path, "wb") as f:
                    f.write(resp.content)

                _unzip_and_clean(zip_path=download_path)

                temp_index += 1
            else:
                print(f"Could not get replit for project {proj}. Maybe cookie error?")
        else:
            print(f"Could not get replit for project {proj}. Url formatted wrong.")


def _load_mixins() -> list[str]:
    """
    Loads the mixins found in mixins/mixins.json
    :return: Mixins
    """
    with open(os.path.abspath(os.path.join(__file__, "../../mixins/mixins.json"))) as f:
        return json.load(f)


def _inject_mixins(file_path: str, mixins: dict[str, list[dict[str, str]]]) -> bool:
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


def _get_main_file(path: str) -> str | None:
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


def _compile_project(path: str, mixins: dict[str, list[dict[str, str]]]) -> tuple[bool, str]:
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

        classpath = os.path.abspath(os.path.join(__file__, "../../mixins/*"))
        file_name = f"{_get_file_name(main_file)}.java"
        subprocess.run(f'javac -cp "{classpath}" {file_name}', cwd=path, shell=True)
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


def _test_project(project_path: str, std_input: str, std_output: str,
                  tries_left: int = 3) -> tuple[bool, int, str, str]:
    """
    Tests a project with an input and an output
    :param project_path: Path to project
    :param std_input: Input to supply
    :param std_output: Output Expected
    :param tries_left: Runs program this many tries before just returning a failure
    :return: Test successful or not, exit code, std_output, real_output
    """
    main_class = _get_main_file(project_path)
    if not main_class:  # Returns false if main class isn't found
        return False, -1, std_output, ""

    file_name = _get_file_name(main_class)

    try:
        # Defining this here b/c very long
        separator = ';' if platform.system() == 'Windows' else ':'
        mixins_path = os.path.join(__file__, '../../mixins/*')

        classpath = f"{os.path.abspath(project_path)}{separator}{os.path.abspath(mixins_path)}"

        # A bunch of weird stuff with subprocess
        proc = subprocess.run(f'java -cp "{classpath}" {file_name}', cwd=os.path.abspath(project_path),
                              input=std_input, text=True, capture_output=True, timeout=10, shell=True)

        # Just normalizing the output
        resp = (proc.stderr or proc.stdout).strip().replace("\r\n", "\n")

        return std_output == resp, proc.returncode, std_output, resp
    except subprocess.TimeoutExpired:
        # Catching timeout error - retrying as necessary
        if tries_left > 0:
            return _test_project(project_path, std_input, std_output, tries_left=tries_left - 1)
        else:
            return False, -2, std_output, ""


def _get_tests(test_path: str) -> list[dict[str, str]]:
    """
    Loads all the tests given a project name
    :param test_path: Path to json file containing tests
    :return: [{"input": "", "output": ""}]
    """
    if not os.path.exists(test_path):
        raise RuntimeError("Test path not valid")  # Should be checked before, we are just going to check again

    with open(test_path) as f:
        return json.load(f)


def test_projects(proj_path: str, test_path: str) -> dict[str, list[tuple[bool, int]]]:
    """
    Tests all projects in a directory
    :param proj_path: Project Directory
    :param test_path: Test File Path
    :return: dict - project_name: [(success, exit_code)]
    """
    executor = ThreadPoolExecutor(3 if in_replit() else 20)  # Only 3 threads in replit b/c lower system resources

    tests = _get_tests(test_path)  # Grabbing all the tests

    # _get_file_name also not meant to be used here (works tho) :p
    # Ugly ass list comprehension, basically just creates an
    # {project_name: [(success, exit_code), ...]}
    to_return = {
        _get_file_name(proj): executor.map(
            lambda x: _test_project(*x),
            ((proj, t["input"], t["output"]) for t in tests)
        ) for proj in _get_projects(proj_path)
    }

    # We submit eveything first and then wait for everything to finish 
    for t in to_return:
        to_return[t] = list(to_return[t])

    executor.shutdown()
    return to_return
