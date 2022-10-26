import autograder

proj_dir = ""
if input("Do you want to download projects (y/n): ").lower().strip() in ("yes", "y"):
    flag = input("Do you want to delete old projects - saying no may lead to errors (y/n): ").lower() in ("yes", "y")
    proj_dir = input("Specify Project Dir (entering nothing will use default): ")
    autograder.cleanup_folder(delete_existing=flag, projects_dir=proj_dir)

    if not autograder.get_chrome_driver():
        autograder.install_chrome_driver()

    projects = input("List Projects separated by spaces: ").split(" ")
    autograder.download_projects(*projects, download_dir=proj_dir)
    autograder.compile_projects(projects_dir=proj_dir)

if input("Do you want to test projects (y/n): ").lower().strip() in ("yes", "y"):
    if not proj_dir:
        proj_dir = input("Specify Project Dir (entering nothing will use default): ")

    resp = autograder.test_projects(projects_dir=proj_dir)
    for i, j in resp.items():
        print(f"Project `{i}` passed {sum(k[0] for k in j)}/{len(j)} Tests: {''.join('X✓'[m[0]] for m in j)}")
