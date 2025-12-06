# UV 使用指南

本專案已遷移至使用 **uv** 進行 Python 依賴管理。

## 為什麼使用 uv？

- 🚀 **速度快**：比 pip 快 10-100 倍
- 🦀 **基於 Rust**：更穩定可靠
- 🎯 **現代化**：支援最新的 Python 包管理標準
- 📦 **自動管理**：自動創建和管理虛擬環境

## 常用命令

### 安裝依賴

```bash
# 同步所有依賴（首次使用或更新時）
uv sync

# 添加新依賴
uv add package-name

# 添加開發依賴
uv add --dev package-name

# 移除依賴
uv remove package-name
```

### 運行專案

```bash
# 運行 Gradio 網頁介面
uv run python app.py

# 或使用便捷腳本
./run.sh

# 運行命令行工具
uv run python main.py -i input.jpg

# 運行多風格版本
uv run python app_multistyle.py
```

### 使用已定義的腳本入口

```bash
# 這些是在 pyproject.toml 中定義的腳本
uv run tempo30 -i input.jpg              # 命令行工具
uv run tempo30-gradio                     # Gradio 介面
uv run tempo30-multistyle                 # 多風格版本
```

### 其他常用命令

```bash
# 查看已安裝的包
uv pip list

# 更新依賴
uv sync --upgrade

# 清理快取
uv cache clean

# 查看虛擬環境路徑
uv venv --python-preference only-managed
```

## 專案結構

```
.
├── pyproject.toml          # uv 專案配置（替代 requirements.txt）
├── .venv/                  # uv 自動管理的虛擬環境
├── run.sh                  # 快速啟動腳本
├── app.py                  # Gradio 網頁介面
├── main.py                 # 命令行工具
└── src/                    # 核心邏輯模組
```

## 遷移說明

✅ **已完成的遷移步驟：**

1. 創建 `pyproject.toml` 配置文件
2. 使用 uv 安裝所有依賴
3. 修復 Gradio 6.x API 兼容性問題
4. 添加腳本入口點
5. 更新 README 文檔

📦 **依賴變更：**

- 從 `requirements.txt` 遷移到 `pyproject.toml`
- 所有依賴已升級到最新穩定版本
- 自動添加 `onnxruntime`（rembg 需要）

🎯 **下次使用時：**

直接運行 `./run.sh` 或 `uv run python app.py` 即可！

