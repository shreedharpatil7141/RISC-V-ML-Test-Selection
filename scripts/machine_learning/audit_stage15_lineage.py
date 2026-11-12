#!/usr/bin/env python3
"""Audit frozen Stage 11-14 hashes without changing manifests or artifacts."""
import argparse
import csv
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEXT_EXTENSIONS = {".csv", ".json", ".txt", ".m", ".bat", ".md"}
IMAGE_MAP_PATH = "reports/stage15_evidence/program_image_map.csv"
_IMAGE_MAP = None


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def lf_bytes(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def normalize_rel(rel: str) -> str:
    rel = rel.replace("\\", "/")
    if rel.startswith("program_images/"):
        entry = load_image_map().get(rel)
        if entry is None:
            raise ValueError(f"No Stage 15 program-image mapping for {rel}")
        rel = entry["destination"]
    if rel.startswith(("xsim/", "verilator/")):
        rel = "reports/stage9_coverage/" + rel
    return rel


def load_image_map():
    global _IMAGE_MAP
    if _IMAGE_MAP is None:
        path = ROOT / IMAGE_MAP_PATH
        if not path.is_file():
            raise FileNotFoundError(f"Stage 15 program-image map missing: {IMAGE_MAP_PATH}")
        with path.open(newline="", encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        required = {"test_id", "manifest_path", "original_relative_path", "sha256", "destination", "storage"}
        if not rows or not required.issubset(rows[0]):
            raise ValueError("Stage 15 program-image map schema is incomplete")
        result = {}
        test_ids = set()
        destinations = set()
        for row in rows:
            manifest_path = row["manifest_path"].replace("\\", "/")
            original = row["original_relative_path"].replace("\\", "/")
            destination = row["destination"].replace("\\", "/")
            if not manifest_path.startswith("program_images/") or original.startswith("/") or ".." in pathlib.PurePosixPath(original).parts:
                raise ValueError(f"Unsafe Stage 15 image mapping path: {manifest_path}")
            if destination.startswith("/") or ".." in pathlib.PurePosixPath(destination).parts:
                raise ValueError(f"Unsafe Stage 15 image destination: {destination}")
            if row["storage"] not in {"packaged", "tracked_existing"}:
                raise ValueError(f"Invalid Stage 15 image storage class: {row['storage']}")
            if manifest_path in result or row["test_id"] in test_ids or destination in destinations:
                raise ValueError("Duplicate Stage 15 image mapping key, test ID, or destination")
            if row["storage"] == "packaged" and not destination.startswith("reports/stage15_evidence/program_images/"):
                raise ValueError(f"Packaged image is outside evidence directory: {destination}")
            result[manifest_path] = row
            test_ids.add(row["test_id"])
            destinations.add(destination)
        storage_counts = {kind: sum(row["storage"] == kind for row in rows)
                          for kind in ("packaged", "tracked_existing")}
        if storage_counts != {"packaged": 34, "tracked_existing": 248}:
            raise ValueError(f"Unexpected Stage 15 image storage inventory: {storage_counts}")
        tracked = set(subprocess.run(["git", "ls-files"], cwd=ROOT, check=True,
                                     capture_output=True, text=True).stdout.splitlines())
        for row in rows:
            if row["storage"] == "tracked_existing" and row["destination"] not in tracked:
                raise ValueError(f"Mapped existing image is not tracked: {row['destination']}")
        _IMAGE_MAP = result
    return _IMAGE_MAP


def load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))


