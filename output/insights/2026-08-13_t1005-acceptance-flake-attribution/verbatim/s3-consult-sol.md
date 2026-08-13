必読 4 ファイルを読了し、指定ログも静的に突合した。結論は、M1 の clock 差そのものは立つが、親の「3 箇所限定」「前処理 2.28 秒以上」「job clock は保存されない」は誤り。M2/M3 は実装可能性としては立つものの、観測された burst への一意帰属はできない。

### A-01 — blocker

- 主張: `max_wall_clock_s` を serialized attempt に立てる経路は 3 箇所だけではない。attempt 終了後の監査・receipt 公開過程でも後付けされる。このため `wall_clock_s=0.716` から「attempt 前処理が 2.28 秒以上」とは逆算できない。

- 根拠: `_latch_final_job_limit()` は job clock を再測定し、`attempts[-1]["limit_trigger"]` を設定する (`tools/codex_worker_launch.py:1954-1977`)。呼出点は attempt 直後 (`:2069`)、最初の receipt 監査後 (`:2085`)、output 公開・監査・receipt staging 後 (`:2124`)。retry 境界も `:2060-2067` で同じ field を設定する。特に後段監査は authority snapshot を再構成して git を複数回起動する (`:2078-2085`, `:2825-2902`)。

- `state.limit_trigger` という変数だけなら親の 3 箇所だが、receipt に出る `attempt.limit_trigger` の producer はそれだけではない。receipt checker は `actuals.wall_clock_s` を検査するが後付けはしない (`:2618-2634`)。

- 実ログの `attempt.wall_clock_s=0.716725251` と `receipt_actuals.wall_clock_s=3.26495975` (`acceptance.log:692-698`) の差 2.548 秒は、前処理だけでなく post-attempt audit を含む。どの latch が発火したかは保存されない。

- 壊す対象: M1 の「3 箇所だけ」、M1 の「前処理 2.28 秒以上」、P1 の一意な近接原因。

- 攻撃結果: attempt clock で wall 判定する経路は見つからなかったため、M1 の中心命題「判定は job clock、診断値は attempt clock」は立った。

### A-02 — must-fix

- 主張: 親は attempt clock の起点も強く言い過ぎている。`state.started_ns` は `Popen` 直前ではなく、hook 検証より前に設定される。

- 根拠: `state.started_ns` は `tools/codex_worker_launch.py:1345-1348`、hook 検証は `:1403`、`Popen` は `:1412`。したがって hook 検証時間は job clock と attempt clock の両方に入り、両者の差には入らない。evidence deadline も同じ `state.started_ns` を使う (`:1427-1429`)。

- attempt 前には、project module import (`:40-65`)、引数解析 (`:3143-3145`)、authority snapshot (`:1873`)、repo binding (`:1916`)、Codex executable の hash/version (`:1949-1951`) がある。authority snapshot は git 3 回、repo binding は git 4 回、version は subprocess 1 回を直列実行する (`tools/dev_waves/launch_authority.py:331-385`, `tools/codex_worker_launch.py:1826-1866`)。48 worker 下で 2 秒級は実装上十分現実的だが、静的検査だけでは実際の費消箇所を確定できない。

- さらに標準ライブラリ import は marker より前 (`tools/codex_worker_launch.py:9-35`) なので job clock 外。一方、in-process test は marker 自体を `main()` 直前へ差し替える (`orchestrator/tests/test_codex_worker_launch.py:1245-1258`)。

- 壊す対象: M1 の時計境界の説明、P2 の遅延源断定。

- 攻撃結果: 2 秒という大きさは非現実的ではない。しかし「hook を含む attempt 前処理が 2.28 秒」という内訳は成立しない。

### A-03 — blocker

- 主張: `codex_exit_code=-9` は M2 固有ではなく、evidence deadline も `-9 / missing / None` を必ず生成しない。観測された 8 件は M2 と強く整合するが、receipt だけでは確定できない。

- 根拠: `_terminate()` は、wall/model/token limit、evidence deadline のいずれでも呼ばれる (`tools/codex_worker_launch.py:1461-1507`)。spawn 後の任意の例外でも呼ばれる (`:1511-1519`)。内部では identity 不明時や wait timeout 時に `process.kill()`、identity 有効時は SIGTERM 後に SIGKILL を送る (`:1167-1191`; `tools/dev_waves/worker.py:181-204`)。OS、scheduler、OOM からの外部 SIGKILLも同じ `returncode=-9` になる。

- specific 8 records は `limit_trigger=None`、`outcome=not_accepted`、`launcher_rc=1` なので、launcher 内部では limit 経路と例外経路を除外できる。残る launcher-owned 経路は evidence deadline だが、外部 SIGKILLとは識別不能。

