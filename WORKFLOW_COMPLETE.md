# 完整處理流程分析（整合版本）

本文檔整合了所有流程分析，基於實際代碼追蹤。

## 快速參考

**照片路徑**：10個步驟（3個AI + 7個程式）- 25-50秒  
**插畫路徑**：8個步驟（3個AI + 5個程式）- 20-40秒

---

## 實際執行順序（照片 - 10步驟）

| 步驟 | 名稱 | 類型 | 函數/工具 | 詳細說明 | 耗時 | 進度% |
|------|------|------|-----------|----------|------|-------|
| **1** | 檢測圖片類型 | 🤖 AI | `GeminiClient.analyze_image_type()` | 調用 Gemini 2.0 Flash，解析回應 | ~3秒 | 4% |
| **2** | 去背處理 | 💻 程式 | `ImageProcessor.remove_background()` | 使用 rembg 套件，u2net 深度學習模型 | 3-8秒 | 12% |
| **3** | 裁切平整底部 | 💻 程式 | `ImageProcessor.crop_to_flat_bottom()` | numpy alpha通道分析，裁切非透明區域邊界 | <0.1秒 | 1% |
| **4** | 檢測身體範圍 | 🤖 AI | `StyleConverter.analyze_image()` | ⚠️ 重複檢測類型+檢測身體部位 | ~3秒 | 4% |
| **5** | 生成處理指令 | 💻 程式 | `BODY_INSTRUCTIONS[body_extent]` | 查表取得對應指令（裁切/生成/保持） | <0.01秒 | 1% |
| **6** | 構建AI Prompt | 💻 程式 | `get_style_prompt(body_extent)` | 組合 Body Instruction + 風格要求，約600字 | <0.01秒 | 1% |
| **7** | AI生成插畫 | 🤖 AI | `convert_to_cartoon_illustration()` | Gemini 3 Pro Image生成向量插畫+賽璐璐+高光 | 15-30秒 | 65% |
| **8** | 白色轉透明 | 💻 程式 | `make_white_transparent()` | numpy連通區域分析，閾值240，保護人物內部白色 | 1-2秒 | 6% |
| **9** | 統一尺寸位置 | 💻 程式 | `normalize_size_and_position()` | 調整到1000x1000，頭部35%，人物70%高85%寬 | <0.5秒 | 3% |
| **10** | 底部裁切 | 💻 程式 | `crop_horizontal_bottom()` | numpy找中心區域(寬度1/3)最低點，水平裁切 | <0.1秒 | 3% |

**總耗時**：25-50秒 | **AI調用**：3次（步驟1 + 步驟4重複 + 步驟7）

---

## 實際執行順序（插畫 - 8步驟）

| 步驟 | 名稱 | 類型 | 函數/工具 | 詳細說明 | 耗時 | 進度% |
|------|------|------|-----------|----------|------|-------|
| **1** | 檢測圖片類型 | 🤖 AI | `analyze_image_type()` | Gemini 2.0 Flash | ~3秒 | 7% |
| **2** | 格式轉換 | 💻 程式 | `convert("RGBA")` | PIL格式轉換 | <0.1秒 | 1% |
| **3** | 檢測身體範圍 | 🤖 AI | `analyze_image()` | ⚠️ 重複檢測，body_extent強制="head_chest" | ~3秒 | 7% |
| **4** | 生成處理指令 | 💻 程式 | `BODY_INSTRUCTIONS["head_chest"]` | 取得保持構圖指令 | <0.01秒 | 1% |
| **5** | 構建Prompt | 💻 程式 | `get_style_prompt()` | 組合完整Prompt | <0.01秒 | 1% |
| **6** | AI生成插畫 | 🤖 AI | `convert_to_cartoon_illustration()` | Gemini 3 Pro Image生成 | 15-30秒 | 75% |
| **7** | 白色轉透明 | 💻 程式 | `make_white_transparent()` | numpy連通區域，閾值240 | 1-2秒 | 5% |
| **8** | 統一尺寸 | 💻 程式 | `normalize_size_and_position()` | 1000x1000，頭部35% | <0.5秒 | 3% |

**總耗時**：20-40秒 | **AI調用**：3次

---

## 代碼調用鏈完整追蹤

