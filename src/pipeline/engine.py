"""Pipeline 執行引擎"""

from PIL import Image
from typing import Dict, Callable, Any


def run_pipeline(image: Image.Image, config: Dict[str, Callable]) -> Image.Image:
    """
    執行處理 Pipeline
    
    Args:
        image: 輸入圖片
        config: 組件配置 {
            "analysis": analysis_func,
            "preprocess": preprocess_func,
            "style": style_func,
            "background": background_func,
            "postprocess": postprocess_func
        }
    
    Returns:
        處理後的圖片
    """
    context = {}
    
    # 步驟1：分析（如果有）
    if "analysis" in config and config["analysis"] is not None:
        analysis_result = config["analysis"](image)
        context.update(analysis_result)
    
    # 步驟2：預處理（如果有）
    if "preprocess" in config and config["preprocess"] is not None:
        image = config["preprocess"](image, context)
    
    # 步驟3：風格生成（如果有）
    if "style" in config and config["style"] is not None:
        image = config["style"](image, context)
    
    # 步驟4：背景處理（如果有）
    if "background" in config and config["background"] is not None:
        image = config["background"](image, context)
    
    # 步驟5：後處理（如果有）
    if "postprocess" in config and config["postprocess"] is not None:
        image = config["postprocess"](image, context)
    
    return image


# 預設組件註冊表
from . import components

COMPONENT_REGISTRY = {
    # 分析
    "analysis": {
        "gemini_2.5": components.gemini_25_analysis_photos_only,  # 修正名稱
        "fast": components.fast_analysis,
    },
    
    # 預處理
    "preprocess": {
        "rembg": components.rembg_preprocess,
        "none": components.no_preprocess,
    },
    
    # 風格
    "style": {
        "detailed": components.detailed_style_generate,
    },
    
    # 背景
    "background": {
        "transparent": components.transparent_background,
        "white": components.keep_white_background,
    },
    
    # 後處理
    "postprocess": {
        "normalize_1000": components.normalize_1000,
        "keep_size": components.keep_original_size,
    }
}


def get_component(category: str, name: str) -> Callable:
    """根據類別和名稱獲取組件"""
    return COMPONENT_REGISTRY[category][name]


def build_pipeline_from_names(config: Dict[str, str]) -> Dict[str, Callable]:
    """
    從組件名稱構建 pipeline 配置
    
    Args:
        config: {"analysis": "gemini_2.5", "preprocess": "rembg", ...}
    
    Returns:
        {"analysis": func, "preprocess": func, ...}
    """
    pipeline = {}
    
    for category, component_name in config.items():
        if component_name and component_name != "none":
            pipeline[category] = get_component(category, component_name)
    
    return pipeline

