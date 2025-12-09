# Pipeline 架構完整指南

## 概述

本專案已從傳統的單一風格架構升級為**函數式 Pipeline 架構**，實現：
- ✅ 可替換的處理組件
- ✅ 自由組合形成不同風格
- ✅ 解決複雜度問題
- ✅ 極致的擴展性

---

## 架構演進

### 過去：單一風格架構

**結構**：
```
src/
└── style_converter.py  # 單一風格，固定流程

流程固定：
  檢測 → 去背 → 分析身體 → AI生成 → 轉透明 → 統一尺寸 → 裁切
  
問題：
  ❌ 無法跳過步驟
  ❌ 無法切換不同實現
  ❌ 新增風格需要複製整個檔案
  ❌ 程式碼重複率高
```

**如果要多風格**：
```
原計劃（app_multistyle.py）：
  style_c_converter.py  (9個獨立檔案)
  style_e_converter.py  
  ...
  style_i2_converter.py
  
問題：
  ❌ 代碼重複 60-70%
  ❌ 維護困難（改一個邏輯要改9個檔案）
  ❌ 檔案數量多（243KB）
```

---

### 現在：Pipeline 架構

**結構**：
```
src/pipeline/
├── components.py      # 所有可替換的組件（函數）
├── engine.py          # Pipeline 執行引擎
└── style_configs.py   # 預設風格配置

組件化：
  分析組件：[gemini_2.5, fast] ← 可選
  預處理組件：[rembg, none] ← 可選
  風格組件：[detailed] ← 可擴展
  背景組件：[transparent, white] ← 可選
  後處理組件：[normalize_1000, keep_size] ← 可選

優勢：
  ✅ 自由組合（2×2×1×2×2 = 16種組合）
  ✅ 代碼重用 100%
  ✅ 新增風格 = 添加配置（不需要新檔案）
  ✅ 維護簡單（改一個組件，所有風格受益）
```

---

## 關鍵差異對比

| 項目 | 過去（單一風格） | 過去（多風格計劃） | 現在（Pipeline） |
|------|----------------|-------------------|-----------------|
| **檔案數量** | 1個 | 9個 | 3個核心檔案 |
| **代碼重複** | N/A | 60-70% | 0% |
| **新增風格** | 複製整個檔案 | 創建新 Converter 類 | 添加配置（5行） |
| **組合彈性** | 無 | 無 | 完全自由 |
| **維護成本** | 低 | 極高 | 低 |
| **擴展性** | 差 | 中 | 極佳 |
| **學習曲線** | 簡單 | 中等 | 簡單 |

---

## Pipeline 架構詳解

### 核心概念

**不要創建「完整的風格」，而是創建「可替換的組件」**

```
風格 = 組件的組合

例如：
  I4詳細版 = [gemini_2.5分析] + [rembg去背] + [詳細Prompt] + [透明背景] + [統一1000]
  
  I4簡化版 = [快速分析] + [不去背] + [詳細Prompt] + [白色背景] + [保持尺寸]
  
  自定義風格 = [gemini_2.5分析] + [rembg去背] + [詳細Prompt] + [藍色圓背景] + [統一1000]
```

**優勢**：
- 可以任意組合
- 共用的組件不重複實現
- 添加新組件後，所有風格都可以選用

---

### 組件系統

#### 5種組件類型

```python
# 1. 分析組件（Analysis）
def analysis_component(image: Image) -> dict:
    """分析圖片，返回資訊"""
    return {
        "image_type": "photo",      # 或 "illustration"
        "body_extent": "head_chest"  # head_only/head_neck/head_chest/full_body
    }

# 2. 預處理組件（Preprocess）
def preprocess_component(image: Image, context: dict) -> Image:
    """預處理圖片（去背、裁切等）"""
    return processed_image

# 3. 風格組件（Style）
def style_component(image: Image, context: dict) -> Image:
    """AI 生成風格"""
    return generated_image

# 4. 背景組件（Background）
def background_component(image: Image, context: dict) -> Image:
    """處理背景（透明、白色、藍色圓等）"""
    return image_with_bg

# 5. 後處理組件（Postprocess）
def postprocess_component(image: Image, context: dict) -> Image:
    """後處理（統一尺寸、描邊等）"""
    return final_image
```

