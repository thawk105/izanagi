## 呼び手の互換性

- repo 全体の静的参照は `build_cells` 23 呼出し、`_build_cells_impl` 1 呼出し。production は fresh/resume の 2 箇所だけで、残りはテストです。追加引数は keyword-only かつ既定値付きなので、既存テスト caller の呼出し構文は壊れません。
- `_build_cells_impl` の唯一の caller は [s8b_floor_campaign.py:4710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:4710) で、両引数を転送しています。
- production の `repo_root` は入口で `None` を許しますが、[s8b_floor_campaign.py:7313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:7313) で `ROOT` または `Path` に正規化されます。fresh の [同:7627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:7627) と resume の [同:7695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:7695) はどちらもその値を渡すため、production で `repo_root=None` が `build_cells` まで到達する経路はありません。
- Pegasus の `reservation_binding` は [同:7411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:7411) 以降で読み、submit receipt との一致を [同:7429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:7429) で検証してから同じ 2 呼出しへ渡しています。reservation 不要環境の `None` は新 helper が fail-closed にします。
- 所有外の直接 caller である materialization、dependency-prefix、predicate-proof の各テストは custom prepare 経路であり、新しい既定 staging 分岐に入りません。
- `_prepare_floor_oracle_dependency(Path, ...)` への変更も互換です。[s8b_oracle_n_pilot.py:822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_oracle_n_pilot.py:822) は `_canonical_floor_fetchcontent_base(None)` の戻り値を受け、[同:823](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_oracle_n_pilot.py:823) で必ず非 `None` の `Path` を dependency helper へ渡します。したがって signature 上の回帰はありません。ただし、これは n-pilot の既存 transport を修復するものではなく、呼出し形を温存しただけです。

## 取り残し consumer の選別

**解消済み**

| 段 3 の consumer | 判定 |
|---|---|
| Holdout claim | 解消済み。core は raw `fetchcontent_base_dir` を分類し、claim へ [s8b_floor_campaign.py:7879](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:7879) から渡します。新規既定 run の claim は意図どおり `[]` です。 |
| Claim-derived eligibility | 解消済み。fresh claim が一様に `[]` なら [s8b_holdout_admission.py:6164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_holdout_admission.py:6164) の再導出と一致します。部分 resume の混在だけは下記の未解消項目です。 |
| Process spawn inventory | 元の懸念は解消済み。copy は `shutil.copytree` で、新しい process site はありません。静的再計算でも process inventory は完全一致しました。ただし別の exact 行番号 consumer が壊れており、must-fix に記します。 |
| `s8b_oracle_n_pilot.py` | 解消済み、正確には新規回帰なし。非 `None` の Path を渡す既存形を維持しています。 |
| buildcache binding/digest | 解消済み。変更前の shell staging も変更後の driver staging も `source-dir` で、identity は [buildcache.py:2485](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/buildcache.py:2485) と [同:2527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/buildcache.py:2527) で同じ値になります。 |
| completion manifest/receipt | 解消済み。completion は [buildcache.py:2850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/buildcache.py:2850) の既存 dependency identity を記録し、staging 所有者の移動では値が変わりません。 |
| floor manifest/runtime projection | 解消済み。runtime base は private field に留まり、argv は [s8b_floor_campaign.py:4784](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:4784) で placeholder 化され、public projection からは除かれます。 |

**未解消**

| 段 3 の consumer | 判定 |
|---|---|
| Resume claim | 未解消、ただし裁定どおり機構追加は不要です。既存 claim の旧 seam は [s8b_holdout_admission.py:1656](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_holdout_admission.py:1656) で温存され、新規補完 claim は `[]` になるため、[同:6149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_holdout_admission.py:6149) が混在を拒否します。新しい `campaign_run_id` で再投入する記録が親に残っています。 |
| Checkpoint/liveness | 未解消だが裁定済みの診断退化です。checkpoint reader は stage を非空文字列として受けるだけで、exact stage whitelist はありません ([floor_job_checkpoint.py:683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/floor_job_checkpoint.py:683))。liveness は最後の stage をそのまま報告します ([floor_liveness.py:633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/floor_liveness.py:633))。構造破壊はありませんが、staging 失敗の表示は `floor-driver` に畳み込まれます。 |

新規 file はありません。`git status` 上の変更は既存 4 file だけなので、file 一覧検査への登録は不要です。

## 変更された既存期待値の判定

1. `test_real_floor_prepare_material_oracle_and_capability_series_when_configured`  
   **妥当**。空 base を prebuild が埋める旧期待から、検証済み 3 source-dir を事前 staging する契約へ移しています。source-dir argv も追加で検査しており、弱体化ではありません。

2. `test_floor_dependency_source_dir_reads_and_binds_payload_policy`  
   **妥当**。削除が認められた production `base-only` 分岐を期待し続けず、payload policy と 3 source-dir の束縛を検査しています。`_canonical_floor_fetchcontent_base(None)` 自体の coverage は別テストに残っています。

3. `test_floor_job_hardens_interpreter`  
   **妥当**。exact checkpoint stage 列から `fetchcontent-staging` だけを削除しており、裁定 §2-6 と一致します。

4. `test_floor_job_invokes_fixed_pilot_cli_without_bypass`  
   **妥当**。driver argv から `--fetchcontent-base-dir` の 2 token だけを除き、pilot 固定と protocol binding の主張は維持しています。

5. `test_floor_job_leaves_fetchcontent_staging_to_driver_default`  
   **妥当**。旧 shell staging の正期待を、shell に staging と transport seam が残っていないことの負期待へ置換しています。driver 側の正経路は別の新規 staging テスト群が担当します。

