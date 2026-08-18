---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-18
wave: dev-wave-t1352-c07-result-judge
seq: 2
---

## {{D:c07-consumer-before-activation}}. 8c 条件 7 の consumer は evaluator 登録より先に land する

**決定:** 8c 事前登録の条件 7 について、consumer (`orchestrator/campaign/s8c_result_judge.py`) と
静的 evaluator (`_evaluate_c07`) を先に land し、`_MACHINE_EVALUATORS` への登録・
`NEGATIVE_CONTROL_CASES` への追加・証拠契約 JSON の `machine_checkable` 反転・
条件凍結 record の新世代発行は、後続の束ね wave が 1 回で行う。

**理由:**
- 登録だけを行うと必ず赤になる。`MACHINE_CHECKABLE_CONDITION_IDS` は `_MACHINE_EVALUATORS` から
  導出され、契約 JSON の `machine_checkable` から導出した集合との全単射を 2 つのテストが要求する。
  契約を反転せずに登録する組み合わせは、evaluator の中身によらず成立しない (実測)。
- 契約 C07 の `reachable_from` には repo に実在しない `accept_trial` が 2 箇所あり、
  `s8b_ratified_freeze.py` 側の `verify_floor_bytes` も実在しない。反転は契約本文の
  入口名の是正と `MACHINE_CONTRACT_FUNCTION_CHECKS` への mapping 追加を同時に要求する。
- 凍結世代の衝突は merge で解けないため、世代発行は 1 wave 1 回に限る。

**却下した選択肢:**
- 未登録 evaluator を production から呼ぶ別 registry (staged registry) の新設 — 条件を迂回する
  機構の新設に当たる。門に阻まれたら門を回り込む口を作らない。
- 全単射検査の緩和 — 正しさゲートを緩める方向であり採らない。
- 登録を諦めて evaluator を書かない — 束ね wave が反転できる形が存在しなくなる。

## {{D:floor-provenance-not-judge-input}}. 床値 artifact は出所検証だけに使い、判定の入力にしない

**決定:** 8c 条件 7 の consumer では、床 artifact の検証 (`verify_floor_bytes`) は
`floor_protocol` と `floor_source` の 2 件を ratified 世代 document 由来の
path / sha256 / `env_tag` / `frozen_at_head` と突き合わせる出所検証に限る。
その結果は床値を一切持たない receipt として `publish_result_table` の必須入力になるが、
`judge` の引数型には現れない。判定が消費してよい主量は対差の有限な平均と有限な標本 SD
(分母 n-1) だけとする。

**理由:**
- 8b の再凍結 (§10.1) が対象別 between-run floor との比較を撤去し、8c 条件 7 も
  「床値 artifact は本条件の入力にしない」と明記している。
- 一方で条件 7 は `verify_floor_bytes` を entrypoint として凍結しているため、関数は必要である。
  出所検証と判定入力を型で分離すると、両方の要求を同時に満たせる。
- 検証を publish の必須前提にしないと、未検証の床のまま公式性能表を生成できてしまう。

**却下した選択肢:**
- 検証結果を module 変数や共有 state に置く — 呼び出し順への暗黙依存を作り、
  検証を飛ばした publish を静的に塞げない。
- 床値を診断値として judge へ渡す — 「診断値」という名目で判定へ再流入する経路を残す。

## {{D:predeclared-cell-set-must-be-independent}}. 事前宣言 cell 集合は生成物から導出しない

**決定:** 結果表の cell 集合の完全一致検査は、期待集合を生成行から導出せず、
独立の必須引数として受け取る。引数省略時に生成行から埋める経路を作らない。
`judge` の入力が空集合のときは 3 条件すべてを判定不能へ固定し、
`all()` / `any()` の空集合既定値で成立側へ倒さない。

**理由:**
- 期待集合を対象から導出する検査は恒真であり、manifest と observations を同時に削っても通る。
- 空集合に対する全称量化は真になるため、入力が無いことが「条件成立」の証拠に化ける。
  これは謳うだけで発火しない保証の典型である。

**却下した選択肢:**
- 件数だけの検査 (6 件なら通す) — 任意の cell ID で通ってしまう。
