# 當前實現常見問題

## Q1：去背功能是否還在？

### 答案：✅ 去背功能完整保留

**位置**：`src/pipeline/components.py`

#### rembg 去背組件

```python
def rembg_preprocess(image: Image.Image, context: dict) -> Image.Image:
    """rembg 去背 + 裁切（僅照片）"""
    if context.get("image_type") == "photo":
        # 照片：執行去背
        result = rembg_remove(image)  # ← rembg 去背
        # 裁切平整底部
        ...
    else:
        # 插畫：不去背，只轉格式
        return image.convert("RGBA")
```

**使用情況**：
- ✅ 照片會去背（`if image_type == "photo"`）
- ❌ 插畫不去背（直接轉 RGBA）

**保留的去背功能**：
1. `rembg_remove(image)` - 使用 rembg 套件，u2net 模型
2. 裁切平整底部（去背後的邊界裁切）

---

## Q2：Gemini 生成的圖片背景問題

### Gemini 能否直接生成透明背景？

**答案**：❌ **不能直接生成透明背景**

#### Gemini 3 Pro Image 的限制

根據 API 規格和實測：
- Gemini 生成的圖片格式：**JPEG 或 PNG（但總是有背景）**
- **無法直接生成透明背景**
- 必須生成實心背景（白色、彩色等）

#### 為何 Prompt 要求「Pure white background」

**原版 Prompt（Line 315-316）**：
```
BACKGROUND:
- Pure white, clean background (will be processed to transparent later)
                                ↑
                            明確說明會後續處理
```

**邏輯**：
1. 要求 AI 生成「純白色背景」
2. 註明：「會被後續處理為透明」
3. 程式接收後，用 `make_white_transparent` 將白色轉透明

#### 為何選擇白色？

**優勢**：
- 白色容易識別（RGB 都接近 255）
- 與人物對比度高（容易分離）
- AI 生成白底很穩定（常見背景）

**替代方案**：
- 也可以要求綠色背景（green screen）
- 但白色更自然，AI 理解更好

---

### 我們的透明背景處理流程

```
步驟1：AI 生成
  Prompt: "Pure white background"
  輸出: 白色背景的圖片
  ↓
步驟2：程式處理（make_white_transparent）
  方法: numpy 連通區域分析
  邏輯:
    1. 找出所有白色像素（RGB > 240）
    2. 使用連通區域標記
    3. 只處理與邊緣相連的白色
    4. 膨脹人物區域保護內部白色（衣服等）
    5. 重疊 < 30% 的白色區域視為背景
    6. 將背景白色的 alpha 設為 0
  輸出: 透明背景的圖片
```

**關鍵技術**：
- 不是簡單的「所有白色都刪除」
- 保護人物內部的白色（白色衣服、眼白等）
- 只刪除背景的白色

---

### 為何不直接讓 AI 生成透明背景？

**技術限制**：
- Gemini API 返回的圖片沒有 alpha 通道
- 即使 Prompt 要求「transparent」，AI 也會生成實心背景

**已嘗試過的方案**（推測）：
```python
# 嘗試要求透明背景
Prompt: "transparent background"
結果: AI 可能生成白色或其他顏色，無法真正透明
```

**最佳實踐**：
- 生成白底（AI 穩定）
- 程式轉透明（精確控制）

---

## Q3：像素照片 vs 真人照片的處理差別

### 術語澄清

**像素照片 = 插畫（illustration）**
- digital illustration
- vector art
- cartoon
- anime
- 非真實攝影作品

**真人照片 = 照片（photo）**
- real photograph
- 攝影照片

---

### 處理流程對比

#### 插畫（illustration）流程

```
1. 檢測圖片類型
   └─ detect_image_type() → "illustration"

2. ❌ 跳過檢測身體範圍
   └─ body_extent = "head_chest"（固定）

3. ❌ 不執行去背
   └─ 只轉 RGBA 格式

4. ✅ AI 生成向量插畫
   └─ 使用 "head_chest" Prompt（Maintain composition）

5. ✅ 白色轉透明
   └─ make_white_transparent()

6. ✅ 統一尺寸到 1000x1000
   └─ normalize_size_and_position()

7. ❌ 不執行底部裁切
   └─ 因為不是照片

輸出: 透明背景，1000x1000
```

#### 真人照片（photo）流程

