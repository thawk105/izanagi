## 変更面

所有範囲の 6 ファイルを実装しました。作業 repo の staging・commit・stash、所有外ファイルの編集はしていません。

| file:line | 変更 |
|---|---|
| [production probe:133](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2790-u1-author/tools/pegasus/probes/t1259_qsub_env_delivery_probe.py:133) | 3 関数に timeout 引数を追加・中継。既定 30.0 |
| [helper:7](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2790-u1-author/orchestrator/tests/t1259_scan_bound.py:7) | 候補値 120.0 と fixture 専用 wrapper |
| [既存 fixture:77](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2790-u1-author/orchestrator/tests/test_t1259_qsub_env_delivery_probe.py:77) | 呼出し 1 行変更、import 1 行追加 |
| [新規 test:53](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2790-u1-author/orchestrator/tests/test_t1259_scan_bound.py:53) | 正例 2 本・例外伝播 1 本、自走 harness |
| [scan_sampler.py:25](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2790-u1-author/output/scratch-t2790/scan_sampler.py:25) | JSONL sampler |
| [junit_scan_survey.py:35](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2790-u1-author/output/scratch-t2790/junit_scan_survey.py:35) | JUnit の層別 Markdown 集計 |

production の呼出しは [684 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2790-u1-author/tools/pegasus/probes/t1259_qsub_env_delivery_probe.py:684)・[852 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2790-u1-author/tools/pegasus/probes/t1259_qsub_env_delivery_probe.py:852)とも `_repo_snapshot(repository)` のままです。

## 走査対象と例外型の不変性

diff は引数定義・timeout 指定・中継だけです。以下を維持しました。

- `rev-parse --verify HEAD`
- `status --porcelain=v1 --untracked-files=no --ignore-submodules=none`
- `ls-files --others --exclude-standard -z`
- `symbolic-ref -q HEAD`

`GIT_OPTIONAL_LOCKS=0`、`check=True`／detached 判定の `check=False`、返り値構造、`ProbeError` 条件は不変です。timeout の変更部分だけを除いた production 全体の AST が変更前と一致しました。`TimeoutExpired` は捕捉せず、直接検証では同一例外オブジェクトの伝播も確認しました。

## 他 caller への波及

- 既存 autouse fixture・consumer 30 test 関数・10 parametrize は不変。ファイル内容も許可された 2 箇所だけの差分と確認しました。
- `lambda _root: ...` の置換先には production が引き続き位置引数 1 個で呼ぶため、互換性を保ちます。120 秒を渡す module fixture は autouse の monkeypatch 前に取得します。
- `conftest.py` の real-repo inventory／process memo、`test_real_repo_serialization.py` の golden・収集検査は非変更です。
- `test_plain_runner_coverage.py` の `_self_runnable()` 判定は成立しました。allowlist は非変更です。
- `test_hooks.py` の probe 実行場所分類は非変更です。
- 新規 3 nodeid の duration 台帳登録は親に残しています。なお現行 G5 は全件必須ではなく **90% 以上の収録率**を検査しており、未登録だけで必ず赤になるとは断定できません。

## 直接呼出しの検証結果

**`DIRECT_CALL_PASS`**

一時 Git repo で実コマンドを spy 経由で実行し、次を確認しました。

- production：4 件すべて `30.0`
- fixture：4 件すべて `120.0`
- 両 snapshot の内容が一致
- 新規 test 3 本の直接呼出しが成立
- 定数 `0.0`／固定 dict 返却の両反実仮想で、test 2 が **AssertionError** により赤化

反実仮想はメモリ内で適用・復元しました。復元確認と `git diff --check` を実施済みです。全 6 `.py` の `py_compile` も成功しました。

## 計測 script の使い方

親が repo 外へ退避して実行する想定です。

```bash
python3 /outside/scan_sampler.py \
  --repo-root /abs/repo --worktree /abs/worktree \
  --out /outside/scans.jsonl --interval-seconds 20 \
  --max-samples 100 --stop-file /outside/stop --self-tag t2790
```

時刻・load・process 数・4 Git 操作それぞれの所要／合計・3 ファイルの hash 所要を JSONL に追記します。出力先が測定 worktree 内なら拒否します。

```bash
python3 /outside/junit_scan_survey.py \
  --shards-root /abs/shards \
  --since '2026-09-18 20:00' --out /outside/survey.md
```

regime・重なった他 session 数別の分位点、error 数、hostname、suite 時刻、個別所要を Markdown に出します。重なりは shard-0〜2 の窓の和集合との交差で数え、ピーク同時実行数とは区別しています。

## 未実走・未確認

pytest、焦点走、受入、正式な変異走、`check_docs.py`、計測 script 2 本は未実走です。120 秒は候補値のままで、採用判断に必要な負荷下の分布は未取得です。直接検証は親の実走を代替しません。

## 総括

実装済み。production 30 秒と走査・拒否条件を維持しました。
直接呼出し、新規 test 3 本、両反実仮想、compile、AST 比較が成立しました。
受入・計測・台帳登録・採用値判断・commit は親の手番です。
