## 総括

作成: [probe/verifier_profile_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/vcap-s1probe/probe/verifier_profile_probe.py) — **839 行、untracked**。

SHA256:
```text
bc86ca222282c5eb1c5f716b240095c435f0474300962689df94a7e86f7bb03d
```

最終 selftest 実走結果（rc=0）:
```text
PASS (a) run rc=0
PASS (b) phase start/end pairs
PASS (c) samples required keys
PASS (d) completed, peaks, estimates
PASS (e) summarize Markdown
PASS (f) serializable=True
PASS (g) restore mismatch rc=4
selftest: PASS=7 FAIL=0 SKIP=0
```

構文確認は PASS。指定された名前 8 件すべてを `getattr` で確認済み。`run` / `_child` / `summarize` / `selftest` の `--help` はすべて rc=0。

zstd の小さい復元・SHA 不一致負例は実走済み。**保全済み実 trace の復元、計算ノード経路、大規模 trace、OOM・thrash、timeout、gc-freeze の A/B は未実走**です。

判断・仕様上の補足:

- SCC wall は別計時の `n_edges` を含み、anomalies 単独の wall も記録します。
- packed 値が符号付き `array("q")` の上限を超える場合も、理由を記録して見積りを中止します。
- RSS 差分は allocator 再利用の影響を含む保持量の観測です。
- usage エラーも出力先が判明して書き込める場合は記録します。出力先未指定・書込不能の場合は記録できません。

tracked 差分はありません。verifier / tests を含む所有外への変更、docs 作成、git add / commit / stash / worktree 操作はありません。