- deadline 判定は「session ID または rollout が未発見」だけを見る (`tools/codex_worker_launch.py:1490-1499`)。metering は rollout/token/terminal usage から独立に計算される (`:1094-1114`)。停止後にも `observe()` が走る (`:1509-1510`) ため、停止時には欠けていた evidence/metering が最終 receipt では complete になりうる。

- `evidence_forced_stop` は定義と代入の 2 箇所しかなく (`:349`, `:1497`)、receipt にも acceptance 判定にも使われない。SIGTERM 後に子が rc=0 で evidence を完成させれば、静的には accepted さえ可能である (`:1256-1265`, `:1546-1555`)。

- 実際、別 burst には `codex_exit_code=-9` だが `metering_status='complete'`、`validator_rc=0` の record がある (`auto-acceptance-3.log:443-449`)。

- 壊す対象: M2 の確定表現、M2 の必須同伴述語、P1。

### A-04 — must-fix

- 主張: `residual=None → termination_verified=False` は正しいが、`None` の原因を `_group_member_count` の scan failure に一意帰属できない。

- 根拠: `_normal_reap()` は確かに `residual == 0` のときだけ成功扱いする (`tools/codex_worker_launch.py:1200-1209`)。一方、`_group_member_count(None)` は走査せず即 `None` (`:1137-1139`)。identity 自体も、`Popen` 直後の `/proc/<pid>/stat` または boot ID 読取失敗で `None` になる (`:1423-1426`; `tools/dev_waves/worker.py:97-121`)。このほか `/proc` 全体の `scandir`、任意 PID の stat 読取・parse failure も同じ `None` を返す (`tools/codex_worker_launch.py:1141-1163`)。

- テストも「missing identity」「全 scan failure」「個別 stat failure」を同じ unknown として扱っている (`orchestrator/tests/test_codex_worker_launch.py:2547-2587`)。

- 壊す対象: M3 の観測 burst への一意帰属、P1。

- 攻撃結果: M3 のコード経路は立ったが、実 record がその経路のどの入口を通ったかは判定不能。

### A-05 — must-fix

- 主張: loadavg 完全一致から「同一瞬間に同時被弾」は導けない。

- 根拠: loadavg は launcher 内の失敗時刻ではなく、pytest 側が returncode mismatch の診断を組み立てる時点で `os.getloadavg()` を 1 回呼んで記録する (`orchestrator/tests/test_codex_worker_launch.py:372-400`)。その前に termination、receipt 読取、診断生成が入る。時刻そのものは保存されない。

- Linux の更新周期を踏まえると、完全一致が示すのは「診断生成が同じ量子化された loadavg sample state を見た可能性が高い」まで。同一の約 5 秒更新窓を示唆しても、gate 発火の同時性、同一瞬間、共通原因は含意しない。同じ値が複数更新にまたがって維持される可能性まで考えると、5 秒以内という厳密な上界にもならない。

- 正確な言い直し: 「各走の失敗診断は 1〜2 個の loadavg sample state に集中した。時間的クラスタリングを支持するが、同時被弾や一原因性は証明しない」。

- 壊す対象: brief:25-27 の強い burst 推論、P1、P2。

### A-06 — blocker

- 主張: test-only の fixture 変更なら production 受理集合は変わらない。しかし「期限テストはすべて自前値なので無影響」は反証された。production 値へ一括で寄せると、少なくとも以下が壊れるか検査が恒真化する。

| nodeid | 現在の依存 | 引上げ時の影響 |
|---|---|---|
| `test_launcher_failure_diagnostic_reports_failed_predicates` | diagnostic に wall=3 / evidence=1.0 / termination=0.05 を literal assert (`test:1391-1423`) | 値変更だけで失敗 |
| `test_check_receipt_marks_self_asserted_limits_and_accepts_external_expectations` | fixture default wall=3 を外部期待値 `"3"` と照合 (`test:3361-3399`) | default 変更だけで失敗 |
| `test_attempt_preflight_delay_exhausts_wall_clock_before_spawn` | wall=3、論理時計を +4 秒 (`test:2224-2255`) | local wall を 4 秒超へ上げると gate 不発 |
| `test_launcher_process_wall_clock_includes_version_preflight` | wall=0.1、version delay=0.2 (`test:2705-2729`) | 0.2 秒超へ上げると gate 不発 |
| `test_receipt_staging_wall_overrun_flips_to_not_accepted_and_removes_output` | shared default wall=3、staging 後 +4 秒 (`test:2774-2810`) | wall default を production 級へ上げると accepted のまま |
| `test_receipt_audit_wall_overrun_flips_to_not_accepted` | shared default wall=3、audit 後 +4 秒 (`test:2813-2848`) | 同上 |
| `test_rollout_missing_after_grace_is_stopped_and_not_accepted` | evidence=1、wall=3、fake は30秒 sleep (`test:3999-4018`) | evidence を5へ単独変更すると wall が先に発火し期待破壊 |
| `test_thread_missing_after_grace_kills_process_group` | evidence=1、termination=0.05、wall=3、TERM無視 (`test:4021-4038`) | evidence/termination 引上げで wall が先行、または10秒 harness timeout |
| `test_sigterm_ignoring_child_is_killed` | wall=3、termination=0.05、fake は30秒 sleep、harness timeout=10 (`test:2498-2544`) | wallを大幅に上げると timeout。terminationを30秒級へ上げ、harnessも延長すると自然終了でも assertions が通り「killed」が恒真化 |
| `test_cli_reported_token_limit_stops_process` / `test_cumulative_limits_do_not_reset_between_attempts` / `test_spawned_process_group_is_cleaned_on_manifest_append_failure` | TERM無視 fake と termination grace に依存 (`test:2454-2475`, `:2610-2636`, `:3942-3956`) | 大幅引上げで10秒 timeout、さらに長くすると自然終了でも cleanup assertions が通りうる |

