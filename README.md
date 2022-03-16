# Tester

## Requirements

- Python 3.7+

## Setup

First install `wkhtmltopdf` on your system such that it is accessible from your terminal.
On Mac, this is:

```
brew cask install wkhtmltopdf
```

Then navigate to this repo and run:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

For development:

```
python3 setup.py develop
```

For use:

```
python3 setup.py install
```

## Running

With your installation complete, run:

```
tester
```

## Directory Structure

All of the tester content is stored within a `_tester_data/` directory.

- `_tester_data/` - Stores all tester data
    - `<course directories>` - Organizes data by course, enabling multiple courses at once
        - `_questions/` - Stores the question pool for the course
            - `<question directories>`
        - `_tests/` - Stores test builds
            - `<test directories>`
        - `modules.json` - Stores module information
        - `students.json` - Stores student information
        - `solution_instructions.md` - The text to be placed at the top of a generated solution.
        - `custom.css` - Custom CSS for generated tests and solutions.
    - `context.json` - Stores tester context information such as the currently active course

The path to the `_tester_data/` directory is set to by the `TESTER_DATA_DIR_PATH` environment variable.
