#!/usr/bin/env python3
"""
多風格圖片轉換前端（Gradio）
- 支援上傳圖片或貼上圖片連結
- 可複選風格（C、E、F），使用中文描述與示意圖
- 生成結果可於預覽區一次檢視，並提供下載按鈕
"""

import io
import os
import tempfile
import zipfile
from datetime import datetime
from typing import List, Tuple

import gradio as gr
import requests
from PIL import Image

from src.style_c_converter import StyleCConverter
from src.style_e_converter import StyleEConverter
from src.style_e2_converter import StyleE2Converter
from src.style_e3_converter import StyleE3Converter
from src.style_f_converter import StyleFConverter
from src.style_g_converter import StyleGConverter
from src.style_h_converter import StyleHConverter
from src.style_i_converter import StyleIConverter
from src.style_i2_converter import StyleI2Converter


# 風格設定（中文呈現 + 示意圖）
STYLE_OPTIONS = [
    {
        "key": "style_c",
        "label": "風格Ｃ｜墨線筆觸寫實插畫",
        "description": "墨水筆觸、臉部留白、服裝灰階色塊。",
        "example": "style_examples/style_c.png",
    },
    {
        "key": "style_e",
        "label": "風格Ｅ｜胸像＋藍色圓背景（灰階）",
        "description": "胸部以上構圖、白色描邊、純藍圓形背景、灰階。",
        "example": "style_examples/style_e.png",
    },
    {
        "key": "style_e2",
        "label": "風格Ｅ2｜胸像＋自然上色",
        "description": "胸部以上構圖、自然膚色/髮色/服裝上色、透明背景。",
        "example": "style_examples/style_e2.png",
    },
    {
        "key": "style_e3",
        "label": "風格Ｅ3｜胸像＋藍綠色高光",
        "description": "胸部以上構圖、自然上色、左上藍綠色高光、無白色描邊。",
        "example": "style_examples/style_e3.png",
    },
    {
        "key": "style_f",
        "label": "風格Ｆ｜炭筆手繪＋藍綠色塊",
        "description": "炭筆/蠟筆粗糙質感，抽象藍綠色塊，大面積留白。",
        "example": "style_examples/style_f.png",
    },
    {
        "key": "style_g",
        "label": "風格Ｇ｜極簡扁平向量＋去背",
        "description": "無描邊、極簡平滑色塊、白色背景去背。",
        "example": "style_examples/style_g.png",
    },
    {
        "key": "style_h",
        "label": "風格Ｈ｜單色調蠟筆素描",
        "description": "藍綠色單色調、粗糙蠟筆線條、大面積留白。",
        "example": "style_examples/style_h.png",
    },
    {
        "key": "style_i",
        "label": "風格Ｉ｜寫實漫畫風格",
        "description": "寫實比例、增強色彩、漫畫質感、清晰線條。",
        "example": "style_examples/style_i.png",
    },
    {
        "key": "style_i2",
        "label": "風格Ｉ2｜成熟寫實漫畫",
        "description": "深輪廓、成熟特徵、更強陰影、橘色高光（左側）。",
        "example": "style_examples/style_i2.png",
    },
]

STYLE_LABEL_TO_KEY = {item["label"]: item["key"] for item in STYLE_OPTIONS}

# 事先初始化 converter，避免重複載入
STYLE_CONVERTERS = {
    "style_c": StyleCConverter(),
    "style_e": StyleEConverter(),
    "style_e2": StyleE2Converter(),
    "style_e3": StyleE3Converter(),
    "style_f": StyleFConverter(),
    "style_g": StyleGConverter(),
    "style_h": StyleHConverter(),
    "style_i": StyleIConverter(),
    "style_i2": StyleI2Converter(),
}


def load_image(image_file, image_url: str) -> Image.Image:
    """從上傳檔案或網址載入圖片"""
    if image_file is not None:
        img = Image.open(image_file)
        return img.convert("RGBA")

    if image_url:
        response = requests.get(image_url, timeout=15)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        return img.convert("RGBA")

    raise ValueError("請先上傳圖片或提供圖片連結")