---

### Pipeline 執行流程

```python
# src/pipeline/engine.py

def run_pipeline(image, config):
    context = {}  # 共享上下文
    
    # 步驟1：分析
    if config.get("analysis"):
        analysis = config["analysis"](image)
        context.update(analysis)
    
    # 步驟2：預處理
    if config.get("preprocess"):
        image = config["preprocess"](image, context)
    
    # 步驟3：風格生成
    if config.get("style"):
        image = config["style"](image, context)
    
    # 步驟4：背景處理
    if config.get("background"):
        image = config["background"](image, context)
    
    # 步驟5：後處理
    if config.get("postprocess"):
        image = config["postprocess"](image, context)
    
    return image
```

**特點**：
- 每個步驟可選（`if config.get()`）
- Context 在步驟間傳遞資訊
- 組件函數專注做一件事

---

## 如何使用

### 1. 使用預設風格

```python
from src.pipeline import run_pipeline, PRESET_STYLES

# 使用詳細版風格
result = run_pipeline(image, PRESET_STYLES["i4_detailed"])

# 使用簡化版風格
result = run_pipeline(image, PRESET_STYLES["i4_simplified"])
```

**當前預設風格**：
- `i4_detailed`：完整處理，詳細Prompt（2000字）
- `i4_simplified`：最小處理，快速

---

### 2. 自定義組合風格

```python
from src.pipeline.components import *

# 自定義配置
custom_style = {
    "analysis": gemini_25_analysis,      # 使用 Gemini 2.5 分析
    "preprocess": rembg_preprocess,      # 使用 rembg 去背
    "style": detailed_style_generate,    # 使用詳細Prompt
    "background": transparent_background, # 透明背景
    "postprocess": normalize_1000        # 統一到 1000x1000
}

# 執行
result = run_pipeline(image, custom_style)
```

**可以任意混搭**：
```python
# 範例1：快速版本
quick_style = {
    "analysis": fast_analysis,           # 快速分析
    "preprocess": no_preprocess,         # 不去背
    "style": detailed_style_generate,    # 詳細生成
    "background": keep_white_background, # 保持白底
    "postprocess": keep_original_size    # 保持原尺寸
}

# 範例2：高品質版本
premium_style = {
    "analysis": gemini_25_analysis,      # Gemini 2.5
    "preprocess": rembg_preprocess,      # rembg 去背
    "style": detailed_style_generate,    # 詳細Prompt
    "background": transparent_background, # 透明
    "postprocess": normalize_1000        # 1000x1000
}
```

---

## 如何擴展

### 新增組件

#### 1. 添加新的分析組件

```python
# 在 src/pipeline/components.py 添加

def gemini_30_analysis(image: Image.Image) -> dict:
    """使用未來的 Gemini 3.0 分析"""
    # 實現分析邏輯
    return {"image_type": "photo", "body_extent": "head_chest"}

# 在 engine.py 的 COMPONENT_REGISTRY 註冊
COMPONENT_REGISTRY["analysis"]["gemini_3.0"] = gemini_30_analysis
```

#### 2. 添加新的背景組件

```python
# 在 src/pipeline/components.py 添加

def blue_circle_background(image: Image.Image, context: dict) -> Image.Image:
    """添加藍色圓形漸層背景"""
    # 創建藍色圓形漸層
    width, height = image.size
    background = Image.new('RGBA', (width, height))
    
    # 繪製漸層圓
    draw = ImageDraw.Draw(background)
    # ... 漸層邏輯
    
    # 合成
    result = Image.alpha_composite(background, image)
    return result

# 註冊
COMPONENT_REGISTRY["background"]["blue_circle"] = blue_circle_background
```

