#!/usr/bin/env python3
"""
簡化版本 - 用於診斷部署問題
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pathlib import Path
import os

app = FastAPI(title="圖片風格轉換工具")


@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "message": "Application is running"
        }
    )


@app.get("/")
async def get_index():
    """首頁"""
    html_path = Path(__file__).parent / "templates" / "index.html"
    
    # 檢查檔案是否存在
    if not html_path.exists():
        return JSONResponse(
            status_code=500,
            content={
                "error": "index.html not found",
                "path": str(html_path),
                "exists": False
            }
        )
    
    return FileResponse(html_path)


@app.get("/api/styles")
async def get_styles():
    """獲取風格列表"""
    try:
        from src.pipeline.style_configs_fine_grained import STYLE_OPTIONS
        return {"styles": STYLE_OPTIONS}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Failed to load styles: {str(e)}"
            }
        )


@app.get("/test")
async def test_imports():
    """測試模組載入"""
    results = {}
    
    try:
        from PIL import Image
        results["PIL"] = "✅"
    except Exception as e:
        results["PIL"] = f"❌ {str(e)}"
    
    try:
        from rembg import remove
        results["rembg"] = "✅"
    except Exception as e:
        results["rembg"] = f"❌ {str(e)}"
    
    try:
        from google import genai
        results["google.genai"] = "✅"
    except Exception as e:
        results["google.genai"] = f"❌ {str(e)}"
    
    try:
        from src.pipeline.style_configs_fine_grained import FINE_GRAINED_STYLES, STYLE_OPTIONS
        results["style_configs"] = f"✅ ({len(STYLE_OPTIONS)} styles)"
    except Exception as e:
        results["style_configs"] = f"❌ {str(e)}"
    
    return results


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0" if os.getenv("PORT") else "127.0.0.1"
    uvicorn.run(app, host=host, port=port)

