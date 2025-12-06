#!/bin/bash
# 系統驗證腳本 - 快速檢查專案是否正常

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  圖片風格轉換工具 - 系統驗證"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$(dirname "$0")"

# 1. 檢查 Python 環境
echo "【1】檢查 Python 環境..."
if uv run python --version > /dev/null 2>&1; then
    VERSION=$(uv run python --version)
    echo "✅ $VERSION"
else
    echo "❌ Python 環境異常"
    exit 1
fi

# 2. 檢查依賴
echo ""
echo "【2】檢查核心依賴..."
if uv run python -c "import gradio, PIL, rembg, numpy" 2>/dev/null; then
    echo "✅ 核心依賴完整"
else
    echo "❌ 缺少依賴，請運行: uv sync"
    exit 1
fi

# 3. 檢查環境變數
echo ""
echo "【3】檢查環境變數..."
if [ -f .env ]; then
    if grep -q "GEMINI_API_KEY" .env; then
        echo "✅ .env 文件配置正確"
    else
        echo "⚠️  .env 缺少 GEMINI_API_KEY"
    fi
else
    echo "❌ 找不到 .env 文件"
    exit 1
fi

# 4. 檢查核心模組
echo ""
echo "【4】檢查核心模組..."
if uv run python -c "from src.style_converter import StyleConverter; from src.config import API_CONFIG" 2>/dev/null; then
    echo "✅ 核心模組正常"
else
    echo "❌ 核心模組異常"
    exit 1
fi

# 5. 檢查 app.py
echo ""
echo "【5】檢查 app.py..."
if uv run python -c "import app; interface = app.create_interface()" 2>/dev/null; then
    echo "✅ app.py 可以正常運行"
else
    echo "❌ app.py 有問題"
    exit 1
fi

# 6. 檢查是否已經在運行
echo ""
echo "【6】檢查服務狀態..."
if lsof -i :7860 > /dev/null 2>&1; then
    echo "✅ 服務正在運行"
    echo "   → 訪問: http://127.0.0.1:7860"
else
    echo "⚠️  服務未運行"
    echo "   → 啟動: ./run.sh 或 uv run python app.py"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ 系統驗證完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