#### 3. 添加新的風格組件（不同Prompt）

```python
# 在 src/pipeline/components.py 添加

def simplified_style_generate(image: Image.Image, context: dict) -> Image.Image:
    """簡化Prompt風格生成（600字）"""
    # 載入簡化版 Prompt
    from src.prompts_simplified_backup import get_style_prompt as get_simple_prompt
    
    prompt = get_simple_prompt(context.get("body_extent", "head_chest"))
    
    # 調用 AI（邏輯與 detailed 相同，只是 Prompt 不同）
    client = genai.Client(...)
    result = client.models.generate_content(...)
    
    return result

# 註冊
COMPONENT_REGISTRY["style"]["simplified"] = simplified_style_generate
```

---

### 新增預設風格

```python
# 在 src/pipeline/style_configs.py 添加

PRESET_STYLES["my_new_style"] = {
    "name": "我的新風格",
    "description": "自定義組合",
    "analysis": components.gemini_25_analysis,
    "preprocess": components.rembg_preprocess,
    "style": components.detailed_style_generate,
    "background": components.blue_circle_background,  # 使用新組件
    "postprocess": components.normalize_1000
}

# 添加到前端選項
STYLE_OPTIONS.append({
    "id": "my_new_style",
    "name": "我的新風格",
    "description": "自定義組合說明",
    "recommended": False
})
```

**就這麼簡單！**不需要創建新的 Converter 類或檔案。

---

### 創建複雜的自定義流程

#### 範例：需要特殊後處理的風格

```python
# 如果需要特殊邏輯，創建自定義組件

def style_c_special_postprocess(image: Image.Image, context: dict) -> Image.Image:
    """風格C的特殊後處理（墨水效果）"""
    # 先做標準後處理
    image = normalize_1000(image, context)
    
    # 添加特殊的墨水筆觸效果
    image = add_ink_brush_texture(image)
    
    # 添加灰階處理
    image = convert_to_grayscale(image)
    
    return image

# 註冊
COMPONENT_REGISTRY["postprocess"]["style_c_special"] = style_c_special_postprocess

# 使用
PRESET_STYLES["style_c"] = {
    "name": "墨線筆觸風格",
    "analysis": components.gemini_25_analysis,
    "preprocess": components.rembg_preprocess,
    "style": components.detailed_style_generate,  # 或特殊的 Prompt
    "background": components.transparent_background,
    "postprocess": style_c_special_postprocess  # 特殊後處理
}
```

---

## Prompt 管理

### 當前 Prompt 系統

**檔案位置**：`src/prompts.py`

**結構**：
```python
# Body Instructions（4種）
BODY_INSTRUCTIONS = {
    "full_body": "CRITICAL INSTRUCTION...",    # 裁切全身照
    "head_only": "CRITICAL INSTRUCTION...",    # 生成身體
    "head_neck": "CRITICAL INSTRUCTION...",    # 生成身體
    "head_chest": "CRITICAL INSTRUCTION..."    # 保持構圖
}

# 主要風格 Prompt 模板
STYLE_PROMPT_TEMPLATE = """
Transform this photo into a VECTOR ILLUSTRATION...
{body_instruction}  # ← Body Instruction 插入這裡
...
[2000+ 字的詳細風格要求]
"""

# Helper 函數
def get_style_prompt(body_extent: str) -> str:
    body_instruction = BODY_INSTRUCTIONS[body_extent]
    return STYLE_PROMPT_TEMPLATE.format(body_instruction=body_instruction)
```

---

### 如何添加新的 Prompt 風格

#### 方法1：在 prompts.py 添加新模板

