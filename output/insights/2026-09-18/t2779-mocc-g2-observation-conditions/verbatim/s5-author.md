## 検証

`defines` に固定列 7 key の整数文字列 / `ON` / `OFF` 値を与えた arm は受理され、その key だけが置換されます。
それ以外の key・値形式・型は `validate_arms` が `ValueError` で拒否します。

正例: `{"CCBENCH_BACK_OFF": "1"}`。

構文確認・JSON 読込みはともに rc=0。selftest は指定の受理 1 例・拒否 7 例、および `[]`・`None` の拒否を含めて成功しました。

## 総括

作成したファイルは次の 2 件だけで、両方 untracked のままです。

| ファイル | 行数 | SHA-256 |
|---|---:|---|
| `probe/t2779_probe.py` | 785 | `7907a545b719845d69b36590cc90cff6b28c242d3b7140d9c52b4a838798df99` |
| `probe/arms-t2779.json` | 35 | `4f6aaf5a172eb8eb737bd0ec6e2fcc52e92b5dce2691803f65d8f34e327ebb56` |

実走: `python3.10 -B probe/t2779_probe.py selftest`、rc=0。要約行は逐語で以下です。

```text
selftest: PASS 21/21 cases
```

v4 との差分は **95 行追加・14 行削除**（`diff -u` 全出力 202 行）。定数を追加し、`validate_defines` を新設、`validate_arms`・`configure_argv`・`run`・`selftest` を変更しました。差分は指定 (a)〜(f) 内で、変更禁止部分は維持しています。

未実走: pytest、compute、build、smoke、本走。

所有外への波及: **無し**。tracked file の変更、git add / commit / stash / worktree の実行はありません。
