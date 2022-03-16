import click
import csv

from tester.config import Config


@click.group()
@click.pass_context
def student(ctx):
    """Manage students in the active course.
    """
    pass


@student.command("import")
@click.argument("path_to_csv_file")
@click.pass_obj
def import_students(config: Config, path_to_csv_file):
    """Imports students from a CSV file, updating any existing ones.
    """
    id_key = "id"
    students = config.get_students()
    with open(path_to_csv_file, "r", encoding="utf-8-sig") as csvfile:
        # TODO: validate CSV format
        reader = csv.reader(csvfile, delimiter=",")
        headers = list(next(reader, None))
        headers = [h.lower().strip() for h in headers]
        headers = [h.replace(" ", "_") for h in headers]
        for row in reader:
            new_student = {}
            for i, h in enumerate(headers):
                new_student[h] = row[i].strip()

            # Ensure other keys exist
            if "answered" not in new_student:
                new_student["answered"] = {}
            if "bonus" not in new_student:
                new_student["bonus"] = 0
            if "penalty" not in new_student:
                new_student["penalty"] = 0
            if "disallowed" not in new_student:
                new_student["disallowed"] = []
            if "hw" not in new_student:
                new_student["hw"] = []
            if "max_questions" not in new_student:
                new_student["max_questions"] = 8

            if new_student[id_key] in students:
                students[new_student[id_key]].update(new_student)
            else:
                students[new_student[id_key]] = new_student

    config.save_students(students)


@student.command("list")
@click.pass_obj
def list_students(config: Config):
    """Prints out the list students in the active course.
    """
    students = config.get_students()
    if not students:
        print(": No students in course")
        return
    students = sorted(list(students.values()), key=lambda k: k["last_name"])
    # Calculate lengths
    more_text = ".."
    more_text_len = len(more_text)
    f_name_max = max(len(s["first_name"]) for s in students)
    l_name_max = max(len(s["last_name"]) for s in students)
    s_id_max = max(len(s["id"]) for s in students)
    email_max = max(len(s["email"]) for s in students)
    username_max = max(len(s["username"]) for s in students)
    f_name_max_more = f_name_max + more_text_len
    l_name_max_more = l_name_max + more_text_len
    s_id_max_more = s_id_max + more_text_len
    email_max_more = email_max + more_text_len
    username_max_more = username_max + more_text_len
    total_width = f_name_max_more + l_name_max_more + s_id_max_more + email_max_more + \
        username_max_more + username_max_more
    bar = "=" * total_width
    # Print course
    active_course = config.context["active_course"]
    print(f": Listing students for course '{active_course}'")
    # Print header
    header = "{}  {}  {}  {}  {}".format(
        "First Name".ljust(f_name_max+2),
        "Last Name".ljust(l_name_max+2),
        "ID".ljust(s_id_max+2),
        "Email".ljust(email_max+2),
        "Username".ljust(username_max+2),
    )
    print(header)
    print(bar)
    # Print students
    for s in students:
        f_name = (s["first_name"][:f_name_max] + "..") \
            if len(s["first_name"]) > f_name_max_more \
            else s["first_name"]
        l_name = (s["last_name"][:l_name_max] + "..") \
            if len(s["last_name"]) > l_name_max_more \
            else s["last_name"]
        s_id = (s["id"][:s_id_max] + "..") \
            if len(s["id"]) > s_id_max_more \
            else s["id"]
        email = (s["email"][:email_max] + "..") \
            if len(s["email"]) > email_max_more \
            else s["email"]
        username = (s["username"][:username_max] + "..") \
            if len(s["username"]) > username_max_more \
            else s["username"]
        line = "{}  {}  {}  {}  {}".format(
            f_name.ljust(f_name_max_more),
            l_name.ljust(l_name_max_more),
            s_id.ljust(s_id_max_more),
            email.ljust(email_max_more),
            username.ljust(username_max_more),
        )
        print(line)
    print(bar)
    print(": {} students in the course.".format(len(students)))


@student.command("add")
@click.option("--unique_id", prompt=True)
@click.option("--first_name", prompt=True)
@click.option("--last_name", prompt=True)
@click.option("--email", prompt=True)
@click.option("--section", prompt=True)
@click.option("--username", prompt=True)
@click.pass_obj
def add(config: Config, unique_id, first_name, last_name, email, section, username):
    """Adds a new student to the active course.
    """
    new_student = {
        "answered": {},
        "bonus": 0,
        "disallowed": [],
        "email": email,
        "first_name": first_name,
        "hw": [],
        "id": unique_id,
        "last_name": last_name,
        "max_questions": 8,
        "section": section,
        "username": username
    }
    students = config.get_students()
    if not unique_id:
        raise InvalidStudentIdError("The provided student ID is invalid.")
    elif unique_id in students:
        raise StudentIdExistsError("A student with that ID already exists.")
    else:
        students[unique_id] = new_student
    config.save_students(students)

    print(": New student added to '{}' course.".format(config.context["active_course"]))


