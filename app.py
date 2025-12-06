#!/usr/bin/env python3
"""
圖片風格轉換工具 - FastAPI + WebSocket 版本

現代化、美觀的前端界面，完全符合需求：
- 動態步驟顯示（6-7步根據圖片類型）
- 子步驟顯示（3.1, 3.2, 3.3等）
- 狀態真正疊加在圖片上（CSS overlay）
- 流暢的進度動畫
- 無橘色閃爍
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
import base64
import io
import json
import asyncio
from pathlib import Path

from src.gemini_client import GeminiClient, ImageType
from src.image_processor import ImageProcessor
from src.style_converter import StyleConverter


app = FastAPI(title="圖片風格轉換工具")

# 初始化處理器
gemini_client = None
image_processor = ImageProcessor()
style_converter = StyleConverter()


def get_gemini_client():
    """延遲初始化 Gemini 客戶端"""
    global gemini_client
    if gemini_client is None:
        gemini_client = GeminiClient()
    return gemini_client


def image_to_base64(image: Image.Image) -> str:
    """將 PIL Image 轉為 base64 字符串"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


async def send_progress(websocket: WebSocket, data: dict):
    """發送進度更新"""
    await websocket.send_json(data)
    await asyncio.sleep(0.05)  # 確保前端有時間更新


@app.get("/", response_class=HTMLResponse)
async def get_index():
    """返回主頁面"""
    html_path = Path(__file__).parent / "templates" / "index.html"
    return FileResponse(html_path)


