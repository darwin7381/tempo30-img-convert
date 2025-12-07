# Body Instructions 設計分析

## 概述

Body Instructions 是這個專案中用來指導 AI 如何處理不同身體構圖的關鍵機制。本文檔深入分析其必要性、優缺點和替代方案。

---

## 當前設計（4種分類）

### 設計邏輯

根據輸入圖片的身體可見範圍，選擇對應的處理指令：

| 分類 | 檢測條件 | AI指令 | 效果 |
|------|----------|--------|------|
| **HEAD_ONLY** | 只有臉/頭部 | 生成脖子、肩膀、上胸部 | 擴展：大頭照→半身像 |
| **HEAD_NECK** | 頭部+脖子，無肩膀 | 生成肩膀和上胸部 | 補充：缺少的肩膀區域 |
| **HEAD_CHEST** | 頭部到上胸部 | 保持當前構圖 | 維持：理想構圖不變 |
| **FULL_BODY** | 腰部以下可見 | 裁切到頭部→上胸部 | 裁切：全身照→半身像 |

### 實現位置

**檔案**：`src/prompts.py` 第14-34行

```python
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
```

### 使用流程

```
輸入圖片
  ↓
AI檢測身體範圍 → HEAD_CHEST
  ↓
查表 BODY_INSTRUCTIONS["head_chest"]
  ↓
組合成完整 STYLE_PROMPT
  ↓
發送給 Gemini 3 Pro Image
  ↓
生成統一構圖的半身像
```

---

## 正面論證：為何需要Body Instructions

### 1. 統一輸出構圖的必要性

**問題場景**：
- 用戶A上傳大頭照（只有臉）
- 用戶B上傳全身照（包含腿）
- 用戶C上傳半身照（理想）

**沒有Body Instructions的結果**：
- 大頭照 → AI可能保持原樣（只有頭）
- 全身照 → AI可能完整轉換（包含腿）
- 半身照 → AI正常處理

**結果**：三張圖片構圖完全不同，不一致！

**有Body Instructions的結果**：
- 大頭照 → AI生成身體 → 統一半身像
- 全身照 → AI裁切下半身 → 統一半身像
- 半身照 → AI保持 → 統一半身像

**結果**：所有圖片構圖一致！

**結論**：✅ 對於需要統一輸出的場景（如企業頭像），這是必要的。

---

### 2. AI生成的精確控制

**AI的自然行為**（無明確指令時）：
- 傾向於保持輸入圖片的構圖
- 可能不會主動裁切或生成缺失部分
- 結果不可預測

**有明確指令後**：
- AI明確知道要「裁切」還是「生成」
- 減少不確定性
- 結果更符合預期

**實證**：
- "Transform to vector art" → AI可能保持原構圖
- "Transform to vector art, crop to upper chest" → AI明確裁切
- "Generate missing shoulders and chest" → AI明確生成

**結論**：✅ 明確指令提高AI執行的準確性。

---

### 3. 處理邊緣案例

**HEAD_NECK 的價值**：
- 輸入：證件照風格（只有頭和領子）
- 如果用 HEAD_ONLY 指令 → AI可能生成太多身體
- 如果用 HEAD_CHEST 指令 → AI可能不夠
- HEAD_NECK 指令 → 剛好補充肩膀

**FULL_BODY 的價值**：
- 輸入：活動照（全身+背景）
- 如果沒有裁切指令 → AI可能保留全身
- 有裁切指令 → AI知道要聚焦上半身

**結論**：✅ 4種分類覆蓋了實際會遇到的各種情況。

---

### 4. 減少後期程式處理

**邏輯**：
- 讓AI在生成時就處理構圖
- 而不是生成後再用程式裁切/擴展

**優勢**：
- AI理解語義，處理更自然
- 程式裁切可能生硬

**例子**：
- AI生成時裁切 → 會自然處理肩膀線條、衣服邊緣
- 程式後期裁切 → 可能切斷不完整

**結論**：✅ 讓AI處理構圖比程式後處理更自然。

---

## 反面論證：為何可能不需要

### 1. 增加系統複雜度

**複雜度增加**：
```
無 Body Instructions：
  檢測類型 → AI生成 → 後處理
  （簡單明瞭）

有 Body Instructions：
  檢測類型 → 檢測身體 → 查表選指令 → 組合Prompt → AI生成 → 後處理
  （多了3個步驟）
```

