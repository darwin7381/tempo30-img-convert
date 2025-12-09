"""Pipeline 細粒度組件 - 每個組件對應一個具體步驟

將原來的粗粒度組件拆分為細粒度組件：
- 更詳細的步驟顯示
- 更靈活的組合
- 更容易追蹤進度
"""

from PIL import Image
import io
import logging
from google import genai
from google.genai import types
import numpy as np
from scipy import ndimage

from ..config import API_CONFIG
from ..prompts import get_style_prompt, IMAGE_TYPE_PROMPT, BODY_EXTENT_PROMPT, UNIVERSAL_INTELLIGENT_PROMPT
from ..utils import prepare_image_for_api

logger = logging.getLogger(__name__)


# ============================================================
# 分析組件（拆分為2個）
# ============================================================

def detect_image_type(image: Image.Image, context: dict) -> dict:
    """步驟1：檢測圖片類型（照片/插畫）"""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("請在 .env 檔案中設定 GEMINI_API_KEY")
    
    client = genai.Client(api_key=api_key)
    _, img_bytes = prepare_image_for_api(image)
    
    response = client.models.generate_content(
        model=API_CONFIG.model_text,
        contents=[
            types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
            IMAGE_TYPE_PROMPT
        ],
        config=types.GenerateContentConfig(response_modalities=['TEXT'])
    )
    
    result = response.candidates[0].content.parts[0].text.strip().upper()
    image_type = "illustration" if "ILLUSTRATION" in result else "photo"
    
    return {"image_type": image_type}


def detect_body_extent(image: Image.Image, context: dict) -> dict:
    """步驟2：檢測身體範圍（僅照片）"""
    # 如果是插畫，跳過此步驟
    if context.get("image_type") == "illustration":
        return {"body_extent": "head_chest"}
    
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("請在 .env 檔案中設定 GEMINI_API_KEY")
    
    client = genai.Client(api_key=api_key)
    _, img_bytes = prepare_image_for_api(image)
    
    response = client.models.generate_content(
        model=API_CONFIG.model_text,
        contents=[
            types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
            BODY_EXTENT_PROMPT
        ],
        config=types.GenerateContentConfig(response_modalities=['TEXT'])
    )
    
    result_body = response.candidates[0].content.parts[0].text.strip().upper()
    
    body_extent = "full_body"
    if "HEAD_ONLY" in result_body:
        body_extent = "head_only"
    elif "HEAD_NECK" in result_body:
        body_extent = "head_neck"
    elif "HEAD_CHEST" in result_body:
        body_extent = "head_chest"
    
    return {"body_extent": body_extent}


# ============================================================
# 預處理組件（拆分為2個）
# ============================================================

def rembg_remove_background(image: Image.Image, context: dict) -> Image.Image:
    """步驟3：rembg 去背（僅照片）"""
    if context.get("image_type") == "photo":
        # 延遲載入 rembg（避免在模組載入時就觸發模型下載）
        logger.info("載入 rembg 模組進行去背...")
        from rembg import remove as rembg_remove
        
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        result = rembg_remove(image)
        logger.info("✅ 去背完成")
        return result
    else:
        return image.convert("RGBA") if image.mode != "RGBA" else image


def crop_to_content(image: Image.Image, context: dict) -> Image.Image:
    """步驟4：裁切到內容區域"""
    if image.mode != "RGBA":
        return image
    
    alpha = np.array(image.split()[-1])
    rows = np.any(alpha > 0, axis=1)
    cols = np.any(alpha > 0, axis=0)
    
    if np.any(rows) and np.any(cols):
        top = np.argmax(rows)
        bottom = len(rows) - np.argmax(rows[::-1])
        left = np.argmax(cols)
        right = len(cols) - np.argmax(cols[::-1])
        return image.crop((left, top, right, bottom))
    
    return image


# ============================================================
# 風格生成組件（拆分為3個）
# ============================================================

def prepare_for_ai(image: Image.Image, context: dict) -> Image.Image:
    """步驟5：準備圖片給 AI（轉 RGB，白底）"""
    if image.mode == "RGBA":
        bg = Image.new("RGB", image.size, (255, 255, 255))
        bg.paste(image, mask=image.split()[3])
        return bg
    elif image.mode != "RGB":
        return image.convert("RGB")
    return image


def generate_body_instruction(image: Image.Image, context: dict) -> dict:
    """步驟5：生成 Body Instruction（查表）"""
    from ..prompts import BODY_INSTRUCTIONS
    
    body_extent = context.get("body_extent", "head_chest")
    instruction = BODY_INSTRUCTIONS.get(body_extent, BODY_INSTRUCTIONS["head_chest"])
    
    return {"body_instruction": instruction}


def build_full_prompt(image: Image.Image, context: dict) -> dict:
    """步驟6：構建完整 Prompt（組合 Body Instruction + Style）"""
    body_extent = context.get("body_extent", "head_chest")
    prompt = get_style_prompt(body_extent)
    return {"prompt": prompt}