```python
# src/prompts.py 添加

# 新的 Body Instructions（如果處理方式不同）
SIMPLIFIED_BODY_INSTRUCTIONS = {
    "full_body": "Crop to upper chest",  # 簡化版
    "head_only": "Generate body",
    "head_neck": "Generate shoulders",
    "head_chest": "Keep framing"
}

# 新的風格模板
SIMPLIFIED_STYLE_PROMPT = """Transform this photo into a VECTOR ILLUSTRATION.
{body_instruction}

Style: Semi-realistic corporate avatar
Rendering: Clean vector art, cel-shaded
Output: Head to upper chest portrait
"""

# 新的 Helper 函數
def get_simplified_prompt(body_extent: str) -> str:
    body_instruction = SIMPLIFIED_BODY_INSTRUCTIONS[body_extent]
    return SIMPLIFIED_STYLE_PROMPT.format(body_instruction=body_instruction)
```

#### 方法2：創建獨立的 Prompt 檔案

```python
# src/prompts/style_c_prompts.py（新檔案）

STYLE_C_BODY_INSTRUCTIONS = {
    "full_body": "Create ink brush portrait, crop to chest",
    # ...
}

STYLE_C_PROMPT_TEMPLATE = """Transform into INK BRUSH style illustration...
{body_instruction}
...
"""

def get_style_c_prompt(body_extent: str) -> str:
    body_instruction = STYLE_C_BODY_INSTRUCTIONS[body_extent]
    return STYLE_C_PROMPT_TEMPLATE.format(body_instruction=body_instruction)
```

然後在組件中使用：
```python
# src/pipeline/components.py

def style_c_generate(image: Image.Image, context: dict) -> Image.Image:
    from src.prompts.style_c_prompts import get_style_c_prompt
    
    prompt = get_style_c_prompt(context.get("body_extent", "head_chest"))
    # ... AI 生成邏輯
    return result

# 註冊
COMPONENT_REGISTRY["style"]["style_c"] = style_c_generate
```

---

## 完整範例：添加新風格

### 場景：添加「墨線筆觸風格」

#### 步驟1：創建 Prompt

```python
# src/prompts/style_c.py（新檔案）

STYLE_C_PROMPTS = """Transform this photo into INK BRUSH ILLUSTRATION.

{body_instruction}

STYLE:
- Ink brush strokes with visible texture
- High contrast black lines
- Grayscale with selective color accents
- Traditional Asian painting style

TECHNIQUE:
- Bold, expressive brush strokes
- Varying line thickness
- White space for emphasis
- Minimal but impactful

OUTPUT:
- Professional ink illustration
- Head to upper chest composition
- White background
"""

def get_style_c_prompt(body_extent):
    # ... 組合邏輯
    return prompt
```

#### 步驟2：創建風格組件（如果需要特殊處理）

```python
# src/pipeline/components.py 添加

def style_c_generate(image: Image.Image, context: dict) -> Image.Image:
    """風格C：墨線筆觸"""
    from src.prompts.style_c import get_style_c_prompt
    
    prompt = get_style_c_prompt(context.get("body_extent", "head_chest"))
    
    # AI 生成（與其他風格相同）
    client = genai.Client(...)
    result = generate_image(image, prompt)
    
    return result

# 如果需要特殊後處理
def style_c_postprocess(image: Image.Image, context: dict) -> Image.Image:
    """風格C的特殊後處理"""
    # 轉灰階
    image = convert_to_grayscale(image)
    
    # 添加墨水紋理
    image = add_ink_texture(image)
    
    # 統一尺寸
    image = normalize_1000(image, context)
    
    return image
```

#### 步驟3：註冊組件

```python
# src/pipeline/engine.py

COMPONENT_REGISTRY["style"]["style_c"] = style_c_generate
COMPONENT_REGISTRY["postprocess"]["style_c"] = style_c_postprocess
```

#### 步驟4：創建預設風格

