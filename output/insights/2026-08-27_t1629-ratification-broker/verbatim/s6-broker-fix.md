指定された 2 ファイルだけを修正しました。

- [ratification_broker.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/tools/ratification_broker.py:77)
- [test_ratification_broker.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/test_ratification_broker.py:572)

| 所見 | 判定 | 対応 |
|---|---|---|
| A3 | closed | remote Git を絶対パス、環境 allowlist、replace refs・commit graph・fsmonitor 無効化で統一 |
| A4 | closed | schema・domain・field・canonical encoder を検証子から参照。40桁以外の HEAD を署名前に拒否 |
| A5 | closed | 秘密鍵を `O_NOFOLLOW` で一度だけ開き、同一 fd に固定。生成署名を捕捉済み公開鍵で自己検証 |
| A7 | closed | 初回も全 closure bytes を表示。LF以外の危険な bytes、C1、bidi、backslash を単射な ASCII 表現へ変換 |
| A9 | closed | hardened bundle snapshot の reachable 全史と、prospective commit を検証子の `_committed_receipts` で検査 |
| A10 broker分 | closed | 恒真 assert と tuple 一致に従属する path type 検査を削除 |
| B4 | closed | ssh・openssl の stdin、argv、環境、remote Git 全 object を PEM、seed、base64、hex ごとに検査 |

既存テストの期待値、M14からM17の node 名、R2からR9、closure tuple 順序は変更していません。

指定4項目の逐語出力です。

```text
CHECK1 bootstrap_committed head=90bddf1969aa3eb46bb1d990fc19c7a71a5e6d1a ledger_bytes=0
CHECK2 verifier_accepts rows=1 serial=1 source_commit=90bddf1969aa3eb46bb1d990fc19c7a71a5e6d1a
CHECK3 sha256_rejected_before_signing signing_started=False error=remote HEAD is not a 40-hex SHA-1 commit id; the receipt verifier does not accept this target object format
CHECK4 bidi_escaped passthrough=False escaped=\xe2\x80\xae ascii_only=True
```

追加の漏えい検査結果です。

```text
EGRESS_FINAL_OK calls=10 encodings=6 history_bytes=9024
```

`compile()`、`git diff --check`、PTY付き commit 経路、履歴書換え拒否、無効生成署名の自己検証拒否も `python3` から確認しました。pytest と Web 検索は実行していません。`git status` 上の変更は許可された2ファイルだけです。親によるテスト実走が必要です。

## 総括

broker が検証子なら拒否する行を commit する経路を、現在履歴と prospective final ledger の両方を同じ検証子で approval 前に検査することで閉じました。秘密鍵 fd 固定、表示完全性、Git hardening、漏えい検出力も合わせて修正済みです。