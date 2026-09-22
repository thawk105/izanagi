N1 は **closed** です。

- [v3check.py:245](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-ccb-b/output/runs/t2854-ccbench-v3/probe/v3check.py:245)：両取引種別の件数検査の直後に、run 全体で R または W の総数が 0 なら `content-table` とする検査を復元しました。OrderLine の番号は記録のみのままです。
- [selftest.py:140](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-ccb-b/output/runs/t2854-ccbench-v3/probe/selftest.py:140)：負例 `delete-all-R-with-correct-count` を 1 件追加。正常 fixture の全 R 行を削除し、各 C の nR を 0 にします。W・E・txid・tx_type・stdout witness を維持し、理由集合が `['content-table']` と完全一致することを検査します。

実走コマンド：

```text
python3 output/runs/t2854-ccbench-v3/probe/v3check.py --selftest
```

結果は **rc=0、193/193 passed、failures=0**。既存 M3／M4 の理由集合完全一致の自己試験も合格しました。

## 総括

- 変更は指定 2 ファイルの検査 1 箇所と負例 1 件のみです。
- 他の検査・既存負例の期待・kill 条件は変更していません。
- tracked file・index・HEAD は変更せず、build・投入は行っていません。