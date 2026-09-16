## 編集した差分

plan v2 を実装しました。変更後の位置は以下です。

- `orchestrator/campaign/p3_s4_loop.py:2714–2724`：指定の if/raise block を emit の `return 0` 後、`build_run_context` 前に挿入。
- `orchestrator/tests/test_p3_s4_loop.py:6587`：I の後半 argv に coder-role を追加。
- 同 file の `7206`、`7246`、`7269`：N・P・F を新設。

既存関数の差分比較でも、変更は I のみでした。E・K、共有 helper、fixture は無変更です。

復元後の `git diff --stat`：

```text
 orchestrator/campaign/p3_s4_loop.py   | 11 +++++
 orchestrator/tests/test_p3_s4_loop.py | 91 +++++++++++++++++++++++++++++++++++
 2 files changed, 102 insertions(+)
```

`git diff --check` は指摘なしです。

## 直接呼び出しと反実仮想

`PYTHONPATH=.`、`PYTHONDONTWRITEBYTECODE=1` で実施しました。各 test に `Path(tempfile.mkdtemp())` と `pytest.MonkeyPatch()` を渡し、終了時に `undo()` しました。

初回確認で次の環境依存を検出しました。

```text
ModuleNotFoundError: No module named 'p3_b4_proposal_binding_support'
ExecutionGuardError: 計測用 env bytes は site='PEGASUS_LOGIN' では生成できない
```

呼び出し用スクリプトで tests ディレクトリを `sys.path` に追加し、既存 conftest の site fixture と同じ `gethostname → test-host`、`_has_nqsv → False` を設定して、次を確認しました。

```text
DIRECT_CALL_PASS test_main_nonempty_manifest_requires_coder_role_before_prepare
DIRECT_CALL_PASS test_main_nonempty_manifest_and_k2_role_accept_k2_wrapper
DIRECT_CALL_PASS test_main_fixture_route_accepts_nonempty_manifest_without_coder_role
DIRECT_CALL_PASS test_emit_context_and_run_iteration_share_manifest_campaign_identity
DIRECT_CALL_PASS test_main_manifest_only_accepts_legacy_flattened_proposal
DIRECT_CALL_PASS test_main_manifest_and_k2_role_accept_k2_wrapper
```

反実仮想では production の条件を一時的に `False and a.run_iteration` に変更し、N を直接呼びました。

```text
COUNTERFACTUAL_RED Failed: drive_iteration reached
RESTORED original production bytes
```

`finally` で元の bytes に復元し、一致を確認しました。pytest・`tools/run_tests.py` は起動していません。

## 波及の静的列挙

test file 内の `L.main(` 全16出現と `--knowledge-manifest` 全5出現は以下です。行番号は変更後です。

| test / helper | `L.main(` | `--knowledge-manifest` | 関係 |
|---|---|---|---|
| sanctioned CLI stdout | 4465, 4504 | — | manifest なし |
| B4 fixture bypass 拒否 | 5674 | — | 既存 B4 拒否 |
| B4 receipt CLI | 5686, 5688 | — | 既存 B4 拒否 |
| I：campaign identity 共有 | 6546, 6585 | 6541 | emit 維持、run に role 追加 |
| resolved projection の loader 引渡し | 6637 | 6640 | 空 sources、role あり |
| emit new state | 6660 | — | emit |
| emit policy hint | 6679 | — | emit |
| emit CLI policy hint | 6692 | — | emit |
| `_run_main_with_actual_proposal_loader` | 7202 | 7198 | P・E・K が共有 |
| N | 7235 | 7238 | 非空、role なしの拒否 |
| F | 7290 | 7292 | fixture 経路の受理 |
| prebuild incompatible routes | 8670 | — | 既存 CLI 拒否 |
| prebuild 両 main 経路 | 8919 | — | manifest なし |

所有外 caller は `p3_b4_launcher.py:141` の base driver 登録、および `tools/pegasus/p3_s4_loop_pegasus.sh:581,588` の CLI 起動を確認しました。後者の manifest / role 引渡しは `78–79` にあります。

