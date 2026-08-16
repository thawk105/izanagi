## 現行挙動

変更前は、submodule manifest に未初期化行があっても、他の検査理由がなければ snapshot を受理していました。

## 実装

- [tools/codex_reasoning_ab.py:1693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1223-snapshot-submodule-gate/tools/codex_reasoning_ab.py:1693)
  - manifest 全行を無条件で走査。
  - `initialization != "initialized"` ごとに path 付き reason を追加。
  - `expected`、`enforce_closure`、`_snapshot_spec`、oracle key 集合は変更していません。
- [test_codex_reasoning_ab.py:2004](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1223-snapshot-submodule-gate/orchestrator/tests/test_codex_reasoning_ab.py:2004)
  - gitlink 直接登録による合成 snapshot helper と独自 spec helper を追加。
  - 既存 fixture・既存テストは変更していません。

## 追加テスト

- `test_verify_snapshot_submodule_gate_rejects_custom_spec_without_closure`
  - N1: closure 無効時の迂回を防止。
- `test_verify_snapshot_submodule_gate_rejects_custom_spec_with_closure`
  - N2: production 相当の closure 有効側を固定。
- `test_verify_snapshot_submodule_gate_checks_every_manifest_row`
  - N3: manifest 先頭行だけを見る退行を検出。
- `test_verify_snapshot_submodule_gate_rejects_default_spec_path`
  - N4: `spec=` を渡さない経路を monkeypatch で固定。理由を docstring に明記。
- `test_verify_snapshot_submodule_gate_accepts_all_initialized`
  - P1: 全初期化済みを受理し、oracle key 集合を exact 固定。
- `test_verify_snapshot_submodule_gate_accepts_empty_manifest`
  - P2: submodule なしを受理。

## 実走結果

実装済み・pytest 未実走です。

実行を試みた範囲:

`python3 tools/run_tests.py orchestrator/tests/test_codex_reasoning_ab.py -k verify_snapshot_submodule_gate -rf`

- rc: `16`
- 実走 node: `0/6`
- 理由: Pegasus dispatch の `qstat -Q` preflight が rc=1。
- 直接 pytest には迂回していません。
- 静的検査: Python AST parse rc=0、`git diff --check` rc=0。
- meta-test を確認しましたが、新規 node は `benchmark_snapshots` 非依存なので `REAL_REPO_SERIAL_NODES` や growth hold 登録の対象外です。

## 波及可能性

- 所有外 caller の `_finish_snapshot_case`、`_supervise_one` の前後検査、`supervise_pair`、`_replay_manifest`、`verify-snapshot` CLI は、全深度の未初期化 submodule を新たに拒否します。
- `benchmark_snapshots` 自体は変更していません。生成 snapshot に未初期化 submodule があれば、その共有 fixture consumer は意図どおり早期拒否されます。
- `_git_closure_reasons` を直接検査する既存 manifest テストの契約は変更していません。
- oracle key は不変なので、受理される snapshot の schedule 突合、replay、`manifest_sha256` に新 field は入りません。
- docs・commit・指定外ファイルには触れていません。

## 総括

未初期化 submodule の fail-open を verifier 層で閉じました。  
closure 設定や caller spec から緩和できない無条件 gate です。  
負例 4・正例 2を合成 repo で追加しました。  
作業木の変更は指定された 2 ファイルだけです。  
限定 pytest は実行基盤の preflight 障害により未実走です。