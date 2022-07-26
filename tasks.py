"""
PyInvoke developer task file
https://www.pyinvoke.org/

These tasks can be run using `invoke <NAME>` or `inv <NAME>` from the project root.

To show all available tasks `invoke --list`

To show task help page `invoke <NAME> --help`
"""
import invoke

from scripts import check_type_hint_coverage

_CHECK_HELP_DESC = "Only checks for needed changes without writing back. Exit with error code if changes needed."
_EXCLUDE_HELP_DESC = "Exclude files or directories"
_PATH_HELP_DESC = "Target path. (Default: .)"


@invoke.task(
    help={
        "check": _CHECK_HELP_DESC,
        "exclude": _EXCLUDE_HELP_DESC,
        "path": _PATH_HELP_DESC,
    }
)
def sort(ctx, path=".", check=False, exclude=None):
    """Sort module imports."""
    cmds = ["isort", path, "--profile", "black"]
    if check:
        cmds.append("--check-only")
    if exclude:
        cmds.extend(["--skip", exclude])
    ctx.run(" ".join(cmds))


@invoke.task(
    help={
        "check": _CHECK_HELP_DESC,
        "exclude": _EXCLUDE_HELP_DESC,
        "path": _PATH_HELP_DESC,
        "sort": "Disable import sorting. Runs by default.",
    }
)
def fmt(ctx, path=".", sort_=True, check=False, exclude=None):
    """
    Run code formatter.
    """
    if sort_:
        sort(ctx, path, check=check, exclude=exclude)

    cmds = ["black", path]
    if check:
        cmds.append("--check")
    if exclude:
        cmds.extend(["--exclude", exclude])
    ctx.run(" ".join(cmds))


@invoke.task
def lint(ctx, path="great_expectations/core"):
    """Run code linter"""
    cmds = ["flake8", path]
    ctx.run(" ".join(cmds))


@invoke.task(help={"path": _PATH_HELP_DESC})
def upgrade(ctx, path="."):
    """Run code syntax upgrades."""
    cmds = ["pyupgrade", path, "--py3-plus"]
    ctx.run(" ".join(cmds))


@invoke.task(
    help={
        "all_files": "Run hooks against all files, not just the current changes.",
        "diff": "Show the diff of changes on hook failure.",
        "sync": "Re-install the latest git hooks.",
    }
)
def hooks(ctx, all_files=False, diff=False, sync=False):
    """Run and manage pre-commit hooks."""
    cmds = ["pre-commit", "run"]
    if diff:
        cmds.append("--show-diff-on-failure")
    if all_files:
        cmds.extend(["--all-files"])
    else:
        # used in CI - runs faster and only checks files that have changed
        cmds.extend(["--from-ref", "origin/HEAD", "--to-ref", "HEAD"])

    ctx.run(" ".join(cmds))

    if sync:
        print("  Re-installing hooks ...")
        ctx.run(" ".join(["pre-commit", "uninstall"]), echo=True)
        ctx.run(" ".join(["pre-commit", "install"]), echo=True)


@invoke.task(aliases=["type-cov"])  # type: ignore
def type_coverage(ctx):
    """
    Check total type-hint coverage compared to `develop`.
    """
    try:
        check_type_hint_coverage.main()
    except AssertionError as err:
        raise invoke.Exit(message=str(err), code=1)


# numbers next to each package represent the last known number of typing errors.
# when errors reach 0 please uncomment the module so it becomes type-checked by default.
DEFAULT_PACKAGES_TO_TYPE_CHECK = [
    # "checkpoint",  # 78
    # "cli",  # 237
    # "core",  # 242
    # "data_asset",  # 1
    # "data_context",  # 272
    # "datasource",  # 98
    # "exceptions",  # 2
    # "execution_engine",  # 109
    # "expectations",  # 462
    # "jupyter_ux",  # 4
    # "marshmallow__shade",  # 14
    "profile",  # 0
    # "render",  # 87
    # "rule_based_profiler",  # 469
    # "self_check",  # 10
    # "types",  # 3
    # "validation_operators", # 47
    # "validator",  # 46
    # util.py # 28
]


@invoke.task(
    aliases=["types"],
    iterable=["packages"],
    help={
        "packages": f"One or more packages to type-check with mypy. (Default: {DEFAULT_PACKAGES_TO_TYPE_CHECK})",
        "show-default-packages": "Print the default packages to type-check and then exit.",
        "install-types": "Automatically install any needed types from `typeshed`.",
    },
)
def type_check(ctx, packages, install_types=False, show_default_packages=False):
    """Run mypy static type-checking on select packages."""
    if show_default_packages:
        # Use this to keep the Type-checking section of the docs up to date.
        # https://docs.greatexpectations.io/docs/contributing/style_guides/code_style#type-checking
        print("\n".join(DEFAULT_PACKAGES_TO_TYPE_CHECK))
        raise invoke.Exit(code=0)

    packages = packages or DEFAULT_PACKAGES_TO_TYPE_CHECK
    # once we have sunsetted `type-coverage` and our typing has matured we should define
    # our packages to exclude (if any) in the mypy config file.
    # https://mypy.readthedocs.io/en/stable/config_file.html#confval-exclude
    ge_pkgs = [f"great_expectations/{p}" for p in packages]
    cmds = [
        "mypy",
        *ge_pkgs,
    ]
    if install_types:
        cmds.extend(["--install-types", "--non-interactive"])
    ctx.run(" ".join(cmds), echo=True)
