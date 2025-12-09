"""Prompt 模板 - 向量插畫風格生成（原版完整版本）

恢復原作者的詳細版本：
- 完整的 RIM LIGHTING 說明（選擇性橘色高光）
- 詳細的 BODY GENERATION 指令
- 所有 CRITICAL、MANDATORY 強調
- 約 2000+ 字完整指導
"""


# ============================================================
# Body Composition Instructions (原版詳細版本)
# ============================================================

BODY_INSTRUCTIONS = {
    "full_body": """CRITICAL INSTRUCTION - BODY COMPOSITION (MANDATORY):
- The input photo shows FULL BODY (waist, legs, etc.)
- You MUST CROP the composition to show ONLY from head to UPPER CHEST (upper torso) - do NOT show waist, lower chest, or legs
- The bottom edge MUST be at the upper chest/shoulder area
- Remove all lower body parts (waist, hips, legs) from the final composition
- The OUTPUT MUST show from head to UPPER CHEST (upper torso) ONLY""",

    "head_only": """CRITICAL INSTRUCTION - BODY GENERATION (MANDATORY):
- The input photo shows ONLY HEAD or HEAD+NECK (stops at or just below the neck)
- YOU MUST ACTIVELY GENERATE NEW CONTENT - create more neck (if missing), more shoulders, and more upper chest area that extends DOWNWARD from where the original photo ends
- The GENERATED area must be SUBSTANTIAL and NATURAL - add enough vertical space so the final composition shows head, neck, shoulders, and upper chest
- Do NOT just keep the same body length as the original - you MUST ADD MORE body content below
- The GENERATED body parts must match the original photo's clothing style, colors, and appearance - make it seamless and natural
- The OUTPUT MUST show from head to UPPER CHEST (upper torso) with the generated body parts""",

    "head_neck": """CRITICAL INSTRUCTION - BODY GENERATION (MANDATORY):
- The input photo shows ONLY HEAD or HEAD+NECK (stops at or just below the neck)
- YOU MUST ACTIVELY GENERATE NEW CONTENT - create more neck (if missing), more shoulders, and more upper chest area that extends DOWNWARD from where the original photo ends
- The GENERATED area must be SUBSTANTIAL and NATURAL - add enough vertical space so the final composition shows head, neck, shoulders, and upper chest
- Do NOT just keep the same body length as the original - you MUST ADD MORE body content below
- The GENERATED body parts must match the original photo's clothing style, colors, and appearance - make it seamless and natural
- The OUTPUT MUST show from head to UPPER CHEST (upper torso) with the generated body parts""",

    "head_chest": """CRITICAL INSTRUCTION - BODY COMPOSITION (MANDATORY):
- The input photo already shows HEAD to UPPER CHEST (upper torso)
- Maintain that composition, ensuring the bottom edge is at the upper chest level
- The OUTPUT MUST show from head to UPPER CHEST (upper torso)"""
}


# ============================================================
# Main Style Prompt Template (原版完整版本)
# ============================================================

