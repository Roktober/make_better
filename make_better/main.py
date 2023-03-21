import argparse
import dataclasses
import subprocess  # nosec: B404
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, List, Sequence, Tuple, Union

import pkg_resources

from make_better import __name__ as pkg_name

if TYPE_CHECKING:
    _CMD = Sequence[Union[str, PathLike[str]]]

_MAKE_BETTER_CONFIGS_DIR = "configs/"


@dataclasses.dataclass
class _Options:
    paths: List[Path]
    autoformat: bool
    config_path: Path
    output_succeed: bool
    line_length: int


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
    args = parser.parse_args()

    _check_paths_exist(args.paths)
    _check_path_exist(args.config_path)

    return _Options(
        paths=args.paths,
        autoformat=args.autoformat,
        config_path=args.config_path,
        output_succeed=args.output_succeed,
        line_length=args.line_length,
    )


def _run_command(args: "_CMD") -> _CommandResult:
    res = subprocess.run(
        args=args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )  # nosec B603
    return _CommandResult(
        output=res.stdout.decode(), return_code=res.returncode, program=str(args[0])
    )


def _start_formatter(options: _Options) -> Tuple[_CommandResult, _CommandResult]:
    return (
        _run_command(
            [
                "isort",
                "--config-root",
                str(options.config_path),
                "--line-length",
                str(options.line_length),
                "--resolve-all-configs",
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
                *options.paths,
            ]
        ),
    )


def _start_linter(
    options: _Options,
) -> Tuple[_CommandResult, _CommandResult]:
    return (
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
    )


def _output(results: List[_CommandResult], output_succeed: bool) -> None:
    has_error = False
    for res in results:
        is_error_code = bool(res.return_code)
        if is_error_code or output_succeed:
            print(  # noqa: T201
                f"{res.program} completed with code {res.return_code}\n{res.output}\n"
            )
            has_error = is_error_code or has_error

    if has_error:
        exit(1)


def main() -> None:
    options = _parse_args()
    result: List[_CommandResult] = []
    if options.autoformat:
        result.extend(_start_formatter(options))
    result.extend(_start_linter(options))
    _output(result, options.output_succeed)


if __name__ == "__main__":
    main()
