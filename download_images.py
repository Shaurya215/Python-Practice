"""
Image collection script for the recipe recommendation project.
==============================================================

Goal
----
Link every recipe in `Data/cuisine_updated.csv` to a **local image file**
in `static/images/` so the Flask app can show images without relying on
external websites.

High‑level steps (no extra folders created):
1. Read the CSV file row‑by‑row.
2. For each recipe:
   - Optionally **reuse** an already‑downloaded image from a source folder
     (e.g. a previous scraping run, one image per recipe index), and copy
     it into `static/images/`.
   - If reuse is not possible and scraping is enabled:
       * Use DuckDuckGo image search to find 1 suitable picture.
       * Download and save it as `<row_index>_<sanitized_name>.jpg`.
3. Update the CSV columns:
   - `image_url` → `/static/images/<filename>`
   - `image_available` → 1 if we have a good image, else 0.

Usage examples
--------------
Basic run over the whole dataset:
    python download_images.py

Run only for the first N recipes (useful in batches):
    python download_images.py --limit 500

Reuse only from an existing folder, do NOT call DuckDuckGo:
    python download_images.py --limit 500 --no-scrape
"""

from __future__ import annotations

import argparse
import io
import hashlib
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
import requests
from PIL import Image
import warnings
import shutil

try:
    from duckduckgo_search import DDGS
except Exception:  # pragma: no cover
    DDGS = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "Data", "cuisine_updated.csv")
IMAGES_DIR = os.path.join(BASE_DIR, "static", "images")

# Silence noisy deprecation/rename warning from duckduckgo_search
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Prefer reusing your already-downloaded images
DEFAULT_SOURCE_DIR = r"C:\Users\shaur\Machine Learning\recipe_images"

# Networking
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
}
REQUEST_TIMEOUT_S = 20
DELAY_BETWEEN_RECIPES_S = 0.2
MIN_BYTES = 15 * 1024  # discard tiny placeholders
MAX_RESULTS_PER_RECIPE = 12


def sanitize_filename(name: str, max_len: int = 90) -> str:
    name = re.sub(r"[<>:\"/\\|?*\x00-\x1F]", "_", str(name))
    name = re.sub(r"\s+", " ", name).strip()
    if not name:
        name = "recipe"
    return name[:max_len]


def make_output_filename(index: int, recipe_name: str) -> str:
    """
    Create a Windows-safe output filename.

    Some recipe names are very long; if the full path becomes too long on Windows,
    fall back to a short hashed filename.
    """
    base = f"{index}_{sanitize_filename(recipe_name, max_len=60)}"
    fname = f"{base}.jpg"
    out_path = os.path.join(IMAGES_DIR, fname)
    # Conservative threshold (Windows legacy MAX_PATH is 260)
    if len(out_path) > 240:
        h = hashlib.md5(f"{index}:{recipe_name}".encode("utf-8", errors="ignore")).hexdigest()[:12]
        fname = f"{index}_{h}.jpg"
    return fname


def is_local_static_path(s: str) -> bool:
    s = str(s or "").strip()
    return s.startswith("/static/images/") and any(s.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp"))


def validate_image_bytes(raw: bytes) -> bool:
    if not raw or len(raw) < MIN_BYTES:
        return False
    try:
        with Image.open(io.BytesIO(raw)) as im:
            im.verify()
        return True
    except Exception:
        return False


def write_as_jpg(raw: bytes, out_path: str) -> None:
    with Image.open(io.BytesIO(raw)) as im:
        im = im.convert("RGB")
        im.save(out_path, format="JPEG", quality=85, optimize=True)


def find_source_image_for_index(source_dir: str, index: int) -> Optional[str]:
    """
    Find a file in source_dir that starts with `<index>_` (common pattern in your old folder).
    Returns absolute path if found.
    """
    p = Path(source_dir)
    if not p.exists() or not p.is_dir():
        return None
    # pick first match; prefer jpg/jpeg over others
    matches: list[Path] = []
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        matches.extend(p.glob(f"{index}_*{ext}"))
    if not matches:
        # fallback: any file starting with index_
        matches = list(p.glob(f"{index}_*"))
    if not matches:
        return None
    matches.sort(key=lambda x: (x.suffix.lower() != ".jpg", x.stat().st_size), reverse=False)
    return str(matches[0])


@dataclass
class DownloadResult:
    ok: bool
    bytes_: Optional[bytes] = None
    source_url: Optional[str] = None


def ddg_image_candidates(query: str) -> Iterable[str]:
    if DDGS is None:
        return []
    try:
        # Suppress noisy rename warning from older duckduckgo_search installs.
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            # Using list() to avoid generator errors mid-stream on some networks
            results = list(DDGS().images(query, max_results=MAX_RESULTS_PER_RECIPE))
        for r in results:
            url = r.get("image") or r.get("thumbnail")
            if url and isinstance(url, str) and url.startswith("http"):
                yield url
    except Exception:
        return []


def try_download(url: str) -> DownloadResult:
    try:
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT_S)
        r.raise_for_status()
        raw = r.content
        if validate_image_bytes(raw):
            return DownloadResult(ok=True, bytes_=raw, source_url=url)
        return DownloadResult(ok=False)
    except Exception:
        return DownloadResult(ok=False)