### app.py 主流程
```python
def process_image(image):
    # === 步驟 1 ===
    client = get_gemini_client()
    image_type = client.analyze_image_type(image)  # AI調用
    
    # === 步驟 2-3 ===（去背在這裡！不是後處理！）
    processed = image_processor.process_image(image, image_type)
    
    # === 步驟 4-10 ===
    result = style_converter.apply_style(processed, transparent_bg=True)
    
    return result
```

### ImageProcessor.process_image()
```python
def process_image(self, image, image_type):
    if image_type == ImageType.REAL_PHOTO:
        # 步驟 2：去背
        processed = self.remove_background(image)  # rembg去背，3-8秒
        # 步驟 3：裁切
        processed = self.crop_to_flat_bottom(processed)  # numpy裁切，<0.1秒
    else:
        # 步驟 2：格式轉換
        processed = image.convert("RGBA")  # <0.1秒
    
    return processed
```

### StyleConverter.apply_style()
```python
def apply_style(self, image, transparent_bg=True, normalize_size=True, ...):
    # 步驟 4：檢測身體範圍（⚠️ 同時重複檢測類型）
    analysis = self.analyze_image(image)  # AI調用，~3秒
    image_type = analysis["image_type"]
    body_extent = analysis["body_extent"]
    
    if image_type == "illustration":
        # 步驟 5-6 隱藏在 convert_to_cartoon_illustration 內部
        # 步驟 7：AI生成
        result = self.convert_to_cartoon_illustration(image, body_extent="head_chest")
        # （內部執行：查表→構建Prompt→調用Gemini 3 Pro→提取圖片）
        
        # 步驟 8：轉透明
        if transparent_bg:
            result = self.make_white_transparent(result)  # numpy，1-2秒
    else:
        # 照片分支同上
        result = self.convert_to_cartoon_illustration(image, body_extent=body_extent)
        if transparent_bg:
            result = self.make_white_transparent(result)
    
    # 步驟 9：統一尺寸
    if normalize_size:
        result = self.normalize_size_and_position(result, target_size=(1000,1000))
    
    # 步驟 10：底部裁切（僅照片）
    if image_type == "photo" and normalize_size:
        result = self.crop_horizontal_bottom(result)
    
    return result
```

---

## 身體範圍分類（4種）

根據 `ANALYZE_PROMPT` 和 `BODY_INSTRUCTIONS`：

### 1. HEAD_ONLY（僅頭部）
- **檢測**：只看到臉/頭部
- **AI指令**：生成脖子、肩膀、上胸部
- **效果**：從頭部照擴展到半身像

### 2. HEAD_NECK（頭部+脖子）
- **檢測**：有頭部和脖子，沒有肩膀
- **AI指令**：生成肩膀和上胸部
- **效果**：補充肩膀區域

### 3. HEAD_CHEST（頭到上胸，理想）
- **檢測**：頭部到上胸部可見
- **AI指令**：保持當前構圖
- **效果**：維持不變

### 4. FULL_BODY（全身照）
- **檢測**：腰部以下可見
- **AI指令**：裁切到頭部→上胸部
- **效果**：移除下半身

---

## 模型版本（2025-12-06確認）

### 當前配置
```python
model_image = "gemini-3-pro-image-preview"  # 圖片生成
model_text = "gemini-2.0-flash"             # 文本分析
```

### 版本確認

**Gemini 3 Pro Image Preview**：
- ✅ 發布日期：2025-11-20
- ✅ 狀態：Public Preview
- ✅ Knowledge cutoff：January 2025
- ✅ 這是最新的圖片生成模型

**Gemini 2.0 Flash**：
- ⚠️ 知識截止：2024年8月
- ⚠️ 可能有 Gemini 2.5 Flash 可用
- 建議：檢查是否升級

**來源**：[Google Cloud - Gemini 3 Pro Image文檔](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-pro-image)

---

## 重複API調用問題

### 問題分析

```
app.py:
  步驟1: analyze_image_type()  → 返回：image_type

apply_style:
  步驟4: analyze_image()       → 返回：image_type + body_extent
                                        ↑
                                  重複檢測 image_type！
```

**浪費**：1次API調用（約3秒 + API配額）

