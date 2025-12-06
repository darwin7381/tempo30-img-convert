#!/bin/bash
# 圖片風格轉換工具 - FastAPI 版本啟動腳本

echo "🚀 啟動圖片風格轉換工具（FastAPI 版本）..."
cd "$(dirname "$0")"
uv run python app.py
