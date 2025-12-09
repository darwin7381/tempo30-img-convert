#!/usr/bin/env python3
"""
測試版本：逐步載入模組找出問題
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import sys
import traceback

app = FastAPI(title="逐步測試")

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/")
async def root():
    """測試各個 import"""
    results = {}
    
    # 測試 1: 基本模組
    try:
        from PIL import Image
        import base64
        import io
        import asyncio
        from pathlib import Path
        results["step1_basic_modules"] = "✅ 成功"
    except Exception as e:
        results["step1_basic_modules"] = f"❌ 失敗: {str(e)}"
        return results
    
    # 測試 2: style_configs_fine_grained
    try:
        from src.pipeline.style_configs_fine_grained import FINE_GRAINED_STYLES, STYLE_OPTIONS
        results["step2_style_configs"] = f"✅ 成功 (載入了 {len(STYLE_OPTIONS)} 個風格)"
    except Exception as e:
        results["step2_style_configs"] = f"❌ 失敗: {str(e)}"
        results["traceback"] = traceback.format_exc()
        return results
    
    # 測試 3: 檢查 templates
    try:
        html_path = Path(__file__).parent / "templates" / "index.html"
        if html_path.exists():
            results["step3_templates"] = f"✅ index.html 存在 ({html_path})"
        else:
            results["step3_templates"] = f"❌ index.html 不存在 ({html_path})"
    except Exception as e:
        results["step3_templates"] = f"❌ 失敗: {str(e)}"
    
    # 測試 4: 測試 WebSocket
    try:
        from fastapi import WebSocket, WebSocketDisconnect
        results["step4_websocket"] = "✅ WebSocket 模組正常"
    except Exception as e:
        results["step4_websocket"] = f"❌ 失敗: {str(e)}"
    
    return results

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

