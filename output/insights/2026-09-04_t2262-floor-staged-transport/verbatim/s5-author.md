## 実装した内容

- 裁定 §2-1〜4: [s8b_floor_campaign.py:3101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:3101)
  - `reservation_binding.nonce` と canonical `receipt_path()` から payload を導出。
  - raw `IZANAGI_SUBMISSION_NONCE` は不使用。束縛不在は fail-closed。
  - payload prefix 全 component、payload root、3 source を no-follow 検査。
  - canonical `TMPDIR/izanagi-floor-fetchcontent` の repo 外判定をコピー前に実施し、事前不在＋排他 `mkdir`。
  - `shutil.copytree(..., symlinks=True, copy_function=copy2)` により symlink、mode bit、`.git` 全木を保持。
- 裁定 §2-5: [s8b_floor_campaign.py:3371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:3371)、[s8b_floor_campaign.py:4289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:4289)
  - default/explicit の双方を pin/clean 検査済み `source-dir` transportへ一本化。
  - core から検証済み binding と canonical repo root を fresh/resume 両経路へ転送。
- 裁定 §2-6, §2-8: [floor_campaign.sh:698](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:698)、[floor_campaign.sh:1200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/tools/pegasus/floor_campaign.sh:1200)
  - shell staging function、`fetchcontent-staging` phase、driver argv の `--fetchcontent-base-dir` を削除。
  - Python CLI の pilot専用 seam は維持。
- 裁定 §2-7: `_assert_official_permitted`、CLI official拒否、`_canonical_floor_fetchcontent_base(None)`、18名 classifier、eligibility判定式を `HEAD` と関数本文比較し不変を確認。
- 機構・変異テストは [test_s8b_floor_campaign.py:4264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/tests/test_s8b_floor_campaign.py:4264) 以降、shell契約は [test_pegasus_floor_tools.py:1213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/tests/test_pegasus_floor_tools.py:1213) ほかへ反映。

## 実走した検査

pytest nodeid は実走できていません。以下2集合を `tools/run_tests.py` へ渡しましたが、いずれも pytest child開始前に rc=16でした。

- 新規・改訂 nodeid:
  - `test_s8b_floor_campaign.py::test_floor_fetchcontent_default_uses_bound_nonce_and_preserves_copy_semantics`
  - `::test_floor_fetchcontent_default_rejects_missing_binding_without_ambient_fallback`
  - `::test_floor_fetchcontent_default_rejects_symlinked_fixed_prefix_ancestor`
  - `::test_floor_fetchcontent_default_rejects_unsafe_layout`
  - `::test_floor_fetchcontent_default_rejects_repo_destination_before_copy`
  - `::test_floor_default_transport_dirty_payload_reaches_pristine_pin_gate`
  - `::test_floor_default_transport_passes_three_verified_source_dirs`
  - `::test_default_staging_and_claim_seam_basis_keep_raw_argument_separate`
  - `::test_floor_dependency_source_dir_reads_and_binds_payload_policy`
  - `test_pegasus_floor_tools.py::test_floor_job_hardens_interpreter`
  - `::test_floor_job_invokes_fixed_pilot_cli_without_bypass`
  - `::test_floor_job_leaves_fetchcontent_staging_to_driver_default`
  - `::test_submit_receipt_round_trips_through_job_validator`
  - `::test_floor_protocol_resolution_is_shared_by_all_consumers`
  - 結果: rc=16、child_started=false、実走0件。
- 制約 meta-test・consumer nodeid:
  - `test_ccbench_spawn_sites.py::test_reviewed_process_launch_inventory_is_recursive_and_exact`
  - `test_acceptance_schedule_order.py::test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order`
  - `test_update_acceptance_duration_ledger.py::test_g7e_checked_in_ledger_has_valid_schema_and_finite_durations`
  - refreeze dataflow、oracle-n-pilot、buildcache source-dir、runtime projection、liveness関連の計14 nodeid
  - 結果: rc=16、child_started=false、実走0件。
- 2テストファイルの `--collect-only`: rc=16、child_started=false。
- 非pytest局所検査:
  - Python compile/import、`git diff --check`: rc=0。
  - positive copy、ancestor symlink、binding不在、dirty pin、3 source-dir transport probe: 各 rc=0。
  - protected関数 byte比較、production subprocess起動点12件の前後一致: rc=0。

## 変更した既存期待値

