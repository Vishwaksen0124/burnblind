"""Publish a prebuilt static frontend through Amplify's manual deployment API."""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import Request, urlopen
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def aws_json(*arguments: str) -> dict:
    result = subprocess.run(
        ["aws", "amplify", *arguments, "--region", "us-east-2", "--output", "json"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(detail or f"AWS CLI command failed with exit code {result.returncode}")
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-id", required=True)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--dist", type=Path, default=ROOT / "frontend/dist")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    args = parser.parse_args()
    if not args.dist.is_dir() or not (args.dist / "index.html").is_file():
        parser.error(f"built frontend not found in {args.dist}; run npm run build first")
    if args.timeout_seconds < 1:
        parser.error("timeout-seconds must be positive")

    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(args.dist.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(args.dist).as_posix())
    archive = archive_buffer.getvalue()
    if len(archive) > 5 * 1024**3:
        parser.error("Amplify manual deployment archive exceeds 5 GB")

    deployment = aws_json(
        "create-deployment",
        "--app-id", args.app_id,
        "--branch-name", args.branch,
    )
    request = Request(
        deployment["zipUploadUrl"],
        data=archive,
        method="PUT",
        headers={"Content-Type": "application/zip"},
    )
    with urlopen(request, timeout=60) as response:
        if response.status not in (200, 201, 204):
            raise RuntimeError(f"Amplify archive upload returned HTTP {response.status}")

    job_id = str(deployment["jobId"])
    aws_json(
        "start-deployment",
        "--app-id", args.app_id,
        "--branch-name", args.branch,
        "--job-id", job_id,
    )
    deadline = time.monotonic() + args.timeout_seconds
    while time.monotonic() < deadline:
        job = aws_json(
            "get-job",
            "--app-id", args.app_id,
            "--branch-name", args.branch,
            "--job-id", job_id,
        )["job"]["summary"]
        status = job["status"]
        print(f"Amplify deployment {job_id}: {status}")
        if status == "SUCCEED":
            app = aws_json("get-app", "--app-id", args.app_id)["app"]
            print(f"Dashboard URL: https://{args.branch}.{app['defaultDomain']}")
            return 0
        if status in {"FAILED", "CANCELLED"}:
            print(job.get("statusReason", "deployment failed"), file=sys.stderr)
            return 1
        time.sleep(5)
    print("Timed out waiting for Amplify; inspect the job in the AWS console.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
