# Pipeline 完整指南（細粒度架構）

## 概述

本專案採用**細粒度 Pipeline 架構**，實現：
- ✅ 12個細粒度組件（每個組件對應一個具體步驟）
- ✅ 萬用的動態步驟顯示（所有風格統一邏輯）
- ✅ 詳細的結果記錄（每個步驟顯示詳細結果）
- ✅ 靈活的組合（不同風格不同步驟數量）

---

## 架構演進

### 第一代：單一風格架構（已淘汰）

```
src/style_converter.py  # 固定流程，無法擴展
```

**問題**：
- ❌ 無法新增風格
- ❌ 流程固定，無法調整

### 第二代：粗粒度 Pipeline 架構（2025-12-08）

```
src/pipeline/
├── components.py      # 5個粗粒度組件
├── engine.py          # Pipeline 引擎
└── style_configs.py   # 風格配置

5個粗組件：
  analysis（檢測類型+身體）
  preprocess（去背+裁切）
  style（準備+構建Prompt+生成）
  background（檢測+轉換）
  postprocess（計算+縮放+裁切）
```

**問題**：
- ⚠️ 組件內部邏輯無法單獨顯示
- ⚠️ 進度顯示需要手動處理每個組件
- ⚠️ 不夠細緻，難以追蹤詳細進度

### 第三代：細粒度 Pipeline 架構（2025-12-09，當前）

```
src/pipeline/
├── components_fine_grained.py      # 12個細粒度組件
├── style_configs_fine_grained.py   # 細粒度風格配置
└── engine.py                       # 通用引擎

12個細組件：
  1. detect_image_type           # 檢測圖片類型
  2. detect_body_extent          # 檢測身體範圍
  3. rembg_remove_background     # rembg 去背
  4. crop_to_content             # 裁切內容
  5. prepare_for_ai              # 準備圖片
  6. generate_body_instruction   # 生成處理指令
  7. build_full_prompt           # 構建完整Prompt
  8. ai_generate_style           # AI 生成
  9. ai_generate_universal       # AI 萬能生成
  10. make_white_transparent     # 白轉透明
  11. resize_and_position        # 縮放定位
  12. crop_bottom_edge           # 裁切底部
```

**優勢**：
- ✅ 每個組件對應一個步驟
- ✅ 自動詳細顯示所有步驟
- ✅ 真正萬用的進度邏輯
- ✅ 極致靈活

---

## 核心組件詳解

### 分析組件（2個）

#### 1. detect_image_type
```python
def detect_image_type(image: Image.Image, context: dict) -> dict:
    """檢測圖片類型（照片/插畫）"""
    # 調用 Gemini 2.5 Flash
    # 返回：{"image_type": "photo"} 或 {"image_type": "illustration"}
```

**用途**：判斷輸入是照片還是插畫，決定後續處理路徑

#### 2. detect_body_extent
```python
def detect_body_extent(image: Image.Image, context: dict) -> dict:
    """檢測身體範圍（僅照片）"""
    # 如果是插畫，直接返回 head_chest
    # 如果是照片，調用 Gemini 2.5 Flash 檢測
    # 返回：{"body_extent": "head_only/head_neck/head_chest/full_body"}
```

**用途**：決定使用哪種 Body Instruction

### 預處理組件（2個）

#### 3. rembg_remove_background
```python
def rembg_remove_background(image: Image.Image, context: dict) -> Image.Image:
    """去背處理（照片）或格式轉換（插畫）"""
    # 照片：使用 rembg 深度學習去背
    # 插畫：只轉 RGBA 格式
```

**用途**：移除背景，準備透明處理

#### 4. crop_to_content
```python
def crop_to_content(image: Image.Image, context: dict) -> Image.Image:
    """裁切到內容區域"""
    # 基於 alpha 通道，裁切到非透明區域邊界
```

**用途**：移除多餘的透明邊緣

**條件**：僅照片執行（插畫跳過）

### 風格生成組件（5個）

#### 5. prepare_for_ai
```python
def prepare_for_ai(image: Image.Image, context: dict) -> Image.Image:
    """準備圖片給 AI（轉 RGB，白底）"""
    # RGBA → RGB with white background
```

#### 6. generate_body_instruction
```python
def generate_body_instruction(image: Image.Image, context: dict) -> dict:
    """生成 Body Instruction（查表）"""
    # 根據 body_extent 從 BODY_INSTRUCTIONS 查找對應指令
    # 返回：{"body_instruction": "..."}
```

#### 7. build_full_prompt
```python
def build_full_prompt(image: Image.Image, context: dict) -> dict:
    """構建完整 Prompt"""
    # 組合 Body Instruction + Style 要求
    # 返回：{"prompt": "完整的2000字Prompt"}
```

