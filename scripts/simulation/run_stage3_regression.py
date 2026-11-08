#!/usr/bin/env python3
"""Canonical Stage 3.7 Verilator entry point; reuses the validated Stage 3.5 suite."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).with_name('run_stage5.py')
raise SystemExit(subprocess.run(
    [sys.executable, str(RUNNER), '--stage3-regression'], cwd=ROOT,
    env=os.environ.copy()).returncode)
