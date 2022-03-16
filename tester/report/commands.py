import click
import datetime
import math
import numpy as np

from tester.config import Config


@click.group()
@click.pass_context
def report(ctx):
    """Create reports about the active course.
    """
    pass


def get_grade(student, modules, all_module_questons, question_limit, verbose=False):
    """Returns the grade for an individual student.
    """
    points_removed = []
    student_answered = [a for l in student["answered"].values() for a in l]
    for module in modules.values():
        q_count = len(module["questions"])
        hw_count = len(module["hw"])
        for hwork in module["hw"]:
            if hwork in student["hw"]:
                continue  # Student did the HW, they get any test questions points they have
            # Deduct points
            if verbose:
                print("  ! Homework {} Not Submitted".format(hwork))
            max_questions_to_remove = math.ceil(q_count / hw_count)
            points_lost_count = 0
            if verbose:
                print("    Questions lost: ", end="")
            for i in module["questions"]:
                if i in student_answered and i not in points_removed:
                    points_removed.append(i)
                    points_lost_count += 1
                    if verbose:
                        print("{} ".format(i), end="")
                if points_lost_count >= max_questions_to_remove:
                    break
            if points_lost_count <= 0 and verbose:
                print("n/a (no questions answered in module yet)")
            elif verbose:
                print()

    answered = []
    for answered_q in student_answered:
        if answered_q in all_module_questons and answered_q not in points_removed:
            answered.append(answered_q)

    if verbose:
        print("  Questions answered:              ", len(student_answered))
        print("  Points lost due to incomplete HW:", len(points_removed))
        print("  Points after HW deductions:      ", len(answered))
        print("  Bonus points:                    ", student["bonus"])
        print("  Penalty points:                  ", student["penalty"])

    points = len(answered) + student["bonus"] - student["penalty"]
    points = points if points <= question_limit else question_limit
    grade = points / question_limit
    grade = grade * 100
    grade = 100.0 if grade > 100.0 else grade
    grade = 0.0 if grade < 0.0 else grade

    print("  Final points:                     {}/{}".format(points, question_limit))
    print("  Final grade:                      {:.2f}%".format(grade))

    return points, grade


@report.command("grades")
@click.option("--question-limit", default=None, type=int)
@click.option("--sid", default=None)
@click.option("--name", default=None)
@click.option("--grade-dist", is_flag=True, default=False)
@click.option("--lower-lim", default=0.0, type=float)
@click.option("--verbose", is_flag=True, default=False)
@click.pass_obj
def grades(config: Config, question_limit: int, sid: str, name: str, grade_dist: bool,
           lower_lim: float, verbose: bool):
    """Prints out a report of student progress.
    """
    modules = config.get_modules()
    students = config.get_students()
    all_module_questions = {q for m in modules.values() for q in m["questions"]}
    if not question_limit:
        question_limit = len(all_module_questions)  # TODO: this should maybe be max()

    students = sorted(list(students.values()), key=lambda k: k["last_name"])
    if not students:
        print("! No students found!")
        return
    if name:
        name = name.lower()
        students = [
            s for s in students
            if name in s["first_name"].lower() or name in s["last_name"].lower()
        ]
    elif sid:
        students = [s for s in students if s["id"] == sid]
    if not students:
        print(f"! No student(s) found!")
        return
    n_students = len(students)
    grades = []
    for student in students:
        print("\nGRADE REPORT for {} {}".format(student["first_name"], student["last_name"]))
        _, grade = get_grade(
            student,
            modules,
            all_module_questions,
            question_limit,
            verbose=verbose
        )
        if grade >= lower_lim:
            grades.append(grade)
        else:
            n_students -= 1

    print("\nSUMMARY")
    print("{} students found".format(n_students))
    average_grade = sum(grades) / n_students
    median_grade = np.median(grades)
    print(f"Mean grade:   {average_grade:.2f}")
    print(f"Median grade: {median_grade:.2f}")

    # Produce a density plot of the grades
    if grade_dist:
        import matplotlib.pyplot as plt
        x_range = list(range(0, 101, 5))
        _, ax = plt.subplots()
        ax.hist(grades, bins=x_range)
        ax.set(xlim=(0, 100))
        ax.set_title("Grade Distribution as of {}".format(datetime.date.today()))
        ax.set(xlabel="Grade", ylabel="Number of Students")
        ax.set_xticks(x_range)
        plt.show()


@report.command("summary")
@click.pass_obj
def summary(config: Config):
    modules = config.get_modules()
    students = config.get_students()
    students = sorted(list(students.values()), key=lambda k: k["last_name"])
    student_count = len(students)
    all_module_questions = {q for m in modules.values() for q in m["questions"]}
    question_limit = len(all_module_questions)

    total_answered = 0
    for student in students:
        student_answered = [a for l in student["answered"].values() for a in l]
        total_student_answered = len(student_answered)  # - student["penalty"] + student["bonus"]
        total_answered += total_student_answered
    average_answered = total_answered / student_count
    print(f"Average questions answered per student: {average_answered:.2f} out of {question_limit}")


@report.command("quiz-history")
@click.pass_obj
def quiz_history(config: Config):
    import matplotlib.pyplot as plt
    from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                                   AutoMinorLocator)

    modules = config.get_modules()
    students = config.get_students()
    students = sorted(list(students.values()), key=lambda k: k["last_name"])
    student_count = len(students)
    all_module_questions = {q for m in modules.values() for q in m["questions"]}
    question_limit = len(all_module_questions)
    quiz_occurrences = []
    for s in students:
        for w in s["answered"].keys():
            quiz_occurrences.append(w)
    quiz_occurrences = sorted(list(set(quiz_occurrences)))
    avg_points_per_quiz_occurrence = {}
    for q in quiz_occurrences:
        students_participating = 0
        avg_points_per_quiz_occurrence[q] = 0
        for s in students:
            if q in s["answered"]:
                avg_points_per_quiz_occurrence[q] += len(s["answered"][q])
                students_participating += 1
        if students_participating > 0:
            avg_points_per_quiz_occurrence[q] /= students_participating

    x_values = list(range(1, len(quiz_occurrences)+1))
    y_values = [v for _, v in sorted(avg_points_per_quiz_occurrence.items())]
    x_max = max(x_values) + 1
    y_max = max(y_values) + 1

    _, ax = plt.subplots()
    ax.plot(x_values, y_values)
    ax.set_xlim((0, x_max))
    ax.set_ylim((0, y_max))
    ax.set_xticks(x_values, minor=True)
    ax.set_title("Quiz Question History as of {}".format(datetime.date.today()))
    ax.set(xlabel="Quiz #", ylabel="Average Questions Answered")
    ax.xaxis.set_major_locator(MultipleLocator(x_max))
    ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
    ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.xaxis.set_minor_formatter(FormatStrFormatter('%d'))
    plt.show()


class InvalidStudentIdError(Exception):
    pass


class StudentIdAlreadyExistsError(Exception):
    pass
