## probe の仕様と実走

作成: [tools/t2637_onerror_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2637-impl/tools/t2637_onerror_probe.py)（149行）。

`--selftest` を実走し、rc=0。workers=4 で EACCES 1件、記録件数と監査の失敗件数の一致を確認しました。

```text
PROBE ok recorded=1 reported=1
```

進捗は stderr、診断結果は指定先の JSON に出力します。

## 挙動不変の根拠

- `record_error` は元 method を呼んでから、lock 付きで記録します。
- `Path.lstat` は元の戻り値を返し、OSError は記録後にそのまま再送出します。
- wrapper は計数を変更しません。終了時には monkeypatch と環境変数を復元します。

`Path.lstat` の観測範囲は候補以外も含みます。未記録の失敗などによる件数差は `mismatch` で確認できます。

## 総括

probe 1ファイルを作成し、tmp 内の selftest に合格しました。実根の走査、監査 tool の編集、git add / commit は行っていません。
