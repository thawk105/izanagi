---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2122-prereg-executable-evidence
seq: 1
title: [T-2122] 完了証明層の充足証明に実行可能な証拠を認める規範を事前登録正本へ一度だけ書いた (docs + 凍結記録、branch worktree-dev-wave-t2122-prereg-executable-evidence、実装面 0・変異 matrix 免除)
---

## 本文

D1386 (ユーザー裁定) を `docs/phase3-8c-preregistration.md` §6 改訂手続きの要件 (a) 末尾へ 2 行で
入れた。D1364 の 4 点は維持し、4 点を強制する新しい機械 gate は作っていない (追加した
test・checker・評価器・証拠契約の変更は 0)。凍結範囲を変えたので、同じ commit で条件契約の
第 14 世代 record を既存生成器 `s8c_preregistration prepare-revision` が発行した。

- **段 3 の 2 レンズが文言で割れた。** 片方はプラン原案の条件節「`required_evidence` /
  `consumer_requirement` を一切緩めずに」を「置換ではない」ことの防御線として支持し、もう片方は
  「緩める」の比較基準が本文に無いため条件ごとの再裁定を招くとして削除を求めた。**親は段 4 で
  どちらの案もそのまま採らず、判定を課す条件節を、許可の射程を述べる宣言文へ置き換えた。**
  確定文言は「この充足証明に用いる証拠は静的解析に限らず、実行可能な証拠を含めてよい (D1386)。
  これは証拠の種類を増やす許可であって、(a)〜(c) のどの要求も置き換えない。」
- **段 6 の 2 レンズは確定文言を初めて見て、must-fix 0 と 3 を返した。** 3 件はいずれも採用した。
  (i) 実測証拠 (exact command と rc) を handoff へ残す。(ii) commit 後検証に holdout scan と
  返却 field の明示 assert を足す。(iii) 台帳 fragment を最終受入より前に commit する。
- **受理集合は動いていない。** `SATISFIABLE_CONDITION_IDS` は exact `{"C10"}` のまま。
  g14 で変わったのは `generation_number` / `supersedes_sha256` / `revision_reason` /
  `ruling_reference` と、規範本文由来の `normative_body_sha256` / `protected_sha256` の 6 field
  だけで、§6 条件 hash 12 件・§5 欄名・証拠契約 hash・`DECIDER_VERSION` (`s8c-decider/v8`) は
  g13 と同値である。版を bump しないのは判定器・評価器・射影の意味を変えないためである。
- **decisions への追記は 0 件とした。** D1386 は着地済みであり、同じ規範を決定として書き直すと
  「一度だけ書く」と衝突する。段 6 のレンズも同じ結論を独立に出した。
- **凍結 record を機械検査する 5 node は保留されたままだった。**
  `test_s8c_preregistration_invariant.py` の実 repository 候補 commit を合成する 5 node は
  `IZANAGI_GROWTH_HOLD_V1` (2026-08-29 T-1434 ユーザー裁定、解除はユーザーの明示指示のみ) で
  skip される。**本 wave の差分に起因しない既存の保留であり、解除していない。**
  そのため「不変条件テストが緑だから g14 が正しい」とは主張しない。代わりに既存 API
  (`validate_condition_freeze_at` / `activation_report_at`) へ exact field の assert を 24 件当て、
  保留 node が見ていた holdout 汚染は既存 CLI `s8b_holdout_freeze search` (rc=0) で確かめた。
  今回足した 2 file は走査結果に現れない。**この代替は 5 node と同値ではない** — candidate commit
  の合成そのものと、batch 呼出し回数の instrumented assertion は覆っていない。
- **待ち手の異常を 1 件観測した。** 段 6 レビュー B の待ち手が、子の稼働中に空出力・rc=0 で返った。
  `.done` も成果物も無いのに完了通知だけが来る型で、`pgrep` と artifact の増加で子の生存を
  確かめて張り直した。子は正常に完走した。待ち手側の欠陥か通知経路の欠陥かは切り分けていない。
- 実装面 (D95 決定 2) の差分は 0 byte なので、変異 matrix は `DW-S04` により免除。したがって
  `DW-M02` の「所見ゼロを変異で裏取りする」は実施していない。段 6 の must-fix 0 はこの限界つきである。
- 検査 (すべて実走): `python3 tools/check_docs.py` → `違反なし`。
  `python3 tools/run_tests.py orchestrator/tests/test_s8c_preregistration_invariant.py -q`
  → 15 passed, 5 skipped (上記保留)。
  `python3 tools/run_tests.py orchestrator/tests/test_s8c_preregistration_core.py
  orchestrator/tests/test_s8c_preregistration_predicates.py -q` → 603 passed。
  `python3 tools/check_ai_provenance.py --message-file <msg>` → 違反なし。

## 次の一手差分

### 完了

- [T-2122] 規範本文への追記と第 14 世代 record を同じ commit で入れ、受理集合が動かないことを
  実行可能な検査で確かめた。
  remaining: none
  base: 1c68c5cf34a553dd84ef919ee7d849b8e248b326c4ad9e0836493f09ff2d9712