**維護成本**：
- 需要維護 BODY_INSTRUCTIONS 字典
- 需要確保 Prompt 組合正確
- 增加除錯難度

**結論**：❌ 系統複雜度明顯增加。

---

### 2. AI能力可能被低估

**Gemini 3 Pro Image 的能力**：
- 2025年11月最新模型
- 知識截止：2025年1月
- 上下文：65,536 tokens

**可能性**：
```python
# 簡化Prompt可能就夠了
SIMPLE_PROMPT = """Create a professional corporate avatar portrait.
- Framing: HEAD TO UPPER CHEST
- Automatically adjust from any input (crop if full body, generate if head only)
- Style: [其他風格要求...]
"""
```

AI可能足夠聰明，不需要4種詳細指令。

**結論**：⚠️ 可能過度設計，應該實測對比。

---

### 3. 分類邊界模糊

**問題案例**：
- 圖片A：頭+脖子+一點肩膀 → HEAD_NECK 還是 HEAD_CHEST？
- 圖片B：上胸部+一點腰 → HEAD_CHEST 還是 FULL_BODY？

**AI判斷可能不穩定**：
- 同一張圖，不同時間可能判斷不同
- 邊界案例難以區分
- 導致選錯指令

**結論**：❌ 分類過細可能導致判斷不穩定。

---

### 4. 實際使用分佈不均

**假設**（需要數據驗證）：
- HEAD_CHEST：70%（最常見，理想構圖）
- FULL_BODY：20%（全身照需裁切）
- HEAD_ONLY：8%（大頭照）
- HEAD_NECK：2%（很少見）

**如果分佈真是如此**：
- HEAD_NECK 只佔2% → 可能不值得單獨處理
- 可以合併到 HEAD_ONLY 或 HEAD_CHEST

**結論**：⚠️ 4種分類可能過細，2-3種可能更實用。

---

## 替代方案詳細分析

### 方案A：簡化為單一智能指令

```python
UNIFIED_INSTRUCTION = """## COMPOSITION
Automatically create a HEAD TO UPPER CHEST corporate portrait:
- If input shows full body: intelligently crop to upper chest
- If input shows only head/face: naturally generate shoulders and chest
- If input already shows head to chest: maintain composition
- Ensure consistent professional framing across all inputs
"""
```

**優點**：
- ✅ 最簡單（1種指令）
- ✅ 代碼簡潔
- ✅ 無需身體檢測步驟
- ✅ 信任AI智能

**缺點**：
- ❌ 控制度降低
- ❌ 一致性可能下降
- ❌ 需要實測驗證

**適用場景**：
- AI模型足夠先進
- 對一致性要求不極端嚴格
- 追求簡潔性

**風險**：中等

---

### 方案B：簡化為2種指令

```python
BODY_INSTRUCTIONS = {
    "crop_required": """## COMPOSITION
- INPUT: Full body or extensive body parts visible
- ACTION: Crop to HEAD → UPPER CHEST
- Focus on upper body, remove lower parts""",
    
    "generate_required": """## COMPOSITION
- INPUT: Head only or insufficient body parts
- ACTION: Generate natural shoulders and upper chest
- Extend composition to create complete upper body portrait"""
}

# 分類邏輯
if body_extent in ["head_only", "head_neck"]:
    instruction = BODY_INSTRUCTIONS["generate_required"]
elif body_extent in ["full_body"]:
    instruction = BODY_INSTRUCTIONS["crop_required"]
else:  # head_chest
    instruction = "Maintain current framing"
```

**優點**：
- ✅ 簡化50%
- ✅ 保留關鍵控制（生成 vs 裁切）
- ✅ 仍有明確指導
- ✅ 降低分類錯誤風險

**缺點**：
- ⚠️ 失去細緻度
- ⚠️ 邊界案例處理不夠精確

**適用場景**：
- 平衡簡潔性和控制度
- 實際只有2種主要情況（生成/裁切）

**風險**：低

---

### 方案C：動態Prompt（根據實際測量）

不依賴AI判斷，用程式測量：

```python
def generate_body_instruction(image):
    # 程式測量身體比例
    height = image.height
    width = image.width
    
    # 檢測人臉位置（用 face detection）
    face_bottom = detect_face_bottom(image)
    body_visible_ratio = (height - face_bottom) / height
    
    if body_visible_ratio < 0.2:
        return "Generate shoulders and chest"
    elif body_visible_ratio > 0.6:
        return "Crop to upper chest"
    else:
        return "Maintain framing"
```