def run_styles(
    image: Image.Image, selected_labels: List[str]
) -> Tuple[List[Tuple[str, str]], str]:
    """套用多個風格並回傳 (label, path) 列表與下載壓縮檔"""
    if not selected_labels:
        raise ValueError("請至少選擇一種風格")

    temp_dir = tempfile.mkdtemp(prefix="tempo_style_")
    base_filename = datetime.now().strftime("%Y%m%d_%H%M%S")

    gallery_items: List[Tuple[str, str]] = []
    saved_paths: List[str] = []

    for idx, label in enumerate(selected_labels, start=1):
        style_key = STYLE_LABEL_TO_KEY.get(label)
        if style_key is None:
            continue

        converter = STYLE_CONVERTERS[style_key]
        result_image = converter.apply_style(image.copy())

        output_path = os.path.abspath(
            os.path.join(temp_dir, f"{base_filename}_{style_key}_{idx}.png")
        )
        result_image.save(output_path, "PNG")
        saved_paths.append(output_path)
        gallery_items.append((output_path, label))

    # 根據生成數量決定下載檔案
    if len(saved_paths) == 1:
        download_path = saved_paths[0]
    else:
        zip_path = os.path.abspath(
            os.path.join(temp_dir, f"{base_filename}_results.zip")
        )
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in saved_paths:
                zipf.write(file_path, arcname=os.path.basename(file_path))
        download_path = zip_path

    return gallery_items, download_path


def process(image_file, image_url, selected_styles):
    """Gradio 介面觸發流程"""
    try:
        image = load_image(image_file, image_url)
        gallery, zip_path = run_styles(image, selected_styles)
        status = "✅ 生成完成！可於預覽區檢視並下載所有圖片。"
        return gallery, zip_path, status
    except Exception as exc:
        return [], None, f"❌ 發生錯誤：{exc}"


def build_style_gallery_data():
    """準備示意圖資料（返回 (image_path, caption)）"""
    gallery_data = []
    for item in STYLE_OPTIONS:
        example_path = os.path.abspath(item["example"])
        if os.path.exists(example_path):
            gallery_data.append((example_path, item["label"]))
    return gallery_data


def main():
    with gr.Blocks(title="Tempo 多風格圖片轉換") as demo:
        gr.Markdown(
            "## Tempo 多風格圖片轉換\n"
            "1. 上傳圖片或貼上圖片連結\n"
            "2. 勾選想要套用的風格\n"
            "3. 點擊「開始生成」，預覽並下載結果"
        )

        with gr.Row():
            with gr.Column():
                image_input = gr.Image(label="資料輸入區：上傳圖片", type="filepath")
                image_url = gr.Textbox(
                    label="或貼上圖片連結",
                    placeholder="https://example.com/photo.png",
                )

        gr.Markdown("### 風格選擇區（可複選）")
        style_checkbox = gr.CheckboxGroup(
            choices=[item["label"] for item in STYLE_OPTIONS],
            label="選擇要套用的風格",
            info="可同時勾選多種風格，系統會分別生成。",
        )

        gr.Markdown("#### 風格示意圖")
        style_gallery = gr.Gallery(
            value=build_style_gallery_data(),
            columns=3,
            height="auto",
            allow_preview=True,
            show_label=False,
        )

        generate_button = gr.Button("開始生成", variant="primary")

        gr.Markdown("### 預覽區")
        preview_gallery = gr.Gallery(
            label="生成結果",
            columns=3,
            height="auto",
            allow_preview=True,
        )

        download_file = gr.File(
            label="下載所有圖片（點擊右側檔名下載）",
            elem_classes=["download-file"],
        )
        status_text = gr.Markdown()

        generate_button.click(
            fn=process,
            inputs=[image_input, image_url, style_checkbox],
            outputs=[preview_gallery, download_file, status_text],
        )

    demo.launch(
        server_name="0.0.0.0",
    )


if __name__ == "__main__":
    main()

