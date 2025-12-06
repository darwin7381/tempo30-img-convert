"""工具函數 - 共用的輔助函數"""

import io
import time
from functools import wraps
from typing import Callable, TypeVar, Any
from PIL import Image

T = TypeVar('T')


def retry_on_quota_error(max_retries: int = 3, base_delay: int = 60) -> Callable:
    """
    API 配額錯誤自動重試裝飾器
    
    Args:
        max_retries: 最大重試次數
        base_delay: 基礎等待秒數（使用指數退避）
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        wait_time = base_delay * (2 ** attempt)
                        print(f"⏳ API 配額限制 (嘗試 {attempt + 1}/{max_retries})，等待 {wait_time} 秒後重試...")
                        time.sleep(wait_time)
                        last_exception = e
                    else:
                        raise
            raise Exception(f"API 呼叫失敗，已達最大重試次數 ({max_retries}): {last_exception}")
        return wrapper
    return decorator


def prepare_image_for_api(image: Image.Image) -> tuple[Image.Image, bytes]:
    """
    準備圖片供 API 使用
    
    Args:
        image: PIL Image 物件
        
    Returns:
        (RGB 模式的圖片, PNG 格式的 bytes)
    """
    # 轉換為 RGB 模式
    if image.mode == "RGBA":
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        rgb_image = background
    elif image.mode != "RGB":
        rgb_image = image.convert("RGB")
    else:
        rgb_image = image.copy()
    
    # 轉換為 bytes
    img_byte_arr = io.BytesIO()
    rgb_image.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    
    return rgb_image, img_bytes
