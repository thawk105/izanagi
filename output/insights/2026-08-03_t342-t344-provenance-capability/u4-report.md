実装単位 U4 を working tree に反映しました。docs・`output/` は未編集、`git add` / commit / branch 操作はしておらず、staging も空です。

## 変更前の挙動

- Layer 3: admission 検査なしで lock/WAL を展開し、実 S8a campaign を v2 report として生成していた。
- critic: 6 種の raw-WAL loader が `CampaignLayout` を直接受け取っていた。
- replay: prefix 発見後の campaign directory を未検証で読んでいた。
- S6/S8a sweep: `COMMIT` の存在だけで `certified=True` にしていた。
- autonomous producer: policy を cfg に含めず ID を複数回導出し、iteration 間の共通 run context、build 後の Layer 3/admission 検査、no-build admission 記録がなかった。
- completeness: build report の positive admission decision を要求せず、fresh Layer 3 経路も admission-aware ではなかった。
- 歴史 campaign: overlay による個別拒否も、post-policy／pre-policy の明示的な境界もなかった。

## 実装結果

共通 validator は [artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u4/orchestrator/campaign/artifact_admission.py:295) に実装しました。

- overlay の既知 ID/path は SHA・件数まで完全一致させ、不一致を改変エラーにして fall-through を禁止。
- post-policy campaign は policy、attempt topology、receipt SHA、WAL genome/src-token と source evidence、lock commit を照合。
- decision receipt に policy、attempt receipt 群、lock/WAL SHA、validator identity/SHA、overlay ledger SHA/key を格納。
- critic の全 loader は [digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u4/orchestrator/critic/digest.py:194) の `AdmittedCampaign` だけを受け付ける。
- Layer 3 は展開前に validator を呼び、v3 schema と `admission_decision` を発行する一方、v2 schema reader は維持。[layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u4/orchestrator/campaign/layer3_report.py:359)、[layer3_schema.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u4/orchestrator/campaign/layer3_schema.json:1)
- replay prefix loader、S6/S8a 集計も validated view 経由。[replay.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u4/orchestrator/campaign/replay.py:89)、[s6_sort_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u4/orchestrator/campaign/s6_sort_sweep.py:416)、[s8a_trigger_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u4/orchestrator/campaign/s8a_trigger_sweep.py:466)
- autonomous producer は policy bind 後に ID を一度だけ導出し、同一 context を全 iteration に渡す。build cell は report 保存前に Layer 3 chain を検査し、no-build は exact `{"admission_status":"not-applicable"}`。[p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u4/orchestrator/campaign/p3_autonomous_workload_trial.py:1228)
- completeness は decision と persisted/fresh Layer 3 chain を照合。[autonomous_trial_completeness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u4/orchestrator/campaign/autonomous_trial_completeness.py:848)

### 新旧 schema の線引き

- 歴史成果物を一括拒否しない分岐: [artifact_admission.py:350](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u4/orchestrator/campaign/artifact_admission.py:350)。lock の `search_config.build_admission` がない非掲載 campaign は `historical-pre-admission-schema`。
- 新 schema 以後の positive receipt 検査: [artifact_admission.py:370](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u4/orchestrator/campaign/artifact_admission.py:370)。policy と U2 attempt topology、source evidence を照合する。
- overlay 掲載物の改変／拒否: [artifact_admission.py:314](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u4/orchestrator/campaign/artifact_admission.py:314)。

## Overlay 台帳

台帳は [legacy_admission_overlay_v1.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u4/orchestrator/campaign/legacy_admission_overlay_v1.json:1) です。

- schema: `legacy-campaign-admission-overlay/v1`
- authority: `T-342+T-343+T-344/s4-ruling/1-C`
- kind: `deny-only-admission-overlay`
- created-from commit: `e0b9073ade90dc59578ad30fa8c8ffbe312b9b4e`
- input-set SHA: `c3b0d4f27b44cf264b7642a6efadfed07b2fc2605dfb777eec0362391589b436`
- 台帳 raw SHA: `d3a5d293a60bb2e87a04ca676b51adf6bba6f8ed3c2b61ac74cc384028fedf0b`
- record exact fields: `path`, `campaign_id`, `campaign_lock_sha256`, `wal_sha256`, `build_start_count`, `verification_status`, `admission_status`
- 全 record: `verification_status=historically-certified`、`admission_status=legacy-unclassified`

