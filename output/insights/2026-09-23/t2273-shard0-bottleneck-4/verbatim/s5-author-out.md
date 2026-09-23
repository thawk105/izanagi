3 ファイルを実装しました。計算ノードでの replica と pytest plugin の実接続は **実装済み・未実走** です。commit は作成していません。

**ファイル別の変更**

- [runner](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe/tools/t2273_replica_runner.py)：TMPDIR 継承、statvfs・mount 情報、smoke の開始・所要・rc、A 中の 1 Hz 標本を追加。標本失敗は欠測として記録します。
- [plugin](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe/tools/t2273_replica_plugin.py)：`copy.list`・`copy.copytree`、親 span ID、可視 path 件数、全 span の self/children CPU 差分を追加。再帰 copytree は外側だけを記録します。
- [analyzer](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe/tools/t2273_replica_analyze.py)：同時本数、O_max/L worker の item 別排他分解、flock と依存 builder の対応、資源平均・CPU 比・指定の区分を追加。既存の key・consumer・shard 出力を保持しました。

**対象名・signature の確認**

対象ファイル内の定義に欠落・改名はありません。

| 対象 | 確認した signature |
|---|---|
| `_run_git` / `_run_git_bytes` | `(root: Path, *args: str)` → `str` / `bytes` |
| `_copy_git_visible_output` | `(source_root: Path, destination: Path) -> set[str]` |
| `_copy_t080_basis_file` | `(root: Path, relative: str)` |
| `_copy_t080_migration_basis_file` | `(root: Path, relative: str, basis: str)` |
| `_T080SharedBases.get` | `(self, key)` |
| helper / builder | `(tmp_path: Path, *, r_trailer="AI-Agent: none", extra_r_path=False, issue_receipt=True, distinct_basis_blob=False, active_v2_base=False)` |

`_t080_join_shared_bases()` の session 接続、標準ライブラリの `copytree`・`run`・`flock` も確認しました。migration の 2 関数は対象ファイル内の呼出し形を確認していますが、完全な定義 signature と実接続は未検証です。

**runner の組立**

A の argv は以下です。

```text
python3.10 <repo>/tools/run_tests.py orchestrator/tests
-n 48 --dist loadgroup
--junitxml=<session>/shard-0/junit.xml
-p tools.acceptance_shards
-p no:cacheprovider -p t2273_replica_plugin
```

session は既存の `acceptance_shards.create_session(repo, 3)` で作成します。env は出発点の除去リストを維持し、次を設定します。

```text
PYTHONDONTWRITEBYTECODE=1
IZANAGI_TASK_RUN_AUTO_RECORD=0
PYTHONPATH=<probe>:<repo>
TMPDIR=<継承値。未設定時のみ tempfile.gettempdir()>
T2273_REPLICA_OUT=<out>/A
IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1=
  {"session_root": "<session>", "shard_count": 3, "shard_index": 0}
```

**analyzer のトップレベル出力 key**

```text
note, missing, component_mapping, record_errors, installations,
key_count, keys, nonshared_builds, span_exceptions,
consumers, consumer_totals, run, controller, shard,
critical_worker_spans, scheduler_memo_lines,
concurrency_timeline, critical_worker_decomposition,
resource_sampling, builder_resources, visible_copies,
diagnostic_notes, complete_observation
```

条件付きで `incomplete`、解析失敗時に `fatal_error` を出します。

**実走した検証**

Python 3.10.12、`pegasus02` で実行しました。

- 両 CLI の `python3 -B tools/t2273_replica_{runner,analyze}.py --help`：rc 0。
- runner の `run --repo-root "$PWD" --probe-dir "$PWD/tools" --out-root "$PWD/tools/.t2273-smoke-out" --job-tag t2273-login-guard`：hostname 防壁で **rc 3**。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/tools" python3 -B -` の inline 検証：import・3.10 構文、`Recorder.invoke()` の同一引数・1 回委譲・同一返り値/例外、実 `/proc` 標本 2 件を確認。
- 同 inline 検証で `analyze()`・`item_decomposition()`・`copy_breakdown()`・`concurrency()`・`resource_table()` を実行。2 key、異なる O_max/L worker、親子 copy・入れ子 verify の排他和を確認。CLI 正例は rc 0、親外子 span の負例は rc 1。counter 欠測・copy.list 欠落も検出しました。依存先の stub は使用していません。

指定の plugin smoke は次のコマンドを実行しました。

```bash
PYTHONDONTWRITEBYTECODE=1 IZANAGI_TASK_RUN_AUTO_RECORD=0 \
PYTHONPATH="$PWD/tools" T2273_REPLICA_OUT="$PWD/tools/.t2273-smoke-out" \
python3 tools/run_tests.py orchestrator/tests/test_s8b_oracle_driver.py \
-k shared_base_builds_real_builder_once_across_processes \
-n 2 --dist loadgroup -p no:cacheprovider -p t2273_replica_plugin
```

結果は **rc 16、`qstat -Q preflight rc=1`、`child_started=false`**。pytest は未起動です。生成された dispatch 診断ファイルと一時出力は削除しました。

資源平均は node/client 全体の観測です。短区間には標本がない場合があり、children CPU は終了・回収済み子 process 分です。login の実標本では llite stats が欠測でした。これらを原因の断定には使いません。

最終 `git status --porcelain`：

```text
?? tools/t2273_replica_analyze.py
?? tools/t2273_replica_plugin.py
?? tools/t2273_replica_runner.py
```

## 総括

3 ファイルの実装と合成正例・負例、軽量な実読取り検証は完了しました。
pytest plugin smoke は dispatch 失敗で未起動、48-worker replica も未実走です。
親は計算ノードの smoke で copy 子 span・CPU・件数・record-error 0 を最初に確認してください。
続いて R1 の TMPDIR/fs、資源欠測、受入 argv、O_max/L の排他分解を確認してください。