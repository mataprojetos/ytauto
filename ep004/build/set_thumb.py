#!/usr/bin/env python3
"""Aplica a capa com thumbnails.set depois de o YouTube acabar de processar o vídeo.
Uso: set_thumb.py VIDEO_ID thumbnails/ep004_thumb.jpg"""
import sys, time, os, requests
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from yt_upload import auth_headers, API, HOST
vid, img = sys.argv[1], sys.argv[2]
h = auth_headers()
for _ in range(60):
    r = requests.get(f"{API}/videos", params={"part": "processingDetails,status", "id": vid}, headers=h, timeout=30)
    it = r.json().get("items", [])
    st = it[0].get("processingDetails", {}).get("processingStatus") if it else None
    print("processingStatus:", st, flush=True)
    if st in ("succeeded", "failed", "terminated"):
        break
    time.sleep(15)
r = requests.post(f"https://{HOST}/upload/youtube/v3/thumbnails/set", params={"videoId": vid},
                  headers={**h, "Content-Type": "image/jpeg"}, data=open(img, "rb").read(), timeout=120)
print("thumbnails.set", r.status_code, r.text[:300])
