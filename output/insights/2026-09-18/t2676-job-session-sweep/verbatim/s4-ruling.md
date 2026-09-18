# [T-2676] 段 4 裁定 — plan v2 と事前登録 (2026-09-18 06:55 JST、結果を見る前に固定)

## 0. 所見の裁定

| 所見 | 判定 | 採否 | 処置 |
|---|---|---|---|
| A-1 同 session 所属は「終了させてよい」帰属証明でない (must-fix) | real | 採用 (scope 内: 殺すべきものだけ殺すのは局所対処の正しさ) | 帰属述語を追加: `readlink(/proc/<pid>/ns/user)` が走査 process 自身の `ns/user` と**異なる** process だけを signal 対象にする。同じ ns・読めない (EACCES/ENOENT) は `attributed=false` として記録し signal しない。根拠: bootstrap は全 task の子を入れ子 user ns (`unshare --user` + inner `unshare(CLONE_NEWUSER)`) に置く (L1112〜1128, L293)。NQSV 側 process は init ns。**login 実測** (`probe_ns_attribution.out.txt`): 同 uid の入れ子 ns 孤児の `ns/user` を外から readlink できた。uid フィルタ (P7) はこの述語に包含され不要 |
| A-2 既存 in-process テストは ambient opt-in `=1` に隔離されていない (must-fix) | real | 採用 | opt-in の**値を request SHA-256 に束縛**する: job script は `export IZANAGI_DISPATCH_JOB_SESSION_SWEEP="$REQUEST_SHA256"`、`_job_run` は `os.environ.get(ENV) == request_sha256` (自分が検証した値) のときだけ発火。ambient `1` や別 sha では発火しない。child_env からの pop は維持。負例テストを 1 本追加 (ambient `1` と別 sha で走査 0) |
| A-3 stat 再読と `os.kill` は原子的でない | real (限界) | 採用 (pidfd) | **pidfd** を使う: 列挙 → `os.pidfd_open(pid)` → `/proc/<pid>/stat` の starttime を列挙時の値と再照合 (不一致は `identity-changed` として skip) → `signal.pidfd_send_signal(fd, SIGTERM/SIGKILL)` → `select.poll` で pidfd の POLLIN (= 終了) を期限まで待つ。**login 実測**: 5.15 kernel で全経路が動作、終了観測 0.8 ms。計算ノードも 5.15.0-100/135 (runbook)。`pidfd_open` が OSError なら `pidfd-unavailable` を記録して signal しない (job の rc は不変)。残る窓 (列挙〜pidfd_open の間の pid 再利用) は starttime 再照合で検出、二重再利用は「言えないこと」へ |
| A-4 / B-2 M6 は指定 1 行変異で赤にならない (must-fix) | real | 採用 | M6 の契約を「後発 process を次巡で回収する」に固定し、変異は**巡数を 1 に固定する 1 行** (`rounds=2` → `rounds=1` 相当) とする。負例: 孤児 C が SIGTERM handler で孫 G を fork してから終了する → 1 巡目の列挙に G は居ない → 2 巡目で G を回収。変異では G が生存 → 赤。author 後に実行可能な 1 行 patch と nodeid を再固定する (2 段階登録) |
| A-5 / B-1 heartbeat の時刻条件が正常な TERM 終了を棄却する (must-fix) | real | 採用 | 判定は B 提案の `H ≤ G` (最終 heartbeat ≤ pidfd で観測した終了時刻) を整合条件にし、attempt との前後は記述統計 |
| B-3 総遅延の閾値が無い (must-fix) | real | 採用 | 判定表に `J − W ≤ 5 秒`、`E − W ∈ [−1, 10] 秒` を追加 (W = `supervisor-wait-complete`)。no-child は待機ゼロ (grace の sleep を通らない) |
| B-4 実 process テストの時間予算 (must-fix) | real | 採用 | 実 process テストは 3 本に集約し、pidfd poll で待つ (固定 sleep 無し)。準備 / sweep / 回収に別期限。猶予短縮は private 関数の引数だけ (production wrapper は定数を渡し、CLI・request・env から変えられない)。production 定数 (5 秒 / 1 秒 / 2 巡) の配線は mock 側で検査 |
| B-5 F-1 の祖先断定は trace から導けない | real | 採用 | facts F-1 を「dispatcher は session leader ではない。祖先鎖は未採取」に訂正。sweep は構築した祖先鎖 (pid, comm) を `session-sweep-start` の trace に残す (計算ノード 2 走で追加走なしに採取) |
| A-6 bound bootstrap が opt-in を再注入する | refuted | — | pop 位置は overlay 後・分岐前で足りる。統合テストは wrapper 実体を通し内側の sweep を mock |
| A-7 fixture の leader を除外できない | refuted | — | plan の構成 (L → S、S が自分の sid を走査) を維持。L の生存を finally 前に assert |
| A-8 F973 と同じ zombie 計数変更 | refuted | — | reparenting 不変。`Z` は signal 対象外・消滅済みにも数えない |
| A-9 配置が rc / schema / envelope を変える | refuted | — | 例外テストは実 wrapper 内の sweep へ注入 |
| B-6 猶予で `E − J` 窓に入らない | refuted | — | J は sweep 後。窓は据え置き、増えるのは `J − W` / `E − W` |
| B-7 `child-exit` 不在で不適格 | refuted | — | 投入前に「TERM 終了の keep に `child-exit` を要求しない」を固定 (本書 §3) |
| B-8 呼出し忘れでも全緑 | refuted | — | M1 は `_job_run` の呼出し行に当て、順序 assert |
| B-9 計算ノードで SIGTERM 無視の追加走が必須 | refuted | — | 結論を「generic 単一子・TERM 終了」に限定。SIGKILL 経路は login テストのみ (計算ノードでの実証とは書かない) |
| A-10 / B-10 行番号・再列挙理由 | nit | 採用 | facts / brief を訂正 (isolation 失敗 return は 1685〜1687、再列挙の理由は後発 fork) |
| A-11 「session 走査が唯一」 | nit | 採用 | 「今回採る経路」に弱める |
| B-11 後始末と orphan hold の手順 | nit | 採用 | §3 の手順に明記 |