```python
# src/pipeline/style_configs.py

PRESET_STYLES["style_c"] = {
    "name": "墨線筆觸風格",
    "description": "傳統水墨畫風格，黑白線條",
    "analysis": components.gemini_25_analysis,
    "preprocess": components.rembg_preprocess,
    "style": style_c_generate,             # 新組件
    "background": components.transparent_background,
    "postprocess": style_c_postprocess     # 新組件
}

STYLE_OPTIONS.append({
    "id": "style_c",
    "name": "墨線筆觸",
    "description": "傳統水墨畫風格",
    "recommended": False
})
```

#### 步驟5：前端會自動載入

前端會自動從 `/api/styles` 獲取風格列表並顯示在下拉選單。

**完成！**只需要5個步驟，約1-2小時工作量。

---

## 進階使用

### 條件式處理

```python
def smart_preprocess(image: Image.Image, context: dict) -> Image.Image:
    """智能預處理：根據類型決定"""
    if context.get("image_type") == "photo":
        # 照片：去背
        return rembg_preprocess(image, context)
    else:
        # 插畫：不去背
        return no_preprocess(image, context)
```

### 組合式處理

```python
def combined_postprocess(image: Image.Image, context: dict) -> Image.Image:
    """組合多個後處理"""
    # 1. 統一尺寸
    image = normalize_1000(image, context)
    
    # 2. 添加描邊（如果需要）
    if context.get("add_outline"):
        image = add_white_outline(image)
    
    # 3. 調整對比度
    image = adjust_contrast(image, 1.2)
    
    return image
```

---

## 與後端整合

### FastAPI 整合（已完成）

```python
# app.py

@app.websocket("/ws/process")
async def process_image_websocket(websocket: WebSocket):
    await websocket.accept()
    
    data = await websocket.receive_json()
    image = load_image(data['image'])
    
    # 獲取用戶選擇的風格
    selected_style = data.get('style', 'i4_detailed')
    style_config = PRESET_STYLES[selected_style]
    
    # 使用 Pipeline 處理
    result = run_pipeline(image, style_config)
    
    # 返回結果
    await websocket.send_json({
        'image': image_to_base64(result),
        'message': '處理完成'
    })
```

**用戶選擇風格** → **自動使用對應的組件組合** → **生成結果**

---

## 與前端整合

### 風格選擇（已實現）

```html
<!-- templates/index.html -->

<select id="style-selector">
    <option value="i4_detailed">I4 詳細版（推薦）</option>
    <option value="i4_simplified">I4 簡化版（快速）</option>
    <!-- 新增風格會自動出現 -->
</select>

<script>
// 發送到後端
ws.send(JSON.stringify({
    image: imageData,
    style: document.getElementById('style-selector').value
}));
</script>
```

**自動化**：
- 後端的 `/api/styles` 端點返回所有風格
- 前端可以動態載入（未來可實現）

---

## 維護指南

### 升級 AI 模型

**過去**：需要修改9個檔案  
**現在**：只需修改1個地方

```python
# src/config.py
model_text = "gemini-3.0-flash"  # ← 改這裡

# 所有使用 gemini_25_analysis 的風格自動升級
```

### 修改共用邏輯

**過去**：修改 `make_white_transparent` 需要改9個檔案  
**現在**：修改1個函數即可

```python
# src/pipeline/components.py
def transparent_background(image, context):
    # 修改邏輯
    threshold = 235  # ← 改這裡
    # ...

# 所有使用此組件的風格自動更新
```

### 新增風格

**過去**：
1. 複製整個 style_converter.py（650行）
2. 修改 Prompt
3. 修改後處理
4. 測試
5. 約 2-4 小時

**現在**：
1. 在 style_configs.py 添加5行配置
2. 測試
3. 約 10 分鐘

---

## 性能優勢

### 記憶體使用

**過去（多風格）**：
```
9個 Converter × 每個初始化 Gemini Client
= 9個 Client 實例
= 高記憶體佔用
```

**現在**：
```
組件按需初始化
Client 在組件內臨時創建
= 更低記憶體佔用
```