@student.command("update")
@click.argument("name")
@click.argument("path_to_csv_file")
@click.pass_obj
def update(config: Config, name: str, path_to_csv_file: str):
    """Updates students' answered questions from a CSV file.
    """
    students = config.get_students()
    with open(path_to_csv_file, "r", encoding="utf-8-sig") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        headers = next(reader, None)
        for row in reader:
            row_dict = {}
            for i, col in enumerate(headers):
                row_dict[col] = row[i]

            if not row_dict["answered"]:
                continue

            sid = row_dict["id"]
            if name not in students[sid]["answered"]:
                students[sid]["answered"][name] = []
            answered = list(map(int, row_dict["answered"].split()))
            students[sid]["answered"][name].extend(answered)
            students[sid]["answered"][name] = list(set(students[sid]["answered"][name]))
    config.save_students(students)


@student.command("update_points")
@click.argument("path_to_csv_file")
@click.pass_obj
def update_points(config: Config, path_to_csv_file: str):
    """Updates students' bonus and penalty points from a CSV file.
    """
    PENALTY_KEY = "penalty"
    BONUS_KEY = "bonus"
    students = config.get_students()
    with open(path_to_csv_file, "r", encoding="utf-8-sig") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        headers = next(reader, None)
        for row in reader:
            row_dict = {}
            for i, col in enumerate(headers):
                col = col.lower().strip()
                row_dict[col] = row[i]
            sid = row_dict["id"]
            new_bonus = row_dict[BONUS_KEY]
            new_penalty = row_dict[PENALTY_KEY]
            students[sid][BONUS_KEY] = abs(int(float(new_bonus))) if new_bonus else 0
            students[sid][PENALTY_KEY] = abs(int(float(new_penalty))) if new_penalty else 0
    config.save_students(students)


@student.command("set")
@click.argument("property")
@click.argument("value", type=int)
@click.option("--ids", type=list)
@click.pass_obj
def set_property(config: Config, property: str, value: int, ids: list):
    """Adds to or sets the property value for all students.
    """
    set_properties = ["max_questions", "penalty", "bonus"]
    add_properties = ["hw", "disallowed"]
    property = property.lower()

    def set_property_value(s: dict, p: str, v: int):
        s[p] = v

    def append_property_value(s: dict, p: str, v: int):
        if v not in s[p]:
            s[p].append(v)

    if property in set_properties:
        operation_func = set_property_value
    elif property in add_properties:
        operation_func = append_property_value
    else:
        raise NotImplementedError(f"Setting property '{property}' is not implemented!")

    students = config.get_students()
    if ids:  # Only applying to specific students
        students_to_modify = {sid: students[sid] for sid in ids}
    else:  # Applying to all students
        students_to_modify = students

    for student in students_to_modify.values():
        if property not in student:
            raise KeyError(f"Student '{student['id']}' doesn't have the '{property}' property.")
        operation_func(student, property, value)

    # config.save_students(students)


@student.command("add_property")
@click.argument("property")
@click.argument("value")
@click.argument("value_type")
@click.option("--force", is_flag=True, default=False)
@click.pass_obj
def add_property(config: Config, property: str, value: str, value_type: str, force: bool):
    """Adds a property (key-value pair) to all students in the active course.
    """
    valid_types = ["string", "int", "float"]
    value_type = value_type.lower()
    if value_type not in valid_types:
        raise InvalidPropertyValueTypeError(f"Supported value types are: {', '.join(valid_types)}")
    students = config.get_students()
    for sid, s in students.items():
        if property not in s or force:
            if value_type == "int":
                s[property] = int(value)
            elif value_type == "float":
                s[property] = float(value)
            else:  # string
                s[property] = value
        else:
            raise StudentPropertyExistsError(
                f"Property '{property}' already exists for student ID '{sid}'."
            )
    # config.save_students(students)


class InvalidStudentIdError(Exception):
    pass


class StudentIdExistsError(Exception):
    pass


class InvalidPropertyValueTypeError(Exception):
    pass


class StudentPropertyExistsError(Exception):
    pass
