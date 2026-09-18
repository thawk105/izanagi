# 段 6 裁定 (review A = 過剰・削除、review B = 逐語照合・実効性) — 2026-09-18 11:52 JST

統合 commit 20aca3006 に対する所見。両レビューとも NO-GO。must-fix は A1=B2 (TERM test)、A2=B3 (signal 時の rc 上書き)、B1 (環境消去)。

| # | 所見 | 判定 | 採否 | fix |
|---|---|---|---|---|
| A1/B2 | 契約 test の TERM 経路が計算ノードで赤 (SIGTERM SIG_IGN 継承、F1012)。受信側 bash を起動する前の子で SIG_DFL + unblock が要る | real (焦点走 5523.nqsv で実測) | 採用 | F1: `_bash` に `preexec_fn` (SIGTERM/SIGHUP/SIGINT を SIG_DFL、`pthread_sigmask(SIG_UNBLOCK)`)。既存例 `test_pegasus_dispatch_compute.py::test_real_child_signal_is_published_from_wait_status` |
| A2/B3 | J:189–190 が driver rc=0 かつ signal 観測で JOB_RC を 143/129/130 へ上書き — 裁定 §4.2「driver rc は保存して伝播」の超過 | real | 採用 | F2: 190 行を削除し `JOB_RC=$DRIVER_RC`。signal は `reason=signal_observed` に残す。test に child `kill -TERM "$PPID"; sleep 0.1; exit 0` → rc 0 / reason signal_observed の正例を足す |
| B1 | 環境消去が `PYTHONPATH PYTHONHOME PYTHONSTARTUP LD_PRELOAD LD_LIBRARY_PATH` の 5 個だけ — 裁定 §4.2 は `PYTHON*/LD_*/GIT_*` | real (逐語) | 採用 | F3: J/S の `clean_environment` を `${!PYTHON@}` `${!LD_@}` `${!GIT_@}` の prefix 全件 unset に。test で汚染 env (`PYTHONWARNINGS`, `LD_AUDIT`, `GIT_DIR`) を与えて実行観測 |
| A7 | `test_checkout_and_input_binding` の X_OK 負例は bytes 不一致のまま chmod するので実行権検査の独立証拠にならない | real | 採用 | F5: 元 bytes に戻してから `chmod 0600` |
| A7/B6 | 文字列 pin は接続変異 (`if false; then check_checkout; fi`、`cmake  --build` の二重空白) に生存。checkout / spec / binary の本番接続と submitter の main flow は実行観測されていない | real (should) | 採用 | F6: J の top-level (210〜233 行) と S の top-level (257〜283 行) をそれぞれ `main()` に包み、`test_gate_order_and_calls` と同型の stub 到達 test を J (bootstrap→…→admit_and_run の呼出し列) と S (parse_args→…→submit_or_dry_run の呼出し列) に足す。文字列 pin は「静的な限定検査」の comment を付けて残す |
| B6 | finalize 専用の header 不一致負例が無い | real (should) | 採用 | F6 に含める: `test_finalize_preflight_requires_terminal` に片窓 `loaded_head` 不一致 → `loaded_head_mismatch` を足す |
| 親 | login の `bash -n` が hook で拒否され構文検査の実走が無い | real | 採用 | F4: `test_scripts_parse` = `subprocess.run(["bash","-n",path])` を両 script に (runner = 計算ノードで実走) |
| A3 | runbook「9 job すべて同じ HEAD」は申し送り 2 (各 spec の 3 段) より強い | real (should) | 採用 (docs、親) | §7.8 を「各 spec の w1・w2・finalize は同じ H。3 spec を同じ H から投げるのは運用の単純化であって要件ではない」に |
| A8 | runbook「実配送を確認してから最初の実投入」は循環 | real (should) | 採用 (docs、親) | 「次の測定 wave の初回実行で確認し記録する」に |
| B4 | runbook に SIG_IGN 継承の帰結 (record_signal 未発火、walltime で KILL、terminal 無し) を書く | real (should) | 採用 (docs、親) | §7.8 未検証の前提に追記 |
| B5 | M1/M5 の期待 node 集合が不完全 (test_hooks の login/suspect bit・sanctioned 集合、`test_no_build_or_output_replacement`) | real (should) | 採用 | probe 走 (SURVIVED 期待・expected_nodes 空) で完全集合を採ってから本走 (DW-M08) |
| A4 | finalize では `nm`/`pgrep` は不要 (loader は sha だけ、現物 1136〜1140 で確認) | real (should) | 不採用 (記録) | 集合を mode で分けない。計算ノードに `nm`/`pgrep` は実在 (焦点走・過去 job)。単純さを優先。insight に「finalize では過剰」と記録 |
| A5 | J の spec 名 3 本の再列挙は二重管理 | should | 不採用 (記録) | `FP_WINDOW_ID` の形の検査に workload が要る。submitter と同じ閉集合を 2 箇所に持つ費用は小さい |
| A6 | `driver_stdout_sha256` と `qsub.rc` は余分 | should | 不採用 | `driver_stdout_sha256` は裁定 §4.2 の field 集合に明記済み (review A の「§4.2 は指定していない」は誤読)。`qsub.rc` は `submit_floor.sh` の型 |
| B7 | hostname の lowercase 化と `--help` alias は裁定の逐語より広い | nit | 採用 (裁定の補正) | §4.2 に「第一 label を lowercase 化してから完全一致 (site_policy._first_label と同じ)」、§4.3 に「`-h`/`--help`」を補う。実装は変えない |
| A9/B8 | 前段の複製は driver 変異を mask する。M1〜M10 は shell/登録簿/docs の kill に限定 | 情報 | 記録 | 段 4 A6 のとおり |

段 4 の規模上限: fix は所有 5 path (J・S・T + 変更なしの registry / test_hooks) の内側。新規 file・新規 gate なし。