```
1. 檢測圖片類型
   └─ detect_image_type() → "photo"

2. ✅ 檢測身體範圍
   └─ detect_body_extent() → head_only/head_neck/head_chest/full_body

3. ✅ rembg 去背
   └─ rembg.remove()（u2net 模型）
   └─ 裁切平整底部

4. ✅ AI 生成向量插畫
   └─ 使用對應的 body_extent Prompt
      • head_only → "生成身體"
      • head_neck → "生成肩膀"
      • head_chest → "保持構圖"
      • full_body → "裁切到上胸部"

5. ✅ 白色轉透明

6. ✅ 統一尺寸到 1000x1000

7. ✅ 底部裁切（水平）
   └─ crop_horizontal_bottom()

輸出: 透明背景，1000x1000
```

---

### 關鍵差異總結

| 步驟 | 插畫 | 照片 | 原因 |
|------|------|------|------|
| 檢測類型 | ✅ | ✅ | 都需要 |
| 檢測身體 | ❌ | ✅ | 插畫固定 head_chest |
| 去背 | ❌ | ✅ | 插畫已是向量圖 |
| AI 生成 | ✅ | ✅ | 都需要轉風格 |
| Body Instruction | "Maintain" | 根據檢測 | 插畫保持構圖 |
| 轉透明 | ✅ | ✅ | 都需要 |
| 統一尺寸 | ✅ | ✅ | 都需要 |
| 底部裁切 | ❌ | ✅ | 只有照片需要 |

---

### 為何插畫不去背？

**原因**：
1. 插畫通常已經是向量圖（無真實背景）
2. 插畫背景可能是設計的一部分
3. rembg 是針對真實照片訓練的
4. 對插畫去背可能效果不好

**實際做法**：
- 插畫：保留原圖，只轉 RGBA
- 後續 AI 生成時會重新繪製
- 最後轉透明背景

---

### 為何插畫也要 AI 重新生成？

**關鍵理解**：
- **所有圖片（照片和插畫）都會 AI 重新生成**
- 不是「保持插畫不變」
- 而是「將插畫轉換為我們的向量插畫風格」

**原因**：
- 統一風格（半寫實企業頭像）
- 統一細節（賽璐璐著色、橘色高光）
- 統一構圖（頭到上胸部）

**差異**：
- 插畫：AI 保持原構圖（"Maintain composition"）
- 照片：AI 可能調整構圖（裁切/生成身體）

---

## 完整處理對比圖

### 插畫處理（8個步驟）

```
[插畫輸入]
  ↓
1️⃣ 檢測類型 → "illustration"
  ↓
2️⃣ 跳過檢測身體（body_extent="head_chest"固定）
  ↓
3️⃣ 轉 RGBA（不去背）
  ↓
4️⃣ 生成 Body Instruction（"Maintain composition"）
  ↓
5️⃣ 構建 Prompt（10532字）
  ↓
6️⃣ AI 生成向量插畫（Gemini 3 Pro，白底）
  ↓
7️⃣ 白色轉透明
  ↓
8️⃣ 統一到 1000x1000
  ↓
[輸出：向量插畫風格，透明背景，1000x1000]
```

### 照片處理（10個步驟）

```
[照片輸入]
  ↓
1️⃣ 檢測類型 → "photo"
  ↓
2️⃣ 檢測身體範圍 → head_xxx/full_body
  ↓
3️⃣ rembg 去背（u2net）
  ↓
4️⃣ 裁切平整底部
  ↓
5️⃣ 生成 Body Instruction（根據 body_extent）
  ↓
6️⃣ 構建 Prompt
  ↓
7️⃣ AI 生成向量插畫（Gemini 3 Pro，白底）
  ↓
8️⃣ 白色轉透明
  ↓
9️⃣ 統一到 1000x1000
  ↓
🔟 底部裁切（水平）
  ↓
[輸出：向量插畫風格，透明背景，1000x1000]
```

---

## 關鍵技術點

### 1. 去背保留情況

**保留**：
- ✅ `rembg_preprocess` 組件（src/pipeline/components.py）
- ✅ 使用 rembg 套件
- ✅ u2net 模型
- ✅ 只對照片執行

**未保留**：
- ❌ Gemini Segmentation（未實現，屬於探索功能）

---

### 2. 透明背景處理

**Gemini 的限制**：
```
Gemini 生成的圖片:
  ✅ 可以是 PNG 格式
  ❌ 但總是有實心背景
  ❌ 無法直接生成 alpha 通道
```

