#!/usr/bin/env python3
"""批次上傳圖片至 WordPress 媒體庫"""

import os
import base64
import mimetypes
import json
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

WP_URL = "https://wp.blocktempo.ai"
USERNAME = "ai@cryptoxlab.com"
PASSWORD = "4P40 DjD5 vw6A urJl IbmW 3SDD"
MEDIA_ENDPOINT = f"{WP_URL}/wp-json/wp/v2/media"

OUTPUT_DIR = Path("output-Tempo20")
RESULTS_FILE = Path("output-Tempo20/wp_upload_results.json")

if not OUTPUT_DIR.exists():
    raise SystemExit(f"❌ 找不到輸出資料夾: {OUTPUT_DIR}")

files = sorted([p for p in OUTPUT_DIR.iterdir() if p.is_file()])
if not files:
    raise SystemExit("❌ 輸出資料夾沒有任何檔案")

auth_token = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
headers = {
    "Authorization": f"Basic {auth_token}",
}

session = requests.Session()
session.headers.update(headers)

results = []

for file_path in files:
    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    print(f"⬆️ 上傳 {file_path.name} ({mime_type})")
    with file_path.open("rb") as f:
        files_payload = {
            "file": (file_path.name, f, mime_type)
        }
        response = session.post(MEDIA_ENDPOINT, files=files_payload)
    if response.status_code not in (200, 201):
        print(f"❌ 上傳失敗 {file_path.name}: {response.status_code} {response.text}")
        results.append({
            "file": file_path.name,
            "status": "error",
            "code": response.status_code,
            "message": response.text
        })
        continue
    data = response.json()
    media_url = data.get("source_url")
    media_id = data.get("id")
    print(f"✅ 成功: {media_url}")
    results.append({
        "file": file_path.name,
        "status": "success",
        "media_id": media_id,
        "url": media_url
    })

RESULTS_FILE.write_text(json.dumps(results, ensure_ascii=False, indent=2))
print(f"📄 上傳結果已儲存: {RESULTS_FILE}")