#### 8. ai_generate_style
```python
def ai_generate_style(image: Image.Image, context: dict) -> Image.Image:
    """AI 生成向量插畫（I4 系列）"""
    # 使用構建好的 Prompt
    # 調用 Gemini 2.5 Pro Image
    # 返回生成的圖片
```

#### 9. ai_generate_universal
```python
def ai_generate_universal(image: Image.Image, context: dict) -> Image.Image:
    """AI 萬能智能生成"""
    # 使用萬能智能 Prompt（~3000字）
    # 不需要 body_extent
    # 一次完成所有處理
```

### 背景處理組件（1個）

#### 10. make_white_transparent
```python
def make_white_transparent(image: Image.Image, context: dict) -> Image.Image:
    """白色轉透明"""
    # 連通區域分析，保護人物內部白色
    # 閾值 240
```

### 後處理組件（2個）

#### 11. resize_and_position
```python
def resize_and_position(image: Image.Image, context: dict) -> Image.Image:
    """縮放和定位到 1000x1000"""
    # 人物70%高，85%寬
    # 頭部35%位置
```

#### 12. crop_bottom_edge
```python
def crop_bottom_edge(image: Image.Image, context: dict) -> Image.Image:
    """裁切底部邊緣（僅照片）"""
    # 找中心區域底部，水平裁切
```

**條件**：僅照片執行（插畫跳過）

---

## 風格配置

### I4 詳細版（10/8步驟）

```python
I4_DETAILED_FINE = {
    "name": "I4 詳細版",
    "steps": [
        步驟1:  detect_image_type,
        步驟2:  rembg_remove_background,
        步驟3:  crop_to_content (條件：僅照片),
        步驟4:  detect_body_extent,
        步驟5:  generate_body_instruction,
        步驟6:  build_full_prompt,
        步驟7:  ai_generate_style,
        步驟8:  make_white_transparent,
        步驟9:  resize_and_position,
        步驟10: crop_bottom_edge (條件：僅照片)
    ]
}
```

**執行結果**：
- 照片：10個步驟全部執行
- 插畫：8個步驟（跳過步驟3和10）

### 萬能智能版（1步驟）

```python
UNIVERSAL_INTELLIGENT_FINE = {
    "name": "萬能智能版",
    "steps": [
        步驟1: ai_generate_universal
    ]
}
```

**特點**：
- 極簡流程（無檢測、無預處理）
- 萬能 Prompt（~3000字，包含所有情況的處理指令）
- 一次 API 調用完成

### I4 簡化版（3步驟）

```python
I4_SIMPLIFIED_FINE = {
    "name": "I4 簡化版",
    "steps": [
        步驟1: prepare_for_ai,
        步驟2: build_full_prompt,
        步驟3: ai_generate_style
    ]
}
```

---

## 萬用執行邏輯

### app.py 核心代碼

```python
@app.websocket("/ws/process")
async def process_image_websocket(websocket: WebSocket):
    # 獲取風格配置
    style_config = FINE_GRAINED_STYLES[selected_style]
    steps = style_config['steps']
    
    # ========== 萬用執行邏輯 ==========
    for i, step in enumerate(steps):
        # 檢查條件
        if 'conditional' in step:
            if not step['conditional'](context):
                # 跳過此步驟
                continue
        
        # 執行組件（統一調用）
        result = step['component'](current_image, context)
        
        # 更新狀態
        if step.get('update_context'):
            context.update(result)
        if step.get('update_image'):
            current_image = result
        
        # 格式化詳細結果
        detail = format_result_detail(step, result, current_image, context)
        
        # 顯示步驟完成
        await send_progress({
            'message': f'✅ {step["name"]}完成\n   {detail}',
            'image': current_image if step.get('show_image') else None
        })
```

**關鍵**：
- 所有風格用同一套循環邏輯
- 根據配置自動執行對應步驟
- 自動顯示詳細結果

---

## 詳細結果顯示

### format_result_detail 函數

```python
def format_result_detail(step, result, image, context) -> str:
    """萬用結果格式化"""
    
    # 檢測類型 → 顯示：類型名稱
    if "檢測圖片類型" in step['name']:
        return f"→ 類型：真人照片"
    
    # 檢測身體 → 顯示：身體範圍描述
    if "檢測身體範圍" in step['name']:
        return f"→ 身體範圍：頭部到上胸部（理想）"
    
    # 生成指令 → 顯示：指令類型
    if "生成處理指令" in step['name']:
        return f"→ 指令類型：保持當前構圖"
    
    # 圖片處理 → 顯示：尺寸變化
    return f"→ 800x600 處理為 1024x1024"
```

**自動捕獲和顯示**：
- 檢測結果：類型、身體範圍
- 處理結果：尺寸變化、模式變化
- 所有信息保留在界面上