STYLE_PROMPT_TEMPLATE = """Transform this photo into a VECTOR ILLUSTRATION in semi-realistic corporate avatar style.

{body_instruction}

ARTISTIC STYLE:
- VECTOR ILLUSTRATION - clean, polished digital vector art
- SEMI-REALISTIC CORPORATE AVATAR STYLE - professional, confident, business-like appearance
- Maintain realistic facial proportions and bone structure - NO exaggerated features
- Clean lines, high contrast, flat color, vector art quality
- Commercial illustration quality - professional and polished

CHARACTER EXPRESSION & FEATURES:
- CONFIDENT EXPRESSION: The character should have a confident, professional expression
- REALISTIC PROPORTIONS: Maintain accurate facial proportions - realistic eye size, face shape, and features
- EYES: Realistic size with clear, natural colors. Detailed pupils, irises, and reflections
- EXPRESSION: Confident, professional expression with clarity and definition
- FACE: Confident expression with clear definition. Natural skin tones
- HAIR: Realistic hair with natural volume. Vector-style rendering with clear highlights

COLORING STYLE:
- FLAT COLOR: Use flat, solid colors - vector art style, NO gradients within shapes
- HIGH CONTRAST: Strong contrast between light and shadow areas
- NATURAL COLORS: Use natural, realistic colors - preserve original skin, hair, and clothing colors
- SKIN: Natural, warm skin tones with flat color rendering
- HAIR: Natural hair color with flat color rendering and distinct highlights
- EYES: Clear, natural eye colors
- LIPS: Natural lip color
- CLOTHING: Preserve original clothing colors with flat color rendering

LIGHTING & SHADING:
- CEL-SHADED LIGHTING: Use cel-shaded lighting technique - hard shadows with distinct, clear boundaries
- HARD SHADOWS: Shadows should have sharp, hard edges - NO soft gradients, NO smooth transitions
- DISTINCT HIGHLIGHTS: Add clear, distinct highlights on hair and face - sharp, defined highlight areas
- SHADING: Use flat color blocks for shadows - cel-shading technique with hard edges
- The lighting should create clear separation between light and shadow areas

RIM LIGHTING EFFECT (CRITICAL - SELECTIVE ORANGE/GOLDEN HIGHLIGHT FROM BEHIND - APPLIES TO ALL IMAGE TYPES):
- IMAGINE a warm light source from BEHIND the subject (person/character), shooting TOWARD the subject's back from a RANDOM angle (randomly choose from: behind-left, behind-right, behind-top-left, behind-top-right, behind-top, behind-bottom-left, behind-bottom-right, etc.) - vary the angle for each portrait
- The light source is positioned BEHIND the subject, creating SELECTIVE rim lighting that highlights ONLY SPECIFIC edges of the subject's silhouette
- MANDATORY: This highlight effect applies to BOTH real photos AND illustrations/vector graphics - ALL image types must have the selective orange/golden rim lighting
- CRITICAL - SELECTIVE HIGHLIGHTING (MANDATORY):
  * The highlight should appear ONLY on SELECTED, PROMINENT edges - NOT on all edges
  * Choose 2-3 KEY areas maximum for the highlight (e.g., top edge of hair, one shoulder edge, one clothing edge)
  * DO NOT apply highlight to the entire silhouette - be SELECTIVE and SPARSE
  * Most of the person's edges should have NO highlight - only a few strategic areas should have the orange/golden rim light
  * The highlight should be LOCALIZED to specific edge segments, NOT continuous along the entire edge
  * AVOID covering large areas with highlight - keep it MINIMAL and SELECTIVE
- The highlight should appear on SELECTED edges that are lit by the rear light source (e.g., if light is from behind-left, highlight appears ONLY on the top-left edge of hair and the left shoulder edge - NOT on the entire left side)
- The highlight should create a warm, orange-golden glow that adds depth and visual interest, but ONLY in SELECTED areas
- IMPORTANT: The highlight should be SPARSE and SELECTIVE - NOT covering large areas:
  * Only 2-3 KEY edge segments should have highlight
  * Most edges should have NO highlight at all
  * The highlight should be LOCALIZED to small, specific edge areas
  * The brightness should vary naturally - some highlighted areas brighter, some more subtle
  * The highlight should NOT be continuous - it should appear in isolated, strategic spots
- GLOW/HALO EFFECT (CRITICAL - MUST BE SUBTLE AND CONTROLLED):
  * The highlight can have a VERY SUBTLE, MINIMAL glow effect - but it MUST be controlled and refined
  * The glow should be TIGHT and CLOSE to the edge - do NOT let it extend too far beyond the sharp edge
  * The glow should be MINIMAL - just a very slight, gentle light diffusion that stays close to the edge
  * AVOID excessive glow, wide halos, or over-diffused light - keep it clean and precise
  * The glow should enhance the edge lighting WITHOUT creating a distracting halo or blur effect
  * If the glow becomes too prominent or extends too far, it should be REDUCED or REMOVED
  * The glow should be consistent with vector art style - clean, controlled, and refined
- The orange/golden color should be warm and luminous: approximately RGB (255, 180, 60) to RGB (255, 150, 30) - a bright, warm orange-golden tone
- IMPORTANT: Vary the light source direction for each portrait - randomly choose different behind angles to create visual variety
- The highlight should be REFINED with natural variation - not completely uniform, with brighter spots and softer fading areas, and a VERY SUBTLE, CONTROLLED glow effect that stays close to the edge

DETAIL FEATURES:
- HAIR: Realistic hair with natural volume. Vector-style rendering with distinct highlights on hair. Include SELECTIVE orange/golden rim light on ONLY 1-2 KEY edge segments (e.g., top edge or one side edge) - NOT on all edges. The highlight should be SPARSE and LOCALIZED, with VARIATIONS in brightness and a VERY SUBTLE, CONTROLLED glow effect that stays close to the edge. MANDATORY: This applies to BOTH real photos AND illustrations/vector graphics
- EYES: Realistic size and proportions, with clear colors and definition (pupils, irises, reflections)
- FACE: Confident expression with clear definition. Distinct highlights on face
- CLOTHING: Realistic colors with flat color rendering and cel-shaded shadows. Include SELECTIVE orange/golden rim light on ONLY 1-2 KEY edge segments (e.g., one shoulder edge or one clothing edge) - NOT on all edges. The highlight should be SPARSE and LOCALIZED, with VARIATIONS in brightness and a VERY SUBTLE, CONTROLLED glow effect that stays close to the edge. MANDATORY: This applies to BOTH real photos AND illustrations/vector graphics
- Keep lines clean and precise - vector art line quality
- AVOID excessive glow, wide halos, or over-diffused light effects - keep everything clean, controlled, and refined
- CRITICAL: The highlight should be SELECTIVE and SPARSE - only 2-3 KEY edge segments should have highlight, NOT the entire silhouette. Most edges should have NO highlight at all. This applies to ALL image types (photos AND illustrations/vector graphics)

PROPORTIONS:
- REALISTIC proportions - maintain accurate bone structure and anatomy
- NO exaggerated features - keep everything proportional and realistic
- Professional quality vector illustration

CROP & COMPOSITION:
- CRITICAL: Show ONLY from the head to the UPPER CHEST (upper torso) - crop at upper chest level, NOT waist, NOT lower chest
- The bottom edge MUST be at the upper chest/shoulder area, showing only head, neck, shoulders, and upper chest
- HEAD POSITIONING: Head should be centered horizontally in the frame
- MANDATORY BODY GENERATION: If the input photo only shows head/neck, you MUST GENERATE SUBSTANTIAL additional body/torso/chest area below the neck. The GENERATED area must be VISIBLY LONGER than the original - do NOT keep the same body length. ACTIVELY CREATE new neck area (extend downward), new shoulder area (widen and extend), and new upper chest content (add below). This ensures consistent composition showing head to upper chest.

COLORS:
- FLAT COLOR palette - no gradients within shapes
- HIGH CONTRAST - strong contrast between light and shadow
- Natural, realistic colors
- Clean vector art lines

BACKGROUND:
- Pure white, clean background (will be processed to transparent later)

OUTPUT:
- Vector illustration in semi-realistic corporate avatar style
- Highly recognizable likeness with realistic proportions
- Confident, professional expression
- Cel-shaded lighting with hard shadows and distinct highlights on hair and face
- SELECTIVE ORANGE/GOLDEN rim lighting effect from BEHIND the subject (person/character), from a RANDOM angle (varies for each portrait) - warm, luminous highlights on ONLY 2-3 SELECTED, KEY edge segments (NOT on all edges), with VARIATIONS in brightness (not uniform) and a VERY SUBTLE, CONTROLLED glow effect that stays close to the edge (avoid excessive glow or wide halos). Most edges should have NO highlight - only strategic, localized edge segments should have the highlight. MANDATORY: This applies to BOTH real photos AND illustrations/vector graphics - ALL image types must have the selective orange/golden rim lighting
- Clean lines, high contrast, flat color, vector art
- Commercial illustration quality
- CRITICAL: MUST show only head to UPPER CHEST (upper torso)

Create a VECTOR ILLUSTRATION of the subject (person/character) in semi-realistic corporate avatar style, with a confident expression, cel-shaded lighting with hard shadows and distinct highlights on hair and face, SELECTIVE ORANGE/GOLDEN rim lighting from BEHIND the subject from a RANDOM angle (varies for each portrait - warm, luminous highlights on ONLY 2-3 SELECTED, KEY edge segments, NOT on all edges, with VARIATIONS in brightness intensity creating brighter spots and softer fading areas, and a VERY SUBTLE, CONTROLLED glow effect that stays close to the edge - AVOID excessive glow, wide halos, or over-diffused light. Most edges should have NO highlight - only strategic, localized edge segments should have the highlight. MANDATORY: This selective orange/golden rim lighting applies to BOTH real photos AND illustrations/vector graphics - ALL image types must have this highlight effect), on a pure white background. Clean lines, high contrast, flat color, vector art, commercial illustration quality. The OUTPUT MUST show from head to UPPER CHEST (upper torso) ONLY."""


