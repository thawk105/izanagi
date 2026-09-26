[起動器](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ud/.t2847-launcher/launch_mutation_run.py) の A03・B02 を修正しました。

- **A03:** V21 の証人あり `_verifier_run` が例外を投げても、trace dir がある間に証人なし検証を試します。両側の argv・rc・結果または例外を `witness_verifier` と `no_witness_verifier` に記録し、元の例外を driver へ再送出します。
- **B02:** stock build 失敗、または workload の `stock_precondition` 不成立時は、その workload の変異を build・run せず、`attribution: "unattributable (stock precondition failed)"` と `skipped: true` を保存します。

実走したコマンドは次のとおりで、すべて **rc=0** でした。`py_compile` は出力なし、plan-only の出力は J1 が W1/W2・V17/V22/V35/V18、J2 が W3/W4・V19/V23/V20/V24、J3 が W4/W5・V33/V21/V26、J4 が W6/W7/W8・V27/V31/V32、s8a が `CLK: 2100` でした。

```text
PYTHONPYCACHEPREFIX=/tmp/t2847-fd-pycache python3 -m py_compile .t2847-launcher/launch_mutation_run.py
python3 .t2847-launcher/launch_mutation_run.py mutations --job J1 --plan-only
python3 .t2847-launcher/launch_mutation_run.py mutations --job J2 --plan-only
python3 .t2847-launcher/launch_mutation_run.py mutations --job J3 --plan-only
python3 .t2847-launcher/launch_mutation_run.py mutations --job J4 --plan-only
python3 .t2847-launcher/launch_mutation_run.py s8a --plan-only
```

加えて、V21 の例外経路を模擬実行し、証人なしの結果保存と元例外の再送出を確認しました。`git diff --check -- .t2847-launcher/launch_mutation_run.py` も rc=0 です。計算ノードでの build・run は未実走です。

差し替え名は既存どおり、両 mode 共通の `buildcache.DEFAULT_CC/CXX` と受動記録用 `subprocess`、s8a の `source_digest.resolve_evidence(cxx)`・`repo_output_root`・`ENV_TAG`、mutations の `PIN`、V21 実行中だけの `_verifier_run` です。V21 の wrapper は元の判定と例外をそのまま driver に返し、証人なしの結果を別欄へ記録します。patch 適用と condition gate の処理は変更していません。

## 総括

A03・B02 を所有 path 内で修正しました。指定された構文確認と J1〜J4・s8a の plan-only はすべて成功しました。