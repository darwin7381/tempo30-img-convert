"""細粒度風格配置 - 使用拆分後的細粒度組件"""

from . import components_fine_grained as fg


# ============================================================
# I4 詳細版 - 細粒度配置
# ============================================================

I4_DETAILED_FINE = {
    "name": "I4 詳細版（細粒度）",
    "description": "完整流程，每個步驟獨立顯示",
    "steps": [
        # 步驟1：檢測圖片類型
        {
            "name": "檢測圖片類型",
            "icon": "🔍",
            "component": fg.detect_image_type,
            "update_context": True
        },
        # 步驟2：去背處理（照片）或格式轉換（插畫）
        {
            "name": "去背處理",
            "icon": "✂️",
            "component": fg.rembg_remove_background,
            "update_image": True,
            "show_image": True
        },
        # 步驟3：裁切平整底部（僅照片）
        {
            "name": "裁切平整底部",
            "icon": "✂️",
            "component": fg.crop_to_content,
            "update_image": True,
            "show_image": True,
            "conditional": lambda ctx: ctx.get("image_type") == "photo"
        },
        # 步驟4：檢測身體範圍（原版順序：在去背之後）
        {
            "name": "檢測身體範圍",
            "icon": "🔍",
            "component": fg.detect_body_extent,
            "update_context": True
        },
        # 步驟5：生成Body Instruction（需要新增組件）
        {
            "name": "生成處理指令",
            "icon": "📝",
            "component": fg.generate_body_instruction,
            "update_context": True
        },
        # 步驟6：構建完整Prompt
        {
            "name": "構建AI Prompt",
            "icon": "📋",
            "component": fg.build_full_prompt,
            "update_context": True
        },
        # 步驟7：AI生成向量插畫
        {
            "name": "AI生成插畫",
            "icon": "🎨",
            "component": fg.ai_generate_style,
            "update_image": True,
            "show_image": True
        },
        # 步驟8：白色轉透明
        {
            "name": "白色轉透明",
            "icon": "🌈",
            "component": fg.make_white_transparent,
            "update_image": True,
            "show_image": True
        },
        # 步驟9：統一尺寸和位置
        {
            "name": "統一尺寸位置",
            "icon": "📐",
            "component": fg.resize_and_position,
            "update_image": True,
            "show_image": True
        },
        # 步驟10：底部裁切（僅照片）
        {
            "name": "底部裁切",
            "icon": "✂️",
            "component": fg.crop_bottom_edge,
            "update_image": True,
            "show_image": True,
            "conditional": lambda ctx: ctx.get("image_type") == "photo"
        }
    ]
}


# ============================================================
# 萬能智能版 - 細粒度配置
# ============================================================

UNIVERSAL_INTELLIGENT_FINE = {
    "name": "萬能智能版（細粒度）",
    "description": "極簡流程，AI 萬能生成 + 透明背景",
    "steps": [
        {
            "name": "AI 萬能智能生成",
            "icon": "🎨",
            "component": fg.ai_generate_universal,
            "update_image": True,
            "show_image": True
        },
        {
            "name": "白色轉透明",
            "icon": "🌈",
            "component": fg.make_white_transparent,
            "update_image": True,
            "show_image": True
        }
    ]
}


# ============================================================
# I4 簡化版 - 細粒度配置
# ============================================================

I4_SIMPLIFIED_FINE = {
    "name": "I4 簡化版（細粒度）",
    "description": "跳過檢測和預處理的快速版本",
    "steps": [
        {
            "name": "準備圖片給 AI",
            "icon": "🔧",
            "component": fg.prepare_for_ai,
            "update_image": True
        },
        {
            "name": "構建風格 Prompt",
            "icon": "📝",
            "component": fg.build_full_prompt,
            "update_context": True
        },
        {
            "name": "AI 生成向量插畫",
            "icon": "🎨",
            "component": fg.ai_generate_style,
            "update_image": True,
            "show_image": True
        }
    ]
}


# ============================================================
# 風格註冊表
# ============================================================

FINE_GRAINED_STYLES = {
    "i4_detailed": I4_DETAILED_FINE,
    "universal_intelligent": UNIVERSAL_INTELLIGENT_FINE,
    "i4_simplified": I4_SIMPLIFIED_FINE
}


# 前端選項
STYLE_OPTIONS = [
    {
        "id": "i4_detailed",
        "name": "I4 詳細版",
        "description": "完整流程（10步驟）",
        "recommended": True
    },
    {
        "id": "universal_intelligent",
        "name": "萬能智能版",
        "description": "極簡流程（2步驟：AI生成+透明背景）",
        "recommended": False
    },
    {
        "id": "i4_simplified",
        "name": "I4 簡化版",
        "description": "快速版（3步驟）",
        "recommended": False
    }
]

