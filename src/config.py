"""設定檔 - 集中管理所有配置"""

import os
from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class StyleConfig:
    """風格轉換設定"""
    target_size: Tuple[int, int] = (1000, 1000)
    head_ratio: float = 0.35
    white_threshold: int = 240
    outline_width: int = 8
    person_height_ratio: float = 0.70
    person_width_ratio: float = 0.85
    side_margin_ratio: float = 0.05


@dataclass
class APIConfig:
    """API 設定"""
    # 根據 Google Cloud 文檔（2025-12-06更新）
    # 圖片理解文檔：https://ai.google.dev/gemini-api/docs/image-understanding
    # 圖片生成文檔：https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-pro-image
    model_image: str = "gemini-3-pro-image-preview"  # 圖片生成模型（發布：2025-11-20，最新）
    model_text: str = "gemini-2.5-flash"  # 文本分析/圖片理解模型（2025年最新，增強的object detection和segmentation）
    max_retries: int = 3
    base_retry_delay: int = 60
    api_gateway_url: str = "https://api-gateway.cryptoxlab.workers.dev/api/openrouter/v1/chat/completions"
    use_gateway: bool = False  # 是否使用 API 網關（設為 False 使用 Gemini SDK）
    
    @property
    def api_key(self) -> str:
        """取得 API Key（用於自定義網關認證）"""
        if self.use_gateway:
            # 嘗試多種可能的環境變量名稱（用於自定義網關的認證）
            key = os.getenv("X_API_KEY") or os.getenv("X_API_Key") or os.getenv("X-API-Key")
            if not key:
                raise ValueError("請在 .env 檔案中設定 X_API_KEY 或 X_API_Key（用於自定義網關認證）")
            return key
        else:
            key = os.getenv("GEMINI_API_KEY")
            if not key:
                raise ValueError("請在 .env 檔案中設定 GEMINI_API_KEY")
            return key
    
    @property
    def openrouter_api_key(self) -> str:
        """取得 OpenRouter API Key（傳遞給網關，可選）"""
        # OpenRouter API key 是可選的，如果網關已經配置了就不需要
        return os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_KEY") or ""


# 全域設定實例
STYLE_CONFIG = StyleConfig()
API_CONFIG = APIConfig()

