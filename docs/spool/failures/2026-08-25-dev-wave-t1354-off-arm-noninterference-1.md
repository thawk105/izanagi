---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1354-off-arm-noninterference
seq: 1
---

## 新規

### {{F:rejected-artifact-adopted-by-content-check}}. 不採用の子成果物を内容検査の緑を理由に採用へ回した [防壁の射程誤認] [手順漏れ]

- 事象: 8 子中 6 子が `evidence_status=invalid` / `accepted=false` / `launcher_rc=1` になった。
  親は保全した `attempt-0001.output.md` を `-o` の path へ複製し、
  `tools/check_codex_output.py` が rc=0 を返したことを根拠に段 2・段 3・段 6 の
  成果物として採用した。F540 が明示的に禁じている操作である。
- 根本原因: 親が 2 つの検査を同じものと見なした。`check_codex_output.py` は成果物の
  **内容**が形式を満たすかだけを見る。launcher の `accepted` は成果物を生んだ
  **実行そのものの証跡**が健全かを見る。前者の緑は後者の赤を打ち消さない。
  F540 は「内容検査が緑でも launcher の赤を迂回することになる」と 1 行で書いているが、
  親は F540 を読む前に採用を済ませていた。段 7 で F217 系を調べる過程で初めて気づいた。
- 恒久対応: {{D:offarm-noninterference-claim-scope}} と同じ規律 — 検査の届く範囲より広い
  結論を出さない。手順としては F540 の回避 (別 `--job-id` での 1 回再投入) を先に行い、
  再投入が通らない子の成果物は「保全して読むが唯一の根拠にしない」に留める。
  本 wave では気づいた時点で段 6 の関門 3 子を再投入し、2 子が受理された。
- 再発検知: 待ち手が rc=70 を返したら、成果物を複製する前に receipt の
  `attempts[].accepted` を読む。`false` なら F540 の再投入を先に実行する。
  `check_codex_output.py` の rc=0 を採用の根拠にしない。

### {{F:resubmitted-prompt-goes-stale-after-tree-advances}}. F540 の再投入で、prompt が指す一次資料が現行 bytes と食い違った [ドリフト]

- 事象: F540 の回避に従い段 6 の敵対レンズを別 `--job-id` で再投入したところ、受理はされたが
  NO-GO の理由が「レビュー入力として指定された差分 bundle が現行 commit と一致せず、
  現行 nodeid と検出力修正が欠落している」になった。実装の semantics に新しい blocker は
  無かったのに、段 6 の署名対象を確定できないという判定が返った。
- 根本原因: F540 は「**同じ prompt を**別の job-id で 1 回だけ再投入する」と定める。
  しかし本 wave では初回投入から再投入までの間に fix が入り commit も済んでいた。
  prompt が絶対 path で指す integration patch は初回時点の bytes のままで、
  同じ prompt が指す source file は現行 tip になっていた。子は両者の食い違いを正しく検出した。
- 恒久対応: 再投入の直前に、prompt が指す一次資料 (patch・差分 bundle・前段成果物) を
  現行 tip から作り直す。prompt 本文が変わらなくても、指し先の bytes は更新する。
  {{D:offarm-noninterference-claim-scope}} と同じく、検査に渡す入力が主張の対象と
  一致していることを先に確かめる。
- 再発検知: 再投入した子が「入力が現行と一致しない」型の NO-GO を返したら本エントリ。
  再投入前に `git diff` の出力を patch file へ取り直したか確認する。

## 再発

### F540

- **再発: 2026-08-25** — 1 wave で 8 子中 **6 子**が `evidence_status=invalid` になった
  (段 2 plan、段 3 レンズ A、段 6 レビュー 2 本、fix、焦点再レビュー)。
  受理されたのは段 5 実装子と段 3 レンズ B の 2 子だけである。
  **F540 の再発検知手順どおり既知 2 原因を実測で否定した。** F217 (web 検索イベントの重複キー) —
  8 子すべての `attempt-0001.events.jsonl` を重複キー拒否 parser で全行 parse し、
  失敗 0 行。文字列 `web_search` は受理された子の events にも現れるため指標にならず、
  不採用の焦点子には 1 件も現れなかった。F223 (非 NFC) — 8 子すべての成果物が NFC 正規。
  launcher-diagnostics にも `conditions_met` は空で、限界超過ではない。
  **F540 の回避 (別 job-id での再投入) は 3 子中 2 子で成功し、1 子は 2 回目も不採用**だった。
  再投入が成功した 2 子は初回と同じ結論を返した (F540 の「同じ結論を返さない」は本 wave では
  再現せず、代わりに {{F:resubmitted-prompt-goes-stale-after-tree-advances}} の型が出た)。

### F106

- **再発: 2026-08-25** — **4 度目**。変異 matrix の本走中に、親が段 7 の spool fragment 2 本を
  worktree へ書いて untracked file を増やした。`tools/mutation_harness.py` の preflight が
  `runner/test 実行前に untracked file を検出` で `rc=2` 停止し、防壁は正しく働いた。
  実害は fragment を repo 外へ退避して `--resume` で続きから走らせる一手間である。
  親は本 wave の handoff に同じ注意を書いていない状態で踏んだ。過去 3 回と同じく
  「dispatch するから worktree を触ってよい」ではなく「投入から結果取得までは worktree を
  触らない」が正しい読み方である。今回の再発は `--resume` が既存の `--attempt-out` を
  要求する点も併せて実測した (新 path を渡すと `--resume + --attempt-out には既存の
  symlink でない通常 file が必要` で停止する)。

### F277

- **再発: 2026-08-25** — 段 4 で事前登録した変異 8 件のうち 5 件が、実装前の静的検討では
  帰属可能に見えたのに、段 6 の敵対レンズが「import 時 assert・既存 guard・既存テストに
  mask される」と静的に反証した。さらに実測すると、集合だけを変える変異は
  **MISMATCH ですらなく pytest の collection error** になり、失敗 node が 1 つも出ずに
  `PARSE_ERROR` で harness が止まった。両層変異へ組み直して初めて node が観測できた。
  **単層変異の「帰属できるはず」は、実効 gate の判定順を追わない限り信用できない。**