親 brief の訂正: (P1) 祖先除外は維持、根拠は「dispatcher pid ≠ sid」まで。(P7) uid フィルタは ns 帰属述語に包含。(P4) 5 秒 / 1 秒 / 2 巡は設計値 (未実測) と明記。F-2 「唯一の経路」→「今回採る経路」。F-3 行番号訂正。

## 1. plan v2 (実装子への確定仕様)

変更 file: `tools/pegasus/dispatch_compute.py`、`orchestrator/tests/test_pegasus_dispatch_compute.py` の 2 file のみ。docs は親。

### 1.1 定数 (L168 付近)
- `_JOB_SESSION_SWEEP_ENV = "IZANAGI_DISPATCH_JOB_SESSION_SWEEP"`
- `_SESSION_SWEEP_TERM_GRACE_S = 5.0`、`_SESSION_SWEEP_KILL_GRACE_S = 1.0`、`_SESSION_SWEEP_ROUNDS = 2`

### 1.2 job script (L911 の隣)
`export IZANAGI_DISPATCH_JOB_SESSION_SWEEP="$REQUEST_SHA256"` を `export IZANAGI_DISPATCH_REQUEST_SHA256="$REQUEST_SHA256"` の直後に足す。既存の substring 契約 (`_is_bound_job_envelope`) は変えない。

### 1.3 child_env (L1627 の直後)
`child_env.pop(_JOB_SESSION_SWEEP_ENV, None)`。allowlist には足さない。

