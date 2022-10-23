# Java AutoGrader [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


This repo aims to get a list of projects from repl.it and checks it against a standard intput/output.

Although running locally right now, in the future I hope to expand this to use online methods, whether through onlinegdb or another java compiler.

---

### How to Run

1. Install [Python 3.8](https://www.python.org/downloads/) or above (type `python` in terminal to test if it works)
2. Install [Java JDK](https://www.oracle.com/java/technologies/javase/javase8-archive-downloads.html) and set 
   %JAVA_HOME% env variable (open terminal and type `java` or `javac` to test if it works)
3. Get [extension](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid) to 
   download cookies
4. Open [repl.it](https://replit.com/~), log into your account, and download cookies
5. Create a file in `/config` called `cookies.txt` and paste cookies in (example in `cookies.txt.example`)
6. Navigate to the directory in terminal
7. Install requirements by doing `pip install -r requirements.txt`
8. Run the program by doing `python main.py`

---

### How this works

This downloads a zip from the repl.it, though you must be logged in to actually get the download. Then, it unzips and 
deletes all unnecessary files. It then compiles all the java files and runs it using python's subprocess library and
compares it to the output.

You can also bypass the replit step entirely, by pasting your .java files in :>

---

### How to create tests

In the project directory, create a folder called `tests`. In it, there will be files `TEST_NAME.in` and `TEST_NAME.out`.

### Example test config

File Structure
```
 - Java-AutoGrader
   - projects
     - tests
        - test1.in
        - test1.out
        - test2.in
        - test2.out
```

test1.in
```
30
50
```

test1.out 
```
Rectangle length: Rectangle width: Rectangle Perimeter: 160
Rectangle Area: 1500
``` 

Note that test1.out isn't what is below because the newline after each input is inputted by the user :>
```
Rectangle length: 
Rectangle width: 
Rectangle Perimeter: 160
Rectangle Area: 1500
``` 

---

### How to set this up on Repl.it

1. Download this repository (or clone it) into a new Python Repl
2. In the terminal side, click shell and run `java -version`
3. When it prompts you to select a java version, select the `adoptopenjdk-openj9-bin-16`
4. Click in the green run button at the top