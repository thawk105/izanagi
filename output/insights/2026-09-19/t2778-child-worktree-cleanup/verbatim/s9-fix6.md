## 総括

指定の2ファイルのみ修正しました。

- reflog の SHA が pin から到達可能、または primary store に実在すれば受理。
- 直接呼出しで全7 parameter が成功。既存 `[reflog]` は rc20 を維持。
- 旧規則の反実仮想では `[default-branch-reflog]` が `backup-precheck`／rc20。検証後は修正规則へ復元済み。
- `git diff --check` 成功。

commit・報告ファイルは作成していません。