def ai_generate_style(image: Image.Image, context: dict) -> Image.Image:
    """步驟7：AI 生成向量插畫（1K 正方形）"""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("請在 .env 檔案中設定 GEMINI_API_KEY")
    
    client = genai.Client(api_key=api_key)
    
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    
    prompt = context.get("prompt", get_style_prompt("head_chest"))
    
    response = client.models.generate_content(
        model=API_CONFIG.model_image,
        contents=[
            prompt,
            types.Part.from_bytes(data=img_bytes, mime_type="image/png")
        ],
        config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE'],
            image_config=types.ImageConfig(
                aspect_ratio="1:1",  # 正方形
                image_size="1K"      # 1024x1024
            )
        )
    )
    
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            return Image.open(io.BytesIO(part.inline_data.data))
    
    raise ValueError("AI 未返回圖片")


def ai_generate_universal(image: Image.Image, context: dict) -> Image.Image:
    """步驟7（萬能版）：AI 萬能智能生成（1K 正方形）"""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("請在 .env 檔案中設定 GEMINI_API_KEY")
    
    client = genai.Client(api_key=api_key)
    
    # 準備圖片
    if image.mode == "RGBA":
        bg = Image.new("RGB", image.size, (255, 255, 255))
        bg.paste(image, mask=image.split()[3])
        image = bg
    elif image.mode != "RGB":
        image = image.convert("RGB")
    
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    
    response = client.models.generate_content(
        model=API_CONFIG.model_image,
        contents=[
            UNIVERSAL_INTELLIGENT_PROMPT,
            types.Part.from_bytes(data=img_bytes, mime_type="image/png")
        ],
        config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE'],
            image_config=types.ImageConfig(
                aspect_ratio="1:1",  # 正方形
                image_size="1K"      # 1024x1024
            )
        )
    )
    
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            return Image.open(io.BytesIO(part.inline_data.data))
    
    raise ValueError("AI 未返回圖片")


# ============================================================
# 背景處理組件（拆分為2個）
# ============================================================

def detect_white_background(image: Image.Image, context: dict) -> dict:
    """步驟8：檢測白色背景區域"""
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
    
    return {"white_labels": edge_labels, "labeled": labeled, "data": data}


def make_white_transparent(image: Image.Image, context: dict) -> Image.Image:
    """步驟9：將白色轉為透明"""
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


def keep_background(image: Image.Image, context: dict) -> Image.Image:
    """保持原背景"""
    return image


# ============================================================
# 後處理組件（拆分為3個）
# ============================================================

def calculate_normalization(image: Image.Image, context: dict) -> dict:
    """步驟10：計算標準化參數"""
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    
    target_size = (1000, 1000)
    alpha = np.array(image.split()[3])
    person_mask = alpha > 0
    
    if not np.any(person_mask):
        return {
            "scale": 1.0,
            "x_offset": 0,
            "y_offset": 0,
            "target_size": target_size
        }
    
    rows, cols = np.where(person_mask)
    min_row, max_row = rows.min(), rows.max()
    min_col, max_col = cols.min(), cols.max()
    
    person_height = max_row - min_row
    person_width = max_col - min_col
    
    padding_h = max(10, int(person_height * 0.1))
    padding_w = max(10, int(person_width * 0.1))
    min_row = max(0, min_row - padding_h)
    max_row = min(image.height - 1, max_row + padding_h)
    min_col = max(0, min_col - padding_w)
    max_col = min(image.width - 1, max_col + padding_w)
    
    person_height = max_row - min_row
    person_width = max_col - min_col
    
    target_person_height = int(target_size[1] * 0.70)
    target_person_width = int(target_size[0] * 0.85)
    
    scale = min(
        target_person_height / person_height if person_height > 0 else 1.0,
        target_person_width / person_width if person_width > 0 else 1.0
    )
    
    return {
        "scale": scale,
        "target_size": target_size,
        "needs_positioning": True
    }


def resize_and_position(image: Image.Image, context: dict) -> Image.Image:
    """步驟11：縮放和定位到 1000x1000"""
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
    
    return result


def crop_bottom_edge(image: Image.Image, context: dict) -> Image.Image:
    """步驟12：裁切底部邊緣（僅照片）"""
    if context.get("image_type") != "photo":
        return image
    
    if image.mode != "RGBA":
        return image
    
    data = np.array(image)
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
    
    return Image.fromarray(data, "RGBA")


def no_postprocess(image: Image.Image, context: dict) -> Image.Image:
    """不做後處理"""
    return image


# ============================================================
# 工具組件
# ============================================================

def convert_to_rgba(image: Image.Image, context: dict) -> Image.Image:
    """轉換為 RGBA 格式"""
    return image.convert("RGBA") if image.mode != "RGBA" else image

