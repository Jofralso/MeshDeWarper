#!/usr/bin/env python3
"""Build the MeshDeWarper .curapackage for Cura 5.x distribution.

Usage:
    python scripts/build_curaplugin.py [--version X.Y.Z]

Produces dist/MeshDeWarper-X.Y.Z.curapackage (a zip with plugins/ subdirectory).
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path


def _load_version() -> str:
    version: dict[str, str] = {}
    src = Path(__file__).resolve().parent.parent / "src" / "mesh_de_warper" / "__version__.py"
    exec(src.read_text(), version)
    return version["__version__"]


def build(version: str | None = None) -> Path:
    root = Path(__file__).resolve().parent.parent
    src_pkg = root / "src" / "mesh_de_warper"
    plugin_json = root / "plugin.json"

    if not src_pkg.is_dir():
        sys.exit(f"Package source not found: {src_pkg}")
    if not plugin_json.is_file():
        sys.exit(f"Plugin manifest not found: {plugin_json}")

    if version is None:
        version = _load_version()

    dist_dir = root / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    output = dist_dir / f"MeshDeWarper-{version}.curapackage"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Cura 5.x expects: plugins/<plugin_name>/...
        plugins_dir = tmp_path / "plugins"
        plugin_dst = plugins_dir / "mesh_de_warper"

        shutil.copytree(str(src_pkg), str(plugin_dst))
        shutil.copy2(str(plugin_json), str(tmp_path / "plugin.json"))

        # Remove dev/CI artefacts from the package
        for d in ("__pycache__", ".git", ".mypy_cache", ".ruff_cache", ".pytest_cache"):
            for p in plugin_dst.rglob(d):
                if p.is_dir():
                    shutil.rmtree(p)

        with zipfile.ZipFile(str(output), "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(str(tmp_path / "plugin.json"), "plugin.json")
            for f in plugin_dst.rglob("*"):
                if f.is_file():
                    arcname = f"plugins/mesh_de_warper/{f.relative_to(plugin_dst)}"
                    zf.write(str(f), arcname)

    print(f"Built: {output} ({output.stat().st_size / 1024:.1f} KiB)")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build .curapackage for Cura 5.x")
    parser.add_argument("--version", help="Override version string")
    args = parser.parse_args()
    build(args.version)
