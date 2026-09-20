---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-fig3b-arc-status
seq: 1
title: 論文の現況図 fig3 の後継図 fig3b (2026-09-19 版の 3 幕と §8 A/B 群の状態だけを描いた模式図) と最小の生成器 (Codex author) を着地させた (コード + docs、branch worktree-dev-wave-fig3b-arc-status)
---

## 本文

- 依頼 (command 引数): 凍結図 `fig3_arc_status.png` (2026-07-10 版時点の模式図で第 3 幕と不一致) の後継図を、着手時点の最新ストーリー版の
  第 1〜3 幕と §8 A/B 群の現在地を値なし・状態 (取得済み / 非認証 / 裁定待ち / 未取得) だけで 1 枚にし、Codex author が
  `tools/plotting/plot_arc_status.py` (状態 JSON をスクリプト脇に) を書き、計測機の外で生成、png/pdf + provenance + `figures/README.md` の
  節を足す。汎用 framework・gate・台帳は scope 外。一次資料は `output/insights/2026-09-20/fig3b-arc-status/README.md`、図の正本は
  `docs/paper-story/figures/README.md` の fig3b 節。専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig3b-arc-status/HANDOFF.md`。
- 前提の実測: main 上の最新版は 2026-09-19 版 (09-20 版は稼働中 wave で未 land、草稿は時点語の置換のみ) → 09-19 版 §8 の各項冒頭【状態】と
  §0 から状態を写し、稼働中 wave は数えない (同版の規則)。`docs/paper-story/README.md` (hot file) は触っていない。
- 段 2 plan (codex read-only) → 段 3 相談 (2 レンズ 1 本、must-fix 4 / should 7 / nit 1、全部 real・採用) → 段 4 裁定 (JSON 名を版で
  `arc_status_story_2026-09-19.json`、anchor を項目 ID 形 `§8 A-1` / `§0 item n` / `§0 act n` にして本文の見出し行が 1 行あることを検査、
  自由文の数量混入を拒否、4 状態の定義は JSON が正本、着地 bytes の pin test は作らない、変異 8 系列を事前登録)。
- 段 5 Codex author 1 本 (生成器 445 行 + JSON + test 8 本) → 親が login で実走 rc=0。段 6 レビュー 2 本 (A: 状態忠実性・正しさ境界、証拠 16 項目
  + Act 8 行は全部一致、must-fix 1 = Act 行の JSON 内部 ID が図に出る (作図規約 §5)。B: 過剰・削除・変異帰属、must-fix 3 = 同 Act ID /
  M2 fixture が診断だけの赤 / group label が自由文検査外、should = 公開 file が 0600) → fix1 (Codex、2 file、+11/−5) → 図を再生成。
  焦点走 (計算ノード) fix 前 29 passed / 9.06 秒、fix 後 30 passed / 9.03 秒。
- 変異 (独立 clone、commit `152c1d99d`、9 変異): probe の観測 node がレビュー B の静的予測と完全一致、final は 9/9 KILLED・期待 node 完全一致 (baseline 30 passed / 8.93 秒、wrapper receipt あり)。等価変異 0。
- 受入 attempt 1 (3 shard) は赤 2 件で rc=70: 新 test file に自走 harness なし (F42 再発) と T7 の subprocess env に bytecode guard なし
  (F521 再発)。どちらも自分起因 → fix2 (Codex、test file のみ、commit `5686eaa2a`) → 焦点走 (新 test + メタテスト 2 本) 39 passed →
  変異 final2 (同 commit) 9/9 KILLED → 受入を取り直した。failures fragment に 2 件の再発を追記。
- 図が言わないこと (README 節と caption に固定): 判定を作らない、A-2 / A-6 の判定は当時の identity 層の下のものとして残る (規律 7)、
  「A-1 の値がある」「mocc は第 2 成功例」「B-10 を閉じた」「床値が発効した」とは読めない。FIGURE_CONVENTIONS §1 (WAL/dat) は
  値を持たない模式図に限った限定で、数値図への免除ではない。
- 工数: codex 7 本 (plan 1、consult 1、author 1、review 2、fix 2)、計算ノード job = 焦点走 3 + provenance 全史監査 1 + 変異 30 走 + 受入全走 2。
  親の逸脱 1 件 (変異用 clone の起点 SHA を rev-parse せず推測で書いて update-ref 失敗、clone 1 回やり直し。memory 既載の罠の再発)。
- 受入全走 (2 回目) は本 fragment の追記 commit の後、段 9 の land 前に `dev_wave_wait.py acceptance` で実走する (結果は land の受入受領証が持つ。本 fragment は受入前に書いた)。

## 次の一手差分

### 新規

- {{T:fig3b-restatus-after-0920}} **P3・新規**: ストーリー 2026-09-20 版が land したら、fig3b の状態 JSON の各項目 (state・副ラベル・
  限定・人間手番) を同版 §8 / §0 と照合し、変わった項目があれば JSON を上書きせず新 snapshot JSON + 別 filename の後継図 (`fig3c_`) を
  作る (手順は `docs/paper-story/figures/README.md` の fig3b 節)。変わらなければ照合結果だけを記録して閉じる。
