指定された[test file](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/orchestrator/tests/test_p3_b4_closed_critic.py)だけを編集しました。production、既存テスト、既存 nodeid は変更していません。構文解析と `git diff --check` は成功しています。

## 総括

追加 nodeid:

- `orchestrator/tests/test_p3_b4_closed_critic.py::test_r1_terminal_pair_revalidation_rejects_raw_envelope_byte_tamper`
  - 改竄前の正例を確認後、disk 上の envelope bytes を変更します。
  - raw envelope hash 比較行を `if False:` にする変異で赤になります。
  - 例外文言 `raw envelope hash does not match its bytes` を固定しています。

- `orchestrator/tests/test_p3_b4_closed_critic.py::test_pair_gate_rejects_certified_and_test_only_evidence_class_mix`
  - fake runner で certified pair と test-only pair の正例を確認後、両 class の混成を拒否します。
  - evidence class 比較行を `if False:` にする変異で赤になります。
  - 例外文言 `pair receipts have different evidence_class values` を固定しています。

既存 nodeid の改名・削除は 0 件です。pytest は指示どおり未実走であり、状態は「実装済み・未実走」です。commit、実 CLI、ネットワーク取得は行っていません。