静的検査のみ実施した。指定された5資料と、関連する launcher、pytest harness、`run_tests.py`、Pegasus dispatch、termination helper の該当行を確認した。pytest は未実行。

**所見 1: F285 A は wall-clock latch までは判定できるが、原因分離までは届かない**

分類: 判定力  
深刻度: Major  
根拠: `stage2-plan.md:147-156` は supervision を「poll/stdout/rollout/manifest」の一括 phase として記録する。`tools/codex_worker_launch.py:1455-1467` は `wall_clock_s` 等を `if/elif` で判定する。実際の形は `if elapsed >= ...: state.limit_trigger = "max_wall_clock_s"` である。  
**失敗シナリオ:** rollout の読み取り、manifest 処理、hook、receipt staging のいずれかが遅れて3秒を超える。sidecar は wall limit と広い phase を記録できるが、どの処理が縁を押したか判定できない。  
提案: supervision 内の処理別時間、I/O、cgroup/PBS の外部資源情報を記録する。現行 wave の scope 外・裁定候補。

**所見 2: F285 B の metering、`-9`、validator failure は相互に原因分離できない**

分類: 判定力  
深刻度: Major  
根拠: `tools/codex_worker_launch.py:1443-1467` は process exit を先に処理し、`evidence_forced_stop` の記録は `:1498-1507` の後段にある。`tools/codex_worker_launch.py:1182-1208` の `_terminate` は residual と boolean だけを返し、`tools/codex_worker_launch.py:1219-1225` の `_validator_rc` は詳細な `failures` を捨てて `0/1` にする。  
**失敗シナリオ:** 外部 OOM、scheduler の SIGKILL、launcher の kill、自然終了がいずれも `codex_exit_code=-9` または同等の疎な値になる。validator の `1` も、実行失敗の直接原因か後続の副作用か判定できない。  
提案: 終了主体、送信 signal、終了を観測した時刻、validator の bounded failure code、外部資源情報を sidecar に追加する。詳細な termination helper の変更は scope 外・裁定候補。

**所見 3: F285 C は launcher 側だけ計装しても termination の判定根拠が残らない**

分類: 全層 scope  
深刻度: Major  
根拠: `stage2-plan.md:90-122` は launcher 内の `_group_member_count` に4種類の source code を追加する計画だが、実際の kill 判定は `tools/dev_waves/worker.py:146-163` の `_group_members` と `:181-204` の `terminate_verified_group` にも依存する。後者は `return True` / `return False` に縮約する。  
**失敗シナリオ:** worker helper の `/proc` scan が一部 entry を `continue` で捨てる。launcher は residual と `termination_verified` を得ても、scan error、TERM、KILL、実際の残留を区別できない。  
提案: `worker.py` に member identity、scan error、TERM/KILL、再確認結果を記録する統合 seam を設ける。現行 plan の対象外であり、scope 外・裁定候補。

**所見 4: 親 brief の「失われている5点」は終了主体と外部資源の証拠を落としており、6点目が必要**

分類: 一般化  
深刻度: Major  
根拠: `brief.md:51-59` の5点には `evidence_forced_stop` はあるが、終了主体や signal はない。`t1005-package.md:88-102` も `codex_exit_code=-9` が外部 OOM/scheduler と同型になると記載する。実装の receipt も `tools/codex_worker_launch.py:1305-1308` では `codex_exit_code` と boolean のみである。  
**失敗シナリオ:** 次の再発で `-9` と `termination_verified=false` が残るが、誰が終了させたか、外部資源制限か、launcher の強制停止かを判定できず、21回目も未確定になる。  
提案: 「終了主体・signal・外部 kill/resource evidence」を独立した観測量として追加する。これは scope 外・裁定候補。

**所見 5: malformed `/proc` stat は `residual=None` にならず、残留ゼロとして誤認され得る**

分類: 判定力  
深刻度: Major  
根拠: `tools/codex_worker_launch.py:1154-1159` は `end <= 0` や `len(fields) <= 2` の場合に error を記録せず、その entry を黙って無視する。`stage2-plan.md:109-113` もこの挙動を変更しない方針である。`tools/codex_worker_launch.py:1211-1216` は戻り値が `0` なら `termination_verified=True` にする。  
**失敗シナリオ:** malformed stat のため実在する group member が数えられず、`residual=0` と `termination_verified=true` が保存される。sidecar にも「観測不能」情報が残らない。  
提案: `proc_stat_malformed` を記録する。意味を unknown に変えるなら制御仕様も変わるため、scope 外・裁定候補。

**所見 6: brief §4⑤の「attempt 個別情報がない」は既存コードに対する誤認**

