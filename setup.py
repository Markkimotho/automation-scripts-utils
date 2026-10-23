"""Build the installable Automation Scripts & Utils command and bundled scripts."""
from pathlib import Path
from setuptools import setup

ROOT = Path(__file__).resolve().parent
files = []
for folder in ("catalog", "scripts", "packages", "research"):
    for file in sorted((ROOT / folder).rglob("*")):
        if file.is_file() and "__pycache__" not in file.parts and not file.name.endswith((".pyc", ".pyo")):
            destination = Path("share/automation-scripts-utils") / file.parent.relative_to(ROOT)
            files.append((str(destination), [str(file.relative_to(ROOT))]))
setup(data_files=files)
