import sys
from pathlib import Path

# The project's internal imports are relative to blueos_repository/
# (e.g. ``from docker.auth import DockerAuthAPI``).  Add it to sys.path
# so pytest can resolve these the same way the consolidation script does.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "blueos_repository"))
