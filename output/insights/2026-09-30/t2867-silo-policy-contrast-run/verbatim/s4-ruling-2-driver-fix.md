# [T-2867] 本走 wave 段 4 追加裁定 2 (親、2026-09-30 13:1x JST) — 前走で見つかった driver の欠陥の最小修正

## 事実 (親が実測)

前走の参照 job (試験版 `reference-1`、request 37757、HEAD 4f412c67b、checkout c01、2026-09-30 12:37〜12:51 JST、Elapse 878 s) で、
stock 5 slot はすべて certified・品質正常 (1,357,628〜1,369,299 tps)。6 slot 目の静的 10 µs (`ref-fixed10-0`) の開始後、driver が rc=1:

```
p3_s4_loop_policy.py:876 run_contrast_unit → :731 measure_slot → :439 run_stock_control → p3_s4_loop.py:536 _require_condition_gate
RuntimeError: condition gate rejected P3 S4 loop: supply=preprocess-failed ...
masstree_wrapper.hh:20:10: fatal error: config.h: No such file or directory
```

slot の結果が書かれず、台帳は `ref-fixed10-0` の slot-start だけが残る (dead-job)。一次記録は
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/preflight/evidence/reference-1/reference-1-a0/job.stderr` と `compute-result.json` (driver_rc 1)。

## 原因

`p3_s4_loop.py` の本流 (2550 行付近) は、offline 供給の receipt (`fetchcontent_dependency_receipt`) があるとき
`_require_condition_gate(sub, genome, configure_args=_condition_gate_offline_configure_args(dependency_prefix=..., fetchcontent_base_dir=..., masstree_source_dir=..., mimalloc_source_dir=..., googletest_source_dir=...))`
を渡し、gate の configure が準備済みの masstree source (config.h を含む) を使う。方策 driver の `run_stock_control` の `fixed10` 経路 (439 行) は
`L._require_condition_gate(sub, genome)` を引数なしで呼ぶので、計算ノード (offline) では gate の前処理が config.h を見つけられない。
生死確認は静的 10 µs を一度も計算ノードで走らせていなかった (事前登録 §11.0「未実測」、実装 insight §7「未実走」)。

## 裁定

- real、本走の blocker (参照 job 3 本すべての静的 10 µs が同じ理由で落ち、参照の系列が dead-job → §7.4 の手順 2 で判定不能)。
- 修正 (Codex author、子 y): `run_stock_control` の `fixed10` 経路で、`fetchcontent_options` に `fetchcontent_dependency_receipt` があるとき、本流と同じ
  `L._condition_gate_offline_configure_args(dependency_prefix=dependency_prefix, fetchcontent_base_dir=..., masstree_source_dir=..., mimalloc_source_dir=..., googletest_source_dir=...)`
  を `configure_args` として `L._require_condition_gate` へ渡す。receipt が無いときは従来どおり引数なし。gate の判定・検査の中身・stock 経路・候補の経路は変えない。
- 規律 2: gate を省く・緩める修正ではない (同じ gate を、本流と同じ入力で通す)。
- 試験: 追加 1〜2 本 (receipt ありなら configure_args が本流の射影と一致して渡る、無ければ渡らない)。gate 本体は計算ノードの compiler を要するので、呼出しの境界 (`L._require_condition_gate`) で引数を捕まえてよい (差し替えを報告に列挙)。
- 変異の事前登録: **M1** = `fixed10` 経路の gate 呼出しから `configure_args` を外す (receipt があっても引数なしで呼ぶ) → 期待 KILLED (新しい試験)。
  **M2** = receipt が無いときも `_condition_gate_offline_configure_args` を呼ぶ (base dir 空で例外になる形) → 期待 KILLED (receipt なしの試験)。
- 実走での確かめ: 修正 commit を HEAD にした checkout で、試験版の参照 1 本 (`reference-2`) を前走として回し、静的 10 µs の 5 slot が certified・品質正常になることを見る。
- 本走の submit checkout は修正 commit へ進める (本走の HEAD = wave branch の修正 commit。main との差は記録する、common-4 §2)。
- 前走の進化×IR (`evo-ir-1`、HEAD 4f412c67b) はそのまま走らせる。修正は `fixed10` 経路だけで、進化×IR の評価と score の経路は変わらない。
