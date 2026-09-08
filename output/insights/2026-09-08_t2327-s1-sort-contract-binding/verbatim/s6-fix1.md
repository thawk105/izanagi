実装は完了し、commit は作成していません。

| 所見 | 状態 | 対応 |
|---|---|---|
| F-P1 | closed | 派生 pin を再計算値へ更新 |
| F-P2 | closed | `resolve_evidence` double を追加し、旧 `resolve` は呼び出し即失敗に変更 |
| F-P3 | closed | `PreparedCell` の契約 ID を `run_block` の evaluate kwargs へ条件付き転送。M7/M8 対応 |
| F-P4 | closed | 契約 ID を evidence 解決と build kwargs へ条件付き転送。M9/M10/M11 対応 |

partial / regressed はありません。

### 変更ファイル

| ファイル | 変更行数 |
|---|---:|
| [s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2327-fix1/orchestrator/campaign/s8b_oracle_driver.py:1735) | +5 / -0 |
| [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2327-fix1/orchestrator/campaign/s8b_floor_campaign.py:4380) | +10 / -0 |
| [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2327-fix1/orchestrator/tests/test_s8b_oracle_driver.py:2182) | +24 / -2 |
| [test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2327-fix1/orchestrator/tests/test_s8b_floor_campaign.py:184) | +33 / -4 |
| [test_s8b_oracle_manifest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2327-fix1/orchestrator/tests/test_s8b_oracle_manifest.py:61) | +1 / -1 |
| [test_sort_swo_oracle.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2327-fix1/orchestrator/tests/test_sort_swo_oracle.py:2687) | +8 / -1 |
| 合計 | +81 / -8 |

`PIN_GATE_SPEC_SHA256`:

- 旧: `63cd82787ebe361e4fc6c4335c542bf76ee10083f419fd0b47f09b97e3d64202`
- 新: `27ed67ab2f358725b9bf959a28fa79603dd4cf4ca470fd541a10a1b2ca7c59e0`
- `hashlib.sha256(PIN_GATE_SPEC_RAW).hexdigest()` との一致を確認済みです。

### 受理・拒否集合

F-P3 は、契約 ID 付き sort_best が同じ ID で evaluate され、backoff_fixed_best / stock_common には key を追加しません。既存の oracle REJECT・binding 不一致経路は変更していません。

F-P4 は、sort_best の evidence と build に同じ契約 ID を渡し、stock_common では両 kwargs に key がありません。既存の receipt 欠落・dependency binding 不備による拒否は変更していません。

### 検証

- `python3 -m py_compile` を変更した6ファイルへ実行: rc=0
- `git diff --check`: rc=0
- pin 再計算検査: `actual == literal` が `True`
- 対象4 pytest file: 指示された sandbox 制約に従い未実走です。実装済み・未実走で、親の login node 焦点走待ちです。

### 静的波及

- `run_block` の production caller: 同ファイル L2060。test caller は `test_s8b_oracle_driver.py` の L2599, 2623, 2845, 2940, 2982, 3363, 3781, 3840, 3870, 4830, 4905, 5418, 6147, 6195、および所有外 [test_s8b_binding_driftguards.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2327-fix1/orchestrator/tests/test_s8b_binding_driftguards.py:278)。
- `_build_cells_impl` の caller は `build_cells` L4720のみ。`build_cells` の production caller は同ファイル L7640, L7708。
- `build_cells` の test caller は `test_s8b_floor_campaign.py` の L2803, 2883, 3131, 3201, 3284, 3352, 3429, 3552, 5251, 5528, 5673, 5776, 5844, 5913, 5985, 6129, 14073。所有外は `test_s8b_materialization.py:655`、`test_s8b_predicate_build_proof.py:133`、`test_s8b_dependency_prefix_bridge.py:101,142`。
- 共有 fixture は `_fixture_source_evidence` と `_make_fake_build` の signature を新 kwarg に追随させました。consumer test は F-P2 の source materializer double を追随済みです。
- 位置引数 `PreparedCell` は全14件、すべて4引数です。`test_s1_direct_comparison.py`: 239, 545, 584, 619, 640, 718, 1846, 1960。`test_s8b_expected_materialization.py`: 384, 446, 480, 518, 573, 611。末尾 optional field のため位置引数対応への影響はありません。

## 総括

- F-P1〜F-P4 はすべて closed です。
- sort_best の契約 ID を oracle driver と floor consumer へそのまま転送しました。
- 非 sort 行の kwargs 集合と既存拒否経路は維持しています。
- 構文・差分・pin は検証済み、pytest は親の焦点走待ちです。