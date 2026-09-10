## 実装した内容

- [p3_s4_loop_sort.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/p3_s4_loop_sort.py:335): `_require_sort_oracle_contract()` を追加し、[run_one_iteration](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/p3_s4_loop_sort.py:388) で identity binding 前に一度だけ取得、既存唯一の `run_campaign()` へ渡した。写し元は [p3_s4_loop.py:1277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/p3_s4_loop.py:1277)、[1451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/p3_s4_loop.py:1451)、[1529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/p3_s4_loop.py:1529)。`default_cfg()` と `search_config` は不変。
- [loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/loop.py:257): keyword-only 引数を追加し、非 `None` 時だけ resolver と evaluator の options に追加した。写し元は同ファイルの backoff 経路 [256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/loop.py:256)、[479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/loop.py:479)、[563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/loop.py:563)。入口 gate、oracle import、既存 backoff gate は未変更。
- [pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/pipeline.py:903): `evaluate` / `_prepare_evaluation_core`、pre-build resolver、legacy/v2 build options を接続した。写し元は隣接する backoff 経路 [1092](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/pipeline.py:1092)、[1257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/pipeline.py:1257)、[1270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/pipeline.py:1270)、[1882](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/pipeline.py:1882)。
- [source_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/source_digest.py:2198): exact str・非空・ASCII・NUL なしを要求する sort binder と exact preimage を実装。[`_resolved_src_token`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/source_digest.py:2222) の相互排他、stock、sort、backoff の順を実装し、[`resolve_evidence`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/source_digest.py:2328) のみ接続した。写し元は [backoff binder](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/source_digest.py:2177)。`resolve()` / `src_token()` / `SourceEvidence` は未変更。
- [buildcache.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/buildcache.py:2245): 4 API の署名、`build_v2` wrapper、v2 hit/fresh と legacy hit/fresh の四出口、再 resolver を接続した。対応する backoff 位置は [2598](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/buildcache.py:2598)、[2841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/buildcache.py:2841)、[3012](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/buildcache.py:3012)、[3186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/buildcache.py:3186)、[3252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/campaign/buildcache.py:3252)。`cache_key()` / `_v2_identity()` は未変更。
- [test_p3_s4_loop_sort.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/tests/test_p3_s4_loop_sort.py:1252): T1〜T13 を追加した。13 test functions、parametrize 展開後 17 nodeids。写し元は [test_p3_s4_loop.py:3394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2253-sort-grammar-cache-binding/orchestrator/tests/test_p3_s4_loop.py:3394) 以降。既存テスト本文は変更していない。

## 変異 M1〜M14 の対応表

| 変異 | 殺すテスト | 単一の赤理由 |
|---|---|---|
| M1 | `test_require_sort_oracle_contract_accepts_only_running_contract` | 不正宣言を直接 helper に渡す。loop 入口に同じ gate はない。 |
| M2 | `test_sort_driver_forwards_producer_contract_to_run_campaign` | producer sentinel が既存呼出しの kwargs から欠落する。呼出し数は検査しない。 |
| M3 | `test_run_campaign_forwards_one_sort_contract_to_resolver_and_evaluate` | resolver spy の `sort_oracle_contract_id` だけが欠落する。spy 内部に拒否層はない。 |
| M4 | 同上 | evaluator spy の同 kwargs だけが欠落し、resolver 側は通過する。 |
| M5 | `test_pipeline_forwards_one_sort_contract_to_resolver_and_selected_build_api` | direct pipeline 経路の resolver kwargs だけが欠落する。外側 loop は実行しない。 |
| M6 | 同上 `[legacy]` | legacy build double の kwargs だけが欠落する。double 内部は実行しない。 |
| M7 | 同上 `[v2]` | v2 build double の kwargs だけが欠落する。wrapper 内部は実行しない。 |
| M8 | `test_sort_binder_exact_preimage_and_rejections` | 最初の対象 assertion `bound != raw` が失敗する。前後の resolver は呼ばない。 |
| M9 | 同上 | `bound != raw` 通過後、独立計算した exact preimage hash の一致だけが失敗する。 |
| M10 | `test_resolved_src_token_rejects_both_bindings` | `current != baseline` で相互排他の `pytest.raises` だけが失敗する。loop gate はない。 |
| M11 | `test_build_v2_wrapper_forwards_sort_contract_to_impl` | `_build_v2_impl` spy の kwargs だけが欠落する。impl は実行しない。 |
| M12 | `test_build_exits_recheck_with_sort_contract[v2-hit]` | v2 hit 出口の recheck spy kwargs だけが欠落する。resolver は spy の内側で実行しない。 |
| M13 | `test_build_exits_recheck_with_sort_contract[legacy-fresh]` | legacy fresh 出口の recheck spy kwargs だけが欠落する。 |
| M14 | なし、`SURVIVED` | 生成 bytes が同じ等価書換えなので、挙動観測テストには差がない。 |

