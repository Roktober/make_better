import argparse
import dataclasses
import subprocess  # nosec: B404
from pathlib import Path

import pkg_resources

from make_better import __name__ as pkg_name

_MAKE_BETTER_CONFIGS_DIR = "configs/"


@dataclasses.dataclass
class _Options:
    path: Path
    autoformat: bool
    config_path: Path
    output_succeed: bool
    line_length: int


@dataclasses.dataclass
class _CommandResult:
    program: str
    output: str
    return_code: int


def _parse_args() -> _Options:
    parser = argparse.ArgumentParser(
        prog=pkg_name, description="Autoformat and lint you code"
    )
    parser.add_argument(
        "dir",
        type=Path,
        default=".",
        nargs="?",
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

    if not args.dir.exists():
        raise ValueError("Path '{path}' does not exist".format(path=str(args.dir)))

    if not args.config_path.exists():
        raise ValueError(
            "Config path '{path}' does not exist".format(path=str(args.config_path))
        )

    return _Options(
        path=args.dir,
        autoformat=args.autoformat,
        config_path=args.config_path,
        output_succeed=args.output_succeed,
        line_length=args.line_length,
    )


def _run_command(args: list[str]) -> _CommandResult:
    res = subprocess.run(
        args=args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )  # nosec B603
    return _CommandResult(
        output=res.stdout.decode(), return_code=res.returncode, program=args[0]
    )


def _start_formatter(options: _Options) -> tuple[_CommandResult, _CommandResult]:
    return (
        _run_command(
            [
                "isort",
                "--config-root",
                str(options.config_path),
                "--line-length",
                str(options.line_length),
                "--resolve-all-configs",
                str(options.path),
            ]
        ),
        _run_command(
            [
                "black",
                "--config",
                str(options.config_path / "pyproject.toml"),
                "--line-length",
                str(options.line_length),
                str(options.path),
            ]
        ),
    )


def _start_linter(
    options: _Options,
) -> tuple[_CommandResult, _CommandResult]:
    return (
        _run_command(
            [
                "bandit",
                "-c",
                str(options.config_path / "pyproject.toml"),
                "-r",
                str(options.path),
            ]
        ),
        _run_command(
            [
                "flake8",
                "--config",
                str(options.config_path / Path("setup.cfg")),
                str(options.path),
            ]
        ),
    )


def _output(results: list[_CommandResult], output_succeed: bool) -> None:
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
    result: list[_CommandResult] = []
    if options.autoformat:
        result.extend(_start_formatter(options))
    result.extend(_start_linter(options))
    _output(result, options.output_succeed)
