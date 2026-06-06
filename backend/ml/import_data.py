"""
Legacy import script - redirects to the Django management command.

Use the management command instead:
    uv run python manage.py import_houses <csv_path>
    uv run python manage.py import_houses --generate-sample
    uv run python manage.py import_houses --generate-sample --count 2000

This script is kept for backward compatibility with CLAUDE.md references.
"""

import subprocess
import sys


def main():
    """Delegate to the Django management command."""
    cmd = [sys.executable, "manage.py", "import_houses"] + sys.argv[1:]
    print(f"Redirecting to: {' '.join(cmd)}")
    subprocess.run(cmd, check=False)


if __name__ == "__main__":
    main()
