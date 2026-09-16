## 総括

単位Aを実装しました。編集は指定の5ファイルのみ。commit・所有外編集・歴史goldenの変更はありません。

gflags / glogをURL＋40桁pinで列挙し、`fetch` / `hydrate` / `verify` の既定対象を5本にしました。`verify-deps` は廃止しました。GitHubからの実取得は**実装済み・未実走**であり、wave全体のclosedは申告しません。

**policyの照合**

`sha256sum tools/pegasus/policy.json` の実測値：

```text
3a3c7d607de77e23368f9ce382b41e6e524de3ee1e2809e7c6d890ada95a6c90
```

親指定値と一致しました。policyの変更は指定2行のみです。`git diff --check` もrc=0でした。

**実走結果**

以下のfile名はすべて `orchestrator/tests/` 配下です。`::*` は全収集nodeを対象にした実走を示します。

| nodeid／範囲 | 結果 | rc |
|---|---:|---:|
| `test_pegasus_thirdparty_fetch.py::*` | 102 passed | 0 |
| `test_hooks.py::*` | 474 passed、既存skip 1件 | 0 |
| `test_plain_runner_coverage.py::*` | 3 passed | 0 |
| `test_silo_ladder_rung1_evidence.py::*` | 2 passed | 0 |
| `test_pegasus_tools.py::*` | 67 passed、2 failed | 1 |
| `test_backoff_extended_sweep.py::*` | 48 passed、1 failed | 1 |
| `test_p3_s4_loop_job_contract.py::*` | 82 passed | 0 |
| `test_paper_story_a1_job_contract.py::*` | 171 passed | 0 |
| `test_b4_binary_record.py::*` | 23 passed | 0 |
| `test_t126_pegasus_tools.py::test_shared_pegasus_policy_owns_no_t126_qualification_keys` | passed | 0 |
| `test_t126_pegasus_tools.py::*` | 長時間化のため中断。全体結果は未確定 | 130 |

hooksの当該tupleを使う次の2 nodeも成功しています。

- `test_bash_login_allows_fetch_third_party_sanctioned_spellings`
- `test_bash_compute_allows_fetch_third_party_spellings`

調達テストでは、両依存について実Git fixtureのHEAD・dirty・shallow・originを変異させ、本物の検証器による拒否を確認しました。URL・pin形式の負例も追加しました。[調達テスト全nodeの実走ログ](/tmp/t548-fetch-final.log)

追加検査の制限：

- `test_check_docs.py`：growth holdが実行を拒否、rc=1。検査本体は未実走です。
- `test_mocc_trace_job_contract.py`：自走入口がなく直接実行は0件、rc=0。緑に数えていません。
- GitHubへのclone、build/install、実consumer・計算ノード走行、M1〜M7の変異実験は未実走です。
- 子の実走は親の全走を代替しません。

**期待赤との突き合わせ**

実際の赤は、指定された期待赤集合内の次の3件でした。

- `test_pegasus_tools.py::test_certify_gflags_stage_is_pinned_fail_closed_and_precedes_ccbench`
- `test_pegasus_tools.py::test_certify_glog_stage_is_pinned_fail_closed_and_precedes_ccbench`
- `test_backoff_extended_sweep.py::test_b10_job_builds_pinned_dependencies_in_job_scratch`

すべて旧 `*_source_path` の要求が原因です。p3・a1・b4は赤になりませんでしたが、旧fixture・stub・静的契約が残るため、consumer移行済みとは判断できません。T-126全体は未完了です。最終実走で、期待集合外のテスト失敗は確認していません。ただし上記の実行拒否・未実走範囲は残ります。

**削除したnode**

接頭辞は `orchestrator/tests/test_pegasus_thirdparty_fetch.py::` です。

- `test_verify_deps_allows_only_shallow_metadata_exception[dangerous-config-dangerous Git config]`
- `test_verify_deps_allows_only_shallow_metadata_exception[commondir-commondir]`
- `test_verify_deps_allows_only_shallow_metadata_exception[sparse-sparse checkout]`
- `test_verify_deps_allows_only_shallow_metadata_exception[assume-unchanged-index bit]`
- `test_verify_deps_is_separate_and_accepts_existing_shallow_dependency`
- `test_cache_root_must_be_explicit_or_environment`

元の4呼出箇所は3関数・展開後6 nodeに当たります。専用helper `_expected_dependency_records` も削除しました。それ以外の既存nodeは削除していません。既存3依存の検査は保持しています。

**受理・拒否挙動の変化**

変更前はcache操作が3本のみで、gflags / glogは旧絶対パスを `verify-deps` が検査し、shallowを許可・originを未照合でした。

変更後はCLIの3操作すべてが5本を対象にします。新2本にも既存のHEAD完全一致・clean・origin一致・非shallowの検査が適用されます。したがって、旧経路で受理したshallowやorigin不一致の状態は受理集合から除かれます。互換入口・opt-inは追加していません。

**所有外への静的波及**

未変更の付け替え対象は次のとおりです。

- shell：`a5_second_boot_backoff_sweep.sh`、`b10_backoff_grid.sh`、`certify_calibration.sh`、`floor_campaign.sh`、`floor_scoping.sh`、`mocc_trace_pilot.sh`、`oracle_n_pilot.sh`、`p3_s4_loop_pegasus.sh`、`paper_story_a1_paired.sh`、`silo_ladder_rung1.sh`、`t126_qualification.sh`、`t141_region_profile.sh`
- probes：`t1683_rr5_cost_probe.pbs`、`t2187_adaptive_const_probe.pbs`、`t2228_driver_gate_liveness_probe.pbs`
- Python：`s3_mocc_lock_coverage.py`、`silo_ladder_rung1.py`、`b4_binary_record.py`、`qualification/identity.py`、`qualification/submission.py`
- その他：`mocc_trace_v1_policy.json`、`tools/pegasus/README.md`

共有 `git_fixture` の旧locator生成は所有テスト内でURL生成へ変更しました。一方、T-126・a1のfixtureには旧locator生成が残ります。MOCC契約テストは `_load_policy()` の3要素戻り値をstubしているため、その形を維持し、CLIで両列挙を必ず合算しました。policy bytes変更による新identity・bindingへの影響も残ります。

実装上の未解決判断はありません。探索した `conftest.py`、`orchestrator/conftest.py`、`orchestrator/tests/git_fixture.py` は不在でしたが、射影された必読fileではないため停止理由にしていません。