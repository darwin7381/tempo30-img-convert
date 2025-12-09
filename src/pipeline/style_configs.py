"""預設風格配置"""

from . import components

# ============================================================
# 預設風格
# ============================================================

PRESET_STYLES = {
    "i4_detailed": {
        "name": "I4 詳細版（原版高品質）",
        "description": "完整10步驟，2000字詳細Prompt，選擇性橘色高光",
        "analysis": components.gemini_25_analysis_photos_only,  # 修正：插畫不檢測身體
        "preprocess": components.rembg_preprocess,
        "style": components.detailed_style_generate,
        "background": components.transparent_background,
        "postprocess": components.normalize_1000
    },
    
    "i4_simplified": {
        "name": "I4 簡化版（快速）",
        "description": "最小步驟，600字簡化Prompt，快速處理",
        "analysis": components.fast_analysis,
        "preprocess": components.no_preprocess,
        "style": components.detailed_style_generate,  # 暫時用詳細版
        "background": components.keep_white_background,
        "postprocess": components.keep_original_size
    }
}


# 用於前端顯示的風格列表
STYLE_OPTIONS = [
    {
        "id": "i4_detailed",
        "name": "I4 詳細版",
        "description": "原版高品質（完整處理）",
        "recommended": True
    },
    {
        "id": "i4_simplified",
        "name": "I4 簡化版",
        "description": "快速版（最小處理）",
        "recommended": False
    }
]

