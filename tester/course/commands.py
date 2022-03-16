import click
import glob
import os

from tester.config import Config


@click.group()
@click.pass_context
def course(ctx):
    """View course information and change the active course.
    """
    pass


def _get_course_list(data_path):
    """Obtains a list of directory names in the data directory.
    """
    courses_pattern = os.path.join(data_path, "*")
    course_names = [os.path.basename(d) for d in glob.glob(courses_pattern) if os.path.isdir(d)]
    return course_names


def _print_course_names(course_names, active_course=""):
    """Prints out the given course names in a standardized way.
    """
    for i, c in enumerate(course_names, 1):
        course_str = "  {}. {}".format(i, c)
        if c == active_course:
            course_str += " [*]"
        print(course_str)


@course.command()
@click.argument("new_course_name")
@click.pass_obj
def add(config: Config, new_course_name):
    """Adds a new course to the tester data directory.
    """
    print(": Creating new course: {}".format(new_course_name))
    course_path = os.path.join(config.data_path, new_course_name)
    course_path = os.path.abspath(course_path)
    if os.path.exists(course_path):
        error_msg = "! Course already exists. You'll have to use a different name."
        raise CourseExistsError(error_msg)
    os.mkdir(course_path)
    print(": Creating course sub-directories:")
    print(":   {}".format(config.question_dir_name))
    questions_dir_path = os.path.join(course_path, config.question_dir_name)
    os.mkdir(questions_dir_path)
    print(":   {}".format(config.tests_dir_name))
    tests_dir_path = os.path.join(course_path, config.tests_dir_name)
    os.mkdir(tests_dir_path)
    print(":   {}".format(config.students_file_name))
    students_file_path = os.path.join(course_path, config.students_file_name)
    with open(students_file_path, "a") as fout:
        fout.write("{}")
    print(":   {}".format(config.modules_file_name))
    modules_file_path = os.path.join(course_path, config.modules_file_name)
    with open(modules_file_path, "a") as fout:
        fout.write("{}")
    print(": {} course created.".format(new_course_name))


@course.command("list")
@click.pass_obj
def list_courses(config: Config):
    """Displays a list of all courses found in the data directory.
    """
    course_names = _get_course_list(config.data_path)
    if course_names:
        print(": Courses:")
        _print_course_names(course_names, config.context["active_course"])
    else:
        print(": No courses found.")


@course.command()
@click.argument("course_name")
@click.pass_obj
def activate(config: Config, course_name):
    """Sets the course with the given name to be the currently active one.
    """
    course_names = _get_course_list(config.data_path)
    matches = [c for c in course_names if course_name in c]
    match_count = len(matches)
    if match_count == 0:
        print(": No courses exist by that name.")
    elif match_count > 1:
        print(": Multiple courses matched .")
        _print_course_names(matches)
    else:
        config._set_active_course(matches[0])
        print(": Course '{}' is active.".format(matches[0]))


class CourseExistsError(Exception):
    pass
