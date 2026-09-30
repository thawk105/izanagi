## 変更内容

[テストファイル](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u2/orchestrator/tests/test_verifier_gate_witness.py) の2つの parametrization に改行を含まない明示 ID を付け、`extra-q` を追加しました。既存の期待値は変更していません。[README](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u2/orchestrator/tests/README.md) の指定区間に、ファイル名を辞書順で allowlist 登録しました。

## 追加・改名した test node id の一覧 (完全な nodeid)

- `orchestrator/tests/test_verifier_gate_witness.py::test_gate_q_frame_m4[missing-q]`
- `orchestrator/tests/test_verifier_gate_witness.py::test_gate_q_frame_m4[dash-txid]`
- `orchestrator/tests/test_verifier_gate_witness.py::test_gate_q_frame_m4[wrong-txid]`
- `orchestrator/tests/test_verifier_gate_witness.py::test_gate_q_frame_m4[extra-q]`
- `orchestrator/tests/test_verifier_gate_witness.py::test_gate_format_fail_closed[bad-key]`
- `orchestrator/tests/test_verifier_gate_witness.py::test_gate_format_fail_closed[stamp-overflow]`
- `orchestrator/tests/test_verifier_gate_witness.py::test_gate_format_fail_closed[r-missing-observed]`
- `orchestrator/tests/test_verifier_gate_witness.py::test_gate_format_fail_closed[unknown-tag]`

## 自己確認

実装を読み、`extra-q` は枠数を超えた Q として `gate_d1c` を **1 件**加算すると確認しました。`py_compile` と `git diff --check` は成功。差分は追加10行・削除3行です。指示どおり pytest は実行していません。

## 総括

指定された2ファイルの範囲で修正を完了しました。実走結果は親の確認待ちです。