import sys
import os

# Ensure the project root is always on the path,
# regardless of how / from where the script is launched.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ui.main_window import run_app

if __name__ == "__main__":
    run_app()