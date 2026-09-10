## 所見対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| F1 private loader の戻り型破壊 | partial | 実装修正と静的確認は完了。runner が `qstat -Q` で失敗し、test child は未起動 |
| F2 到達不能な型 guard | partial | 全呼び手を確認して guard を削除。test は未実走 |
| 新規 regression | regressed なし | AST parse、import、signature 検査、`git diff --check` は成功 |

`closed` は申告しない。

## F1 の直し方と全数 grep

[attempt_registry_core.py:1400](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-fix1/orchestrator/campaign/attempt_registry_core.py:1400) に seed 版 `_load_registry_bytes_with_budget_counts(...)` を分離した。

[attempt_registry_core.py:1430](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-fix1/orchestrator/campaign/attempt_registry_core.py:1430) の `_load_registry_bytes(...)` は旧 signature と `RegistryRows` 戻り型へ復元した。通常 loader はこれを、budget-count loader は seed 版を使用する。

`orchestrator/campaign/` 全数 grep の結果:

- `_load_registry_bytes`: core 内の定義 `:1430`、通常 loader からの呼出し `:1446`
- `_load_registry_bytes_with_budget_counts`: core 内の定義 `:1400`、内部呼出し `:1434,1458`
- core private loader の外部直接参照: [trial_registry.py:2348](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-fix1/orchestrator/campaign/trial_registry.py:2348) の 1 件だけ
- `trial_registry.py:862` に同名の別ローカル関数があるが、core private 関数ではない

他に同型の外部直接参照はなかった。

## F2 の到達可能性の判定

全参照は定義を除いて 3 件だった。

- production: [s8b_attempt_registry.py:1208](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-fix1/orchestrator/campaign/s8b_attempt_registry.py:1208) の 1 件。`_read_regular_bytes()` の結果を `:1207` で非 `None` と確定して渡す。同関数は `bytes` の join を返す。
- test: [test_s8b_attempt_registry.py:2062](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-fix1/orchestrator/tests/test_s8b_attempt_registry.py:2062) と `:2091`。双方とも `Path.read_bytes()` を渡す。

非 `bytes` 入力は現行 caller から構成不能と判断し、[s8b_attempt_registry.py:586](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-fix1/orchestrator/campaign/s8b_attempt_registry.py:586) の型 guard を削除した。到達可能に見せる test は追加していない。

## 受理集合の変化

到達可能な入力の受理集合は変更していない。

- F1 は同じ parse・canonical 検査・replay を実行し、通常経路で budget counts を返さない旧境界へ戻しただけ
- seed 付き横断予算 API の挙動は維持
- F2 は型契約と全 caller が保証する `bytes` の外側にあった分岐だけを削除
- schema、retryable 集合、v2 mutation、claim、resume、terminal projectionには未変更

## 波及の静的列挙

- 所有外 caller: `trial_registry.py:2348` が F1 の直接修復対象
- public loader consumer: `s8b_holdout_admission.py:5620`、`s8b_scheduler_accounting.py:335`
- transitive consumer: `p3_autonomous_workload_trial.py:1380`
- consumer test: `test_trial_registry.py`、`test_attempt_registry_core_equivalence.py`、holdout、launcher、scheduler、reflux、floor campaign
- 共有 fixture: `s8b_floor_evidence_fixture.py`。変更していない
- fix では test file、fixture、`trial_registry.py` を編集していない
- 現在の変更は段 5 由来を含む許可済み 5 fileだけ。`git add`、commit は未実施

runner へ主面 3 fileと `test_trial_registry.py` を渡したが、`qstat -Q preflight rc=1`、`child_started=false`、rc=16 だった。実走 nodeid は 0 件。receipt は除去済み。

## 総括

- F1 と F2 の最小修正を作業ツリーへ残した。
- core private loader の外部直接参照は `trial_registry.py:2348` の 1 件だけ。
- F2 guard は production 1、test 2 callerの全てで到達不能だった。
- AST、import、signature、`git diff --check` は成功。
- pytest は dispatch 障害で未実走のため、両所見とも `partial`。