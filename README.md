# 圖片風格轉換工具

向量插畫風格轉換工具，將照片轉換為半寫實企業頭像風格。

## ✨ 功能特點

- **向量插畫風格**：乾淨線條、高對比、扁平色彩
- **半寫實企業頭像風格**：專業、自信的商業外觀
- **賽璐璐著色（cel-shaded）**：硬陰影、清晰邊界
- **隨機高光效果**：橘色/金色邊緣光，背後光源，隨機角度
- **透明背景**：自動去除白色背景
- **身體生成機制**：自動處理不同構圖
  - 如果只有脖子，生成到胸部
  - 如果全身，裁切到胸部以上
- **統一尺寸和位置**：確保所有輸出圖片一致
- **✨ 即時進度顯示**：清楚看到每個處理步驟和進度百分比

## 安裝

本專案使用 [uv](https://docs.astral.sh/uv/) 進行 Python 依賴管理，速度比 pip 快 10-100 倍。

### 安裝 uv（如果還沒安裝）

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 Homebrew
brew install uv
```

### 安裝專案依賴

```bash
# uv 會自動創建虛擬環境並安裝所有依賴
uv sync
```

## 配置

在專案根目錄創建 `.env` 文件，並添加您的 Gemini API Key：

```
GEMINI_API_KEY=your_api_key_here
```

## 使用方法

### 方法 1：FastAPI 網頁介面（推薦）

```bash
# 使用啟動腳本
./run.sh

# 或直接使用 uv
uv run python app.py
```

然後在瀏覽器訪問 http://127.0.0.1:8000（或自動分配的端口）

**新版本特色**：
- ✅ 動態步驟顯示（根據圖片類型6-7步）
- ✅ 所有步驟都有子步驟詳情
- ✅ 進度分配符合實際耗時
- ✅ 狀態真正疊加在圖片上
- ✅ 現代化美觀設計
- ✅ WebSocket 即時推送

### 方法 1-B：Gradio 網頁介面（備份）

如果需要使用 Gradio 版本：

```bash
uv run python app_Gradio.py
```

### 方法 2：命令行工具

```bash
uv run python main.py --input photo.jpg --output result.png
```

參數說明：
- `-i, --input`: 輸入圖片路徑（必需）
- `-o, --output`: 輸出圖片路徑（可選，預設為輸入文件名_style.png）
- `-q, --quiet`: 安靜模式（不顯示處理過程）

### 範例

```bash
# 基本使用
uv run python main.py -i photo.jpg

# 指定輸出路徑
uv run python main.py -i photo.jpg -o output/result.png

# 安靜模式
uv run python main.py -i photo.jpg -q
```

## 文件結構

```
.
├── main.py                 # 主程式入口
├── src/
│   ├── __init__.py
│   ├── style_converter.py  # 風格轉換核心邏輯
│   ├── gemini_client.py    # Gemini API 客戶端
│   └── image_processor.py # 圖片處理工具
├── requirements.txt        # Python 依賴
├── .env                    # 環境變數（需自行創建）
└── README.md              # 本文件
```

## 輸出說明

- 輸出格式：PNG（支援透明背景）
- 輸出尺寸：1000x1000 像素（可自訂）
- 構圖：頭部到上胸部（upper chest）
- 人物位置：水平置中，頭部在畫面上方 35% 位置

## 注意事項

- 需要有效的 Gemini API Key
- 處理時間約 20-40 秒（AI 生成最耗時）
- 建議使用高品質的輸入圖片以獲得最佳效果

## 📚 文檔導覽

- **README.md**（本文件）- 快速開始指南
- **WORKFLOW_COMPLETE.md** - 完整處理流程分析（照片10步/插畫8步，實際執行順序）
- **BODY_INSTRUCTIONS_ANALYSIS.md** - Body Instructions 設計分析（必要性、替代方案）
- **TECHNICAL_NOTES.md** - 技術細節、API 配置、優化建議
- **STYLE_DOCUMENTATION.md** - 風格設計規範、Prompt 模板
- **UV_USAGE.md** - uv 包管理器使用指南

