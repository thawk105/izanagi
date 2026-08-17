## _attempt_loop の反復作業

判定: 現象は捕捉済みだが、[T-1298] の直接原因は未分離である。正常経路では attempt 1 と attempt 2 の作業量を増やす分岐はない。

| 作業 | 根拠 | attempt 間の量 |
|---|---|---|
| `codex` 実体の再 hash | `tools/codex_worker_launch.py:1670`、`tools/codex_worker_launch.py:660` | 同じ全 bytes。変更時は遅くなるのでなく `LaunchError` |
| attempt artifact の path 構築・存在検査・handle 作成 | `tools/codex_worker_launch.py:1673`、`:1676`、`:1679` | 3 path 検査、stdout/stderr の 2 open で同じ |
| argv、state、diagnostics の作成 | `tools/codex_worker_launch.py:1681`、`:1698`、`:1706` | 同じ |
| cwd の Git root 検証 | `tools/codex_worker_launch.py:1764`、`:277`、`:280` | attempt ごとに `git rev-parse --show-toplevel` 1 回。同じ |
| hook 配線・5 pinned file の再検証 | `tools/check_codex_hooks.py:98`、`:129`、`:306` | 同じ file 集合、同じ hash |
| hook 検証中の Git | `tools/check_codex_hooks.py:235`、`:259`、`:281` | 正常 checkout なら `rev-parse` 2 回と `cat-file blob` 5 回。外側の 1 回を含め各 attempt 8 subprocess |
| wall 判定と boundary 記録 | `tools/codex_worker_launch.py:1765`、`:1774` | clock 読み取り 1 回で同じ |
| docs authority snapshot | `tools/codex_worker_launch.py:2351`、`tools/dev_waves/launch_authority.py:334`、`:343` | **attempt ごとには 0 回**。`_preflight_run` で一度だけ取得し、`:1756-1757` は既存 snapshot の転記 |
| `git` repository binding と `codex --version` | `tools/codex_worker_launch.py:2310`、`:2319`、`:2341`、`:2342`、`:2429` | attempt 前に一度だけ。retry では繰り返さない |

spawn 後の `observe`、rollout 探索、manifest append は `tools/codex_worker_launch.py:1719` 以降で attempt ごとに行われるが、子の出力量に依存する。reap、final drain、fsync、seal も `:1898`、`:1938`、`:1986`、`:2018` で繰り返される。

重要なのは計測境界である。`attempt_started_ns` は hash、artifact 準備、argv 作成の後の `tools/codex_worker_launch.py:1698` で設定される。sidecar の `phase_duration_s.attempt_preflight` はその後の `attempt_state_created` から `attempt_preflight_completed` までしか測らない (`tools/codex_worker_launch.py:420`、`:522`、`:1775`)。さらに evidence deadline もこの時刻を起点にする (`tools/codex_worker_launch.py:1797`)。

したがって、一次資料の attempt 1 `0.29` 秒、attempt 2 `1.10` 秒という preflight 差は、sidecar の `attempt_preflight` を指す限り、codex executable 再 hashそのものでは説明できない。

## 3.6 倍を説明する仮説

1. hook 検証内の特定の Git / filesystem 操作が attempt 2 だけ遅い。

   8 回の Git subprocess と5 fileの読み取り回数は変わらないが、共有 FS の metadata、Git object、remote filesystem の待ち時間は変わり得る。通常の page cache の単純な cold start なら同じ file を二度読む attempt 2 が遅くなる方向とは合わず、cache eviction または FS server 輻輳が必要である。

   既存の観測量は `phase_duration_s.attempt_preflight` と boundary 時刻だけ (`tools/codex_worker_launch.py:407`、`:468`)。必要なのは hash、外側の `git rev-parse`、各 `_run_git_raw`、各 file read の個別 duration、returncode、bytes である。これは新規観測量である。

