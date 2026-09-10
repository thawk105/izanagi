実装は完了しましたが、Pegasus の dispatch preflight 障害により pytest は未実走です。そのため緑・closed は主張しません。docs・activation leaf/data・commit には触れていません。

変更後は [env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract.py:405) の frozen `AuthorizedContract` と `authorize()` が契約・activation state・serial/hash・PID・process seal を一体で発行します。[execution_guard.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/execution_guard.py:44) はその値だけから契約を解決し、`lookup()` と `lookup_required_attestation_contract()` への fallback を持ちません。

変更前後の挙動は次のとおりです。

- 変更前: 素の `ExecutionEnvironmentContract` を受理し、guard 内で receipt を自己発行・自己照合していた。
- 変更後: `authorize()` が発行した exact `AuthorizedContract` のみ受理する。素の契約、コピー、改竄、stale、別 PID/seal、fork 継承値は拒否する。
- Pegasus required 契約も receipt 内 state の active rows から導出する。
- serial 2 の Pegasus g2 は取得口→guard→`pipeline.evaluate` を通り、同 state の g1 authorization は拒否するテストを追加した。
- [t126_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/qualification/t126_driver.py:512) は fork 後の child 内で authorization を再取得する。
- floor/oracle/selector/T126/PBS wrapper の入口 gate は追加していない。

## 総括

### 1. 所見対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| R1: caller-held receipt | partial | 実装・全 production caller 配線・raw contract 拒否テストは完了。pytest 未実走 |
| R2: Pegasus g2 production seam | partial | serial 2 g2 の certified sink 正例、g1 拒否、lookup 不使用を追加。pytest 未実走 |
| R3: thread-held-lock fork | partial | worker thread＋Event＋bounded pipe/select＋timeout kill/wait を追加。callback 削除時は継承 lock で timeout する構造。pytest 未実走 |
| regressed | なしを静的確認 | compileall・diff check は成功。ただし実走による確定なし |

### 2. 変更ファイルと行数

段 6 integration snapshot との差分は **29 files、+478/-304** です。

主要・重複ファイル:

- `env_contract.py` `+69/-0`
- `execution_guard.py` `+53/-122`
- `test_campaign.py` `+82/-79`
- `test_execution_guard.py` `+101/-21`
- `test_env_contract_activation.py` `+56/-0`

caller・consumer 追随:

```text
backoff_repro.py                 +1/-1
backoff_sweep.py                 +4/-4
demo.py                          +2/-2
loop.py                          +3/-3
p2_2.py                          +1/-1
p3_kickoff.py                    +2/-2
p3_s4_loop.py                    +1/-1
p3_s4_loop_sort.py               +1/-1
p3_s4_loop_trigger_gating.py     +2/-1
p3_s4_red.py                     +2/-2
pipeline.py                      +1/-1
s1_direct_comparison.py          +1/-1
s6_sort_sweep.py                 +3/-3
s8a_trigger_sweep.py             +3/-3
s8b_oracle_driver.py             +9/-5
sanity_silo.py                   +3/-2
screening_driver.py              +3/-3
qualification/t126_driver.py     +5/-1
test_dev_wave_land.py            +4/-3
test_p3_build_authority_cli.py   +2/-1
test_s1_direct_comparison.py     +4/-3
test_s8b_oracle_driver.py        +18/-4
test_screening_driver.py         +21/-20
test_t126_qualification_driver.py +21/-14
```

### 3. 走らせた検査と結果

- `python3 -m compileall -q orchestrator/campaign orchestrator/qualification orchestrator/tests`: rc=0
- `git diff --check`: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- production caller 静的検索: `authorization_contract=env_contract.lookup(...)` および素の contract 渡しは残存なし
- pytest runner は以下を試行したが、すべてテスト開始前に rc=16:
  - `test_execution_guard.py + test_env_contract_activation.py + test_campaign.py`
  - `test_execution_guard.py`
  - `test_activation_receipt_resolves_current_contract_without_lookup`
  - 関連7ファイルの `--collect-only`
- 共通理由: `Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1`

### 4. 未実走・未達

- 焦点 pytest、consumer test、meta-test、受入全走、変異検査は未実走。
- 既知の赤2群には到達していない。
- 緑・closed の主張なし。
- docs 編集、commit、provenance 監査は指示どおり未実施。

### 5. 親への申し送り

- dispatch 復旧後、まず追加した以下の node を実走してください。
  - `test_pegasus_g2_authorization_reaches_certified_sink_without_lookup`
  - `test_worker_thread_held_receipt_lock_is_reinitialized_after_fork`
  - `test_plain_execution_environment_contract_is_rejected`
  - `test_fork_child_cannot_reuse_parent_activation_receipt`
- 続いて `test_campaign.py`、`test_screening_driver.py`、`test_s1_direct_comparison.py`、`test_s8b_oracle_driver.py`、`test_t126_qualification_driver.py` を通す必要があります。
- 所有外への静的波及は、module-level authorization fixture、oracle `_V2Plan` fixture、T126 direct pipeline fixture、dev-wave-land/P3 CLI の直接 sink consumer まで追随済みです。`test_s6_sort_sweep.py` と `test_s8a_trigger_sweep.py` は kwargs 捕捉のみで、呼出形の変更不要と確認しました。
- `env_contract_activation.py`、`env_contract_activations/`、docs、既存期待値の意味、入口 gate は未変更です。