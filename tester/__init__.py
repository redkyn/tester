import click

from tester.config import Config
from tester.build.commands import build
from tester.course.commands import course
from tester.module.commands import module
from tester.report.commands import report
from tester.student.commands import student


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = Config()


cli.add_command(build)
cli.add_command(course)
cli.add_command(module)
cli.add_command(report)
cli.add_command(student)


if __name__ == "__main__":
    cli()
