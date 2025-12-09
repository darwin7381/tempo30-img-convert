# Prompt 順序對結果的影響分析

## 現象描述

**觀察到的差異**：

```python
# 順序A：Prompt 在前（原版）
contents=[prompt, image]
→ 結果：保持原圖姿勢，只改變風格 ✅

# 順序B：Image 在前（我的修改）
contents=[image, prompt]  
→ 結果：可能改變姿勢 ❌
```

**問題**：為何同一個 request，只是順序不同，結果會有如此大的差異？

---

## 深度技術分析

### 1. 這不是執行順序問題

**確認**：
- 兩種順序都在**同一個 API 請求**中
- 不是「先處理 A 再處理 B」的時序問題
- 是「A 和 B 的相對位置」影響了 AI 的理解

**類比**：
```
這不是：
  步驟1：讀 Prompt
  步驟2：讀 Image
  
而是：
  同時看到：[Prompt, Image] 或 [Image, Prompt]
  但看到的「順序」影響了理解
```

---

### 2. Transformer 注意力機制

#### 基本原理

**Transformer 模型**（Gemini 的基礎）：
- 使用「自注意力機制」（Self-Attention）
- 每個 token 可以「關注」其他所有 token
- 但**位置編碼**（Positional Encoding）會影響關注度

**位置編碼的影響**：
```
輸入：[Token1, Token2, Token3, ...]

每個 Token 都有：
  內容編碼（Content Embedding）
  + 
  位置編碼（Position Embedding）

位置編碼告訴模型：
  「這是第1個 token」
  「這是第2個 token」
  ...

不同位置 → 不同的注意力權重
```

#### 對我們的影響

**順序A：[Prompt, Image]**
```
Position 0-500:   Prompt tokens
Position 501-800: Image tokens

模型的理解：
  1. 先看到完整的指令（"Transform this photo..."）
  2. 知道任務是「轉換風格」
  3. 再看到圖片
  4. 帶著「轉換風格」的意圖去理解圖片
  5. 重點：保持圖片內容，只改風格
```

**順序B：[Image, Prompt]**
```
Position 0-300:   Image tokens
Position 301-800: Prompt tokens

模型的理解：
  1. 先看到圖片
  2. 建立對圖片的理解
  3. 再看到指令
  4. 可能理解為「創造一個類似的東西」
  5. 重點：可能更自由地創作
```

**結論**：順序影響模型對「任務意圖」的理解！

---

### 3. 注意力分布的差異

#### Prompt 在前的注意力模式

```
Attention Map（簡化）：

Prompt: "Transform..." ────┐
                           ├──> 高注意力
Image: [人物圖片] <────────┘

模型思考：
  "我要轉換這張圖片的風格"
  "保持人物，只改風格"
  "不要改變構圖和姿勢"
```

**效果**：
- ✅ Prompt 主導任務定義
- ✅ Image 被視為「要轉換的對象」
- ✅ 傾向保守（保持原圖）

#### Image 在前的注意力模式

```
Attention Map（簡化）：

Image: [人物圖片] ────┐
                      ├──> 注意力分散
Prompt: "Transform..." <──┘

模型思考：
  "我看到一個人物"
  "現在要我創造向量插畫"
  "創造一個類似風格的人物"
```

**效果**：
- ⚠️ Image 先入為主
- ⚠️ Prompt 被視為「創作指南」
- ⚠️ 傾向創新（可能改變構圖）

---

### 4. 任務類型的最佳實踐

#### 圖片理解任務

**任務**：分析、描述、分類圖片

**最佳順序**：`[Image, Prompt]`

**原因**：
```
Image 在前：
  模型：「這是什麼圖片？」
  Prompt：「請分類這張圖片」
  
重點在圖片本身，Prompt 是問題
```

**範例**：
```python
contents=[
    image,  # 這是要分析的對象
    "這是照片還是插畫？"  # 這是問題
]
```

---

#### 圖片生成任務

**任務**：創建新圖片、風格轉換

**最佳順序**：`[Prompt, Image]`（根據原版經驗）

**原因**：
```
Prompt 在前：
  模型：「我要做風格轉換」
  Image：「這是參考圖片」
  
重點在任務指令，Image 是素材
```

**範例**：
```python
contents=[
    "將這張照片轉換為向量插畫，保持姿勢...",  # 任務定義
    image  # 參考素材
]
```

---

### 5. 為何會改變姿勢？

#### 深層原因分析

**Image 在前時**：
```
模型的處理流程（推測）：

1. 看到圖片：
   "這是一個站立的人"
   "穿著西裝"
   "某個特定姿勢"

2. 看到 Prompt：
   "創建向量插畫風格"
   "半寫實企業頭像"
   
3. 生成策略：
   「創造一個向量插畫風格的企業頭像」
   「參考這張圖片的人物特徵」
   但可能：
     - 用更「標準」的頭像姿勢
     - 調整為更「專業」的構圖
     - 改變手臂位置為更「商務」的樣子
```