### 優化方案

**方案 A：在 app.py 直接調用 analyze_image()**
```python
# 改為：
analysis = style_converter.analyze_image(image)  # 一次調用取得兩個結果
image_type = analysis["image_type"]
body_extent = analysis["body_extent"]

processed = image_processor.process_image(image, ImageType(image_type))
result = style_converter.apply_style_optimized(processed, body_extent, ...)
```

**方案 B：讓 apply_style 接受已分析的結果**
```python
def apply_style(self, image, analysis=None, ...):
    if analysis is None:
        analysis = self.analyze_image(image)
    # 使用 analysis...
```

**節省**：33% API配額 + ~3秒處理時間

---

## 條件分支點

### 分支 1：圖片類型
```
if image_type == "illustration":
    # 插畫路徑（8步驟）
    # 步驟2：格式轉換
    # 無步驟10
else:
    # 照片路徑（10步驟）
    # 步驟2-3：去背+裁切
    # 有步驟10
```

### 分支 2：透明背景
```
if transparent_bg == True:  # 預設True
    result = make_white_transparent(result)  # 步驟8
else:
    # 跳過步驟8
```

### 分支 3：統一尺寸
```
if normalize_size == True:  # 預設True
    result = normalize_size_and_position(result)  # 步驟9
    
    if image_type == "photo":
        result = crop_horizontal_bottom(result)  # 步驟10
```

---

## AI vs 程式處理統計

### 照片路徑
- **AI處理**：步驟1（檢測類型）+ 步驟4（檢測身體）+ 步驟7（生成插畫）
- **程式處理**：步驟2（去背）+ 步驟3（裁切）+ 步驟5-6（指令）+ 步驟8-10（後處理）
- **AI耗時**：~21秒（佔80%）
- **程式耗時**：~5-11秒（佔20%）

### 插畫路徑
- **AI處理**：步驟1 + 步驟3 + 步驟6
- **程式處理**：步驟2 + 步驟4-5 + 步驟7-8
- **AI耗時**：~21秒（佔95%）
- **程式耗時**：~2秒（佔5%）

---

## 詳細步驟說明

### 步驟1：檢測圖片類型
- **函數**：`GeminiClient.analyze_image_type()`
- **模型**：Gemini 2.0 Flash
- **Prompt**：判斷 REAL_PHOTO 或 PIXEL_ART
- **輸出**：ImageType枚舉
- **位置**：app.py

### 步驟2：去背處理（照片）或格式轉換（插畫）
**照片分支**：
- **函數**：`ImageProcessor.remove_background()`
- **工具**：rembg 套件
- **模型**：u2net 深度學習模型
- **處理**：移除背景，保留人物
- **輸出**：RGBA 透明背景圖片

**插畫分支**：
- **函數**：`image.convert("RGBA")`
- **處理**：簡單格式轉換
- **輸出**：RGBA 格式圖片

### 步驟3：裁切平整底部（僅照片）
- **函數**：`ImageProcessor.crop_to_flat_bottom()`
- **方法**：numpy alpha通道分析
- **處理**：找出非透明區域邊界，裁切到邊界
- **效果**：去除多餘透明區域

### 步驟4：檢測身體範圍
- **函數**：`StyleConverter.analyze_image()`
- **模型**：Gemini 2.0 Flash
- **Prompt**：`ANALYZE_PROMPT`（同時檢測類型+身體）
- **輸出**：`{image_type, body_extent}`
- **⚠️ 問題**：重複檢測了類型（步驟1已檢測）
- **位置**：apply_style 內部

### 步驟5：生成Body Instruction
- **函數**：查表 `BODY_INSTRUCTIONS[body_extent]`
- **輸入**：body_extent（步驟4的輸出）
- **輸出**：對應的處理指令文字
- **選項**：
  - full_body → 裁切指令
  - head_only → 生成身體指令
  - head_neck → 生成肩膀指令
  - head_chest → 保持指令
- **位置**：convert_to_cartoon_illustration 內部（隱藏）

### 步驟6：構建完整Prompt
- **函數**：`get_style_prompt(body_extent)`
- **處理**：`STYLE_PROMPT.format(body_instruction=...)`
- **包含**：
  - Body Instruction（步驟5）
  - Style Requirements（向量插畫、賽璐璐）
  - Rim Lighting（橘色高光）
  - Constraints（禁止事項）
