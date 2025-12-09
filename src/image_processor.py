"""圖片處理模組 - 去背與裁切"""

from PIL import Image
import numpy as np
from rembg import remove

from .gemini_client import ImageType


class ImageProcessor:
    """圖片處理器，負責去背和裁切"""
    
    @staticmethod
    def remove_background(image: Image.Image) -> Image.Image:
        """
        移除圖片背景
        
        Args:
            image: PIL Image 物件
            
        Returns:
            去背後的 RGBA 圖片
        """
        # 確保圖片為 RGBA 模式
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        
        # 使用 rembg 去背
        result = remove(image)
        return result
    
    @staticmethod
    def crop_to_flat_bottom(image: Image.Image) -> Image.Image:
        """
        裁切圖片，使人物底部保持平整的水平邊緣
        找出非透明區域的邊界並進行裁切
        
        Args:
            image: PIL Image 物件 (應為 RGBA 模式)
            
        Returns:
            裁切後的圖片
        """
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        
        # 獲取 alpha 通道
        alpha = np.array(image.split()[-1])
        
        # 找出非透明像素的邊界
        rows = np.any(alpha > 0, axis=1)
        cols = np.any(alpha > 0, axis=0)
        
        if not np.any(rows) or not np.any(cols):
            return image
        
        # 取得邊界
        top = np.argmax(rows)
        bottom = len(rows) - np.argmax(rows[::-1])
        left = np.argmax(cols)
        right = len(cols) - np.argmax(cols[::-1])
        
        # 裁切圖片
        cropped = image.crop((left, top, right, bottom))
        return cropped
    
    def process_image(self, image: Image.Image, image_type: ImageType) -> Image.Image:
        """
        根據圖片類型處理圖片
        
        Args:
            image: PIL Image 物件
            image_type: 圖片類型
            
        Returns:
            處理後的圖片
        """
        if image_type == ImageType.REAL_PHOTO:
            # 真人照片：去背後裁切
            processed = self.remove_background(image)
            processed = self.crop_to_flat_bottom(processed)
        else:
            # 像素插畫：保留全圖，但確保有 alpha 通道
            if image.mode != "RGBA":
                processed = image.convert("RGBA")
            else:
                processed = image.copy()
        
        return processed