共有面は `_resolved_knowledge_fixture`、`_resolved_empty_knowledge_fixture`、実 proposal loader helper、conftest の site fixture です。いずれも変更していません。

`orchestrator/tests/` の `p3_s4_loop` 参照検索で、変更対象外の consumer 候補として次を確認しました（参照の存在を示すもので、実走済みという意味ではありません）。

```text
test_real_repo_serialization.py
test_p3_b4_raw_record_producer.py
test_p3_s4_loop_sort.py
test_p3_exploration_namespace.py
test_p3_s4_loop_trigger_gating.py
test_campaign.py
test_p3_s4_loop_job_contract.py
test_codex_agents.py
test_hooks.py
test_p3_build_authority_cli.py
test_s1_direct_comparison.py
test_p3_b4_proposal_binding.py
test_s8a_trigger_sweep.py
test_p3_b4_wiring_probe.py
test_pytest_collection_config.py
test_floor_pair_driver.py
test_s8b_floor_campaign.py
test_auditor_gate.py
test_p3_b4_material_report.py
test_update_acceptance_duration_ledger.py
test_trigger_gate_binding.py
test_s8b_oracle_driver.py
test_s1_known_axes_freeze.py
test_p3_b4_launcher.py
test_p3_b4_closed_critic.py
test_sort_swo_oracle.py
test_layer3_report.py
test_s6_sort_sweep.py
test_campaign_import_invariant.py
test_pegasus_tools.py
```

支援ファイルには `conftest.py`、`s1_expected_goldens.py`、`acceptance_duration_ledger.json` の参照があります。`test_p3_s4_loop` を名指す検索では、新設 test 数や全関数名集合を固定する meta-test は見つかりませんでした。`test_real_repo_serialization.py` と conftest は既存 checkpoint node を列挙しており、全体 collection を行うテストへの影響は親の実走対象です。

B-4 closure は production bytes の変更による hash 変化があり、旧 closure の互換性は保証しません。非空 sources と `completed_empty` の逆向き整合検査も scope 外です。

## 受理・拒否の含意

受理について、変更前に通っていた空 sources＋role 省略、適切な manifest＋K2 role、manifest なし、emit、fixture 経路は、変更後も既存条件の下で受理されます。  
拒否について、変更前には legacy loader へ進めた「run あり・emit なし・sources 非空・role なし」の1セルだけが、変更後は build context 作成・prepare・drive より前に `ValueError` となります。

## 変異 anchor

以下の old 逐語は、復元後の production file 内でそれぞれ出現数1を確認しました。

M1：2714–2724 の削除 block。前後を含む一意 anchor は2713–2725です。

```python
        return 0
    if (
        a.run_iteration
        and resolved_knowledge is not None
        and resolved_knowledge.manifest.sources
        and a.coder_role is None
    ):
        raise ValueError(
            "--run-iteration: --knowledge-manifest の sources が非空 "
            f"(sources_count={len(resolved_knowledge.manifest.sources)}) "
            "のため --coder-role coder-v4-autonomous-k2 が必要"
        )
    build_context = build_run_context(
```

M2：2717。

```python
        and resolved_knowledge.manifest.sources
```

M3：2718。

```python
        and a.coder_role is None
```

M4：2720–2724。

```python
        raise ValueError(
            "--run-iteration: --knowledge-manifest の sources が非空 "
            f"(sources_count={len(resolved_knowledge.manifest.sources)}) "
            "のため --coder-role coder-v4-autonomous-k2 が必要"
        )
```

M5：2714–2716。run guard 除去用の一意 anchor。

```python
    if (
        a.run_iteration
        and resolved_knowledge is not None
```

M1〜M5 の変異 harness 自体は未実走です。

## 総括

**実装済み・未実走（親が実測する）**。6 test の直接呼び出しと、N の反実仮想赤化を確認しました。

作業リポジトリのステージング・commit は行っていません。指定の既存 fixture は `/tmp` 内で Git 履歴を作成しました。

この会話には `-o` の出力先パスが提示されていないため、報告用ファイルは作成していません。