### 1.4 発火 wrapper `_maybe_sweep_job_session(request_sha256)` (`_job_trace` の後に置く)
- 先頭: `if request_sha256 is None or os.environ.get(_JOB_SESSION_SWEEP_ENV) != request_sha256: return` — この判定より前に getsid / `/proc` / signal を行わない。
- `sid = os.getsid(0)`、`own_ns = os.readlink("/proc/self/ns/user")`、`excluded = 自分 + 祖先鎖 (ppid を 1 まで、既訪問で打切り)`。祖先鎖を読めなければ `session-sweep-error` (reason=`ancestry-unreadable`) を出して return (候補へ混ぜない)。
- `_sweep_job_session(sid, own_user_ns=own_ns, excluded_pids=excluded, term_grace_s=定数, kill_grace_s=定数, rounds=定数)` を `try/except Exception` で囲み、例外は `session-sweep-error` (type, message) に記録。**child_rc / payload / return 値を変えない。**

### 1.5 `_sweep_job_session(sid, *, own_user_ns, excluded_pids, term_grace_s, kill_grace_s, rounds)` (private、引数は private helper 以外から変えられない)
巡ごとに:
1. `_list_session_residuals(sid, excluded_pids, own_user_ns)` — `/proc` の数値 dir を列挙し `/proc/<pid>/stat` を parse (comm は最後の `)` で切る。state=tail[0]、ppid=tail[1]、pgrp=tail[2]、session=tail[3]、starttime=tail[19])。`session == sid` かつ `pid ∉ excluded` を候補にし、各候補に `user_ns = readlink(/proc/<pid>/ns/user)` (失敗は None)、`uid` (`/proc/<pid>/status` の Uid 先頭、失敗は None)、`attributed = (user_ns is not None and user_ns != own_user_ns)` を付ける。ENOENT/ESRCH は走査中の消失として継続。parse 異常・EACCES は `readable=false` で記録し signal しない。
2. 各候補を trace `session-residual` (round, pid, ppid, comm, state, uid, starttime, pgrp, user_ns, attributed, readable) に記録。
3. `attributed` かつ state≠`Z` の候補だけ: `fd = os.pidfd_open(pid)` (OSError → `session-signal` result=`pidfd-unavailable`/errno、skip) → stat 再読で starttime 一致を確認 (不一致 / 不在 → `identity-changed` / `absent`、fd close、skip) → `signal.pidfd_send_signal(fd, SIGTERM)` (ProcessLookupError → `esrch`、PermissionError → `eperm`、その他 OSError → errno を記録。いずれも継続) → trace `session-signal` (pid, starttime, signal, result, time_ns)。
4. TERM を送った fd 群を `select.poll` で `term_grace_s` まで待つ (全部 POLLIN で早期終了)。終了を観測した pid は trace `session-process-exited` (pid, starttime, after=`term`, time_ns)。
5. 未終了へ `SIGKILL` を送り (`session-signal` signal=KILL)、`kill_grace_s` まで poll。終了は `after=kill`。期限内に終了しなければ `session-process-remaining` (pid, starttime, state 再読)。
6. fd を全部 close。次巡は再列挙から (後発 fork を拾う)。**新規候補が 0 なら巡を終える。**
7. 最終列挙で残る `attributed` 候補 (生存 / Z / unreadable) を集計し trace `session-sweep-complete` (status ∈ {`clean`, `remaining`, `error`}, rounds_used, found_total, attributed_total, unattributed_total, exited_after_term, exited_after_kill, remaining, zombies, unreadable, elapsed_ms)。**完了事象は処理終了の意味で、成功の同義語ではない。**
- 候補 0 の巡では sleep も poll もしない (no-child は待機ゼロ)。
- 全体の協調的上限 = `rounds × (term_grace_s + kill_grace_s)` + 列挙。watchdog は新設しない。
- 非子への `waitpid`・subreaper・PID ns・setsid・`os.kill(pid)` (pidfd を使わない送信) は使わない。

