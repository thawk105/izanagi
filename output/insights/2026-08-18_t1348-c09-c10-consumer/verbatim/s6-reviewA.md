blockerあり。実装はそのまま着地不可です。

### F1. 登録済み build 正例が到達不能

深刻度: blocker  
該当: `orchestrator/tests/test_trial_registry.py:1317`、`orchestrator/campaign/trial_registry.py:2793`、`orchestrator/campaign/autonomous_trial_completeness.py:3651`、`orchestrator/campaign/p3_autonomous_workload_trial.py:208`

登録 acceptance は `rr80` / `rr20` を要求する一方、C09 は `ycsb-a` / `ycsb-b` / `ycsb-c` だけを producer-supported と判定する。formal fallback の `resolve_workload_entry` はこの membership check を変えず、実 producer も formal workload を拒否する。`do_build=False` は明示的 no-build であり代替にならない。

影響: build 6件の受理集合と build-derived receipt leaf を作れず、実際に発行できるのは `no-build` と未束縛12 fieldを持つ非認証 receiptだけになる。親判断は反証できなかった。

### F2. ハッシュ検証後に別の WAL を再読込する

深刻度: blocker  
該当: `orchestrator/campaign/autonomous_trial_completeness.py:3275`、`orchestrator/campaign/wal.py:681`

`read_and_verify_bytes` の戻り値 `_wal_raw` を捨て、`read_records_checked` が WAL を再度ディスクから読む。検証後に WAL を差し替えれば、digestで承認された内容Aではなく未検証の内容Bから `build_records`、`bench_records`、`source_refs`、receipt hashを生成できる。

影響: 受理済み report・台帳・cross-binding leaf が、承認digestに対応しないWALを参照する。

### F3. 欠落した `bench_wall_s` を 0.0 として受理する

深刻度: must-fix  
該当: `orchestrator/campaign/autonomous_trial_completeness.py:3062`、`orchestrator/tests/test_autonomous_trial_completeness.py:3030`

`bench_wall_s` が無い場合に `.get(..., 0.0)` で補完し、generation側も同じ値なら通過する。layer3 schemaでもこのfieldは必須ではない。

影響: 実測時間の無い bench を `bench_wall_seconds=0.0` として report・台帳・binding hashに取り込める。

### F4. M01-M11 の mutation kill が不成立または別ゲートに隠れる

深刻度: blocker  
該当: `orchestrator/tests/test_trial_registry.py:1317`、`orchestrator/campaign/trial_registry.py:2856`、`orchestrator/tests/test_autonomous_trial_completeness.py:3106`

- M01 / M05: build正例が基線から既に赤。M05は呼出削除後に `trial_registry.py:2979` の辞書参照で落ちるだけで、C10の意味的killではない。
- M02 / M04 / M06: acceptanceに対する空cells、failure reason、別output rootの負例がない。
- M09: `:3130` は既存payload改変であり、未分類WAL recordを追加していない。`autonomous_trial_completeness.py:3325` の別検査に隠れる。
- M10: `:3136` のartifact ref削除は、全件再読でなくても `:2920` の完全列挙検査で落ちる。
- M03 / M07 / M08 / M11 は、それぞれ `test_trial_registry.py:1288`、`test_autonomous_trial_completeness.py:3059`、`:3118`、`test_s8c_acceptance_receipt_v2.py:441` に有効なkillがある。

影響: C09/C10を弱めた変異が、基線赤または別ゲートの赤を利用して生き残り、受理集合・receipt leaf・台帳参照の改変を検出できない。

### F5. 評価器は acceptance 側のdead callをまだ見抜けない

深刻度: nit  
該当: `orchestrator/campaign/s8c_preregistration_evidence.py:299`、`:1645`、`:1691`、`orchestrator/tests/test_s8c_preregistration_predicates.py:1382`

`_evaluate_c09/_evaluate_c10` はAST全体の `_called_names` と `_strings` を使い、live解析の `_live_called_names` を使っていない。現差分にdead callや未使用literalは確認できず、12 fieldと`"no-build"`も実判定で使われている。ただし acceptance callを `if False` や未呼出関数へ移す変異を検査するテストはない。

影響: 将来その変異が入ると、実ゲート無しでも `EVIDENCE_UNDEFINED` のまま報告・台帳の根拠だけが残る。

## 総括

順序 `assert_campaign_layer3_chain` → `verify_s8c_cross_binding` → `accepted.append` → receipt発行は、`trial_registry.py:2904`、`:2918`、`:2927`、`:3041` で正しい。v3 aggregateも `s8c_acceptance_receipt.py:986-997` でleafから再計算され、保存値を無条件には信じていない。

そのまま着地させてよい部分は、no-buildを明示的に未束縛化する経路、`read_and_verify_bytes` のpath・symlink・digest検査、v1/v2/v3のschema分離、`certifying=True` を発行しないreceipt構造です。