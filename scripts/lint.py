#!/usr/bin/env python3
import os
import subprocess
import sys

EXCLUDE = [
    ".venv",
    "venv",
    "__pycache__",
    "python",
    "site-packages",
    ".git",
    "node_modules",
    "cdk.out",
]


def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exclude_arg = ",".join(EXCLUDE)
    black_exclude = "(" + "|".join(EXCLUDE) + ")"
    print(f"Auto-formatting with black from {root_dir} (excluding: {black_exclude})")
    subprocess.run(
        [sys.executable, "-m", "black", root_dir, "--exclude", black_exclude],
        check=True,
    )
    print(
        f"Auto-sorting imports with isort from {root_dir} (using .isort.cfg for exclusions)"
    )
    subprocess.run([sys.executable, "-m", "isort", root_dir], check=True)
    print(f"Auto-fixing with ruff from {root_dir} (excluding: {exclude_arg})")
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                root_dir,
                "--exclude",
                exclude_arg,
                "--fix",
            ],
            check=True,
        )
    except FileNotFoundError:
        print("ruff not installed, skipping ruff auto-fix.")
    print("Auto-formatting and auto-fixing complete.")


if __name__ == "__main__":
    main()
