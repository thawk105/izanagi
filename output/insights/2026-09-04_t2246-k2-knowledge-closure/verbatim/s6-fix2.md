## 所見の対応表

partial — 実装済み・未実走: [test_p3_s4_loop.py:6399](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/tests/test_p3_s4_loop.py:6399)

## 実装した変更

legacy flattened proposal の期待値へ `"justification": ""` を追加しました。完全一致比較は維持しており、検査を緩めていません。production は未変更です。

## 同型の確認

K2 wrapper など他の完全一致比較を確認しました。期待値には `justification` が既に明示されており、追加修正は不要でした。

## 未了・疑問

pytest は実走していません。親による実測待ちです。`git diff --check` は通過しました。

## 総括

対象テストの期待値を実際の `CoderProposal` の形へ揃えました。  
変更は 1 行のみで、完全一致比較を維持しています。  
commit は作成していません。