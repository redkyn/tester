import click
import json

from tester.config import Config


@click.group()
@click.pass_context
def module(ctx):
    """View and manage modules for the active course.
    """
    pass


def _print_module_names(modules):
    for i, k in enumerate(modules, 1):
        module_str = "  {}: {}".format(k, modules[k]["name"])
        print(module_str)


@module.command("list")
@click.pass_obj
def list_modules(config: Config):
    """Displays a list of modules found for the active course.
    """
    modules = config.get_modules(config.modules_file_path)
    if modules:
        print(": Modules:")
        _print_module_names(modules)
    else:
        print(": No modules found.")


@module.command()
@click.argument("new_module_id")
@click.argument("new_module_name")
@click.pass_obj
def add(config: Config, new_module_id, new_module_name):
    """Adds a new module to the active course.
    """
    print(": Creating new module: {}".format(new_module_name))

    modules = config.get_modules(config.modules_file_path)
    if new_module_id in modules:
        error_msg = ": Module with that ID already exists. " + \
            "You'll have to use a different ID."
        raise ModuleExistsError(error_msg)
    modules[new_module_id] = {
        "hw": [],
        "name": new_module_name,
        "questions": []
    }
    with open(config.modules_file_path, "w") as fout:
        json.dump(modules, fout, indent=config.json_indent, sort_keys=True)

    print(": Module {}, {}, created.".format(new_module_id, new_module_name))


class ModuleExistsError(Exception):
    pass
