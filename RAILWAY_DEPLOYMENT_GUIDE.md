# Railway 部署指南

## 📦 專案簡介

這是一個 **FastAPI + Python** 圖片風格轉換工具，支援部署到 Railway 平台。

## 🚀 部署步驟

### 1️⃣ 準備 GitHub Repository

確保你的專案已經推送到 GitHub：

```bash
git add .
git commit -m "準備部署到 Railway"
git push origin main
```

### 2️⃣ 在 Railway 創建專案

1. 前往 [Railway](https://railway.app/)
2. 登入或註冊帳號（可用 GitHub 登入）
3. 點擊 **"New Project"**
4. 選擇 **"Deploy from GitHub repo"**
5. 選擇你的 `Tempo30_img_convert` repository
6. Railway 會自動檢測到這是 Python 專案

### 3️⃣ 設定環境變數

Railway 部署後，需要設定以下環境變數：

1. 在 Railway 專案面板中，點擊你的服務
2. 前往 **"Variables"** 標籤
3. 添加以下環境變數：

| 變數名稱 | 說明 | 必需 |
|---------|------|------|
| `GEMINI_API_KEY` | Google Gemini API Key | ✅ 必需 |
| `PORT` | 端口號 | ⚠️ Railway 自動提供，無需手動設定 |

**如何獲取 Gemini API Key：**
- 前往 [Google AI Studio](https://makersuite.google.com/app/apikey)
- 創建或獲取你的 API Key
- 複製並貼到 Railway 的 `GEMINI_API_KEY` 變數中

### 4️⃣ 部署配置

Railway 會自動檢測以下檔案：

#### ✅ Procfile（已創建）
```
web: uvicorn app:app --host 0.0.0.0 --port $PORT
```

這告訴 Railway 如何啟動你的 FastAPI 應用程式。

#### ✅ 依賴管理

Railway 支援以下任一方式：

**選項 A：使用 requirements.txt**（推薦給 Railway）
```txt
google-generativeai>=0.8.0
google-genai>=1.0.0
Pillow>=10.0.0
rembg>=2.0.50
python-dotenv>=1.0.0
numpy>=1.24.0
scipy>=1.10.0
requests>=2.28.0
fastapi>=0.123.9
uvicorn>=0.38.0
websockets>=15.0.1
```

**選項 B：使用 pyproject.toml**（本專案已有）

Railway 會自動安裝 `pyproject.toml` 中定義的依賴。

### 5️⃣ 自動部署

1. Railway 會自動開始建置和部署
2. 建置過程約需 3-5 分鐘（首次部署）
3. 部署完成後，Railway 會提供一個公開 URL

### 6️⃣ 訪問你的應用程式

部署成功後：

1. 在 Railway 專案面板中找到 **"Deployments"**
2. 點擊最新的部署
3. 複製提供的 **Public URL**（格式：`https://your-app.up.railway.app`）
4. 在瀏覽器訪問該 URL

## 🔍 驗證部署

### 檢查應用程式狀態

訪問你的 Railway URL：
- 首頁：`https://your-app.up.railway.app/`
- API 文檔：`https://your-app.up.railway.app/docs`（FastAPI 自動生成）
- 風格列表：`https://your-app.up.railway.app/api/styles`

### 查看日誌

在 Railway 專案面板中：
1. 點擊你的服務
2. 前往 **"Deployments"** 標籤
3. 點擊最新部署查看即時日誌

成功啟動的日誌應該顯示：
```
🚀 啟動圖片風格轉換工具（Railway 生產環境）
--------------------------------------------------
📡 端口: 8080
🌐 監聽: 0.0.0.0
--------------------------------------------------
✨ 特點：
  - I4 詳細版：10 個細粒度步驟（照片）/ 8 個步驟（插畫）
  - 萬能智能版：1 個步驟（極簡流程）
  - 所有風格統一萬用邏輯
--------------------------------------------------
```

## ⚙️ 進階設定

### 自動部署

Railway 預設會在你推送到 GitHub 時自動部署：

```bash
# 本地修改後
git add .
git commit -m "更新功能"
git push origin main

# Railway 會自動觸發重新部署
```

### 暫停部署

如果想暫時關閉自動部署：
1. 在 Railway 專案中，前往 **"Settings"**
2. 找到 **"Automatic Deployments"**
3. 關閉該選項

### 環境分離

建議創建多個 Railway 專案：
- **Production**：主分支，穩定版本
- **Staging**：開發分支，測試新功能

## 🐛 常見問題

### ❌ 部署失敗：找不到模組

**原因：** 依賴沒有正確安裝

**解決方案：**
1. 確保 `requirements.txt` 包含所有依賴
2. 或確保 `pyproject.toml` 正確配置
3. 檢查 Railway 建置日誌中的錯誤訊息

### ❌ 應用程式啟動但無法訪問

**原因：** 應用程式沒有監聽正確的 host 和 port

**解決方案：**
- 確保 `app.py` 已修改為支援 `PORT` 環境變數
- 確保監聽 `0.0.0.0`（而非 `127.0.0.1`）

### ❌ 圖片處理失敗

**原因：** 缺少 Gemini API Key 或 API 限制

**解決方案：**
1. 檢查 Railway 環境變數中的 `GEMINI_API_KEY` 是否正確
2. 確認 API Key 有效且有配額
3. 查看應用程式日誌中的錯誤訊息

### ❌ 建置時間過長

**原因：** 安裝 `rembg` 等大型依賴需要時間

**解決方案：**
- 這是正常的，首次建置需要 3-5 分鐘
- 後續部署會使用快取，速度會快很多

## 📊 資源使用

Railway 的免費方案限制：
- **執行時間**：每月 500 小時（約 $5 USD 額度）
- **記憶體**：8GB
- **磁碟**：100GB

本專案資源需求：
- **記憶體**：約 1-2GB（取決於圖片處理）
- **CPU**：中等（AI 生成時較高）

**建議：** 監控使用量，避免超出免費額度。

## 🔄 更新部署

### 推送更新

```bash
# 修改代碼
git add .
git commit -m "功能更新"
git push origin main

# Railway 自動重新部署
```

### 手動重新部署

在 Railway 專案面板中：
1. 前往 **"Deployments"**
2. 點擊 **"Redeploy"**

## 📝 檢查清單

部署前確認：

- [ ] ✅ `Procfile` 已創建
- [ ] ✅ `app.py` 已修改為支援 Railway 環境
- [ ] ✅ `requirements.txt` 或 `pyproject.toml` 包含所有依賴
- [ ] ✅ 代碼已推送到 GitHub
- [ ] ✅ Railway 專案已創建並連接 GitHub
- [ ] ✅ 環境變數 `GEMINI_API_KEY` 已設定
- [ ] ✅ 部署成功且應用程式可訪問

## 🎉 完成

恭喜！你的圖片風格轉換工具現在已經部署到 Railway，可以公開訪問了。

---

**需要幫助？**
- Railway 文檔：https://docs.railway.app/
- FastAPI 文檔：https://fastapi.tiangolo.com/
- 本專案 README：[README.md](./README.md)

