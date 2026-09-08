## 総括

must-fix はありません。R1〜R4 は裁定どおり実装され、余分な production 判定も追加されていません。  
MU-1 / MU-2 はともに、新規 2 node が固有理由で殺します。MU-2 の再登録は不要です。  
実 repo 負例の展開元は変異 worktree ではなく `git archive <HEAD oid>` の blob で、二重変異はありません。  
以下は静的予測であり、このレビューでは pytest・変異 probe を実走していません。

## 変異事前登録の評価

### MU-1 — 3 件目を削除

殺されます。[判定対象 tuple](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/s8c_preregistration_evidence.py:2065) が `mark` と `forbid` だけになるため、`reject_started_trial` を除去した入力が `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` まで通ります。次の final status assert が赤になります。

- `orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_c04_rejects_missing_started_trial_preflight`
- `orchestrator/tests/test_s8c_preregistration_predicates.py::test_c04_rejects_missing_started_trial_preflight`

前者は xdist の記録形式によって `@s8c-predicate-snapshot` suffix が付く可能性があるため、mutation ledger の exact node 文字列は計画どおり probe で確定すべきです。

### MU-2 — 3 件目を `forbid_trial_restart` の重複へ変更

これも殺されます。`_declared_call` の真偽は確かに `mark=True, forbid=True, forbid=True` となりますが、それこそが `reject_started_trial` 欠落を見逃すため、上記 2 node が MU-1 と同じ形で赤になります。登録し直しは不要です。

既存 C04 負例は主として `mark_experiment_indeterminate`、`forbid_trial_restart`、`main -> run_trial` を壊すため、MU-1/MU-2でも予測上は引き続き緑です。したがって DW-M08 の固有 semantic delta は新規 2 node だけです。

### drift mask と帰属

新規 2 node はどちらも [`M.get_registry().evaluate_all(...)`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:140) を直接呼び、`contract_loader_binding` を通りません。したがって `contract-loader-drift` の mask ではなく、C04 の最終 status assert による固有 kill です。

一方、対象 file は [`CONTRACT_LOADER_RELATIVE_PATHS`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/campaign_lock.py:49) に含まれるため、repo-wide 走行では無関係な mask failure も出ます。静的に少なくとも次が候補です。

- `test_campaign.py::test_ensure_campaign_identity_uses_atomic_lock_and_loser_only_verifies`
- `_writer_authority()` を読む `test_p3_b4_raw_record_producer.py` の複数 node

helper fan-out と xdist 配置があるため、mask の完全な exact-set は probe で観測が必要です。

### `git archive` の展開元

[`_snapshot_current_commit`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:153) は先に `git rev-parse HEAD` で `evaluated_head` を固定し、`git archive ... evaluated_head` を実行しています。展開される workload / registry は HEAD blob です。

worktree から上書きするのは evidence contract だけであり、今回の evaluator 変異や production call 除去は展開物へ混入しません。二重変異による帰属破壊はありません。

## 所見

### 焦点走の列挙は広義 consumer を 2 file 取りこぼしている

file:line:

- [test_s8c_cli_entrypoints.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_cli_entrypoints.py:29)
- [test_s8c_gate_report.py:464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_gate_report.py:464)

なぜ破れるか: grep 上、前者は `EVALUATOR_MODULE_PATH` の実 bytes を一時 repo へコピーして library/CLI 同値性を検査し、後者は実 HEAD の activation report を gate report へ投影します。親の 6 file には含まれていません。ただし両者とも C04 の固定意味を pin せず、MU-1/MU-2を殺すテストでもないため、今回の semantic focus に実質的な穴はありません。

成果物影響: evaluator の import/CLI transport や report 投影まで同時に壊れた場合、レポートの predicate 値・参照が library とずれる可能性がありますが、今回の 1 行変更はその経路を変更していません。

重さ: **nit**

### 共有 C04 fixture の reader inventory に 1 node の明記漏れ

file:line: [test_s8c_preregistration_predicates.py:2866](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:2866)

なぜ破れるか: `test_registry_preserves_reachability_limit_reason` も `_negative_control_case("nc_c04_partial_crash_survives")` を読みます。実装子の「parametrize 群」以外の reader です。ただし explorer を即座に例外化するテストなので、registry stub 拡張による期待値変化はありません。ほかの C04 reader は同じ test file 内の absence-shape、entrypoint-cut、test-only-target、unimported-decoy、および既存 negative-control parametrize です。

成果物影響: 現差分ではありません。将来 fixture 構築が C04 評価前に失敗すると、error reason の保存性を検査できなくなるだけです。

重さ: **nit**

R1〜R4については不足・過剰なしです。

- R1: `reject_started_trial` の target 1 行だけ追加。
- R2: import、preflight call、registry stub 定義を追加し、既存 negative-control ID は不変。
- R3: 実 HEAD blob から call だけを除去し、他 2 call と両定義の残存を確認。
- R4: token-only fixture から 3 件目だけを除去。
- reason code、contract JSON、registry `_functions` 検査は未変更。

契約 exact-set は既に [`reject_started_trial` を含む 5 個の C04 symbol`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_invariant.py:70) を pin し、契約と production symbol を比較するだけです。evaluator の target tuple は比較対象でないため変更不要です。

`test_plain_runner_coverage.py` は test filename と `__main__`/allowlist だけを列挙します。新規 file、改名、runner 変更がないため、今回の焦点走から外して問題ありません。

## scope 外の real 所見

新規所見はありません。段4で裁定済みの呼出し位置・支配関係、callee 本体、契約 `field_paths` の状態遷移検査は再提出しません。repo-wide 変異時の `contract-loader-drift` は実在する帰属 mask ですが、二つの owner node 自体は mask を経由しないため、計画どおり「probe で全 failure set を観測し、mask 込み KILLED、owner 証拠は新規 2 node」と分離できます。