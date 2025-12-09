# Railway 部署經驗教訓

## 🎯 核心問題

### 問題描述
FastAPI 應用程式在 Railway 部署時出現 **502 Bad Gateway** 錯誤，但所有依賴都能正常安裝。

### 錯誤症狀
- ✅ Build 階段成功（所有依賴安裝正常）
- ✅ Container 啟動成功
- ❌ 應用程式無法響應請求（502 錯誤）
- ❌ Deploy Logs 只顯示 "Starting Container"，沒有後續日誌

---

## 🔍 根本原因

### 問題根源：模組頂層 import 觸發重度依賴載入

```python
# ❌ 原始 app.py（失敗）
from src.pipeline.style_configs_fine_grained import FINE_GRAINED_STYLES, STYLE_OPTIONS
# ↑ 在模組載入時立即執行

app = FastAPI(...)
```

### Import 鏈路分析

```
Railway 執行: uvicorn app:app
  ↓
Python 載入 app.py 模組（import 階段）
  ↓
第 19 行: from src.pipeline.style_configs_fine_grained import ...
  ↓
載入 style_configs_fine_grained.py
  ↓
import components_fine_grained
  ↓
components_fine_grained 第 15 行: from rembg import remove as rembg_remove
  ↓
rembg 首次載入時自動下載 AI 模型（u2net.onnx，約 176MB）
  ↓
下載過程需要 2-3 分鐘
  ↓
Railway 健康檢查超時（默認 60 秒）
  ↓
容器被標記為不健康 → 502 Bad Gateway
```

### 為什麼本地開發沒問題？

- **本地環境：** rembg 模型在首次使用後會快取在 `~/.u2net/`
- **本地開發：** 模型已下載，啟動快速
- **Railway 環境：** 每次部署都是全新容器，模型未快取
- **結果：** 每次部署都需要重新下載模型

---

## ✅ 解決方案

### 方案：延遲載入（Lazy Loading）

**核心原則：不在模組載入時 import 重度依賴，而是在首次使用時才載入**

```python
# ✅ 修復版 app_fixed.py（成功）

# 全局變數（初始為 None）
_STYLES_LOADED = False
_FINE_GRAINED_STYLES = None
_STYLE_OPTIONS = None

def load_styles():
    """延遲載入風格配置"""
    global _STYLES_LOADED, _FINE_GRAINED_STYLES, _STYLE_OPTIONS
    
    if not _STYLES_LOADED:
        # 只在首次調用時才執行 import
        from src.pipeline.style_configs_fine_grained import FINE_GRAINED_STYLES, STYLE_OPTIONS
        _FINE_GRAINED_STYLES = FINE_GRAINED_STYLES
        _STYLE_OPTIONS = STYLE_OPTIONS
        _STYLES_LOADED = True
    
    return _FINE_GRAINED_STYLES, _STYLE_OPTIONS

# 在端點中才調用
@app.websocket("/ws/process")
async def process_image_websocket(websocket: WebSocket):
    FINE_GRAINED_STYLES, _ = load_styles()  # ← 首次請求時才載入
    ...
```

### 工作流程

```
Railway 執行: uvicorn app:app
  ↓
Python 載入 app_fixed.py 模組
  ↓
✅ 沒有立即 import style_configs（只定義了 load_styles 函數）
  ↓
✅ FastAPI 應用程式快速啟動（< 5 秒）
  ↓
✅ Railway 健康檢查通過（訪問 /health）
  ↓
✅ 部署成功！
  ↓
用戶首次上傳圖片
  ↓
執行 load_styles() → 載入 style_configs → 載入 rembg → 下載模型
  ↓
✅ 首次請求較慢，但後續請求快速（模型已快取）
```

---

## 📊 性能對比

| 階段 | 原始版本 | 修復版本 |
|------|---------|---------|
| **模組載入** | 2-3 分鐘（下載模型） | < 5 秒 |
| **健康檢查** | ❌ 超時失敗 | ✅ 立即通過 |
| **首次請求** | N/A（無法啟動） | 2-3 分鐘（下載模型） |
| **後續請求** | N/A | < 1 秒（模型已快取） |