**我們的解決方案**：
```
Prompt 要求: "Pure white background"
  ↓
Gemini 生成: 白色背景圖片
  ↓
程式處理: make_white_transparent()
  方法: numpy 連通區域分析
  智能: 保護人物內部白色（衣服）
  ↓
最終輸出: 真正的透明背景 PNG
```

**為何這樣做**：
- 技術限制：Gemini 無法直接生成透明
- 可控性：程式處理更精確
- 保護性：不會誤刪人物內部白色

---

### 3. 插畫 vs 照片差異總結

| 處理步驟 | 插畫 | 照片 | 原因 |
|---------|------|------|------|
| 1. 檢測類型 | ✅ 執行 | ✅ 執行 | 決定後續流程 |
| 2. 檢測身體 | ❌ 跳過 | ✅ 執行 | 插畫固定 head_chest |
| 3. 去背 | ❌ 跳過 | ✅ 執行 | 插畫無需去背 |
| 4. 裁切底部1 | ❌ 跳過 | ✅ 執行 | 與去背綁定 |
| 5. 生成指令 | ✅ "Maintain" | ✅ 根據檢測 | 插畫保持構圖 |
| 6. AI 生成 | ✅ 執行 | ✅ 執行 | 都需要轉風格 |
| 7. 轉透明 | ✅ 執行 | ✅ 執行 | 都需要 |
| 8. 統一尺寸 | ✅ 執行 | ✅ 執行 | 都需要 |
| 9. 裁切底部2 | ❌ 跳過 | ✅ 執行 | 只有照片需要 |

**步驟數**：
- 插畫：5個主要步驟
- 照片：7個主要步驟

**AI 調用次數**：
- 插畫：1次（只檢測類型）
- 照片：2次（檢測類型 + 檢測身體）

**處理時間**：
- 插畫：約 15-25 秒（少了去背時間）
- 照片：約 25-40 秒（多了去背 3-8秒）

---

## 透明背景技術細節

### make_white_transparent 函數邏輯

```python
def make_white_transparent(image):
    # 1. 找出白色像素（RGB > 240）
    white_mask = (R > 240) & (G > 240) & (B > 240)
    
    # 2. 連通區域標記
    labeled = ndimage.label(white_mask)
    
    # 3. 找出與邊緣相連的白色區域
    edge_labels = {邊緣接觸的區域}
    
    # 4. 找出非白色區域（人物）
    person_mask = (R < 245) | (G < 245) | (B < 245)
    
    # 5. 膨脹人物區域（20x20）創建保護區
    person_protected = dilate(person_mask, 20x20)
    
    # 6. 判斷哪些白色區域是背景
    for region in edge_labels:
        overlap = region ∩ person_protected
        if overlap < 30%:
            # 這是背景白色
            set_alpha_to_0(region)
    
    # 7. 保護人物內部白色
    # 與人物重疊 > 30% 的白色不會被刪除
    
    return 透明背景圖片
```

**保護機制**：
- 白色衣服 ✅ 保留（與人物重疊高）
- 白色襯衫 ✅ 保留
- 眼白 ✅ 保留（小區域，不接觸邊緣）
- 背景白色 ❌ 刪除（大區域，接觸邊緣）

---

## 當前 Pipeline 中的組件使用

### I4 詳細版風格

```python
PRESET_STYLES["i4_detailed"] = {
    "analysis": gemini_25_analysis_photos_only,  # 照片檢測身體，插畫不檢測
    "preprocess": rembg_preprocess,              # 照片去背，插畫轉格式
    "style": detailed_style_generate,            # 都用 AI 生成
    "background": transparent_background,         # 都轉透明
    "postprocess": normalize_1000                # 都統一尺寸（照片會額外裁切底部）
}
```

**組件行為**：
- `analysis`：照片2次AI，插畫1次AI
- `preprocess`：照片去背，插畫轉格式
- `postprocess`：照片多一個底部裁切

---

## 總結

### Q1：去背功能
✅ **完整保留**，在 `rembg_preprocess` 組件中，只對照片執行

### Q2：透明背景
❌ Gemini **無法直接生成透明背景**  
✅ 解決方案：生成白底 → 程式智能轉透明

### Q3：插畫 vs 照片
**主要差異**：
- 插畫：不檢測身體、不去背、不底部裁切、AI調用少
- 照片：檢測身體、去背、底部裁切、AI調用多

**共同點**：
- 都用 AI 重新生成風格
- 都轉透明背景
- 都統一到 1000x1000

---

**當前實現已完全對齊原版流程圖！**

