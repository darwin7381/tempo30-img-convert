"""Pipeline 組件 - 所有可替換的處理組件（函數式）

重要修正：
- 插畫只檢測類型，不檢測身體範圍（跳過步驟2）
- 照片檢測類型和身體範圍（執行步驟2）
- 完全對齊原版流程圖
"""

from PIL import Image
import io
from google import genai
from google.genai import types
import numpy as np
from scipy import ndimage
from rembg import remove as rembg_remove

from ..config import API_CONFIG
from ..prompts import get_style_prompt, IMAGE_TYPE_PROMPT, BODY_EXTENT_PROMPT
from ..utils import prepare_image_for_api


# ============================================================
# 分析組件
# ============================================================

def gemini_25_analysis_photos_only(image: Image.Image) -> dict:
    """Gemini 2.5 Flash 分析（照片：類型+身體，插畫：只類型）
    
    這個組件完全對齊原版流程：
    - 先檢測類型
    - 如果是照片，再檢測身體範圍
    - 如果是插畫，body_extent 固定為 "head_chest"
    """
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("請在 .env 檔案中設定 GEMINI_API_KEY")
    
    client = genai.Client(api_key=api_key)
    _, img_bytes = prepare_image_for_api(image)
    
    # 步驟1：只檢測圖片類型（對所有圖片）
    response = client.models.generate_content(
        model=API_CONFIG.model_text,
        contents=[
            types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
            IMAGE_TYPE_PROMPT  # 只問類型，不問身體
        ],
        config=types.GenerateContentConfig(response_modalities=['TEXT'])
    )
    
    result = response.candidates[0].content.parts[0].text.strip().upper()
    image_type = "illustration" if "ILLUSTRATION" in result else "photo"
    
    # 插畫：跳過步驟2，body_extent 固定
    if image_type == "illustration":
        return {"image_type": image_type, "body_extent": "head_chest"}
    
    # 照片：執行步驟2，檢測身體範圍
    response_body = client.models.generate_content(
        model=API_CONFIG.model_text,
        contents=[
            types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
            BODY_EXTENT_PROMPT  # 檢測身體
        ],
        config=types.GenerateContentConfig(response_modalities=['TEXT'])
    )
    
    result_body = response_body.candidates[0].content.parts[0].text.strip().upper()
    
    body_extent = "full_body"
    if "HEAD_ONLY" in result_body:
        body_extent = "head_only"
    elif "HEAD_NECK" in result_body:
        body_extent = "head_neck"
    elif "HEAD_CHEST" in result_body:
        body_extent = "head_chest"
    
    return {"image_type": image_type, "body_extent": body_extent}


def fast_analysis(image: Image.Image) -> dict:
    """快速分析（假設為照片，head_chest）"""
    return {"image_type": "photo", "body_extent": "head_chest"}


# ============================================================
# 預處理組件
# ============================================================

def rembg_preprocess(image: Image.Image, context: dict) -> Image.Image:
    """rembg 去背 + 裁切（僅照片）"""
    if context.get("image_type") == "photo":
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        
        # 去背
        result = rembg_remove(image)
        
        # 裁切平整底部
        alpha = np.array(result.split()[-1])
        rows = np.any(alpha > 0, axis=1)
        cols = np.any(alpha > 0, axis=0)
        
        if np.any(rows) and np.any(cols):
            top = np.argmax(rows)
            bottom = len(rows) - np.argmax(rows[::-1])
            left = np.argmax(cols)
            right = len(cols) - np.argmax(cols[::-1])
            result = result.crop((left, top, right, bottom))
        
        return result
    else:
        # 插畫：只轉格式
        return image.convert("RGBA") if image.mode != "RGBA" else image


def no_preprocess(image: Image.Image, context: dict) -> Image.Image:
    """不預處理，只轉格式"""
    return image.convert("RGBA") if image.mode != "RGBA" else image


# ============================================================
# 風格生成組件
# ============================================================

def detailed_style_generate(image: Image.Image, context: dict) -> Image.Image:
    """詳細Prompt風格生成（原版2000字）"""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("請在 .env 檔案中設定 GEMINI_API_KEY")
    
    client = genai.Client(api_key=api_key)
    
    # 準備圖片（轉 RGB，白底）
    if image.mode == "RGBA":
        bg = Image.new("RGB", image.size, (255, 255, 255))
        bg.paste(image, mask=image.split()[3])
        image = bg
    elif image.mode != "RGB":
        image = image.convert("RGB")
    
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    
    # 生成Prompt
    body_extent = context.get("body_extent", "head_chest")
    prompt = get_style_prompt(body_extent)
    
    # AI生成（使用原版順序：Prompt 在前）
    response = client.models.generate_content(
        model=API_CONFIG.model_image,
        contents=[
            prompt,  # Prompt 在前（原版順序）
            types.Part.from_bytes(data=img_bytes, mime_type="image/png")
        ],
        config=types.GenerateContentConfig(response_modalities=['TEXT', 'IMAGE'])
    )
    
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            return Image.open(io.BytesIO(part.inline_data.data))
    
    raise ValueError("AI 未返回圖片")


