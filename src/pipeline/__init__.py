"""
Pipeline 架構 - 函數式組件系統

設計理念：
- 每個處理步驟是一個可替換的組件（函數）
- 組件可以自由組合形成不同風格
- 解決複雜度問題：邏輯分散到各組件

組件類型：
1. 分析組件（Analysis）- 分析圖片類型和身體範圍
2. 預處理組件（Preprocess）- 去背、裁切等
3. 風格組件（Style）- AI 生成不同風格
4. 背景組件（Background）- 透明、白色、藍色圓等
5. 後處理組件（Postprocess）- 統一尺寸、描邊等
"""

from .engine import run_pipeline, build_pipeline_from_names
from .style_configs import PRESET_STYLES, STYLE_OPTIONS

__all__ = [
    'run_pipeline',
    'build_pipeline_from_names',
    'PRESET_STYLES',
    'STYLE_OPTIONS'
]

