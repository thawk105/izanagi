## 所見対応表

- `partial`: 型検査は修正済み。指定テストは dispatch infrastructure failure (`rc=16`) により未実走。

## 直した内容

変更前:

```python
assert type(selection_calls[0][1]) is Path
```

変更後:

```python
assert type(selection_calls[0][1]) is type(root)
```

直後の値検査は維持しています。

```python
assert selection_calls[0][1] == root
```

これにより、渡された root が CLI の root と同じ型かつ同じ値であることを検査します。

## 実走

対象:

```text
orchestrator/tests/test_s8b_oracle_judge.py
```

実行コマンド:

```text
python3 tools/run_tests.py orchestrator/tests/test_s8b_oracle_judge.py -q
```

結果: `rc=16`。`qstat -Q preflight rc=1` の dispatch infrastructure failure で、テスト子プロセスは開始されませんでした。実装済み・未実走です。

## 総括

指定された assert 1 行だけを修正しました。  
`git diff --check` は通過しています。  
テスト結果はインフラ失敗のため緑とは報告しません。