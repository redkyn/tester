import os
import random
import shutil
import smtplib
from getpass import getpass
from email.message import EmailMessage

import click
import parmap
import pdfkit
import tqdm
from markdown2 import markdown

from tester.config import Config

MAX_LINES = 55


def _get_next_questions(student: dict, questions: dict, max_questions: int):
    """Obtains the next set of questions for the given student and question pool.
    """
    sorted_question_keys = sorted(questions.keys())
    selected_questions = []
    questions_added = 0
    answered_questions = [q for sublist in student["answered"].values() for q in sublist]
    for q_num in sorted_question_keys:
        already_answered = q_num in answered_questions
        cant_answer = q_num in student["disallowed"]
        if already_answered or cant_answer:
            continue
        selected_questions.append(questions[q_num])
        questions_added += 1
        if questions_added >= max_questions:
            break

    return selected_questions


def _build_test(config: Config, output_path: str, output_dir_name: str, student: dict,
                all_question_content: str, dryrun: bool) -> tuple:
    """Generates a single test for the given information.
    """
    output_file_name = "{}_{}.{}".format(student["last_name"], student["id"], config.test_file_ext)
    test_output_path = os.path.join(output_path, output_file_name)
    if not dryrun:
        test_header_content = ""
        with open(config.test_header_path, "r") as fin:
            test_header_content = fin.read()
        test_content = ""
        test_content += "{}\n\n".format(test_header_content, output_dir_name)
        test_content += "**Name: {0} {1} (ID: {2}) (Section: {3})**\n\n".format(
            student["first_name"],
            student["last_name"],
            student["id"],
            student["section"]
        )
        test_content += all_question_content
        html_text = markdown(test_content, extras=["tables"])
        html_text = "<html><body style=\"\">" + html_text + "</body></html>"
        pdfkit.from_string(
            html_text,
            test_output_path,
            options=config.pdf_options,
            css=config.custom_css_file_path
        )
    return (student, test_output_path)


def _build_solution(config: Config, solution_path, questions):
    """Generates a single file with all questions and answers.
    """
    sorted_question_keys = sorted(questions.keys())
    solution_content = ""
    with open(config.solution_header_path, "r") as fin:
        solution_content += fin.read()

    for q_num in sorted_question_keys:
        sorted_question_options = sorted(questions[q_num]["options"])
        for o_num, option in enumerate(sorted_question_options, start=1):
            question_content = None
            answer_content = None
            with open(option, "r") as fin:
                question_content = [x.strip("<br/>") for x in fin.readlines()]
            answer_filename, answer_file_ext = os.path.splitext(option)
            answer_filename = f"{answer_filename}.solution{answer_file_ext}"
            with open(answer_filename, "r") as fin:
                answer_content = [x for x in fin.readlines()]

            if question_content and answer_content:
                solution_content += "## Question {}.{}\n\n".format(q_num, o_num)
                solution_content += "".join(question_content)

                solution_content += "#### Answer {}.{}\n\n".format(q_num, o_num)
                solution_content += "".join(answer_content)

    html_text = markdown(solution_content, extras=["tables"])
    html_text = "<html><body style=\"\">" + html_text + "</body></html>"
    pdfkit.from_string(
        html_text,
        solution_path,
        options=config.pdf_options,
        css=config.custom_css_file_path
    )


@click.command()
@click.argument("output_dir_name")
@click.option("--dryrun", is_flag=True, default=False,
              help="Just prints the questions each student will get if a test was generated.")
@click.option("--force", is_flag=True, default=False,
              help="Forces a rebuild of tests if a test directory already exists.")
@click.option("--solution-only", is_flag=True, default=False,
              help="Only build the solution file, no tests.")
@click.option("--max-question", default=None, type=int,
              help="The maximum question number that may appear on a test.")
@click.option("--max-questions", default=None, type=int,
              help="The maximum number of questions that may appear on a test.")
@click.option("--email", is_flag=True, default=False,
              help="Send each student their test via email immediately after the build.")
