## 総括

単位 C のコード・テストを実装し、closure を exact 25 path へ拡張した。  
read-only 批准台帳 verifier と必須の正負対照を追加した。  
`ident.py` には単位 A 側で 1 行の呼出し追加が必要で、現状は未閉包である。  
pytest は dispatch 障害で未実走。commit・docs・`hooks/` は変更していない。

## exact closure 集合と導出根拠

exact 25 path は以下。

- 従来 14:
  `env_contract.py`, `env_contract_activation.py`, `execution_guard.py`, `loop.py`, `pipeline.py`, `wal.py`, `ident.py`, `artifact_admission.py`, `verifier/core.py`, `dsg.py`, `model.py`, `parse.py`, `__init__.py`, `report.py`
- S8C 判定器 3:
  `s8c_preregistration.py`, `s8c_preregistration_evidence.py`, `s8c_generation_projection.py`
- 批准比較の自己保護 3:
  `campaign_lock.py`, `contract_loader_binding.py`, `enforcement_source_ratification.py`
- receipt 面 5:
  `guided.py`, `replay.py`, `qualification/artifacts.py`, `qualification/t126_driver.py`, `verifier/commit_receipt.py`

S8C 3 本は `CORE_MODULE_PATH` / `EVALUATOR_MODULE_PATH` / `PROJECTION_MODULE_PATH` と実値を照合した。`s8b_oracle_judge.py` は除外した。

receipt 面を除外すると、具体的には guided の source proof、replay の source receipt admission、qualification sink の receipt 検証、driver の source-lock binding、issuer 本体を弱化しても digest が変わらない。一方、`t126_evaluation_event_schema.json` は `artifacts.py` の live・historical 意味検査を単独では迂回できないため、過剰閉包化を避けて除外した。`pipeline.py`、`wal.py`、verifier entrypoint/core は従来 14 に既収載。

台帳データ自身は自己参照を避けるため closure 外。Git commit SHA も closure digest に含めていない。

## 変更点 (file:line)

- [campaign_lock.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/campaign_lock.py:29): exact 25 path を単一源として固定。
- [enforcement_source_ratification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/enforcement_source_ratification.py:81): canonical path→blob SHA-256 map の closure digest。
- [enforcement_source_ratification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/enforcement_source_ratification.py:99): exact schema・canonical JSONL 検査。
- [enforcement_source_ratification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/enforcement_source_ratification.py:241): committed history の strict-prefix、一回一行追加検査。
- [contract_loader_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/contract_loader_binding.py:363): binding map を批准比較へ渡す adapter。
- [artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/artifact_admission.py:65): E1 scope 表示を exact 25 に更新。
- [test_t671_source_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/tests/test_t671_source_binding.py:181): exact 集合、S8C 権威、receipt 面、verifier census を固定。
- [test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/tests/test_artifact_admission.py:46): closure 専用 E1 fixture を exact 25 化。
- [test_enforcement_source_ratification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/tests/test_enforcement_source_ratification.py:120): 批准台帳の正負対照一式。

## 負の対照

実装したテストは以下。

- 未批准 digest からの新 certified lock を拒否。
- テスト内で批准行を持つ一時 Git repo を作り、新 lock が成功する正例。
- 台帳行の削除・置換・並替え・一度の複数行追加を個別に拒否。
- 批准 digest と実 path map の不一致を拒否。
- non-canonical JSON、extra key、終端改行欠落を拒否。
- S8C 3 本を各 1 本だけ改変し、旧 exact 14 は通るが exact 25 は拒否。
- receipt 追加面 5 本も各 1 本だけ改変し、同じ旧 14/new 25 対照を固定。
- `commit_receipt.py` を verifier package census へ正規登録。

## 所有外への波及 (親が回す分)

- [ident.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/ident.py:234) の live verify 直後に、単位 A 側で次の 1 行が必要。

  ```python
  contract_loader_binding.verify_ratified_contract_loader_binding(binding)
  ```

  現状、この欠落を `test_new_certified_lock_rejects_unratified_closure_digest` と call-site census が検出する設計。

- `test_s6_sort_sweep.py:620` と `test_s8a_trigger_sweep.py:830` の closure fixture docstring に旧 `exact 14-path` が残る。fixture 本体は tuple を動的反復するため機能変更不要だが、所有外なので編集していない。
- `campaign_lock_test_support.py`、`test_campaign_lock_codec.py`、`test_bench_first_real_wal.py`、`test_layer3_report.py`、`test_env_contract_activation.py` は動的 consumer で変更不要。
- 単位 A 新設の `test_t762_ident_wrapper.py` も動的 consumer として追加検出したが変更不要。
- `hooks/enforcement-source-closure-ratifications.v1.jsonl` は作成・追記していない。committed path 不在を 0 行として fail-closed に扱う。

## 未実走・未解決

- `python3 tools/run_tests.py orchestrator/tests/test_enforcement_source_ratification.py -q` を2回、対象3 fileの collect-only を1回試したが、すべて `qstat -Q preflight rc=1`、runner rc=16。pytest 本体は未起動・0 nodeid。
- よって「実装済み・未実走」であり、closed とは申告しない。
- 静的検査は AST parse 7/7、`git diff --check`、closure 25件・重複0件を確認済み。
- closure member を編集中のため、commit 前の実 repo 検査では `contract-loader-drift` が予想される。
- docs 編集・commit は行っていない。