def stage_records():
    s11 = load_json("reports/stage11_matlab_ml/manifest.json")
    s12 = load_json("reports/stage12_test_selection/manifest.json")
    s13 = load_json("reports/stage13_active_learning/manifest.json")
    s14_config = load_json("reports/stage14_experiments_corrected_retry/configuration.json")
    s14_manifest = load_json("reports/stage14_experiments_corrected_retry/manifest.json")

    records = []
    source_groups = []

    def add(stage, rel, expected, kind):
        normalized = normalize_rel(rel)
        records.append((stage, normalized, expected.lower(), kind))

    def add_inputs(stage, items):
        for item in items:
            add(stage, item["path"], item["sha256"], "input")

    def add_outputs(stage, base, items):
        for item in items:
            add(stage, f"{base}/{item['path']}", item["sha256"], "output")

    add_inputs("11", s11["input_hashes"])
    add_outputs("11", "reports/stage11_matlab_ml", s11["output_files"].values())
    source_groups.append(("11", "stage11-complete", [x for x in s11["input_hashes"]
        if normalize_rel(x["path"]).startswith("scripts/machine_learning/")]))

    add_inputs("12", s12["input_hashes"])
    add_outputs("12", "reports/stage12_test_selection", s12["output_files"].values())
    source_groups.append(("12", "stage12-complete", [x for x in s12["input_hashes"]
        if normalize_rel(x["path"]).startswith("scripts/machine_learning/")]))

    add_inputs("13", s13["inputs"])
    add_outputs("13", "reports/stage13_active_learning", s13["outputs"])
    source_groups.append(("13", "stage13-complete", [x for x in s13["inputs"]
        if normalize_rel(x["path"]).startswith("scripts/machine_learning/")]))

    add_inputs("14-input", s14_config["input_hashes"])
    sources14 = s14_config.get("execution_provenance", {}).get("source_hashes", [])
    add_inputs("14-source", sources14)
    source_groups.append(("14", "stage14-complete", sources14))

    s14_base = "reports/stage14_experiments_corrected_retry"
    manifest_map = {
        "configuration_sha256": "configuration.json",
        "cost_join_audit_sha256": "cost_join_audit.csv",
        "rare_mask_audit_sha256": "rare_mask_audit.csv",
        "initial_sets_sha256": "initial_sets.csv",
        "curves_sha256": "partial_replay_curves.csv",
        "policy_order_audit_sha256": "policy_order_audit.csv",
        "paired_summary_sha256": "paired_summary.csv",
        "paired_differences_sha256": "paired_differences.csv",
        "auc_summary_sha256": "auc_summary.csv",
    }
    for key, rel in manifest_map.items():
        if key not in s14_manifest:
            raise ValueError(f"Stage 14 output manifest is missing {key}.")
        add("14-output", f"{s14_base}/{rel}", s14_manifest[key], "output")

    program_images = load_image_map()
    stage10_inputs = load_json("reports/stage10_dataset/manifest.json")["input_hashes"]
    expected_images = {p: h for p, h in stage10_inputs.items() if p.startswith("program_images/")}
    if set(expected_images) != set(program_images):
        raise ValueError("Stage 15 image map does not cover the frozen Stage 10 image inputs exactly")
    for manifest_path, expected in expected_images.items():
        if program_images[manifest_path]["sha256"].lower() != expected.lower():
            raise ValueError(f"Stage 15 image map differs from frozen Stage 10 hash: {manifest_path}")
    if len(program_images) != 282:
        raise ValueError(f"Expected 282 Stage 10 image mappings, found {len(program_images)}")
    return records, source_groups, s14_config


def expected_matches(path: pathlib.Path, expected: str, data: bytes) -> str | None:
    if digest(data) == expected:
        return "raw"
    if path.suffix.lower() in TEXT_EXTENSIONS and digest(lf_bytes(data)) == expected:
        return "lf"
    return None


def audit() -> tuple[list, list, dict]:
    records, source_groups, s14_config = stage_records()
    counts = {stage: {"raw": 0, "lf_only": 0, "unexpected": 0, "missing": 0}
              for stage, _, _, _ in records}
    by_path = {}
    for stage, rel, expected, kind in records:
        path = ROOT / rel
        if not path.is_file():
            counts[stage]["missing"] += 1
            raise FileNotFoundError(f"Stage {stage} {kind} missing: {rel}")
        data = path.read_bytes()
        match = expected_matches(path, expected, data)
        if match is None:
            counts[stage]["unexpected"] += 1
            raise ValueError(f"Stage {stage} {kind} hash mismatch: {rel}")
        counts[stage]["raw" if match == "raw" else "lf_only"] += 1
        by_path.setdefault(rel, []).append(expected)

    source_result = []
    for stage, tag, items in source_groups:
        seen = set()
        for item in items:
            rel = normalize_rel(item["path"])
            path = pathlib.PurePosixPath(rel)
            if path.suffix.lower() not in {".m", ".bat"} or rel in seen:
                continue
            seen.add(rel)
            expected = item["sha256"].lower()
            blob = subprocess.run(["git", "show", f"{tag}:{rel}"], cwd=ROOT,
                                  check=True, capture_output=True).stdout
            if digest(blob) != expected:
                raise ValueError(f"Stage {stage} recorded source differs from {tag}:{rel}")
            current = (ROOT / rel).read_bytes()
            if digest(lf_bytes(current)) != expected:
                raise ValueError(f"Current Stage {stage} source changed semantically: {rel}")
            source_result.append((stage, tag, rel, expected))

    snapshot_hash = s14_config.get("execution_provenance", {}).get("configuration_input_sha256")
    if snapshot_hash:
        snapshot = ROOT / "reports/stage14_experiments_corrected_retry/configuration_input_snapshot.json"
        if not snapshot.is_file() or expected_matches(snapshot, snapshot_hash.lower(), snapshot.read_bytes()) is None:
            raise ValueError("Stage 14 frozen configuration input snapshot hash mismatch.")
        by_path.setdefault("reports/stage14_experiments_corrected_retry/configuration_input_snapshot.json", []).append(snapshot_hash.lower())

    for stage, tally in counts.items():
        print(f"STAGE{stage} HASH AUDIT PASS raw={tally['raw']} lf_only={tally['lf_only']}")
    print(f"STAGE15 PRODUCER SOURCE AUDIT PASS source_files={len(source_result)}")
    program_images = load_image_map()
    packaged = [x for x in program_images.values() if x["storage"] == "packaged"]
    existing = [x for x in program_images.values() if x["storage"] == "tracked_existing"]
    print(f"STAGE11 PROGRAM IMAGES PASS total={len(program_images)} packaged={len(packaged)} tracked_existing={len(existing)} owner_local_dependencies=0")
    return records, source_result, by_path