- test fixture は `3 / 1.0 / 0.05` を明示送信する (`orchestrator/tests/test_codex_worker_launch.py:950-1043`)。production dispatcher が送るのは wall/model/token だけ (`tools/dev_wave_codex.py:206-223`) で、evidence/termination は launcher default `5 / 2` (`tools/codex_worker_launch.py:3103-3110`)。termination の比は親表で欠けているが 40 倍。

- したがって、test file 内だけを変える限り production acceptance bit は不変。一方、launcher parser default を変えると production がその値を暗黙利用するため P3 は成立しない。

- 壊す対象: P3 の「wall 上限テストは無影響」という補助主張。literal な「test-only 変更は production bit 不変」は攻撃したが立った。

### A-07 — blocker

- 主張: 述語の均一性は「1 burst 1 近接原因」を含意しない。実装が混合原因を単一 field と優先順位で潰すからである。

- 根拠: running process では wall → model calls → tokens を `if/elif` で 1 個の `pending_limit` に縮約する (`tools/codex_worker_launch.py:1461-1475`)。`limit_trigger` が立てば evidence deadline を調べる前に break する (`:1487-1499`)。同じ poll で wall と evidence が両方期限を越えても記録は wall だけになる。

- evidence deadline の発火理由は保存されず、診断の `failed_predicates` は最終 acceptance conjunct の差分にすぎない (`orchestrator/tests/test_codex_worker_launch.py:171-187`)。同じ evidence stop でも、最終 `observe()` の進み具合により triple、`codex_exit_code` 単独、あるいは別集合になりうる。

- 各走で失敗したテスト集合も異なる (`acceptance.log:245-265`, `auto-acceptance-2.log:529-535`, `auto-acceptance-3.log:522-524`)。走ごとに、たまたま preflight、evidence 待ち、normal reap にいたテストだけが異なる terminal predicate を出すという selection effect で説明できる。

- 壊す対象: P1。uniform predicate は親の説明と「整合」はするが、一原因性の証拠ではない。

### A-08 — must-fix

- 主張: P2 のうち「並行 Codex 子は必要条件でない」は立つが、「遅延源は 48 worker + 共有 `/work`」はまだ確定できない。

- 根拠: 親 Codex 子ゼロでも発火した記録がある (`docs/failures.md:1613-1623`)。48 worker で連続赤、`-n 8` で緑という対照も concurrency を risk factor として支持する (`docs/failures.md:1860-1880`)。

- しかし M3 は `/proc` 観測、M2 は `/tmp` の rollout discovery・process scheduling・hook の git I/O、M1 は preflight と post-attempt audit の双方が候補である。per-phase timestamps、I/O latency、CPU scheduling、`/proc` error provenance がなく、共有 `/work` だけを原因へ固定できない。

- 壊す対象: P2 の原因確定部分。

## 総括

- M1 — **立つ**。job clock と attempt clock の差は確認。ただし「3 箇所限定」「前処理 2.28 秒以上」「job clock は receipt に無い」は崩れる。
- M2 — **判定不能**。observed 8件と強く整合するが SIGKILL provenance がなく、`missing` の必須同伴も成り立たない。
- M3 — **判定不能**。`None → False` は立つが、`None` の発生源を scan failure に一意帰属できない。
- P1 — **崩れる**。優先順位・単一 field・未記録の forced-stop reason が混合原因を隠す。
- P2 — **判定不能**。48-worker concurrency は支持され、並行 Codex 子は不要だが、共有 `/work` 原因は未分離。
- P3 — **立つ**（test-only edit という literal に限る）。ただし「期限テストは無影響」は崩れ、一括予算変更は複数 nodeid を壊すか恒真化する。

pytest は実走しておらず、緑とは記録していない。