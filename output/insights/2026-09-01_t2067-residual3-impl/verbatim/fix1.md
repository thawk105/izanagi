## 所見対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| F1 | **partial** — root cause 修正・診断再現済み、正式 nodeid 未実走 | [s8b_ratified_freeze.py:3608](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/campaign/s8b_ratified_freeze.py:3608)、[test_s8b_ratified_verify.py:889](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/tests/test_s8b_ratified_verify.py:889) |
| F2 | **partial** — fixture と例外理由を修正、正式 nodeid 未実走 | [test_s8c_result_judge.py:1711](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/tests/test_s8c_result_judge.py:1711) |
| F3 | **partial** — domain-level の受理反転を追加・診断確認済み、正式 nodeid 未実走 | [test_s8b_ratified_verify.py:1544](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/tests/test_s8b_ratified_verify.py:1544) |
| F4 | **partial** — loader/selection 境界を分離、正式 nodeid 未実走 | [s8c_result_judge.py:2075](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/campaign/s8c_result_judge.py:2075)、[test_s8c_result_judge.py:1630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/tests/test_s8c_result_judge.py:1630) |

## 実装した内容

- `assert_g1_floor_selection_identity(ratified: RatifiedFreeze, root=ROOT) -> None`

  - 禁止署名: `selected_path_info["proto8"] != canonical_protocol_sha256(protocol)[:8]`
    → `floor-selection-unverifiable / selection-path-proto8`
  - 禁止署名: `ratified.document["env_tag"] != selected_path_info["env_tag"]` または `selected_path_info["env_tag"] != protocol["env_tag"]`
    → `floor-selection-unverifiable / selection-env-chain`
  - いずれも `_hf._assert_floor_selection_identity` より前で検査。
  - certificate 検査引数は渡していません。
  - 通る正例: [test_g1_selection_helper_accepts_valid_selection:952](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/tests/test_s8b_ratified_verify.py:952)。

- `_RatifiedFloorSelectionError.__init__(self, reason: str) -> None` と `_load_selection_checked_ratified_floor() -> Any`

  - selection assertion の `RatifiedFreezeError` だけを内部例外へ変換。
  - loader 自身の失敗は従来の汎用表示へ流します。
  - `verify_floor_bytes(...)` と `_validate_verified_floor(evidence: Any)` の捕捉境界を追随。

- テスト追加・変更:

  - `test_g1_selection_helper_rejects_foreign_env_namespace(...)`
  - `test_g1_selection_helper_rejects_protocol_hash_prefix_mismatch(...)`
  - `test_g1_only_selection_helper_skips_earlier_eligible_run_for_g2(...)`
  - `test_publish_requires_current_ratified_floor_receipt(...)`
  - `test_floor_verification_preserves_loader_failure(...)`
  - `test_publish_preserves_current_floor_loader_failure(...)`

新 API の reason 集合、g2 の no-op、歴史再検証経路は変更していません。

## F1 の裏取り

修正前に production-emitter fixture を使い、loader が受理する g1 を構築しました。

- generation/protocol env: `linux-baremetal`
- `floor_source.path`: `output/env/foreign-env/.../20260718T120000Z-75b01122/result.json`
- 真の namespace の earlier run: `output/env/linux-baremetal/.../20260718T115959Z-75b01122/result.json`
- earlier の導出適格性 stub: `True`

修正前の結果は `assert_g1_floor_selection_identity(...) == None`、導出呼出しは `[]` でした。つまり foreign namespace だけを探索し、真の earlier run を除外していました。

修正後の同型診断は以下です。

- foreign env: `floor-selection-unverifiable / selection-env-chain`
- proto8 不一致: `floor-selection-unverifiable / selection-path-proto8`

## 受理・拒否対比

| 入力の型 | fix 前 | fix 後 | 変化 |
|---|---|---|---|
| foreign env を指す g1＋真の namespace に earlier eligible | 受理 | `floor-selection-unverifiable` | 狭める |
| protocol hash と異なる proto8 の g1 | 束縛なし | `floor-selection-unverifiable` | 狭める |
| env/proto8 が一致する valid g1 | 受理 | 受理 | 不変 |
| earlier eligible を持つ g2 | no-op で受理 | no-op で受理 | 不変 |
| 上記 g2 で g1 分岐を無条件実行する変異 | 自然な domain 拒否を固定できず | `floor-selection-rule-mismatch` | 変異時のみ反転 |
| loader 自身の失敗 | 汎用 loader 表示 | 同じ汎用表示 | 不変 |
| selection mismatch | selection reason 付き拒否 | 同じ | 不変 |
| foreign floor receipt | current-binding mismatch で拒否 | 同じ。test が理由まで固定 | 不変 |

## 実走結果

正式 pytest の緑はありません。次の12 nodeidを `tools/run_tests.py` で投入しましたが、`qstat -Q` が `EACCTAUTH` となり、`rc=16 / child_started=false` で停止しました。

- s8b: foreign-env、proto8、rule-mismatch、valid-g1、既存g2 sentinel、新g2 mutation の6 nodeid
- s8c: selection mismatch、verify loader failure、current receipt、publish mismatch、publish loader failure、valid publish の6 nodeid

`queue_state` は ENA/STS 観測不能、login headroom は予約台帳を安全に更新できず dispatch 判定でした。規律を迂回した pytest 直起動はしていません。

実施済みの非pytest検査:

- 4ファイル AST parse: 成功
- `git diff --check`: 成功
- F1 post-fix crafted input 診断: 期待 reason/cause
- F3 crafted input 診断: baseline `None`、無条件分岐相当で `floor-selection-rule-mismatch`

## 波及の静的列挙

`s8b_ratified_freeze` を名指す `orchestrator/tests/` 内ファイルは20本です。うち support 2本:

- `calibration_freeze_authority_execution.py`
- `real_repo_ratified_memo.py`

test 18本:

- `test_autonomous_trial_completeness.py`
- `test_ccbench_spawn_sites.py`
- `test_official_perf_closure.py`
- `test_p3_autonomous_workload_trial.py`
- `test_s8b_approved.py`
- `test_s8b_binding_driftguards.py`
- `test_s8b_floor_stats.py`
- `test_s8b_holdout_admission.py`
- `test_s8b_oracle_driver.py`
- `test_s8b_oracle_manifest.py`
- `test_s8b_oracle_report.py`
- `test_s8b_protocol_builder.py`
- `test_s8b_ratified_freeze.py`
- `test_s8b_ratified_verify.py`
- `test_s8b_verdict.py`
- `test_s8c_acceptance_receipt_v2.py`
- `test_s8c_preregistration_invariant.py`
- `test_s8c_preregistration_predicates.py`

`s8c_result_judge` を名指すものは3本です。

- `test_s8c_preregistration_invariant.py`
- `test_s8c_preregistration_predicates.py`
- `test_s8c_result_judge.py`

## 残した赤・未了

既知の赤はありません。

未了は、Pegasus infrastructure により child が起動しなかった正式12 nodeidと、上記consumer test群の実走です。そのためF1〜F4を `closed` とは申告していません。

## 総括

F1 の namespace/proto8 回避、F2 の偽緑、F3 の変異帰属、F4 の診断境界を実装・テスト上で修正しました。  
受理集合はg1の不正入力についてのみ狭まり、valid g1・g2・loader診断は維持しています。  
変更は指定された4ファイルだけで、staged変更・docs変更・commitはありません。  
正式pytestは infrastructure blocker により未実走のため、全所見を `partial` として引き渡します。