# ============================================================
# Helper Function
# ============================================================

def get_style_prompt(body_extent: str) -> str:
    """
    根據身體範圍生成完整的風格 prompt（原版詳細版本）
    
    Args:
        body_extent: "head_only", "head_neck", "head_chest", or "full_body"
        
    Returns:
        完整的 prompt 字串
    """
    body_instruction = BODY_INSTRUCTIONS.get(body_extent, BODY_INSTRUCTIONS["full_body"])
    return STYLE_PROMPT_TEMPLATE.format(body_instruction=body_instruction)


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


# ============================================================
# 身體檢測 Prompt (原版詳細版本)
# ============================================================

BODY_EXTENT_PROMPT = """Analyze this photo of a person and determine the visible body parts:

1. HEAD_ONLY - if the photo shows ONLY the head/face (stops at the chin or neck base, no visible shoulders or chest)
2. HEAD_NECK - if the photo shows head and neck, but stops at or just below the neck (no visible shoulders or chest)
3. HEAD_CHEST - if the photo shows head, neck, shoulders, and upper chest ONLY (stops at upper chest level, NO visible waist, NO visible lower chest below the shoulders, NO visible abdomen, NO visible lower body parts)
4. FULL_BODY - if the photo shows ANY part of the body below the upper chest, including:
   - Waist (腰部)
   - Lower chest below shoulders (肩膀以下的胸部)
   - Abdomen (腹部)
   - Hips (臀部)
   - Legs (腿部)
   - Or ANY lower body parts

CRITICAL: If you can see the waist (腰部), lower chest below shoulders, abdomen, or any part below the upper chest/shoulder area, it MUST be classified as FULL_BODY, NOT HEAD_CHEST.

Answer ONLY with "HEAD_ONLY", "HEAD_NECK", "HEAD_CHEST", or "FULL_BODY", nothing else."""


# ============================================================
# 圖片類型檢測 Prompt
# ============================================================

IMAGE_TYPE_PROMPT = """Analyze this image and determine if it is:
1. ILLUSTRATION - if it is a digital illustration, vector art, cartoon, anime, or any non-photographic artwork
2. PHOTO - if it is a real photograph of a person

Answer ONLY with "ILLUSTRATION" or "PHOTO", nothing else."""