def ensure_dirs() -> None:
    os.makedirs(IMAGES_DIR, exist_ok=True)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Collect recipe images into static/images and update cuisine_updated.csv")
    p.add_argument("--source-dir", default=os.environ.get("RECIPE_IMAGE_SOURCE_DIR", DEFAULT_SOURCE_DIR))
    p.add_argument("--limit", type=int, default=None, help="Process only first N rows (useful for multiple runs)")
    p.add_argument(
        "--no-scrape",
        action="store_true",
        help="Only reuse/copy from source-dir; do not try DuckDuckGo downloads for missing images.",
    )
    return p.parse_args()


def main() -> None:
    ensure_dirs()
    args = parse_args()
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")

    source_dir = args.source_dir
    total = min(len(df), args.limit) if args.limit else len(df)

    updated = 0
    reused = 0
    downloaded = 0
    failed = 0

    for idx in range(total):
        row = df.iloc[idx]
        name = str(row.get("name", f"recipe_{idx}")).strip() or f"recipe_{idx}"
        current_url = str(row.get("image_url", "")).strip()

        # If already points to a local static file AND it exists, keep it.
        if is_local_static_path(current_url):
            local_file = current_url.replace("/static/images/", "", 1)
            if os.path.exists(os.path.join(IMAGES_DIR, local_file)):
                if "image_available" in df.columns:
                    df.at[idx, "image_available"] = 1
                continue

        out_fname = make_output_filename(idx, name)
        out_path = os.path.join(IMAGES_DIR, out_fname)

        if os.path.exists(out_path) and os.path.getsize(out_path) >= MIN_BYTES:
            df.at[idx, "image_url"] = f"/static/images/{out_fname}"
            if "image_available" in df.columns:
                df.at[idx, "image_available"] = 1
            continue

        # 1) Reuse existing image from old folder (fast + stable)
        src_img = find_source_image_for_index(source_dir, idx)
        if src_img and os.path.exists(src_img) and os.path.getsize(src_img) >= MIN_BYTES:
            try:
                # Fast path: most cached files are already JPG/JPEG -> just copy.
                ext = Path(src_img).suffix.lower()
                if ext in (".jpg", ".jpeg"):
                    shutil.copy2(src_img, out_path)
                else:
                    # Normalize to JPG for consistent web serving.
                    with Image.open(src_img) as im:
                        im = im.convert("RGB")
                        im.save(out_path, format="JPEG", quality=85, optimize=True)
                df.at[idx, "image_url"] = f"/static/images/{out_fname}"
                if "image_available" in df.columns:
                    df.at[idx, "image_available"] = 1
                updated += 1
                reused += 1
                if (idx + 1) % 50 == 0:
                    print(f"Progress {idx+1}/{total} | updated={updated} reused={reused} downloaded={downloaded} failed={failed}")
                continue
            except Exception:
                # If copy/convert fails, fall through to DDG
                pass

        # 2) DuckDuckGo fallback (multiple tries)
        if args.no_scrape:
            failed += 1
            if "image_available" in df.columns:
                df.at[idx, "image_available"] = 0
            continue

        query = f"{name} recipe"
        got = False
        for url in ddg_image_candidates(query):
            res = try_download(url)
            if res.ok and res.bytes_:
                try:
                    write_as_jpg(res.bytes_, out_path)
                    df.at[idx, "image_url"] = f"/static/images/{out_fname}"
                    if "image_available" in df.columns:
                        df.at[idx, "image_available"] = 1
                    updated += 1
                    downloaded += 1
                    got = True
                except Exception:
                    got = False
                break
            # avoid hammering if we tried a URL and it failed/was invalid
            time.sleep(0.3)

        if not got:
            failed += 1
            if "image_available" in df.columns:
                df.at[idx, "image_available"] = 0

        if (idx + 1) % 50 == 0:
            print(f"Progress {idx+1}/{total} | updated={updated} reused={reused} downloaded={downloaded} failed={failed}")

        if not src_img:
            # Only wait when we actually had to scrape (helps avoid rate limits)
            time.sleep(DELAY_BETWEEN_RECIPES_S)

    # Save updated dataset in-place (as requested)
    df.to_csv(DATA_PATH, index=False, encoding="utf-8-sig")
    print(
        f"\nDone. Total={total} | updated={updated} (reused={reused}, downloaded={downloaded}) | failed={failed}\n"
        f"Images: {IMAGES_DIR}\n"
        f"Dataset updated: {DATA_PATH}\n"
        f"Source dir (reuse): {source_dir}\n"
        "Tip: Set env var RECIPE_IMAGE_SOURCE_DIR to change the reuse folder."
    )


if __name__ == "__main__":
    main()