6. `test_floor_protocol_resolution_is_shared_by_all_consumers`  
   **妥当**。resolver と driver が共有する protocol path の主張は同じで、削除された 2 argv token の期待だけを改訂しています。

7. `test_production_floor_dependency_preflight_failure_persists_private_attempt[checkout]`  
   **妥当**。checkout diagnostic の基準を fixture の canonical `repo_root` に変え、新しい転送契約と一致させています。診断 code、origin、outcome の期待は弱めていません。

8. `test_core_passes_fetchcontent_base_dir_to_fresh_and_resume_build_cells`  
   **妥当、かつ実際に強化**。元の `fetchcontent_base_dir` assertion を残したまま、fresh/resume 両 callsite に `repo_root` と `reservation_binding` の exact name 転送を追加しています ([test_s8b_floor_campaign.py:7640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/tests/test_s8b_floor_campaign.py:7640))。別主張へのすり替えではありません。これは静的配線の検査であり、binding の実検証は production code 側の別 gate が担います。

共有 fixture も問題ありません。`_receipt_validator_fragment` は削除済み staging block の直前ではなく `source-identity` までを切るようになっただけで、receipt validator の範囲は変わっていません。`_driver_tail` から除いた `FETCHCONTENT_STAGING` は現 tail から参照されず、これを使う protocol、driver rc、result writer 各テストの意味も変わりません。

分類結果は **妥当 8、弱体化 0、すり替え 0** です。

## must-fix

1. **real: benchmark build-sink の exact 行番号 ledger が stale です。**  
   [test_ccbench_spawn_sites.py:853](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/tests/test_ccbench_spawn_sites.py:853) は `build_cells.invoke_build=4543` と `main=8457` を固定していますが、現在の実 sink は [s8b_floor_campaign.py:4705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:4705) と [同:8625](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/campaign/s8b_floor_campaign.py:8625) です。[test_ccbench_spawn_sites.py:2647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/tests/test_ccbench_spawn_sites.py:2647) の exact match は両方 0 件になります。新しい process site はなく、行番号 ledger だけの更新です。  
   成果物影響: `test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink` が赤になり、受入全走の受理集合が green にならないため、このままでは wave を受入済みにできません。

**疑い**: 追加なし。

## 直すべきだが must-fix でない

- **real**: 部分 claim resume と liveness 診断退化の worklog/decisions 記録が未完です。[s5-author.md:87](/work/1/SFC/tanab/dev-wave-jobs/t2262-floor-staged-transport/s5-author.md:87) のとおり親作業です。生きた既存 claim が無いという裁定のため、コード must-fix ではありません。
- **real**: shell test の改名前 nodeid は [acceptance_duration_ledger.json:11355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/tests/acceptance_duration_ledger.json:11355) に孤児として残り、新 nodeid [test_pegasus_floor_tools.py:2589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/tests/test_pegasus_floor_tools.py:2589) は未計測です。これは「可能性」ではなく確定です。
- source-dir へ改名したテストは旧 nodeid も台帳に無く、孤児は増やしていませんが、新 nodeid は同様に未計測です。
- 台帳 schema 検査は型、有限値、`nodeid_count` だけを要求し、現 collection との完全一致を要求しません ([test_update_acceptance_duration_ledger.py:306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport/orchestrator/tests/test_update_acceptance_duration_ledger.py:306))。新 nodeid は acceptance scheduling で unknown cost として扱われるだけなので、受理集合や certified 値は変わりません。実測値を得た後の通常台帳更新で十分です。

## 実装子の報告との食い違い

- [s5-author.md:81](/work/1/SFC/tanab/dev-wave-jobs/t2262-floor-staged-transport/s5-author.md:81) は spawn inventory consumer を「未実走」とだけ報告しています。未実走という事実は正しい一方、exact build-sink 行番号の不一致は静的に確定でき、単なる未確認事項ではありません。
- [s5-author.md:82](/work/1/SFC/tanab/dev-wave-jobs/t2262-floor-staged-transport/s5-author.md:82) の「旧 ledger entry が残り、新 nodeid が未計測扱いになる可能性」は不正確です。旧 entry の残存と新 entry の欠落はいずれも現物上確定しています。
- 「production subprocess 起動点が不変」は正しいです。食い違っているのは process inventory 自体ではなく、同じ外部テストにある build-sink の exact 行番号 ledger です。
- それ以外の 4 file 限定、n-pilot の非 `None` 呼出し、共有 fixture 改訂、pytest 未実走という報告はコードと一致します。

## scope 外候補

- `s8b_oracle_n_pilot` の FetchContent transport 自体の修復。
- 部分 claim の移行、backfill 機構。現裁定どおり新しい `campaign_run_id` での再投入を優先します。
- staging failure を再び専用 liveness 診断へ分離する変更。
- official permit gate、CLI official 拒否、shell の pilot 固定の解除。
- 新しい一般 gate、台帳、file 一覧検査の新設は不要です。

## 総括

`build_cells` と `_build_cells_impl` の既存 caller は互換で、production の `repo_root=None` 経路も閉じています。  
oracle n-pilot は非 `None` Path を渡すため signature 回帰はありませんが、既存 transport の修復ではありません。  
変更された既存期待値 8 件はすべて妥当で、弱体化や主張のすり替えはありません。  
must-fix は `test_ccbench_spawn_sites.py` の stale な exact 行番号 2 件です。  
部分 resume、liveness 診断、duration ledger は既知または非受理影響の残件です。  
新規 file はなく、本レビューでは pytest を再実走していません。