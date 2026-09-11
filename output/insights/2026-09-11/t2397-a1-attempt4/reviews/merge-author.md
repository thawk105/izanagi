## 総括

実装済み・未実走です。[対象ファイル](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2397-merge-author/orchestrator/tests/test_ccbench_spawn_sites.py) の2箇所を `apply_patch` で7268→7374に更新しました。

- 根拠：wave `6a8696d9` の `run_measurement` 内の `run_campaign` 呼出しが7374行であることを、ソースとASTで確認。
- main `d42eca79` との差分は指定2箇所のみ。T2520等、owner/kind/scope/reason、全負例の保持をバイト比較で確認。`git diff --check` 通過。
- 波及範囲：A1呼出し位置と、それに束縛する台帳・consumer test。共有fixture・所有外callerは未変更。
- テストは未実走。A1本体未統合による当該行番号束縛の期待赤があり得ます。親treeで統合後の検査が必要です。
- add・commit・merge・他ファイル編集は行っていません。

ファイル SHA-256：
`b38fe910fcac976687ba04e3b632539e33cc6b42ad5bce7ed10404368cacfbee`