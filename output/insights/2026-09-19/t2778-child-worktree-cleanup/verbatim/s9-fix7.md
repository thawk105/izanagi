## 総括

指定の2ファイルだけを修正しました。main・manifest branchから到達できない履歴も、任意のlocal branchが保持していれば受理します。

直接呼出しで確認済みです。

- 新正例：`removed`、証拠ファイルと両branchの残存を確認。
- 既存負例：到達不能履歴を引き続きrc20で拒否。
- 反実仮想：追加分岐を外すと新正例がintegration／rc20で拒否。検証後に復元済み。
- allowlistの完全一致・不正形拒否、`git diff --check`：成功。

commit・報告ファイルは作成していません。