def prepare_historical(checkout: pathlib.Path, records, source_result, by_path):
    """Materialize the exact hash-recorded bytes in a disposable worktree."""
    checkout = checkout.resolve()
    if not (checkout / ".git").exists():
        raise ValueError(f"Not a Git worktree: {checkout}")

    # Producer source files come from release-tag Git blobs, never from newer edits.
    for _, tag, rel, expected in source_result:
        blob = subprocess.run(["git", "show", f"{tag}:{rel}"], cwd=ROOT,
                              check=True, capture_output=True).stdout
        if digest(blob) != expected:
            raise ValueError(f"Producer source hash changed during preparation: {tag}:{rel}")
        target = checkout / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)

    source_paths = {rel for _, _, rel, _ in source_result}
    # Artifacts are copied only after their recorded hash form is verified.
    expected_by_path = {}
    for _, rel, expected, _ in records:
        expected_by_path.setdefault(rel, set()).add(expected)
    for rel, expected_set in expected_by_path.items():
        if rel in source_paths:
            continue
        source = ROOT / rel
        data = source.read_bytes()
        target = checkout / rel
        # Prefer the current raw producer bytes when an existing manifest records
        # them; otherwise materialize the portable LF form for text artifacts.
        if digest(data) in expected_set:
            material = data
        elif source.suffix.lower() in TEXT_EXTENSIONS and digest(lf_bytes(data)) in expected_set:
            material = lf_bytes(data)
        else:
            raise ValueError(f"Producer artifact bytes do not match any manifest: {rel}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(material)

    # The historical MATLAB producer code resolves the old program_images/ key
    # to its original workspace-relative path. Populate those temporary paths
    # from the tracked Stage 15 package, never from owner-local sim_out trees.
    for row in load_image_map().values():
        if row["storage"] != "packaged":
            continue
        expected = row["sha256"].lower()
        packaged = ROOT / row["destination"]
        data = packaged.read_bytes()
        if digest(data) != expected:
            raise ValueError(f"Packaged program image hash mismatch: {row['destination']}")
        original = checkout / row["original_relative_path"]
        original.parent.mkdir(parents=True, exist_ok=True)
        original.write_bytes(data)

    # Re-audit prepared input/output bytes against all frozen manifests.
    for stage, rel, expected, _ in records:
        target = checkout / rel
        if not target.is_file() or expected_matches(target, expected, target.read_bytes()) is None:
            raise ValueError(f"Historical checkout preparation failed hash check: {rel}")
        if stage == "11" and digest(target.read_bytes()) != expected:
            raise ValueError(f"Stage 11 raw-byte historical input/output mismatch: {rel}")
    print("STAGE15 HISTORICAL CHECKOUT PREPARATION PASS")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-historical", type=pathlib.Path)
    args = parser.parse_args()
    try:
        records, sources, by_path = audit()
        if args.prepare_historical:
            prepare_historical(args.prepare_historical, records, sources, by_path)
    except (OSError, ValueError, subprocess.CalledProcessError, KeyError) as exc:
        print(f"STAGE15 HASH AUDIT FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