2. attempt 1 の残存 process、reap、seal が attempt 2 の FS / CPU を圧迫する。

   retry は attempt 1 の `_terminate` または `_normal_reap`、final drain、handle close、seal の後で初めて行われる (`tools/codex_worker_launch.py:1898`、`:1938`、`:1985`、`:2018`; retry 呼び出しは `:2519`)。従って「待機が attempt 2 と同時に走る」はコード上は誤りだが、残存 process や attempt 1 の大量 artifact I/O が後続へ影響する可能性は残る。

   sidecar は reap、final drain、seal の phase、`residual_observation`、送信 signal を既に記録する (`tools/codex_worker_launch.py:475`、`:489`、`:496`)。残存 process の PID/PGID、reap 中の process 数、wait の個別 duration は新規観測量である。

3. attempt 1 に依存しない共有 FS / cache / scheduler 圧力である。

   48 worker 全体の並行 read、Git subprocess 数、page fault、I/O wait、cgroup の CPU/I/O pressure が attempt 2 の開始時だけ悪化した可能性がある。sidecar の aggregate phase 時間では外乱と内部処理を区別できない。

   必要なのは major/minor page fault、process CPU time、`/proc` I/O、cgroup pressure、同時 Git process 数、filesystem mount 情報である。これらは sidecar にない。

artifact 保存は sidecar、attempt stream、stderr、output、receipt、manifest を保存するだけで (`orchestrator/tests/test_codex_worker_launch.py:144`、`:156`、`:312`)、内部 syscall や外部負荷を追加記録しない。3 仮説を区別するには計装追加が要る。

## 決定的な再現手順

結論: 現行コードだけで、単独実行により実 FS 上の 3.6 倍を必ず再現する手順はない。

- `max_attempts=2` は固定できる。`_run_supervised` が `range(1, max_attempts + 1)` を使う (`tools/codex_worker_launch.py:2519`)。既存の `test_max_attempts_never_spawns_extra_attempt` も2 attemptを生成する (`orchestrator/tests/test_codex_worker_launch.py:4501`、`:4519`)。
- しかし `FAKE_SEQUENCE` の mode 選択は子 process 内 (`orchestrator/tests/test_codex_worker_launch.py:1271`) で、fake の `0.04` 秒待機も spawn 後 (`:1420`、`:1421`) である。preflight は spawn 前 (`tools/codex_worker_launch.py:1764`、`:1778`) なので、fake の sleep では preflight を遅くできない。
- 背景負荷や `dd` などで共有 FS を混ませる方法は、3.6 倍を保証せず、scheduler の偶然を再現条件にするだけである。
- `validate_installation` や Git runner を2回目だけ人工的に止める monkeypatch は可能である。既存テストも validator monkeypatch と logical clock を使っている (`orchestrator/tests/test_codex_worker_launch.py:3419`、`:3423`、`:3489`、`:3497`)。ただし、それで得られるのは synthetic な遅延であり、実際の原因の再現ではない。

計算ノードで実走できる既存の対照は、`python3 tools/run_tests.py --force-dispatch -n 1 orchestrator/tests/test_codex_worker_launch.py -k test_hook_preflight_is_rechecked_before_each_retry` である。ただしこれは hook 再検証を2回確認するだけで、3.6 倍を再現する手順ではない。今回は実走していない。

## 決定性 regression の形

[T-1298] が外部 FS 輻輳や page cache の性能差そのものなら、sleep、負荷、wall-clock 閾値に依存せず「修正前は必ず赤、修正後は必ず緑」とするテストは書けない。

書けるのは、原因が構造的な場合だけである。

- worker-local path を使う修正なら、operation recorder で attempt ごとの path と Git argv を固定し、real-repo smoke を別 test に残す。
- 呼び出し順や回数の修正なら、logical clock と deterministic fake backend で検査する。
- hook 再検証を削って速くする案は不可。既存の `test_hook_preflight_is_rechecked_before_each_retry` が validator の2回呼び出しを要求する (`orchestrator/tests/test_codex_worker_launch.py:3409`、`:3430`)。

