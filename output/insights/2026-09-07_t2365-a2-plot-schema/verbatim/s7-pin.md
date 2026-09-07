## 総括

新 attempt `t2364-20260907b` の pin を追加しました。  
certification SHA-256: `e74d0f870497941b95ac4d1e244634188813e249f2821d571178e4854a3ed671`  
raw manifest SHA-256: `b23ee2ee6ff36d2377da80c2cf4eccc925bae9c3d89aab8a6a8543edfe9ae319`  
現物からの計算結果は親の測定値と一致しています。既存凍結 entry は変更していません。

## 変更点

- [tools/plotting/plot_a2_certification.py:51](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-pin/tools/plotting/plot_a2_certification.py:51): `CANONICAL_SHA256` に新版 entry を追加。
- [orchestrator/tests/test_plot_a2_certification.py:969](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-pin/orchestrator/tests/test_plot_a2_certification.py:969): pin 表が厳密に 2 件であることと、新版 hash 組を検査。

## 実走した検査

- `sha256sum`: 射影された両成果物について期待値との一致を確認。
- 自走 harness（`PYTHONPATH=.`）: 両ファイルの構文と厳密な 2-entry pin 表を確認 — PASS。
- 更新対象 test 関数を pytest runner 非経由で直接実行 — PASS。
- `git diff --check` — PASS。
- 最初の複合検査コマンドは防護 hook に拒否されたため、分割して再実行済み。

## 所有外への波及

リポジトリ内の変更は指定された 2 ファイルだけです。凍結成果物、docs、既存凍結 hash の期待値には変更ありません。`git add`・commit も行っていません。

## 未了・申し送り

通常の pytest は指定された sandbox 制約により未実走です。また、新成果物がこの worktree の repo 相対 path に存在しないため、新 entry を使う end-to-end 経路は実装済み・未実走です。親での実走をお願いします。