再計算値:

| campaign | lock SHA | WAL SHA | build_start |
|---|---|---|---:|
| `p3-s4-loop-s4-autonomous-0b53a387` | `0b53a3876589a61ae35b318237751015acebb3761e612e4374f9944ffca7f7c9` | `2163b794fa3b1fce4de76a1b69262cadfc095bd986225a7266d6eacb6210a611` | 3 |
| `p3-s5-sort-loop-s5-sort-autonomous-3be89e0d` | `3be89e0ddad8e8b2b37d35168c49affe7889ea580831973dc0d6d9706aaa4f97` | `b901f23a502e4d3843454de807ca01666c145ee7d9d424a957bb366ef3e793a5` | 1 |
| `p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5` | `3f72ecd58a6df4018d136bcbb8abb276114ba8d302c64aaf792c473ae4b1de0c` | `a539648d29afce9be036eba519b53f21fd1f8e1fb7bfe24549f4ec3ceac31ea3` | 2 |

実 WAL の receipt 件数はいずれも 0。`certified:true` は順に 3、2、4 件で、歴史的 verifier 判定を否定していません。

## 検査結果

pytest 実行済み nodeidはありません。Pegasus 規律に従い直接 pytest は実行せず、計算ノード dispatch を2回試しましたが、どちらも収集前に `qstat -Q preflight rc=1` で停止しました。

2回目に指定した nodeid:

- `test_artifact_admission.py::test_overlay_raw_sha_and_exact_membership_are_independently_pinned`
- `test_artifact_admission.py::test_overlay_named_campaign_with_changed_hash_is_tampering_not_fallthrough`
- `test_layer3_report.py::test_real_legacy_s8a_campaign_is_rejected`
- `test_critic.py::test_real_legacy_s4_critic_entry_is_rejected`
- `test_s6_sort_sweep.py::test_real_legacy_sort_campaign_cannot_be_certified_by_commit_only`
- `test_s8a_trigger_sweep.py::test_real_legacy_trigger_campaign_cannot_be_certified_by_commit_only`

結果はいずれも「実行 0 件」で、green は主張しません。

通過した静的検査:

- 全変更 Python ファイルの `python3 -m py_compile`
- 両 JSON の parse
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

フルスイート、変更テストファイル全体、build、campaign 実走、provenance 履歴監査は未実行です。

## 期待される赤と波及

裁定により意図して変わる旧期待値は、実 S8a campaign の Layer 3 render 成功期待だけです。現在は overlay 拒否を期待する試験へ置換しました。

U3 が未適用のため、次は静的に予想される cross-unit finding です。

- `p3_s4_loop_trigger_gating.drive_iteration()` はまだ `build_context` を受け取らない。
- `p3_s4_loop.py`、`p3_s4_loop_sort.py`、`p3_s4_red.py` は critic raw loader にまだ `CampaignLayout` を渡す。
- そのため `test_p3_s4_loop.py::test_make_critic_digest_reflux_off_drops_red_section`、sort の auditor rejection 3試験、trigger-gating の syntax rejection 2試験は U3 配線前なら `TypeError` が予想される。

この集合以外の赤は U4 回帰として扱うべきです。

所有外 caller／fixture の静的波及先:

- `orchestrator/campaign/p3_s4_loop.py`
- `orchestrator/campaign/p3_s4_loop_sort.py`
- `orchestrator/campaign/p3_s4_red.py`
- `orchestrator/campaign/p3_s4_loop_trigger_gating.py`
- `orchestrator/tests/test_p3_s4_loop_sort.py`
- `orchestrator/tests/test_p3_s4_loop_trigger_gating.py`

`backoff_sweep_report.py` は replay が返す validated view をそのまま利用できるため、裁定どおり追加 guard は入れていません。

## 総括

最重要の設計判断は次の3点です。

1. 歴史的 `certified` と T-316 admission を混同せず、overlay を deny-only の二次元台帳にした。
2. raw-WAL consumer ごとの任意 guard ではなく、一度だけ発行される validated view に収束させた。
3. post-policy artifact だけに positive receipt chain を要求し、非掲載の歴史成果物は一括拒否しなかった。

既知限界は、全歴史 artifact inventory が別 wave、immutable source snapshot による完全な ABA 遮断が scope 外、U3 caller 配線と計算ノード pytest が未完了である点です。