- `test_real_floor_prepare_material_oracle_and_capability_series_when_configured`: defaultが空 baseを後から埋める期待は誤りで、検証済み3 source-dirを事前 stagingする契約になったため。
- `test_floor_dependency_source_dir_reads_and_binds_payload_policy`（旧 `...base_only...`）: production defaultの `base-only` は外部取得可能で、裁定 §2-5 が `source-dir` へ改訂したため。
- `test_floor_job_hardens_interpreter`: `fetchcontent-staging` checkpoint phaseをshellから削除する裁定 §2-6のため。
- `test_floor_job_invokes_fixed_pilot_cli_without_bypass`: shell callerが transport seam 2 tokenを渡す期待は裁定 §2-6と逆だったため。
- `test_floor_job_leaves_fetchcontent_staging_to_driver_default`（旧 `...stages_payload...`）: shell stagingの存在期待はdriver内部既定化と矛盾するため。
- `test_floor_protocol_resolution_is_shared_by_all_consumers`: 記録されるdriver argvから同じ2 tokenを除く必要があるため。
- `test_production_floor_dependency_preflight_failure_persists_private_attempt[checkout]`: canonical `repo_root` がdriver staging/prebuildへ転送されるため、checkout診断pathもそのfixture root基準になる。
- `test_core_passes_fetchcontent_base_dir_to_fresh_and_resume_build_cells`: raw seamに加え、検証済み binding と repo root の両経路転送を要求するよう強化。

## 変異帰属の自己申告

| 変異 | 自己申告 |
|---|---|
| MU1 | 単一理由へ照準。binding nonceとambient nonceの双方に実payloadを置き、コピー内容の違いだけで検出。 |
| MU2 | 単一理由へ照準。driver helper直呼びで、固定prefix ancestorだけをsymlink化。production shellの既存検査はこのunit外。 |
| MU3 | 単一理由へ照準。ambient payloadが有効でもbinding不在だけで拒否。 |
| MU4 | 単一理由へ照準。mimallocだけをdirtyにし、後段masstree検査とは重ならない。 |
| MU5 | 単一理由へ照準。実3 Git sourceを検証後、prebuildへ渡る3 source-dirをexact検査。 |
| MU6 | 単一理由へ照準。実staging成立と、coreのraw引数→classifier→claim seam basisのAST dataflowを同時検査。 |
| MU7 | 単一理由にできない。事前 `lexists` [同:3228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:3228) と排他 `mkdir` [同:3237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:3237) が同じ既存destinationを拒否する。両方とも裁定の必須条件なので重複を残した。 |

いずれもpytest未実走のため、動的な mutation kill は未確定です。

## 波及可能性

- 所有外 caller: `s8b_oracle_n_pilot.py` は温存した `_canonical_floor_fetchcontent_base(None)` から非None baseを渡すため呼出し形は維持。
- `build_cells` の直接consumerである `test_s8b_materialization.py`、`test_s8b_dependency_prefix_bridge.py`、`test_s8b_predicate_build_proof.py` はcustom prepare経路だが、任意引数追加の波及候補。
- `s8b_holdout_admission.py` の部分claimは本変更をまたいでresumeできない。新しい `campaign_run_id` が必要。
- shell phase削除により、`floor_liveness` のstaging失敗診断はgeneric `floor-driver` へ退化する。
- buildcache completion identity、manifest/runtime projection、oracle-n-pilot、spawn inventoryのconsumer testsは未実走。
- 共有fixture `_receipt_validator_fragment` と `_driver_tail` を改訂。改名nodeidの旧duration-ledger entryは残り、新nodeidは未計測扱いになる可能性がある。

## 停止した項目

- pytest実走。Pegasus loginのユーザーcgroupは実効天井約14 GiBに対して約14.49 GiB使用中でlocal admission不可、計算ノードdispatchは `qstat -Q` が restricted socketでrc=1となり停止しました。
- 裁定L1/L2のworklog・decisions記録は編集許可4ファイル外なので未実施。親で記録が必要です。
- `bash -n` はPegasus実行体guardにより起動前拒否され、未実走です。
- 実装上の停止条件該当はなし。in-process copyで要求されたsymlink、mode bit、`.git` 全木を保持できることは局所probeで確認済みです。

## 総括

裁定 §2のdriver-owned staged transportを4ファイル内で実装しました。  
ambient nonceや外部取得へのfallbackはなく、defaultは検証済みbindingと3 source pin検査を必須化しています。  
official拒否、18名集合、eligibility式、canonical helperの`None`分岐は不変です。  
変更は未stage・未commitで、許可された4ファイルだけに残しています。  
pytestは実装済み・未実走のため、現時点ではclosedとは申告しません。