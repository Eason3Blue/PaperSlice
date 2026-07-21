# AGENTS.md — PaperSlice Project Guide

## Quick Start
```powershell
# Run app (production)
.venv\Scripts\python.exe -m pdfsplitter.main

# Run app (debug logging)
$env:pdfsplitter_DEV = "1"; .venv\Scripts\python.exe -m pdfsplitter.main

# Run all tests
.venv\Scripts\python.exe -m pytest tests/ -v

# Run tests per module
.venv\Scripts\python.exe -m pytest tests/domain/geometry/ -v
.venv\Scripts\python.exe -m pytest tests/domain/layout/ -v

# Build exe (always does clean + build)
.venv\Scripts\python.exe build.py --clean
```

## Architecture: Clean Architecture + MVVM
```
Presentation (PySide6)  →  ViewModel  →  UseCase  →  Repository Interface  →  MuPDF
```
- `bootstrap.py:App` is the DI composition root — all wiring happens here.
- Absolute imports only: `from pdfsplitter.domain.geometry.rect import Rect`
- Import order: stdlib → third-party → local (alphabetical within each group).

## Layer Constraints (enforced by existing architecture)
| Layer | Allowed | Forbidden |
|-------|---------|-----------|
| `domain/` | stdlib only | Qt, PyMuPDF, pypdf |
| `application/` | domain, application | Qt, PyMuPDF |
| `infrastructure/` | domain, application, fitz/pypdf | Qt (except logging) |
| `presentation/` | DTOs only (not domain objects) | PyMuPDF, raw fitz |

## Known Architectural Violations (do not copy these patterns)
1. **`application/export_usecase.py:15`** — `ExportUseCase` directly imports `PdfSplitter` from infrastructure. Should go through an export strategy interface.
2. **`presentation/main_viewmodel.py`** — `MainViewModel.render_page_preview()` calls `fitz` directly. Should use a render repository/service.
3. The `Length` unit value-object (`domain/units/length.py`) exists but is unused — all code uses raw floats with `MM_TO_PT = 72.0 / 25.4`.
4. `domain/event/event_bus.py` exists but no component subscribes to it — use Qt Signals for communication.
5. `application/pipeline.py` exists but `Pipeline.execute()` is never called — export orchestration is manual in `ExportUseCase`.

## Code Style
- **Docstrings**: Google style (Args/Returns/Raises), required on all public API.
- **Dataclasses**: `frozen=True` for value objects, `field(default_factory=list)` for mutable defaults.
- **Naming**: `snake_case` for modules/functions/vars, `CapWords` for classes, `UPPER_CASE` for constants, `_private` prefix for internals.
- **Qt signals**: Name with `_signal` suffix (e.g., `document_loaded_signal`).
- **Logging**: `logging.getLogger(__name__)` per module. Never `print()`.
- **No lint/typecheck config** exists in this repo (no ruff, mypy, pyproject.toml).

## Key Files
| File | Role |
|------|------|
| `pdfsplitter/bootstrap.py` | DI container, assembles all components |
| `pdfsplitter/main.py` | Entry point |
| `pdfsplitter/presentation/main_viewmodel.py` | Central VM, all app state + signals |
| `pdfsplitter/presentation/main_window.py` | Main window, wire signals in `_connect_signals()` |
| `pdfsplitter/presentation/preview_widget.py` | QGraphicsView with draggable lines + tile ordering |
| `pdfsplitter/infrastructure/pdf_splitter.py` | Core split logic, `split()` / `split_all()` |
| `pdfsplitter/infrastructure/mupdf_repository.py` | MuPDF adapter, `supports()` + `load()` |
| `pdfsplitter/domain/layout/layout_engine.py` | Pure geometry: `calculate()` + `calculate_from_lines()` |
| `pdfsplitter/domain/layout/split_lines.py` | Split line builder: vertical/horizontal, presets, drag |
| `pdfsplitter/infrastructure/config.py` | `ConfigService` — reads/writes `settings.json` |

## Repo Quirks
- `settings.json` is **gitignored** and lives at repo root (not inside `pdfsplitter/`).
- `logs/` directory is auto-created at repo root by `logging_config.py`.
- `.ppslc` is the JSON-based project save format for page configurations.
- App UI is Chinese-first (`language: "zh_CN"` default); strings are mostly in Chinese.
- `build.py` always runs `clean()` first (even without `--clean`). `--clean` only cleans without building.

## Build & Packaging
- PyInstaller spec: `PaperSlice.spec` (hardcoded absolute paths — regenerate via `build.py`).
- Icons: `resources/icon/icon.ico`.
- Hidden imports required: `PySide6.QtCore`, `PySide6.QtGui`, `PySide6.QtWidgets`, `fitz`, `pypdf`, `rich.logging`.
