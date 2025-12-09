"""風格轉換模組 - 向量插畫風格（半寫實企業頭像、賽璐璞著色、隨機高光、透明背景）

優化版本:
- 合併圖片類型與身體範圍檢測為單一 API 呼叫（減少 33% API 配額消耗）
- 加入 API 配額錯誤自動重試機制
- 使用集中式設定管理
"""

import os
import io
import math
import base64
import json
import re
import requests
from PIL import Image, ImageDraw, ImageFilter
from google import genai
from google.genai import types
from dotenv import load_dotenv
import numpy as np
from scipy import ndimage

from .config import STYLE_CONFIG, API_CONFIG
from .utils import retry_on_quota_error, prepare_image_for_api
from .prompts import get_style_prompt, ANALYZE_PROMPT


class StyleConverter:
    """風格轉換器 - 將照片轉為向量插畫風格（半寫實企業頭像、賽璐璜著色、隨機高光、透明背景，胸部以上裁剪，統一尺寸）"""
    
    def __init__(self):
        """初始化 API 客戶端"""
        load_dotenv()
        if API_CONFIG.use_gateway:
            # 使用 API 網關（OpenRouter）
            self.api_key = API_CONFIG.api_key
            self.api_url = API_CONFIG.api_gateway_url  # 已經包含完整路徑
            self.client = None
        else:
            # 直接使用 Gemini SDK
            self.client = genai.Client(api_key=API_CONFIG.api_key)
            self.api_key = None
            self.api_url = None
    
    def _call_openrouter_api(self, prompt: str, image: Image.Image = None, response_format: str = "text") -> dict:
        """
        通過 OpenRouter API 網關調用模型
        
        Args:
            prompt: 文字提示
            image: 可選的圖片
            response_format: "text" 或 "image"
            
        Returns:
            API 回應的字典
        """
        _, img_bytes = prepare_image_for_api(image) if image else (None, None)
        img_base64 = base64.b64encode(img_bytes).decode('utf-8') if img_bytes else None
        
        # 構建消息內容
        content = [{"type": "text", "text": prompt}]
        if img_base64:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_base64}"
                }
            })
        
        payload = {
            "model": API_CONFIG.model_text if response_format == "text" else API_CONFIG.model_image,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ]
        }
        
        headers = {
            "X-API-Key": self.api_key,  # 自定義網關的認證 key
            "Content-Type": "application/json",
            "HTTP-Referer": "https://blocktempo.ai",
            "X-Title": "Tempo Image Converter"
        }
        
        # 如果配置了 OpenRouter API key，也添加到 header 中
        openrouter_key = API_CONFIG.openrouter_api_key
        if openrouter_key:
            headers["Authorization"] = f"Bearer {openrouter_key}"
        
        response = requests.post(self.api_url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        
        # 調試：打印響應狀態和內容
        try:
            return response.json()
        except json.JSONDecodeError as e:
            print(f"⚠️ API 回應不是有效的 JSON")
            print(f"⚠️ 狀態碼: {response.status_code}")
            print(f"⚠️ 回應內容 (前500字符): {response.text[:500]}")
            print(f"⚠️ 請求 URL: {self.api_url}")
            print(f"⚠️ 請求 Headers: {headers}")
            raise ValueError(f"API 回應格式錯誤: {e}")
    
    @retry_on_quota_error(max_retries=API_CONFIG.max_retries, base_delay=API_CONFIG.base_retry_delay)
    def analyze_image(self, image: Image.Image) -> dict:
        """
        合併檢測：同時分析圖片類型和身體範圍（單一 API 呼叫）
        
        此方法將原本的 detect_image_type() 和 detect_body_extent() 合併為一次 API 呼叫，
        減少 33% 的 API 配額消耗。
        
        Args:
            image: PIL Image 物件
            
        Returns:
            dict: {
                "image_type": "photo" 或 "illustration",
                "body_extent": "head_only", "head_neck", "head_chest", 或 "full_body"
            }
        """
        prompt = ANALYZE_PROMPT
        
        try:
            if API_CONFIG.use_gateway:
                # 使用 OpenRouter API 網關
                response = self._call_openrouter_api(prompt, image, response_format="text")
                result = response["choices"][0]["message"]["content"].strip().upper()
            else:
                # 使用 Gemini SDK（Prompt 順序：圖片在前，符合最佳實踐）
                _, img_bytes = prepare_image_for_api(image)
                api_response = self.client.models.generate_content(
                    model=API_CONFIG.model_text,
                    contents=[
                        types.Part.from_bytes(
                            data=img_bytes,
                            mime_type="image/png"
                        ),
                        prompt  # Prompt 在圖片後面
                    ],
                    config=types.GenerateContentConfig(
                        response_modalities=['TEXT']
                    )
                )
                result = api_response.candidates[0].content.parts[0].text.strip().upper()
            
            # 解析回應
            image_type = "photo"
            body_extent = "full_body"
            
            if "ILLUSTRATION" in result:
                image_type = "illustration"
            
            if "HEAD_ONLY" in result:
                body_extent = "head_only"
            elif "HEAD_NECK" in result:
                body_extent = "head_neck"
            elif "HEAD_CHEST" in result:
                body_extent = "head_chest"
            else:
                body_extent = "full_body"
            
            return {"image_type": image_type, "body_extent": body_extent}
            
        except Exception as e:
            print(f"⚠️ 圖片分析失敗，使用預設值: {e}")
            return {"image_type": "photo", "body_extent": "full_body"}
    
    def detect_image_type(self, image: Image.Image) -> str:
        """
        檢測圖片類型（保留向後相容性，內部使用 analyze_image）
        """
        return self.analyze_image(image)["image_type"]
    
    def detect_body_extent(self, image: Image.Image) -> str:
        """
        檢測身體部位範圍（保留向後相容性，內部使用 analyze_image）
        """
        return self.analyze_image(image)["body_extent"]
    
    def convert_to_grayscale(self, image: Image.Image) -> Image.Image:
        """
        將圖片轉換為灰階（用於插畫/向量圖）
        
        Args:
            image: PIL Image 物件
            
        Returns:
            灰階圖片 (RGBA 模式)
        """
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        
        # 分離通道
        r, g, b, a = image.split()
        
        # 轉換為灰階 (使用標準亮度公式)
        gray = Image.merge("RGB", (r, g, b)).convert("L")
        
        # 重新組合為 RGBA
        result = Image.merge("RGBA", (gray, gray, gray, a))
        return result
    
    def convert_to_cartoon_illustration(self, image: Image.Image, body_extent: str = "head_chest") -> Image.Image:
        """
        將照片轉換為向量插畫風格
        
        Args:
            image: PIL Image 物件
            body_extent: 身體部位範圍 ("head_only", "head_neck", "head_chest", "full_body")
            
        Returns:
            轉換後的插畫圖片
        """
        # 使用模組化的 Prompt 模板（減少 66% Token 消耗）
        prompt = get_style_prompt(body_extent)
        
        if API_CONFIG.use_gateway:
            # 使用 OpenRouter API 網關
            # OpenRouter 使用 OpenAI 兼容格式，但圖片生成可能需要特殊處理
            try:
                response = self._call_openrouter_api(prompt, image, response_format="image")
                
                # 嘗試從回應中提取圖片
                # OpenRouter 的圖片回應可能在不同位置
                if "choices" in response and len(response["choices"]) > 0:
                    choice = response["choices"][0]
                    
                    # 檢查 message.content 是否包含圖片
                    if "message" in choice:
                        content = choice["message"].get("content", "")
                        if isinstance(content, str):
                            # 檢查是否有 base64 圖片
                            base64_match = re.search(r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)', content)
                            if base64_match:
                                image_data = base64.b64decode(base64_match.group(1))
                                result_image = Image.open(io.BytesIO(image_data))
                                return result_image
                        elif isinstance(content, list):
                            # 如果 content 是列表，查找圖片項
                            for item in content:
                                if item.get("type") == "image_url":
                                    url = item.get("image_url", {}).get("url", "")
                                    if url.startswith("data:image"):
                                        base64_match = re.search(r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)', url)
                                        if base64_match:
                                            image_data = base64.b64decode(base64_match.group(1))
                                            result_image = Image.open(io.BytesIO(image_data))
                                            return result_image
                    
                    # 檢查是否有直接的圖片數據
                    if "image" in choice or "image_data" in choice:
                        image_data = choice.get("image") or choice.get("image_data")
                        if isinstance(image_data, str):
                            # 如果是 base64 字符串
                            if not image_data.startswith("data:"):
                                image_data = f"data:image/png;base64,{image_data}"
                            base64_match = re.search(r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)', image_data)
                            if base64_match:
                                image_bytes = base64.b64decode(base64_match.group(1))
                                result_image = Image.open(io.BytesIO(image_bytes))
                                return result_image
                
                # 如果沒有找到圖片，打印回應以便調試
                print(f"⚠️ OpenRouter API 回應格式: {json.dumps(response, indent=2)[:500]}")
                raise ValueError("OpenRouter API 回應中未找到圖片數據")
            except Exception as e:
                print(f"⚠️ OpenRouter API 調用失敗: {e}")
                if 'response' in locals():
                    print(f"⚠️ 回應內容: {json.dumps(response, indent=2)[:1000]}")
                raise
        else:
            # 使用 Gemini SDK
            _, img_bytes = prepare_image_for_api(image)
            api_response = self.client.models.generate_content(
                model=API_CONFIG.model_image,
                contents=[
                    prompt,
                    types.Part.from_bytes(
                        data=img_bytes,
                        mime_type="image/png"
                    )
                ],
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE']
                )
            )
            
            # 從回應中提取圖片
            for part in api_response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image_data = part.inline_data.data
                    result_image = Image.open(io.BytesIO(image_data))
                    return result_image
            
            raise ValueError("Gemini API 未返回圖片")
    
    def make_white_transparent(self, image: Image.Image, threshold: int = 240) -> Image.Image:
        """
        將白色背景轉為透明（處理邊緣連通的白色區域，並保護人物內部）
        """
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        
        data = np.array(image)
        height, width = data.shape[0], data.shape[1]
        
        # 找出接近純白色的像素（降低閾值以捕捉更多白色）
        white_mask = (data[:, :, 0] > threshold) & \
                     (data[:, :, 1] > threshold) & \
                     (data[:, :, 2] > threshold)
        
        # 使用連通區域標記
        labeled, num_features = ndimage.label(white_mask)
        
        # 找出與邊緣接觸的標籤
        edge_labels = set()
        edge_labels.update(labeled[0, :])
        edge_labels.update(labeled[-1, :])
        edge_labels.update(labeled[:, 0])
        edge_labels.update(labeled[:, -1])
        edge_labels.discard(0)
        
        # 找出非白色區域（人物區域），提高閾值保護亮部衣物
        person_mask = (data[:, :, 0] < 245) | (data[:, :, 1] < 245) | (data[:, :, 2] < 245)
        
        # 對人物遮罩進行膨脹，創建保護區域
        if np.any(person_mask):
            person_mask_expanded = ndimage.binary_dilation(person_mask, structure=np.ones((20, 20)))
        else:
            person_mask_expanded = np.zeros((height, width), dtype=bool)
        
        # 處理每個與邊緣相連的白色區域
        bg_mask = np.zeros((height, width), dtype=bool)
        for label in edge_labels:
            region_mask = (labeled == label)
            
            # 檢查這個區域是否主要在保護區域外
            overlap = np.sum(region_mask & person_mask_expanded)
            total = np.sum(region_mask)
            
            # 如果重疊小於30%，視為背景
            if total > 0 and overlap / total < 0.3:
                bg_mask = bg_mask | region_mask
        
        # 將背景設為透明
        data[bg_mask, 3] = 0
        
        return Image.fromarray(data, "RGBA")
    
    def add_white_outline(self, image: Image.Image, outline_width: int = 8) -> Image.Image:
        """
        為圖片添加白色粗線描邊
        
        Args:
            image: 輸入圖片（RGBA 模式）
            outline_width: 描邊寬度（像素）
            
        Returns:
            添加描邊後的圖片
        """
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        
        # 獲取 alpha 通道
        alpha = image.split()[3]
        
        # 創建一個更大的畫布來容納描邊
        width, height = image.size
        new_width = width + outline_width * 2
        new_height = height + outline_width * 2
        
        # 創建新圖片（透明背景）
        result = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))
        
        # 將原圖貼到中心位置
        result.paste(image, (outline_width, outline_width), image)
        
        # 獲取結果的 alpha 通道
        result_alpha = result.split()[3]
        
        # 對 alpha 通道進行膨脹來創建描邊
        alpha_array = np.array(result_alpha)
        
        # 使用多次膨脹來創建粗線描邊
        for _ in range(outline_width):
            alpha_array = ndimage.binary_dilation(alpha_array, structure=np.ones((3, 3)))
        
        # 創建描邊遮罩（膨脹後的區域減去原始區域）
        original_alpha = np.array(result.split()[3])
        outline_mask = alpha_array & (~original_alpha.astype(bool))
        
        # 創建白色描邊
        result_array = np.array(result)
        result_array[outline_mask, 0] = 255  # R
        result_array[outline_mask, 1] = 255  # G
        result_array[outline_mask, 2] = 255  # B
        result_array[outline_mask, 3] = 255  # A
        
        return Image.fromarray(result_array, "RGBA")
    
    def crop_horizontal_bottom(self, image: Image.Image) -> Image.Image:
        """
        將圖片底部裁切成水平（在最終畫布上檢測人物底部，然後水平裁切）
        
        Args:
            image: 輸入圖片（RGBA 模式，應該是已經統一尺寸的畫布）
            
        Returns:
            底部水平裁切後的圖片
        """
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        
        data = np.array(image)
        height, width = data.shape[0], data.shape[1]
        
        # 獲取非透明區域
        alpha = data[:, :, 3]
        person_mask = alpha > 0
        
        if not np.any(person_mask):
            return image
        
        # 找出人物區域
        rows, cols = np.where(person_mask)
        if len(rows) == 0:
            return image
        
        # 找出人物寬度的中心區域（身體部分，不包括側邊的手部）
        min_col = cols.min()
        max_col = cols.max()
        center_col = (min_col + max_col) // 2
        center_width = (max_col - min_col) // 3  # 中心 1/3 區域
        
        # 在中心區域找出最低點（身體底部）
        center_region = (cols >= center_col - center_width) & (cols <= center_col + center_width)
        if np.any(center_region):
            body_bottom_row = rows[center_region].max()
        else:
            body_bottom_row = rows.max()
        
        # 將身體底部以下的所有內容設為透明（水平裁切）
        # 確保底部是水平的
        if body_bottom_row < height - 1:
            data[body_bottom_row + 1:, :, 3] = 0
        
        return Image.fromarray(data, "RGBA")
    def normalize_size_and_position(
        self,
        image: Image.Image,
        target_size: tuple[int, int] = (1000, 1000),
        head_ratio: float = 0.35
    ) -> Image.Image:
        """
        統一尺寸和位置，增加同質性（保留完整人物，不裁切任何部分）
        
        Args:
            image: 輸入圖片（RGBA 模式）
            target_size: 目標尺寸 (width, height)
            head_ratio: 頭部在畫面中的比例（從頂部開始）
            
        Returns:
            統一尺寸和位置後的圖片
        """
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        
        width, height = image.size
        target_width, target_height = target_size
        
        # 獲取非透明區域
        alpha = np.array(image.split()[3])
        person_mask = alpha > 0
        
        if not np.any(person_mask):
            # 如果沒有找到人物，直接縮放
            return image.resize(target_size, Image.Resampling.LANCZOS)
        
        # 找出人物區域的邊界
        rows, cols = np.where(person_mask)
        min_row, max_row = rows.min(), rows.max()
        min_col, max_col = cols.min(), cols.max()
        
        person_height = max_row - min_row
        person_width = max_col - min_col
        
        # 為了避免被裁切，對邊界加上 10% 的緩衝（增加緩衝）
        padding_h = max(10, int(person_height * 0.1))
        padding_w = max(10, int(person_width * 0.1))
        min_row = max(0, min_row - padding_h)
        max_row = min(height - 1, max_row + padding_h)
        min_col = max(0, min_col - padding_w)
        max_col = min(width - 1, max_col + padding_w)
        person_height = max_row - min_row
        person_width = max_col - min_col
        
        # 計算縮放比例（確保人物大小一致，不同照片的人物比例相同）
        # 固定人物高度為目標高度的 70%（確保一致性）
        # 固定人物寬度為目標寬度的 85%（確保一致性）
        target_person_height = int(target_height * 0.70)
        target_person_width = int(target_width * 0.85)
        
        # 計算基於高度和寬度的縮放比例
        scale_height = target_person_height / person_height if person_height > 0 else 1.0
        scale_width = target_person_width / person_width if person_width > 0 else 1.0
        
        # 使用較小的縮放比例，確保完整保留人物（包括手部和兩側）
        # 這樣可以確保人物大小一致，不會因為原始圖片大小不同而變化
        scale = min(scale_height, scale_width)
        
        # 計算需要的邊距（左右各 5%）
        side_margin = int(target_width * 0.05)
        
        # 縮放圖片
        new_width = int(width * scale)
        new_height = int(height * scale)
        scaled_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 重新計算人物位置（縮放後）
        scaled_alpha = np.array(scaled_image.split()[3])
        scaled_person_mask = scaled_alpha > 0
        if np.any(scaled_person_mask):
            scaled_rows, scaled_cols = np.where(scaled_person_mask)
            scaled_min_row = scaled_rows.min()
            scaled_max_row = scaled_rows.max()
            scaled_min_col = scaled_cols.min()
            scaled_max_col = scaled_cols.max()
            
            scaled_person_height = scaled_max_row - scaled_min_row
            scaled_person_width = scaled_max_col - scaled_min_col
        else:
            scaled_person_height = new_height
            scaled_person_width = new_width
            scaled_min_row = 0
            scaled_min_col = 0
            scaled_max_col = new_width
        
        # 創建目標尺寸的畫布
        result = Image.new("RGBA", target_size, (0, 0, 0, 0))
        
        # 計算位置：確保人物完整顯示，兩側都有邊距
        # 水平：讓人物在畫布中居中，確保最左和最右都有邊距
        # 計算人物在縮放後圖片中的實際位置
        person_left_in_scaled = scaled_min_col
        person_right_in_scaled = scaled_max_col
        person_width_in_scaled = person_right_in_scaled - person_left_in_scaled
        person_center_in_scaled = person_left_in_scaled + person_width_in_scaled / 2
        
        # 計算畫布的中心位置
        target_center_x = target_width / 2
        
        # 計算 x_offset：讓人物的中心對齊到畫布中心
        x_offset = int(target_center_x - person_center_in_scaled)
        
        # 確保人物完整顯示（檢查邊界）
        # 如果人物太寬，調整位置以確保不超出邊界
        if x_offset + person_left_in_scaled < side_margin:
            # 人物左邊超出，調整到左邊距
            x_offset = side_margin - person_left_in_scaled
        if x_offset + person_right_in_scaled > target_width - side_margin:
            # 人物右邊超出，調整到右邊距
            x_offset = (target_width - side_margin) - person_right_in_scaled
        
        # 垂直：頭部位置固定（根據 head_ratio）
        head_top_y = int(target_height * head_ratio)
        y_offset = head_top_y - scaled_min_row
        
        # 確保垂直方向不超出
        if y_offset < 0:
            y_offset = 0
        if y_offset + new_height > target_height:
            y_offset = target_height - new_height
        
        # 貼上圖片（完整保留，不裁切）
        result.paste(scaled_image, (x_offset, y_offset), scaled_image)
        
        return result
    
    def apply_style(
        self, 
        image: Image.Image,
            transparent_bg: bool = True,  # 使用透明背景
            add_outline: bool = False,  # 不使用白色描邊
        outline_width: int = 8,
        output_size: tuple[int, int] = None,
        normalize_size: bool = True,
        target_size: tuple[int, int] = (1000, 1000)
    ) -> Image.Image:
        """
        套用風格轉換（向量插畫風格，半寫實企業頭像、賽璐璐著色、隨機高光、透明背景，胸部以上裁剪，統一尺寸）
        
        Args:
            image: 輸入圖片
            transparent_bg: 是否使用透明背景（預設為 True，透明背景）
            add_outline: 是否添加白色粗線描邊（預設為 False，不使用描邊）
            outline_width: 描邊寬度（像素）
            output_size: 輸出尺寸 (width, height)，None 則使用 target_size
            normalize_size: 是否統一尺寸和位置（增加同質性）
            target_size: 目標統一尺寸 (width, height)
            
        Returns:
            轉換後的圖片
            
        Note:
            - 向量插畫風格，半寫實企業頭像
            - 賽璐璐著色（cel-shaded），硬陰影
            - 隨機高光效果（橘色/金色邊緣光，隨機角度）
            - 透明背景
            - 身體生成機制：如果只有脖子，生成到胸部；如果全身，只生成到胸部
        """
        # 使用合併的 API 呼叫同時檢測圖片類型和身體範圍（節省 33% API 配額）
        analysis = self.analyze_image(image)
        image_type = analysis["image_type"]
        body_extent = analysis["body_extent"]
        
        print(f"📊 圖片分析結果: 類型={image_type}, 身體範圍={body_extent}")
        
        if image_type == "illustration":
            # 如果是插畫/向量圖，也進行 AI 生成轉換（所有圖片都轉換，包括選擇性橘色高光）
            result = self.convert_to_cartoon_illustration(image, body_extent="head_chest")
            
            # 處理透明背景（插畫/向量圖也需要處理）
            if transparent_bg:
                result = self.make_white_transparent(result)
        else:
            # 如果是真人照片，根據身體部位範圍進行處理
            # 轉換為向量插畫風格（AI 會根據 body_extent 自動處理身體生成和裁剪到胸部以上，包括選擇性橘色高光）
            result = self.convert_to_cartoon_illustration(image, body_extent=body_extent)
            
            # 處理透明背景
            if transparent_bg:
                result = self.make_white_transparent(result)
        
        # 統一尺寸和位置（增加同質性）
        if normalize_size:
            result = self.normalize_size_and_position(result, target_size=target_size)
            # 使用統一的輸出尺寸
            if output_size is None:
                output_size = target_size
        
        # 不添加白色描邊
        # 對於真人照片，進行水平底部裁切
        if image_type == "photo" and normalize_size:
            result = self.crop_horizontal_bottom(result)
        
        return result