分類: 一般化  
深刻度: Major  
根拠: `brief.md:47-49,59` は diagnostic が limits/actuals だけで attempt 個別情報を出さないとする。しかし `orchestrator/tests/test_codex_worker_launch.py:316-339` は `receipt["attempts"]` を列挙し、`limit_trigger`、`codex_exit_code`、`validator_rc`、residual、termination 等を出力する。`orchestrator/tests/test_codex_worker_launch.py:479-492` で16 KiBに制限される。  
**失敗シナリオ:** 既存の attempt summary を「失われた観測」として扱い、実際には新規でない情報を計装成果として数える。なお、完全な file body と sidecar は依然として不足している。  
提案: brief を訂正し、新規項目を「full body、終了主体、source code、phase、全 latch」と明確化する。

**所見 7: preflight failure と launcher 外部 kill では sidecar が存在しない**

分類: 全層 scope  
深刻度: Major  
根拠: `stage2-plan.md:182-204` は `_preflight_run` を既存の `try` の外に残し、preflight failure では sidecar を書かない。実装も `tools/codex_worker_launch.py:2234-2246` で `_preflight_run(args)` が `try` より前にある。既存テスト `orchestrator/tests/test_codex_worker_launch.py:2306-2337` では `attempts=[]` の launcher error になる。  
**失敗シナリオ:** hook、codex path、preflight の失敗で test harness が `LauncherReturncodeMismatch` を得る。B は tmp を退避できても、A の evidence、phase、residual、latch がない。launcher 自体が SIGKILL された場合も同じである。  
提案: `diagnostics_status=not_started` のような欠損記録を archive metadata に残すか、preflight 用の安全な最小 artifact を定義する。実装範囲は scope 外・裁定候補。

**所見 8: 退避後の receipt は絶対 path が古くなり、機械的な再読込が壊れる**

分類: 運用  
深刻度: Major  
根拠: plan は `stage2-plan.md:245-274` で `tmp_path` 全体をコピーするが、receipt は `tools/codex_worker_launch.py:1278-1283`、`:1295-1303` で `path=os.fspath(...)` の絶対 path を保存する。test 側の各 path は `orchestrator/tests/test_codex_worker_launch.py:983-997` で `tmp_path` 配下に作られる。  
**失敗シナリオ:** pytest の tmp teardown 後、archive 内の `receipt.json` が消滅した元の `/tmp/pytest...` を指す。人間は手動で探せても、receipt checker や replay は archived file を読めず、1時間以内の原因到達を保証できない。  
提案: 元の exact bytes は保存しつつ、archive 相対 path 版と `path-map.json` を生成し、archive 上で checker が通ることを検証する。reader/rebase の追加は scope 外・裁定候補。

**所見 9: 21件同時退避の容量と退避時間に上限・原子性がない**

分類: 運用  
深刻度: Major  
根拠: `stage2-plan.md:233-243,272-274` は `pytest_runtest_makereport` 内で tmp 全体を同期コピーする。`tools/codex_worker_launch.py:427-443` の `_hash_file` は無制限時に全体を読み、`:1044-1052` の rollout offset は増え続ける。`tools/codex_worker_launch.py:72-73` の上限は JSON 全体と1行だけで、archive 全体の上限ではない。  
**失敗シナリオ:** 21 worker が大きな rollout、stdout、manifest を同時コピーし、Lustre の容量・帯域を圧迫する。退避が F57 のwall edgeを押し、ENOSPCやEIOで途中ディレクトリだけ残る。  
提案: file数/総byte/一run quota、timeout、残容量確認、`.complete` marker、退避失敗時に元の test failure を保持する処理を定義する。retention/GC は scope 外・裁定候補。

**所見 10: archive root の環境変数は計算ノードへ届かない**

分類: 全層 scope  
深刻度: Major  
根拠: plan は `stage2-plan.md:245-253` で `IZANAGI_LAUNCHER_FAILURE_ARTIFACT_ROOT` を root override とする。一方 `tools/pegasus/dispatch_compute.py:59-72` の tests allowlist にこの変数がなく、`:1390-1494` で allowlist 外の環境変数を request から除外する。compute 側は `:588-600` の `requested_env` だけを child env に追加する。  
**失敗シナリオ:** login node で durable root を設定して `python3 tools/run_tests.py` を実行する。dispatch 後の pytest はその変数を受け取らず、既定の worktree 内 `output/runs` に退避する。archive 自体は発火しても、指定した受入先には残らない。  
提案: allowlist、request、compute child の三層を通し、実際の root を metadata に保存する。runner/dispatch の変更は scope 外・裁定候補。

**所見 11: 退避物を列挙・読む run-level consumer が scope にない**

