## 実測した現状

静的検査だけを行った。ファイル編集、pytest 実走、緑の主張はしていない。

### S1 の実体

- F57 の過去事象は、成功を期待した normal launcher が `rc=1`、launcher の stdout・stderr は空、単独再走は緑というものだった。該当 node は移動しつつ、一部が再発している (`refs/f57-full.md:3-35,49-76,100-114`)。
- 現行の `_base_command` は `max_wall="3"`、evidence grace `1.0`、termination grace `0.05`、poll interval `0.01` を渡す (`orchestrator/tests/test_codex_worker_launch.py:1542-1555,1610-1635`)。
- fake の `FAKE_MODE` 分岐は `cwd_missing`、`payload_decoy`、`no_thread`、`delayed_thread`、`no_rollout`、`cached_bad`、`cli_exact`、`token_wait`、`retry_reject`、`retry_wait`、`final_drain`、`rollback`、`rollback_equal_cli`、`null_info`、`no_token`、`id_change`、`multiple_sessions`、`id_change_wait`、`inconsistent`、`child_error`、`term_success`、`sigterm_ignore`、`setsid_escape`、`manifest_while_running`、`late_writer`、および通常経路である (`orchestrator/tests/test_codex_worker_launch.py:1271-1535`)。
- 通常 fake にも rollout 作成前の `0.04` 秒待ちがあり (`orchestrator/tests/test_codex_worker_launch.py:1421`)、`manifest_while_running` は `0.5` 秒、`late_writer` は別 process で `0.5` 秒を使う (`orchestrator/tests/test_codex_worker_launch.py:1520-1535`)。

### 固定されている時間予算

| 予算 | 定義・使用箇所 | 被検査性質か、運び手か |
|---|---|---|
| wall `3` 秒 | `test_codex_worker_launch.py:1553,1610-1611`。production の監視点は `tools/codex_worker_launch.py:1595-1607,1764-1773,1830-1838,1854-1876,2432-2466,2556-2581` | wall 発火を検査する node では被検査性質。それ以外、特に名指しされた四 node では運び手 |
| evidence grace `1.0` 秒 | `test_codex_worker_launch.py:1630-1631`。attempt 開始時刻を preflight 前に採り (`tools/codex_worker_launch.py:1698-1705`)、deadline を `started_ns + grace` とする (`tools/codex_worker_launch.py:1797-1800`) | `test_rollout_missing_after_grace_is_stopped_and_not_accepted` と `test_thread_missing_after_grace_kills_process_group` では被検査性質 (`test_codex_worker_launch.py:5926-5986`)。normal control では運び手 |
| termination grace `0.05` 秒 | `test_codex_worker_launch.py:1632-1633`、使用は `tools/codex_worker_launch.py:1898-1918,1943-1968` | 強制終了、残存 process、送信 signal を検査する node では被検査性質。四つの normal control では運び手 |
| poll interval `0.01` 秒 | `test_codex_worker_launch.py:1634-1635`、使用は `tools/codex_worker_launch.py:1867-1892` | 監視処理の運び手。ただし limit・evidence 強制停止 node の観測順へ影響するため一律変更しない |
| launcher subprocess 上限 `10` 秒 | `_run_launcher_subprocess`、`_communicate_launcher`、unordered 版 (`test_codex_worker_launch.py:1122-1146,1149-1169,1204-1226`) | pytest のハング防止。`rc=1` は timeout ではないので今回の修正対象外 |
| check-receipt 上限 `10` 秒 | `test_codex_worker_launch.py:3543,3637,5179,5232,5282,5297,5323,5356,5388,5410,5416,5441,5460,5660,6019,6056,6064,6083,6099` | checker を運ぶ watchdog。名指しされた receipt 二 nodeでも数値自体は検査していない |
| nested pytest 上限 `30` 秒 | artifact 配線検査 (`test_codex_worker_launch.py:2180-2189,2238-2247`) | artifact reporter のハング防止 |
| fake barrier `5` 秒、identity 子待ち `2` 秒 | `test_codex_worker_launch.py:1274-1284,1459-1467` | fixture 内 handshake の watchdog。F57 対策として延長しない |
| PID 消滅 `3` 秒、child PID 登録 `2` 秒 | `test_codex_worker_launch.py:2347-2351,3798-3806` | process cleanup の検出力を持つため変更しない |
| manifest 観測 `3` 秒 | `test_codex_worker_launch.py:5815-5833` | 数値は watchdogだが、「manifest 公開時に leader が生存」の観測を運ぶ。延長で直さない |
| late writer 観測 `3` 秒 | `test_codex_worker_launch.py:6010-6016` | late write の発生を待つ watchdog。今回の対象外 |
| thread barrier/join `2` 秒 | `test_codex_worker_launch.py:4057-4075` | termination concurrency 単体検査の watchdog |
| production preflight の git 上限 `5` 秒 | `tools/codex_worker_launch.py:277-300,2328-2336` | launcher の fail-closed 契約。tests 側の予算変更対象ではない |

