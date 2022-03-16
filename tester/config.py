import json
import os
import re


class Config():
    """Configuration management commands and information.
    """
    def __init__(self):
        # Checking for data directory
        data_path = os.environ.get("TESTER_DATA_DIR_PATH")

        # Ensure the data directory path to an absolute path
        if data_path is None:
            error_msg = "Environment variable TESTER_DATA_DIR_PATH not set."
            raise InvalidDataDirectoryPathError(error_msg)
        data_path = os.path.expanduser(data_path)
        data_path = os.path.abspath(data_path)
        self.data_path = data_path

        # Check that the data directory exists and it is actually a directory
        if not os.path.exists(self.data_path):
            print(": Data path does not exist, creating it...")
            os.mkdir(self.data_path)
        if not os.path.isdir(self.data_path):
            error_msg = "Data path does not point to a diretory. " +\
                "Either delete what's there or change the path."
            raise InvalidDataDirectoryPathError(error_msg)

        # Set file and directory name per convention
        self.context_file_name = "context.json"
        self.question_dir_name = "_questions/"
        self.tests_dir_name = "_tests/"
        self.modules_file_name = "modules.json"
        self.students_file_name = "students.json"
        self.test_file_ext = "pdf"
        self.test_header_file_name = "test_header.md"
        self.solution_file_ext = "pdf"
        self.solution_file_name = f"_solution.{self.solution_file_ext}"
        self.solution_header_file_name = "solution_header.md"
        self.custom_css_file_name = "custom.css"
        self.pdf_options = {
            "page-size": "Letter",
            "margin-top": "0.5in",
            "margin-right": "0.5in",
            "margin-bottom": "0.5in",
            "margin-left": "0.5in",
            "encoding": "UTF-8",
            "user-style-sheet": "test.css",
            "log-level": "none"
        }
        self.email_body_file_name = "email_body.md"
        self.email_server = None
        self.question_dir_pattern = re.compile(r"[0-9]+")
        self.question_file_pattern = re.compile(r"^[0-9]+\.md$")
        self.json_indent = 4

        # Load context info form config file
        self.context_path = os.path.join(self.data_path, self.context_file_name)
        self.context = {
            "active_course": None
        }
        if not os.path.exists(self.context_path):
            print(": No context file found, creating it...")
            with open(self.context_path, "w+") as f:
                json.dump(self.context, f, indent=self.json_indent)

        with open(self.context_path, "r") as f:
            loaded_context = json.load(f)
            self.context.update(loaded_context)

        if self.context["active_course"]:
            self.active_course_path = os.path.join(self.data_path, self.context["active_course"])
            self.active_course_path = os.path.abspath(self.active_course_path)
            self.students_file_path = os.path.join(self.active_course_path, self.students_file_name)
            self.students_file_path = os.path.abspath(self.students_file_path)
            self.questions_dir_path = os.path.join(self.active_course_path, self.question_dir_name)
            self.questions_dir_path = os.path.abspath(self.questions_dir_path)
            self.modules_file_path = os.path.join(self.active_course_path, self.modules_file_name)
            self.modules_file_path = os.path.abspath(self.modules_file_path)
            self.test_header_path = os.path.join(self.active_course_path,
                                                 self.test_header_file_name)
            self.test_header_path = os.path.abspath(self.test_header_path)
            self.solution_header_path = os.path.join(self.active_course_path,
                                                     self.solution_header_file_name)
            self.solution_header_path = os.path.abspath(self.solution_header_path)
            self.custom_css_file_path = os.path.join(self.active_course_path,
                                                     self.custom_css_file_name)
            self.email_body_file_path = os.path.join(self.active_course_path,
                                                     self.email_body_file_name)
        else:
            raise NoActiveCourseError("! Please activate a course first!")

    def _save_context(self):
        """Saves out the current context to a JSON file.
        """
        with open(self.context_path, "w") as f:
            json.dump(self.context, f, indent=self.json_indent, sort_keys=True)
        print(": Context updated.")

    def _set_active_course(self, course_name):
        """Sets the currently active course and saves the context.
        """
        self.context["active_course"] = course_name
        self._save_context()

    def _ensure_consecutiveness(self, list_type, number_list):
        """Asserts that a list of numbers are consecutive.
        """
        if number_list != list(range(min(number_list), max(number_list)+1)):
            raise QuestionsAreNotConsecutiveError("{} not consecutive.".format(list_type))

    def get_students(self) -> dict:
        """Obtains the students dictionary from the active course.
        """
        with open(self.students_file_path) as fin:
            students = json.load(fin)
        return students

    def save_students(self, students: dict):
        """Saves the students dictionary to the active course.
        """
        with open(self.students_file_path, "w") as fout:
            json.dump(students, fout, indent=self.json_indent, sort_keys=True)

    def get_modules(self) -> dict:
        with open(self.modules_file_path, "r") as fin:
            modules = json.load(fin)
        return modules

    def get_questions(self) -> dict:
        """Obtains questions from questions folder and ensures everything is proper.
        """
        questions_nums = [
            int(q) for q in os.listdir(self.questions_dir_path)
            if self.question_dir_pattern.match(q)
        ]
        if not questions_nums:
            return []
        questions_nums.sort()
        self._ensure_consecutiveness("Question folders", questions_nums)

        questions = {}
        for q_num in questions_nums:
            q_path = os.path.join(self.questions_dir_path, str(q_num))

            q_options = [q for q in os.listdir(q_path) if self.question_file_pattern.match(q)]
            assert q_options, "No options for question #{}".format(q_num)
            q_options.sort()

            questions[q_num] = {
                "num": q_num,
                "path": q_path,
                "options": [
                    os.path.join(q_path, x) for x in os.listdir(q_path)
                    if self.question_file_pattern.match(x)
                ]
            }

        return questions


class InvalidDataDirectoryPathError(Exception):
    pass


class NoActiveCourseError(Exception):
    pass


class QuestionsAreNotConsecutiveError(Exception):
    pass
