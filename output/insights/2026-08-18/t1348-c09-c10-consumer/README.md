# 8c 前提条件 C09 / C10 の consumer 配線 (dev-wave)

- wave branch: `worktree-dev-wave-t1348-c09-c10-consumer`
- base: `64d37b1a` (main を ff-only 取り込み。並行していた t1333 wave は land 済み)
- 実施: 2026-08-18 18:00-22:20 JST (背景 job)

## 到達点

| 条件 | 変更前 | 変更後 |
|---|---|---|
| C09 | UNSATISFIED / `formal-acceptance-layer3-consumer-absent` | EVIDENCE_UNDEFINED / `completion-proof-not-machine-checkable` |
| C10 | UNSATISFIED / `cross-binding-verifier-incomplete` | EVIDENCE_UNDEFINED / `completion-proof-not-machine-checkable` |

`EVIDENCE_UNDEFINED` / `completion-proof-not-machine-checkable` は、この評価器で
機械的に到達できる最良の終端である。`_evaluate_c09` / `_evaluate_c10` に
`SATISFIED` を返す枝は存在しない (親が実測)。

12 条件のうち `SATISFIED` は変更後も 0 件である。

## 何を作ったか

- `orchestrator/campaign/trial_registry.py` の `assert_trial_registry_acceptance` が、
  build report ごとに `assert_campaign_layer3_chain` を実走する。
  `do_build=True` かつ cells 空、`campaign_root` 欠落、report の run root から導いた
  output root との不一致は fail-closed で拒否する。
- `orchestrator/campaign/autonomous_trial_completeness.py` に
  `verify_s8c_cross_binding` と `read_and_verify_bytes` を新設し、
  role event / provider / proposal / WAL / bench / Layer 3 の 12 field を
  実 bytes の再読で束縛する。acceptance は registry 受理より前にこれを呼ぶ。
  検証 CLI (`verify_autonomous_trial_files`) からも同じ verifier を呼ぶ。
- 受領証を v3 へ上げ、trial ごとの leaf digest を保存して top-level の aggregate を
  leaf から再計算・照合する。v1 / v2 は schema 別 exact key 集合で従来どおり parse できる。

## 実測

- 焦点 9 file: 814 passed / 1 failed → commit 後は該当 1 件 (状態表 tripwire) も緑。
- 全史 AI provenance: 4064 件、新規違反なし (rc=0)。
- `check_docs.py`: 違反なし。
- 変異 matrix: baseline PASSED・**11/11 KILLED**・SURVIVED 0・MISMATCH 0
  (`mutation/mutation-spec.json` / `mutation/mutation-ledger.json`)。
  probe 走 (`mutation/*-probe.json`) は KILLED 5 / MISMATCH 6 / SURVIVED 0 で、
  MISMATCH はすべて期待 node 集合が実際より狭かったことによる。

## 実測で確定した制約

登録 manifest の holdout workload (`rr80` / `rr20`) と producer が対応する workload
(`ycsb-a` / `ycsb-b` / `ycsb-c`) は**互いに素**である。したがって登録済み build report は
`assert_campaign_layer3_chain` の「workload is not producer-supported」で必ず fail-closed し、
**acceptance の build 正例は前提条件 1 (C01) が着地するまで緑にできない**。
本 wave はこれを偽装せず、「acceptance が層3 gate へ到達して exact な理由で fail-closed する」
ことを pin するテストへ書き直した。C10 の 12 field 束縛の正例は unit 段で緑である。

## 検出力の注記

変異 M09 と M10 では、その gate のために新設した専用の負例が発火せず、
隣接 gate と正例が代わりに検出した。KILLED ではあるが、
**当該負例はその gate の単独証拠にならない**。詳細は failures 台帳の該当エントリ。

## 段別の逐語

`verbatim/` に段 1 brief、段 2 プラン、段 3 敵対 2 本、段 4 裁定、
段 5 実装子報告、段 6 レビュー 2 本と fix 3 巡を収めた。
