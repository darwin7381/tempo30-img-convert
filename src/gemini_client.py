"""Gemini API 客戶端 - 用於判斷圖片類型"""

import os
from enum import Enum
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv


class ImageType(Enum):
    """圖片類型枚舉"""
    REAL_PHOTO = "real_photo"  # 真人照片
    PIXEL_ART = "pixel_art"    # 像素插畫


class GeminiClient:
    """Gemini API 客戶端，用於分析圖片類型"""
    
    def __init__(self):
        """初始化 Gemini 客戶端"""
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("請在 .env 檔案中設定 GEMINI_API_KEY")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
    
    def analyze_image_type(self, image: Image.Image) -> ImageType:
        """
        分析圖片是真人照片還是像素插畫
        
        Args:
            image: PIL Image 物件
            
        Returns:
            ImageType: 圖片類型
        """
        prompt = """
        請分析這張圖片的類型，只回答以下其中一個選項：
        
        1. REAL_PHOTO - 如果這是一張真實的人物照片（攝影照片、寫實風格的數位繪畫）
        2. PIXEL_ART - 如果這是像素風格的插畫、8-bit風格、復古遊戲風格的圖像
        
        只回答 REAL_PHOTO 或 PIXEL_ART，不要有其他文字。
        """
        
        # Prompt 順序：圖片在前（符合 Gemini 最佳實踐）
        response = self.model.generate_content([image, prompt])
        result = response.text.strip().upper()
        
        if "PIXEL" in result or "ART" in result:
            return ImageType.PIXEL_ART
        else:
            return ImageType.REAL_PHOTO
    
    def analyze_image_from_path(self, image_path: str) -> ImageType:
        """
        從檔案路徑分析圖片類型
        
        Args:
            image_path: 圖片檔案路徑
            
        Returns:
            ImageType: 圖片類型
        """
        image = Image.open(image_path)
        return self.analyze_image_type(image)

