<!-- 可逆最小正規化 (可視文字不変): 原文 sha256 4651c10f024adf9fe893d4a3650bf4565faa8d6c6ef4b852b9377b48fd50e8db、1565 byte。行末の空白 (markdown の hard line break の 2 空白等) を 2 行 (行番号 10, 12) で除いた。復元法 = 原文は job dir の codex/ 配下の同名出力。 -->
## 実装と残件

指定の2ファイルを作成しました。走ごとの逐次保存、AB/BA交互実行、G2検出と discriminator 結論の別集計を実装しています。

**compute 実行には policy の不一致が残っています。** 指定の `tools/pegasus/policy.json` には `_load_policy` 必須の compiler digest／`mocc_trace` がありません。無断の policy 置換は行わず、runner は理由を `result.json` に保存して停止します。

## 総括

- 作成ファイル：
  - `probe/mocc-close-version-counter-gap.patch`：37行
    SHA256：`8a25bd0a5687437269c720cb34a4b26024a6f1f119adf1c16281d455b9ecaa1d`
  - `probe/t2774_probe.py`：524行
    SHA256：`ef668a7981477bc1431c3767824aecb47636dc525ce8796b919d47ea0a5b98e9`
- selftest 実走要約：`selftest: PASS 10/10 cases`
- patch dry-run：`checking file cc/mocc/transaction.cc`、rc=0。既存行の削除・変更なし、論理行番号の保持も確認。
- 構文確認・helper 7個の実在確認：PASS。
- 未実走：hydrate、checkout、build、benchmark、実 trace に対する verifier／discriminator、複数実験 block の集計、pytest。
- 所有外への変更：**無し**。Git status は上記2ファイルの untracked のみ。add／commit／stash／worktree コマンドは未実行。

追加の policy ロード確認は自動 hook に拒否されました。理由は `tools/pegasus/policy.json` を未登録 Pegasus 実行体として分類したためです。この確認は実走成功として数えていません。