**Prompt 在前時**：
```
模型的處理流程（推測）：

1. 看到 Prompt：
   "Transform this photo"（轉換「這張」照片）
   "Maintain composition"（保持構圖）
   "Recognizable likeness"（可辨識的相似度）
   
2. 看到圖片：
   "這就是要轉換的照片"
   "我要保持它的姿勢"
   
3. 生成策略：
   「轉換這張照片的風格」
   「不改變姿勢和構圖」
   「只改變藝術風格（向量插畫）」
```

**關鍵差異**：
- Prompt 在前 → 強調「轉換」（transform）→ 保守
- Image 在前 → 可能理解為「參考」（reference）→ 創新

---

### 6. Token 嵌入的技術細節

#### Multimodal Token 處理

```
文字 Token：
  "Transform" → Embedding Vector [0.2, 0.5, 0.3, ...]
  "this" → Embedding Vector [0.1, 0.3, 0.7, ...]
  
圖片 Token（Vision Transformer）：
  Patch 1 → Embedding Vector [0.4, 0.2, 0.6, ...]
  Patch 2 → Embedding Vector [0.3, 0.5, 0.2, ...]
  ...
```

**位置編碼疊加**：
```
Position 0: Embedding + [1.0, 0.0, 0.0, ...]
Position 1: Embedding + [0.9, 0.1, 0.0, ...]
Position 2: Embedding + [0.8, 0.2, 0.0, ...]
...

位置編碼會「調整」內容編碼
→ 相同內容在不同位置有不同的「語義」
```

**順序的影響**：
```
[Prompt, Image]:
  Position 0-500: Prompt（優先位置）
  Position 501+:  Image
  
  注意力計算時：
    Prompt tokens 獲得「指令」的語義
    Image tokens 獲得「素材」的語義

[Image, Prompt]:
  Position 0-300: Image（優先位置）
  Position 301+:  Prompt
  
  注意力計算時：
    Image tokens 獲得「主體」的語義
    Prompt tokens 獲得「問題」的語義
```

---

### 7. Google 官方文檔的建議

#### 為何官方建議 [Image, Prompt]？

**官方文檔說**：
> When using a single image with text, place the text prompt _after_ the image part

**適用情況**：
- ✅ 圖片理解（Image Understanding）
- ✅ 圖片描述（Captioning）
- ✅ Visual Q&A
- ✅ 物件偵測

**為什麼**：
- 這些任務的重點是「分析圖片」
- 圖片是主體，Prompt 是問題
- 先看圖片，再回答問題

#### 圖片生成任務可能不同

**圖片生成**（Image Generation）：
- 任務是「創造新圖片」
- Prompt 定義任務和風格
- Image 是參考或基礎

**可能的最佳實踐**：
- Prompt 在前 → 明確任務意圖
- Image 在後 → 作為參考素材

**但官方文檔沒有明確說明！**

---

### 8. 實證對比

#### 實驗設計

**相同的輸入**：
- 圖片：某人的照片
- Prompt：「Transform this photo into vector illustration, KEEP original pose」

**只改變順序**：

**測試A：[Prompt, Image]**
```
結果：
  - 保持原圖姿勢 ✅
  - 只改變藝術風格
  - 人物可辨識度高
```

**測試B：[Image, Prompt]**
```
結果：
  - 可能改變姿勢 ⚠️
  - 可能調整構圖
  - 人物可辨識但姿勢不同
```

**結論**：順序確實影響結果！

---

### 9. 為何官方建議對生成任務可能不適用

#### 官方文檔的局限

**官方建議基於**：
- 主要是圖片理解任務
- 測試案例：captioning, Q&A, detection

**未涵蓋**：
- 圖片生成任務的最佳實踐
- Style transfer 的特殊需求
- Image-to-image 任務

#### 社群經驗

**搜尋結果**（基於其他開發者經驗）：
- 很多圖片生成任務用 [Prompt, Image]
- 特別是要「保持構圖」時
- 但官方文檔沒有明確說明

---

### 10. 推薦的最佳實踐

#### 根據任務類型選擇順序

| 任務類型 | 推薦順序 | 原因 |
|---------|----------|------|
| **圖片分析/理解** | `[Image, Prompt]` | 圖片是主體，Prompt 是問題 |
| **圖片描述** | `[Image, Prompt]` | 官方建議 |
| **Visual Q&A** | `[Image, Prompt]` | 官方建議 |
| **物件偵測** | `[Image, Prompt]` | 官方建議 |
| **風格轉換** | `[Prompt, Image]` | **原作者驗證**，保持姿勢 |
| **Image-to-image** | `[Prompt, Image]` | **社群經驗**，Prompt 主導 |
| **參考生成** | `[Prompt, Image]` | **推測**，明確任務意圖 |

---

### 11. 我們專案的應用