# ============================================================
# 背景處理組件
# ============================================================

def transparent_background(image: Image.Image, context: dict) -> Image.Image:
    """白色轉透明"""
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    
    data = np.array(image)
    threshold = 240
    
    white_mask = (data[:, :, 0] > threshold) & (data[:, :, 1] > threshold) & (data[:, :, 2] > threshold)
    labeled, _ = ndimage.label(white_mask)
    
    edge_labels = set()
    edge_labels.update(labeled[0, :])
    edge_labels.update(labeled[-1, :])
    edge_labels.update(labeled[:, 0])
    edge_labels.update(labeled[:, -1])
    edge_labels.discard(0)
    
    person_mask = (data[:, :, 0] < 245) | (data[:, :, 1] < 245) | (data[:, :, 2] < 245)
    
    if np.any(person_mask):
        person_mask_expanded = ndimage.binary_dilation(person_mask, structure=np.ones((20, 20)))
    else:
        person_mask_expanded = np.zeros_like(person_mask)
    
    bg_mask = np.zeros_like(white_mask)
    for label in edge_labels:
        region_mask = (labeled == label)
        overlap = np.sum(region_mask & person_mask_expanded)
        total = np.sum(region_mask)
        
        if total > 0 and overlap / total < 0.3:
            bg_mask = bg_mask | region_mask
    
    data[bg_mask, 3] = 0
    return Image.fromarray(data, "RGBA")


def keep_white_background(image: Image.Image, context: dict) -> Image.Image:
    """保持白色背景"""
    return image


# ============================================================
# 後處理組件
# ============================================================

def normalize_1000(image: Image.Image, context: dict) -> Image.Image:
    """統一到 1000x1000（完全對齊原版邏輯）"""
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    
    target_size = (1000, 1000)
    alpha = np.array(image.split()[3])
    person_mask = alpha > 0
    
    if not np.any(person_mask):
        return image.resize(target_size, Image.Resampling.LANCZOS)
    
    # 找出人物區域
    rows, cols = np.where(person_mask)
    min_row, max_row = rows.min(), rows.max()
    min_col, max_col = cols.min(), cols.max()
    
    person_height = max_row - min_row
    person_width = max_col - min_col
    
    # 添加緩衝
    padding_h = max(10, int(person_height * 0.1))
    padding_w = max(10, int(person_width * 0.1))
    min_row = max(0, min_row - padding_h)
    max_row = min(image.height - 1, max_row + padding_h)
    min_col = max(0, min_col - padding_w)
    max_col = min(image.width - 1, max_col + padding_w)
    
    person_height = max_row - min_row
    person_width = max_col - min_col
    
    # 計算縮放
    target_person_height = int(target_size[1] * 0.70)
    target_person_width = int(target_size[0] * 0.85)
    
    scale = min(
        target_person_height / person_height if person_height > 0 else 1.0,
        target_person_width / person_width if person_width > 0 else 1.0
    )
    
    # 縮放和定位
    scaled = image.resize((int(image.width * scale), int(image.height * scale)), Image.Resampling.LANCZOS)
    result = Image.new("RGBA", target_size, (0, 0, 0, 0))
    
    # 計算位置
    scaled_alpha = np.array(scaled.split()[3])
    if np.any(scaled_alpha > 0):
        scaled_rows, scaled_cols = np.where(scaled_alpha > 0)
        scaled_min_row = scaled_rows.min()
        scaled_min_col = scaled_cols.min()
        scaled_max_col = scaled_cols.max()
        
        person_center = scaled_min_col + (scaled_max_col - scaled_min_col) / 2
        x_offset = int(target_size[0] / 2 - person_center)
        
        head_top_y = int(target_size[1] * 0.35)
        y_offset = head_top_y - scaled_min_row
        
        result.paste(scaled, (x_offset, y_offset), scaled)
    
    # 底部裁切（僅照片）
    if context.get("image_type") == "photo":
        data = np.array(result)
        alpha = data[:, :, 3]
        person_mask = alpha > 0
        
        if np.any(person_mask):
            rows, cols = np.where(person_mask)
            min_col, max_col = cols.min(), cols.max()
            center_col = (min_col + max_col) // 2
            center_width = (max_col - min_col) // 3
            
            center_region = (cols >= center_col - center_width) & (cols <= center_col + center_width)
            if np.any(center_region):
                body_bottom_row = rows[center_region].max()
                if body_bottom_row < data.shape[0] - 1:
                    data[body_bottom_row + 1:, :, 3] = 0
        
        result = Image.fromarray(data, "RGBA")
    
    return result


def keep_original_size(image: Image.Image, context: dict) -> Image.Image:
    """保持原始尺寸"""
    return image
