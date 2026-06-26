# Claude Pro 用量監控視窗

一個小工具，在螢幕角落顯示你的 Claude Pro 用量，每分鐘自動更新。

---

## 事前準備

1. 確認你的電腦已安裝 **Python 3.10 以上版本**
   - 開啟「命令提示字元」輸入 `python --version`，有顯示版本號就沒問題
   - 尚未安裝請至 [python.org](https://www.python.org/downloads/) 下載

2. 確認你已登入 **[claude.ai](https://claude.ai)**

---

## 第一步：取得 CLAUDE_SESSION_KEY

Session Key 是瀏覽器用來證明「你已登入」的通行證。

> ⚠️ **Session Key 有時效限制，不是永久有效。**
> 即使你沒有登出，它也可能在數天至數週內自動失效。
> 一旦工具顯示錯誤（例如 `❌ 401`），就代表需要重新取得。
> 建議將取得方式記起來，日後定期更新。

1. 用 **Chrome 或 Edge** 開啟 [claude.ai](https://claude.ai)，確認已登入

2. 按 **F12** 開啟開發人員工具

3. 點選上方的 **「Application」** 分頁
   > 若看不到，點工具列最右邊的 `>>` 展開選單

4. 在左側面板找到 **Cookies** → 點展開 → 點 **`https://claude.ai`**

5. 在右側清單中找到名稱為 **`sessionKey`** 的那一列

6. 點那一列，在下方的「Value」欄位框選全部文字（通常以 `sk-ant-sid` 開頭），複製

   > **注意：** 這個值非常長，確保完整複製，不要漏掉任何字元

---

## 第二步：取得 CLAUDE_ORG_ID

Org ID 是你帳號所屬組織的識別碼，通常不會變動。

1. 保持 F12 開發人員工具開啟，切換到 **「Network」** 分頁

2. 按 **F5** 重新整理頁面

3. 在 Network 的搜尋框輸入 **`usage`**

4. 等幾秒後，清單中會出現一筆請求，點選它

5. 在右側 **「Headers」→「Request URL」** 中可以看到類似這樣的網址：
   ```
   https://claude.ai/api/organizations/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/usage
   ```

6. 複製中間那串 `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` 格式的 ID

   > 如果找不到，代表頁面還沒送出請求，可以多等幾秒或切到其他頁面再回來

---

## 第三步：建立設定檔

1. 在工具資料夾中找到 **`.env.example`** 檔案，複製並命名為 **`.env`**

   > Windows 可能不讓你直接建立以「.」開頭的檔案，請用記事本另存新檔時，檔案名稱輸入 `.env`，存檔類型選「所有檔案」

2. 用記事本打開 `.env`，填入剛才取得的兩個值：

   ```
   CLAUDE_SESSION_KEY=sk-ant-sid01-你的完整sessionKey
   CLAUDE_ORG_ID=你的ORG_ID
   ```

   > 等號前後不要有空格，值也不要加引號

3. 存檔

---

## 第四步：安裝套件（只需執行一次）

1. 在工具資料夾空白處，按住 **Shift + 右鍵** → 選「在這裡開啟 PowerShell 視窗」

2. 輸入以下指令並按 Enter：
   ```
   .venv\Scripts\pip install -r requirements.txt
   ```

---

## 第五步：啟動工具

雙擊 **`start_gui.vbs`** 即可啟動，不會出現黑色命令列視窗。

---

## 操作說明

| 操作 | 功能 |
|------|------|
| 拖曳標題列 | 移動視窗位置 |
| 點 **⊟ / ⊞** | 切換完整／精簡模式 |
| 點 **↺** | 立即重新整理 |
| 點 **✕** | 關閉視窗 |
| 拖動底部滑桿 | 調整視窗透明度 |

### 完整模式

顯示兩個用量的進度條、百分比與重置倒數。若 claude.com 當天有事故通報，會自動顯示在下方。

### 精簡模式

縮小為一行，只顯示 `Session% / Weekly%`，方便常駐在螢幕角落。

### 顏色說明

- 綠色 ✓：用量正常
- 橘色 ⚠：用量偏高，注意節省
- 紅色 ●：用量接近上限

---

## 常見問題

**Q：顯示「❌ 401」或「sessionKey 已過期」**
> Session Key 有時效，請重新執行第一步取得新的值，更新 `.env` 後重啟工具。

**Q：視窗出現「❌ 請先設定 CLAUDE_SESSION_KEY」**
> `.env` 檔案未建立，或 `CLAUDE_SESSION_KEY=` 後面的值是空的，請檢查第三步。

**Q：雙擊 `start_gui.vbs` 沒反應**
> 請確認第四步的套件安裝指令有成功執行（沒有出現紅色錯誤訊息）。
