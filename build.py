"""Build script — 使用 PyInstaller 打包为 Windows exe."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
APP_NAME = "PaperSlice"
MAIN_SCRIPT = PROJECT_ROOT / "pdfsplitter" / "main.py"
ICON_PATH = PROJECT_ROOT / "resources" / "icon" / "icon.ico"


def clean() -> None:
    """清理上次构建产物."""
    for d in ["build", "dist"]:
        path = PROJECT_ROOT / d
        if path.exists():
            shutil.rmtree(path)
    for spec in PROJECT_ROOT.glob("*.spec"):
        spec.unlink()


def build() -> None:
    """执行 PyInstaller 打包."""
    if not ICON_PATH.exists():
        print(f"[WARN] 图标文件不存在: {ICON_PATH}")
        icon_arg = []
    else:
        icon_arg = ["--icon", str(ICON_PATH)]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onefile",
        "--windowed",
        "--clean",
        "--add-data", f"resources{os.pathsep}resources",
        *icon_arg,
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtGui",
        "--hidden-import", "PySide6.QtWidgets",
        "--hidden-import", "fitz",
        "--hidden-import", "pypdf",
        "--hidden-import", "rich.logging",
        "--collect-submodules", "pdfsplitter",
        str(MAIN_SCRIPT),
    ]

    print(f"[BUILD] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if result.returncode == 0:
        exe = PROJECT_ROOT / "dist" / f"{APP_NAME}.exe"
        print(f"[OK] 打包完成: {exe}")
    else:
        print(f"[FAIL] 打包失败, 返回码: {result.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    if "--clean" in sys.argv:
        clean()
        print("[CLEAN] 已清理 build/dist")
    else:
        clean()
        build()
