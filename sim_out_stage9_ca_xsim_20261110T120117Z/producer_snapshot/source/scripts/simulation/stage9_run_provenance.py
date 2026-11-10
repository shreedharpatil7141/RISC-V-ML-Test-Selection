#!/usr/bin/env python3
"""Capture exact producer/input bytes and reject mid-run source changes."""
import hashlib
import json
import shutil
from pathlib import Path


def capture_snapshot(directory: Path, sources: list[Path], inputs: list[Path], command: list[str]) -> Path:
    directory.mkdir(parents=True, exist_ok=False)
    entries=[]
    for kind,paths in (("source",sources),("input",inputs)):
        for path in sorted({Path(p).resolve() for p in paths},key=str):
            if not path.is_file(): raise FileNotFoundError(f"snapshot {kind} missing: {path}")
            data=path.read_bytes(); digest=hashlib.sha256(data).hexdigest()
            try: rel=path.relative_to(Path.cwd().resolve())
            except ValueError: rel=Path(path.name)
            saved=directory/kind/rel
            saved.parent.mkdir(parents=True,exist_ok=True); saved.write_bytes(data)
            entries.append({"kind":kind,"path":str(path),"snapshot":str(saved),"sha256":digest})
    manifest={"schema":"stage9-producer-snapshot-1","command":command,"files":entries}
    target=directory/"snapshot.json"
    target.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8",newline="\n")
    return target


def verify_snapshot(manifest_path: Path) -> None:
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        path=Path(entry["path"])
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=entry["sha256"]:
            raise RuntimeError(f"producer/input changed during run: {path}")
        snapshot=Path(entry["snapshot"])
        if not snapshot.is_file() or hashlib.sha256(snapshot.read_bytes()).hexdigest()!=entry["sha256"]:
            raise RuntimeError(f"producer snapshot corrupt: {snapshot}")

