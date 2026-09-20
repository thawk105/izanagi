## 総括

所有する 2 ファイルを修正しました。

- `t2700_ab_analyze.py`: `inspect_run`、`analyze`、`wilcoxon`、`dump_consumers`、`write_analysis`、`selftest`、`main` を更新し、`consumer_set` と `--check-run` を追加。
- `t2700_history_estimate.py`: `extract`、`estimate`、`main` を更新。scheduler・取得可能な repository SHA・取得不能件数を追加。E の「適合前 N 件」は維持。

失敗診断の stdout／stderr／child.log 探索、解析締切と `post_cutoff` 集計、slot 順序検算、v2 束縛検算、複製失敗と原本不発行の区別を実装しました。MC の説明を訂正し、Wilcoxon の非ゼロ差が 20 件超の場合は明示的に拒否します。

**実走結果**

- `python3 probe-t2700/t2700_ab_analyze.py --selftest`: **PASS**。既存反例 5 件・判定文言を維持。分類別 CLI 正負例、診断形式、witness、時差、取り直し・順序逸脱、締切後の結論不変を確認。
- `--dump-consumers orchestrator/tests/conftest.py`: **rc=0**。`source_sha256` を出力。
- 履歴 `--e-limit 10 --out /tmp/t2700-fix2-history-final`: **rc=0**。5,495 ログ走査、187 shard 抽出、131 採用、56 除外、125 session。採用分は全件 `loadgroup`、repository SHA は全 131 件「取得不能」。除外は全件 `pytest_rc != 0`。

**単走判定の契約**

```bash
python3 probe-t2700/t2700_ab_analyze.py \
  --check-run <run-dir> \
  --measurement-tip <sha> \
  --consumer-nodes <json>
```

有効なら **rc=0**、無効なら **rc=1**。stdout の JSON に `classification` と `reasons` を出します。selected digest の全走一致・時刻非重複・worktree 一致は `analyze` で検査します。

**v2 で読む field／成果物**

- `run.json`: `schema`、`run`、`condition`、`pair_slot`、`measurement_tip`、`tip_sha`、`tip_sha_after`、`worktree_realpath`、`warm_tip`、`warm_rc`、`submitted_at`、`finished_at`、`session_dir`、`session_dir_origin`、`copy_ok`、`artifacts.{status,requirement}`、`env`、`rc`、前後の dirty 件数。
- 各 shard: `junit.xml`、`report.json`、`dispatch/{receipt,request,result}.json`、対応する `.e<job>`／`.o<job>`。
- receipt: `request.args`、`result.pbs_jobid`、`result.child_rc`、`outcome.{kind,rc,accounting_verified}`、`terminal_reason`。request／result の複製とも照合。
- `session/SHA256SUMS`: receipt・request・result・stdout を含め再計算。optional 成果物も保存成功なら掲載を要求。
- consumer JSON: registry と `source_sha256`。後者は `analysis.json` に転記。

指定された 01-A の chain.log／child.log に timeout 本文はありませんでした。fixture は両 memo の例外生成形式に基づきます。

未実走は、実測 E/L 系列への適用、実 launcher との連続運転、pytest・変異検査です。docs 編集・commit・git 操作は行っていません。