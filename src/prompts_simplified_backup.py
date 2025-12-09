"""Prompt 模板 - 向量插畫風格生成

優化版本：
- 從 ~1800 字精簡至 ~600 字（減少 66%）
- 結構化格式，提高 AI 理解效率
- 分離正面/負面指令
"""


# ============================================================
# Body Composition Instructions (根據檢測結果動態選擇)
# ============================================================

BODY_INSTRUCTIONS = {
    "full_body": """## COMPOSITION
- INPUT: Full body photo
- ACTION: Crop to HEAD → UPPER CHEST only
- Remove: waist, legs, lower body""",

    "head_only": """## COMPOSITION  
- INPUT: Head/face only
- ACTION: Generate neck, shoulders, upper chest
- Extend naturally to create head-to-chest composition""",

    "head_neck": """## COMPOSITION
- INPUT: Head and neck only  
- ACTION: Generate shoulders and upper chest
- Extend naturally below neck""",

    "head_chest": """## COMPOSITION
- INPUT: Head to upper chest (ideal)
- ACTION: Maintain current framing
- Ensure bottom edge at upper chest level"""
}


# ============================================================
# Main Style Prompt Template
# ============================================================

STYLE_PROMPT = """Transform this photo into a VECTOR ILLUSTRATION.

{body_instruction}

## STYLE REQUIREMENTS
| Aspect | Specification |
|--------|--------------|
| Type | Semi-realistic corporate avatar |
| Rendering | Clean vector art, cel-shaded |
| Colors | Flat solid blocks, NO gradients |
| Shadows | Hard edges, high contrast |
| Proportions | Realistic, no exaggeration |
| Expression | Confident, professional |

## RIM LIGHTING (REQUIRED)
- Color: Warm orange-golden (RGB ~255,165,45)
- Source: Behind subject, random angle each time
- Coverage: ONLY 2-3 key edges (examples: hair top, one shoulder)
- Style: Subtle glow, localized, not continuous

## CONSTRAINTS (DO NOT)
- Use soft gradients or blurs
- Exaggerate facial features  
- Add glow halos or wide diffusion
- Highlight entire silhouette
- Show body below upper chest
- Use any background color (use pure white)

## OUTPUT
- Vector illustration, commercial quality
- Recognizable likeness preserved
- White background (for transparency processing)
- Frame: Head to upper chest only"""


# ============================================================
# Helper Function
# ============================================================

def get_style_prompt(body_extent: str) -> str:
    """
    根據身體範圍生成完整的風格 prompt
    
    Args:
        body_extent: "head_only", "head_neck", "head_chest", or "full_body"
        
    Returns:
        完整的 prompt 字串
    """
    body_instruction = BODY_INSTRUCTIONS.get(body_extent, BODY_INSTRUCTIONS["full_body"])
    return STYLE_PROMPT.format(body_instruction=body_instruction)


# ============================================================
# Analysis Prompt (用於合併檢測)
# ============================================================

ANALYZE_PROMPT = """Analyze this image:

1. TYPE: Is this a PHOTO or ILLUSTRATION?
2. BODY: What body parts are visible?
   - HEAD_ONLY: Face/head only
   - HEAD_NECK: Head + neck, no shoulders
   - HEAD_CHEST: Head to upper chest
   - FULL_BODY: Waist or below visible

Response format (exactly 2 lines):
TYPE: [PHOTO/ILLUSTRATION]
BODY: [HEAD_ONLY/HEAD_NECK/HEAD_CHEST/FULL_BODY]"""
