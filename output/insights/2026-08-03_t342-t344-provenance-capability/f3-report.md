実装・テスト修正を working tree に残しました。docs、`output/`、所有外ファイル、staging、commit、branch は変更していません。

## 80件の対応表

`closed` は失敗トレース上の原因を静的に解消済み、ただし pytest 未実行という意味です。

| 型 | 件数 | 状態 | 対応 |
|---|---:|---|---|
| campaign identity / driver policy 配線 | 35 | partial | 34件を修正。S8a旧ID sentinel 1件は裁定上変更せず残置 |
| SourceEvidence API・caller/mock追随 | 19 | closed | `resolve_evidence` caller、S1準備境界、mockを現契約へ追随 |
| attempt topology・receipt・checkpoint | 10 | closed | receiptful fixture、pre-build reject attempt ID、policy-aware replay |
| critic validated-view consumer | 6 | closed | 全loaderを `require_admitted_campaign()` の view 経由へ |
| Layer3一時fixture・chain | 5 | partial | git HEAD依存4件を修正。旧campaign ID固定1件は残置 |
| buildcache v2 fixture | 3 | closed | enum typo2件、同一canonical source root fixture 1件 |
| overlay改変判定 | 1 | closed | semantic WAL parseより先にexact byte/hash照合 |
| Layer3 v3期待 | 1 | closed | 明示許可されたv2→v3期待変更 |
| regressed | 0 | — | 静的検査で新規回帰なし |
| 合計 | 80 | 78 closed / 2 partial | 動的受入は未検証 |

主要な実装修正は以下です。

- policyをdefault configとS1/S6/S8a driverへ束縛: [p3_s4_loop.py:520](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/campaign/p3_s4_loop.py:520)、[s1_direct_comparison.py:216](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/campaign/s1_direct_comparison.py:216)、[s6_sort_sweep.py:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/campaign/s6_sort_sweep.py:168)、[s8a_trigger_sweep.py:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/campaign/s8a_trigger_sweep.py:208)
- receiptless pre-build rejectに一意なattempt IDを付与: [p3_s4_loop.py:232](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/campaign/p3_s4_loop.py:232)
- criticをvalidated viewへ収束: [p3_s4_loop.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/campaign/p3_s4_loop.py:254)
- S1 preparationは安定tokenだけ取得し、full evidence検証はmaterializer境界に維持: [s1_direct_comparison.py:557](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/campaign/s1_direct_comparison.py:557)

## Layer3 v3とv2読み取り互換

v3を生成しつつ、`schema_version == layer3-material-report/v2` の場合だけv3 schemaのコピーから `admission_decision` を除いたreader schemaを組み立てています。[layer3_report.py:190](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/campaign/layer3_report.py:190)

この互換経路は [test_layer3_report.py:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/tests/test_layer3_report.py:76) が、v2 reportから`admission_decision`を除いても検証可能であることを固定しています。v3期待への変更は許可対象の [test_t126_qualification_artifacts.py:281](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/tests/test_t126_qualification_artifacts.py:281) だけです。

## Overlay境界

2つの線引きは維持しています。

- 新schemaのterminal buildにはpositive receiptとattempt topologyを要求: [artifact_admission.py:384](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/campaign/artifact_admission.py:384)。positive controlは [test_artifact_admission.py:167](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/tests/test_artifact_admission.py:167)、receiptless terminal拒否は [test_artifact_admission.py:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/tests/test_artifact_admission.py:174)。
- 非掲載のpre-policy歴史成果物は一括拒否しない: [artifact_admission.py:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/campaign/artifact_admission.py:367)、固定テストは [test_artifact_admission.py:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/tests/test_artifact_admission.py:180)。

既知overlayはWAL parse前にpath/ID/lock SHA/WAL SHAを照合し、改変WALがgeneric parse errorへfall-throughしないようにしました。[artifact_admission.py:316](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/campaign/artifact_admission.py:316)。3件の既定除外は [test_artifact_admission.py:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/tests/test_artifact_admission.py:134)、改変判定は [test_artifact_admission.py:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/tests/test_artifact_admission.py:153) が固定します。

## 検査結果

計算ノードdispatchを3回試しましたが、すべて収集前に `qstat -Q preflight rc=1`、runner rc=16で停止しました。実行件数は0です。

最後に指定したnodeid:

- `test_artifact_admission.py::test_overlay_named_campaign_with_changed_hash_is_tampering_not_fallthrough`
- `test_buildcache_v2.py::test_v2_ccbench_path_is_not_cache_preimage_when_src_token_is_identical`
- `test_campaign.py::test_loop_probe_error_is_retryable_after_recovery`
- `test_p3_s4_loop.py::test_make_critic_digest_reflux_off_drops_red_section`
- `test_s6_sort_sweep.py::test_public_sweep_fresh_reject_then_next_candidate_resumes`
- `test_s8a_trigger_sweep.py::test_public_sweep_fresh_reject_then_next_candidate_resumes`
- `test_t126_qualification_artifacts.py::test_m2_normal_formal_campaign_remains_accepted`

先行2回の指定範囲は `test_artifact_admission.py` 単独、および `test_artifact_admission.py`＋`test_buildcache_v2.py` でした。いずれも0件です。

通過した静的検査:

- 変更Python全ファイルの`python3 -m py_compile`
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

pytest全範囲、フルスイート、build、campaign実走、provenance履歴監査は未実行です。greenは主張しません。

## 直さずに報告した項目

裁定§1-B(7)ではpolicyがcampaign identityに加わるため、次の旧ID期待は現契約と衝突します。しかし§1-Eの変更許可列挙外なので期待値を元のまま残しました。

- `test_s8a_trigger_sweep.py::test_default_off_campaign_ids_remain_historical_values`  
  旧期待は [test_s8a_trigger_sweep.py:232](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/tests/test_s8a_trigger_sweep.py:232)。policy-aware IDはbalanced=`cb953bfa`、write-heavy=`e46e0904`。
- `test_autonomous_trial_completeness.py::test_campaign_identity_is_pinned_without_producer_helper_oracle`  
  旧期待`948f4c43`は [test_autonomous_trial_completeness.py:1295](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f3/orchestrator/tests/test_autonomous_trial_completeness.py:1295) に残置。policy-aware fixture IDは`623e929a`。

所有外ファイルを必要とする追加修正はありませんでした。

## 総括

1. policy、4 identity面、attempt topology、validated consumerをcaller側で追随させ、gateは緩めていません。
2. Layer3はv3発行と凍結v2読み取りを両立し、overlayの「新成果物はpositive receipt必須」「歴史成果物は一括拒否しない」を維持しました。
3. 80件中78件は失敗原因を静的に解消、2件は裁定§1-E外の旧ID期待として未変更です。計算ノード障害により、残存する動的な赤は未確定です。