**優點**：
- ✅ 更精確（基於測量，不是AI猜測）
- ✅ 可重複（相同圖片相同結果）
- ✅ 不需要額外AI調用

**缺點**：
- ❌ 需要額外的人臉檢測模型
- ❌ 代碼更複雜
- ❌ 可能誤判（遮擋、側臉等）

**適用場景**：
- 追求最高精確度
- 願意增加技術複雜度
- 有可靠的人臉檢測工具

**風險**：中高

---

### 方案D：讓AI在生成時自己決定

完全不給構圖指令，只給風格要求：

```python
STYLE_ONLY_PROMPT = """Transform this into a VECTOR ILLUSTRATION.

## STYLE REQUIREMENTS
- Type: Semi-realistic corporate avatar
- Rendering: Clean vector art, cel-shaded
- Framing: Professional head-to-upper-chest portrait (adjust as needed)
- [其他風格要求...]

Note: Automatically adjust composition to create a professional corporate headshot.
"""
```

**優點**：
- ✅ 極簡（無 Body Instructions）
- ✅ 完全信任AI
- ✅ 讓AI發揮創意
- ✅ 無需檢測身體範圍

**缺點**：
- ❌ 控制度最低
- ❌ 一致性無法保證
- ❌ 可能產生意外結果
- ❌ 不同圖片可能差異很大

**適用場景**：
- 藝術創作（而非企業頭像）
- 接受多樣性
- AI模型極度先進

**風險**：高

---

## 必要性分析

### ✅ 支持「必要」的論據

#### 論據1：企業級一致性需求

**場景**：公司要為100名員工製作統一風格頭像

**需求**：
- 所有頭像構圖必須一致
- 頭部位置、身體比例統一
- 專業、標準化的輸出

**Body Instructions 的價值**：
- 確保所有輸入（大頭照、全身照、半身照）都輸出相同構圖
- 明確告訴AI要做什麼（生成/裁切/保持）
- 減少意外和不一致

**評分**：9/10（對企業應用幾乎必要）

---

#### 論據2：減少後期程式處理

**對比**：

**無 Body Instructions**：
```
AI生成（可能構圖不對）→ 程式強制裁切/擴展 → 生硬、不自然
```

**有 Body Instructions**：
```
AI生成時就按指令處理 → 自然、協調的構圖
```

**例子**：
- 全身照用程式裁切 → 可能切斷手臂、衣服邊緣生硬
- 全身照AI裁切 → 自然處理邊緣、調整構圖

**評分**：8/10（AI處理確實更自然）

---

#### 論據3：精確的業務邏輯表達

**需求**：「所有圖片都要是頭部到上胸部的半身像」

**表達方式對比**：

**方式A（籠統）**：
```
"Create a portrait"  
→ AI可能理解為：全身像？半身像？大頭照？
```

**方式B（Body Instructions）**：
```
"Crop to head→upper chest" 或 "Generate to upper chest"
→ AI明確知道要做什麼
```

**評分**：7/10（明確性高，但可能過度詳細）

---

### ❌ 反對「必要」的論據

#### 論據1：過度工程化

**現實**：
- 4種分類可能過細
- HEAD_NECK 和 HEAD_ONLY 差異不大（都是生成身體）
- HEAD_CHEST 和保持原樣類似

**簡化可能性**：
```
實際只需要2種：
1. needs_generation（頭部不足）
2. needs_crop（身體過多）
```

**評分**：8/10（確實可能過度細分）

---

#### 論據2：增加失敗點

**問題鏈**：
```
AI檢測身體範圍
  ↓ 如果判斷錯誤
選錯 Body Instruction
  ↓
AI執行錯誤的指令
  ↓
結果不理想
```

**風險**：
- 邊界案例判斷不穩定
- 增加了一個可能出錯的環節

**替代**：
- 讓AI自己判斷可能更準確
- 減少中間環節

**評分**：7/10（確實增加了複雜度和失敗可能）

---

#### 論據3：AI能力可能被低估

**Gemini 3 Pro Image 的能力**：
- 最新模型（2025-11-20）
- 強大的圖像理解
- 可能不需要如此詳細的指導

