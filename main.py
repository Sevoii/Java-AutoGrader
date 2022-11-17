import autograder
from colorama import Fore, Style
import os

proj_name = ""
test_path = ""
proj_path = ""

if input("Do you want to download projects (y/n): ").lower().strip() in ("yes", "y"):
    proj_name = input("Specify Project Name (name of test file): ")
    test_path = os.path.abspath(os.path.join(__file__, f"../tests/{proj_name}.json"))
    proj_path = os.path.abspath(os.path.join(__file__, f"../projects/{proj_name}"))

    if not os.path.exists(test_path):
        if input(f"There are no tests that match name {proj_name}, continue? ").lower() not in ("yes", "y", ""):
            exit(0)

    flag = input("Do you want to delete old projects: ").lower() in ("yes", "y")

    autograder.cleanup_folder(delete_existing=flag, projects_dir=proj_path)

    projects = input("List Replit links separated by spaces: ").strip().split(" ")
    autograder.download_projects(*projects, download_dir=proj_path)  # Could change this to just input a list
    autograder.compile_projects(projects_dir=proj_path)

if input("Do you want to test projects (y/n): ").lower().strip() in ("yes", "y"):
    if not proj_name:
        proj_name = input("Specify Project Name (name of test file): ")
        test_path = os.path.abspath(os.path.join(__file__, f"../tests/{proj_name}.json"))
        proj_path = os.path.abspath(os.path.join(__file__, f"../projects/{proj_name}"))

    if not os.path.exists(test_path):
        print(f"There are no tests that match name {proj_name}.")
        exit(0)

    resp = autograder.test_projects(proj_path=proj_path, test_path=test_path)
    for i, j in resp.items():
        print(
            f"Project `{i}` passed {sum(k[0] for k in j)}/{len(j)} Tests: {''.join([f'{Fore.RED}X', f'{Fore.BLUE}✓'][m[0]] for m in j)}{Style.RESET_ALL}")