@click.pass_obj
def build(config: Config, output_dir_name: str, dryrun: bool, force: bool, solution_only: bool,
          max_question: int, max_questions: int, email: str):
    """Build tests for the active course.
    """
    test_directory_exists = False
    if not dryrun:
        output_path = os.path.join(
            config.active_course_path,
            config.tests_dir_name,
            output_dir_name
        )
        if os.path.exists(output_path):
            if not force:
                test_directory_exists = True
            else:
                shutil.rmtree(output_path)
        if not test_directory_exists:
            os.mkdir(output_path)

    students = config.get_students()
    questions = config.get_questions()
    if max_question:
        questions = {k: v for k, v in questions.items() if k <= max_question}

    if not dryrun:
        solution_path = os.path.join(output_path, config.solution_file_name)
        _build_solution(config, solution_path, questions)
        if solution_only:
            return
        elif test_directory_exists:
            msg = "That test directory already exists.  Make a new one or delete the existing one."
            raise TestDirectoryExistsError(msg)

    all_test_data = []
    print("Acquiring test data...")
    for sid, student in tqdm.tqdm(students.items()):
        max_questions = student["max_questions"] if not max_questions else int(max_questions)
        selected_questions = _get_next_questions(student, questions, max_questions)
        if not selected_questions:
            print("! Student {} has no questions; no test will be generated.".format(sid))
            continue  # If the student has no questions, print a message and skip them

        if dryrun:  # Just print the question numbers if we're doing a dry run.
            print(sid, ":", sep="", end="")
            for question in selected_questions:
                print("", question["num"], end="")
            print()

        all_question_content = ""
        if not dryrun:
            line_count = 0
            for question in selected_questions:
                selected_option_path = random.choice(question["options"])
                question_content = None
                with open(selected_option_path, "r") as fin:
                    question_content = [x for x in fin.readlines()]
                lines_added = len(question_content)
                line_count += lines_added
                for line in question_content:
                    # adding an extra line for each table row
                    if line.startswith("|") and not line.startswith("|-"):
                        lines_added += 1
                        line_count += 1
                if line_count > MAX_LINES:
                    all_question_content += "<p class='keep-together break-after'><p>\n"
                    line_count = lines_added
                assert question_content, "Question at '{}' has no content".format(
                    selected_option_path
                )
                all_question_content += "**{}.** ".format(question["num"])  # TODO: include option #
                for line in question_content:
                    all_question_content += line

        test_data = (config, output_path, output_dir_name, student, all_question_content, dryrun)
        all_test_data.append(test_data)
        # TODO: generate a log file containing details of what questions students received

    print("Generating PDFs...")
    results = parmap.starmap(
        _build_test,
        all_test_data,
        pm_pbar=True
    )
    if email:
        # Gather login information; update context as necessary
        # TODO: validate user input
        email_server = config.context["email_server"]
        email_server_port = config.context["email_server_port"]
        instructor_email = config.context["instructor_email"]
        grader_email = config.context["grader_email"] if "grader_email" in config.context else None
        # TODO: following is way too specific, switch to use config.context["active_course"]
        test_subject = f"CS341: Quiz {output_dir_name}"
        # Assembly all tests
        outgoing = []
        print("Building test emails...")
        for student, test_path in tqdm.tqdm(results):
            outgoing.append(_get_email(
                to_email=student["email"],
                from_email=instructor_email,
                subject=test_subject,
                attachment_path=test_path,
                body_path=config.email_body_file_path,
                cc_email=instructor_email
            ))
        # Send the latest solution to the grader
        if grader_email:
            print("Building solution email for grader... ", end="")
            outgoing.append(_get_email(
                to_email=config.context["grader_email"],
                from_email=instructor_email,
                # TODO: following is way too specific, switch to use config.context["active_course"]
                subject=f"CS341: Latest Solution",
                attachment_path=solution_path,
                body_path=None,
                cc_email=instructor_email
            ))
            print("done")
        # Send all emails
        print(f"Authenticating as '{instructor_email}' at '{email_server}'")
        with smtplib.SMTP(email_server, email_server_port) as ems:
            ems.ehlo()
            ems.starttls()
            instructor_password = getpass(f"Enter '{instructor_email}' password: ")
            ems.login(instructor_email, instructor_password)
            print("Authenticated!")
            print(f"Sending tests{' and solution' if grader_email else ''}...")
            for email in tqdm.tqdm(outgoing):
                ems.send_message(email)


def _get_email(to_email, from_email, subject, attachment_path, body_path=None,
               cc_email=None):
    msg = EmailMessage()
    body = "See attachment."
    if body_path and os.path.exists(body_path):
        with open(body_path) as fp:
            body = fp.read()
    msg.set_content(body)

    base_file_name = os.path.basename(attachment_path)
    with open(attachment_path, "rb") as fp:
        attachment = fp.read()
    msg.add_attachment(
        attachment,
        maintype="application/pdf",
        subtype="pdf",
        filename=base_file_name)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Cc"] = cc_email
    return msg


class TestDirectoryExistsError(Exception):
    pass
