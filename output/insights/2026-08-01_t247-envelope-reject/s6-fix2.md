## 総括

### (a) G1 / G2 対応

| 所見 | 状態 | 対応 |
|---|---|---|
| G1 | closed（静的確認済み、pytest 未実測） | 数値 7 key の equal-float 負例を submit/job 双方へ追加。単層証拠と Bash mapping に遮蔽される両層証拠を別テストへ分離 |
| G2 | closed（静的確認済み、pytest 未実測） | `0o755` 完全一致を owner executable bit の検査へ緩和。source/生成先 mode の完全一致 assert は維持 |
| regressed | なし | near-float、bool、`walltime=10`、F5 を含む既存負例・拒否条件は削除していない |

### (b) 編集箇所

今回の 2 巡目で編集したのはテスト 1 ファイルだけです。

- [test_t126_pegasus_tools.py:829](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:829): Git executable bit 検査と生成先 mode 比較
- [同:3084](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:3084): submit 単層 equal-float
- [同:3114](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:3114): submit 両層 equal-float
- [同:3138](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:3138): submit 過剰決定の診断 pin
- [同:4036](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:4036): job 単層 equal-float
- [同:4058](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:4058): job 両層 equal-float
- [同:4079](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:4079): job 過剰決定の診断 pin

production script、`contract.py`、policy JSON、docs は今回変更していません。commit もしていません。

### (c) 新設・更新テスト

- `test_submit_rejects_each_single_layer_equal_float_type_drift`
- `test_submit_rejects_each_mapping_masked_equal_float_type_drift`
- `test_submit_rejects_overdetermined_reservation_policy_type_drift`
- `test_job_rejects_each_single_layer_equal_float_type_drift`
- `test_job_rejects_each_mapping_masked_equal_float_type_drift`
- `test_job_rejects_overdetermined_reservation_policy_type_drift`

### (d) key × 層 × 拒否理由

| 側 | key / 負例 | 層 | 理由 | 型 guard 除去後の静的追跡 |
|---|---|---|---|---|
| submit | `member_cap_s=900.0` | 単層 | 単一理由 | scheduler 到達 |
| submit | `round_gap_s=1800.0` | 単層 | 単一理由 | scheduler 到達 |
| submit | `prologue_cap_s=900.0` | 単層 | 単一理由 | scheduler 到達 |
| submit | `attestation_cap_s=600.0` | 単層 | 単一理由 | scheduler 到達 |
| submit | `finalize_reserve_s=600.0` | 単層 | 単一理由 | scheduler 到達 |
| submit | `walltime_s=36000.0` | 両層 | 過剰決定（型＋mapping） | 型だけの除去では mapping が拒否。両層除去で scheduler 到達 |
| submit | `wmax_s=29100.0` | 両層 | 過剰決定（型＋mapping） | 型だけの除去では mapping が拒否。両層除去で scheduler 到達 |
| job | `member_cap_s=900.0` | 単層 | 単一理由 | downstream marker 到達 |
| job | `round_gap_s=1800.0` | 単層 | 単一理由 | downstream marker 到達 |
| job | `attestation_cap_s=600.0` | 単層 | 単一理由 | downstream marker 到達 |
| job | `finalize_reserve_s=600.0` | 単層 | 単一理由 | downstream marker 到達 |
| job | `walltime_s=36000.0` | 両層 | 過剰決定（型＋mapping） | 型だけの除去では mapping が拒否。両層除去で downstream 到達 |
| job | `wmax_s=29100.0` | 両層 | 過剰決定（型＋mapping） | 同上 |
| job | `prologue_cap_s=900.0` | 両層 | 過剰決定（型＋mapping） | 同上 |
| submit | `attestation_cap_s=600.0000000000001` | 単層扱い | 過剰決定（型・値・和） | 値／和が引き続き拒否 |
| submit | `round_gap_s=True` | 単層扱い | 過剰決定（型・値・和） | 値／和が引き続き拒否 |
| submit | `walltime=10` | 単層扱い・診断のみ | 過剰決定（型・値） | 値比較が拒否。semantic KILL には数えない |
| job | `attestation_cap_s=600.0000000000001` | 単層扱い | 過剰決定（型・値） | 値比較が引き続き拒否 |
| job | `round_gap_s=True` | 単層扱い | 過剰決定（型・値） | 値比較が引き続き拒否 |
| job | `walltime=10` | 単層扱い・診断のみ | 過剰決定（型・値） | 値比較が拒否。semantic KILL には数えない |

JSON round-trip で全 equal-float が `.0` を保持し、canonical 整数とは `==`、strict `int` とは不一致になることも確認しました。

### (e) 検査結果

成功した静的検査:

- `git diff --check`
- 両 production shell の `bash -n`
- 変更 Python 3 ファイルの `python3 -m py_compile`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- equal-float の JSON／値比較／mapping 到達性マイクロプローブ
- mode probe: `0700` は executable-bit guard を通過、`0600` は拒否

`tools/run_tests.py -rf` へ次の selector を渡しました。

- submit の新規 3 node
- job の新規 3 node
- `test_fr3_mutation_node_registry_is_exact_and_complete`

結果は `qstat -Q preflight rc=1`、runner rc=16 で投入前停止です。pytest 実走は 0 node、緑は主張しません。

### (f) 波及可能性

- `_attempt` を使う既存 fixture 全体。source と生成先の mode 完全一致は維持されるため、`copymode` no-op 変異の検出力は残る
- `_submit_fixture` と `_run_job_reservation_probe` の policy override 経路
- submit の scheduler 非到達、job の dependency marker 非到達を観測する subprocess 境界
- production の受理集合には今回変更なし
- scope 外 4 件、F5、他 7 readarray、term grace、重複 key 非対称には変更なし

### (g) 未了事項

- 焦点 pytest、test file 全体、変異 matrix、計算ノード全走は親による実測が必要
- G1 の単層／両層変異本走は未実施
- 親による焦点再レビュー、記録、commit が必要
- `git add`、commit、push は実行していません