## 総括

指定の2ファイルだけを修正しました。

- submodule の変換属性検査を除去。他の検査と superproject の検査は維持。
- fixture の source に `.gitattributes` を commit してから submodule を追加する形へ変更。期待値は変更なし。

直接呼出しで6 parameter と既存 clean-filter 2 parameter が成功しました。メモリ上で検査を戻す反実仮想では、`[clean]` が rc=20／`backup-precheck` で失敗し、復元済みです。

`git diff --check` 成功。commit・報告ファイルの作成はしていません。