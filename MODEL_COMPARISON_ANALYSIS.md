# 模型使用分析與建議

基於 [Gemini API 圖片理解官方文檔](https://ai.google.dev/gemini-api/docs/image-understanding)（更新日期：2025-11-18）

---

## 關鍵發現

### 🔍 Google 最先進的圖片理解模型

根據官方文檔，Gemini 模型演進：

| 模型版本 | 發布時間 | 圖片理解能力 |
|----------|----------|--------------|
| **Gemini 2.5 Flash/Pro** | 2025年 | ✅ 增強的 object detection + **segmentation** |
| **Gemini 2.0 Flash** | 2024年 | ✅ 增強的 object detection |
| Gemini 1.5 Flash/Pro | 2024年 | ✅ 基本 multimodal 能力 |

**最新推薦**：`gemini-2.5-flash` 或 `gemini-2.5-pro`

**文檔中的示例代碼都使用**：
```python
model='gemini-2.5-flash'  # 最新推薦
```

---

## 我們當前的實現

### 當前配置（src/config.py）

```python
model_image = "gemini-3-pro-image-preview"  # 圖片生成
model_text = "gemini-2.0-flash"             # 文本分析（包括圖片理解）
```

### 用途分析

| 步驟 | 任務 | 當前使用模型 | 任務類型 |
|------|------|-------------|---------|
| 步驟1 | 檢測圖片類型 | `gemini-2.0-flash` | 🔍 圖片理解 |
| 步驟4 | 檢測身體範圍 | `gemini-2.0-flash` | 🔍 圖片理解 |
| 步驟7 | 生成向量插畫 | `gemini-3-pro-image-preview` | 🎨 圖片生成 |

---

## 重大發現：我們混淆了兩種不同的任務

### 圖片理解 vs 圖片生成

#### 圖片理解（Image Understanding）
- **用途**：分析、描述、檢測圖片中的內容
- **任務**：captioning, classification, object detection, segmentation
- **輸出**：文字或 JSON（描述圖片）
- **推薦模型**：`gemini-2.5-flash`（理解能力最強）

#### 圖片生成（Image Generation）
- **用途**：創建新的圖片
- **任務**：text-to-image, image-to-image, style transfer
- **輸出**：圖片
- **推薦模型**：`gemini-3-pro-image-preview`（生成能力）

### 我們的使用情況

**步驟1、4（圖片理解任務）**：
- ✅ 正確地使用了理解模型（`gemini-2.0-flash`）
- ⚠️ 但不是最新版本

**步驟7（圖片生成任務）**：
- ✅ 正確地使用了生成模型（`gemini-3-pro-image-preview`）
- ✅ 這是最新的生成模型

---

## 詳細對比

### 當前實現 vs 最佳實踐

#### 步驟1、4：檢測類型和身體範圍

**當前實現**：
```python
model = "gemini-2.0-flash"  # 2024年的模型

prompt = """Analyze this image:
1. TYPE: Is this a PHOTO or ILLUSTRATION?
2. BODY: What body parts are visible?
..."""

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=[prompt, image],
    config=types.GenerateContentConfig(
        response_modalities=['TEXT']
    )
)
```

**最佳實踐（根據2025-11-18文檔）**：
```python
model = "gemini-2.5-flash"  # ✅ 最新模型（2025年）

# 官方推薦的寫法
from google import genai
from google.genai import types

client = genai.Client()
response = client.models.generate_content(
    model='gemini-2.5-flash',  # 最新
    contents=[
        types.Part.from_bytes(
            data=image_bytes,
            mime_type='image/jpeg'
        ),
        'Analyze this image...'  # Prompt 在後面
    ]
)
```

**差異**：
1. ❌ 模型版本：`2.0-flash` vs `2.5-flash`（落後一個大版本）
2. ✅ API 調用方式：基本相同
3. ⚠️ Prompt 位置：我們的在前面，官方建議在後面

---

#### 步驟7：生成向量插畫

**當前實現**：
```python
model = "gemini-3-pro-image-preview"

response = client.models.generate_content(
    model='gemini-3-pro-image-preview',
    contents=[prompt, image],
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE']
    )
)
```

**分析**：
- ✅ 使用圖片生成模型（正確）
- ✅ Gemini 3 是最新的（2025年11月）
- ✅ 配置正確（TEXT + IMAGE）

---

## Gemini 2.5 的新能力

### 增強的 Object Detection

**Gemini 2.0+** 支持：
```python
prompt = """Detect all prominent items in the image.
box_2d should be [ymin, xmin, ymax, xmax] normalized to 0-1000."""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[image, prompt],
    config=types.GenerateContentConfig(
        response_mime_type="application/json"
    )
)

# 返回 JSON 格式的 bounding boxes
bounding_boxes = json.loads(response.text)
```

**我們可以用來做什麼**：
- 精確檢測人物位置
- 取代或輔助 body_extent 檢測
- 更準確的裁切和定位

---

### 增強的 Segmentation

**Gemini 2.5** 新增分割能力：
```python
prompt = """Give segmentation masks for the person.
Output JSON with box_2d, mask (base64 PNG), and label."""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[prompt, image],
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0)  # 關鍵配置
    )
)
```

**返回**：
- 精確的分割遮罩（segmentation mask）
- Base64 編碼的 PNG 遮罩
- Bounding box 座標

**我們可以用來做什麼**：
- 取代 rembg 去背（用 Gemini 的分割）
- 更精確的人物提取
- 統一使用 Gemini（減少依賴）

---

### Gemini 3 的 Media Resolution

**新參數**：`media_resolution`

```python
config = types.GenerateContentConfig(
    media_resolution='high'  # 或 'medium', 'low'
)
```

**用途**：
- 控制每張圖片分配的 token 數量
- 高解析度 → 更好的細節識別，但更多 token
- 低解析度 → 更快，但可能漏掉細節

**我們可以用來**：
- 步驟1、4 用 low（簡單分類）
- 步驟7 用 high（需要細節）

---

## 問題分析

### ⚠️ 問題1：圖片理解模型過時

**當前**：`gemini-2.0-flash`（2024年）  
**最新**：`gemini-2.5-flash`（2025年）

**差異**：
- 2.5 有增強的 object detection
- 2.5 有全新的 segmentation 能力
- 2.5 可能更準確

**影響**：
- 步驟1檢測類型可能不夠準
- 步驟4檢測身體範圍可能有誤

---

### ⚠️ 問題2：Prompt 位置不符合最佳實踐

**官方建議**（文檔 Tips）：
> When using a single image with text, place the text prompt _after_ the image part in the `contents` array.

**我們當前**：
```python
contents=[prompt, image]  # ❌ Prompt 在前
```

**應該改為**：
```python
contents=[image, prompt]  # ✅ 圖片在前
```

**影響**：可能略微降低準確性

---

### ✅ 優勢：我們正確區分了任務

- ✅ 圖片理解任務用理解模型（2.0-flash）
- ✅ 圖片生成任務用生成模型（3-pro-image）
- ✅ 沒有混用

---

## 升級建議

### 立即升級（P0）

#### 1. 更新圖片理解模型

**修改**：`src/config.py`

```python
# 從：
model_text = "gemini-2.0-flash"

# 改為：
model_text = "gemini-2.5-flash"  # ✅ 最新（2025年）
```

**好處**：
- ✅ 更準確的檢測
- ✅ 支持新的 segmentation 能力（未來可用）
- ✅ 符合最新最佳實踐

**風險**：低（向下兼容）

---

#### 2. 調整 Prompt 順序

**修改**：所有圖片理解的調用

```python
# 從：
contents=[prompt, image]

# 改為：
contents=[image, prompt]
```

**位置**：
- `src/gemini_client.py` analyze_image_type()
- `src/style_converter.py` analyze_image()

**好處**：符合官方最佳實踐

---

### 探索性升級（P1）

#### 3. 使用 Gemini 2.5 的 Segmentation 取代 rembg

**當前**：
```python
# 步驟2：使用 rembg 去背
from rembg import remove
result = remove(image)  # 外部依賴，u2net 模型
```

**新方案**：
```python
# 使用 Gemini 2.5 的 segmentation
prompt = """Segment the person in this image.
Output JSON with segmentation mask."""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[image, prompt],
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0)
    )
)

# 取得分割遮罩
mask = extract_mask_from_response(response)
# 應用遮罩去背
```

**優點**：
- ✅ 統一使用 Gemini（減少依賴）
- ✅ 可能更準確（Gemini 2.5 的增強能力）
- ✅ 一個API解決多個問題

**缺點**：
- ❌ 增加 API 調用次數
- ❌ 可能更慢
- ❌ 成本可能更高

**建議**：先測試對比，如果品質明顯更好再考慮

---

#### 4. 使用 Object Detection 輔助身體檢測

**當前**：
```python
# 用 AI 判斷身體範圍（語義理解）
body_extent = analyze_image()["body_extent"]
```

**新方案**：
```python
# 用 Object Detection 精確定位（座標）
prompt = "Detect the person's head, shoulders, chest. Return bounding boxes."

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[image, prompt],
    config=types.GenerateContentConfig(
        response_mime_type="application/json"
    )
)

boxes = json.loads(response.text)
# 根據座標計算身體比例
body_ratio = calculate_body_ratio(boxes)
# 更精確地判斷 body_extent
```

**優點**：
- ✅ 更精確（座標而非語義）
- ✅ 可量化
- ✅ 減少判斷錯誤

**缺點**：
- ❌ 需要額外解析邏輯
- ❌ 更複雜

---

### 優化配置（P2）

#### 5. 使用 Media Resolution 參數（Gemini 3 特性）

**針對不同步驟優化**：

```python
# 步驟1、4：簡單分類，用低解析度
config_analysis = types.GenerateContentConfig(
    media_resolution='low'  # 節省 token
)

# 步驟7：生成圖片，用高解析度
config_generation = types.GenerateContentConfig(
    media_resolution='high',  # 更多細節
    response_modalities=['TEXT', 'IMAGE']
)
```

**好處**：
- 節省 token（成本）
- 提高速度（低解析度更快）
- 步驟7 保持高品質

---

## 當前實現的正確性評估

### ✅ 做對的部分

1. **正確區分任務類型**
   - 理解任務用理解模型 ✅
   - 生成任務用生成模型 ✅

2. **API 調用方式基本正確**
   - 使用 google.genai SDK ✅
   - 使用 types.Part.from_bytes ✅

3. **圖片生成模型是最新的**
   - gemini-3-pro-image-preview ✅

---

### ⚠️ 需要改進的部分

1. **圖片理解模型不是最新**
   - 當前：gemini-2.0-flash（2024年）
   - 最新：gemini-2.5-flash（2025年）
   - 差距：一個大版本
   - 影響：檢測準確性

2. **Prompt 順序不符合最佳實踐**
   - 當前：[prompt, image]
   - 建議：[image, prompt]
   - 影響：可能略微降低準確性

3. **未使用新特性**
   - Gemini 2.5 的 segmentation（可取代 rembg）
   - Gemini 3 的 media_resolution（可優化 token）
   - Object detection（可更精確檢測身體）

---

## 建議的升級方案

### 方案A：保守升級（推薦）

**修改**：
1. 更新 `model_text` 為 `gemini-2.5-flash`
2. 調整 Prompt 順序為 [image, prompt]
3. 保持其他不變

**工作量**：10分鐘  
**風險**：極低  
**效果**：提升檢測準確性

---

### 方案B：激進升級

**修改**：
1. 使用 Gemini 2.5 segmentation 取代 rembg
2. 使用 object detection 輔助身體檢測
3. 使用 media_resolution 優化

**工作量**：4-6小時  
**風險**：中等  
**效果**：
- 可能提升品質
- 統一 Gemini 生態
- 但成本可能增加

---

### 方案C：混合方案

**修改**：
1. 立即升級到 gemini-2.5-flash（方案A）
2. 保留 rembg（已經運作良好）
3. 未來再評估 segmentation

**工作量**：10分鐘  
**風險**：極低  
**效果**：穩健提升

---

## Token 和成本分析

### 當前消耗（估算）

**每張圖片**：
- 步驟1（分析）：~300 tokens（圖片）+ ~100 tokens（prompt）
- 步驟4（重複分析）：~300 tokens + ~100 tokens ⚠️ 浪費
- 步驟7（生成）：~2000 tokens（生成成本高）

**總計**：~2800 tokens/圖片

---

### 升級到 2.5-flash 的影響

**Token 計算**（根據文檔）：
- 圖片 ≤ 384px：258 tokens
- 圖片 > 384px：每個 768x768 tile = 258 tokens

**假設圖片 1024x768**：
- Crop unit：floor(768 / 1.5) = 512
- Tiles：2 x 2 = 4 tiles
- Total：4 x 258 = 1032 tokens

**結論**：Token 消耗相近，成本差異不大

---

## 我的具體建議

### 立即執行（今天）

**升級到 gemini-2.5-flash**

**修改 2 個地方**：

1. `src/config.py` 第24行：
```python
model_text: str = "gemini-2.5-flash"  # 從 2.0 升級到 2.5
```

2. `src/style_converter.py` 和 `src/gemini_client.py`：
```python
# Prompt 順序調整
contents=[image_part, prompt]  # 圖片在前
```

**預期效果**：
- 檢測更準確（尤其是邊界案例）
- 符合最新最佳實踐
- 風險極低

---

### 探索測試（本週）

**測試 Gemini 2.5 segmentation 取代 rembg**

**方法**：
1. 創建 image_processor_v2.py
2. 實現 Gemini 2.5 segmentation 去背
3. 對比測試：
   - 品質（哪個去背更乾淨）
   - 速度（哪個更快）
   - 成本（API vs 本地模型）
4. 如果 Gemini 明顯更好，再切換

---

## 總結

### 當前狀態：8/10

**優點**：
- ✅ 正確區分理解/生成任務
- ✅ 圖片生成用最新模型
- ✅ API 調用方式基本正確

**缺點**：
- ⚠️ 理解模型落後一個版本（2.0 vs 2.5）
- ⚠️ Prompt 順序不符最佳實踐
- ⚠️ 未使用新特性（segmentation, object detection）

### 建議優先級

1. **P0（立即）**：升級到 gemini-2.5-flash + 調整 Prompt 順序
2. **P1（本週）**：測試 segmentation 取代 rembg
3. **P2（未來）**：使用 object detection 輔助檢測
4. **P3（探索）**：使用 media_resolution 優化

### 下一步

您想要我：
- A. 立即升級到 gemini-2.5-flash？（10分鐘）
- B. 先測試新模型再決定？
- C. 探索 segmentation 取代 rembg？
- D. 保持現狀，先優化其他部分？

我建議選 A（立即升級），風險極低且有明顯好處。

