#!/usr/bin/env python3
"""
圖片風格轉換工具 - 最終正確版本

改進：
1. 總體進度條（頂部）
2. 每個步驟的詳細進度（流暢動畫）
3. 步驟詳細說明整合到步驟框中（2行）
4. 當前狀態繪製在圖片底部（疊加）
5. 布局：左側上傳，右側結果+步驟
"""

import gradio as gr
from PIL import Image, ImageDraw, ImageFont
import time

from src.gemini_client import GeminiClient, ImageType
from src.image_processor import ImageProcessor
from src.style_converter import StyleConverter


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


def add_status_to_image(image: Image.Image, status_text: str) -> Image.Image:
    """
    在圖片底部繪製狀態條（半透明黑底白字）
    統一圖片尺寸以保持狀態條大小一致
    
    Args:
        image: 原始圖片
        status_text: 狀態文字
        
    Returns:
        帶狀態條的圖片（統一尺寸）
    """
    if image is None:
        return None
    
    # 統一尺寸為 800x800（顯示用）
    display_size = (800, 800)
    
    # 調整圖片大小（保持比例）
    img_copy = image.copy()
    img_copy.thumbnail(display_size, Image.Resampling.LANCZOS)
    
    # 創建固定尺寸的畫布
    canvas = Image.new('RGBA', display_size, (40, 40, 40, 255))
    
    # 將圖片貼到畫布中央
    paste_x = (display_size[0] - img_copy.width) // 2
    paste_y = (display_size[1] - img_copy.height) // 2
    
    if img_copy.mode != 'RGBA':
        img_copy = img_copy.convert('RGBA')
    canvas.paste(img_copy, (paste_x, paste_y), img_copy)
    
    # 在底部繪製固定高度的狀態條
    bar_height = 50
    overlay = Image.new('RGBA', (display_size[0], bar_height), (0, 0, 0, 200))
    canvas.paste(overlay, (0, display_size[1] - bar_height), overlay)
    
    # 繪製文字
    draw = ImageDraw.Draw(canvas)
    
    # 嘗試載入中文字體
    font = None
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
    ]
    
    for font_path in font_paths:
        try:
            font = ImageFont.truetype(font_path, 20)
            break
        except:
            continue
    
    # 如果都失敗，使用默認（但移除 emoji）
    if font is None:
        font = ImageFont.load_default()
        # 移除 emoji，只保留文字
        status_text = ''.join(c for c in status_text if ord(c) < 0x1F000)
    
    # 計算文字位置（居中）
    try:
        bbox = draw.textbbox((0, 0), status_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except:
        # 如果 textbbox 失敗，使用估算
        text_width = len(status_text) * 10
        text_height = 20
    
    text_x = (display_size[0] - text_width) // 2
    text_y = display_size[1] - bar_height + (bar_height - text_height) // 2
    
    # 繪製白色文字
    draw.text((text_x, text_y), status_text, fill=(255, 255, 255, 255), font=font)
    
    return canvas


def process_image_with_progress(image: Image.Image):
    """
    處理圖片 - 完整的多步驟進度顯示
    
    Yields: (結果圖帶狀態, 總進度, 步驟1, 步驟2, 步驟3, 步驟4)
    """
    if image is None:
        yield None, 0, "⚪ 等待開始", "⚪ 等待開始", "⚪ 等待開始", "⚪ 等待開始"
        return
    
    try:
        # ========== 步驟 1: 分析圖片類型 ==========
        step1 = "⏳ 【步驟 1/4】分析圖片類型 - 0%\n🔍 正在調用 Gemini AI..."
        img_with_status = add_status_to_image(image, "🔍 調用 AI 分析圖片類型 - 0%")
        yield img_with_status, 0.0, step1, "⚪ 等待中", "⚪ 等待中", "⚪ 等待中"
        
        # 模擬進度增加
        for pct in [10, 20, 30, 40]:
            step1 = f"⏳ 【步驟 1/4】分析圖片類型 - {pct}%\n🤖 等待 AI 回應中..."
            img_with_status = add_status_to_image(image, f"🔍 AI 分析圖片類型... {pct}%")
            yield img_with_status, pct/400, step1, "⚪ 等待中", "⚪ 等待中", "⚪ 等待中"
            time.sleep(0.05)
        
        # 實際 AI 調用
        client = get_gemini_client()
        
        for pct in [50, 60, 70, 80, 90]:
            step1 = f"⏳ 【步驟 1/4】分析圖片類型 - {pct}%\n🤖 AI 正在分析圖片內容..."
            img_with_status = add_status_to_image(image, f"🔍 AI 分析中... {pct}%")
            yield img_with_status, pct/400, step1, "⚪ 等待中", "⚪ 等待中", "⚪ 等待中"
            time.sleep(0.05)
        
        image_type = client.analyze_image_type(image)
        type_name = "真人照片" if image_type == ImageType.REAL_PHOTO else "像素插畫"
        
        # 完成
        step1 = f"✅ 【步驟 1/4】分析完成 - 100%\n結果: {type_name}"
        img_with_status = add_status_to_image(image, f"✅ 分析完成：{type_name}")
        yield img_with_status, 0.25, step1, "⚪ 等待中", "⚪ 等待中", "⚪ 等待中"
        
        # ========== 步驟 2: 圖片預處理 ==========
        process_desc = "移除背景" if image_type == ImageType.REAL_PHOTO else "處理格式"
        
        # 0-50%
        for pct in [0, 10, 20, 30, 40]:
            step2 = f"⏳ 【步驟 2/4】圖片預處理 - {pct}%\n✂️ 正在{process_desc}..."
            img_with_status = add_status_to_image(image, f"✂️ {process_desc}... {pct}%")
            yield img_with_status, 0.25 + pct/400, step1, step2, "⚪ 等待中", "⚪ 等待中"
            time.sleep(0.05)
        
        # 實際處理
        for pct in [50, 60, 70, 80, 90]:
            step2 = f"⏳ 【步驟 2/4】圖片預處理 - {pct}%\n🔧 {process_desc}處理中..."
            img_with_status = add_status_to_image(image, f"✂️ {process_desc}處理... {pct}%")
            yield img_with_status, 0.25 + pct/400, step1, step2, "⚪ 等待中", "⚪ 等待中"
            time.sleep(0.05)
        
        processed = image_processor.process_image(image, image_type)
        
        # 完成
        step2 = f"✅ 【步驟 2/4】預處理完成 - 100%\n尺寸: {processed.width}x{processed.height}"
        img_with_status = add_status_to_image(processed, f"✅ 預處理完成 ({processed.width}x{processed.height})")
        yield img_with_status, 0.5, step1, step2, "⚪ 等待中", "⚪ 等待中"
        
        # ========== 步驟 3: AI 風格轉換（最耗時） ==========
        # 0-30%
        for pct in [0, 5, 10, 15, 20, 25]:
            step3 = f"⏳ 【步驟 3/4】AI 風格轉換 - {pct}%\n🤖 正在調用 Gemini AI 生成向量插畫..."
            img_with_status = add_status_to_image(processed, f"🤖 調用 Gemini AI 生成... {pct}%")
            yield img_with_status, 0.5 + pct/400, step1, step2, step3, "⚪ 等待中"
            time.sleep(0.1)
        
        # 30-60%
        for pct in [30, 35, 40, 45, 50, 55]:
            step3 = f"⏳ 【步驟 3/4】AI 風格轉換 - {pct}%\n🎨 AI 正在生成半寫實企業頭像風格..."
            img_with_status = add_status_to_image(processed, f"🎨 生成向量插畫風格... {pct}%")
            yield img_with_status, 0.5 + pct/400, step1, step2, step3, "⚪ 等待中"
            time.sleep(0.1)
        
        # 實際 AI 調用
        for pct in [60, 65, 70, 75, 80, 85, 90]:
            step3 = f"⏳ 【步驟 3/4】AI 風格轉換 - {pct}%\n✨ 套用賽璐璐著色和橘色高光效果..."
            img_with_status = add_status_to_image(processed, f"✨ 套用賽璐璐著色和高光... {pct}%")
            yield img_with_status, 0.5 + pct/400, step1, step2, step3, "⚪ 等待中"
            time.sleep(0.1)
        
        result = style_converter.apply_style(processed, transparent_bg=True)
        
        # 完成
        step3 = "✅ 【步驟 3/4】AI 轉換完成 - 100%\n向量插畫風格已生成"
        img_with_status = add_status_to_image(result, "✅ AI 風格轉換完成")
        yield img_with_status, 0.875, step1, step2, step3, "⚪ 等待中"
        
        # ========== 步驟 4: 最終處理 ==========
        # 0-80%
        for pct in [0, 20, 40, 60]:
            step4 = f"⏳ 【步驟 4/4】最終處理 - {pct}%\n📐 統一尺寸和位置到 1000x1000..."
            img_with_status = add_status_to_image(result, f"📐 統一尺寸和位置... {pct}%")
            yield img_with_status, 0.875 + pct/800, step1, step2, step3, step4
            time.sleep(0.05)
        
        # 80-100%
        for pct in [80, 90]:
            step4 = f"⏳ 【步驟 4/4】最終處理 - {pct}%\n🎭 套用透明背景和最終調整..."
            img_with_status = add_status_to_image(result, f"🎭 套用透明背景... {pct}%")
            yield img_with_status, 0.875 + pct/800, step1, step2, step3, step4
            time.sleep(0.05)
        
        # 完成
        step4 = f"✅ 【步驟 4/4】全部完成 - 100%\n{type_name} → 向量插畫 | {result.width}x{result.height}"
        img_with_status = add_status_to_image(result, f"🎉 完成！({type_name} → 向量插畫)")
        yield img_with_status, 1.0, step1, step2, step3, step4
        
    except Exception as e:
        error_msg = f"❌ 處理失敗: {str(e)}"
        yield None, 0, f"❌ 失敗: {error_msg}", f"❌ 未執行", f"❌ 未執行", f"❌ 未執行"


def create_interface():
    """建立 Gradio 介面"""
    
    with gr.Blocks(title="圖片風格轉換工具") as interface:
        
        gr.Markdown("# 🎨 圖片風格轉換工具")
        gr.Markdown("將人物照片轉換為向量插畫風格：半寫實企業頭像 + 透明背景")
        
        # 總體進度條（置頂）
        overall_progress = gr.Slider(
            minimum=0,
            maximum=1,
            value=0,
            label="📊 總體進度",
            interactive=False,
            show_label=True
        )
        
        with gr.Row():
            # 左側：只有輸入
            with gr.Column(scale=1):
                input_image = gr.Image(
                    label="📤 上傳圖片",
                    type="pil",
                    sources=["upload", "clipboard"],
                    height=400
                )
                
                process_btn = gr.Button(
                    "🚀 開始轉換",
                    variant="primary",
                    size="lg"
                )
            
            # 右側：結果圖 + 處理步驟
            with gr.Column(scale=1):
                output_image = gr.Image(
                    label="🖼️ 處理結果（狀態顯示在圖片底部）",
                    type="pil",
                    height=400
                )
                
                gr.Markdown("### 📋 處理步驟詳情")
                
                step1_box = gr.Textbox(
                    label="",
                    value="⚪ 步驟 1/4: 分析圖片類型",
                    interactive=False,
                    lines=2,
                    max_lines=2,
                    show_label=False
                )
                
                step2_box = gr.Textbox(
                    label="",
                    value="⚪ 步驟 2/4: 圖片預處理",
                    interactive=False,
                    lines=2,
                    max_lines=2,
                    show_label=False
                )
                
                step3_box = gr.Textbox(
                    label="",
                    value="⚪ 步驟 3/4: AI 風格轉換",
                    interactive=False,
                    lines=2,
                    max_lines=2,
                    show_label=False
                )
                
                step4_box = gr.Textbox(
                    label="",
                    value="⚪ 步驟 4/4: 最終處理",
                    interactive=False,
                    lines=2,
                    max_lines=2,
                    show_label=False
                )
        
        gr.Markdown("""
        ---
        ### 📋 使用說明
        
        - 上傳人物照片後點擊「開始轉換」
        - 左側顯示各步驟的詳細進度
        - 右側即時顯示處理結果圖
        - 圖片下方顯示當前執行的動作
        """)
        
        # 綁定事件
        process_btn.click(
            fn=process_image_with_progress,
            inputs=[input_image],
            outputs=[output_image, overall_progress, step1_box, step2_box, step3_box, step4_box]
        )
    
    return interface


def main():
    """主程式入口"""
    print("🚀 啟動圖片風格轉換工具...")
    print("   最終優化版本")
    print("-" * 40)
    
    interface = create_interface()
    interface.queue()
    interface.launch(
        server_name="127.0.0.1",
        share=False,
        inbrowser=True
    )


if __name__ == "__main__":
    main()