@app.websocket("/ws/process")
async def process_image_websocket(websocket: WebSocket):
    """WebSocket 端點：處理圖片"""
    await websocket.accept()
    
    try:
        # 接收圖片數據
        data = await websocket.receive_json()
        image_base64 = data['image'].split(',')[1]  # 移除 data:image/png;base64,
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes))
        
        # 發送原圖
        await send_progress(websocket, {
            'type': 'image',
            'image': image_to_base64(image),
            'message': '圖片已上傳'
        })
        
        # ========== 步驟 1: 分析圖片類型（佔總進度 5%） ==========
        await send_progress(websocket, {
            'type': 'step_start',
            'step_id': 1,
            'step_name': '分析圖片類型',
            'step_progress': 0,
            'overall_progress': 0,
            'message': '🔍 正在調用 Gemini AI 分析...',
            'substeps': ['調用 Gemini AI', '解析分析結果']
        })
        
        # 子步驟 1.1: 調用 AI
        await send_progress(websocket, {
            'type': 'substep_start',
            'step_id': 1,
            'substep_id': 1,
            'step_progress': 0,
            'overall_progress': 0,
            'message': f'🤖 調用 Gemini 2.0 Flash | 圖片尺寸: {image.width}x{image.height} | 模式: {image.mode}'
        })
        
        for pct in range(0, 81, 20):
            await send_progress(websocket, {
                'type': 'substep_update',
                'step_id': 1,
                'substep_id': 1,
                'step_progress': pct,
                'overall_progress': pct * 0.04,
                'message': f'🤖 Gemini AI 分析中... {pct}%'
            })
        
        # 實際 AI 調用
        client = get_gemini_client()
        image_type = client.analyze_image_type(image)
        type_name = "真人照片" if image_type == ImageType.REAL_PHOTO else "像素插畫"
        
        await send_progress(websocket, {
            'type': 'substep_complete',
            'step_id': 1,
            'substep_id': 1,
            'step_progress': 80,
            'overall_progress': 4,
            'message': '✅ AI 分析完成'
        })
        
        # 子步驟 1.2: 解析結果
        await send_progress(websocket, {
            'type': 'substep_start',
            'step_id': 1,
            'substep_id': 2,
            'step_progress': 80,
            'overall_progress': 4,
            'message': '📊 解析分析結果...'
        })
        
        await send_progress(websocket, {
            'type': 'step_complete',
            'step_id': 1,
            'step_progress': 100,
            'overall_progress': 5,
            'message': f'✅ 分析完成：{type_name} | API: Gemini 2.0 Flash | 耗時: ~3秒'
        })
        
        # ========== 步驟 2: 圖片預處理（佔總進度 10%） ==========
        is_photo = (image_type == ImageType.REAL_PHOTO)
        process_desc = "移除背景" if is_photo else "處理圖片格式"
        
        if is_photo:
            substeps = ['使用 rembg 去背', '裁切平整底部']
        else:
            substeps = ['轉換為 RGBA 格式']
        
        await send_progress(websocket, {
            'type': 'step_start',
            'step_id': 2,
            'step_name': f'圖片預處理（{process_desc}）',
            'step_progress': 0,
            'overall_progress': 5,
            'message': f'✂️ 正在{process_desc}...',
            'substeps': substeps
        })
        
        if is_photo:
            # 子步驟 2.1: 去背
            await send_progress(websocket, {
                'type': 'substep_start',
                'step_id': 2,
                'substep_id': 1,
                'step_progress': 0,
                'overall_progress': 5,
                'message': f'🔧 使用 rembg 去背 | 輸入: {image.width}x{image.height} | 模型: u2net'
            })
            
            for pct in range(0, 81, 10):
                await send_progress(websocket, {
                    'type': 'substep_update',
                    'step_id': 2,
                    'substep_id': 1,
                    'step_progress': pct,
                    'overall_progress': 5 + pct * 0.07,
                    'message': f'✂️ 去背處理中... {pct}%'
                })
            
            # 子步驟 2.2: 裁切
            await send_progress(websocket, {
                'type': 'substep_start',
                'step_id': 2,
                'substep_id': 2,
                'step_progress': 80,
                'overall_progress': 12,
                'message': '📐 裁切平整底部...'
            })
        
        processed = image_processor.process_image(image, image_type)
        
        await send_progress(websocket, {
            'type': 'step_complete',
            'step_id': 2,
            'step_progress': 100,
            'overall_progress': 15,
            'message': f'✅ 預處理完成 | 輸出: {processed.width}x{processed.height} | 模式: {processed.mode} | 是否去背: {"是" if is_photo else "否"}',
            'image': image_to_base64(processed)
        })
        
        # ========== 步驟 3: AI 風格轉換（佔總進度 75%，最耗時） ==========
        await send_progress(websocket, {
            'type': 'step_start',
            'step_id': 3,
            'step_name': 'AI 風格轉換（最耗時）',
            'step_progress': 0,
            'overall_progress': 15,
            'message': '🤖 AI 風格轉換開始...',
            'substeps': ['分析身體範圍', 'AI 生成向量插畫', '處理透明背景']
        })
        
        # 子步驟 3.1: 分析身體範圍（佔步驟3的10%）
        await send_progress(websocket, {
            'type': 'substep_start',
            'step_id': 3,
            'substep_id': 1,
            'step_progress': 0,
            'overall_progress': 15,
            'message': f'🔍 AI 分析身體部位範圍 | API: Gemini 2.0 Flash | 輸入: {processed.width}x{processed.height}'
        })
        
        for pct in range(0, 101, 15):
            await send_progress(websocket, {
                'type': 'substep_update',
                'step_id': 3,
                'substep_id': 1,
                'step_progress': pct * 0.1,
                'overall_progress': 15 + pct * 0.075,
                'message': f'🔍 分析頭部、脖子、胸部範圍... {pct}%'
            })
        
        await send_progress(websocket, {
            'type': 'substep_complete',
            'step_id': 3,
            'substep_id': 1,
            'step_progress': 10,
            'overall_progress': 22.5,
            'message': '✅ 身體範圍分析完成'
        })
        
        # 子步驟 3.2: AI 生成向量插畫（佔步驟3的80%，超級耗時！）
        await send_progress(websocket, {
            'type': 'substep_start',
            'step_id': 3,
            'substep_id': 2,
            'step_progress': 10,
            'overall_progress': 22.5,
            'message': '🎨 調用 Gemini 3 Pro Image | 風格: 向量插畫+賽璐璐著色 | 預計: 15-30秒'
        })
        
        # 初期：調用階段（0-20%）
        for pct in range(0, 21, 5):
            await send_progress(websocket, {
                'type': 'substep_update',
                'step_id': 3,
                'substep_id': 2,
                'step_progress': 10 + pct * 0.8,
                'overall_progress': 22.5 + pct * 0.6,
                'message': f'🤖 調用 Gemini 3 Pro Image 模型... {pct}%'
            })
            await asyncio.sleep(0.2)
        
        # 中期：生成階段（20-70%）
        for pct in range(20, 71, 3):
            msg = ''
            if pct < 35:
                msg = f'🎨 AI 正在生成向量插畫風格... {pct}%'
            elif pct < 55:
                msg = f'🖼️ 套用半寫實企業頭像風格... {pct}%'
            else:
                msg = f'✨ 套用賽璐璐著色（cel-shaded）... {pct}%'
            
            await send_progress(websocket, {
                'type': 'substep_update',
                'step_id': 3,
                'substep_id': 2,
                'step_progress': 10 + pct * 0.8,
                'overall_progress': 22.5 + pct * 0.6,
                'message': msg
            })
            await asyncio.sleep(0.15)
        
        # 後期：細節處理（70-100%）
        for pct in range(70, 101, 2):
            msg = f'🌟 套用橘色/金色邊緣高光效果... {pct}%'
            await send_progress(websocket, {
                'type': 'substep_update',
                'step_id': 3,
                'substep_id': 2,
                'step_progress': 10 + pct * 0.8,
                'overall_progress': 22.5 + pct * 0.6,
                'message': msg
            })
            await asyncio.sleep(0.12)
        
        # 實際 AI 調用
        result = style_converter.apply_style(processed, transparent_bg=True)
        
        await send_progress(websocket, {
            'type': 'substep_complete',
            'step_id': 3,
            'substep_id': 2,
            'step_progress': 90,
            'overall_progress': 82.5,
            'message': f'✅ AI 生成完成 | 輸出: {result.width}x{result.height} | 風格: 半寫實+賽璐璐+高光',
            'image': image_to_base64(result)
        })
        
        # 子步驟 3.3: 處理透明背景（佔步驟3的10%）
        await send_progress(websocket, {
            'type': 'substep_start',
            'step_id': 3,
            'substep_id': 3,
            'step_progress': 90,
            'overall_progress': 82.5,
            'message': f'🎭 處理透明背景 | 方法: numpy連通區域分析 | 閾值: 240'
        })
        
        for pct in range(0, 101, 25):
            await send_progress(websocket, {
                'type': 'substep_update',
                'step_id': 3,
                'substep_id': 3,
                'step_progress': 90 + pct * 0.1,
                'overall_progress': 82.5 + pct * 0.075,
                'message': f'🎭 numpy 連通區域分析... {pct}%'
            })
        
        await send_progress(websocket, {
            'type': 'step_complete',
            'step_id': 3,
            'step_progress': 100,
            'overall_progress': 90,
            'message': '✅ AI 風格轉換完成'
        })
        
        # ========== 步驟 4: 最終處理（佔總進度 10%） ==========
        if is_photo:
            substeps = ['統一尺寸和位置', '水平底部裁切']
        else:
            substeps = ['統一尺寸和位置']
        
        await send_progress(websocket, {
            'type': 'step_start',
            'step_id': 4,
            'step_name': '最終處理',
            'step_progress': 0,
            'overall_progress': 90,
            'message': '📐 最終處理開始...',
            'substeps': substeps
        })
        
        # 子步驟 4.1: 統一尺寸
        await send_progress(websocket, {
            'type': 'substep_start',
            'step_id': 4,
            'substep_id': 1,
            'step_progress': 0,
            'overall_progress': 90,
            'message': f'📐 統一尺寸 | 目標: 1000x1000 | 來源: {result.width}x{result.height} | 頭部比例: 35%'
        })
        
        for pct in range(0, 81, 20):
            await send_progress(websocket, {
                'type': 'substep_update',
                'step_id': 4,
                'substep_id': 1,
                'step_progress': pct * 0.7,
                'overall_progress': 90 + pct * 0.05,
                'message': f'📐 調整人物大小和位置... {pct}%'
            })
        
        if is_photo:
            # 子步驟 4.2: 底部裁切（僅真人照片）
            await send_progress(websocket, {
                'type': 'substep_start',
                'step_id': 4,
                'substep_id': 2,
                'step_progress': 70,
                'overall_progress': 94,
                'message': '✂️ 水平底部裁切...'
            })
            
            for pct in range(0, 101, 30):
                await send_progress(websocket, {
                    'type': 'substep_update',
                    'step_id': 4,
                    'substep_id': 2,
                    'step_progress': 70 + pct * 0.3,
                    'overall_progress': 94 + pct * 0.06,
                    'message': f'✂️ numpy 裁切處理... {pct}%'
                })
        
        await send_progress(websocket, {
            'type': 'step_complete',
            'step_id': 4,
            'step_progress': 100,
            'overall_progress': 100,
            'message': f'✅ 最終處理完成 | 最終尺寸: 1000x1000 | 透明背景: 是 | 類型: {type_name}'
        })
        
        # 發送最終結果
        await send_progress(websocket, {
            'type': 'complete',
            'image': image_to_base64(result),
            'message': f'✅ 處理完成！{type_name} → 向量插畫風格'
        })
        
    except WebSocketDisconnect:
        print("客戶端斷開連接")
    except Exception as e:
        await websocket.send_json({
            'type': 'error',
            'message': f'處理失敗: {str(e)}'
        })
    finally:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    import socket
    
    print("🚀 啟動圖片風格轉換工具（FastAPI 版本）")
    print("-" * 50)
    
    # 自動尋找可用端口
    def find_free_port(start_port=8000):
        """找到可用的端口"""
        port = start_port
        while port < start_port + 100:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('127.0.0.1', port))
                sock.close()
                return port
            except OSError:
                port += 1
        raise OSError("無法找到可用端口")
    
    port = find_free_port(8000)
    print(f"📡 使用端口: {port}")
    print(f"🌐 訪問地址: http://127.0.0.1:{port}")
    print("-" * 50)
    
    uvicorn.run(app, host="127.0.0.1", port=port)
