#!/usr/bin/env python3
"""Activate an evergreen task in the existing build."""
import os
import sys

import click
import structlog
from pydantic.main import BaseModel
from evergreen.api import RetryingEvergreenApi, EvergreenApi

# Get relative imports to work when the package is not installed on the PYTHONPATH.
if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=wrong-import-position
from buildscripts.util.cmdutils import enable_logging
from buildscripts.util.fileops import read_yaml_file
from buildscripts.util.taskname import remove_gen_suffix
# pylint: enable=wrong-import-position

LOGGER = structlog.getLogger(__name__)

EVG_CONFIG_FILE = "./.evergreen.yml"


class EvgExpansions(BaseModel):
    """
    Evergreen expansions file contents.

    build_id: ID of build being run.
    task_name: Name of task creating the generated configuration.
    """

    build_id: str
    task_name: str

    @classmethod
    def from_yaml_file(cls, path: str) -> "EvgExpansions":
        """Read the generation configuration from the given file."""
        return cls(**read_yaml_file(path))

    @property
    def task(self) -> str:
        """Get the task being generated."""
        return remove_gen_suffix(self.task_name)


def activate_task(build_id: str, task_name: str, evg_api: EvergreenApi) -> None:
    """
    Activate the given task in the specified build.

    :param build_id: Build to activate task in.
    :param task_name: Name of task to activate.
    :param evg_api: Evergreen API client.
    """
    build = evg_api.build_by_id(build_id)
    task_list = build.get_tasks()
    for task in task_list:
        if task.display_name == task_name:
            LOGGER.info("Activating task", task_id=task.task_id, task_name=task.display_name)
            evg_api.configure_task(task.task_id, activated=True)

            # if any(ARCHIVE_DIST_TEST_TASK in dependency["id"] for dependency in task.depends_on):
            #     _activate_archive_debug_symbols(evg_api, task_list)


# def _activate_archive_debug_symbols(evg_api: EvergreenApi, task_list):
#     debug_iter = filter(lambda tsk: tsk.display_name == ACTIVATE_ARCHIVE_DIST_TEST_DEBUG_TASK,
#                         task_list)
#     activate_symbol_tasks = list(debug_iter)
#
#     if len(activate_symbol_tasks) == 1:
#         activated_symbol_task = activate_symbol_tasks[0]
#         if not activated_symbol_task.activated:
#             LOGGER.info("Activating debug symbols archival", task_id=activated_symbol_task.task_id)
#             evg_api.configure_task(activated_symbol_task.task_id, activated=True)


@click.command()
@click.option("--expansion-file", type=str, required=True,
              help="Location of expansions file generated by evergreen.")
@click.option("--evergreen-config", type=str, default=EVG_CONFIG_FILE,
              help="Location of evergreen configuration file.")
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose logging.")
def main(expansion_file: str, evergreen_config: str, verbose: bool) -> None:
    """
    Activate the associated generated executions based in the running build.

    The `--expansion-file` should contain all the configuration needed to generate the tasks.
    \f
    :param expansion_file: Configuration file.
    :param evergreen_config: Evergreen configuration file.
    :param verbose: Use verbose logging.
    """
    enable_logging(verbose)
    expansions = EvgExpansions.from_yaml_file(expansion_file)
    evg_api = RetryingEvergreenApi.get_api(config_file=evergreen_config)

    activate_task(expansions.build_id, expansions.task, evg_api)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
