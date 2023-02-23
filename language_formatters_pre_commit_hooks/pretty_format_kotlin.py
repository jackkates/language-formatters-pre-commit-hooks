# -*- coding: utf-8 -*-
import argparse
import sys
import typing

from language_formatters_pre_commit_hooks import _get_default_version
from language_formatters_pre_commit_hooks.pre_conditions import java_required
from language_formatters_pre_commit_hooks.utils import download_url
from language_formatters_pre_commit_hooks.utils import run_command

def _fix_paths(paths: typing.Iterable[str]) -> typing.Iterable[str]:
    # Starting from KTLint 0.41.0 paths cannot contain backward slashes as path separator
    # Odd enough the error messages reported by KTLint contain `\` :(
    for path in paths:
        yield path.replace("\\", "/")


@java_required
def pretty_format_kotlin(argv: typing.Optional[typing.List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--autofix",
        action="store_true",
        dest="autofix",
        help="Automatically fixes encountered not-pretty-formatted files",
    )
    parser.add_argument(
        "--ktlint-version",
        dest="ktlint_version",
        default=_get_default_version("ktlint"),
        help="KTLint version to use (default %(default)s)",
    )

    parser.add_argument("filenames", nargs="*", help="Filenames to fix")
    args = parser.parse_args(argv)

    # ktlint does not return exit-code!=0 if we're formatting them.
    # To workaround this limitation we do run ktlint in check mode only,
    # which provides the expected exit status and we run it again in format
    # mode if autofix flag is enabled
    check_status, check_output = run_command(
        "ktlint", "--log-level", "info", "--relative", "--", *_fix_paths(args.filenames)
    )

    not_pretty_formatted_files: typing.Set[str] = set()
    if check_status != 0:
        print(check_output)
        not_pretty_formatted_files.update(line.split(":", 1)[0] for line in check_output.splitlines())

        if args.autofix:
            run_command(
                "ktlint",
                "--log-level",
                "info",
                "--relative",
                "--format",
                "--",
                *_fix_paths(not_pretty_formatted_files),
            )

    status = 0
    if not_pretty_formatted_files:
        status = 1

    return status


if __name__ == "__main__":
    sys.exit(pretty_format_kotlin())
