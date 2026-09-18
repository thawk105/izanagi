---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2775-a1-sized-results-draft
seq: 2
---

## 再発

### F1

- **再発: 2026-09-18 (2 件。1 件は他 wave の凍結記録に残った実害、1 件は本 wave の near miss)** — (1) [T-1505] の記録 insight
  `output/insights/2026-09-18/t1505-a1-sized-attempt1/README.md` §4 の表は、balanced と read-heavy の verify `commits` 数を
  入れ替えて記載している (balanced に 516607 / 515988、read-heavy に 466561 / 483318。WAL の `verify_done` と同 insight の
  `receipts/job-stdout-{balanced,read-heavy}.txt` は逆)。取り違えの経緯は同 wave の記録に無く本 wave は推測しない。
  A-1 attempt-0001 の単独 results 稿を書く本 wave が WAL を直接読んで検出した。他文書 (paper-story README の stale 注記・
  worklog) には波及していない (`grep 516607|466561` は insight 表と job stdout だけ)。insight は凍結記録なので書き換えず、
  results 稿 §2.4 と本 wave の insight が正しい値と差分を明記する。(2) 本 wave の親が results 稿 §2.2 の 180 標本の表を
  記憶から手打ちして全行を誤り、§1.1 の read-heavy `planned_sigma_tps` の文字列も末尾 2 桁を誤った (`…46` → 現物 `…48`)。
  後者は親が現物を読み直して commit 前に直し、前者は「180 標本を見ていない」と気づいた時点で表を現物 result.json からの
  機械生成 (`pairs_tables.py`) に差し替えた。その後、稿の全 sha256 (64 / 40 hex)・§2.1〜§2.4・§1.4・§5 の数値を権威 bytes から
  再計算して突き合わせる機械照合 (`check_draft.py`、PROBLEMS 0 / ok 62) を commit 前に通した。転写対象が hash の手打ち
  (2026-09-18 の前件) から**標本表の手打ちと、1 手で複数 file を読んだ転写**へ広がった顕在化。恒久対応は変更なし —
  results 稿の数表は現物から script で生成し、稿へ入れる値は機械照合を通すまで根拠にしない (`DW-O16`)。
  一次資料は `output/insights/2026-09-18/t2775-a1-sized-results-draft/README.md`。
