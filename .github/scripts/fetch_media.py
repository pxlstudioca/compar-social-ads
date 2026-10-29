"""GitHub Action side of the media fetch.

For every inbox/<id>.json on main that has no media/<id>/done.json on the `media` branch yet:
download each listed file (Higgsfield hosts only), save it under media/<id>/<name>, write done.json.
The `media` branch is a cache: it is rewritten as a single commit on each run and keeps only the last KEEP_DAYS days.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_HOSTS = {"d8j0ntlcm91z4.cloudfront.net", "d1xarpci4ikg0w.cloudfront.net", "cdn.higgsfield.ai"}
SAFE = re.compile(r"^[A-Za-z0-9._-]{1,80}$")
MAX_BYTES = 95 * 1024 * 1024  # GitHub rejects files over 100 MB
KEEP_DAYS = 7

repo = Path.cwd()
work = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "media-tree"
index = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "media.index"
genv = dict(os.environ, GIT_DIR=str(repo / ".git"), GIT_INDEX_FILE=str(index), GIT_WORK_TREE=str(work))
genv.update(GIT_AUTHOR_NAME="compar-bot", GIT_AUTHOR_EMAIL="actions@users.noreply.github.com",
            GIT_COMMITTER_NAME="compar-bot", GIT_COMMITTER_EMAIL="actions@users.noreply.github.com")


def git(*args, env=None, check=True):
    # env=genv runs against the media tree (cwd inside it); otherwise the main checkout.
    return subprocess.run(["git", *args], cwd=work if env is genv else repo, env=env, check=check,
                          capture_output=True, text=True)


def download(url, dest):
    host = urlparse(url).hostname or ""
    if urlparse(url).scheme != "https" or host not in ALLOWED_HOSTS:
        raise ValueError(f"host not allowed: {host}")
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "compar-social-ads/fetch-media"})
            with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
                total = 0
                while chunk := r.read(1 << 20):
                    total += len(chunk)
                    if total > MAX_BYTES:
                        raise ValueError("file over 95 MB")
                    f.write(chunk)
            return total
        except ValueError:
            raise
        except Exception as e:  # network hiccup: retry
            last = e
            time.sleep(3 * (attempt + 1))
    raise last


def main():
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    index.unlink(missing_ok=True)
    has_branch = git("fetch", "--depth", "1", "origin", "+refs/heads/media:refs/remotes/origin/media", check=False).returncode == 0
    if has_branch:
        git("read-tree", "origin/media", env=genv)
        git("checkout-index", "-a", "-f", env=genv)

    media = work / "media"
    media.mkdir(exist_ok=True)
    changed = False

    for req_file in sorted((repo / "inbox").glob("*.json")):
        rid = req_file.stem
        if not SAFE.match(rid) or (media / rid / "done.json").exists():
            continue
        out = media / rid
        out.mkdir(parents=True, exist_ok=True)
        results = []
        try:
            files = json.loads(req_file.read_text())["files"]
        except Exception as e:
            files, results = [], [{"name": None, "ok": False, "error": f"bad request: {e}"}]
        for item in files:
            name, url = item.get("name", ""), item.get("url", "")
            if not SAFE.match(name):
                results.append({"name": name, "ok": False, "error": "bad file name"})
                continue
            try:
                size = download(url, out / name)
                results.append({"name": name, "ok": True, "bytes": size})
            except Exception as e:
                (out / name).unlink(missing_ok=True)
                results.append({"name": name, "ok": False, "error": str(e)[:300]})
        done = {"id": rid, "done_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "files": results}
        (out / "done.json").write_text(json.dumps(done, indent=2))
        print(f"{rid}: " + ", ".join(f"{r['name']}={'ok' if r['ok'] else r['error']}" for r in results))
        changed = True

    # Keep the cache small: drop request folders older than KEEP_DAYS.
    cutoff = datetime.now(timezone.utc) - timedelta(days=KEEP_DAYS)
    for d in media.iterdir():
        try:
            done_at = datetime.fromisoformat(json.loads((d / "done.json").read_text())["done_at"])
        except Exception:
            continue
        if done_at < cutoff:
            shutil.rmtree(d)
            changed = True

    if not changed:
        print("nothing to fetch")
        return
    (media / ".keep").touch()
    git("add", "-A", env=genv)
    tree = git("write-tree", env=genv).stdout.strip()
    commit = git("commit-tree", tree, "-m", f"Media cache {datetime.now(timezone.utc):%Y-%m-%d %H:%M}Z", env=genv).stdout.strip()
    git("push", "--force", "origin", f"{commit}:refs/heads/media")
    print(f"pushed media @ {commit[:8]}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(e.stdout, e.stderr, file=sys.stderr)
        raise