`expected_returncode=99` の完全な集合は `test_codex_worker_launch.py:2570,2605,2616,2627,2753,2773,2790`。前四件は順に metering、Codex rc、validator、evidence の診断を検査し、後三件は returncode assertion の配線を故意に発火させる (`test_codex_worker_launch.py:2566-2635,2734-2808`)。したがって、brief が例示した `:2570` と `:2627` は wall 発火を主張する case ではない。

実際に wall 契約を主張する集合は次であり、いずれも予算を変更しない。

- `test_attempt_preflight_delay_exhausts_wall_clock_before_spawn` (`test_codex_worker_launch.py:3476-3509`)
- `test_sigterm_ignoring_child_is_killed` (`test_codex_worker_launch.py:3780-3826`)
- `test_launcher_diagnostics_limit_conditions_negative_and_exact_boundary` ほか limit 判定三 node (`test_codex_worker_launch.py:4310-4418`)
- `test_launcher_process_wall_clock_includes_version_preflight` (`test_codex_worker_launch.py:4540-4564`)
- `test_receipt_staging_wall_overrun_flips_to_not_accepted_and_removes_output` (`test_codex_worker_launch.py:4683-4721`)
- `test_receipt_audit_wall_overrun_flips_to_not_accepted` (`test_codex_worker_launch.py:4724-4761`)

### 共有状態三経路

1. `~/.codex/sessions`

   - fake は `CODEX_HOME/sessions` だけへ書く (`test_codex_worker_launch.py:1290`)。
   - fixture は `CODEX_HOME` を node 固有の `tmp_path/codex-home` に置換し、同じ場所を明示的な `--sessions-root` にも渡す (`test_codex_worker_launch.py:1575,1626-1627,1642`)。
   - launcher の探索も `args.sessions_root` を使用する (`tools/codex_worker_launch.py:1719-1728,2410`)。`~/.codex/sessions` fallback は引数が無い場合だけである (`tools/codex_worker_launch.py:3837-3843`)。
   - 結論: tmp 外へ出ない。共有状態候補から除外できる。

2. docs authority snapshot

   - `_base_command` の既定 `repo_root` は共有 worktree の `_ROOT` (`test_codex_worker_launch.py:1557,1598-1601`)。
   - 実体は `docs/dev-wave/operations.md` と `docs/dev-wave/workers.md` (`tools/dev_waves/launch_authority.py:17-20`)。
   - launcher は `_preflight_run` でその repo を snapshot する (`tools/codex_worker_launch.py:2347-2353`)。commit blob を `git show` で読み、live working file と byte 比較する (`tools/dev_waves/launch_authority.py:331-345,369-385`)。
   - 別 worktree の未 commit 差分はこの worktree の file や HEAD を変えない。同じ worktree の変更なら byte 比較が `AuthorityError` となり、main は `NG:` を stderr に出して rc=2 を返す (`tools/codex_worker_launch.py:3844-3849`)。したがって silent rc=1 を生む内容競合ではない。
   - ただし共有 filesystem の read I/O は競合しうる。特に各 attempt の hook 再検証は attempt clock 開始後に共有 repo を読む (`tools/codex_worker_launch.py:1698-1705,1764-1777`)。これは T190 が観測した preflight 肥大と整合するが、内容の共有状態とは別問題である。

3. receipt / manifest

   - 既定は各 `tmp_path` の `receipt.json` と `manifest.json` (`test_codex_worker_launch.py:1571-1585,1622-1625`)。
   - pytest の `tmp_path` は node ごとに分離される。明示的に同じ manifest を渡す concurrency test 以外に worker 間共有はない。
   - 結論: F57 の normal control に共有 receipt 競合はない。

### T190 artifact

失敗 artifact は既に実装済みである。

