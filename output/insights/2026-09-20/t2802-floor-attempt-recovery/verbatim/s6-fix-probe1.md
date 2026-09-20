## 総括

[t2802_ab_analyze.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2802-unit-probe/probe-t2802/t2802_ab_analyze.py) のみ修正しました。332→389行（純増57行）。

変更関数: `parse_junit`、`parse_session`、`read_run`、`analyze`、`selftest`。

- skipped を許容し、走ごとにソート済み `skipped_floor` を記録。記録された time を F に含めます。
- 対に `skipped_match` を追加。不一致対は理由付きで無効化します。
- failed/error 拒否、重複・集合・time 検査、指標・判定式・閾値は維持しました。

実行検査:

```bash
python3 probe-t2802/t2802_ab_analyze.py --selftest
```

**rc=0、PASS**。過去6走の同一 skipped 3件、合成例の集合一致／不一致、判定3分岐、insufficient、12走超過、hash 改竄による無効化を確認しました。docs 編集・git 操作・commit は行っていません。