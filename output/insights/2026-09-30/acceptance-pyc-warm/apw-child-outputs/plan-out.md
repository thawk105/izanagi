brief の前提への反証: P2 の「preflight は tree を書かない」は成立しない。`_preflight_submodule` は marker が無い場合に `git submodule update --init --no-fetch` を実行する（`tools/run_tests.py:921–986`）。その実行と login collection を並行させると、両者が見る tree がずれうる。また、明示 shard mode は admission を迂回して直接 dispatch するため、通常経路に queue hint の事前検査はない（同 `2526–2533`, `2650–2659`）。**代案は、submodule marker が初めから有効な場合だけ collection を前倒しし、無効な場合は従来の preflight → dispatch → collection を維持すること。** これなら時間のかかる削除検査と RuleOps 検査には重ねられる。

| file:line | 変更内容 | 理由 |
|---|---|---|
| `tools/run_tests.py:1432–1487` | command・env の構築、process 起動、回収・log・parse を小さな共通 helper に分ける | 前倒し経路と従来経路の内容を一致させる |
| `tools/run_tests.py:2332–2382` | `_dispatch_result` に任意の起動済み collection を渡し、`collect_login` がそれを回収する。無ければ既存 helper を呼ぶ | `run_parallel` の順序と非前倒し経路を保つ |
| `tools/run_tests.py:2503–2524, 2618–2659` | shard 適格性確定後、preflight 前に条件つきで起動し、全 return と例外を `finally` で後始末する | 対象経路の一致と孤児防止 |
| `orchestrator/tests/test_run_tests_shards.py:386–417, 667–725` | 起動・回収・後始末の正負テストを追加し、既存の `_dispatch_result` モックには起動 helper のモックを添える | 既存期待値を変えず実 subprocess の混入を防ぐ |
| job dir `meas/make-trees.sh:3–15`, `run-pair.sh:3–5, 19–39, 56–73, 97–138` | K/H の commit 分離、同時起動、識別・記録を更新する | 別 commit の fresh 木を正しく対照する |

## 1. 起動条件と場所

`main` の `shard_count` 確定（`2503–2521`）と dispatch 免除判定（`2523`）の後、`2618` の最初の preflight より前に起動する。条件は `shard_mode`、`args == []`、`internal_shard_spec is None`、`not dispatch_exempt`、Pegasus LOGIN、`bounded_membership is not True`、有効な submodule marker（`_submodule_is_initialized`）の連言とする。空 argv／LOGIN／internal spec／bounded membership の大半は resolver（`267–298`）にも含まれるが、起動直前に同じ確定値を使う。

起動済み process は一つの所有変数として `_dispatch_result` へ渡し、`run_parallel` の callback が回収時に所有権を消費する。起動したのに callback が呼ばれなければ `main` の `finally` が破棄する。callback に process が無ければ従来の `_collect_login_universe` を使う。この二方向の扱いで、条件のずれによる未回収と process 不在を防ぐ。`run_parallel` 自体（`tools/acceptance_shards.py:1408–1500`）は変えない。

## 2. 回収

callback は `communicate(timeout=deadline_at - time.monotonic())` で待ち、残時間が非有限または 0 以下なら `_PEGASUS_DISPATCH_RC, ()` を返す。成功・非ゼロ rc のどちらも、現行と同じ `command=` の JSON 行、`stdout:\n`、stdout、`\nstderr:\n`、stderr を UTF-8 `errors="replace"` で encode し、`acceptance_shards._write_bytes_create_only(session / "login-collection.log", ...)` で書く（現行 `1461–1485`）。非ゼロ rc、timeout、起動・回収・log・parse の対象例外は rc 16 と空 tuple にする。成功時だけ `_parse_collect_only_nodeids(stdout)` を呼ぶ。

現行との差は `subprocess.run` の開始時刻が早まること、`Popen` と `communicate` に分かれること、timeout の時計が起動後も進むこと。command、env、cwd、log bytes、rc と parse の規則は共通 helper を使って一致させる。既存の `_collect_login_universe` の公開テスト seam と、残時間を検査するテスト（`test_run_tests_shards.py:691–714`）は残す。

## 3. 後始末

起動直後から `main` の `try/finally` が process を所有する。削除・RuleOps・submodule preflight の赤、例外、queue／dispatch の早期 return、`run_parallel` の deadline 超過・session 作成失敗・dispatcher-start 失敗（`acceptance_shards.py:1415–1498`）では、未回収 process を停止して `communicate()` または `wait()` で reap する。callback が回収済みなら後始末は何もしない。

`run_parallel` が signal handler を設置するのは session 作成後（`1435–1442`）。前倒しからその時点までの SIGINT/SIGTERM も捕まえる必要がある。外側で一時 handler を設置して中断を例外化し、`finally` で停止・reap 後に元へ戻す。collection を新しい process group で起動し、破棄時は group に停止 signal、猶予後に kill、最後に親 PID を必ず `wait` する。これにより collection の子孫も残さない。`run_parallel` 内の handler と重なる期間は既存 handler が優先し、外側の `finally` はなお実行される。

## 4. command・env・cwd・出力

現行の `sys.executable -m pytest`、exclusion tokens、`_DEFAULT_TARGET --collect-only -q -p no:cacheprovider`（`run_tests.py:1441–1451`）を共通構築関数から使う。`cwd=_REPO`、`_dispatch_environment()` から shard／plugin spec を除き、exclusion payload を設定する処理（`1452–1460`）も共通化する。