- 保存先は共有 FS の `output/runs/pytest-launcher-failures` (`test_codex_worker_launch.py:54`)。
- sidecar、attempt events、attempt stderr、attempt output、receipt、manifest を優先保存する (`test_codex_worker_launch.py:117-160`)。
- call failure を autouse plugin が捕捉し、archive 自身の失敗で元の赤を隠さない (`test_codex_worker_launch.py:599-649`)。
- returncode mismatch 本文にも receipt、stop reason、各 predicate、予算、host、xdist worker が入る (`test_codex_worker_launch.py:964-1119`)。

この機構は既に48-worker全走で三 bundleを保存し、retry attempt 2 の preflight が `1.04` から `1.11` 秒へ伸び、evidence grace `1.0` を消費した型を確定している。wall は `3.0` 秒中 `2.46` から `2.65` 秒で発火していない (`docs/worklog.md:690-703`, `docs/failures.md:2103-2140`)。ただしこれは retry attempt 2 の実測で、歴代の max-attempts 1 の normal control がすべて同じ機序だったことまでは証明しない。

## rc=1 かつ無出力の経路

`run` サブコマンドに直接の `return 1` や `sys.exit(1)` はない。grep で得られる唯一の literal `return 1` は `check-receipt` の audit 結果であり (`tools/codex_worker_launch.py:3673-3676`)、観測された `run` の経路ではない。

`run` の rc は最終 receipt の `launcher_rc` から返る (`tools/codex_worker_launch.py:2690-2701`)。rc=1 の完全な writer 経路は `_writer_truth` の次の三つである (`tools/codex_worker_launch.py:2059-2078`)。

1. 最終 attempt は accepted だが、それ以前に `evidence_status != "complete"` の attempt がある  
   `not_accepted / max_attempts / 1` (`:2065-2071`)。

2. いずれかの attempt に `limit_trigger` がある  
   `not_accepted / <limit_trigger> / 1` (`:2073-2075`)。trigger は wall、model calls、CLI reported tokens の三種で、判定点は attempt seal、natural exit、running poll、retry admission、final latch である (`tools/codex_worker_launch.py:1595-1607,1830-1838,1854-1876,2432-2466,2556-2581`)。

3. accepted attempt も limit trigger もなく、`max_attempts` を使い切る  
   `not_accepted / max_attempts / 1` (`:2076-2077`)。accepted を構成する条件は、Codex rc=0、validator rc=0、evidence complete、metering complete、residual=0、termination verified、limit 無しである (`tools/codex_worker_launch.py:1608-1617`)。したがって、このどれか一つが欠けてもこの rc=1 へ到達できる。evidence の missing/invalid は `:1354-1371`、metering の missing/incomplete/inconsistent は `:1331-1351` で決まる。

spawn 後の例外は `force_launcher_error=True` の receiptを作って rc=2 にする (`tools/codex_worker_launch.py:1943-2038,2519-2548`)。preflight の wall 超過も rc=2 (`tools/codex_worker_launch.py:2494-2514`)。その他の `AuthorityError`、`LaunchError`、`OSError`、`ValueError` は `NG:` を stderr に出して rc=2 (`tools/codex_worker_launch.py:3844-3849`)。例外ハンドラから silent rc=1 になる経路はない。

一方、Codex 子の stdout・stderr は launcher process の stream へ中継せず、attempt artifact file へ直接 redirect している (`tools/codex_worker_launch.py:1673-1680,1778-1785`)。正常な not-accepted 処理は何も print しない。sidecar 書込みまで成功した場合、上の三経路はすべて launcher stdout・stderr が空のまま rc=1 になりうる。sidecar 書込み自体が失敗した場合だけ stderr 診断を試みる (`tools/codex_worker_launch.py:2837-2855`)。

したがって、「wall gate が発火すれば stderr に診断が出るはず」という反証は現行 production には成立しない。診断先は sidecar / receipt であり、stderr ではない。反対に、空の stderr だけから wall 発火を肯定することもできない。P1 の `max_wall="3"` 説は、過去の出力署名だけでは未確定であり、T190 の保存済み三例については実測により否定されている。

## S1 プラン

現時点の推奨実装は**変更を入れず、現行 artifact 保存下で次の normal-control 再発を一度捕捉すること**である。これは既知赤扱い、retry、skip、期待値緩和ではない。D362 は原因未確定かつ main 単独で再現しない外乱を除外対象にしない (`refs/d362.md:3-9,20-22`)。

