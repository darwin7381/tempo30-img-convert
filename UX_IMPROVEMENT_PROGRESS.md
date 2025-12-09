# UX 改進：模擬進度顯示

## 問題

**之前的體驗**：
```
步驟開始 → 0%
（卡住很久...用戶不知道是否還在處理）
步驟完成 → 100%
```

**問題**：
- 用戶看到進度條卡在 0%，不知道是否在處理
- 沒有視覺反饋，體驗差
- 特別是 AI 生成步驟（15-30秒），完全沒有進度更新

---

## 解決方案

**模擬進度 + 真實完成**：

```
步驟開始 → 0%
模擬進度 → 5% → 10% → 15% → ... → 85%
（持續更新，讓用戶知道還在處理）
實際完成 → 95% → 100%（快速跳轉）
```

### 實現邏輯

```python
# 1. 步驟開始時，啟動模擬進度任務
progress_task = asyncio.create_task(
    simulate_progress(websocket, step_id, ...)
)

# 2. 模擬進度異步運行
async def simulate_progress(...):
    for pct in range(5, 85, 5):  # 從 5% 到 85%
        await send_progress({'step_progress': pct})
        await asyncio.sleep(0.3)  # 每 0.3 秒更新一次

# 3. 實際組件執行（同步）
result = component(image, context)

# 4. 完成時停止模擬，快速跳到 100%
progress_task.cancel()
await send_progress({'step_progress': 95})  # 先到 95%
await send_progress({'step_progress': 100}) # 再到 100%
```

### 不同步驟的進度速度

| 步驟類型 | 最大模擬進度 | 更新間隔 | 原因 |
|---------|-------------|---------|------|
| AI 生成 | 85% | 0.5秒 | 真的很慢（15-30秒），慢速進度更真實 |
| 檢測類型 | 80% | 0.3秒 | 中等速度（2-3秒） |
| 其他處理 | 90% | 0.2秒 | 較快（<1秒），快速進度 |

**為什麼不到 100%**：
- 留空間給真實完成時快速跳到 100%
- 讓用戶感受到「完成」的瞬間

---

## 改進效果

### 之前

```
步驟7: AI生成插畫 - 0%
（等待 20 秒，進度條完全不動）
步驟7: AI生成插畫 - 100%
```

**用戶感受**：卡住了？崩潰了？

### 現在

```
步驟7: AI生成插畫 - 0%
步驟7: AI生成插畫 - 5%
步驟7: AI生成插畫 - 10%
步驟7: AI生成插畫 - 15%
...
步驟7: AI生成插畫 - 80%
步驟7: AI生成插畫 - 85%
（實際完成）
步驟7: AI生成插畫 - 95%
步驟7: AI生成插畫 - 100% ✅
```

**用戶感受**：正在處理中，有進展！

---

## 技術細節

### 異步任務控制

```python
# 創建模擬進度任務
progress_task = asyncio.create_task(simulate_progress(...))

# 執行實際處理（阻塞）
result = component(image, context)

# 取消模擬進度
progress_task.cancel()

# 等待任務結束
try:
    await progress_task
except asyncio.CancelledError:
    pass  # 正常取消
```

### 進度計算

```python
# 步驟內進度
step_progress = 5% → 85%

# 整體進度
overall_progress = (step_id - 1 + step_progress/100) / total_steps * 100

# 例如：第3步進行到50%
overall_progress = (3 - 1 + 0.5) / 10 * 100 = 25%
```

---

## 總結

**改進點**：
1. ✅ 每個步驟開始時**立即**顯示進度更新（無延遲）
2. ✅ 根據步驟類型調整模擬速度
3. ✅ 實際完成時快速跳到 100%
4. ✅ 步驟間無縫銜接（上一步100% → 下一步立即5%）

**用戶現在會看到**：
- 持續的進度更新（不會卡住）
- 步驟間流暢過渡（無停頓感）
- 符合實際處理時間的進度速度
- 完成時的明確反饋

### 關鍵改進：立即進度

**修改前**：
```python
# 步驟開始
await send_progress({'step_progress': 0})
# 啟動模擬任務
progress_task = asyncio.create_task(simulate_progress(...))
# 模擬任務內：await sleep(0.5) → 發送 5%
```
**問題**：0% → （等待0.5秒）→ 5%

**修改後**：
```python
# 步驟開始
await send_progress({'step_progress': 0})
# 啟動模擬任務
progress_task = asyncio.create_task(simulate_progress(...))
# 模擬任務內：立即發送 5% → await sleep(0.5) → 發送 10%
```
**效果**：0% → 立即5% → （等待0.5秒）→ 10%

**無縫銜接！**

