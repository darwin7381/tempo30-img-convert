# Prompt 版本對比分析

## 概述

當前 `src/prompts.py` 是簡化版（約600字），原作者的版本更詳細（約2000+字）。

---

## 關鍵差異

### BODY_INSTRUCTIONS

#### 當前版本（簡化）

```python
"head_only": """## COMPOSITION  
- INPUT: Head/face only
- ACTION: Generate neck, shoulders, upper chest
- Extend naturally to create head-to-chest composition"""
```

**字數**：約 20 字

#### 原版（詳細）

```python
"head_only/head_neck": """CRITICAL INSTRUCTION - BODY GENERATION (MANDATORY):
- The input photo shows ONLY HEAD or HEAD+NECK (stops at or just below the neck)
- YOU MUST ACTIVELY GENERATE NEW CONTENT - create more neck (if missing), more shoulders, and more upper chest area that extends DOWNWARD from where the original photo ends
- The GENERATED area must be SUBSTANTIAL and NATURAL - add enough vertical space so the final composition shows head, neck, shoulders, and upper chest
- Do NOT just keep the same body length as the original - you MUST ADD MORE body content below
- The GENERATED body parts must match the original photo's clothing style, colors, and appearance - make it seamless and natural
- The OUTPUT MUST show from head to UPPER CHEST (upper torso) with the generated body parts"""
```

**字數**：約 120 字

**差異**：
- 原版強調 CRITICAL、MANDATORY
- 原版明確說明「ACTIVELY GENERATE」「SUBSTANTIAL」
- 原版警告「Do NOT just keep the same body length」
- 原版要求「seamless and natural」

---

### STYLE_PROMPT

#### 當前版本（簡化）

```python
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
```

**字數**：約 180 字

#### 原版（詳細）

包含（從用戶提供的代碼）：
- ARTISTIC STYLE（向量插畫、半寫實、商業品質）
- CHARACTER EXPRESSION & FEATURES（表情、五官、頭髮詳細要求）
- COLORING STYLE（扁平色彩、高對比、自然顏色）
- LIGHTING & SHADING（賽璐璐著色、硬陰影）
- **RIM LIGHTING EFFECT（超詳細，約500字）**：
  - SELECTIVE HIGHLIGHTING
  - GLOW/HALO EFFECT 控制
  - 顏色規格
  - 應用到所有圖片類型的強調
- DETAIL FEATURES（頭髮、眼睛、臉部、衣服的詳細要求）
- PROPORTIONS（比例要求）
- CROP & COMPOSITION（構圖和裁切）
- COLORS（顏色要求）
- BACKGROUND（背景）

**字數**：約 2000+ 字

---

## 主要差異分析

### 1. RIM LIGHTING（橘色高光）

**當前版本**：
```
- Color: Warm orange-golden (RGB ~255,165,45)
- Source: Behind subject, random angle each time
- Coverage: ONLY 2-3 key edges
- Style: Subtle glow, localized, not continuous
```

**原版**：
```
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
  ...（還有更多）
```

**分析**：
- 原版長度約10倍
- 原版使用大量強調詞
- 原版更詳細地說明「選擇性」（SELECTIVE）
- 原版明確說適用於所有圖片類型

---

### 2. BODY GENERATION 指令

**當前版本 head_only**：
```
- INPUT: Head/face only
- ACTION: Generate neck, shoulders, upper chest
- Extend naturally
```

**原版 head_only/head_neck**：
```
CRITICAL INSTRUCTION - BODY GENERATION (MANDATORY):
- YOU MUST ACTIVELY GENERATE NEW CONTENT
- The GENERATED area must be SUBSTANTIAL and NATURAL
- Do NOT just keep the same body length
- you MUST ADD MORE body content below
- The GENERATED body parts must match the original photo's clothing style
```

**分析**：
- 原版強調「ACTIVELY」「SUBSTANTIAL」「MUST ADD MORE」
- 原版警告常見錯誤（「Do NOT just keep」）
- 原版要求匹配原照片風格

---

### 3. 詳細程度對比

| 部分 | 當前字數 | 原版字數 | 差異 |
|------|----------|----------|------|
| BODY_INSTRUCTIONS | ~20字/種 | ~120字/種 | 6倍 |
| Style Requirements | ~50字 | ~300字 | 6倍 |
| RIM LIGHTING | ~60字 | ~500字 | 8倍 |
| 其他細節 | 無 | ~500字 | ∞ |
| **總計** | **~600字** | **~2000字** | **3.3倍** |

---

## 我的分析

### 為何當初簡化？

從代碼註釋看：
```python
"""Prompt 模板 - 向量插畫風格生成

優化版本：
- 從 ~1800 字精簡至 ~600 字（減少 66%）
- 結構化格式，提高 AI 理解效率
- 分離正面/負面指令
"""
```

**簡化理由**：
1. 減少 token 消耗（省錢）
2. 提高 AI 理解效率（更簡潔）
3. 移除冗餘資訊

---

### 簡化版的問題

從用戶反饋和原版設計看，可能遺失了：

1. **強調的力度**
   - 沒有 CRITICAL、MANDATORY
   - AI 可能不夠重視某些要求

2. **選擇性橘色高光的詳細說明**
   - 當前：「2-3 key edges」
   - 原版：詳細說明如何選擇、如何控制、如何避免過度
   - 可能導致高光效果不準確

3. **身體生成的明確性**
   - 當前：「Generate」
   - 原版：「ACTIVELY GENERATE」「SUBSTANTIAL」「ADD MORE」
   - 可能導致生成不足

4. **常見錯誤的警告**
   - 原版有「Do NOT」警告
   - 幫助AI避免常見錯誤

---

## 建議

### 方案A：完全恢復原版

**優點**：
- ✅ 恢復所有細節和強調
- ✅ 可能提升生成品質
- ✅ 更明確的指導

**缺點**：
- ❌ Token 消耗增加 3.3倍
- ❌ Prompt 可能過長
- ❌ 維護更複雜

---

### 方案B：選擇性恢復關鍵部分

**保留簡化**：
- Style Requirements（基本風格）
- Constraints（禁止事項）

**恢復詳細**：
- RIM LIGHTING（橘色高光很關鍵）
- BODY GENERATION 警告（避免常見錯誤）

**優點**：
- ✅ 平衡 token 和品質
- ✅ 保留關鍵細節
- ✅ 不會過長

**缺點**：
- ⚠️ 需要判斷哪些該詳細

---

### 方案C：保持當前版本

如果當前品質已滿意，保持不變。

---

## 我的建議

**建議方案B（選擇性恢復）**

**具體做法**：

1. **BODY_INSTRUCTIONS**：恢復原版的詳細度
   - 特別是 head_only/head_neck 的「ACTIVELY GENERATE」「SUBSTANTIAL」
   - 這些強調詞可能很重要

2. **RIM LIGHTING**：恢復原版的選擇性說明
   - 詳細的「SELECTIVE」「SPARSE」說明
   - 這是風格的關鍵特色

3. **其他部分**：保持簡化
   - Style Requirements 表格形式已經清楚
   - Constraints 列表也夠用

**預期效果**：
- Prompt 約 1200 字（介於兩者之間）
- 保留關鍵細節
- 平衡 token 和品質

**您的選擇**？
- A. 完全恢復原版（2000字）
- B. 選擇性恢復（1200字）
- C. 保持當前簡化版（600字）

我建議 B，但如果品質差異明顯，應該選 A。

