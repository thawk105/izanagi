# 修正内容

所有する `loop.py` と `test_campaign.py` のみ変更しました。docs 編集、`git add`、`git commit` は行っていません。

- validator を含む引数を明示 keyword parameter 化し、`pre_write_validator(identity)` として呼び出します。
- 初回認可を例外変換の `try` 外へ移しました。`ClaimError` は直接透過し、再利用検査だけ従来の変換を維持します。
- 未発行・同型コピーの負例を、claim が存在しない状態での「`ExecutionGuardError`・claim 取得 0 回」に変更しました。copy／deepcopy／pickle の拒否検査も維持しています。
- 初回例外の同一オブジェクト透過と、失敗後の再試行・再利用を検査するテストを追加しました。

今回の fix によって新たに受理する入力はありません。今回の fix によって新たに拒否する入力もありません。

維持する正例は、発行済み・未 close・同 PID・全束縛一致の session による 2 回の認可で、claim 取得が 1 回となるケースです。

# M4' と重複比較

発行確認は `.get(session)` の結果 `entry` を検査してから展開する形にしました。M4' は次の拒否部分を、

```python
if entry is None:
    raise execution_guard.ExecutionGuardError("authorization session is unissued or closed")
```

次へ置換することで、未発行の同型個体を初回認可・新規束縛まで通す構造です。

```python
if entry is None:
    entry = (os.getpid(), None)
    _AUTHORIZATION_SESSIONS[session] = entry
```

これは変異の定義であり、製品コードには導入していません。KILLED の実測は未実施です。

削除した比較は次の 2 点です。

- 保存 record の PID：初回 claim 作成時の一致と発行 PID 検査に含意されます。
- 保存 record の protocol digest：初回保存時の一致と現在の digest／保存 binding 比較に含意されます。

実ファイル読取りと record 全体比較、process starttime 検査は維持しました。

# 確認結果

`py_compile`、`git diff --check`、NFC 確認は成功しました。AST 比較で S 無しの認可本体と既存テストの不変も確認しました。

作業木を向け直した probe 全体は、未 commit の `loop.py` に対する **`contract-loader-drift`** で停止しました。追加の静的部分の確認では、生成経路 26 関数の unresolved issues は 0 件でした。

この作業木には `_run_stock_cli_step` が存在しないため、その逆到達集合への包含は確認できません。親の A2 統合・commit 後に probe 全体の再確認が必要です。

## 総括

**実装済み・未実走です。** pytest・変異検査は実行していません。

赤 (a) の原因となる局所 callable は解消し、静的解析は成功しましたが、probe 全体の成功は未確認です。初回例外の透過、M4' が新規取得・束縛まで到達できる構造、取得 0 回の負例を実装しました。重複する保存 record の PID・digest 比較を削除しました。