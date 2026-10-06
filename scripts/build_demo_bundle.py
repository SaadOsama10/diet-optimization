"""Build docs/demo/pybundle.zip, the Python tree the browser demo runs inside Pyodide.

The bundle holds the repository's own src/ and data/ (unchanged), the demo driver, and a
pure-Python copy of pymoo 0.6.1.6 (its compiled extensions are optional and are left out). Two tiny
stand-ins replace packages that cannot run in WebAssembly: moocore (exact hypervolume, compiled C)
and alive_progress (a terminal progress bar pymoo imports but this project never uses).

    python scripts/build_demo_bundle.py
"""
import importlib.metadata
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "docs" / "demo"
PYMOO_VERSION = "0.6.1.6"
SKIP_SUFFIXES = {".so", ".pyd", ".dylib", ".cpp", ".c", ".h", ".pyx", ".pyc"}


def main():
    import pymoo

    version = importlib.metadata.version("pymoo")
    if version != PYMOO_VERSION:
        raise SystemExit(f"pymoo {PYMOO_VERSION} is required to build the bundle (found {version})")
    pymoo_dir = Path(pymoo.__file__).parent
    license_file = next(Path(importlib.metadata.distribution("pymoo")._path).glob("licenses/LICENSE"))

    out = DEMO / "pybundle.zip"
    # fixed timestamps + sorted order so the zip is byte-for-byte reproducible
    stamp = (2020, 1, 1, 0, 0, 0)

    def add(zf, src, arcname):
        info = zipfile.ZipInfo(arcname, stamp)
        info.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(info, Path(src).read_bytes())

    files = []
    for p in sorted(pymoo_dir.rglob("*")):
        if p.is_file() and p.suffix not in SKIP_SUFFIXES and "__pycache__" not in p.parts:
            files.append((p, "pymoo/" + p.relative_to(pymoo_dir).as_posix()))
    files.append((license_file, "pymoo/LICENSE"))
    files += [(DEMO / "shims" / "moocore.py", "moocore.py"), (DEMO / "shims" / "alive_progress.py", "alive_progress.py")]
    files += [(p, "src/" + p.relative_to(ROOT / "src").as_posix()) for p in sorted((ROOT / "src").rglob("*.py"))]
    files += [(ROOT / "scripts" / n, "scripts/" + n) for n in ("_db_env.py", "build_sqlite.py")]
    files += [(p, "data/" + p.name) for p in sorted((ROOT / "data").iterdir()) if p.suffix in {".csv", ".sql"}]
    files.append((DEMO / "runner.py", "runner.py"))

    with zipfile.ZipFile(out, "w") as zf:
        for src, arc in files:
            add(zf, src, arc)
    print(f"{out.relative_to(ROOT)}: {len(files)} files, {out.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
