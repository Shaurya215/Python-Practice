"""
Fetch YouTube video IDs WITHOUT API key.
Uses youtube-search-python (scrapes - no API key needed).

Install: pip install youtube-search-python
"""

import os
import pandas as pd
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "Data", "cuisine_updated.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "Data", "cuisine_with_youtube.csv")

def search_youtube_no_api(recipe_name):
    """Search YouTube without API - returns first video ID."""
    try:
        from youtubesearchpython import VideosSearch
        search = VideosSearch(f"{recipe_name} recipe", limit=1)
        results = search.result()
        # Handle different response formats
        if results:
            items = results.get("result") or results.get("results") or []
            if items:
                vid = items[0].get("id") or items[0].get("videoId")
                if vid:
                    return vid
    except ImportError:
        print("Install: pip install youtube-search-python")
        return None
    except Exception as e:
        return None
    return None

def main():
    df = pd.read_csv(DATA_PATH)
    total = len(df)

    if "youtube_url" not in df.columns:
        df["youtube_url"] = ""

    # How many to process (change as needed)
    LIMIT = 100  # Start with 100, run multiple times for more
    fetched = 0

    for i in range(min(LIMIT, total)):
        if pd.notna(df.at[i, "youtube_url"]) and str(df.at[i, "youtube_url"]).strip():
            continue
        name = df.at[i, "name"]
        print(f"[{i+1}/{total}] {name[:45]}...")
        vid = search_youtube_no_api(name)
        if vid:
            df.at[i, "youtube_url"] = f"https://www.youtube.com/watch?v={vid}"
            fetched += 1
        time.sleep(1)  # Be nice to servers

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nDone! Fetched {fetched} videos. Saved to: cuisine_with_youtube.csv")

if __name__ == "__main__":
    main()
