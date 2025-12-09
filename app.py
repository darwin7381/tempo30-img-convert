#!/usr/bin/env python3
"""
圖片風格轉換工具 - 細粒度 Pipeline 版本

真正萬用的動態顯示：
- 根據風格配置自動執行所有步驟
- 詳細顯示每個步驟的結果
- 所有風格統一使用相同的執行邏輯
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from PIL import Image
import base64
import io
import asyncio
from pathlib import Path

from src.pipeline.style_configs_fine_grained import FINE_GRAINED_STYLES, STYLE_OPTIONS


app = FastAPI(title="圖片風格轉換工具（細粒度 Pipeline）")


def image_to_base64(image: Image.Image) -> str:
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"


async def send_progress(websocket: WebSocket, data: dict):
    await websocket.send_json(data)
    await asyncio.sleep(0.03)


async def simulate_progress(websocket: WebSocket, step_id: int, total_steps: int, step_name: str):
    """模擬步驟進度（在實際處理時顯示假進度）"""
    try:
        # 根據步驟類型決定進度速度
        if "AI" in step_name or "生成" in step_name:
            # AI 步驟：慢速進度（因為真的很慢）
            max_progress = 85  # 只到 85%，留空間給完成時跳到 100%
            sleep_time = 0.5   # 慢一點
        elif "檢測" in step_name:
            # 檢測步驟：中速進度
            max_progress = 80
            sleep_time = 0.3
        else:
            # 其他步驟：快速進度
            max_progress = 90
            sleep_time = 0.2
        
        # 立即發送第一個進度更新（不等待）
        await send_progress(websocket, {
            'type': 'step_update',
            'step_id': step_id,
            'step_progress': 5,
            'overall_progress': ((step_id - 1) + 0.05) / total_steps * 100,
            'message': f'⚙️ {step_name}處理中... 5%'
        })
        
        # 繼續模擬進度更新
        for pct in range(10, max_progress, 5):
            await asyncio.sleep(sleep_time)
            await send_progress(websocket, {
                'type': 'step_update',
                'step_id': step_id,
                'step_progress': pct,
                'overall_progress': ((step_id - 1) + pct / 100) / total_steps * 100,
                'message': f'⚙️ {step_name}處理中... {pct}%'
            })
            
    except asyncio.CancelledError:
        # 實際處理完成，停止模擬
        pass


def format_result_detail(step: dict, result: any, image: Image.Image, context: dict) -> str:
    """萬用結果格式化"""
    step_name = step['name']
    
    # 檢測類型步驟
    if "檢測圖片類型" in step_name:
        if isinstance(result, dict) and 'image_type' in result:
            type_name = "真人照片" if result['image_type'] == "photo" else "插畫作品"
            return f"→ 類型：{type_name}"
        return "→ 檢測完成"
    
    # 檢測身體範圍步驟
    if "檢測身體範圍" in step_name or "身體範圍" in step_name:
        if isinstance(result, dict) and 'body_extent' in result:
            body_map = {
                "head_only": "僅頭部",
                "head_neck": "頭部+脖子",
                "head_chest": "頭部到上胸部（理想）",
                "full_body": "全身照"
            }
            body_desc = body_map.get(result['body_extent'], result['body_extent'])
            return f"→ 身體範圍：{body_desc}"
        return "→ 檢測完成"
    
    # 生成處理指令步驟
    if "生成處理指令" in step_name or "Body Instruction" in step_name:
        if isinstance(result, dict) and 'body_instruction' in result:
            body_extent = context.get('body_extent', 'unknown')
            instruction_type = {
                "full_body": "裁切全身到上胸部",
                "head_only": "生成脖子、肩膀、上胸部",
                "head_neck": "生成肩膀和上胸部",
                "head_chest": "保持當前構圖"
            }.get(body_extent, "預設處理")
            return f"→ 指令類型：{instruction_type}"
        return "→ 指令生成完成"
    
    # 構建 Prompt 步驟
    if "構建" in step_name and "Prompt" in step_name:
        if isinstance(result, dict) and 'prompt' in result:
            prompt_len = len(result['prompt'])
            return f"→ Prompt 長度：{prompt_len}字"
        return "→ Prompt 構建完成"
    
    # 圖片處理步驟（通用）
    if isinstance(image, Image.Image):
        prev_size = context.get('prev_size', 'unknown')
        curr_size = f"{image.width}x{image.height}"
        
        # 如果尺寸改變了
        if prev_size != 'unknown' and prev_size != curr_size:
            return f"→ {prev_size} 處理為 {curr_size}"
        else:
            return f"→ 尺寸：{curr_size}"
    
    return "→ 處理完成"


@app.get("/", response_class=HTMLResponse)
async def get_index():
    html_path = Path(__file__).parent / "templates" / "index.html"
    return FileResponse(html_path)


@app.get("/api/styles")
async def get_styles():
    return {"styles": STYLE_OPTIONS}


@app.websocket("/ws/process")
async def process_image_websocket(websocket: WebSocket):
    """萬用處理函數 - 所有風格統一邏輯"""
    await websocket.accept()
    
    try:
        data = await websocket.receive_json()
        image_base64 = data['image'].split(',')[1]
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes))
        
        # 獲取選定的風格
        selected_style = data.get('style', 'i4_detailed')
        style_config = FINE_GRAINED_STYLES.get(selected_style)
        
        if not style_config:
            await send_progress(websocket, {
                'type': 'error',
                'message': f'找不到風格：{selected_style}'
            })
            return
        
        # 發送原圖
        await send_progress(websocket, {
            'type': 'image',
            'image': image_to_base64(image),
            'message': f'圖片已上傳 | 尺寸: {image.width}x{image.height} | 模式: {image.mode}'
        })
        
        # 獲取步驟列表
        steps = style_config['steps']
        total_steps = len(steps)
        
        await send_progress(websocket, {
            'type': 'info',
            'message': f'📋 {style_config["name"]} | 共 {total_steps} 個步驟'
        })
        
        # 初始化
        context = {'prev_size': f"{image.width}x{image.height}"}
        current_image = image
        
        # ========== 萬用執行邏輯：依次執行所有步驟 ==========
        for i, step in enumerate(steps):
            step_id = i + 1
            step_name = step['name']
            icon = step['icon']
            component = step['component']
            
            # 檢查條件執行
            if 'conditional' in step:
                if not step['conditional'](context):
                    await send_progress(websocket, {
                        'type': 'step_complete',
                        'step_id': step_id,
                        'step_progress': 100,
                        'overall_progress': step_id / total_steps * 100,
                        'message': f'⏭️ {icon} {step_name} | 跳過（不適用）'
                    })
                    continue
        
            # 步驟開始
            await send_progress(websocket, {
                'type': 'step_start',
                'step_id': step_id,
                'step_name': f"{icon} {step_name}",
                'step_progress': 0,
                'overall_progress': (step_id - 1) / total_steps * 100,
                'substeps': []
            })
            
            # 執行步驟
            try:
                # 記錄執行前的狀態
                context['prev_size'] = f"{current_image.width}x{current_image.height}" if isinstance(current_image, Image.Image) else 'unknown'
                
                # 立即發送第一個進度更新（5%）
                await send_progress(websocket, {
                    'type': 'step_update',
                    'step_id': step_id,
                    'step_progress': 5,
                    'overall_progress': ((step_id - 1) + 0.05) / total_steps * 100,
                    'message': f'⚙️ {step_name}處理中... 5%'
                })
                
                # 啟動模擬進度（異步，從 10% 開始）
                progress_task = asyncio.create_task(
                    simulate_progress(websocket, step_id, total_steps, step_name)
                )
                
                # 在執行器中運行組件（不阻塞事件循環，讓模擬進度能並行執行）
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, component, current_image, context)
                
                # 停止模擬進度
                progress_task.cancel()
                try:
                    await progress_task
                except asyncio.CancelledError:
                    pass
                
                # 處理結果
                if step.get('update_context') and isinstance(result, dict):
                    # 更新上下文
                    context.update(result)
                    result_for_detail = result
                elif step.get('update_image') and isinstance(result, Image.Image):
                    # 更新圖片
                    current_image = result
                    result_for_detail = current_image
                else:
                    result_for_detail = result
                
                # 格式化詳細結果
                detail = format_result_detail(step, result_for_detail, current_image, context)
                
                # 快速推進到 95%（完成前的最後衝刺）
                await send_progress(websocket, {
                    'type': 'step_update',
                    'step_id': step_id,
                    'step_progress': 95,
                    'overall_progress': ((step_id - 1) + 0.95) / total_steps * 100,
                    'message': f'✅ {icon} {step_name}即將完成...'
                })
                await asyncio.sleep(0.1)
                
                # 步驟完成（跳到 100%）
                progress_data = {
                    'type': 'step_complete',
                    'step_id': step_id,
                    'step_progress': 100,
                    'overall_progress': step_id / total_steps * 100,
                    'message': f'✅ {icon} {step_name}完成\n   {detail}'
                }
                
                # 如果需要顯示圖片
                if step.get('show_image') and isinstance(current_image, Image.Image):
                    progress_data['image'] = image_to_base64(current_image)
                
                await send_progress(websocket, progress_data)
                
            except Exception as e:
                await send_progress(websocket, {
                    'type': 'error',
                    'step_id': step_id,
                    'message': f'❌ {icon} {step_name}失敗：{str(e)}'
                })
                raise
        
        # 最終結果
        await send_progress(websocket, {
            'type': 'complete',
            'image': image_to_base64(current_image),
            'message': f'🎉 全部完成！{style_config["name"]} | 共 {total_steps} 個步驟 | 最終尺寸: {current_image.width}x{current_image.height}'
        })
        
    except WebSocketDisconnect:
        print("WebSocket 連接已斷開")
    except Exception as e:
        await send_progress(websocket, {
            'type': 'error',
            'message': f'處理失敗：{str(e)}'
        })
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import uvicorn
    import socket
    import os
    
    # 檢查是否在 Railway 或其他雲端環境（有 PORT 環境變數）
    railway_port = os.getenv("PORT")
    
    if railway_port:
        # Railway 環境：使用環境變數的 PORT，監聽所有介面
        port = int(railway_port)
        host = "0.0.0.0"
        print(f"🚀 啟動圖片風格轉換工具（Railway 生產環境）")
        print(f"--------------------------------------------------")
        print(f"📡 端口: {port}")
        print(f"🌐 監聽: {host}")
    else:
        # 本地開發環境：自動尋找可用端口（從 8000 開始）
        def find_free_port(start_port=8000):
            port = start_port
            while port < 65535:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.bind(('127.0.0.1', port))
                    return port
                except OSError:
                    port += 1
            raise RuntimeError("找不到可用端口")
        
        port = find_free_port(8000)
        host = "127.0.0.1"
        print(f"🚀 啟動圖片風格轉換工具（本地開發環境）")
        print(f"--------------------------------------------------")
        print(f"📡 自動選擇端口: {port}")
        print(f"🌐 訪問地址: http://{host}:{port}")
    
    print(f"--------------------------------------------------")
    print(f"✨ 特點：")
    print(f"  - I4 詳細版：10 個細粒度步驟（照片）/ 8 個步驟（插畫）")
    print(f"  - 萬能智能版：1 個步驟（極簡流程）")
    print(f"  - 所有風格統一萬用邏輯")
    print(f"--------------------------------------------------")
    uvicorn.run(app, host=host, port=port)

