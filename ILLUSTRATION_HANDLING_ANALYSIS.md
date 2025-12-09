# 插畫處理分析

## 問題

插畫被重新生成，看起來不一樣了。為什麼？

---

## 原版邏輯檢查

### 原版對插畫的處理（已確認）

**檔案**：`style_i4_converter.py` line 676-682

```python
if image_type == "illustration":
    # 插畫也進行 AI 生成轉換！
    result = self.convert_to_cartoon_illustration(image, body_extent="head_chest")
    
    # 處理透明背景
    if transparent_bg:
        result = self.make_white_transparent(result)
```

**關鍵事實**：
- ✅ 插畫也會用 AI 重新生成（不是保持原圖）
- ✅ body_extent 固定為 "head_chest"
- ✅ 使用 "head_chest" 的 BODY_INSTRUCTION

---

### head_chest 的 BODY_INSTRUCTION

**原版內容**（已確認完全相同）：
```
CRITICAL INSTRUCTION - BODY COMPOSITION (MANDATORY):
- The input photo already shows HEAD to UPPER CHEST (upper torso)
- Maintain that composition, ensuring the bottom edge is at the upper chest level
- The OUTPUT MUST show from head to UPPER CHEST (upper torso)
```

**關鍵詞**：
- ✅ "Maintain that composition"（保持構圖）
- ✅ "ensuring the bottom edge at upper chest"
- ✅ "shows HEAD to UPPER CHEST"

**邏輯**：
- 告訴 AI「已經是理想構圖」
- 「保持」這個構圖
- 只需要轉換風格

---

## 當前實現檢查

### 當前 Prompt（已驗證）

```python
# src/prompts.py
BODY_INSTRUCTIONS["head_chest"] = """CRITICAL INSTRUCTION - BODY COMPOSITION (MANDATORY):
- The input photo already shows HEAD to UPPER CHEST (upper torso)
- Maintain that composition, ensuring the bottom edge is at the upper chest level
- The OUTPUT MUST show from head to UPPER CHEST (upper torso)"""
```

**確認**：✅ 與原版完全相同

### 當前處理流程

```python
# Pipeline components.py
analysis = gemini_25_analysis(image)  # → "illustration"
body_extent = "head_chest"  # 插畫固定為此

processed = no_preprocess(image)  # 不去背

result = detailed_style_generate(image, {"body_extent": "head_chest"})
  ↓ 使用 get_style_prompt("head_chest")
  ↓ 包含 "Maintain that composition"
  ↓ AI 生成
```

**確認**：✅ 邏輯與原版一致

---

## 為何還是改變了？

### 可能的原因

#### 原因1：Prompt 順序（已修復）

**之前**：
```python
contents=[image, prompt]  # Image 在前
```

**影響**：
- AI 先看到圖片
- 「Maintain composition」的指令可能被忽略
- AI 可能理解為「創建類似風格的新圖」

**現在（已修復）**：
```python
contents=[prompt, image]  # Prompt 在前
```

**效果**：
- AI 先看到「Maintain composition」
- 明確知道要保持構圖
- 應該保持姿勢

---

#### 原因2：模型版本差異

**檢查**：原版用什麼模型？

**原版**：
```python
response = self.client.models.generate_content(
    model="gemini-3-pro-image-preview",  # 圖片生成
    ...
)
```

**當前**：
```python
response = client.models.generate_content(
    model=API_CONFIG.model_image,  # = "gemini-3-pro-image-preview"
    ...
)
```

**確認**：✅ 模型相同

---

#### 原因3：Prompt 內容差異（需仔細對比）

讓我對比完整 Prompt 的每個部分...

**原版 Prompt 結構**（從 line 222-327）：
1. Transform this photo into a VECTOR ILLUSTRATION...
2. {body_instruction}
3. ARTISTIC STYLE
4. CHARACTER EXPRESSION & FEATURES
5. COLORING STYLE
6. LIGHTING & SHADING
7. RIM LIGHTING EFFECT
8. DETAIL FEATURES
9. PROPORTIONS
10. CROP & COMPOSITION
11. COLORS
12. BACKGROUND
13. OUTPUT
14. Create a VECTOR ILLUSTRATION... (最後總結)

**當前 Prompt 結構**（src/prompts.py）：
1. Transform this photo into a VECTOR ILLUSTRATION...
2. {body_instruction}
3. ARTISTIC STYLE
4. CHARACTER EXPRESSION & FEATURES
5. COLORING STYLE
6. LIGHTING & SHADING
7. RIM LIGHTING EFFECT
8. DETAIL FEATURES
9. PROPORTIONS
10. CROP & COMPOSITION
11. COLORS
12. BACKGROUND
13. OUTPUT
14. Create a VECTOR ILLUSTRATION... (最後總結)

**確認**：✅ 結構完全相同

---

### 問題定位

**如果 Prompt 和模型都相同，為何結果不同？**

**可能性排查**：

#### 1. 隨機性

**Gemini 3 Pro Image 有隨機性**：
- Temperature 參數
- 每次生成可能略有不同

**測試**：
- 用相同圖片測試3次
- 看結果是否一致

#### 2. Prompt 順序（應該已修復）

**確認修復狀態**：
- [x] Prompt 在前（已修復）
- [x] Image 在後（已修復）

#### 3. Context 資訊不完整

**檢查**：
```python
context = {"body_extent": "head_chest"}
```

**原版**：
```python
# 直接傳遞 body_extent 參數
self.convert_to_cartoon_illustration(image, body_extent="head_chest")
```

**當前**：
```python
# 從 context 讀取
body_extent = context.get("body_extent", "head_chest")
```

**可能問題**：
- Context 傳遞可能有問題
- body_extent 可能不是 "head_chest"

---

## 檢查點

請協助確認：

1. **插畫被分類為什麼**？
   - 從圖二看：「圖片類型: 像素插畫 | 身體範圍: 全身照 (FULL_BODY)」
   - ⚠️ 這裡有問題！

2. **body_extent 應該是什麼**？
   - 原版：插畫 → body_extent = "head_chest"（固定）
   - 當前：插畫 → body_extent = "full_body"（從圖二）
   - ❌ 錯誤！

3. **FULL_BODY 的指令是什麼**？
   ```
   CRITICAL INSTRUCTION - BODY COMPOSITION (MANDATORY):
   - You MUST CROP the composition to show ONLY from head to UPPER CHEST
   - Remove all lower body parts
   ```
   - ❌ 這會讓 AI 重新構圖（裁切）！

---

## 問題根源

**發現**：插畫的 body_extent 被設為 "full_body" 而非 "head_chest"！

**原因**：我的實現可能在分析時沒有正確處理插畫的 body_extent。

**修復方向**：
- 確保插畫的 body_extent 固定為 "head_chest"
- 而不是從分析結果獲取

讓我立即修復...

EOF

