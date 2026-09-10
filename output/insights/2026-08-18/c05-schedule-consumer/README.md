# 8c 条件 5 (schedule consumer) の新設 — insight package

wave: `dev-wave-c05-schedule-consumer` / branch `worktree-dev-wave-c05-schedule-consumer`
base main `64d37b1a` / 2026-08-18 JST

## この wave が作ったもの

- `orchestrator/campaign/s8c_schedule.py` (新設、leaf module)
- `orchestrator/tests/test_s8c_schedule.py` (新設、自走 harness 付き)
- `orchestrator/campaign/s8c_preregistration_evidence.py` に `_evaluate_c05` と
  `ReasonCode.SCHEDULE_CONSUMER_UNREACHABLE` を追加 (**registry へは登録していない**)
- `orchestrator/tests/test_s8c_preregistration_predicates.py` に負の対照
  `nc_c05_initial_state_hash_bitflip` と C05 evaluator の直接テストを追加
- `orchestrator/tests/test_s8c_preregistration_invariant.py` の `WAVE_REQUIRED_PATHS` へ新規 2 file

## この wave が主張しないこと (重要)

**C05 は発効していない。** 本 wave 後も判定は
`EVIDENCE_UNDEFINED / schedule-schema-absent` のままである。理由は次のとおり。

- 契約 JSON の `machine_checkable` は `false` のままで、`_evaluate_c05` は呼ばれない。
- `_MACHINE_EVALUATORS` は 7 件のままで C05 は未登録。
- schedule artifact は commit しておらず、§5 の `master_seed` も未記入。
- production 配線 (`run_trial` からの到達) は無い。

したがって「C05 の gate が存在する」「C05 が検証済み」と読んではならない。
正しい表現は **「consumer は実装済み、条件の充足証拠は未定義」**である。
certified な選択結果・材料レポート・試行台帳は、この状態からは produce されない。

## 実測 (すべて親が実行)

| 対象 | 結果 |
|---|---|
| 焦点走 (fix 後) | rc=0 / **548 passed** (bounded local、受入形ではない) |
| 判定器の再実測 (library 経路) | C05 = `EVIDENCE_UNDEFINED / schedule-schema-absent` (変化なし) |
| `MACHINE_CHECKABLE_CONDITION_IDS` | 7 件のまま (変化なし) |
| 全史 provenance 監査 | rc=0 / 4064 件 / 新規違反なし |
| `check_docs.py` | rc=0 |
| fold dry-run | rc=0 |
| 変異 matrix | baseline **PASSED** / **9/9 KILLED** / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0 |

## 変異 matrix の erratum (DW-M02)

初回 probe (`mutation-probe1-erratum.json`) では **m03 / m07 / m09 の 3 件が生存**した。
初回結果は消さずここに残す。

- **m03** — `verify_schedule` が exact 検証と共有検証へ同じ権威を渡すため、共有層が exact 層に
  対して冗長だった。外部供給の期待 digest を受け取る形へ変えて独立させ、殺せるようになった。
- **m09** — `consume_schedule` が検証を通ることを守るテストが存在しなかった。正当な artifact では
  復号だけでも通り、評価器も production 未配線ゆえ元から到達不能を返すため区別できなかった。
  seed 不一致の consume 検査を足して殺せるようになった。
- **m07** — cell 数 6 の検査は後段の全単射検査に隠れる冗長 gate だった。両層同時変異へ再照準した。

**静的な敵対レビュー 2 本ではこの 3 件は閉じなかった。** 変異が実測で暴いた。

## 変異本走の分割理由

`c05.m07` は本走と resume の 2 度とも、計算資源側の終了コード (テスト結果ではないもの) で
harness を fail-closed 停止させた。resume では当該変異が最初に走ってなお同じ失敗をしたため、
順序ではなく変異固有と切り分けた。順番を入れ替えた独立 spec で回して完走させた。
台帳は 2 分割 (`mutation-ledger-part1.json` が m01〜m06、`part2.json` が m07〜m09)。
両走とも baseline は PASSED。

## 段別成果物 (verbatim/)

- `s2-plan.md` — 段 2 プラン起草 (codex)
- `s3-lensA.md` / `s3-lensB.md` — 段 3 敵対相談 (正しさ境界 / 整合・波及)
- `s4-adjudication.md` — 段 4 の確定裁定 (仕様の正本)
- `s5-unitA.md` / `s5-unitB.md` — 段 5 実装子の完了報告
- `s6-reviewA.md` / `s6-reviewB.md` — 段 6 敵対レビュー
- `s6-fix.md` / `s6-fix2.md` — 段 6 fix

## 未実施

- 受入全走は本 wave では実施していない (段 9 の land 手順で扱う)。
- schedule artifact の実データによる検証は、artifact を commit していないため未実施。
- production 配線が無いため、契約が要求する到達性は満たされていない。