## 実走結果

実装済み・未実走です。

`python3 tools/run_tests.py orchestrator/tests/test_p3_s4_loop_sort.py -q` を試したが、Pegasus の `qstat -Q` preflight が rc=1、runner は rc=16、`child_started=false` で、pytest nodeid は 1 件も実行されていない。したがって緑として報告できる nodeid・範囲はない。

静的には全 6 ファイルの AST parse、`git diff --check`、結合文字検査、呼出し数検査を通過。read-only smoke では import、契約 gate、exact binder、相互排他、8 seam の署名、campaign identity `p3-s5-sort-loop-s5-sort-autonomous-6f6a8cf1` を確認した。

runner が禁止領域へ自動生成した `receipt.json`、`request.json`、`interpreter_probe.py`、`dispatch.sh` は削除済み。再生成可能な一時診断物で、現存しない。

## 所有外への波及

`rg` による静的確認結果:

- `campaign.loop.run_campaign` の所有外 caller は `b10_backoff_shape_sweep.py`、`backoff_extended_sweep.py`、`backoff_repro.py`、`backoff_sweep.py`、`demo.py`、`p2_2.py`、`p3_kickoff.py`、`p3_s4_loop.py`、`p3_s4_loop_trigger_gating.py`、`p3_s4_red.py`、`paper_story_a1_paired.py`、`paper_story_a2_certification.py`、`s6_sort_sweep.py`、`s8a_trigger_sweep.py`、`sanity_silo.py`。いずれも新引数を渡さず既定 `None`。
- `resolve_evidence` の共有 consumer は backoff 系 5 本、`between_run_floor.py`、`build_admission.py`、`buildcache.py`、`loop.py`、`pegasus_floor_scoping.py`、`pipeline.py`、S1/S2/S3/S5/S8a/S8b 系、`screening_driver.py`。既存 caller の呼出し形は変わらない。
- build API の共有 consumer は backoff 系、between-run、Pegasus floor、pipeline、S1/S2/S3/S5、S8b floor。追加引数は keyword-only default `None`。
- seam 名を含む consumer/double は 42 test modules。重点波及先は `test_p3_s4_loop.py`、`test_buildcache_v2.py`、`test_build_site_gate.py`、`test_campaign.py`、`test_s6_sort_sweep.py`、`test_s1_direct_comparison.py`、`test_trigger_gate_binding.py`、各 S8b test。
- 制約 meta-test は `test_campaign.py:5355/5436` の caller inventory、`test_pytest_collection_config.py:1096` の oracle import/checker pin、`test_mutation_harness.py:857` の nodeid collection、`test_real_repo_serialization.py` / `conftest.py` の実 repo node inventory、`test_update_acceptance_duration_ledger.py` の ledger commitment を確認した。AST 上の sort driver `run_campaign` 呼出しは引き続き 1。
- checked-in duration ledger は既存 29 nodeidsのままで、新規 17 nodeidsは未登録。揮発時間を捏造できないため変更しておらず、親の段 6 実走後に collection/ledger 方針の確認が必要。

## 受理集合の不変

既定 `None` では source/evaluate/build options に新 key を追加せず、非 stock は従来の raw digest、stock は `"stock"` のままで、既存 caller の `SourceEvidence`・variant・cache identity は変わらない。  
verify、oracle、diff 検疫、auditor、`diffq_variant_id`、`record_diff_reject` の分岐は変更しておらず、scope 前の受理候補と拒否候補の集合は同じである。

## 総括

sort campaign の実契約 ID を、単一 producer から source token と両 cache API の四出口まで局所的に接続した。  
編集は許可された 6 ファイルだけで、backoff 経路・campaign identity・受理集合は維持した。  
Pegasus dispatch preflight failure のため pytest は未実走であり、成果は closed ではない。  
親の段 6 では新規 17 nodeids、D1411 回帰、共有 build/cache consumer、caller inventory、duration ledger を必ず実走確認する必要がある。