### 1.6 配置 (`_job_run` L1684、except 連鎖の後・`if isolation_failed:` の前)
```python
if stage in ("child", "child-launch"):
    _maybe_sweep_job_session(request_sha256)
```
`main` (L4485〜4501) は変えない。

### 1.7 trace 事象 (新規、`_job_trace` の既存 top-level `pid` は発行者)
`session-sweep-start` (sid, own_user_ns, ancestors=[{pid, comm}])、`session-residual`、`session-signal`、`session-process-exited`、`session-process-remaining`、`session-sweep-complete`、`session-sweep-error`。consumer は無い (facts F-3)。

### 1.8 テスト (`orchestrator/tests/test_pegasus_dispatch_compute.py`、`_job_run_with_mocked_child` L4083 の付近)
実 process テスト 3 本 (各 2 秒目標、期限は準備 3 秒 / sweep 3 秒 / 回収 3 秒を別に持つ。同期は pipe、固定 sleep なし):
- `test_session_sweep_terminates_attributed_orphan_and_preserves_others`: pytest が `Popen(start_new_session=True)` で leader L (python) を作る。L は (a) scanner S、(b) 入れ子 user ns の短命親 P (`/usr/bin/unshare --user --map-root-user -- python -c ...`、inner `unshare(CLONE_NEWUSER)` は不要 — 外側 ns だけで own_ns と異なる) が孤児 C (SIGTERM 既定動作、stdio は DEVNULL) を fork して終了、(c) 同 session・init ns の非祖先 N (sleep する python)、を作る。pytest は別 session の対照 D も作る。S は自分の `os.getsid(0)` と `readlink(/proc/self/ns/user)` を渡して `_sweep_job_session(…, term_grace_s=0.5, kill_grace_s=0.5, rounds=2)` を実行し、結果 (trace 相当の記録) を pipe/file で返す。期待: C は `attributed=true` で TERM 後に exited、N は `attributed=false` で signal されず生存、L 生存、D 生存。finally で L の group と D を回収。
- `test_session_sweep_kills_sigterm_ignoring_orphan`: C が SIGTERM を `SIG_IGN` にしてから準備完了を通知。期待: TERM → KILL で exited、`after=kill`。
- `test_session_sweep_rescans_for_late_orphan`: C の SIGTERM handler が孫 G (入れ子 ns を継承、stdio DEVNULL) を fork してから exit。期待: 1 巡目に G 不在、2 巡目で G を回収、最終 remaining=0。
mock / fake `/proc` テスト (実待機ゼロ):
- `test_session_stat_parses_spaced_parenthesized_comm`
- `test_session_sweep_without_opt_in_does_not_touch_processes`: env 不在 / `1` / 別 sha で wrapper が getsid・列挙・pidfd・signal を 0 回 (mock で計数)、sha 一致でのみ `_sweep_job_session` を呼ぶ (定数 5.0 / 1.0 / 2 が渡ることも assert)。
- `test_session_sweep_rechecks_identity_before_signal`: starttime 変化 → signal しない (`identity-changed`)。
- `test_session_sweep_does_not_claim_unconfirmed_disappearance`: pidfd poll が期限内に POLLIN を返さない → exited に数えず remaining。
- `test_session_sweep_records_signal_errors_and_zombies`: esrch / eperm / pidfd-unavailable / Z / unreadable の区別。
- `test_session_sweep_stops_at_round_limit`: 毎巡新候補が出ても rounds で止まり status=remaining。
- `test_job_run_sweeps_before_result_and_strips_opt_in`: `_job_run_with_mocked_child` を env 注入可能に拡張。env==sha で wrapper 実体 → 内側 `_sweep_job_session` mock が result 書込み前に 1 回呼ばれ、child_env に ENV 無し、非ゼロ child_rc 保持。env `1` では 0 回。
- `test_job_run_sweeps_after_isolation_failure_without_replacing_guard`
- `test_job_run_sweep_error_preserves_child_result`: 実 wrapper 内の sweep に例外注入、rc / payload 不変、`session-sweep-error` 記録。
- 既存 job script 検査へ export 行の assert を追加。
合計 14 nodeid 目安。テストを甘くする変更 (既存期待値の変更・skip) は禁止。

