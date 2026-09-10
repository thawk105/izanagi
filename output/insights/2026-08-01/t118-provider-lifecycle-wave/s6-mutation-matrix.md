# 変異 matrix 本走の raw 台帳 — [T-118] provider neutral tree の lifecycle

`DW-O19` に従い、統合 commit `f7baa9f` の**後**に tracked file へ本走した。
harness は `/home/SFC/tanab/.claude/jobs/0db43107/tmp/t118-wave/mutation_harness.py`、
raw 結果は同 dir の `mutation-matrix.json` と `mutation-parent-run.log` (本 dir へ複写)。

## 走行条件

- 対象 (変異先): `orchestrator/campaign/s8b_prediction_runner.py`、
  `orchestrator/campaign/claude_projected_provider.py`、
  `orchestrator/campaign/p3_autonomous_workload_trial.py`、および guard test 2 ファイル
- 判定 (テスト): `orchestrator/tests/test_s8b_prediction_runner.py` +
  `orchestrator/tests/test_p3_autonomous_workload_trial.py` を 1 回の走行で (`-rf`)
- 変異と復元は **login node** で行い、pytest だけを `tools/run_tests.py` 経由で
  Pegasus gen_S 計算ノードへ dispatch した。外側 job walltime で親が殺されて `finally` の復元が
  走らない事故 (F32) を構造的に避けるための配置である
- **harness の作成は Codex author、実行は親**。codex の sandbox は socket 作成を拒否するため
  子から `qstat` を呼べず dispatch できない (段 5・段 6 の実装子が 2 回とも rc=16 で
  pytest を走らせられなかったのも同じ原因である)
- `flock` の単一走行 guard を持ち、取得失敗で abort する (`DW-M05`)
- 置換ごとに累積後の anchor 一意性を assert し、注入をディスク内容で確認する (`DW-M04`)
- 復元は `git checkout --` の後に**内容比較** (`read_text() == 元ソース`) で検査する (`DW-M05`)

## 結果 (2 回目 = 採用)

```
mutations=16  killed=16  survived=0  timeout=0  parse_error=0  canonical_matched=16
baseline: rc=0 / failed=0 (26.82s)
restore : identical_to_original=True (全 16 変異 + 最終)
anchor  : 16 件すべて一意 (count=1)
repo_head: f7baa9f85b06282088ef3b7d30c278551da8c734
```

| ID | 変異 | 結果 | 新規赤 node 数 | canonical 期待 kill | 一致 |
|---|---|---|---:|---|---|
| M1 | `close()` を no-op 化 | KILLED | 9 | `test_claude_headless_close_removes_only_neutral_tree` | yes |
| M2 | interface を保つ未登録 (即 detach 済み) finalizer | KILLED | 16 | `test_claude_headless_finalize_fallback_removes_only_neutral_tree` | yes |
| M3 | finalize callback を owner の bound method に | KILLED | 2 | 同 fallback test | yes |
| M4 | 削除対象を作成時 identity から `resolve()` 済み path へ | KILLED | 2 | `test_claude_headless_close_refuses_symlink_swapped_identity` | yes |
| M5 | `close()` の cleanup 例外抑止を除去 | KILLED | 3 | `test_claude_headless_close_never_raises_and_retries_before_detach` | yes |
| M6 | 削除成功前に `finalizer.detach()` | KILLED | 3 | 同 retry test | yes |
| M7 | `__init__` の例外時 close を除去 | KILLED | 3 | `test_claude_headless_init_failure_removes_neutral_root[mcp-config]` | yes |
| M8 | `seal()` の `finally: provider.close()` を除去 | KILLED | 2 | `test_seal_calls_provider_close_with_strong_reference[success]` | yes |
| M9 | `run_trial()` の owned provider close を除去 | KILLED | 2 | `test_run_trial_closes_owned_providers_in_reverse_order[success]` | yes |
| M10 | `run_trial()` が injected provider も close (**過剰拒否側の正例**) | KILLED | 1 | `test_run_trial_does_not_close_injected_providers` | yes |
| M11 | `_provider_set` の partial-failure close を除去 | KILLED | 1 | `test_provider_set_closes_partial_projected_provider_set_in_reverse_order` | yes |
| M12 | invocation 完了時に neutral cwd を即時削除 | KILLED | 2 | `test_claude_headless_argv_stdin_env_and_neutral_cwd` | yes |
| M13 | guard の root 消滅 assert を除去 | KILLED | 1 | predicate guard `[root]` | yes |
| M14 | guard の `artifact_root` 存続 assert を除去 | KILLED | 1 | predicate guard `[artifact]` | yes |
| M15 | guard の artifact bytes 不変 assert を除去 | KILLED | 1 | predicate guard `[bytes]` | yes |
| M16 | 削除対象を `self.artifact_root` へ変更 | KILLED | 8 | `test_claude_headless_close_removes_only_neutral_tree` の非交差 assert | yes |

