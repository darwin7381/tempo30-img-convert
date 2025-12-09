#!/usr/bin/env python3
"""
Railway 診斷測試
用於快速診斷 Railway 部署問題
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import sys
import os

app = FastAPI(title="Railway 診斷測試")

@app.get("/")
async def root():
    """根路徑 - 返回診斷資訊"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "message": "Railway 部署成功！",
            "python_version": sys.version,
            "environment": {
                "PORT": os.getenv("PORT", "未設定"),
                "GEMINI_API_KEY": "已設定" if os.getenv("GEMINI_API_KEY") else "未設定",
            }
        }
    )

@app.get("/health")
async def health():
    """健康檢查"""
    return {"status": "healthy"}

@app.get("/test-imports")
async def test_imports():
    """測試各個模組是否能正常載入"""
    results = {}
    
    # 測試 1：PIL
    try:
        from PIL import Image
        results["PIL"] = "✅ 成功"
    except Exception as e:
        results["PIL"] = f"❌ 失敗: {str(e)}"
    
    # 測試 2：rembg
    try:
        from rembg import remove
        results["rembg"] = "✅ 成功"
    except Exception as e:
        results["rembg"] = f"❌ 失敗: {str(e)}"
    
    # 測試 3：google.genai
    try:
        from google import genai
        results["google.genai"] = "✅ 成功"
    except Exception as e:
        results["google.genai"] = f"❌ 失敗: {str(e)}"
    
    # 測試 4：numpy
    try:
        import numpy as np
        results["numpy"] = "✅ 成功"
    except Exception as e:
        results["numpy"] = f"❌ 失敗: {str(e)}"
    
    # 測試 5：scipy
    try:
        from scipy import ndimage
        results["scipy"] = "✅ 成功"
    except Exception as e:
        results["scipy"] = f"❌ 失敗: {str(e)}"
    
    return results

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 啟動測試伺服器於端口 {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