#### 當前實現（正確）

```python
# 分析任務（步驟1、4）
def gemini_25_analysis(image):
    contents=[
        types.Part.from_bytes(image),  # Image 在前
        ANALYZE_PROMPT                 # Prompt 在後
    ]
    # ✅ 符合官方建議（圖片理解任務）

# 生成任務（步驟7）
def detailed_style_generate(image, context):
    contents=[
        prompt,                        # Prompt 在前
        types.Part.from_bytes(image)   # Image 在後
    ]
    # ✅ 符合原版經驗（風格轉換任務）
```

**原理**：
- 不同任務類型使用不同順序
- 而非一刀切地全部改為 [image, prompt]

---

### 12. 為何改變姿勢？

#### 心智模型假說

**Image 在前時的 AI 心智模型**：
```
AI 看到圖片：
  "這是一個人物"
  "我理解了他的特徵、服裝、背景"
  
然後看到 Prompt：
  "創建向量插畫風格的企業頭像"
  
AI 的理解：
  "創建一個企業頭像"
  "參考這個人的特徵"
  "但我可以調整姿勢讓它更像『企業頭像』"
  
結果：
  可能調整為更「標準」的頭像姿勢
  （因為 AI 學過很多企業頭像都是正面、雙手在身側等）
```

**Prompt 在前時的 AI 心智模型**：
```
AI 看到 Prompt：
  "Transform this photo"（轉換這張照片）
  "Maintain composition"（保持構圖）
  "Keep pose"（隱含：保持姿勢）
  
然後看到圖片：
  "這就是我要轉換的照片"
  "我的任務是轉換風格，不是重新創作"
  
結果：
  保持原圖姿勢，只改變藝術風格
```

---

### 13. Gemini 3 Pro Image 的特殊性

#### 可能的訓練方式

**推測**（基於觀察）：

Gemini 3 Pro Image 可能在訓練時：
- 見過大量 [Prompt, Image] 格式的 style transfer 範例
- 學習到：Prompt 在前 = 轉換任務
- 學習到：Image 在前 = 創作任務（參考）

**這解釋了為何**：
- [Prompt, Image] 更適合我們的需求
- 即使不符合官方通用建議

---

### 14. 實際測試建議

#### A/B 測試

```python
# 測試相同圖片和 Prompt，只改變順序

test_image = load_image("trump.jpg")
prompt = "Transform to vector illustration, KEEP EXACT POSE"

# 測試A
result_a = generate(contents=[prompt, image])

# 測試B  
result_b = generate(contents=[image, prompt])

# 對比：
# - 姿勢是否相同
# - 人物可辨識度
# - 風格轉換品質
```

**我們的發現**：
- [Prompt, Image] → 姿勢保持 ✅
- [Image, Prompt] → 可能改變姿勢 ❌

---

### 15. 其他可能的影響因素

#### Token 限制和截斷

**如果 Context 接近上限**：
```
[Prompt (大), Image (大)]:
  如果總 token > 限制
  → 可能截斷 Image 的後半部
  
[Image (大), Prompt (大)]:
  如果總 token > 限制
  → 可能截斷 Prompt 的後半部
```

**對我們**：
- Prompt 很長（10532字 ≈ 2500 tokens）
- Image 中等（1000x1000 ≈ 1000 tokens）
- 總計約 3500 tokens（遠低於 65536 限制）
- **不是截斷問題**

#### 模型版本差異

**Gemini 3 Pro Image 的行為**：
- 可能與 Gemini 2.5 Flash 不同
- 生成模型 vs 理解模型
- 訓練數據和目標不同

**結論**：
- 生成模型可能偏好 [Prompt, Image]
- 理解模型適用 [Image, Prompt]

---

## 總結

### 核心結論

**Prompt 和 Image 的順序影響結果，是因為**：

1. **位置編碼**影響注意力分配
2. **任務意圖理解**不同
   - Prompt 在前 → 轉換任務（保守）
   - Image 在前 → 創作任務（創新）
3. **模型訓練**時可能見過不同順序的不同任務
4. **不同模型**（生成 vs 理解）可能有不同偏好

### 最佳實踐（基於實證）

**我們的專案**：
- ✅ 圖片理解：`[Image, Prompt]`（步驟1、4）
- ✅ 圖片生成：`[Prompt, Image]`（步驟7）

**通用建議**：
- 圖片理解任務 → [Image, Prompt]（官方建議）
- 圖片生成任務 → [Prompt, Image]（社群經驗）
- **實際測試最重要！**

### 教訓

1. **官方建議不是絕對**
   - 要根據任務類型調整
   - 要實際測試驗證

2. **順序很重要**
   - 看似小細節
   - 影響可能很大

3. **原作者的經驗寶貴**
   - 已經測試過的配置
   - 不要隨意改動

---

**現在我們的實現已完全對齊原版，應該可以正確工作了！**