**測試假設**：
```python
# 簡單指令
SIMPLE = "Create head-to-upper-chest portrait, adjust composition as needed"

# 複雜指令（當前）
COMPLEX = [4種詳細的Body Instructions]
```

**可能結果**：兩者品質相同或差異很小

**評分**：6/10（需要實測才能確定）

---

## 替代方案對比

### 方案對比表

| 方案 | 複雜度 | 控制度 | 一致性 | 風險 | 推薦度 |
|------|--------|--------|--------|------|--------|
| **當前（4種）** | 高 | 高 | 高 | 中 | ⭐⭐⭐⭐ |
| **方案A（1種）** | 低 | 低 | 中 | 高 | ⭐⭐ |
| **方案B（2種）** | 中 | 中高 | 中高 | 低 | ⭐⭐⭐⭐⭐ |
| **方案C（測量）** | 很高 | 很高 | 很高 | 中高 | ⭐⭐⭐ |
| **方案D（無指令）** | 最低 | 最低 | 低 | 很高 | ⭐ |

---

## 我的分析和建議

### 當前設計評分：7.5/10

**優點**：
- ✅ 邏輯清晰
- ✅ 覆蓋全面
- ✅ 一致性高

**缺點**：
- ⚠️ 可能過度細分
- ⚠️ HEAD_NECK 使用率可能很低
- ⚠️ 增加系統複雜度

---

### 建議的演進路徑

#### 階段1：保持當前設計（短期）

**理由**：
- 已經實現且運作
- 沒有明顯問題
- 先收集數據

**行動**：
- 記錄每種分類的使用頻率
- 觀察哪些分類常用
- 收集品質反饋

**時間**：使用1-2個月

---

#### 階段2：數據驅動決策（中期）

**根據數據判斷**：

**情況A**：如果 HEAD_NECK < 5%
```
→ 合併 HEAD_NECK 到 HEAD_ONLY
→ 簡化為3種分類
```

**情況B**：如果 HEAD_ONLY + HEAD_NECK 的結果品質相同
```
→ 合併為單一「generate」指令
→ 簡化為2種（generate / crop）
```

**情況C**：如果4種分類都常用且效果好
```
→ 保持當前設計
```

---

#### 階段3：實驗對比（長期）

**A/B測試**：
```
組A：使用當前4種Body Instructions
組B：使用簡化2種指令
組C：使用單一智能指令

對比指標：
1. 構圖一致性
2. 生成品質
3. 用戶滿意度
4. 處理時間
5. API成本
```

**根據結果選擇最佳方案**

---

## 討論問題

### Q1：必要性判斷

**您認為當前的4種分類是**：
- A. 完全必要（業務需求）
- B. 部分必要（可以簡化）
- C. 不太必要（過度設計）
- D. 需要實測才能判斷

### Q2：簡化意願

**如果要簡化，您傾向**：
- A. 簡化為2種（generate / crop）
- B. 簡化為1種（智能指令）
- C. 保持4種（確保品質）
- D. 先實測再決定

### Q3：優先級

**Body Instructions 優化的優先級**：
- A. P0（立即處理）
- B. P1（重要但不緊急）
- C. P2（有空再說）
- D. P3（暫不考慮）

---

## 我的個人建議

### 推薦：方案B（簡化為2種）+ 實測驗證

**理由**：
1. **平衡**：保留核心控制（生成/裁切），減少複雜度
2. **實用**：2種分類足以覆蓋主要情況
3. **風險低**：如果效果不好，易於回退
4. **可驗證**：容易對比測試

**實施步驟**：
1. 複製當前 prompts.py 為 prompts_v2.py
2. 實現2種版本
3. 同時測試兩個版本
4. 對比結果
5. 選擇更好的

**預估工作量**：1-2小時

---

## 總結

**當前設計**：
- 合理性：7.5/10
- 必要性：根據業務需求而定
- 優化空間：存在，但不緊急

**建議優先級**：
1. **P0**：消除重複API調用（33%配額）
2. **P1**：完善前端顯示（已完成）
3. **P2**：Body Instructions 優化（中期考慮）

**下一步討論**：
- 您的業務場景對一致性要求有多高？
- 願意犧牲多少一致性來換取簡潔性？
- 是否願意投入時間做A/B測試？

我等待您的意見再決定是否優化這部分。