## 2. 変異事前登録 (意味と期待 nodeid を固定。実行可能な 1 行 patch は author 後・変異実行前に再固定)

| 変異 | 意味 | 期待 KILLED nodeid |
|---|---|---|
| M0 | comment 1 行だけの対照 (drift 計測) | SURVIVED 期待 |
| M1 | `_job_run` の `_maybe_sweep_job_session(...)` 呼出しを `pass` に | `test_job_run_sweeps_before_result_and_strips_opt_in` |
| M2 | 祖先除外を `pid == os.getpid()` だけに縮小 | `test_session_sweep_terminates_attributed_orphan_and_preserves_others` (L が死ぬ) |
| M3 | wrapper 先頭の opt-in 判定を `if False:` に | `test_session_sweep_without_opt_in_does_not_touch_processes` |
| M4 | SIGKILL 送信行を `pass` に | `test_session_sweep_kills_sigterm_ignoring_orphan` |
| M5 | pidfd poll の結果を無視して「送信 = 終了」と数える (poll 呼出しを `events = [(fd, POLLIN) ...]` 相当に) | `test_session_sweep_does_not_claim_unconfirmed_disappearance` |
| M6 | 巡数を 1 に固定 | `test_session_sweep_rescans_for_late_orphan` |
| M7 | 帰属述語を恒真に (`attributed = True`) | `test_session_sweep_terminates_attributed_orphan_and_preserves_others` (N が死ぬ) |
M2 / M4 / M7 が赤でも fixture の finally が回収する。冗長 gate (drift mask) は較正走で実測して `--deselect`。

## 3. 計算ノード実測の事前登録 (投入前に固定)

器具: T-2675 probe (sha256 `f781162298f8885bd8d73f9e5d65d0d763fa14cc7e1673dd9961d42f9dc5b3e1`、30,373 bytes) を worktree の `tools/probe_t2675_run_membership.py` に untracked で置く (commit しない)。argv は plan §7 のとおり (`--parent-seconds 5 --child-seconds 75`、evidence は `output/insights/2026-09-18/t2676-job-session-sweep/evidence/probe-<cond>.jsonl`)。順序: no-child → keep (直列、前走の receipt・会計・evidence 確認後に次を投入)。

記号: W = `supervisor-wait-complete`、S/C = `session-sweep-start` / `-complete`、T = `session-signal` (TERM) の time_ns、G = `session-process-exited` の time_ns、J = `job-run-returned`、E = `.e` の `Ended Request Time` (JST 秒精度)、H = 最終 heartbeat の realtime。

| 指標 | no-child | keep (TERM 終了) |
|---|---|---|
| `session-residual` (attributed) | 0 | 1、pid = probe evidence `fork` の `child_pid`、comm = python3、ppid = 1 |
| unattributed / unreadable | 0 (非 0 は期待外として記録、成功にしない) | 同左 |
| signal | 0 | TERM 1 回 result=sent、KILL 0 |
| 終了確認 | 対象なし | `session-process-exited` after=term、`G ≤ C ≤ J`、G < t0+75 |
| `session-sweep-complete` | status=clean、rounds_used=1、待機なし | status=clean、remaining=0 |
| `E − J` | [−1, 5] 秒 | [−1, 5] 秒 |
| `J − W` | ≤ 5 秒 | ≤ 5 秒 |
| `E − W` | [−1, 10] 秒 | [−1, 10] 秒 |
| heartbeat | 子記録なし | 0 件を許容。存在すれば `H ≤ G` |
| `child-exit` | 該当なし | 不要 (TERM 終了) |
| 祖先鎖 (`session-sweep-start`) | 記録される (採取のみ、判定に使わない) | 同左 |

