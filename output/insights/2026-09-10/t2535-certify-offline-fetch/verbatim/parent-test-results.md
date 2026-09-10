# 親が実走した検査 (T-2535 段 6 レビュー向け射影)

実行者は親 (Claude)。作業ツリーは
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch`、
base commit `7f17e1c63`、変更は所有 3 file のみ (`git status --short` で確認)。
実装子の worktree と wave worktree を `diff -rq` で比較し、**差分がちょうど所有 3 file**であることを
確認したうえで取り込んだ。

## 焦点走

```
python3 tools/run_tests.py orchestrator/tests/test_pegasus_calibration_workload.py -q
```

- 結果: **35 passed in 7.35s**、rc=0。
- 実行場所: Pegasus 計算ノードへ dispatch (request 988656.nqsv および 988xxx の 2 回、いずれも rc=0)。
- **これは受入全走ではない。** runner 自身が「受入形でない走行です」と警告している。

## 親が段 1〜4 で取った実測 (レビューの前提)

- login node は github.com を解決する (20.27.177.113)。計算ノードは解決しない
  (T-2224 が bnode122 / bnode013 の 2 ノードで実測)。
- 永続 cache `/work/1/SFC/tanab/izanagi-thirdparty-cache` の masstree には
  **ignored artifact が 71 件**ある (`git ls-files --others --ignored --exclude-standard` で実測)。
- hydrate 済み staging root
  (`output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src`) の masstree は
  **ignored artifact 0 件**、mode 0755、所有者は実行 user。実測済み。
- 同 staging root は `.gitignore:24` の対象で、hydrate 後も `git status --short` は空。
- CCBench の FetchContent 依存はちょうど 3 本 (`external/ccbench/cmake/ThirdParty.cmake:42,106,130`)。
- masstree は `add_custom_command` の `WORKING_DIRECTORY` を source dir にして
  `bootstrap.sh` → `configure` → `make` → `ar` → `ranlib` を実行し、
  `libkohler_masstree_json.a` と `config.h` を **source dir の中へ**生成する
  (`ThirdParty.cmake:57-78`)。
- `policy.json` の `perf_candidates` は
  `/usr/lib/linux-tools/5.15.0-135-generic/perf` と `.../5.15.0-100-generic/perf` の絶対 path 2 本。
- 較正 record の実体は calibrator が staging へ書く `calibration.json`
  (`orchestrator/calibrator/cli.py:1106-1117`)。

## まだ実走していないもの

- 受入全走 (`tools/run_tests.py` の受入形)。段 6 の後半で親が走らせる。
- 変異 matrix。統合 commit 後に親が走らせる。
- 計算ノードでの実 CCBench configure / build / 較正。段 6 の後に親が投入する。
- 所有外の consumer test 群 (`test_pegasus_tools.py` ほか)。段 6 で親が走らせる。
