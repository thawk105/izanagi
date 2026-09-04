---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-05
wave: dev-wave-paper-story-backoff-scaffold
seq: 1
---

## {{D:repo-holds-multiple-paper-story-series}}. repo は複数の論文ストーリー系列を持ち、系列ごとに別ディレクトリの同じ凍結契約で管理する

**決定:** `docs/paper-story/` (izanagi 本体の論文) と並んで、`docs/paper-story-backoff/`
(CCBench の adaptive backoff の診断を主題にする単独論文) を**別の論文ストーリー系列**として置く。
系列ごとに独立した `README.md` (腐らない入口)、日付付きの凍結スナップショット、stale 注記を持ち、
契約は `docs/paper-story/README.md` と同じ (append-only、新しい日付の版はその日付時点の正典全体からの
導出、正典は `docs/decisions.md` / `docs/worklog.md` / `output/insights/` の一次資料)。
系列は 1 系列 1 ディレクトリとし、1 つのディレクトリの中で複数論文の版を混ぜない。

**理由:**
- 主題が違う。本体論文は「AI が CC を合成する」を主題にし、backoff はその一事例と基準線の話として
  現れる。backoff の 3 定数の診断 (律速は更新間隔、D1505 / D1506) はそれ自体が独立の主張系列であり、
  本体論文の stale 注記 1 に散らばったまま置くと、執筆時に「窓あたり commit 数」の旧機序が一般化して
  本体論文へ入る (本体論文の README 自身が警告している)。
- 凍結契約は「その日付時点の正典全体からの導出」を要求する。2 論文を 1 系列に畳むと、片方の
  一次資料が動くたびにもう片方まで全面再導出しなければ差分改訂の嘘が生じる。系列を分ければ
  再導出の単位が主題ごとに閉じる。
- 一次資料は共有し、数値と図は共有しない。同じ `output/insights/` と `docs/decisions.md` を
  両系列がそれぞれ独立に引くので、系列間で数値を引き写す経路が要らない。D1013 が版と作業表を
  namespace で分けた理由と同じである。

**却下した選択肢:**
- 本体論文の新しい版の中に backoff 論文の節を足す — 本体論文の版は全面再導出が必要で、
  backoff だけの決着のために本体論文を再導出する費用が釣り合わない。主題も違う。
- `docs/paper-story/` の下にサブディレクトリを切る — 版の履歴表・stale 注記・figures の凍結契約が
  1 ディレクトリで 2 論文分に絡み、どの版がどの論文の最新かが入口から読めなくなる。
- 論文ストーリーを 1 本に限る規則を置く — 診断の材料は既に一次資料として存在し、置き場が無いことで
  材料が消えるわけではない。置き場を作らない方が stale の危険が大きい。
