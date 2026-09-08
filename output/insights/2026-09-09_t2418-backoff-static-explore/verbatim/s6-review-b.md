## shell 分岐の追跡

- `t2418-explore` は job 側の受理 case、`t2418_explore_sweep` stage、`SWEEP_COMMAND` の `--run-kind t2418-explore` 付与を順に通ります（`b10_backoff_grid.sh:186,581,591`）。
- T2418 は extended 専用の追加分析・正式 report を通らず、cleanup、finalize へ進みます。
- `extended` は従来どおり `--run-kind` を省略して driver の既定値を使い、追加分析・正式 report を実行します。
- `t2266-tail` の stage、driver 引数、finalizer 本体は変更されていません。共有条件式が T2418 を加える形で拡張されたのみです。
- `B10_RUN_KIND`、`PY`、`OUTPUT_ROOT` などは初期化または `${...:-}` で保護されており、T2418 経路に `set -Eeuo pipefail` 起因の未定義変数や空配列展開は見当たりません。

## finalize の完了検査

- T2418 分岐は WAL の `stage == "commit"` から `variant` の集合を作り、unique commit が5件で `None` を含まないことを要求します（`b10_backoff_grid.sh:645`）。
- 専用 stem の `.dat` と `.json` を両方要求し、通常ファイルでない場合と symlink を拒否します（同:656）。
- `5` は finalizer の独立 literal です。genome 側は `none`、`adaptive` と `T2418_REALIZED_US` の3点から構成され、さらに binary 完全性検査と report loader も独立した literal `5` を持ちます。同じ長さ式を再利用した恒真検査ではありません。
- exact genome 集合と correctness は driver の report 生成時に検査されるため、finalizer の unique variant 数だけに依存して完了する構造ではありません。
- ただし finalizer は report の内容を検査しないため、後述する必須 provenance の欠落を検知せず `completion.json` を作れます。

## submit script の 3 か所

- usage: `extended|t2266-tail|t2418-explore`（`submit_b10_backoff_grid.sh:6`）。
- 受理 case: 同じ三値（同:36）。
- qsub 転送: T2418 と T2266 の場合に `B10_RUN_KIND` を `QSUB_ENV` へ追加（同:184）。
- 既定値は `extended` のままです（同:12）。したがって、T2418 指定が job 側で消えて正式29点へフォールバックする経路は塞がれています。

## driver の完走判定

- `run_workload()` は `total == committed == len(ordered_genomes)` かつ `aborted == 0` の場合だけ T2418 report を生成します（`backoff_extended_sweep.py:1445`）。
- loader は exact 5 genome、重複なし、attempt-bound bench、全rep、有限値、全 verify record の `certified=True` を要求します（同:1006）。
- `main()` は `total=5`、`committed=5`、`aborted=0` と `.dat`／`.json` の両方を要求します（同:1487,1503）。
- いずれかが欠ければ driver は非ゼロ終了し、PBS shell の finalize には進みません。

## 成果物から読める測定条件

- `reps`、`extime_s`、`records`、`threads`、`declared_use_class` は search_config（`backoff_extended_sweep.py:626`）、JSON top-level（同:1145）、`.dat` provenance（同:1253）に同値で載っています。
- run kind、claim scope、探索値、formal-series/grid/stopping-criterion の開示も3か所で一致しています。
- `.dat` 単体でも provenance 行から `reps` を確認できます。
- 一方、確定仕様が要求する「codec/wire 構成は実測済みだが、正値の runtime physical meaning witness は既存同様 unestablished」という境界は、いずれの成果物にもありません。これは must-fix です。

## 失敗時の記録

- `OUTPUT_ROOT_READY=1` 以降の通常の ERR 経路では、failure receipt に `run_kind` と `CURRENT_STAGE` が入ります（`b10_backoff_grid.sh:32,114`）。
- T2418 driver 実行中は `stage=t2418_explore_sweep`、その後は `ccbench_worktree_cleanup`、`finalize` が残ります。
- report 生成は driver 呼出しの内部なので、そこで失敗した場合も stage は `t2418_explore_sweep` です。測定本体と report 生成の区別までは残りません。
- receipt が残らない区間は、Python確定・output root 作成前、すなわち概ね同:186–265です。また SIGKILL、node消失、receipt writer 自体の失敗では残りません。これは確定仕様で submission receipt と stdout/stderr を併用する運用境界として受理済みです。

## 既存 consumer への波及

- T2418 は専用 campaign identity、schema、artifact stem を使用します。
- `backoff_extended_sweep_report.py` は shell の `run_kind == "extended"` 分岐内でしか呼ばれないため、T2418 成果物を処理しません（`b10_backoff_grid.sh:597`）。
- T2266 loader は exact genome 集合の照合で T2418 view を拒否し、その負テストも差分にあります。
- `plot_t2266_tail_mechanism.py`、`t2216_backoff_walk_model.py`、`backoff_requested_us.py` の現物は今回の射影対象外です。確定仕様に記録された exact 照合による拒否と、今回の差分で入口・schema・stemを変更していないことの範囲では、新成果物を誤受理する新経路はありません。

## must-fix

- 成果物への影響: T2418 report が、正値を確立済みの物理 backoff と誤読できる provenance のまま正式完了として受理されます。主張: 確定仕様の runtime-meaning 境界が search_config、JSON、`.dat` のすべてから欠落しています。file:line: `orchestrator/campaign/backoff_extended_sweep.py:626,1145,1253`。成り立たなくなる条件: adjudication package を伴わず成果物単体を受け取る場合、`realized_us`／`backoff_us` だけでは meaning witness が未確立だと判別できません。最小の是正: exact caveat を共有定数または機械可読 field として3か所へ同値で追加し、独立 literal のテストで固定してください。

## nit

- 主張: T2418 `.dat` の短い write でも例外文が `short T-2266 report write` になります。file:line: `orchestrator/campaign/backoff_extended_sweep.py:390`。成り立たなくなる条件: `_write_create_only_text` がT2418 report書込み中に short write を検出した場合。最小の是正: メッセージを `short report write` など run-kind 非依存の表現にします。完了受理や測定値には影響しません。

## 総括

must-fix は1件です。T2418 の submit→job→driver→report→finalize 経路と5件完了検査は静的には通っていますが、確定仕様が要求する runtime meaning の限定が成果物から欠落しています。修正前の投入は避けるべきです。

テストは実行しておらず、実装子報告の「47件 passed」は本レビューで再確認した緑としては扱っていません。