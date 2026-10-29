"""Download Higgsfield outputs through GitHub (the runs can't reach Higgsfield's CDNs directly).

Usage:
  python3 engine/fetch_media.py --out posts/2026-10-30-slug/src opt1.png=https://d8j0ntlcm91z4.cloudfront.net/... opt2.png=https://...

Pushes inbox/<id>.json to main, waits for the fetch-media GitHub Action to publish the files on the `media` branch,
then copies them into --out. Prints one JSON line per file. Exit code 1 if any file failed, 2 on timeout.
"""
import argparse
import json
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SAFE = re.compile(r"^[A-Za-z0-9._-]{1,80}$")


def git(*args, check=True, text=True):
    return subprocess.run(["git", *args], cwd=REPO, check=check, capture_output=True, text=text)


def push_request(rid, files):
    path = REPO / "inbox" / f"{rid}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({"id": rid, "files": files}, indent=2) + "\n")
    git("add", str(path))
    git("commit", "-m", f"Fetch media {rid}", "--only", str(path))
    for attempt in range(4):
        if git("push", "origin", "HEAD:main", check=False).returncode == 0:
            return
        git("pull", "--rebase", "--autostash", "origin", "main", check=False)
        time.sleep(2 * (attempt + 1))
    raise SystemExit("could not push the fetch request to main")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("pairs", nargs="+", help="name=url")
    a = ap.parse_args()

    files = []
    for p in a.pairs:
        name, _, url = p.partition("=")
        if not SAFE.match(name) or not url.startswith("https://"):
            raise SystemExit(f"bad pair: {p}")
        files.append({"name": name, "url": url})

    rid = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    push_request(rid, files)

    deadline = time.time() + a.timeout
    done = None
    while time.time() < deadline:
        time.sleep(10)
        git("fetch", "--depth", "1", "origin", "+refs/heads/media:refs/remotes/origin/media", check=False)
        r = git("show", f"origin/media:media/{rid}/done.json", check=False)
        if r.returncode == 0:
            done = json.loads(r.stdout)
            break
    if done is None:
        print(json.dumps({"id": rid, "error": f"timeout after {a.timeout}s: check the fetch-media Action"}))
        sys.exit(2)

    out = Path(a.out)
    if not out.is_absolute():
        out = REPO / out
    out.mkdir(parents=True, exist_ok=True)
    failed = False
    for f in done["files"]:
        if f.get("ok"):
            blob = git("show", f"origin/media:media/{rid}/{f['name']}", text=False).stdout
            (out / f["name"]).write_bytes(blob)
            print(json.dumps({"name": f["name"], "ok": True, "path": str(out / f["name"]), "bytes": len(blob)}))
        else:
            failed = True
            print(json.dumps({"name": f.get("name"), "ok": False, "error": f.get("error")}))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
