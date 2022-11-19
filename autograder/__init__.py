from dotenv import load_dotenv

load_dotenv()  # Loading before importing any other views

from autograder.setup import *
from autograder.grader import download_projects, compile_projects, test_projects