1. 次回 bundle で、次を同時に確定する。

   - receipt の `stop_reason`、全 attempt の `limit_trigger`
   - sidecar の `evidence_forced_stop`、`phase_duration_s.attempt_preflight`
   - `failed_predicates`
   - `receipt_published` 時点と wall budget
   - launcher 自身が送った signal
   - failure node の `max_attempts` と `FAKE_MODE`

2. bundle が evidence grace 型だった場合だけ、`test_codex_worker_launch.py:1542-1561` に `evidence_grace: str = "1.0"` の明示引数を追加し、`:1630-1631` の固定値をその引数へ置換する。値は次の実測後に親が定め、global default は変えない。

3. override は bundle で同じ型が確認された成功 control にだけ渡す。裁定文が名指しした四 node は予算の検査ではないが、これは変更資格を示すだけで、現時点の変更根拠にはしない。

| case | 予算が被検査性質でない根拠 |
|---|---|
| `test_all_repo_policy_reasoning_values_are_accepted` | launcher 成功後に assert するのは `requested_effort == reasoning` だけ (`test_codex_worker_launch.py:3133-3145`) |
| `test_check_receipt_recomputes_usage_actuals_from_sealed_artifacts` | launcher は準備。receipt の model calls を改変し、checker が rc=2 と sealed artifact 不一致を検出することが本体 (`test_codex_worker_launch.py:5426-5445`) |
| `test_manifest_is_appended_while_correlated_session_is_running` | 本体は manifest に session が入り、その時点で leader が生存すること (`test_codex_worker_launch.py:5801-5858`)。launcher 四予算は運び手。ただし外側の3秒 deadlineと fake の0.5秒 windowは変更しない |
| `test_check_receipt_detects_executable_identity_change` | launcher は準備。fake executable 改変後に checker が rc=2 を返すことが本体 (`test_codex_worker_launch.py:6088-6101`) |

4. `:2570,2605,2616,2627,2753,2773,2790` の診断発火 case、`:5926-5986` の evidence grace case、実 wall case一覧には override を渡さない。

5. bundle が wall trigger を示した場合も、`max_wall` を変更できるのはその exact normal-control callだけである。上記 wall 契約 node と limit nodeは絶対に変更しない。ただし現状では値を選ぶ根拠がないため、今は実装案に採用しない。

6. bundle が `attempt_preflight` の共有 repo I/O を指した場合、tests-only の次案として worker-local authority repoを検討する。その場合は `test_codex_worker_launch.py:1542-1601` の既定 repoを tmp の commit済み mirrorへ切り替える一方、real repo docs / hook 配線を読む専用 integration nodeを一つ残す必要がある。そうしないと `tools/dev_waves/launch_authority.py:369-417` と `tools/check_codex_hooks.py:98-130` の実配線検出力を失う。この案も attribution 前には実施しない。

7. sessions と receipt はすでに fixture 側で分離済み、docs は immutableな読み取りであり、現時点で「fixture 側で断てない共有 mutable state」は確認されなかった。従って xdist groupによる直列化は提案しない。

8. bundle が production の evidence deadline 定義、hook preflight順序、acceptance predicateの誤りを示した場合、`tools/` は変更せず、段4の再裁定へ返す。

## S2 プラン

S2 は現行 tipですでに解消済みと判定する。`orchestrator/tests/` への追加変更は行わない。

### `test_dev_wave_wait.py` の三 node

`2da49c56` は、maskを変更しない問い合わせで旧 maskを先に保存し、その後の blockを `finally` の保護範囲内へ移した。対象は cleanup、receipt publish、handler restore の三箇所 (`refs/2da49c56-production-diff.patch:62-102`)。現行 production でも同じ順序を確認できる (`tools/dev_wave_wait.py:2422-2448,2883-2923,3421-3438`)。

また、実 maskを monkeypatchの外から検査し、各 test の入口・出口で blocked signalを fail-closedにする autouse fixtureがある (`orchestrator/tests/test_dev_wave_wait.py:71-96`)。F306 の現行記録も、真因を負荷 raceではなく一つの testによる worker signal mask汚染として supersedeしている (`docs/failures.md:7833-7835`)。

