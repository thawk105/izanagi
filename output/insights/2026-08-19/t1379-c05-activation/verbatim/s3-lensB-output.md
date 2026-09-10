## 総括

判定は「そのまま段5へ進めない」です。F393 の dirty tree + `--commit OLD_HEAD` 自体は実装と整合しますが、検証手順・authority・既存メタテストに must-fix があります。pytest は未実施です。

### must-fix

1. **F393 後の activation 検証対象が不成立**

`validate_condition_freeze_at` は commit tree の blob だけを読みます（`s8c_preregistration.py:1526-1643`）。一方 `prepare_revision` は旧 commit を検証した後、worktree の source/evidence を読みます（`1966-2009`）。したがって dirty tree + `--commit OLD_HEAD` は意図された使い方です。

ただし `OLD_HEAD == 現在の HEAD` の確認はコードにありません。さらに段2プラン §7 の「未 commit のまま `core.activation_report_at` で確認」は成立しません。`activation_report_at` は live core/evaluator bytes と指定 commit の blob を比較し、差分があれば `core-blob-mismatch` / `evaluator-blob-mismatch` にします（`s8c_preregistration.py:1715-1722,1818-1845`）。`OLD_HEAD` は旧契約のままで、`HEAD` も commit 前なら新 g8/artifact を見ません。

候補 commit を `git write-tree`/`git commit-tree` で作るか、検証後に `reset --soft OLD_HEAD` して、最終的に一 commit へ戻す手順が必要です。

2. **P1 authority が未解決**

`_c05_authority()`（`test_s8c_preregistration_predicates.py:37-95`）はテスト用のダミーです。`s8c_schedule.validate_authority`（`s8c_schedule.py:210-249`）は key/type/非空しか検証せず、production 定数由来かは保証しません。`regenerate`（`317-349`）はその値を正しく hash するだけです。

実 production 側も `_load_s8c_schedule_authority` が明示的に unavailable を返します（`p3_autonomous_workload_trial.py:1555-1560`）。従って dummy authority で schedule bytes を commit すると、将来 T-1380 が real authority を使った際に再生成 drift します。§5 の「seed 単独では束縛しない」（`phase3-8c-preregistration.md:135-138`）にも反します。real projection を作るか、authority 未解決のまま artifact/§5 を進めない裁定が必要です。

なお「authority に依存せず C05 が UNSATISFIED」という親の実測は、現 evaluator が artifact の存在と call graph だけを見ること（`s8c_preregistration_evidence.py:1631-1740`）を示すだけで、schedule artifact の正当性を示しません。

3. **追随漏れ**

- 現行 snapshot は C05 を `EVIDENCE_UNDEFINED/schedule-schema-absent` と固定（`test_s8c_preregistration_predicates.py:207-240`）。artifact を commit するなら `UNSATISFIED/schedule-consumer-unreachable` へ更新が必要。
- `test_legacy_contract_routes_machine_evaluators_to_undefined`（`2554-2572`）は C05 追加後も一律 `completion-proof-not-machine-checkable` を期待するが、`_evaluate_undefined` の C05 分岐（`evidence.py:2635-2643`）は artifact 無しなら `schedule-schema-absent` を返す。
- C06 staged 件数 `len(...) == 7`（`test...:3007-3012`、t1353 取り込み後は `3132`）を 8 に更新する必要がある。
- bitflip test（`2697-2738`）は C05 を `NON_MACHINE_CHECKABLE_NEGATIVE_CONTROL_CASES` から移すと空 parametrization になり、テストが黙って消えます。明示 test として残してください。

4. **t1353 との実ファイル衝突**

指定コマンドを実行した結果、t1353 の commit 済み差分は次の論理面と重なります。

- constants: t1353 `+544-717`
- `_negative_control_case`: `+923-941`
- control map: `+1007-1012`
- satisfiable test/static test: `+2275-2289`
- runtime negative-control tests: `+2346-2571`

つまり brief/plan の `488-638`, `824-915`, `918-931`, `2390-2443` は、そのまま line patch できません。t1353 worktree は clean でした。取り込み後に、`TOKEN_ONLY_C04`、`if identifier == "nc_c04..."`、辞書 key などの symbol anchor で C05 を挿入してください。

5. **親の実測値の一般化が強すぎる**

`p3_autonomous_workload_trial.py` に production の `load_schedule` / `verify_schedule` / `consume_schedule` 呼出しが無いことは静的に確認できます。しかし artifact が無ければ C05 の結果は `schedule-schema-absent` であり、親が報告した `schedule-consumer-unreachable` にはなりません。

また brief の「CLI は evaluator bytes 比較で全て `evaluator-exception`」という説明もコードとは一致しません。bytes 不一致は `evaluator-blob-mismatch`（`s8c_preregistration.py:1718-1722`）、`evaluator-exception` は evaluator 実行中の例外（`1764-1777`）です。CLI と library は同じ `activation_report_at` を呼びます（`2109-2121`）。実験時の commit と dirty state を分けて記録すべきです。

### file:line の精度

- `_evaluate_c05`: `evidence.py:1631-1740` は正確。
- `_MACHINE_EVALUATORS`: `evidence.py:2607-2615`、5 は 4 と 9 の間で正確。
- C05 契約: JSON `:190-228`、反転対象 `:227` は正確。
- §5 `master_seed`: `phase3-8c-preregistration.md:192` は正確。
- `_evaluate_undefined`: 実際の終端は `:2659` で、plan の `:2650` は途中まで。
- `PredicateRegistry.evaluate` は存在せず、実装は `PredicateRegistry.evaluate_all`（`evidence.py:2662-2735`）。名称を修正すべき。
- DECIDER_VERSION は `s8c_preregistration.py:51` で正確。

### DECIDER_VERSION

`git log --branches --not main -- orchestrator/campaign/s8c_preregistration.py` は空ではなく、C12 merge の `6c752666` が出ました。ファイル全体の「無競合」という親の主張は不正確です。

一方、`-G`/`-S 's8c-decider/v4'` と各関連 branch の実体を確認した限り、v4 の commit はまだ無く、main・T1353・T1355・T1379 は全て v3 です。現時点では v4 は利用可能ですが、T1355 の着地直前に再確認が必要です。T1379 HEAD は `a31832d9`、現在 main は `0665e5fc` です。

### 変異事前登録候補

- `s8c_preregistration_evidence_contract.v1.json:227` を true にせず false のままにする、または `evidence.py:2607-2615` の C05 registry 登録を落とす。bijectivity test（`test...:2770-2780`）で reject。
- `evidence.py:1666-1681` または `1722-1733` の required call/target を弱め、`consume_schedule` 未到達を通す。C05 token-only consumer の欠落 edge を別 fixture として追加し、`UNSATISFIED` にならなければ reject。
- `s8c_preregistration.py:51` を v3 のままにする。g8 の `decider_version` と v4 固定を明示検査し、世代 identity の不一致を reject。