各変異の逐語 old/new は harness の変異定義が正本であり、上表の note はその要約である。

## 事前登録からの逸脱 (`DW-M01` の記録義務)

- **M2 の逐語を変更した。** 事前登録は「`weakref.finalize` の登録を削除」だったが、
  単純な行削除は `finalizer` 未定義の setup ERROR になり**偽 kill** になる (段 6 レンズ D が指摘)。
  interface を保つ「登録直後に `detach()` する finalizer」へ再照準した
- **M16 は封じ込めた。** guard test の `artifact_root` は `tmp_path` 配下にあり、recorder が
  実削除を既知 identity へ委譲するため、実 `output/` を削除する形にはしていない

## erratum — 1 回目の本走は harness の計測不良で全件 SURVIVED になった (`DW-M02`)

初回結果は消さず `mutation-matrix-erratum-run1.json` に残す。

- 1 回目は baseline 緑 (rc=0) の後、**M1〜M16 すべてが `rc=1 failed=0` で `SURVIVED`** になった
- 親が dispatch 成果物を直接読んで裏取りしたところ、M16 の job stdout
  (`output/pegasus-dispatch/c5106baed7d826acd48f3b7155561ad6/izdw-c5106baed7.o876956`) には
  `8 failed, 92 passed` と `FAILED <nodeid>` 行が 8 本あり、canonical 期待 node も含まれていた。
  **変異は効いていた。生存ではなく抽出の失敗である**
- 真因は harness の `FAILED_RE` が `FAILED <node> - <error>` の ` - <error>` を**必須**にしていたこと。
  pytest の `-rf` サマリは assertion message が多行だと **nodeid で行が終わる**ため全件不一致になった。
  加えて dispatch のコンソール出力は行頭 `| ` 付きで `omitted_bytes` により切り詰められるため、
  そもそもコンソールから取ること自体が不健全だった
- fix: failed node の正本を**計算ノード job stdout 全文** (`izdw-*.o<request-id>`) へ移し、
  ` - ` が無ければ行末までを node とし、**`rc != 0` なのに抽出 0 件なら `SURVIVED` にせず
  `PARSE_ERROR` で fail-closed 停止**する形にした
- これは harness 個別のミスではなく **`DW-M08` の規約文言の欠陥**である。同日、並行実行中の
  別 wave 2 本 (t244 / t249) も同じ欠陥を独立に踏んでいた (process 一覧で確認)。
  独立 3 例なので `DW-G03` の族一般化条件を満たす → F71

## この wave の guard が届かない層 (正直な限定)

`DW-G05` に従い、検出力を過大表現しない。guard が実証したのは
明示 `close()` の正常/異常、参照破棄後の fallback、静止した削除境界、owner の close 呼び出し、
partial construction、owned/injected 分岐、cleanup 失敗後の再試行 (2 回目の `close()`) までである。

**届かない層**: interpreter shutdown 中の live object、fork child の atexit、
並行 invoke/close、close 後の再 invoke、scope 外 callsite。

さらに `test_claude_headless_close_removes_only_neutral_tree` の recorder は、実引数を記録した上で
**既知 identity を削除する**ため、この test 単体では「production が渡された identity を消したこと」を
証明しない。同性質は M4 の symlink test (`cleanup_error`)、M7 の init 失敗 test、fallback test の
実委譲で被覆されており、焦点再レビューは「何も削除しなければ root assert が赤になる」として
closed と判定した。
