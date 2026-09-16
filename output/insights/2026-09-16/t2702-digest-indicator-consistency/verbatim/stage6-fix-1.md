## 変更点

`orchestrator/critic/digest.py`

変更前:
```python
   下がるのに abort_rate がほぼ不変なら、backoff は競合を減らしておらず
   待ち時間のコストだけを払っている、と読める。cache miss / IPC で機序を補強する。
```

変更後:
```python
   下がるのに abort_rate がほぼ不変なら、abort 率の改善は観測されず、
   待機コスト増が第一の仮説になる (cache miss / IPC で機序を裏取りする)。
```

`orchestrator/calibrator/model.py`

変更前:
```python
    # 算術平均 (一方でも欠損なら None)。
```

変更後:
```python
    # 算術平均 (一方でも欠損なら None)。
    # 有効 throughput が 0 件なら、最後に解析できた rep の 5 field をそのまま保持する。
```

## 所見ごとの対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| 5 | closed | 帰属を仮説表現に変更。恒等変換の説明は維持。 |
| 6 | closed | `rep_results[-1][1:]` と一致する保持規則を補足。 |

## 総括

指定の2ファイルの docstring・コメントだけを変更しました。
指定の AST 構文検査は終了コード 0 で成功しました。
テスト・git・commit・push は実行していません。
