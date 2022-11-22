import autograder
from colorama import Fore, Back, Style
import os


def main():
    proj_name = ""
    test_path = ""
    proj_path = ""

    if input("Do you want to download projects (y/n): ").lower().strip() in ("yes", "y"):
        proj_name = input("Specify Project Name (name of test file): ")
        test_path = os.path.abspath(os.path.join(__file__, f"../tests/{proj_name}.json"))
        proj_path = os.path.abspath(os.path.join(__file__, f"../projects/{proj_name}"))

        if not os.path.exists(test_path):
            if input(f"There are no tests that match name {proj_name}, continue? ").lower() not in ("yes", "y", ""):
                return

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
            return

        resp = autograder.test_projects(proj_path=proj_path, test_path=test_path)
        for i, j in resp.items():
            print(
                f"Project `{i}` passed {sum(k[0] for k in j)}/{len(j)} Tests: {''.join([f'{Fore.RED}X', f'{Fore.BLUE}✓'][m[0]] for m in j)}{Style.RESET_ALL}"
            )

        if len(resp) == 1:
            v, = resp.values()
            for i, (success, code, std_output, real_output) in enumerate(v, 1):
                if success:
                    continue

                print(f"------ TEST CASE {i} ------")
                if code == -1:
                    print("Could not find main class")
                elif code == -2:
                    print("Timed out")
                elif code != 0:
                    print(real_output)
                else:
                    std_output = repr(std_output)[1:-1]
                    real_output = repr(real_output)[1:-1]
                    j = 0  # Getting PyCharm to stop yelling at me

                    for j, (x, y) in enumerate(zip(std_output, real_output)):
                        if x != y:
                            break

                    print(
                        f"Standard Output: {Back.LIGHTYELLOW_EX}{Fore.BLACK}{std_output[max(j - 17, 0):j + 17]}{Style.RESET_ALL}",
                        f"    Your Output: {Back.LIGHTYELLOW_EX}{Fore.BLACK}{real_output[max(j - 17, 0): j + 17]}{Style.RESET_ALL}",
                        sep="\n", end="\n\n")


if __name__ == "__main__":
    main()