共通の適格性: `terminal_reason=scheduler-end-state`、`accounting_verified=true`、`qdel.attempted=false`、rc=0、対象 request の orphan hold なし (「一度も発生しなかった」とは書かない)、evidence の JSON 完全・`recording_errors=[]`、親終了 δ ∈ [4.5, 10]、request/host/J/E の対応。欠測は「判定不能」とし、事後に緩めない。

結論の 2 軸: (会計・総遅延 合格 / 不合格) × (独立した消滅確認 合格 / 不合格・不明)。両方合格のときだけ「当該条件 (generic 単一子・TERM 終了) で終了遅延短縮と残存消滅を確認」と書く。E − J 短縮だけを成果にしない。実 workload (xdist、FIFO 孫、TERM handler 付き)・計算ノードでの SIGKILL 経路は言えないことへ。

後始末: 2 走の後、probe を job dir と `cmp` で照合してから worktree から削除、evidence は insight へ配置、`git status --short --untracked-files=all` で `??` 0 件を確認してから commit。無関係な untracked は消さない。

## 3′. §3 の事前登録の改訂 (2026-09-18 07:45 JST、計算ノード 2 走の投入前。改訂の契機 = probe `probe_sigign.py` の結果 `sigign.log` mtime 07:43:18)

**新事実 (request 5043.nqsv、bnode145):** 計算ノード job 内の全 process (dispatcher python3.10 / bash / nqs_shpd (uid 31609、session leader) / 隔離 bootstrap / 子) は
**SIGTERM を SIG_IGN として継承している** (`SigIgn` bit 14、bash 252296 = `0x4004`、python 系 = `0x1005000`)。これは F1012 (継承された signal 無視設定) と同じ環境事実であり、
T-2675 probe の子は SIGTERM handler を設定しない (SIGALRM のみ) ので **keep 条件の残存子は TERM では終了せず、5 秒の猶予後の SIGKILL で終了する。**
段 6 焦点走の赤 (term mode) も同じ機序 (F1012 の再発、fixture 側は F1 で SIG_DFL + unblock を明示)。

**§3 の keep 列を次に改める (結果を見る前に固定):**

| 指標 | keep (改訂: TERM 無視 → KILL 終了) |
|---|---|
| `session-residual` (attributed) | 1、pid = probe evidence `fork` の `child_pid`、comm = python3、ppid = 1 (据え置き) |
| signal | TERM 1 回 result=sent → (5 秒猶予、exit なし) → KILL 1 回 result=sent |
| 終了確認 | `session-process-exited` after=**kill**、`G ≤ C ≤ J`、G < t0+75 |
| `session-sweep-complete` | status=clean、remaining=0、exited_after_term=0、exited_after_kill=1、rounds_used=2 (2 巡目の再列挙で新規 0 → 終了) |
| `E − J` | [−1, 5] 秒 (据え置き) |
| `J − W` | **≤ 8 秒** (TERM 猶予 5 + KILL 猶予 ≤ 1 + 列挙 2 回 + result 書込み) |
| `E − W` | **[−1, 13] 秒** |
| heartbeat | 0 件を許容。存在すれば `H ≤ G` (据え置き) |
| `child-exit` | 不要 (据え置き) |

no-child 列は不変。`unreadable 0` は F4 の改名により **`session_unknown 0`** と読む (非 0 は期待外)。
この改訂は「TERM 猶予 5 秒を残存があるときだけ支払う」という設計 (段 4 P4) を変えない。dispatcher 自身で SIGTERM を SIG_DFL に戻して子孫へ既定を継承させる案は、
job body 全体の signal 環境を変える (受入 suite の既存挙動に波及しうる) ので本 wave の scope 外とし、次の一手候補として insight に置く。

## 4. 完了条件
焦点走緑 (新規 14 + consumer)、変異 matrix (M0 SURVIVED、M1〜M7 KILLED 期待 node 完全一致)、計算ノード 2 走が §3 の両軸合格、受入全走緑、insight + worklog/decisions fragment、land。