---

## 🎓 關鍵經驗教訓

### 1. **雲端部署的啟動時間至關重要**

- Railway、Vercel、Cloud Run 等平台都有健康檢查機制
- 應用程式必須在 **30-60 秒內**啟動並響應
- 超時會導致部署失敗，即使依賴都正確安裝

### 2. **避免在模組頂層執行重操作**

❌ **不要在頂層做的事：**
- 下載大型檔案或模型
- 連接資料庫（除非使用連接池）
- 執行耗時的初始化
- Import 重度依賴（如 ML 模型）

✅ **應該在頂層做的事：**
- Import 輕量級模組
- 定義函數和類別
- 設定常量配置
- 創建 FastAPI app 實例

### 3. **延遲載入是生產環境最佳實踐**

**好處：**
- ⚡ 快速啟動
- 💰 節省資源（只載入需要的）
- 🔄 更好的錯誤隔離
- 🚀 更快的健康檢查

**適用場景：**
- ML/AI 模型（如 rembg, transformers）
- 大型配置檔案
- 資料庫連接
- 第三方 API 客戶端

### 4. **Railway 特殊性**

#### Railway 使用 Nixpacks 建置系統
- 自動檢測 Python 專案（`requirements.txt` 或 `pyproject.toml`）
- 自動安裝依賴
- 使用 `Procfile` 或自動檢測啟動命令

#### 關鍵配置檔案
```
Procfile          # 啟動命令（必需）
requirements.txt  # Python 依賴（推薦）
runtime.txt       # Python 版本（可選）
nixpacks.toml     # 進階建置配置（可選）
```

#### 環境變數
- `PORT` - Railway 自動提供，應用程式必須使用
- 自定義變數 - 在 Railway Dashboard > Variables 設定

### 5. **診斷策略**

當遇到 502 錯誤時：

1. ✅ **創建診斷工具** - 簡單的 FastAPI app 測試環境
2. ✅ **逐步測試** - 測試每個 import 是否成功
3. ✅ **對比差異** - 找出成功版本和失敗版本的差異
4. ❌ **不要瞎猜** - 基於實際錯誤日誌進行診斷

---

## 🔧 標準部署檢查清單

### 部署前

- [ ] 所有依賴在 `requirements.txt` 中明確列出
- [ ] 避免在模組頂層 import 重度依賴
- [ ] 使用延遲載入策略
- [ ] 健康檢查端點（`/health`）存在
- [ ] 應用程式監聽 `0.0.0.0` 和 `$PORT` 環境變數

### 部署後

- [ ] Build Logs 無錯誤
- [ ] Deploy Logs 顯示應用程式啟動成功
- [ ] 訪問 `/health` 返回 200 OK
- [ ] 首頁能正常顯示
- [ ] 功能測試通過

---

## 📚 相關文檔

- [RAILWAY_DEPLOYMENT_GUIDE.md](./RAILWAY_DEPLOYMENT_GUIDE.md) - 完整部署指南
- [PIPELINE_COMPLETE_GUIDE.md](./PIPELINE_COMPLETE_GUIDE.md) - Pipeline 架構說明
- [PIPELINE_ARCHITECTURE_GUIDE.md](./PIPELINE_ARCHITECTURE_GUIDE.md) - 架構設計文檔

---

## 🎉 最終結論

**成功的關鍵：**
1. ✅ 明確所有依賴（包括間接依賴如 `onnxruntime`）
2. ✅ 使用延遲載入避免啟動超時
3. ✅ 簡化啟動邏輯
4. ✅ 系統性診斷而非猜測

**部署時間：** 從首次嘗試到成功解決約 3 小時（包含診斷和多次測試）

**最終狀態：** ✅ 成功部署到 Railway，應用程式完全正常運行

---

**日期：** 2025-12-10  
**專案：** Tempo30 圖片風格轉換工具  
**平台：** Railway.app

