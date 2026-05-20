"""
Shared fixtures and utilities for tap-google-sheets regression tests.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REGRESSION_DIR = Path(__file__).parent
BASELINE_DIR = REGRESSION_DIR / "baseline"
TAP_CMD = str(Path(sys.executable).parent / "tap-google-sheets")

REQUIRED_ENV = [
    "TAP_GOOGLE_SHEETS_CLIENT_ID",
    "TAP_GOOGLE_SHEETS_CLIENT_SECRET",
    "TAP_GOOGLE_SHEETS_REFRESH_TOKEN",
    "TAP_GOOGLE_SHEETS_SPREADSHEET_ID",
]


def build_config():
    missing = [v for v in REQUIRED_ENV if not os.getenv(v)]
    if missing:
        pytest.skip(f"Missing required env vars: {missing}")

    return {
        "client_id": os.environ["TAP_GOOGLE_SHEETS_CLIENT_ID"],
        "client_secret": os.environ["TAP_GOOGLE_SHEETS_CLIENT_SECRET"],
        "refresh_token": os.environ["TAP_GOOGLE_SHEETS_REFRESH_TOKEN"],
        "spreadsheet_id": os.environ["TAP_GOOGLE_SHEETS_SPREADSHEET_ID"],
        "start_date": os.getenv("TAP_GOOGLE_SHEETS_START_DATE", "2010-01-01T00:00:00Z"),
        "user_agent": "peliqan-regression/1.0",
        "request_timeout": 300,
    }


def _tap_env():
    env = os.environ.copy()
    env.setdefault("AES_SECRET_KEY", "peliqan-test-key")
    return env


def discover_catalog(config_path):
    """Run tap-google-sheets in --discover mode and return the catalog dict."""
    result = subprocess.run(
        [TAP_CMD, "--config", config_path, "--discover"],
        capture_output=True, text=True, env=_tap_env()
    )
    if result.returncode != 0:
        raise RuntimeError(f"discover failed: {result.stderr[-2000:]}")
    return json.loads(result.stdout)


def select_all_streams(catalog):
    """Mark every stream and every field as selected in the catalog metadata."""
    for stream in catalog.get("streams", []):
        for entry in stream.get("metadata", []):
            entry.setdefault("metadata", {})["selected"] = True
    return catalog


def write_catalog(catalog):
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(catalog, tmp)
    tmp.close()
    return tmp.name


@pytest.fixture(scope="session")
def config_file():
    config = build_config()
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(config, tmp)
    tmp.close()
    yield tmp.name
    os.unlink(tmp.name)


@pytest.fixture(scope="session")
def catalog_file(config_file):
    catalog = discover_catalog(config_file)
    select_all_streams(catalog)
    path = write_catalog(catalog)
    yield path
    os.unlink(path)


def run_tap(config_path, catalog_path=None, extra_args=None):
    cmd = [TAP_CMD, "--config", config_path]
    if catalog_path:
        cmd += ["--catalog", catalog_path]
    cmd += (extra_args or [])
    result = subprocess.run(cmd, capture_output=True, text=True, env=_tap_env())
    return result.stdout, result.stderr, result.returncode


def parse_messages(stdout):
    schemas, records, states = {}, {}, []
    for line in stdout.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = msg.get("type")
        if t == "SCHEMA":
            schemas[msg["stream"]] = msg["schema"]
            records.setdefault(msg["stream"], [])
        elif t == "RECORD":
            records.setdefault(msg["stream"], []).append(msg["record"])
        elif t == "STATE":
            states.append(msg["value"])
    return schemas, records, states