現時点では production に preflight collaborator や個別 timer の注入点がない。従って、T-1298 の原因が性能・外乱である限り、決定性 regression は「書けない」。この条件を満たせない実装は入れるべきでない。

## 所見

1. **[T-1298] は現象の確認までは到達済みだが、原因分離までは到達していない。** 3 bundle は全て attempt 2 の evidence-grace 枯渇、launcher 自身の SIGTERM/SIGKILL、`limit_trigger` 無しを示す (`refs/t1298-primary-sources.md:21`、`:35`、`:40`)。しかし sidecar に個別 I/O 時間がないため、現行資料だけで hash、hook、Git、FS 輻輳を選べない。成果物は「原因分離未了」のままであり、修正根拠にはならない。

2. **codex executable 再 hash を直接原因とする親 brief の provisional 説は、測定境界と整合しない。** hash は attempt clock と evidence deadline の前に行われる (`tools/codex_worker_launch.py:1670`、`:1698`、`:1797`)。成果物影響は、hash を理由に evidence grace を上げる案を却下できること。

3. **「次の normal-control 再発まで待つ」は、現行 artifact のままでは情報を増やさない。** 一次資料は既に3 bundleで機序を確定し、残りを「3.6倍の内訳」と明記している (`refs/t1298-primary-sources.md:94`、`:100`、`:107`)。未計装の再発は同じ aggregate phase 値を増やすだけである。成果物影響は、受入1走と lease 窓を消費し、台帳更新を遅らせること (`refs/rulings.md:28`、`:48`; `brief.md:64`)。

4. **待たない危険はあるが、直ちに budget を上げる理由にはならない。** 誤った原因で evidence grace を広げれば、遅い preflight を受理する方向へ集合を広げる (`refs/t1298-primary-sources.md:54`、`:109`)。正しい次手は無計装の再発待ちではなく、個別 timer と外乱観測を持つ焦点 probe である。

5. **親の [T-1298] への方向転換は、診断目的なら妥当だが、production 修正まで含めると過大である。** brief の成果物は `orchestrator/tests/` の test/fixture 編集で、production 変更は S2 の特定条件に限定される (`brief.md:69`、`:71`)。`_attempt_loop` の再設計、hook 検証の省略、受入直列化、budget 引き上げは別 P2 task または段4裁定に戻すべきである。

6. **S2 は現行 plan の「追加変更なし」が妥当である。** plan は `2da49c56` 後の3 nodeと mutation nodeについて、mask復元、Event、wakeup-fd、ready 後の handler 設置を根拠にしている (`plan.md:130`、`:140`、`:150`)。ただしこの段では pytest を実走していないため、緑や解消済み受入結果を主張してはいけない。

## この wave が今日届けられる最小の成果

段4で選べるのは次の3択である。

- 推奨: 実装差分ゼロ。S2 は追加変更なし、S1 は budget・retry・skip・直列化を行わず、[T-1298] を「effect confirmed / attribution open」として記録する。
- 診断を続ける場合: production の受理集合を変えない焦点 probe を新設し、hash、hook、Git、reap、外部 FS の個別観測だけを追加する。これは scope 拡張なので段4で明示裁定する。
- T-1298 を別 wave に送る場合: 今 wave は既存の `test_hook_preflight_is_rechecked_before_each_retry` と S2 の前提解消を台帳へ確定するだけにする。

いずれも既存テストの期待値変更、evidence grace の一律引き上げ、受入直列化は含めない。

## 総括

- `_attempt_loop` の正常な preflight は attempt 1 と2で同じ仕事量である。
- 成功経路では attempt ごとに Git subprocess が8回走るが、docs authority snapshot は一度だけである。
- sidecar の preflight 計測は executable hash より後に始まる。
- 3 bundle は evidence-grace 型を確定したが、3.6倍の内訳は未確定である。
- 単独で実 FS 上の3.6倍を必ず再現する現行手順はない。
- 次の未計装 bundleを待つ費用は高く、診断 probeなしでは情報が増えない。
- 最小成果は実装差分ゼロと、[T-1298] を未解決として正しく記録することである。
