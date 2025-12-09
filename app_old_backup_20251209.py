#!/usr/bin/env python3
"""
圖片風格轉換工具 - FastAPI + WebSocket 版本

完整顯示所有處理步驟（照片7步/插畫6步）
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from PIL import Image
import base64
import io
import asyncio
from pathlib import Path

from src.pipeline.engine import run_pipeline, build_pipeline_from_names
from src.pipeline.style_configs import PRESET_STYLES, STYLE_OPTIONS


app = FastAPI(title="圖片風格轉換工具（Pipeline 架構）")


def image_to_base64(image: Image.Image) -> str:
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"


async def send_progress(websocket: WebSocket, data: dict):
    await websocket.send_json(data)
    await asyncio.sleep(0.03)


@app.get("/", response_class=HTMLResponse)
async def get_index():
    html_path = Path(__file__).parent / "templates" / "index.html"
    return FileResponse(html_path)


@app.get("/api/styles")
async def get_styles():
    """返回可用的風格列表"""
    return {"styles": STYLE_OPTIONS}


async def process_universal_intelligent(websocket: WebSocket, image: Image.Image, style_config: dict):
    """萬能智能版：極簡流程（2步驟）"""
    
    # 發送原圖
    await send_progress(websocket, {
        'type': 'image',
        'image': image_to_base64(image),
        'message': f'圖片已上傳 | 尺寸: {image.width}x{image.height} | 模式: {image.mode}'
    })
    
    # ========== 步驟 1: 準備圖片 ==========
    await send_progress(websocket, {
        'type': 'step_complete',
        'step_id': 1,
        'step_progress': 100,
        'overall_progress': 10,
        'message': '⚡ 極簡流程：無需檢測和預處理'
    })
    
    # ========== 步驟 2: AI 一次生成（萬能 Prompt）==========
    await send_progress(websocket, {
        'type': 'step_start',
        'step_id': 2,
        'step_name': 'AI 萬能智能生成',
        'step_progress': 0,
        'overall_progress': 10,
        'substeps': ['調用 Gemini 2.5 Pro Image', '萬能 Prompt 智能判斷', '一次完成']
    })
    
    await send_progress(websocket, {
        'type': 'substep_start',
        'step_id': 2,
        'substep_id': 1,
        'overall_progress': 10,
        'message': '🤖 調用 Gemini 2.5 Pro Image | 使用萬能智能 Prompt（~3000字）'
    })
    
    # 模擬進度
    for pct in range(0, 91, 5):
        if pct < 30:
            msg = f'🎨 AI 智能分析圖片構圖... {pct}%'
        elif pct < 60:
            msg = f'✨ 套用向量插畫風格... {pct}%'
        else:
            msg = f'🌟 生成最終結果... {pct}%'
        
        await send_progress(websocket, {
            'type': 'substep_update',
            'step_id': 2,
            'substep_id': 1,
            'step_progress': pct,
            'overall_progress': 10 + pct * 0.8,
            'message': msg
        })
        await asyncio.sleep(0.2)
    
    # 實際 AI 生成
    result = style_config["style"](image, {})
    
    await send_progress(websocket, {
        'type': 'step_complete',
        'step_id': 2,
        'step_progress': 100,
        'overall_progress': 100,
        'message': f'✅ 完成！萬能智能版一次生成 | 尺寸: {result.width}x{result.height}',
        'image': image_to_base64(result)
    })
    
    # 發送最終結果
    await send_progress(websocket, {
        'type': 'complete',
        'image': image_to_base64(result),
        'message': f'🎉 完成！萬能智能版 | 極簡流程（1次 API 調用）| 最終尺寸: {result.width}x{result.height}'
    })


@app.websocket("/ws/process")
async def process_image_websocket(websocket: WebSocket):
    await websocket.accept()
    
    try:
        data = await websocket.receive_json()
        image_base64 = data['image'].split(',')[1]
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes))
        
        # 獲取選定的風格（預設為 i4_detailed）
        selected_style = data.get('style', 'i4_detailed')
        style_config = PRESET_STYLES.get(selected_style, PRESET_STYLES['i4_detailed'])
        
        # 判斷處理流程
        if selected_style == 'universal_intelligent':
            # 萬能智能版：極簡流程
            await process_universal_intelligent(websocket, image, style_config)
            return
        
        # I4 系列：詳細流程
        # 發送原圖
        await send_progress(websocket, {
            'type': 'image',
            'image': image_to_base64(image),
            'message': f'圖片已上傳 | 尺寸: {image.width}x{image.height} | 模式: {image.mode}'
        })
        
        # ========== 步驟 1: 檢測圖片類型+身體範圍（AI，合併檢測）==========
        # 檢查是否需要分析（萬能智能版不需要）
        if style_config.get("analysis") is not None:
            await send_progress(websocket, {
                'type': 'step_start',
                'step_id': 1,
                'step_name': '檢測圖片類型+身體範圍',
                'step_progress': 0,
                'overall_progress': 0,
                'substeps': ['調用 Gemini AI', '解析圖片類型', '解析身體範圍']
            })
            
            # 1.1 調用 AI
            await send_progress(websocket, {
                'type': 'substep_start',
                'step_id': 1,
                'substep_id': 1,
                'overall_progress': 0,
                'message': f'🤖 調用 Gemini 2.0 Flash | 輸入: {image.width}x{image.height}'
            })
            
            for pct in range(0, 71, 10):
                await send_progress(websocket, {
                    'type': 'substep_update',
                    'step_id': 1,
                    'substep_id': 1,
                    'step_progress': pct,
                    'overall_progress': pct * 0.03,
                    'message': f'🤖 AI 分析圖片（類型+身體範圍）... {pct}%'
                })
            
            # 使用 Pipeline 分析組件
            analysis = style_config["analysis"](image)
            image_type = analysis["image_type"]
            body_extent = analysis["body_extent"]
            type_name = "真人照片" if image_type == "photo" else "像素插畫"
            is_photo = (image_type == "photo")
            
            # 1.2 解析類型
            await send_progress(websocket, {
                'type': 'substep_complete',
                'step_id': 1,
                'substep_id': 1,
                'step_progress': 70,
                'overall_progress': 2.1,
                'message': '✅ AI 調用完成'
            })
            
            await send_progress(websocket, {
                'type': 'substep_start',
                'step_id': 1,
                'substep_id': 2,
                'step_progress': 70,
                'overall_progress': 2.1,
                'message': '📊 解析圖片類型...'
            })
            
            await send_progress(websocket, {
                'type': 'substep_complete',
                'step_id': 1,
                'substep_id': 2,
                'step_progress': 85,
                'overall_progress': 3,
                'message': f'✅ 解析結果：{type_name} ({"PHOTO" if is_photo else "ILLUSTRATION"})'
            })
            
            # 1.3 解析身體範圍
            await send_progress(websocket, {
                'type': 'substep_start',
                'step_id': 1,
                'substep_id': 3,
                'step_progress': 85,
                'overall_progress': 3,
                'message': '📊 解析身體範圍...'
            })
            
            body_desc = {
                "head_only": "僅頭部",
                "head_neck": "頭部+脖子",
                "head_chest": "頭部到上胸部（理想）",
                "full_body": "全身照"
            }.get(body_extent, body_extent)
            
            await send_progress(websocket, {
                'type': 'step_complete',
                'step_id': 1,
                'step_progress': 100,
                'overall_progress': 4,
                'message': f'✅ 步驟1完成 | 圖片類型: {type_name} | 身體範圍: {body_desc} ({body_extent.upper()}) | API: Gemini 2.0 Flash'
            })
        else:
            # 萬能智能版：跳過分析步驟
            await send_progress(websocket, {
                'type': 'step_complete',
                'step_id': 1,
                'step_progress': 100,
                'overall_progress': 4,
                'message': '⚡ 萬能智能版：跳過檢測步驟（極簡流程）'
            })
            analysis = {}
            image_type = "photo"  # 預設值
            body_extent = "head_chest"  # 預設值
            body_desc = "頭部到上胸部（理想）"  # 預設值
            type_name = "真人照片"  # 預設值
            is_photo = True  # 預設值
        
        # ========== 步驟 2: 圖片預處理 ==========
        # 檢查預處理類型
        preprocess_func = style_config.get("preprocess")
        needs_rembg = (preprocess_func is not None and 
                      preprocess_func.__name__ == "rembg_preprocess")
        
        if needs_rembg:
            # I4 詳細版：去背 + 裁切
            await send_progress(websocket, {
                'type': 'step_start',
                'step_id': 2,
                'step_name': '圖片預處理（去背）',
                'step_progress': 0,
                'overall_progress': 4,
                'substeps': ['rembg 去背', '裁切平整底部']
            })
            
            # 2.1 去背
            await send_progress(websocket, {
                'type': 'substep_start',
                'step_id': 2,
                'substep_id': 1,
                'overall_progress': 4,
                'message': f'✂️ 使用 rembg 去背 | 模型: u2net | 輸入: {image.width}x{image.height}'
            })
            
            for pct in range(0, 81, 10):
                await send_progress(websocket, {
                    'type': 'substep_update',
                    'step_id': 2,
                    'substep_id': 1,
                    'step_progress': pct,
                    'overall_progress': 4 + pct * 0.08,
                    'message': f'✂️ 去背處理中（rembg deep learning）... {pct}%'
                })
            
            # 2.2 裁切
            await send_progress(websocket, {
                'type': 'substep_start',
                'step_id': 2,
                'substep_id': 2,
                'step_progress': 80,
                'overall_progress': 10.4,
                'message': '📐 裁切平整底部 | 方法: numpy alpha分析'
            })
            
            # 使用 Pipeline 預處理組件
            processed = preprocess_func(image, analysis)
            
            await send_progress(websocket, {
                'type': 'step_complete',
                'step_id': 2,
                'step_progress': 100,
                'overall_progress': 12,
                'message': f'✅ 預處理完成 | 輸出: {processed.width}x{processed.height} | 已去背',
                'image': image_to_base64(processed)
            })
        else:
            # I4 簡化版 / 萬能智能版：跳過預處理
            await send_progress(websocket, {
                'type': 'step_complete',
                'step_id': 2,
                'step_progress': 100,
                'overall_progress': 6,
                'message': '⚡ 跳過預處理步驟（極簡流程）'
            })
            # 調用 no_preprocess 或直接轉格式
            if preprocess_func is not None:
                processed = preprocess_func(image, analysis)
            else:
                processed = image.convert("RGBA") if image.mode != "RGBA" else image
        
        # ========== 步驟 3: 生成 Body Instruction ==========
        await send_progress(websocket, {
            'type': 'step_start',
            'step_id': 3,
            'step_name': '生成處理指令',
            'step_progress': 0,
            'overall_progress': 12 if is_photo else 6,
            'substeps': ['查找對應指令模板']
        })
        
        instruction_type = {
            "full_body": "裁切全身到上胸部",
            "head_only": "生成脖子、肩膀、上胸部",
            "head_neck": "生成肩膀和上胸部",
            "head_chest": "保持當前構圖"
        }.get(body_extent, "預設處理")
        
        await send_progress(websocket, {
            'type': 'substep_start',
            'step_id': 3,
            'substep_id': 1,
            'overall_progress': 12 if is_photo else 6,
            'message': f'📝 生成 Body Instruction | 身體範圍: {body_desc} | 指令類型: {instruction_type}'
        })
        
        await send_progress(websocket, {
            'type': 'step_complete',
            'step_id': 3,
            'step_progress': 100,
            'overall_progress': 13 if is_photo else 7,
            'message': f'✅ 步驟3完成 | 指令類型: {instruction_type} | Body Extent: {body_extent} | 來源: BODY_INSTRUCTIONS字典'
        })
        
        # ========== 步驟 4: 構建完整 Prompt ==========
        await send_progress(websocket, {
            'type': 'step_start',
            'step_id': 4,
            'step_name': '構建 AI Prompt',
            'step_progress': 0,
            'overall_progress': 13 if is_photo else 7,
            'substeps': ['組合風格要求']
        })
        
        await send_progress(websocket, {
            'type': 'substep_start',
            'step_id': 4,
            'substep_id': 1,
            'overall_progress': 13 if is_photo else 7,
            'message': '📋 組合 Prompt | Body Instruction + Style Requirements + Rim Lighting + Constraints'
        })
        
        await send_progress(websocket, {
            'type': 'step_complete',
            'step_id': 4,
            'step_progress': 100,
            'overall_progress': 14 if is_photo else 8,
            'message': f'✅ 步驟4完成 | Prompt長度: ~600字 | 包含: Body Instruction + Style要求 + Rim Lighting + 限制條件 | 目標: Gemini 3 Pro Image'
        })
        
        # ========== 步驟 5: AI 生成向量插畫（最耗時！）==========
        await send_progress(websocket, {
            'type': 'step_start',
            'step_id': 5,
            'step_name': 'AI 生成向量插畫（最耗時）',
            'step_progress': 0,
            'overall_progress': 14 if is_photo else 8,
            'substeps': ['調用 Gemini 3 Pro', '等待 AI 生成', '提取圖片結果']
        })
        
        # 5.1 調用 AI
        await send_progress(websocket, {
            'type': 'substep_start',
            'step_id': 5,
            'substep_id': 1,
            'overall_progress': 14 if is_photo else 8,
            'message': f'🤖 調用 Gemini 3 Pro Image | Prompt: {instruction_type} | 預計: 15-30秒'
        })
        
        for pct in range(0, 21, 5):
            await send_progress(websocket, {
                'type': 'substep_update',
                'step_id': 5,
                'substep_id': 1,
                'step_progress': pct,
                'overall_progress': (14 if is_photo else 8) + pct * 0.05,
                'message': f'🤖 發送 Prompt 到 Gemini 3 Pro Image... {pct}%'
            })
        
        # 5.2 等待 AI 生成
        await send_progress(websocket, {
            'type': 'substep_start',
            'step_id': 5,
            'substep_id': 2,
            'step_progress': 20,
            'overall_progress': (15 if is_photo else 9),
            'message': '🎨 AI 正在生成中（這是最耗時的步驟）...'
        })
        
        # 細分 AI 生成過程
        for pct in range(20, 91, 3):
            if pct < 35:
                msg = f'🎨 AI 生成向量插畫風格 | 進度: {pct}%'
            elif pct < 55:
                msg = f'🖼️ 套用半寫實企業頭像風格 | 進度: {pct}%'
            elif pct < 75:
                msg = f'✨ 套用賽璐璐著色（cel-shaded）| 進度: {pct}%'
            else:
                msg = f'🌟 套用橘色/金色邊緣高光 | 進度: {pct}%'
            
            await send_progress(websocket, {
                'type': 'substep_update',
                'step_id': 5,
                'substep_id': 2,
                'step_progress': pct,
                'overall_progress': (15 if is_photo else 9) + (pct - 20) * 0.6,
                'message': msg
            })
            await asyncio.sleep(0.15)
        
        # 使用 Pipeline 風格生成組件
        result = style_config["style"](processed, analysis)
        
        # 5.3 提取圖片
        await send_progress(websocket, {
            'type': 'substep_start',
            'step_id': 5,
            'substep_id': 3,
            'step_progress': 90,
            'overall_progress': (57 if is_photo else 51),
            'message': '📦 提取 AI 生成的圖片...'
        })
        
        await send_progress(websocket, {
            'type': 'step_complete',
            'step_id': 5,
            'step_progress': 100,
            'overall_progress': (58 if is_photo else 52),
            'message': f'✅ 步驟5完成 | AI生成結果: {result.width}x{result.height} | 風格特徵: 向量插畫+半寫實+賽璐璐著色+橘色高光 | 背景: 白色 | 模型: Gemini 3 Pro Image',
            'image': image_to_base64(result)
        })
        
        # ========== 步驟 6: 後處理 ==========
        await send_progress(websocket, {
            'type': 'step_start',
            'step_id': 6,
            'step_name': '後處理',
            'step_progress': 0,
            'overall_progress': (58 if is_photo else 52),
            'substeps': ['白色轉透明', '統一尺寸和位置']
        })
        
        # 6.1 白色轉透明
        await send_progress(websocket, {
            'type': 'substep_start',
            'step_id': 6,
            'substep_id': 1,
            'overall_progress': (58 if is_photo else 52),
            'message': '🎭 白色背景轉透明 | 方法: numpy連通區域分析 | 閾值: 240'
        })
        
        for pct in range(0, 101, 20):
            await send_progress(websocket, {
                'type': 'substep_update',
                'step_id': 6,
                'substep_id': 1,
                'step_progress': pct * 0.5,
                'overall_progress': (58 if is_photo else 52) + pct * 0.15,
                'message': f'🎭 分析連通區域，保護人物內部白色... {pct}%'
            })
        
        # 使用 Pipeline 背景組件
        result = style_config["background"](result, analysis)
        
        await send_progress(websocket, {
            'type': 'substep_complete',
            'step_id': 6,
            'substep_id': 1,
            'step_progress': 50,
            'overall_progress': (73 if is_photo else 67),
            'message': '✅ 透明背景處理完成'
        })
        
        # 6.2 統一尺寸
        await send_progress(websocket, {
            'type': 'substep_start',
            'step_id': 6,
            'substep_id': 2,
            'step_progress': 50,
            'overall_progress': (73 if is_photo else 67),
            'message': f'📐 統一尺寸和位置 | 目標: 1000x1000 | 頭部比例: 35% | 來源: {result.width}x{result.height}'
        })
        
        for pct in range(0, 101, 20):
            await send_progress(websocket, {
                'type': 'substep_update',
                'step_id': 6,
                'substep_id': 2,
                'step_progress': 50 + pct * 0.5,
                'overall_progress': (73 if is_photo else 67) + pct * 0.15,
                'message': f'📐 調整人物大小和位置（人物高度70%，寬度85%）... {pct}%'
            })
        
        # 使用 Pipeline 後處理組件
        result = style_config["postprocess"](result, analysis)
        
        await send_progress(websocket, {
            'type': 'step_complete',
            'step_id': 6,
            'step_progress': 100,
            'overall_progress': (88 if is_photo else 82),
            'message': f'✅ 步驟6完成 | 最終尺寸: {result.width}x{result.height} | 背景: 透明 | 人物位置: 頭部35% | 人物大小: 高70%寬85%'
        })
        
        # ========== 步驟 7: 照片特殊處理（僅照片）==========
        if is_photo:
            await send_progress(websocket, {
                'type': 'step_start',
                'step_id': 7,
                'step_name': '照片特殊處理',
                'step_progress': 0,
                'overall_progress': 88,
                'substeps': ['水平底部裁切']
            })
            
            await send_progress(websocket, {
                'type': 'substep_start',
                'step_id': 7,
                'substep_id': 1,
                'overall_progress': 88,
                'message': '✂️ 水平底部裁切 | 方法: numpy找中心區域最低點'
            })
            
            for pct in range(0, 101, 25):
                await send_progress(websocket, {
                    'type': 'substep_update',
                    'step_id': 7,
                    'substep_id': 1,
                    'step_progress': pct,
                    'overall_progress': 88 + pct * 0.12,
                    'message': f'✂️ 裁切底部多餘空間，保持平整邊緣... {pct}%'
                })
        
            # 底部裁切已整合到 normalize_1000 組件中
            
            await send_progress(websocket, {
                'type': 'step_complete',
                'step_id': 7,
                'step_progress': 100,
                'overall_progress': 100,
                'message': f'✅ 步驟7完成 | 底部裁切: 已執行 | 方法: numpy中心區域分析 | 效果: 平整水平底邊 | 照片處理全部完成'
            })
        else:
            # 插畫沒有步驟7，直接完成
            await send_progress(websocket, {
                'type': 'step_complete',
                'step_id': 6,
                'step_progress': 100,
                'overall_progress': 100,
                'message': '✅ 插畫處理全部完成'
            })
        
        # 發送最終結果
        await send_progress(websocket, {
            'type': 'complete',
            'image': image_to_base64(result),
            'message': f'🎉 完成！{type_name} → 向量插畫風格 | 最終尺寸: {result.width}x{result.height} | 透明背景'
        })
        
    except WebSocketDisconnect:
        print("客戶端斷開連接")
    except Exception as e:
        import traceback
        traceback.print_exc()
        await websocket.send_json({
            'type': 'error',
            'message': f'處理失敗: {str(e)}'
        })
    finally:
        try:
            await websocket.close()
        except:
            pass


if __name__ == "__main__":
    import uvicorn
    import socket
    
    print("🚀 啟動圖片風格轉換工具（FastAPI 版本）")
    print("-" * 50)
    
    def find_free_port(start_port=8000):
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
