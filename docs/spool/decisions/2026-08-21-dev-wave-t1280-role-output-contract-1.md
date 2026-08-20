---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: dev-wave-t1280-role-output-contract
seq: 1
---

## {{D:s8c-malformed-role-fixture-needs-raw-shape-assertion}}. role 出力契約 fixture 回帰テストは raw 形状の直接検証を必須とする

**決定:** parser の fail-closed 動作を fixture で個別に固定する回帰テストは、共通の `status`/`error_type`/`stop_reason` assertion だけでなく、malformed provider が実際に返した raw response 文字列の形状 (prefix/suffix・特定部分文字列の有無・キー集合など) を直接検証する assertion を必須で含める。

**理由:**
- S8C live pilot (worklog entry 612) で観測された role 出力契約非適合3パターン (auditor が入力の `descriptor_binding` を出力へ複製し top-level 7 キー化・JSON を fence 包み・JSON 区切り文字欠落) を fixture 回帰テストとして新設する dev-wave で、段3 敵対相談の独立2レンズ (sol・luna) が、fence ケースと区切り文字欠落ケースは同じ parser 経路 (`JSONDecodeError` → `PredictionRunnerError` → `AutonomousTrialError`) を通り同じ `status`/`error_type`/`stop_reason` に収束するため、raw 形状を検証しない限り mutation testing で互いを区別できない冗長 gate になる、と**独立に同一の結論**を報告した。
- 段4 裁定でこの指摘を採用し、各テストへ raw 形状の直接検証 (7 キー: `descriptor_binding` の複製確認、fence: prefix/suffix 確認、区切り文字欠落: 特定部分文字列の有無確認) を実装要件に追加した。
- 変異 matrix (7キー緩和・fence 除去追加・delimiter 緩和、それぞれ auditor 経路限定の一時変異) を実測した結果、3 変異とも対応する 1 テストだけが KILLED (matches_expectation=true) となり、raw 形状 assertion の追加が実際に単一理由性を担保することを確認した。raw 形状を検証しない設計 (共通 assertion のみ) では、この単一理由性が保証されない。

**却下した選択肢:**
- 共通 assertion (`status`/`error_type`/`stop_reason` 等) だけで3ケースを新設する — 段3 2レンズが独立に指摘したとおり、fence と区切り文字欠落が同じ例外経路に収束するため、mutation testing で区別できない冗長 gate になり実効性を欠く。
