生死確認 driver 一式を `g01/` に作成しました。repo の tracked file・docs・commitには一切触れていません。

### 作成ファイル

- [spec.json](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/spec.json) — 56 行
- [run_leg1_dispatch.sh](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/run_leg1_dispatch.sh) — 60 行
- [submit_leg2_bundle.sh](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/submit_leg2_bundle.sh) — 73 行（100 行以内）
- [compare_verdicts.py](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/compare_verdicts.py) — 190 行
- [README.md](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/README.md) — 89 行

`spec.json` SHA-256 は `1d13164c2830896656bdc3b12261756996decef018c9fd83dd4f7f495de2d70e`。両 leg に固定済みです。

### old 逐語と期待 node

`rg -Fxc` で実測した出現回数はすべて 1 です。

- G01: `    if path.name != expected:` — 1 回
- G03: `        if symbol.key in seen:` — 1 回
- G04: `            if brace >= 0:` — 1 回

裁定資料の行番号 608 / 729 / 744 は現 anchor では 793 / 914 / 929 に移っていますが、対象逐語と guard は一致しています。

期待 node は `rg -c '^def <name>\(' orchestrator/tests/test_spool_fold.py` で確認し、各 1 定義でした。

- N01 — 369 行
- N03 — 388 行
- N04 — 398 行

pytest collection による実在確認は未実施です。実走時には harness 自身の collection gate が再確認します。

### walltime

`00:45:00`（2700 秒）です。

- 5 走 × 実測 240 秒 = 1200 秒
- 起動・停止・復元余裕 = 1500 秒
- 合計 2700 秒
- gen_S 上限 86400 秒未満

20 分では実測 5 走分だけで余裕がないというレンズ A の所見を、PBS script のコメントにも記載しました。

### 単一理由性

静的には各 fixture は狙った guard のみを発火させます。

- G01: 正常な fragment を作り、filename だけを frontmatter 再構成値とずらしています。
- G03: 有効な decision fragment 2 件で、同一 symbol key の重複だけを作っています。
- G04: 有効な `D:valid` 定義に、正規 placeholder に一致しない underscore 付き残留だけを加えています。

fixture 逐語、issue code、各 old 逐語を repo-wide 検索し、期待 node 以外の直接 consumer は見つかりませんでした。ただし全走未実施のため、動的生成 fixture、xdist、cross-test interaction による追加赤は未確認です。

### 確認範囲と波及

確認済み:

- 両 shell の `bash -n`
- 比較 script の Python compile
- harness `_load_spec` による schema 受理
- `_validate_registrations` による全 anchor count=1
- canonical 全走 command に selector、nodeid、`-n 0` がないこと
- repo HEAD が anchor のまま
- `git status --porcelain=v1 --untracked-files=all --ignore-submodules=none` が空
- `git diff --quiet HEAD` 成功

未確認:

- pytest、qsub、両 ledger、比較結果
- submodule init、実際の復元、scheduler signal、cross-node flock
- `check_docs.py`、`check_codex_agents.py`
- pytest 緑

実行時には tracked 変異は `g01/worktree` 内だけです。ただし `git worktree add` は source repo の Git 管理領域へ worktree metadata を書き、leg 2 は `/tmp` lock と `g01/` 内の PBS 出力を作り得ます。

## 総括

- 3 変異・個別 dispatch・1-job local bundle・固定比較器・実行手順を作成した。
- 親の最初の command: `git -C /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch worktree add --detach /work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/worktree ea6ca433eb83d666ec64f3629cc35c769a2b5c19`
- 続きは [README.md](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/README.md) の command 列どおり。
- この smoke では恒久 transport の安全性を確認できない。
- cross-node lock と walltime kill 後の復元安全性も確認できない。