### 載入速度

**過去（多風格）**：
```
啟動時初始化所有9個 Converter
= 慢啟動
```

**現在**：
```
組件按需載入
= 快速啟動
```

---

## 擴展能力對比

| 需求 | 過去（單一） | 過去（多風格） | 現在（Pipeline） |
|------|------------|---------------|-----------------|
| 支持2個風格 | ❌ | ✅ 需2個檔案 | ✅ 5行配置 |
| 支持14個風格 | ❌ | ✅ 需14個檔案 | ✅ 70行配置 |
| 混搭組合 | ❌ | ❌ | ✅ 任意組合 |
| 新增組件後 | N/A | 需修改所有檔案 | 所有風格自動可用 |
| A/B測試 | ❌ | ⚠️ 困難 | ✅ 極簡單 |

---

## 實戰案例

### 案例1：對比兩個 Prompt 版本

```python
# 測試詳細版 vs 簡化版
results = {}

for style in ["i4_detailed", "i4_simplified"]:
    result = run_pipeline(image, PRESET_STYLES[style])
    results[style] = result
    
# 對比品質、速度、token 消耗
```

### 案例2：創建14個風格

**只需在 `style_configs.py` 添加**：
```python
PRESET_STYLES.update({
    "style_c": {...},   # 5行
    "style_e": {...},   # 5行
    "style_e2": {...},  # 5行
    # ... 14個風格 = 70行配置
})
```

**vs 過去**：14個檔案 × 650行 = 9100行代碼（大量重複）

---

## 故障排除

### 問題：組件找不到

```python
KeyError: 'my_component'
```

**解決**：確認組件已註冊
```python
# src/pipeline/engine.py
COMPONENT_REGISTRY["category"]["my_component"] = my_func
```

### 問題：Context 資訊缺失

```python
KeyError: 'body_extent'
```

**解決**：確保分析組件在前面執行
```python
config = {
    "analysis": gemini_25_analysis,  # ← 必須有
    "style": detailed_style_generate # ← 需要 body_extent
}
```

---

## 未來擴展方向

### 1. 添加更多預設風格

基於原來的9個風格：
- style_c: 墨線筆觸
- style_e: 藍色圓背景
- style_e2: 自然上色
- style_e3: 藍綠高光
- style_f: 炭筆手繪
- style_g: 極簡扁平
- style_h: 單色蠟筆
- style_i: 寫實漫畫
- style_i2: 成熟寫實

**工作量**：每個約1-2小時（如果只是 Prompt 不同）

### 2. 添加更多組件

**分析組件**：
- Gemini 3.0（未來）
- 離線分析（不用 API）
- 批量分析

**預處理組件**：
- Gemini 2.5 Segmentation
- 不同的去背模型
- 圖片增強

**背景組件**：
- 藍色圓形漸層
- 自定義顏色漸層
- 圖案背景
- 模糊背景

**後處理組件**：
- 不同尺寸（512, 1024, 2048）
- 白色描邊
- 黑色描邊
- 濾鏡效果

### 3. 前端進階功能

**當前**：下拉選單選擇預設風格

**未來可實現**：
- 自定義每個步驟的組件
- 儲存自定義配置
- 批量處理多個風格
- 即時預覽對比

---

## 總結

### Pipeline 架構的核心價值

1. **解決複雜度問題**
   - 邏輯分散到各組件
   - 每個組件簡單明瞭（<50行）

2. **極致的靈活性**
   - 可以跳過任意步驟
   - 可以替換任意實現
   - 可以自由組合

3. **維護成本降低**
   - 代碼重複 0%
   - 修改一處，所有受益
   - 易於升級和測試

4. **擴展性極佳**
   - 新增風格：5行配置
   - 新增組件：1個函數
   - 組合數量：無限

### 當前狀態