- **輸出**：約600字完整Prompt
- **位置**：convert_to_cartoon_illustration 內部（隱藏）

### 步驟7：AI生成向量插畫
- **函數**：`StyleConverter.convert_to_cartoon_illustration()`
- **模型**：Gemini 3 Pro Image Preview
- **輸入**：Prompt（步驟6）+ 預處理後的圖片
- **處理**：AI生成向量插畫風格
- **風格特色**：
  - 半寫實企業頭像
  - 賽璐璐著色（cel-shaded）
  - 橘色/金色邊緣高光（隨機角度）
  - 扁平色彩，硬陰影
  - 白色背景
- **輸出**：向量插畫圖片（白色背景）
- **耗時**：15-30秒（最耗時！）

### 步驟8：白色背景轉透明
- **函數**：`StyleConverter.make_white_transparent()`
- **方法**：numpy 連通區域標記（ndimage.label）
- **閾值**：240（RGB都>240視為白色）
- **邏輯**：
  1. 找出與邊緣相連的白色區域
  2. 膨脹人物區域20x20作為保護
  3. 重疊<30%的區域視為背景
  4. 將背景白色設為透明
- **保護**：人物內部白色（衣服等）不會被刪除
- **輸出**：透明背景圖片

### 步驟9：統一尺寸和位置
- **函數**：`StyleConverter.normalize_size_and_position()`
- **目標尺寸**：1000x1000
- **參數**：
  - head_ratio: 0.35（頭部在畫面上方35%）
  - person_height_ratio: 0.70（人物高度佔70%）
  - person_width_ratio: 0.85（人物寬度佔85%）
  - side_margin_ratio: 0.05（左右各5%留白）
- **處理**：創建畫布，調整人物大小，置中，固定頭部位置
- **輸出**：1000x1000標準化圖片

### 步驟10：水平底部裁切（僅照片）
- **函數**：`StyleConverter.crop_horizontal_bottom()`
- **條件**：image_type=="photo" AND normalize_size==True
- **方法**：
  1. 找出人物寬度中心1/3區域
  2. 在中心區域找最低非透明點
  3. 將該點以下全部設為透明
- **效果**：底部平整的水平邊緣
- **輸出**：裁切後的圖片

---

## 關鍵發現

### ⚠️ 重大問題

1. **重複API調用**：
   - 步驟1調用 `analyze_image_type()`
   - 步驟4調用 `analyze_image()`（包含類型檢測）
   - **浪費**：1次API調用，約3秒，33%配額

2. **步驟被隱藏**：
   - 步驟5-6 在 `convert_to_cartoon_illustration` 內部
   - 用戶看不到這兩步在做什麼

3. **進度分配不準確**：
   - 步驟7佔65-75%時間
   - 但進度顯示可能不夠細緻

### ✅ 優勢

1. **模組化設計**：每個函數職責清楚
2. **錯誤處理**：有重試機制
3. **參數可配置**：透明背景、統一尺寸等可選

---

## 優化建議（優先級排序）

### P0 - 立即修復
1. **消除重複API調用**
   - 修改 app.py，直接調用 `analyze_image()`
   - 修改 `apply_style` 接受已分析的結果
   - 節省：33% API配額，~3秒

### P1 - 重要改進
2. **暴露隱藏步驟**
   - 在前端顯示步驟5-6的處理
   - 讓用戶知道 AI 在做什麼準備工作

3. **模型版本檢查**
   - 確認是否有 Gemini 2.5 Flash
   - 如果有且更好，升級

### P2 - 體驗優化
4. **細化AI生成進度**
   - 步驟7內部模擬更細緻的進度
   - 每2-3秒更新一次

5. **添加取消功能**
   - WebSocket支持，可中斷處理

---

## 文檔對照

本文檔整合了以下內容：
- COMPLETE_WORKFLOW.md（用戶更新版）
- ACTUAL_EXECUTION_ORDER.md（代碼追蹤）
- CORRECT_WORKFLOW.md（正確流程）

整合後保留所有關鍵資訊，更完整準確。

