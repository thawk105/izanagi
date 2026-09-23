[起動器](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ud/.t2847-launcher/launch_mutation_run.py)を作成しました。編集したのは指定された 1 ファイルだけです。`s8a` と `mutations --job J1〜J4` を実装し、計算ノードでの本走は**実装済み・未実走**です。

**検査結果:** `py_compile`、J1〜J4 と s8a の `--plan-only`、`check_codex_agents.py`、`check_docs.py` はすべて rc=0 でした。plan-only の出力を要約すると次のとおりです。

```text
J1 W1,W2    V17:W1 V22:W1 V35:W1 V18:W2
J2 W3,W4    V19:W3 V23:W3 V20:W4 V24:W4
J3 W4,W5    V33:W4 V21:W5 V26:W5
J4 W6,W7,W8 V27:W6 V31:W7 V32:W8
s8a         driver=s8a_trigger_coverage CLK=2100
```

実走したコマンドは `python3 -m py_compile .t2847-launcher/launch_mutation_run.py`、`python3 .t2847-launcher/launch_mutation_run.py mutations --job J1`〜`J4 --plan-only`、`python3 .t2847-launcher/launch_mutation_run.py s8a --plan-only` です。各 job の plan-only JSON には patch・macro・workload・flags の全件が出力され、patch の実在検査は行いません。

差し替え名の全件は、**s8a** が `buildcache.DEFAULT_CC/CXX`、`source_digest.resolve_evidence(cxx)`、`repo_output_root`、`ENV_TAG`、`subprocess.run`、**mutations** が `buildcache.DEFAULT_CC/CXX`、`PIN`、`subprocess.run`、V21 実行中だけの `_verifier_run` です。compiler・pin・出力先の指定と subprocess の受動保存は、patch 適用や condition gate、verifier の判定を変更しません。V21 のラッパーは元の verifier を先に呼び、同じ trace に証人なしの追加検査を行って別欄へ保存します。CLK は両 mode とも差し替えず、meta に記録します。

## 総括

親が job dir へ移せる起動器が完成しました。build・run・verifier の計算ノード実走結果はまだありません。