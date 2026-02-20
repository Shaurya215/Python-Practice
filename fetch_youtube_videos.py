"""
Automatically fetch YouTube video IDs for recipes and add to CSV.
Uses YouTube Data API v3 (free, needs API key from Google Cloud).

Setup:
1. Go to https://console.cloud.google.com/
2. Create project -> APIs & Services -> Enable "YouTube Data API v3"
3. Create Credentials -> API Key
4. Put key in YOUTUBE_API_KEY below or set env variable YOUTUBE_API_KEY
"""

import os
import pandas as pd
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "Data", "cuisine_updated.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "Data", "cuisine_with_youtube.csv")

# Add your YouTube API key here (or set YOUTUBE_API_KEY in environment)
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "YOUR_API_KEY_HERE")

def search_youtube_video(recipe_name, api_key):
    """Search YouTube for recipe and return first video ID. Returns None if not found."""
    try:
        from googleapiclient.discovery import build
        youtube = build("youtube", "v3", developerKey=api_key)
        # Search: recipe name + "recipe" for better results
        query = f"{recipe_name} recipe"
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=1,
            videoDuration="medium"  # Prefer 4-20 min videos
        )
        response = request.execute()
        items = response.get("items", [])
        if items:
            return items[0]["id"]["videoId"]
    except Exception as e:
        print(f"  Error: {e}")
    return None

def main():
    if YOUTUBE_API_KEY == "YOUR_API_KEY_HERE":
        print("ERROR: Add your YouTube API key in the script or set YOUTUBE_API_KEY env variable")
        print("Get free key: https://console.cloud.google.com/ -> APIs -> YouTube Data API v3")
        return

    df = pd.read_csv(DATA_PATH)
    total = len(df)

    # Add youtube_url column if not exists
    if "youtube_url" not in df.columns:
        df["youtube_url"] = ""

    # Process in batches (YouTube API limit: 10000 units/day, 1 search = 100 units = 100/day)
    BATCH_SIZE = 50  # Run 50 per day, or increase if you have quota
    start = 0
    if "last_processed" in open(DATA_PATH).readline():
        pass  # Could add resume logic

    fetched = 0
    for i in range(start, min(start + BATCH_SIZE, total)):
        if pd.notna(df.at[i, "youtube_url"]) and str(df.at[i, "youtube_url"]).strip():
            continue  # Already has URL
        name = df.at[i, "name"]
        print(f"[{i+1}/{total}] Searching: {name[:50]}...")
        vid = search_youtube_video(name, YOUTUBE_API_KEY)
        if vid:
            df.at[i, "youtube_url"] = f"https://www.youtube.com/watch?v={vid}"
            fetched += 1
        time.sleep(0.5)  # Avoid rate limit

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nDone! Fetched {fetched} videos. Saved to: cuisine_with_youtube.csv")
    print("Replace cuisine_updated.csv with this file, or rename.")

if __name__ == "__main__":
    main()
