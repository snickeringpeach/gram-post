#!/usr/bin/env python3
"""Post today's Gazette carousel to Instagram and Facebook through Meta's API.

Runs on GitHub's machines (the workflow fires twice each morning so 7:30 New York
time is covered in summer and winter). Reads queue.json, posts what is due today and
not yet in posted.json, records the post ids. Idempotent: running it again does nothing.

    python3 post.py            post what is due now
    python3 post.py --dry-run  say what would go out, check the image URLs, post nothing

Needs three repo secrets, set once by ./connect: META_PAGE_TOKEN, META_PAGE_ID, META_IG_ID.
Without them it runs as a dry run. Standard library only.
"""
import datetime as dt
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

API = "https://graph.facebook.com/v25.0"
ROOT = Path(__file__).resolve().parent
NY = ZoneInfo("America/New_York")
TOKEN = os.environ.get("META_PAGE_TOKEN", "")
PAGE = os.environ.get("META_PAGE_ID", "")
IG = os.environ.get("META_IG_ID", "")
DRY = "--dry-run" in sys.argv or not (TOKEN and PAGE and IG)


def call(method, path, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params, doseq=True).encode()
    url = f"{API}/{path}"
    if method == "GET":
        req = urllib.request.Request(url + "?" + data.decode())
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"{method} {path}: HTTP {e.code} {body[:400]}") from None


def image_urls(slug, files):
    repo = os.environ.get("GITHUB_REPOSITORY", "snickeringpeach/gram-post")
    sha = os.environ.get("GITHUB_SHA") or subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    return [f"https://raw.githubusercontent.com/{repo}/{sha}/images/{slug}/{f}" for f in files]


def wait_finished(container, tries=24):
    for _ in range(tries):
        st = call("GET", container, fields="status_code").get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {container} {st}")
        time.sleep(5)
    raise RuntimeError(f"container {container} not ready after {tries * 5}s")


def post_instagram(urls, caption):
    if len(urls) == 1:
        c = call("POST", f"{IG}/media", image_url=urls[0], caption=caption)["id"]
    else:
        kids = [call("POST", f"{IG}/media", image_url=u, is_carousel_item="true")["id"] for u in urls[:10]]
        for k in kids:
            wait_finished(k)
        c = call("POST", f"{IG}/media", media_type="CAROUSEL", children=",".join(kids), caption=caption)["id"]
    wait_finished(c)
    return call("POST", f"{IG}/media_publish", creation_id=c)["id"]


def post_facebook(urls, caption):
    ids = [call("POST", f"{PAGE}/photos", url=u, published="false")["id"] for u in urls]
    attached = {f"attached_media[{i}]": json.dumps({"media_fbid": x}) for i, x in enumerate(ids)}
    return call("POST", f"{PAGE}/feed", message=caption, **attached)["id"]


def reachable(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=30) as r:
            return r.status == 200 and r.headers.get("Content-Type", "").startswith("image/jpeg")
    except Exception:
        return False


def main():
    now = dt.datetime.now(NY)
    today = now.date().isoformat()
    queue = json.loads((ROOT / "queue.json").read_text())
    posted_path = ROOT / "posted.json"
    posted = json.loads(posted_path.read_text())
    print(f"{now:%Y-%m-%d %H:%M} New York — {'DRY RUN' if DRY else 'live'}; {len(queue)} in queue")

    for e in sorted(queue, key=lambda e: (e["date"], e.get("time", "07:30"))):
        slug, done = e["slug"], posted.get(e["slug"], {})
        targets = [t for t in e.get("to", ["instagram", "facebook"]) if t not in done]
        if not targets:
            continue
        if e["date"] < today:
            print(f"  MISSED {e['date']} {slug} ({', '.join(targets)}) — not posted late; re-date it with ./queue")
            continue
        if e["date"] > today or now.strftime("%H:%M") < e.get("time", "07:30"):
            continue
        files = sorted(p.name for p in (ROOT / "images" / slug).glob("*.jpg"))
        urls = image_urls(slug, files)
        print(f"  DUE {slug}: {len(urls)} image(s) → {', '.join(targets)}")
        if DRY:
            bad = [u for u in urls if not reachable(u)]
            print("    images reachable" if not bad else f"    NOT reachable: {bad}")
            continue
        for t in targets:
            pid = (post_instagram if t == "instagram" else post_facebook)(urls, e["caption"])
            done[t] = pid
            done[f"{t}_at"] = dt.datetime.now(NY).isoformat(timespec="minutes")
            posted[slug] = done
            posted_path.write_text(json.dumps(posted, indent=1, sort_keys=True) + "\n")
            print(f"    {t}: posted {pid}")


if __name__ == "__main__":
    main()