**已實現**：
- ✅ Pipeline 核心架構
- ✅ 基礎組件（分析、預處理、風格、背景、後處理）
- ✅ 2個預設風格
- ✅ 前端風格選擇
- ✅ 完整文檔

**服務地址**：http://127.0.0.1:8000

**啟動方式**：`uv run python app.py` 或 `./run.sh`

---

**專案已完全重構為 Pipeline 架構，準備好無限擴展！** 🎉

---

## 細粒度 Pipeline 架構（2025-12-09 升級）

### 重大升級：粗粒度 → 細粒度

**之前的問題**：
- 5個粗粒度組件（analysis, preprocess, style, background, postprocess）
- 無法詳細顯示內部步驟
- 進度顯示需要手動處理每個組件的內部邏輯

**升級後的優勢**：
- 12個細粒度組件（每個組件對應一個具體步驟）
- 自動詳細顯示所有步驟
- 真正萬用的進度顯示邏輯

### 細粒度組件列表

**檔案**：`src/pipeline/components_fine_grained.py`

```python
# 分析組件（2個）
detect_image_type        # 步驟1：檢測圖片類型
detect_body_extent       # 步驟4：檢測身體範圍

# 預處理組件（2個）
rembg_remove_background  # 步驟2：去背處理
crop_to_content          # 步驟3：裁切平整底部

# 風格生成組件（4個）
prepare_for_ai           # 步驟5：準備圖片給AI
generate_body_instruction # 步驟5：生成處理指令
build_full_prompt        # 步驟6：構建完整Prompt
ai_generate_style        # 步驟7：AI生成
ai_generate_universal    # 步驟7（萬能版）：AI萬能生成

# 背景組件（1個）
make_white_transparent   # 步驟8：白色轉透明

# 後處理組件（3個）
resize_and_position      # 步驟9：縮放和定位
crop_bottom_edge         # 步驟10：裁切底部邊緣
```

### 細粒度風格配置

**檔案**：`src/pipeline/style_configs_fine_grained.py`

```python
I4_DETAILED_FINE = {
    "name": "I4 詳細版",
    "steps": [
        # 照片：10個步驟
        # 插畫：8個步驟（步驟3和10有條件跳過）
        步驟1: 檢測圖片類型,
        步驟2: 去背處理,
        步驟3: 裁切平整底部 (僅照片),
        步驟4: 檢測身體範圍,
        步驟5: 生成處理指令,
        步驟6: 構建AI Prompt,
        步驟7: AI生成插畫,
        步驟8: 白色轉透明,
        步驟9: 統一尺寸位置,
        步驟10: 底部裁切 (僅照片)
    ]
}

UNIVERSAL_INTELLIGENT_FINE = {
    "name": "萬能智能版",
    "steps": [
        步驟1: AI 萬能智能生成
    ]
}
```

### 萬用執行邏輯

**檔案**：`app_fine_grained.py`

```python
# 所有風格統一使用這套邏輯
for step in steps:
    # 檢查條件
    if 'conditional' in step and not step['conditional'](context):
        skip_and_notify()
        continue
    
    # 執行組件
    result = step['component'](current_image, context)
    
    # 格式化結果
    detail = format_result_detail(step, result, image, context)
    
    # 顯示步驟完成 + 詳細結果
    display(f"✅ {step['name']}完成\n   {detail}")
```

### 步驟數量總結

| 風格 | 步驟數量 | 說明 |
|------|----------|------|
| I4 詳細版（照片） | 10個 | 全部執行 |
| I4 詳細版（插畫） | 8個 | 跳過步驟3和10 |
| 萬能智能版 | 1個 | 極簡流程 |
| I4 簡化版 | 3個 | 快速流程 |

### 服務啟動

```bash
# 細粒度 Pipeline 版本
uv run python app_fine_grained.py

# 訪問：http://127.0.0.1:8003
```

---

**專案已升級為細粒度 Pipeline 架構，實現真正萬用的動態步驟顯示！** 🎉