---

## 步驟數量對比

### 舊版 vs 新版

| 類型 | 舊版（粗粒度） | 新版（細粒度） |
|------|---------------|---------------|
| **組件數量** | 5個 | 12個 |
| **照片步驟** | 10個（手動拆分） | 10個（自動） |
| **插畫步驟** | 8個（手動拆分） | 8個（自動） |
| **萬能智能** | N/A | 1個 |
| **進度邏輯** | 為每個風格手寫 | 所有風格統一 |
| **新增風格** | 需要手寫進度邏輯 | 只需配置步驟列表 |

---

## 處理流程詳解

### I4 詳細版（照片）- 10步驟

```
輸入圖片
  ↓
步驟1: 🔍 檢測圖片類型
  → 類型：真人照片
  ↓
步驟2: ✂️ 去背處理
  → 800x600 處理為 750x580
  ↓
步驟3: ✂️ 裁切平整底部
  → 750x580 處理為 740x580
  ↓
步驟4: 🔍 檢測身體範圍
  → 身體範圍：頭部到上胸部（理想）
  ↓
步驟5: 📝 生成處理指令
  → 指令類型：保持當前構圖
  ↓
步驟6: 📋 構建AI Prompt
  → Prompt 長度：2000字
  ↓
步驟7: 🎨 AI生成插畫
  → 740x580 處理為 1024x1024
  ↓
步驟8: 🌈 白色轉透明
  → 尺寸：1024x1024
  ↓
步驟9: 📐 統一尺寸位置
  → 1024x1024 處理為 1000x1000
  ↓
步驟10: ✂️ 底部裁切
  → 尺寸：1000x1000
  ↓
輸出結果
```

### I4 詳細版（插畫）- 8步驟

```
輸入圖片
  ↓
步驟1: 🔍 檢測圖片類型
  → 類型：插畫作品
  ↓
步驟2: ✂️ 去背處理
  → 800x600 處理為 800x600（只轉格式）
  ↓
[步驟3: 跳過 - 僅照片]
  ↓
步驟4: 🔍 檢測身體範圍
  → 身體範圍：頭部到上胸部（理想）
  ↓
步驟5: 📝 生成處理指令
  → 指令類型：保持當前構圖
  ↓
步驟6: 📋 構建AI Prompt
  → Prompt 長度：2000字
  ↓
步驟7: 🎨 AI生成插畫
  → 800x600 處理為 1024x1024
  ↓
步驟8: 🌈 白色轉透明
  → 尺寸：1024x1024
  ↓
步驟9: 📐 統一尺寸位置
  → 1024x1024 處理為 1000x1000
  ↓
[步驟10: 跳過 - 僅照片]
  ↓
輸出結果
```

### 萬能智能版 - 1步驟

```
輸入圖片
  ↓
步驟1: 🎨 AI 萬能智能生成
  → 800x600 處理為 1024x1024
  ↓
輸出結果
```

**特點**：
- 無檢測、無預處理
- 使用萬能智能 Prompt（~3000字）
- AI 自動判斷所有情況
- 1次 API 調用完成

---

## 如何新增風格

### 超簡單：只需配置步驟列表

```python
# 在 style_configs_fine_grained.py 添加

MY_NEW_STYLE = {
    "name": "我的新風格",
    "steps": [
        {"name": "檢測類型", "component": fg.detect_image_type, "update_context": True},
        {"name": "AI生成", "component": fg.ai_generate_style, "update_image": True, "show_image": True},
        {"name": "白轉透明", "component": fg.make_white_transparent, "update_image": True, "show_image": True}
    ]
}

FINE_GRAINED_STYLES["my_new_style"] = MY_NEW_STYLE
```

**完成！**不需要寫任何進度邏輯，自動顯示所有步驟和結果。

---

## 萬用進度邏輯

### 核心優勢

**一套代碼，適配所有風格**：

```python
# 這段代碼處理所有風格
for step in style_config['steps']:
    # 條件判斷（自動）
    if skip_condition: continue
    
    # 執行組件（自動）
    result = component(image, context)
    
    # 格式化結果（自動）
    detail = format_result_detail(...)
    
    # 顯示步驟（自動）
    display(step_name, detail, result_image)
```

**不需要**：
- ❌ 為每個風格寫獨立函數
- ❌ 手動處理每個步驟的進度
- ❌ 手動格式化每種結果

**自動處理**：
- ✅ 步驟數量（10/8/1/3...任意）
- ✅ 條件跳過（照片/插畫）
- ✅ 詳細結果顯示
- ✅ 圖片更新和顯示

---

## 新舊版本對比

### 舊版（app_old_backup_20251209.py）

