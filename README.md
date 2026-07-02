# 📡 Paper Radar（公共行政版）

個人化論文追蹤雷達：每天自動從 Crossref 抓取 14 本公共行政期刊的新文章，
依你的研究興趣（PSM、倫理行為、Do No Harm…）評分排序，呈現在一個手機也好用的網頁上。

靈感來自 [drpwchen/paper-radar](https://github.com/drpwchen/paper-radar)，
改為 **GitHub Actions + GitHub Pages** 架構——不需要伺服器、不需要 Cloudflare、零依賴套件。

## 架構

```
GitHub Actions（每天台北時間 6:00）
    └─ fetch_and_score.py
         ├─ Crossref API 抓 14 本期刊近 30 天新文章（含摘要）
         ├─ 依 interest_model.json 關鍵字權重評分
         └─ 寫入 docs/papers.json 並 commit
GitHub Pages（/docs）
    └─ index.html 讀 papers.json 渲染
         └─ ✅已看 / ⭐想細讀 / 👍👎 存在瀏覽器 localStorage
```

## 檔案說明

| 檔案 | 用途 |
|---|---|
| `config.json` | 追蹤哪些期刊（ISSN）、回溯天數、保留天數 |
| `interest_model.json` | 關鍵字權重表——**調整口味改這裡** |
| `fetch_and_score.py` | 抓取 + 評分腳本（純標準函式庫） |
| `docs/index.html` | 前端網頁 |
| `docs/papers.json` | 自動產生的資料（勿手動編輯） |
| `.github/workflows/update.yml` | 每日自動更新排程 |

## 本機測試

```bash
python3 fetch_and_score.py        # 抓取並產生 docs/papers.json
python3 -m http.server -d docs    # 開 http://localhost:8000 預覽
```

## 部署（一次性設定）

1. 在 GitHub 建立新 repo（例如 `paper-radar`），把這個資料夾推上去
2. Repo → **Settings → Pages** → Source 選 `Deploy from a branch`，
   Branch 選 `main`、資料夾選 `/docs`，按 Save
3. Repo → **Actions** 頁面確認 workflow 已啟用（第一次可按 Run workflow 手動跑）
4. 網址就是 `https://你的帳號.github.io/paper-radar/`

> 注意：免費帳號的 GitHub Pages 一定是公開網頁（雖然標了 noindex 不被搜尋引擎收錄）。
> 網頁內容只是論文清單，你的勾選記錄存在自己瀏覽器裡，不會上傳。

## 調整口味

- **加期刊**：在 `config.json` 的 `journals` 加一筆 `{"name": "...", "issn": "..."}`（用電子版 ISSN）
- **改權重**：編輯 `interest_model.json`，分數 = Σ 權重 ×（標題出現次數×2 + 摘要出現次數）
- **改更新時間**：編輯 `.github/workflows/update.yml` 的 cron（注意是 UTC 時間）

評分覺得不準時，看看高分卡片上亮起的關鍵字標籤，把不想要的降權重、常漏掉的主題加進去，隔天就會生效。
