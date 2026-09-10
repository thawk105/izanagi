## 実装した変更 (file:line)

- [_driver_configs](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_b4_launcher.py:147)
  - `base` に `_current_site`、`_admit_env_contract`、`_campaign_cfg_for_site` の順で射影を追加。
  - 分岐は `if base / elif trigger`。`sort` は射影対象外。
- [test_p3_b4_launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/test_p3_b4_launcher.py:24)
  - `site_policy.socket` を差し替える seam と N1 から N5 の test を追加。
- docs、台帳、既存 test の期待値は未変更。commit、add、stash、branch 操作も未実施。

## 追加した test node と対応する N

- N1: `test_base_driver_configs_project_both_arms_for_pegasus_compute`  
  on/off の未射影 ID との差、実 helper による射影済み ID との一致を検査。
- N2: `test_base_driver_configs_bind_resolved_contract_for_both_admitted_sites`  
  PEGASUS_COMPUTE と OTHER の contract binding を直接検査。
- N3: `test_base_launcher_pegasus_context_passes_real_authorization_and_g4`  
  launcher が発行した production context を実物の `require_b4_production_context` と `verify_b4_launch_context` に通す。registry spy のため launcher 分岐の証明であり、base `main` 全体の実走証明ではない。
- N4: `test_base_driver_configs_preserve_other_campaign_ids`  
  OTHER の ID 不変と `measurement_env` 不在を検査。
- N5: `test_sort_driver_configs_remain_unprojected_on_pegasus_compute`  
  PEGASUS_COMPUTE 下でも sort ID が未射影値を保つことを検査。

## 実走した検査 (argv と nodeid と結果)

新設 5 node:

```text
PYTHONPATH=. python3 tools/run_tests.py \
  orchestrator/tests/test_p3_b4_launcher.py::test_base_driver_configs_project_both_arms_for_pegasus_compute \
  orchestrator/tests/test_p3_b4_launcher.py::test_base_driver_configs_bind_resolved_contract_for_both_admitted_sites \
  orchestrator/tests/test_p3_b4_launcher.py::test_base_launcher_pegasus_context_passes_real_authorization_and_g4 \
  orchestrator/tests/test_p3_b4_launcher.py::test_base_driver_configs_preserve_other_campaign_ids \
  orchestrator/tests/test_p3_b4_launcher.py::test_sort_driver_configs_remain_unprojected_on_pegasus_compute
```

結果: rc=16。`qstat -Q preflight rc=1`、`child_started=false`。5 node とも未実走。

焦点 2 file と制約 meta-test:

```text
PYTHONPATH=. python3 tools/run_tests.py \
  orchestrator/tests/test_p3_b4_launcher.py \
  orchestrator/tests/test_p3_b4_closed_critic.py \
  orchestrator/tests/test_plain_runner_coverage.py
```

結果: rc=16、同じく子未起動。meta-test の次の 3 node も未実走。

- `test_every_test_file_is_self_runnable_or_allowlisted`
- `test_allowlist_has_no_stale_or_self_runnable_entries`
- `test_this_metatest_is_itself_self_runnable`

静的検査:

- `git diff --check -- orchestrator/campaign/p3_b4_launcher.py orchestrator/tests/test_p3_b4_launcher.py`: rc=0
- 両 Python file の `ast.parse`: rc=0
- `git diff --name-only`: 対象 2 file のみ

## 残った赤

観測された test 赤はありません。ただし pytest 子が一度も起動していないため、緑もありません。状態は「実装済み・未実走」です。

実走不能理由は、sandbox から login headroom 予約台帳を安全に更新できず compute dispatch へ倒れ、dispatch も `qstat -Q` で失敗したためです。

## 波及の静的列挙

- 直接 caller: `test_p3_b4_closed_critic.py:185,532,2702`
- `_marked_driver_configs` 経由: `:819,1002,1029,2322`
- production: `p3_b4_launcher.prepare_launch` と、その先の `launch_bootstrap` / `launch_continuation` 全 caller
- 共有 fixture: `conftest.py` の hostname 中立化により通常 test は OTHER。ID と `measurement_env` は従来どおりだが、base config には解決済み contract が束縛される。
- launcher bytes を含む closure hash は base、sort、trigger 全体で変化しうる。ただし sort と trigger の実行挙動は変更していない。
- base config の完全一致や contract field を見る consumer test は波及候補。既存期待値は変更していない。

変更前は base launcher が全 site で未射影 config を返し、PEGASUS_COMPUTE では driver の射影済み ID と食い違って厳密な授権境界に拒否されていました。変更後は PEGASUS_COMPUTE が一致し、OTHER の ID は不変、LOGIN と SUSPECT は launcher で早期拒否されます。sort、trigger、厳密比較、site allowlist は不変です。

## 総括

裁定のプラン v2 を対象 2 fileだけに実装しました。N1 から N5 と静的検査は揃っていますが、実行基盤の rc=16 により焦点 test と meta-test は未実走です。