**特點**：
- 手動調用每個組件
- 為 I4 詳細版硬編碼10個步驟的進度邏輯
- 如果新增風格，需要寫新的進度邏輯

**代碼量**：~600行

**問題**：
- ⚠️ 不符合 Pipeline 架構理念
- ⚠️ 無法輕易新增風格
- ⚠️ 進度邏輯和處理邏輯混在一起

### 新版（app.py，原 app_fine_grained.py）

**特點**：
- 使用細粒度組件
- 萬用的動態步驟執行邏輯
- 新增風格只需配置步驟列表

**代碼量**：~270行

**優勢**：
- ✅ 完全符合 Pipeline 架構
- ✅ 真正萬用（所有風格統一邏輯）
- ✅ 代碼簡潔（減少55%）
- ✅ 詳細結果自動顯示

---

## 檔案結構

### 核心檔案

```
/
├── app.py                                    # 主程式（細粒度版本）
├── src/
│   ├── config.py                            # API 配置
│   ├── prompts.py                           # Prompt 模板
│   ├── utils.py                             # 工具函數
│   └── pipeline/
│       ├── components_fine_grained.py       # 12個細粒度組件 ⭐
│       ├── style_configs_fine_grained.py    # 細粒度風格配置 ⭐
│       └── engine.py                        # 通用引擎
├── templates/
│   └── index.html                           # 前端界面
└── 文檔/
    ├── PIPELINE_COMPLETE_GUIDE.md           # 本文件 ⭐
    ├── PIPELINE_ARCHITECTURE_GUIDE.md       # 架構指南
    ├── FINE_GRAINED_PIPELINE_SUMMARY.md     # 細粒度總結
    └── BODY_INSTRUCTIONS_ANALYSIS.md        # Body Instructions 分析
```

### 舊版備份

```
app_old_backup_20251209.py  # 舊版 app.py（粗粒度架構）
src/pipeline/
├── components.py           # 舊的粗粒度組件（保留）
└── style_configs.py        # 舊的粗粒度配置（保留）
```

---

## 使用指南

### 啟動服務

```bash
# 方式1：直接運行
uv run python app.py

# 方式2：使用運行腳本
./run.sh

# 自動選擇可用端口（從 8000 開始）
```

### 訪問界面

```
http://127.0.0.1:8000  # 或自動分配的端口
```

### 選擇風格

前端下拉選單：
1. **I4 詳細版**（推薦）- 完整流程（10步驟）
2. **萬能智能版**（實驗）- 極簡流程（1步驟）
3. **I4 簡化版**（快速）- 快速版（3步驟）

---

## API 調用次數對比

| 風格 | 檢測類型 | 檢測身體 | AI生成 | 總計 |
|------|---------|---------|--------|------|
| I4 詳細版（照片） | 1次 | 1次 | 1次 | **3次** |
| I4 詳細版（插畫） | 1次 | 0次 | 1次 | **2次** |
| 萬能智能版 | 0次 | 0次 | 1次 | **1次** |
| I4 簡化版 | 0次 | 0次 | 1次 | **1次** |

---

## 未來擴展

### 新增風格（5分鐘）

只需在 `style_configs_fine_grained.py` 添加配置：

```python
STYLE_C_INK_BRUSH = {
    "name": "墨線筆觸風格",
    "steps": [
        {"component": fg.detect_image_type, ...},
        {"component": fg.rembg_remove_background, ...},
        {"component": fg.ai_generate_ink_style, ...},  # 新組件
        {"component": fg.make_white_transparent, ...}
    ]
}
```

### 新增組件（10分鐘）

只需在 `components_fine_grained.py` 添加函數：

```python
def ai_generate_ink_style(image: Image.Image, context: dict) -> Image.Image:
    """AI 生成墨線筆觸風格"""
    # 使用特殊的墨線 Prompt
    # 調用 Gemini API
    # 返回結果
```

---

## 總結

### 核心成就

1. **細粒度組件**：12個獨立組件，每個對應一個具體步驟
2. **萬用邏輯**：所有風格使用同一套執行代碼
3. **自動顯示**：詳細步驟和結果自動顯示
4. **靈活組合**：輕鬆組合不同步驟創建新風格
5. **條件執行**：自動處理照片/插畫的差異

### 達成的目標

- ✅ 實現了您要求的萬用即時通知
- ✅ 把所有子步驟變為獨立步驟
- ✅ 確實顯示每個步驟的詳細結果
- ✅ 新 Pipeline 架構完全符合設計理念

### 當前狀態

**主程式**：`app.py`（細粒度版本）  
**服務地址**：http://127.0.0.1:8000（自動端口）  
**準備就緒**：可以開始使用和測試！

---

**細粒度 Pipeline 架構已完成，實現真正萬用的動態步驟顯示！** 🎉

