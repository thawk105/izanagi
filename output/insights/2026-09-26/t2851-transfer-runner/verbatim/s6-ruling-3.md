# 段 6 裁定 (3 巡目) — 2026-09-26 10:30 JST、対象 commit 16f654141、錨の生死確認 3 回目 (29210.nqsv、smoke-out-3)

## 実測 (smoke-out-3、YCSB Silo wh-base、cohort 1、bnode096、CCBench e9e477ca)
- job: completed_blocks 32、使えない走 0、単独性 開始・終了とも成立、next_action none、順序 R0 先 15 / R1 先 17 block。
- 平均 tps: R0 1,373,345.9、R1 2,448,188.8。ln(R1/R0) の平均 0.5780 (無補正 95% [0.5693, 0.5866]、記述)。
- verify (R1、wh-base): **status indeterminate、reason indeterminate**、anomaly 0、total_cycles 0、serializable true、integrity の違反件数は全て 0 で notes 空、`clean=false`、`certified=false`。

## 所見 G-1 (real / must-fix / 採用)
`verify_candidate` は `verify_trace_dir(trace_dir, expected_commits=..., protocol=...)` を `ccbench_root` なしで呼ぶ。
`orchestrator/verifier/model.py` の `assess_protocol_proof_surfaces` は `ccbench_root is None` のとき X/P/I 三面を `unavailable` にし、
`Integrity.clean()` は `proof_surfaces.certification_gate_satisfied()` を要求するので、**YCSB の検証は常に indeterminate で certified に到達しない**。
放置すると全 (候補, cell) が主張の資格を失い、主要表は全て判定不能になる。
fixture 版 test は verifier を差し替えるので、この到達性を検査していなかった。

直し方:
- 凍結入力の `binaries[identity]` に、trace-enabled binary を compile した CCBench source tree の絶対 path `trace_ccbench_root` を必須で置く (hash 対象)。
  verify は `verify_trace_dir(..., protocol=protocol, ccbench_root=<その path>)` を呼び、記録に写す。
  verifier の判定そのもの (clean・certified の条件) は変えない (規律 2)。
- test: `verify_candidate` が実 verifier 経路で `ccbench_root` を渡すことを、trace_runner だけを fixture 化し verifier は実物 (`verify_trace_dir`) のまま、
  repo の `external/ccbench` を source root にした最小 trace で certified になる正例と、`trace_ccbench_root` を存在しない path にしたとき indeterminate になる負例で固定する
  (既存の real verifier fixture が使えるならそれを使う)。
- smoke driver: 各 identity の `trace_ccbench_root` に、build に使った CCBench source (`ROOT / "external/ccbench"`) を入れる。

## 変異の追加登録 (fix 前、DW-M01)
| ID | 変異 | 期待 |
|---|---|---|
| M13 | verify で `ccbench_root` を渡さない (引数を落とす) | KILLED |
