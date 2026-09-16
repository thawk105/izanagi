---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2662-bounded-reference-truth-table
seq: 1
title: [T-2662] path 参照の抑止判定 (helper と本番) の真偽表を取り、本番の単一走査側を維持した — 862 行で本番だけ True は 0、差は探索根より下に境界 byte を含む path だけ、D248 は内部探索方式を一意に定めない (docs のみ、branch worktree-dev-wave-t2662-bounded-reference-truth-table、実装面の差分ゼロのため変異 matrix 免除)
---

## 本文

- D2104 項 25 (AI 実測先行、暫定は本番側) の実測手番。probe は Codex `role=author` が書き (314 行、
  SHA-256 `799d9140…`)、親が job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2662-bounded-reference-truth-table/`
  へ退避して login node で本走した。repo には入れない。子の自己検査 JSON と親の本走 JSON は byte 同一。
- 真偽表 862 行 (単根、pattern 型 P0〜P14 × content 型 C0〜C14): 一致 718、helper だけ True 144
  (本番の入力領域外 4 行を除き 140)、**本番だけ True 0**。境界 byte を含まない path は 1 MiB chunk 跨ぎ
  42 行を含め全 72 行一致。実在 path 対照: 本番探索根に境界 byte 入り entry 6 件 (空白入り dir 4 件 =
  配下 467 file、`[?]*`・`:(glob)` の file 2 件、pytest tmp 残骸) があり、各 1 file の引用 3 形 18 行で差が
  発火。陽性対照 (main blob が引用する実在 job dir の祖先) は helper・本番とも True。
- 段 6 敵対レビュー 2 本 (レンズ A 候補集合と対照、レンズ B D248 解釈と向き): real 4 (うち重大 2)・
  refuted 8・不明 1・nit 1。倒された言い過ぎ: (1) 「D248 の意味は本番側で確定」は追加規則であり
  真偽表では決まらない、(2) 「境界 byte 入り path は必ず報告される」は祖先 dir 参照 (D247 条件 5) で
  抑止されうるので不成立 (表の R0098・R0245 に測定済み)、(3) 単根の表は本番の全根集合 (根ごとの和集合)
  と同一視できない。是正後の結論と設計判断は {{D:bounded-reference-truth-table-keeps-production}}。
- 段 2・3 は省略 (既定の軽量版、裁定が向きの不変条件を先に固定)。段 5 の author 子 1 本、段 6 の
  review 子 2 本。fix 子・変異 matrix は実装差分ゼロのため無し。
- 一次資料: `output/insights/2026-09-17/t2662-bounded-reference-truth-table/` (README = 是正後の結論、
  `verbatim/truth-table.md` = 本走の表、`s6-adjudication.md` = 所見の裁定)。

## 次の一手差分

### 完了

- [T-2662] 同じ候補集合で helper と本番の真偽表を取り、実在 path を対照にした。本番だけ True は 0 行、
  D248 の逐語は内部探索方式を一意に定めず、向きは本番維持 (実装差分ゼロ)。
  remaining: none
  base: d41df0905ad3fb8b3b840d8a104532fed64f222c9354fb63c85685ab4ae9cbf6

### 新規

- {{T:bounded-reference-equivalence-test-scope}} **P3・新規**: `orchestrator/tests/test_audit_dangling_commits.py` の
  同値テスト `test_bounded_path_reference_single_scan_matches_legacy_boundary_semantics` に射程 (境界 byte を
  含まない path) を docstring と id で明記し、境界 byte を含む path の差分 (helper True・本番 False) を
  「現行挙動と legacy との差の記録」として pin する。あわせて `tools/audit_dangling_commits.py` の
  `_bounded_path_reference_matches` 内コメントの無条件な同値主張を射程付きに直す (反例は insight の
  R0075)。抑止集合は変えない。実装面なので Codex `role=author`。
- {{T:d248-inner-boundary-rule-ruling}} **P3・ユーザー裁定待ち**: 本番の方式 (候補 path 内部の境界 byte は
  path を終端する byte として扱い、内部に境界 byte を含む path の完全 path 参照は認めない) を D248 の
  追加規則として明文化するか。現状維持で挙動は変わらず実害なし。明文化は将来の意味変更の基準になる
  だけで、しなければ D2104 項 25 の運用判断 (抑止を広げない側を維持) が基準のまま。親の推奨は
  「明文化しない (D2104 項 25 と {{D:bounded-reference-truth-table-keeps-production}} の記録で足りる)」。
