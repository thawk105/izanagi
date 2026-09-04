## 現行の受理・拒否挙動

着手前は既存 31 点の拡張格子だけを受理し、job body は常に sweep、overthrottle、B-10 report を順次実行していました。submitter は `--output-parent` のみを受理し、各 receipt に run kind はありませんでした。既存 report は exact 31 点以外を拒否するため、T-2266 の 8 点には使用不能でした。

## 実装した内容

- [backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2266-author/orchestrator/campaign/backoff_extended_sweep.py:58)
  - 要求集合、実現集合、F718 未実現理由を別定数化。
  - `t2266_genomes()` で `none`、`adaptive`、固定 6 点の exact 8 genome を生成。
  - `t2266_config_for()` で専用 slug、格子、測定順、要求・実現・未実現を campaign identity に束縛。
  - `run_workload()` に最小の mode 選択を追加し、既存 gate、prebuild、`run_campaign`、`GeneratorId.BACKOFF_SWEEP` を共有。
  - T-2266 mode の各 rep から throughput と abort 率を採取し、採用 round の WAL TPS と照合。
- [b10_backoff_grid.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2266-author/tools/pegasus/b10_backoff_grid.sh:30)
  - `extended` を既定とする閉じた run kind を追加。
  - T-2266 時だけ `--run-kind t2266-tail` を付与し、overthrottle と既存 B-10 report を省略。
  - submit由来の failure、reservation、completion に run kind を保存。
  - completion 前に 8 commit と `.dat`、JSON の存在を検査。
- [submit_b10_backoff_grid.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2266-author/tools/pegasus/submit_b10_backoff_grid.sh:6)
  - `--run-kind extended|t2266-tail` を追加。
  - 既定 qsub 環境を維持し、T-2266 opt-in 時だけ `B10_RUN_KIND` を渡す。
  - manifest、submitted、failed の全 submit event に run kind を保存。
- [test_backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2266-author/orchestrator/tests/test_backoff_extended_sweep.py:183)
  - exact 8 点、要求・実現集合とF718、全 rep schema、create-only、run kind routing／receipt を検査するテストを追加。

## report の実装先

[orchestrator/campaign/backoff_extended_sweep.py:materialize_t2266_report()](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2266-author/orchestrator/campaign/backoff_extended_sweep.py:676) です。

- `.dat`: `backoff_us throughput_tps abort_rate latency_ns cv`。固定 6 点を出力。
- JSON: 8 点すべてについて全 5 rep の `throughput_tps` と `abort_rate` を保存。
- 両方とも create-only で、既存ファイルを拒否。
- 合否、閾値、shape 分類は追加していません。

## 走らせた検査

- `git diff --check`: rc=0。
- production/test Python の `ast.parse`: 成功。
- submitter の `bash -n`: rc=0。
- import-level smoke: 3 workloadすべてで 8 genome、専用 slug、全 5 rep JSON schemaを確認。
- `python3 tools/run_tests.py orchestrator/tests/test_backoff_extended_sweep.py -q`: rc=16。`qstat -Q preflight rc=1`、`child_started=false` のため、全 nodeid 未実走。
- 制約 meta-test invocation:
  - `test_ccbench_spawn_sites.py` 全体
  - `test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed`
  - `test_p3_build_authority_cli.py::test_machine_callers_use_closed_generator_receipts`
  - `test_official_perf_closure.py` の inventory 2 nodeid
  - `test_hooks.py` の registry/inventory 2 nodeid
  - 同じ rc=16 で子は起動せず、すべて未実走です。

したがって、pytestについては「実装済み・未実走」であり、緑とは報告しません。

## 受理集合の変化

- 新規受理: driver、job body、submitter の exact `t2266-tail`。
- 継続受理: 引数省略時の既存 `extended`。
- 新規拒否: `extended`／`t2266-tail` 以外の run kind。
- 新規拒否: T-2266 の genome総数が8でない、8点すべてがcommitされていない、reportの片方でもない場合の completion。
- 新規拒否: report先に同名 `.dat` またはJSONが存在する場合。
- workload 3種、PBS envelope、既定 qsub環境、既存31点格子、既存campaign identityは変更していません。

## 波及可能性

- `backoff_extended_sweep_report.py`、`backoff_requested_us.py`、既存 plotting は従来の `config_for()`、`genomes()`、31点artifactを引き続き参照します。
- completion consumerには新しい `run_kind` fieldが追加されます。repo内既存consumerは追加keyを拒否しません。
- `test_campaign.py` の certified-writer inventory、`test_p3_build_authority_cli.py` のgenerator authority、official perf closure、CCBench spawn inventoryが静的な影響候補です。
- Pegasus registry path、class、gate、evidenceは変更していないため、`admission_registry.json` とhooks goldenは無変更です。
- 新規ファイルはなく、repo file一覧への登録追加は不要です。
- 親所有のdocs、freeze、patch、既存report、plotterには触れていません。

## 総括

- T-2266専用の要求集合と実現集合を分離しました。
- 固定1000はF718による未実現、999は最近傍の実測点として保持します。
- 測定格子は `none + adaptive + 固定6点` のexact 8点です。
- 既存31点経路の定数、格子生成、identityは維持しています。
- T-2266 reportはdriver内に実装し、全repのTPSとabort率を残します。
- run kindはsubmit、reservation、failure、completionの全receiptへ保存します。
- T-2266 completionは8 commitとreport 2成果物を必須にしました。
- 変更は許可された4ファイルだけで、commit／addは行っていません。
- pytestはPegasus dispatch障害により未実走です。