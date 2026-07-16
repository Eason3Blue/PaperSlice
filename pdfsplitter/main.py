"""PDF Poster Splitter - 入口点."""

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from pdfsplitter.bootstrap import App


def main() -> None:
    """应用入口函数."""
    app = App()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
