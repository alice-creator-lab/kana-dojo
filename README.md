# 五十音練習（kana-dojo）

免費五十音練習 webapp，獨立於「日語階梯」課程站，用來接觸新學習者。

## 內容
- 平假名／片假名、濁音・半濁音・拗音
- 發音：Azure Speech（`ja-JP-MayuNeural`，語速 −10%），音檔在 `audio/m/`（105 段）
- 手寫筆順（`kana-templates.json` 筆順資料）、聽音選字、日文鍵盤輸入
- 錯題簿、連續練習天數、進度紀錄（存本機 `localStorage`）

## 開發
純靜態：`index.html` ＋ `audio/m/` ＋ `kana-templates.json`，直接開檔或用任何靜態伺服器。

重新生成音檔（需 `AZURE_SPEECH_KEY`／`AZURE_SPEECH_REGION`）：

```
python3 tools/make_kana_audio.py --engine azure --voice ja-JP-MayuNeural --rate -10% --dir audio/m --force
python3 tools/trim_seq_audio.py audio/m --force --copy --head 0.10 --tail 0.25
```

## 部署
GitHub Pages：`main` 分支根目錄 → https://alice-creator-lab.github.io/kana-dojo/

## 版本
版本號用「主.次.修」：大改版跳主號（2.0），加功能升次號（1.1），文字或小修升修號（1.0.1）。寫在頁面 `verTag`。音檔路徑固定為 `audio/m/<羅馬字>.mp3`（`を` 另用 `wo-chart.mp3`），更新音檔後如遇手機快取，可改檔名或加查詢參數。

## 五十音筆順字帖
`downloads/kana-worksheet.pdf`：17 頁 A4，封面＋平假名／片假名各 46 字；每行四格＝筆順字（附 1/2/3 筆順）→ 兩格虛線描紅 → 一格空白。
重新產生：`python3 tools/make_worksheet.py`（字形取自 KanjiVG，快取在 `cache/kanjivg/`）。
字形授權 CC BY-SA 4.0，字帖屬衍生作品，同樣以 CC BY-SA 4.0 提供；封面的署名不可移除。
