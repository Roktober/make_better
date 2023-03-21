import argparse
import dataclasses
import itertools
import logging
import subprocess  # nosec: B404
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, List, Sequence, Union

import pkg_resources

from make_better import __name__ as pkg_name

if TYPE_CHECKING:
    _CMD = Sequence[Union[str, PathLike[str]]]

logger = logging.getLogger(__name__)

_MAKE_BETTER_CONFIGS_DIR = "configs/"


@dataclasses.dataclass
class _Options:
    paths: List[Path]
    autoformat: bool
    config_path: Path
    output_succeed: bool
    line_length: int
    check_formatting: bool


@dataclasses.dataclass
class _CommandResult:
    program: str
    output: str
    return_code: int


def _check_path_exist(path: Path) -> None:
    if not path.exists():
        raise ValueError(f"Path '{path}' does not exist")


def _check_paths_exist(paths: List[Path]) -> None:
    for path in paths:
        _check_path_exist(path)


def _parse_args() -> _Options:
    parser = argparse.ArgumentParser(
        prog=pkg_name, description="Autoformat and lint you code"
    )
    parser.add_argument(
        "paths",
        type=Path,
        default=[Path(".")],
        nargs="*",
    )
    parser.add_argument(
        "-f", "--autoformat", action="store_true", help="Enable autoformatting code"
    )
    parser.add_argument(
        "-o",
        "--output-succeed",
        action="store_true",
        help="Enables output of linters and formatter results on successful exit code",
    )
    parser.add_argument(
        "-c",
        "--config-path",
        default=Path(pkg_resources.resource_filename(pkg_name, _MAKE_BETTER_CONFIGS_DIR)),
        help="Path to the directory with configurations",
    )
    parser.add_argument(
        "-l",
        "--line-length",
        default=90,
        type=int,
        help="Configure line-length for isort and black",
    )
    parser.add_argument(
        "-g",
        "--check-formatting",
        action="store_true",
        help="Checking code formatting. Has more priority then --autoformat",
    )
    args = parser.parse_args()

    _check_paths_exist(args.paths)
    _check_path_exist(args.config_path)

    return _Options(
        paths=args.paths,
        autoformat=args.autoformat,
        config_path=args.config_path,
        output_succeed=args.output_succeed,
        line_length=args.line_length,
        check_formatting=args.check_formatting,
    )


def _run_command(args: "_CMD") -> _CommandResult:
    logger.debug(f"run command args: {args}")
    res = subprocess.run(
        args=args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )  # nosec B603
    return _CommandResult(
        output=res.stdout.decode(), return_code=res.returncode, program=str(args[0])
    )


def _start_formatter(options: _Options) -> List[_CommandResult]:
    black_additional_options = []
    isort_additional_options = []
    if not options.check_formatting and not options.autoformat:
        return []

    if options.check_formatting:
        black_additional_options.append("--check")
        isort_additional_options.append("--check")

    return [
        _run_command(
            [
                "isort",
                "--config-root",
                str(options.config_path),
                "--line-length",
                str(options.line_length),
                "--resolve-all-configs",
                *isort_additional_options,
                *options.paths,
            ]
        ),
        _run_command(
            [
                "black",
                "--config",
                str(options.config_path / "pyproject.toml"),
                "--line-length",
                str(options.line_length),
                *black_additional_options,
                *options.paths,
            ]
        ),
    ]


def _start_linter(
    options: _Options,
) -> List[_CommandResult]:
    return [
        _run_command(
            [
                "bandit",
                "-c",
                str(options.config_path / "pyproject.toml"),
                "-r",
                *options.paths,
            ]
        ),
        _run_command(
            [
                "flake8",
                "--config",
                str(options.config_path / Path("setup.cfg")),
                *options.paths,
            ]
        ),
    ]


def _make_better(options: _Options) -> None:
    has_error = False
    for res in itertools.chain(_start_formatter(options), _start_linter(options)):
        is_error_code = bool(res.return_code)
        if is_error_code or options.output_succeed:
            print(  # noqa: T201
                f"{res.program} completed with code {res.return_code}\n{res.output}\n"
            )
            has_error = is_error_code or has_error

    if has_error:
        exit(1)


def main() -> None:
    options = _parse_args()
    _make_better(options)


if __name__ == "__main__":
    main()
