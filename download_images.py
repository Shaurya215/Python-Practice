"""
Download recipe images and save locally. Run once to get real images.
Archana's Kitchen may block - if so, placeholders will be used.
"""
import os
import pandas as pd
import requests
from urllib.parse import urlparse
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "Data", "cuisine_updated.csv")
IMAGES_DIR = os.path.join(BASE_DIR, "static", "images")

# Headers to mimic browser - some sites allow this
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
}

def get_image_path(url, index):
    """Generate local filename from URL or index."""
    if pd.isna(url) or not str(url).strip():
        return None
    url = str(url).strip()
    if not any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
        return None
    ext = '.jpg'
    for e in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
        if url.lower().endswith(e):
            ext = e
            break
    h = hashlib.md5(url.encode()).hexdigest()[:12]
    return f"recipe_{index}_{h}{ext}"

def main():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    df = pd.read_csv(DATA_PATH)
    
    # Build mapping: image_url -> local path
    url_to_local = {}
    total = len(df)
    
    for i, row in df.iterrows():
        url = row.get('image_url')
        if pd.isna(url) or not str(url).strip():
            continue
        url = str(url).strip()
        if not any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
            continue
        if url in url_to_local:
            continue
        fname = get_image_path(url, i)
        if not fname:
            continue
        local_path = os.path.join(IMAGES_DIR, fname)
        if os.path.exists(local_path):
            url_to_local[url] = f"/static/images/{fname}"
            continue
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200 and len(r.content) > 1000:
                with open(local_path, 'wb') as f:
                    f.write(r.content)
                url_to_local[url] = f"/static/images/{fname}"
        except Exception:
            pass
        if (i + 1) % 100 == 0:
            print(f"Processed {i+1}/{total}...")
    
    # Save mapping for app to use
    import json
    mapping_path = os.path.join(BASE_DIR, "image_mapping.json")
    with open(mapping_path, 'w') as f:
        json.dump(url_to_local, f, indent=2)
    print(f"Done. Downloaded {len(url_to_local)} images. Mapping saved to image_mapping.json")

if __name__ == "__main__":
    main()
