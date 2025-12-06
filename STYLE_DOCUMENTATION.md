# 圖片風格轉換 - 完整生圖流程和 Prompt 文檔

## 📋 目錄

1. [完整生圖流程](#完整生圖流程)
2. [API 調用優化](#api-調用優化)
3. [Prompt 詳細說明](#prompt-詳細說明)
4. [後處理流程](#後處理流程)

---

## 🔄 完整生圖流程

### 步驟 1：圖片分析（合併檢測）

**方法**：`analyze_image(image)`

**API 調用次數**：1 次

**功能**：同時檢測圖片類型和身體範圍

```python
analysis = self.analyze_image(image)
image_type = analysis["image_type"]  # "photo" 或 "illustration"
body_extent = analysis["body_extent"]  # "head_only", "head_neck", "head_chest", "full_body"
```

**使用的 Prompt**：`ANALYZE_PROMPT`

```
Analyze this image:

1. TYPE: Is this a PHOTO or ILLUSTRATION?
2. BODY: What body parts are visible?
   - HEAD_ONLY: Face/head only
   - HEAD_NECK: Head + neck, no shoulders
   - HEAD_CHEST: Head to upper chest
   - FULL_BODY: Waist or below visible

Response format (exactly 2 lines):
TYPE: [PHOTO/ILLUSTRATION]
BODY: [HEAD_ONLY/HEAD_NECK/HEAD_CHEST/FULL_BODY]
```

**返回結果**：
- `image_type`: 圖片類型（"photo" 或 "illustration"）
- `body_extent`: 身體範圍（"head_only", "head_neck", "head_chest", "full_body"）

---

### 步驟 2：AI 風格轉換

**方法**：`convert_to_cartoon_illustration(image, body_extent)`

**API 調用次數**：1 次

**功能**：將照片/插畫轉換為向量插畫風格

**使用的 Prompt**：根據 `body_extent` 動態生成（見下方詳細說明）

**模型**：`gemini-3-pro-image-preview`

**返回**：轉換後的插畫圖片（白色背景）

---

### 步驟 3：後處理

#### 3.1 透明背景處理

**方法**：`make_white_transparent(image, threshold=240)`

**功能**：將白色背景轉為透明

**邏輯**：
1. 找出接近純白色的像素（RGB > 240）
2. 使用連通區域標記
3. 找出與邊緣接觸的白色區域
4. 保護人物內部（膨脹人物遮罩 20px）
5. 只移除邊緣連通且與保護區域重疊 < 30% 的白色區域

#### 3.2 統一尺寸和位置

**方法**：`normalize_size_and_position(image, target_size=(1000, 1000), head_ratio=0.35)`

**功能**：確保所有輸出圖片一致

**邏輯**：
1. 固定人物高度為目標高度的 70%
2. 固定人物寬度為目標寬度的 85%
3. 水平置中：人物中心對齊畫布中心
4. 垂直定位：頭部在畫面上方 35% 位置
5. 左右各保留 5% 邊距

#### 3.3 水平底部裁切（僅真人照片）

**方法**：`crop_horizontal_bottom(image)`

**功能**：將底部裁切成水平

**邏輯**：
1. 檢測人物中心 1/3 區域的最低點（身體底部，排除手部）
2. 將底部以下設為透明

---

## ⚡ API 調用優化

### 優化前（3 次 API 調用）

1. `detect_image_type()` - 檢測圖片類型
2. `detect_body_extent()` - 檢測身體範圍
3. `convert_to_cartoon_illustration()` - 風格轉換

### 優化後（2 次 API 調用）

1. `analyze_image()` - **合併檢測**（一次返回 type + body_extent）
2. `convert_to_cartoon_illustration()` - 風格轉換

**優化效果**：
- API 配額節省：**33%**
- 處理時間減少：**33%**
- 成本降低：**33%**

---

## 📝 Prompt 詳細說明

### 主 Prompt 模板

```
Transform this photo into a VECTOR ILLUSTRATION.

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
- Frame: Head to upper chest only
```

### 身體構圖指令（根據檢測結果動態選擇）

#### full_body（全身照）

```
## COMPOSITION
- INPUT: Full body photo
- ACTION: Crop to HEAD → UPPER CHEST only
- Remove: waist, legs, lower body
```

#### head_only（只有頭部）

```
## COMPOSITION  
- INPUT: Head/face only
- ACTION: Generate neck, shoulders, upper chest
- Extend naturally to create head-to-chest composition
```

#### head_neck（頭部到脖子）

```
## COMPOSITION
- INPUT: Head and neck only  
- ACTION: Generate shoulders and upper chest
- Extend naturally below neck
```

#### head_chest（頭部到胸部）

```
## COMPOSITION
- INPUT: Head to upper chest (ideal)
- ACTION: Maintain current framing
- Ensure bottom edge at upper chest level
```

---

## 🎨 風格特徵詳解

### 1. 向量插畫風格

- **類型**：半寫實企業頭像（Semi-realistic corporate avatar）
- **渲染方式**：乾淨的向量藝術，賽璐璐著色（cel-shaded）
- **線條**：乾淨、精確的向量藝術線條品質

### 2. 色彩處理

- **風格**：扁平實色塊（Flat solid blocks）
- **禁止**：形狀內不使用漸層
- **對比**：高對比，強烈的明暗對比

### 3. 光影處理

- **陰影**：硬邊緣（Hard edges），清晰的邊界
- **高光**：選擇性橘色/金色邊緣光
  - 顏色：溫暖的橘金色（RGB 約 255, 165, 45）
  - 光源：背後，隨機角度
  - 覆蓋範圍：**僅 2-3 個關鍵邊緣**（例如：頭髮頂部、一個肩膀）
  - 風格：輕微光暈，局部化，不連續
  - **禁止**：不要高光整個輪廓

### 4. 比例和表情

- **比例**：寫實比例，不誇張
- **表情**：自信、專業
- **特徵**：不誇大面部特徵

### 5. 構圖要求

- **範圍**：頭部到上胸部（upper chest）
- **背景**：純白色（後續處理為透明）
- **禁止**：不顯示上胸部以下的身體部分

---

## 🔧 後處理流程詳解

### 1. 透明背景處理 (`make_white_transparent`)

**目的**：將 AI 生成的白色背景轉為透明

**步驟**：
1. 找出接近純白色的像素（RGB > 240）
2. 使用連通區域標記（`ndimage.label`）
3. 找出與邊緣接觸的白色區域
4. 保護人物內部：
   - 找出非白色區域（人物遮罩）
   - 膨脹人物遮罩 20px，創建保護區域
5. 只移除邊緣連通且與保護區域重疊 < 30% 的白色區域

**參數**：
- `threshold = 240`：白色檢測閾值
- `person_mask_threshold = 245`：人物區域檢測閾值
- `dilation_size = 20`：保護區域膨脹大小
- `overlap_threshold = 0.3`：重疊判斷閾值（30%）

### 2. 統一尺寸和位置 (`normalize_size_and_position`)

**目的**：確保所有輸出圖片的人物大小和位置一致

**步驟**：
1. 檢測人物邊界（非透明區域）
2. 計算人物尺寸（高度、寬度）
3. 固定人物大小比例：
   - 高度：目標高度的 70%
   - 寬度：目標寬度的 85%
4. 計算縮放比例（取較小值，確保完整顯示）
5. 縮放圖片
6. 定位到畫布：
   - **水平**：人物中心對齊畫布中心
   - **垂直**：頭部在畫面上方 35% 位置
   - **邊距**：左右各 5%

**參數**：
- `target_size = (1000, 1000)`：目標尺寸
- `head_ratio = 0.35`：頭部位置比例（35%）
- `target_person_height_ratio = 0.70`：人物高度比例（70%）
- `target_person_width_ratio = 0.85`：人物寬度比例（85%）
- `side_margin_ratio = 0.05`：左右邊距比例（5%）

### 3. 水平底部裁切 (`crop_horizontal_bottom`)

**目的**：將底部裁切成水平，但保留手部

**步驟**：
1. 檢測人物區域（非透明區域）
2. 找出人物寬度的中心 1/3 區域（身體部分，排除側邊的手部）
3. 在中心區域找出最低點（身體底部）
4. 將身體底部以下的所有內容設為透明（水平裁切）

**適用條件**：僅真人照片（`image_type == "photo"`）

---

## 📊 完整流程圖

```
輸入圖片
    ↓
[步驟 1] analyze_image() - 合併檢測（1 次 API 調用）
    ├─ 檢測圖片類型 (photo/illustration)
    └─ 檢測身體範圍 (head_only/head_neck/head_chest/full_body)
    ↓
[步驟 2] convert_to_cartoon_illustration() - 風格轉換（1 次 API 調用）
    ├─ 根據 body_extent 選擇構圖指令
    ├─ 生成向量插畫風格
    └─ 返回白色背景的插畫圖片
    ↓
[步驟 3] 後處理
    ├─ make_white_transparent() - 透明背景處理
    ├─ normalize_size_and_position() - 統一尺寸和位置
    └─ crop_horizontal_bottom() - 水平底部裁切（僅真人照片）
    ↓
輸出圖片（透明背景，統一尺寸，水平底部）
```

---

## 🎯 關鍵參數總結

### API 配置
- **模型**：`gemini-3-pro-image-preview`
- **API 調用次數**：2 次（優化後）
  - 1 次：圖片分析（合併檢測）
  - 1 次：風格轉換

### 圖片處理參數
- **目標尺寸**：1000 x 1000 像素
- **人物高度比例**：70%
- **人物寬度比例**：85%
- **頭部位置比例**：35%（從頂部）
- **左右邊距**：各 5%

### 背景處理參數
- **白色檢測閾值**：240
- **人物保護閾值**：245
- **保護區域膨脹**：20px
- **重疊判斷閾值**：30%

---

## 📌 注意事項

1. **API 配額**：每次處理需要 2 次 API 調用
2. **處理時間**：取決於 API 響應速度，通常 10-30 秒
3. **輸出格式**：PNG（支援透明背景）
4. **構圖**：所有輸出都是頭部到上胸部
5. **高光效果**：選擇性、局部化，僅 2-3 個關鍵邊緣
6. **背景**：自動處理為透明

---

## 🔍 除錯技巧

1. **背景去背失敗**：調整 `threshold` 參數（240-250）
2. **人物被切割**：檢查 `normalize_size_and_position` 的邊距設定
3. **底部不水平**：確認 `crop_horizontal_bottom` 在統一尺寸之後執行
4. **人物大小不一致**：檢查固定比例設定（70% 高度，85% 寬度）
5. **高光過多**：檢查 prompt 中的選擇性高光指令

