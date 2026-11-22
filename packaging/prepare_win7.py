"""Prepare a Windows 7 (Python 3.8 + PySide2 + Qt5) staging tree.

Run this with the modern development Python (3.14). The generated tree is
built with Python 3.8.10 and PyInstaller 5.13.2.
"""
from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from pathlib import Path

import libcst as cst

PEP585 = {
    "list": "List",
    "dict": "Dict",
    "tuple": "Tuple",
    "set": "Set",
    "frozenset": "FrozenSet",
}


class AnnotationTransformer(cst.CSTTransformer):
    def __init__(self) -> None:
        self.depth = 0
        self.used: set[str] = set()

    def visit_Annotation(self, node: cst.Annotation) -> None:
        self.depth += 1

    def leave_Annotation(self, original: cst.Annotation, updated: cst.Annotation) -> cst.Annotation:
        self.depth -= 1
        return updated.with_changes(annotation=_convert_unions(updated.annotation, self.used))

    def leave_Subscript(self, original: cst.Subscript, updated: cst.Subscript) -> cst.Subscript:
        if self.depth and isinstance(updated.value, cst.Name):
            replacement = PEP585.get(updated.value.value)
            if replacement:
                self.used.add(replacement)
                return updated.with_changes(value=cst.Name(replacement))
        return updated


def _flatten_union(node: cst.BaseExpression) -> list[cst.BaseExpression]:
    if isinstance(node, cst.BinaryOperation) and isinstance(node.operator, cst.BitOr):
        return _flatten_union(node.left) + _flatten_union(node.right)
    return [node]


def _convert_unions(node: cst.BaseExpression, used: set[str]) -> cst.BaseExpression:
    if isinstance(node, cst.BinaryOperation) and isinstance(node.operator, cst.BitOr):
        members = [m for m in _flatten_union(node) if not (isinstance(m, cst.Name) and m.value == "None")]
        has_none = len(members) != len(_flatten_union(node))
        members = [_convert_unions(m, used) for m in members]
        if has_none:
            used.add("Optional")
            if len(members) == 1:
                inner = members[0]
            else:
                used.add("Union")
                inner = cst.Subscript(
                    value=cst.Name("Union"),
                    slice=[cst.SubscriptElement(slice=cst.Index(value=m)) for m in members],
                )
            return cst.Subscript(
                value=cst.Name("Optional"),
                slice=[cst.SubscriptElement(slice=cst.Index(value=inner))],
            )
        used.add("Union")
        return cst.Subscript(
            value=cst.Name("Union"),
            slice=[cst.SubscriptElement(slice=cst.Index(value=m)) for m in members],
        )
    if isinstance(node, cst.Subscript):
        return node.with_changes(
            slice=[element.with_changes(slice=_convert_subscript_slice(element.slice, used)) for element in node.slice]
        )
    if isinstance(node, cst.Tuple):
        return node.with_changes(elements=[e.with_changes(value=_convert_unions(e.value, used)) for e in node.elements])
    return node


def _convert_subscript_slice(node: cst.SubscriptElement, used: set[str]) -> cst.BaseSlice:
    if isinstance(node, cst.Index):
        return node.with_changes(value=_convert_unions(node.value, used))
    return node


def _add_typing_import(module: cst.Module, used: set[str]) -> cst.Module:
    if not used:
        return module
    import_line = cst.SimpleStatementLine(
        body=[
            cst.ImportFrom(
                module=cst.Name("typing"),
                names=[cst.ImportAlias(name=cst.Name(name)) for name in sorted(used)],
            )
        ]
    )
    body = list(module.body)
    insert_at = 0
    if body and isinstance(body[0], cst.SimpleStatementLine) and len(body[0].body) == 1:
        first = body[0].body[0]
        if isinstance(first, cst.Expr) and isinstance(first.value, cst.SimpleString):
            insert_at = 1
    if insert_at < len(body) and isinstance(body[insert_at], cst.SimpleStatementLine):
        stmt = body[insert_at].body[0]
        if isinstance(stmt, cst.ImportFrom) and isinstance(stmt.module, cst.Name) and stmt.module.value == "__future__":
            insert_at += 1
    body.insert(insert_at, import_line)
    return module.with_changes(body=body)


