# Java AutoGrader [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This repo aims to download a list of projects from replit and check it against a standard input/output.

Currently, it is running locally right now, but in the future I hope to expand this to use online methods, either
through onlinegdb or another java compiler.

### THE CURRENT TEST YOU ARE RUNNING IS CALLED `powerball`

---

### How to set this up on Replit

1. Download this repository by clicking on the green `<> Code` button at the top and click `Download Zip`
   ![Step 1](https://files.catbox.moe/dsgaeg.png)
2. Open [repl.it](https://replit.com/~) and create a new `Python` repl
3. Unzip the folder you downloaded and drag the contents onto the repl (Make sure the main.py overwrites the current
   main.py)
4. Alternatively, when creating a new repl click `Import from GitHub` and follow the instructions
5. On the right side, click shell and run `java -version`
6. When it prompts you to select a java version, select the `adoptopenjdk-openj9-bin-16`
   ![Step 5](https://files.catbox.moe/30cd7g.png)
7. Read [here](https://github.com/Chitaso/Java-AutoGrader/tree/master#how-to-get-connectsid-cookie) to read how to get
   your connect.sid cookie
8. Add a secret to your repl. On the left handed bar, click the padlock icon, and put `CONNECT_SID` where the key is,
   and the cookie you just grabbed in the value section.
   ![Step7](https://files.catbox.moe/1yljn8.png)
9. Click in the green run button at the top

---

### How to Run Locally

1. Install [Python 3.8](https://www.python.org/downloads/) or above (type `python` in terminal to test if it works)
2. Install [Java JDK](https://www.oracle.com/java/technologies/javase/javase8-archive-downloads.html) and set
   `%JAVA_HOME%` env variable (open terminal and type `java` or `javac` to test if it works)
3. Download this repository by clicking on the green `<> Code` button at the top and click `Download Zip`
   ![Step 1](https://files.catbox.moe/dsgaeg.png)
4. Unzip the folder and navigate to it from the command line
5. Alternatively if you have git, clone this repository.
6. Setup pip dependencies by running `python -m pip install -r requirements.txt`
7. Read [here](https://github.com/Chitaso/Java-AutoGrader/tree/master#how-to-get-connectsid-cookie) to read how to get
   your connect.sid cookie
8. Rename `example.env` to `.env`, and replace `REPLACE_THIS` with your cookie
9. Run the program by running `python main.py` or double clicking `main.py`

---

### How to get connect.sid cookie

1. In your search bar, click on the padlock icon and click Cookies.
   ![Step 1](https://files.catbox.moe/m7yysy.png)
2. Expand the `replit.com` and `Cookies` dropdowns.
   ![Step 2](https://files.catbox.moe/9igp8p.png)
3. Look for the connect.sid header, click on it, and copy the cookie content.
   ![Step 3](https://files.catbox.moe/doazii.png)

---

### How this works

This downloads a zip from the replit through requests library, though you must be logged in to actually get the
download. It then unzips and deletes all unnecessary files, as well as injects mixins based off the
file `mixins/mixin.json`. Finally, it compiles all the java files and runs it using python's subprocess library and
compares it to the output supplied in `test/name.json`.

---

### How to create your own tests

In the `tests` directory, create a JSON file with its name being the name of the project.

### Example test config

File Structure

```
 - AutoGrader
   - tests
     - example.json
```

example.json

```json
[
   {
      "input": "hello",
      "output": "world"
   }
]
```

Reminder: the output does not have the newline/text inputted by the user.