`_dispatch_environment()` は起動時の `os.environ.copy()` を使う（`1320–1334`）。対象となる明示 shard 経路では `main` の途中に恒久的な env 変更はない。ただし `_call_with_runner_exclusions` は呼出し中だけ exclusion env を変更する（`224–228`）。前倒し側も同じ exclusion payload を明示して渡し、開始時 env と現行 callback 時 env の差をテストで照合する。stdout／stderr は `PIPE` にしても、回収まで約 3 MB の出力で子が停止しうる。**起動時から別々の一時 file に流し、回収後に読み込む**方式を推奨する。一時 file は repo 外に置き、全経路で close・削除する。`communicate()` を開始直後から並行実行する方式でもよいが、追加 thread の管理が増える。

## 5. 検査順序と結果

`git ls-files --deleted` は読取り（`821–826`）。RuleOps の `check` は `validate_candidate_ledger` を呼び、結果を stdout に書く（`tools/ruleops.py:2617–2635`）。その Git 呼出しは read-only の閉集合と `--no-optional-locks` を使う（`397–443`）。コード上、ledger や repo の明示的な書込みはない。ただし Python の import は通常の pyc を書きうるので、「一切書かない」とは言わない。

submodule preflight だけは前述のとおり書込み可能である。有効 marker を起動条件に加えれば、この分岐では `_preflight_submodule` は marker の読取りで終わる（`892–927`）。marker 不在は従来順序へ戻す。collection が書く通常の `__pycache__` は ignore 対象で、`git ls-files --deleted` の追跡済み削除集合と RuleOps の Git snapshot を変えない。RuleOps が検証する ledger と tracked blob は collection の入力に依存しない。tree が外部から同時に変更される場合の一致はこの静的論証の対象外であり、既存の独立 login universe と shard universe の gate 3（D711）で不一致を拒否する。

## 6. テスト

`test_run_tests_shards.py` に、(a) marker 有効の shard 正例で preflight 中に起動済みであること、回収した nodeid が universe になり log bytes が現行形式であること、(b) preflight 赤で元の rc を返し process group を kill・reap すること、(c) 回収時 deadline 超過で rc 16 と空 tuple、(d) 非 shard・非 LOGIN・dispatch 免除・internal spec・marker 不在では前倒ししないこと、(e) dispatcher-start 失敗で callback 未呼出しでも reap することを追加する。3 MB 級 stdout/stderr の完走も file 使用の回帰として検査する。

既存 `test_all_dispatch_workers_start_before_parent_wait_or_collection_result_use`、`test_parallel_parent_uses_one_absolute_deadline_contract`、`test_composite_defers_parent_task_record_and_strips_shard_sidecar` の期待値は変えない。`test_login_collection_uses_remaining_absolute_deadline` は従来 helper に対する検査として残し、前倒し callback の残時間を別テストで検査する。`main` をモック dispatch で呼ぶ既存テストには起動 helper のモックを添える必要があるが、期待 rc・引数は維持する。実走は親担当であり、ここでは行っていない。

## 7. 事前登録する変異

| 変異 | 殺す test nodeid（追加予定） |
|---|---|
| marker 有効でも起動を preflight 後へ戻す | `test_early_login_collection_starts_before_preflight` |
| callback が起動済み出力を使わず再 collection する | `test_early_login_collection_reuses_output_and_log_format` |
| 回収時に `login-collection.log` を書かない／形式を変える | `test_early_login_collection_reuses_output_and_log_format` |
| preflight 赤で停止・reap しない | `test_early_login_collection_preflight_failure_reaps_process` |
| dispatcher-start 失敗で未消費 process を放置する | `test_early_login_collection_dispatcher_start_failure_reaps_process` |

## 8. 対照 runner

`make-trees.sh:3–15` の単一 `C` を `K_COMMIT`／`H_COMMIT` の引数にし、K1/K2 は base、H1/H2 は wave tip から順次 fresh 木を作る。各 HEAD、初期 pyc 0、submodule marker を記録する。runner は job dir に置き、repo に入れない。

`run-pair.sh:3–5, 34–39, 97–138` は期待 commit を K/H の 2 個に分け、各 HEAD を各期待値と照合する。従来の「K と H の HEAD が同一」という `aggregate.py` の判定も対応して変更する。両側とも `PYTHONDONTWRITEBYTECODE` を unset し、`IZANAGI_ACCEPTANCE_SHARDS=3` で現行どおり数秒以内に同時起動する（`56–73`）。古い K だけ bytecode 禁止にする比較では、この wave の差を測れない。

指標の outer は既存の dispatch intent 起点ではなく `start-epoch` → 統合 `junit.xml` mtime と明記して追加する。各 shard の pre、W_max、`login-collection.log` mtime と compute-visible.json mtime を保存する。後二者は別ホストの時計なので、順序は時計同期を確認できた場合だけ断定し、境界近傍は不確実と記す。受理集合は K/H の login universe と各 shard の observed universe を要素単位で照合する。2 対の結果で pre が温の峰に入るかを判定し、待ち行列条件も同時に記録する。

## 総括

前倒しは marker が有効な shard 経路に限定し、書込み可能な submodule 初期化との競合を避ける。
起動済み process は `main` が所有し、回収されない全経路で停止・reap する。
command・env・log・universe 判定は共通 helper で現行と一致させる。
未解決点は前倒し起点から 5100 秒を数えるか、従来どおり dispatch 起点にするかという deadline の定義であり、実装前に一つに固定してテストする。