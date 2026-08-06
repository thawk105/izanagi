---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-07
wave: dev-wave-t503-disposable-worktree
seq: 3
---

## 新規

### {{F:stage1-rc-read-through-pipe}}. 段 1 前提実測の rc を pipe 越しに読み、`tail` の rc を実測値として報告した [恒真ゲート] [手順漏れ]

- 事象: 段 1 の前提実測 probe を `command ... | tail -N` の形で書き、直後の `$?` を実測 rc として
  brief に載せた。`pipefail` が無いため読んでいたのは `tail` の rc であり、
  **producer が失敗しても常に 0 が報告される**構造だった。段 3 の敵対レンズ 2 本が独立に指摘した。
- 根本原因: 実測を「読みやすく tail する」ことと「rc を取る」ことを同じ pipeline で行った。
  検査対象の rc が pipeline の最終段に来ないため、gate が恒真化した。
  段 1 brief は子の起動根拠になるので、恒真な前提実測は wave 全体の土台を崩す。
- 恒久対応: 段 1 の前提実測では **producer を pipe の最終段に置くか、`PIPESTATUS` / 出力を
  file へ落として rc を別に取る**。本 wave では pipe を外して測り直し、
  worktree add / submodule init / 受入全走 / `--plan-only` の rc をすべて再取得した
  (逐語 = `output/insights/2026-08-07_t503-disposable-worktree/verbatim/s3-lensA.md` A-8、
  同 `s3-lensB.md` B-13、再測定手順 = 同 README の実測表)。
- 再発検知: 段 3 のレンズ prompt に「親自身の実測値とその一般化も攻撃対象」を入れておくこと
  (`DW-S03` の既存義務)。本件はその義務が実際に発火して検出された事例である。

## 再発

### F106

- **再発: 2026-08-07** — 記録 commit 後の再走 (F34) として受入全走を投入した直後、
  **走行中に誤診断の訂正 commit を作った**。`test_s8b_oracle_driver.py` の
  `test_real_freeze_gate_lists_floor_and_budget_null@real-repo` が `validation_head` の不一致
  (走行開始時の HEAD 対 訂正 commit 後の HEAD) で赤になり、1 failed / 7076 passed になった。
  tree を固定して単独再走すると 7077 passed / 20 skipped で消えた。
  根本原因は F106 と同一で、**長い走行を待ち時間とみなし、その間に別の作業を worktree 内で
  進めた**こと。本 wave の親は変異本走では規律を守れたのに、受入では同じ罠を踏んだ。
  訂正の緊急性を感じたことが「走行中でも短い docs commit なら」という判断を通した。
  恒久対応は F106 のまま。**訂正であっても走行中は repo 外に控え、結果取得後に commit する。**

### F148

- **再発: 2026-08-07** — 変異 matrix の本走が MW-06 で rc=16・stdout 0 byte で停止した。
  変異適用中の tree は必ず dirty なので、local 試行から dispatch への fallback が
  「tree が clean なら」の条件で拒否され続ける。D209 決定 9 の指紋比較が
  `mutation_harness` 経由の経路へ届くまで、変異本走はこの停止を踏みうる。
  初回台帳 = `output/insights/2026-08-07_t503-disposable-worktree/mutation-ledger-run1-erratum.json`。

### F149

- **再発: 2026-08-07** — 同じ停止で harness が `receipt 表示行が exactly one でない: 0` を記録した。
  `--runner-mode dispatch` の consumer は receipt 行の実在に依存し続けており、
  D209 決定 10 の `--force-dispatch` を `mutation_harness` 側が渡すまで塞がらない。
  親は当初これを計算機の queue 混雑と誤診断し、待ち行列を見て投げ直す運用で凌いだ。
  **混雑は相関であって原因ではなかった** — 待ち 142 件のままでも完走した走行がある。