- `test_public_main_failure_restores_handler_without_release` は、Python handler の `Event` と wakeup-fd tokenの両方を signal送信後に待つ (`test_dev_wave_wait.py:7510-7559`)。補助関数は handler実行と C側 tokenを別々の5秒 watchdogで待つ (`:99-108`)。
- `test_public_main_real_signal_after_success_uses_restored_handler` も生成 runner内で `Event.wait` と `select` を待ってから結果を assertする (`test_dev_wave_wait.py:8411-8507`)。
- `test_public_main_real_signal_releases_lease` は子 commandが親へ signalを送る (`test_dev_wave_wait.py:8379-8382`)。production handlerは command実行前に installされ (`tools/dev_wave_wait.py:3478-3496`)、subprocess完了後に rc=143 と lease消滅を検査する (`test_dev_wave_wait.py:8384-8408`)。過去の rc=70 は handler設置前 raceではなく inherited blocked maskで説明済みである。

従って三 nodeへ timeout延長、retry、追加 sleep、重複 handshakeを加えない。

### `test_mutation_worktree.py`

P3 の「ready が child handler設置完了を含意しない」はソース順序に反する。

- fake child は signal handlerを `SIGINT`、`SIGTERM` の順に設置し (`test_mutation_worktree.py:95-101`)、その後で ready fileを書く (`:102-104`)。
- testは ready fileを確認してから wrapperへ signalを送る (`test_mutation_worktree.py:823-855`)。
- wrapper自身の handlerも preflightより前に設置される (`tools/mutation_worktree.py:1124-1131`, handler本体は `:736-759`)。
- signalが `Popen` 復帰と `signal_state.process` 代入の間に届いても signumを保存し、代入後に再検査して子 process groupへ転送する (`tools/mutation_worktree.py:767-793`)。
- child handlerは signal recordを同期的に書いてから `SystemExit(128 + signum)` に入る (`test_mutation_worktree.py:95-101`)。
- wrapperは子を waitしてから最終 rcを選び (`tools/mutation_worktree.py:722-733,786-793`)、`128 + signum` を返す (`:960-967,1324-1332`)。

したがって、wrapperが rc=`128 + signum` を返したのに child recordがまだ未書込みという局所的な窓はない。過去の mutation nodeの赤も、同じ xdist workerで先行した `test_dev_wave_wait.py` が maskを汚染し、wrapperとchildが blocked maskを継承したことで説明できる。`2da49c56` の autouse fixtureは汚染源の test終了時に実 maskを復元するため、mutation fileを直接変更していなくても原因の射程には入っている。

今後 `2da49c56` 後の bundleで再発し、別の汚染源から inherited maskが確認された場合は `tools/mutation_worktree.py` の production境界に関わる。tests側で強制 unblockして隠さず、段4の再裁定へ返す。

## テスト計画

この段では実走しない。実装段で変更が発生した場合は、直接 pytestを起動せず `python3 tools/run_tests.py` を使う。

S1 の焦点 node候補:

- `test_codex_worker_launch.py::test_all_repo_policy_reasoning_values_are_accepted`
- `test_codex_worker_launch.py::test_check_receipt_recomputes_usage_actuals_from_sealed_artifacts`
- `test_codex_worker_launch.py::test_manifest_is_appended_while_correlated_session_is_running`
- `test_codex_worker_launch.py::test_check_receipt_detects_executable_identity_change`
- `test_codex_worker_launch.py::test_launcher_failure_diagnostic_reports_failed_predicates`
- `test_codex_worker_launch.py::test_launcher_failure_artifact_reporter_live_wiring`
- `test_codex_worker_launch.py::test_rollout_missing_after_grace_is_stopped_and_not_accepted`
- `test_codex_worker_launch.py::test_thread_missing_after_grace_kills_process_group`
- 上記で列挙した実 wall gate node一式

S1 の決定性を主張するには、48-worker全走の反復だけでは足りない。次の bundleで原因を確定した後、その判定点へ logical clock、`threading.Event`、barrier fileのいずれかを注入し、負荷や sleepに頼らず修正前を必ず赤、修正後を必ず緑にする regressionを置く。fixture isolation案なら、worker-local pathを読むことと real repo smokeが残ることを別 nodeで検査する。予算案なら、変更対象の commandだけが新値を持ち、evidence/wall negative caseが従来値を保持することを検査する。

S2 の確認 node候補:

- `test_dev_wave_wait.py::test_public_main_real_signal_after_success_uses_restored_handler`
- `test_dev_wave_wait.py::test_public_main_real_signal_releases_lease`
- `test_dev_wave_wait.py::test_public_main_failure_restores_handler_without_release`
- `test_mutation_worktree.py::test_sigint_and_sigterm_are_forwarded_between_observation_points` の SIGINT / SIGTERM 両 parameter
- `test_dev_wave_wait.py` の mask復元 regression三 nodeと autouse fixture検査

S2 の決定性根拠は実負荷ではなく、mask変更直後への同期的な例外注入、Python handlerの `Event`、wakeup-fd tokenである (`refs/2da49c56-production-diff.patch:31-48`)。

変更を作った場合の完了検査は、関連 test file、`python3 tools/check_codex_agents.py`、`python3 tools/check_docs.py`、全受入の順とする。全受入は統合確認であり、上記の決定的 regressionの代用にはしない。

## 危険な点

- `max_wall` の一律引き上げは wall gate、late receipt gate、process kill検査の検出力を失わせる。
- evidence graceの一律引き上げは missing rollout/threadを止める二 nodeを遅延させ、場合によっては evidence failureを wall failureへ変えてしまう。
- `expected_returncode=99` caseは実失敗を意図的に作る診断検査である。成功させる変更は assertion配線の検出力を消す。
- fake の `0.04`、`0.12`、`0.15`、`0.5` 秒刺激や外側 deadlineを変更すると、検査対象の観測窓そのものが変わる。
- worker-local authority repoへの全面置換は、現行 repoの docs authorityと hook配線が壊れていても unit testが緑になる危険がある。real repo smokeを残せないなら採用しない。
- xdist直列化は原因を隠し、受入時間を増やす。現在は共有 mutable stateが残る証拠も、fixture側で断てない証拠もない。
- mutation test側で signal maskを無条件に解除すると、productionが不正な inherited maskを扱えない回帰を隠す可能性がある。
- D362による除外、skip、xfail、retryは本件のような原因未確定かつ単独非再現の赤には適用できない。

## 親が裁定すべき択一

1. **S1を今すぐ予算変更するか、次の保存済み bundleを待つか**

   推奨は後者。artifactは既に機能しており、次の normal-control再発は predicateとstop reasonを保存できる。T190の三例は evidence grace型を強く示すが、歴代の max-attempts 1 normal controlまで同一とは未証明であり、値を決める根拠もまだない。

2. **次の bundleが preflight I/O型だった場合、worker-local repoへ分離するか、成功 caseだけ evidence graceを上げるか**

   推奨は、まず phase計測から共有 repo readが支配的か確定し、支配的なら fixture分離を優先すること。分離が実契約を失わせると判明した場合だけ、case-local evidence graceへ進む。productionのdeadline定義を変える必要が出たら段4へ返す。

3. **S2を追加修正するか、`2da49c56` で解消済みとして変更しないか**

   推奨は変更しないこと。三つの `dev_wave_wait` nodeには mask修復と明示 handshakeが入り、mutation nodeも handler設置後に readyを書き、wrapperはchild終了まで待つ。局所 raceは確認できない。

4. **S1を受入で直列化するか**

   推奨は却下。sessionsとreceiptは分離済み、docs内容は immutableかつfail-closedであり、「fixture側で断てない共有 mutable state」という裁定条件を満たしていない。

## 総括

- `run` の silent rc=1 は `_writer_truth` の三経路だけで、wall専用の署名ではない。
- launcherはrc=1時にstderrへ診断せず、receiptとsidecarへ記録するため、空stderrはwall説の肯定にも反証にもならない。
- sessionsとreceiptはtmpへ分離済みで、docs authorityの内容競合はrc=2になる。
- 残る候補は共有repoのread I/Oがattempt preflightを押し、evidence graceを消費する型である。
- T190 artifactは既に一つのretry型を確定したが、歴代normal-control全体への一般化はまだできない。
- S1は今すぐ予算を上げず、次のnormal-control bundleでpredicateを確定する案を推奨する。
- S1の直列化は根拠不足であり提案しない。
- S2の`dev_wave_wait`三nodeは`2da49c56`で解消済みである。
- mutation testもhandler設置後にreadyを書き、child終了後にrcを返すため追加待ち合わせは不要である。
- 親の主な裁定は「S1の次回artifactを待つか、未確定のままcase-local evidence予算へ進むか」である。