分類: 全層 scope  
深刻度: Major  
根拠: `stage2-plan.md:354-375` の consumer は launcher、test file、`tools/dev_wave_codex.py` とその tests だけで、`run_tests.py`、dispatch、human/next-wave reader を含まない。退避 layout も `stage2-plan.md:245-274` の leaf 単位で、root index を定義しない。`tools/run_tests.py:867-927` は task-run metadata と終了値を記録するだけである。  
**失敗シナリオ:** 21件の leaf は存在するが、どの worker/nodeid がどこにあるかを受入結果から辿れない。worktree cleanup 後に人間や次 wave が手作業で探すことになり、1時間以内の原因到達を保証できない。  
提案: run-level manifest、archive status、worker/nodeid/PBS/job mapping、読むためのCLIまたは次 wave連携を定義する。scope 外・裁定候補。

**所見 12: 「48並列・21件同時」は現行の `run_tests.py` からは保証されない**

分類: 一般化  
深刻度: Major  
根拠: `tools/run_tests.py:60-62` は `_NPROC_CAP=32`、`:215-229` は未指定時にこの cap を使い、`:1887-1903` で pytest を構成する。plan は `stage2-plan.md:270` で48並列を前提にする。  
**失敗シナリオ:** affinity が48でも `IZANAGI_TEST_NPROC` を指定しない通常の `python3 tools/run_tests.py` は32 workerになる。21件同時の容量、競合、wall edgeへの影響を現行受入条件として再現できない。  
提案: effective nproc を受入 metadata に記録し、48を検証する場合は明示的に設定する。変更は scope 外・裁定候補。

**所見 13: failure-side 21件だけから「常に3秒縁で全属性が原因」と一般化できない**

分類: 一般化  
深刻度: Major  
根拠: `t1005-package.md:25-32` は failure-side の3 burstだけを表にし、`:144-146` は green distribution が未測定と明記する。一方 `:47-53` は一つの説明が全属性を説明するとしている。  
**失敗シナリオ:** green run は十分なwall余裕があり、failure runだけが特定のnodeやI/O条件に偏っている。現状の表から常時発火条件や単一原因を断定すると、計装後も誤った修正対象を選ぶ。  
提案: brief の表現を「整合する仮説」に下げ、green/failure双方のwall、phase、node、resource分布を別途測定する。

**所見 14: 環境変数 transport の欠落変異は、計画テストでは帰属できない**

分類: 変異  
深刻度: Major  
根拠: plan の archive test は `stage2-plan.md:313-316,352` の local exact-byte、sentinel、collision 中心で、consumer list は `:354-375` の範囲に留まる。dispatch allowlist は `tools/pegasus/dispatch_compute.py:59-72` にある。  
**失敗シナリオ:** dispatch allowlist から root variable を削除しても、local default root のテストは緑になる。受入計算ノードだけが別 root に書き、mutation がこの wave の変更による失敗として検出されない。  
提案: dispatched child で env と実際の archive root を確認する mutation test を追加する。dispatch検査は scope 外・裁定候補。

**所見 15: path rebase の欠落変異は、exact-byte test では検出できない**

分類: 変異  
深刻度: Major  
根拠: plan は `stage2-plan.md:313-316` で exact bytes、`:352` で sentinel を確認するが、receipt の path 形式は `tools/codex_worker_launch.py:1295-1303` の絶対 path のままである。  
**失敗シナリオ:** archive helper が全ファイルを正しくコピーするが、receipt の path を元の tmp path のままにする。planned test は通る一方、tmp teardown 後の replay/checker は失敗する。  
提案: copied bundle に対して receipt checker を実行し、全 path が archive 内で解決できることを mutation test の受入条件にする。reader/rebase自体は scope 外・裁定候補。

**所見 16: termination helper の変異は、launcher helper だけを差し替えるテストでは検出できない**

分類: 変異  
深刻度: Major  
根拠: plan の residual test は `stage2-plan.md:300-308` で launcher 側 callback を対象にする。既存テストも `orchestrator/tests/test_codex_worker_launch.py:2629-2690` で `_group_member_count` を monkeypatch するだけで、実際の `tools/dev_waves/worker.py:146-204` は通らない。  
**失敗シナリオ:** `worker.py` の scan error handling、TERM/KILL分岐、member identity確認を壊しても、planned tests は緑になる。F285 C の attributionだけが壊れたまま出荷される。  
提案: worker helperまで通す integration seam または実プロセスでの termination trace test を追加する。現行 plan の全層 scope 外・裁定候補。

## 総括

v1 は A の即時 wall latch と一部の phase/receipt binding は改善するが、F285 B/C の原因判定、preflight failure、外部終了主体、worker termination helper、archive replay を未解決のまま残す。

特に、親 brief の5点列挙には「終了主体・signal・外部 resource evidence」という6点目が必要であり、⑤の attempt 個別情報については既存 diagnostic が既に一部取得している。計装層だけでなく、dispatch transport、archive reader、run-level index、容量管理まで含めない限り、次の再発を1時間以内に判定できる成果物とは言えない。