def transform_annotations(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    module = cst.parse_module(source)
    transformer = AnnotationTransformer()
    updated = module.visit(transformer)
    updated = _add_typing_import(updated, transformer.used)
    result = updated.code.replace('Mapped["Inventory | None"]', 'Mapped[Optional["Inventory"]]')
    if result != source:
        path.write_text(result, encoding="utf-8")


def replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Pattern not found in {path}:\n{old[:200]}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def patch_backend(root: Path) -> None:
    for path in (root / "app").rglob("*.py"):
        transform_annotations(path)

    features = root / "app" / "ml" / "features.py"
    replace(
        features,
        'df["week_of_year"] = iso.week.to_numpy()',
        'df["week_of_year"] = np.asarray(iso.week, dtype="float64")',
    )
    replace(
        features,
        'df["month"] = index.month.to_numpy()',
        'df["month"] = np.asarray(index.month, dtype="int64")',
    )
    replace(
        features,
        "    iso_week = target.isocalendar().week\n",
        '    _iso = target.isocalendar()\n'
        '    iso_week = int(_iso.week if hasattr(_iso, "week") else _iso[1])\n',
    )

    settings = root / "app" / "api" / "settings.py"
    replace(
        settings,
        '"relative_path": str(DB_PATH.relative_to(ROOT_DIR)) if DB_PATH.is_relative_to(ROOT_DIR) else str(DB_PATH),',
        '"relative_path": _relative_path(DB_PATH, ROOT_DIR),',
    )
    replace(
        settings,
        "def database_info(db: Session) -> dict:",
        "def _relative_path(path: Path, base: Path) -> str:\n"
        "    try:\n"
        "        return str(path.relative_to(base))\n"
        "    except ValueError:\n"
        "        return str(path)\n"
        "\n\n"
        "def database_info(db: Session) -> dict:",
    )

    config = root / "app" / "core" / "config.py"
    replace(
        config,
        'ROOT_DIR = Path(__file__).resolve().parents[3]\nload_dotenv(ROOT_DIR / ".env")',
        'import shutil\nimport sys\n\n'
        'if getattr(sys, "frozen", False):\n'
        '    ROOT_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))\n'
        '    _DEFAULT_DATA_DIR = Path(os.getenv("APOTEK_DATA_DIR", Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "ApotekPahala"))\n'
        'else:\n'
        '    ROOT_DIR = Path(__file__).resolve().parents[3]\n'
        '    _DEFAULT_DATA_DIR = ROOT_DIR\n'
        'load_dotenv(ROOT_DIR / ".env")',
    )
    replace(config, 'ROOT_DIR / "storage"', '_DEFAULT_DATA_DIR / "storage"')
    replace(config, 'ROOT_DIR / "models"', '_DEFAULT_DATA_DIR / "models"')
    replace(config, 'ROOT_DIR / "backups"', '_DEFAULT_DATA_DIR / "backups"')
    replace(
        config,
        'DB_PATH = Path(os.getenv("APOTEK_DB_PATH", STORAGE_DIR / "apotek_pahala.db"))\n',
        'DB_PATH = Path(os.getenv("APOTEK_DB_PATH", STORAGE_DIR / "apotek_pahala.db"))\n'
        'if getattr(sys, "frozen", False) and not DB_PATH.exists():\n'
        '    _seed_db = ROOT_DIR / "storage" / "apotek_pahala.db"\n'
        '    if _seed_db.exists():\n'
        '        DB_PATH.parent.mkdir(parents=True, exist_ok=True)\n'
        '        shutil.copy2(_seed_db, DB_PATH)\n',
    )

    run_py = root / "run.py"
    replace(
        run_py,
        'import argparse\n\nimport uvicorn',
        'import argparse\nimport logging\nimport os\nimport sys\nfrom logging.handlers import RotatingFileHandler\nfrom pathlib import Path\n\nimport uvicorn',
    )
    replace(
        run_py,
        '    args = parser.parse_args()\n    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)',
        '    args = parser.parse_args()\n'
        '    if getattr(sys, "frozen", False):\n'
        '        data_dir = Path(os.getenv("APOTEK_DATA_DIR", Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "ApotekPahala"))\n'
        '        log_dir = data_dir / "logs"\n'
        '        log_dir.mkdir(parents=True, exist_ok=True)\n'
        '        handler = RotatingFileHandler(log_dir / "backend.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")\n'
        '        logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s", handlers=[handler])\n'
        '        from app.main import app as fastapi_app\n'
        '        uvicorn.run(fastapi_app, host=args.host, port=args.port, log_config=None)\n'
        '    else:\n'
        '        uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)',
    )


def patch_desktop(root: Path) -> None:
    for path in list(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        text = text.replace("PySide6", "PySide2")
        text = text.replace("event.position().x()", "event.localPos().x()")
        text = text.replace(".exec()", ".exec_()")
        path.write_text(text, encoding="utf-8")

    theme = root / "app" / "core" / "theme.py"
    replace(
        theme,
        '        if app is not None:\n'
        '            hint = app.styleHints().colorScheme()\n'
        '            if hint == Qt.ColorScheme.Dark:\n'
        '                return "dark"\n'
        '        return "light"\n',
        '        if app is not None:\n'
        '            try:\n'
        '                hint = app.styleHints().colorScheme()\n'
        '                if hint == Qt.ColorScheme.Dark:\n'
        '                    return "dark"\n'
        '            except AttributeError:\n'
        '                pass\n'
        '        return "light"\n',
    )

    config = root / "app" / "core" / "config.py"
    replace(config, "import os\nfrom pathlib import Path", "import os\nimport sys\nfrom pathlib import Path")
    replace(
        config,
        'DESKTOP_DIR = Path(__file__).resolve().parents[2]\nROOT_DIR = DESKTOP_DIR.parent\nASSETS_DIR = DESKTOP_DIR / "app" / "assets"\nICONS_DIR = ASSETS_DIR / "icons"\nLOGO_PATH = ASSETS_DIR / "logo.png"\nBACKEND_DIR = ROOT_DIR / "backend"',
        'if getattr(sys, "frozen", False):\n'
        '    DESKTOP_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))\n'
        '    ROOT_DIR = Path(sys.executable).resolve().parent\n'
        '    BACKEND_DIR = ROOT_DIR / "backend"\n'
        'else:\n'
        '    DESKTOP_DIR = Path(__file__).resolve().parents[2]\n'
        '    ROOT_DIR = DESKTOP_DIR.parent\n'
        '    BACKEND_DIR = ROOT_DIR / "backend"\n'
        'ASSETS_DIR = DESKTOP_DIR / "app" / "assets"\n'
        'ICONS_DIR = ASSETS_DIR / "icons"\n'
        'LOGO_PATH = ASSETS_DIR / "logo.png"',
    )

    launcher = root / "app" / "core" / "backend.py"
    replace(
        launcher,
        "import socket\nimport sys\nimport time",
        "import os\nimport socket\nimport sys\nimport time",
    )
    replace(
        launcher,
        "from PySide2.QtCore import QObject, QProcess, QTimer, Signal",
        "from PySide2.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, Signal",
    )
    replace(
        launcher,
        '        run_script = BACKEND_DIR / "run.py"\n'
        '        if not run_script.exists():\n'
        '            self.failed.emit(\n'
        '                f"Berkas backend tidak ditemukan di {run_script}. Jalankan backend secara manual."\n'
        '            )\n'
        '            return\n\n'
        '        if self.process is None:\n'
        '            self.process = QProcess(self)\n'
        '            self.process.setWorkingDirectory(str(BACKEND_DIR))\n'
        '            self.process.setProgram(sys.executable)\n'
        '            self.process.setArguments(["run.py", "--host", host, "--port", str(port)])\n'
        '            self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)\n'
        '            self.process.readyReadStandardOutput.connect(self._read_output)\n'
        '            self.process.finished.connect(self._on_process_finished)',
        '        frozen = bool(getattr(sys, "frozen", False))\n'
        '        run_script = BACKEND_DIR / "run.py"\n'
        '        backend_exe = BACKEND_DIR / "apotek-backend.exe"\n'
        '        if frozen and not backend_exe.exists():\n'
        '            self.failed.emit(f"Program backend tidak ditemukan di {backend_exe}.")\n'
        '            return\n'
        '        if not frozen and not run_script.exists():\n'
        '            self.failed.emit(\n'
        '                f"Berkas backend tidak ditemukan di {run_script}. Jalankan backend secara manual."\n'
        '            )\n'
        '            return\n\n'
        '        if self.process is None:\n'
        '            self.process = QProcess(self)\n'
        '            self.process.setWorkingDirectory(str(BACKEND_DIR))\n'
        '            if frozen:\n'
        '                self.process.setProgram(str(backend_exe))\n'
        '                # Bind ke semua antarmuka agar PWA mobile dapat dibuka dari perangkat lain.\n'
        '                self.process.setArguments(["--host", "0.0.0.0", "--port", str(port)])\n'
        '                environment = QProcessEnvironment.systemEnvironment()\n'
        '                data_dir = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "ApotekPahala"\n'
        '                environment.insert("APOTEK_DATA_DIR", str(data_dir))\n'
        '                self.process.setProcessEnvironment(environment)\n'
        '            else:\n'
        '                self.process.setProgram(sys.executable)\n'
        '                self.process.setArguments(["run.py", "--host", host, "--port", str(port)])\n'
        '            self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)\n'
        '            self.process.readyReadStandardOutput.connect(self._read_output)\n'
        '            self.process.finished.connect(self._on_process_finished)',
    )

    run_py = root / "run.py"
    replace(
        run_py,
        "    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False)\n",
        "    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)\n"
        "    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)\n"
        "    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False)\n",
    )


def copy_tree(source: Path, target: Path) -> None:
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"))


def stage(project: Path, out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    copy_tree(project / "backend" / "app", out / "backend" / "app")
    shutil.copy2(project / "backend" / "run.py", out / "backend" / "run.py")
    copy_tree(project / "desktop", out / "desktop")
    copy_tree(project / "mobile-web" / "dist", out / "mobile-web" / "dist")
    copy_tree(project / "datasets", out / "datasets")

    storage = out / "storage"
    storage.mkdir(parents=True)
    source_db = project / "storage" / "apotek_pahala.db"
    target_db = storage / "apotek_pahala.db"
    with sqlite3.connect(str(source_db)) as src, sqlite3.connect(str(target_db)) as dst:
        src.backup(dst)
    # secret.key sengaja tidak dibundel: setiap instalasi membuat kunci JWT
    # sendiri pada saat pertama dijalankan agar tidak ada kunci yang dibagi.

    patch_backend(out / "backend")
    patch_desktop(out / "desktop")
    print(f"staged {out}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    stage(args.project.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
