# [T-2676] 計算ノード job の終了遅延への局所対処 — job body が session に残る process を特定して回収する

authority: none / default_effect: no-state-change

wave = `dev-wave-t2676-job-session-sweep`、基準 commit = `d2ebef7a4` (local main)、実装 commit = `1e4d0bbd1`。
一次資料 (前 2 wave) = `output/insights/2026-09-16/t2622-compute-job-exit-hang/README.md` (D2048)、
`output/insights/2026-09-17/t2675-nqsv-run-membership/README.md` (D2124)。
目的は**局所対処の実装と計算ノードでの実測**。subreaper は採らない (F973)。一般的な process 管理機構へ広げない。
仮想リスク向けの gate・検査・台帳・一般化は scope 外。規律 2 に触れない。

---

## 0. 結論 (先に書く)

**限定した条件 (generic 単一子 probe、TERM を無視する残存子 1 本) で、終了遅延の短縮と残存子の消滅を別々の証拠で確認した。**

| 条件 | request / node | 残存 (attributed) | signal | 消滅確認 (pidfd) | `E − J` | `J − W` | `E − W` | status |
|---|---|---|---|---|---|---|---|---|
| no-child (統制) | `5077.nqsv` / bnode073 | 0 | なし | 対象なし | **−0.468 秒** | 0.042 秒 | −0.426 秒 | clean、rounds 1、30.9 ms |
| keep (陽性対照、子 75 秒) | `5086.nqsv` / bnode080 | 1 (probe の子 pid 1230822、python3、ppid 1、入れ子 ns) | TERM sent → 5 秒無応答 → KILL sent | `after=kill`、G − t0 = 10.0 秒 (< 75)、`H ≤ G` (0.034 秒) | **−0.381 秒** | 5.077 秒 | 4.696 秒 | clean、rounds 2、5054 ms |

前 2 wave の同器具・同条件 (keep) では `E − J` = 69.5 / 69.7 秒だった (D2048、D2124)。本 wave の keep は −0.381 秒。
判定は §4 の事前登録 (段 4 §3、投入前に §3′ で改訂) どおり。**会計短縮と残存子の消滅の両軸が合格。**

**言えないこと (先に書く):** 実 workload (xdist、FIFO で block した孫、TERM handler 付き process) への適用性、計算ノードでの TERM 終了経路
(この cluster の job は SIGTERM を SIG_IGN で継承するので、handler を持たない残存子は必ず KILL 経路になる)、別 session へ移った process、
sweep 到達前に直接の子が戻らない経路。§7。

---

## 1. 実装 (何をしたか)

変更 file は `tools/pegasus/dispatch_compute.py` と `orchestrator/tests/test_pegasus_dispatch_compute.py` の 2 つ (commit `1e4d0bbd1`、+777/−1)。
Codex `role=author` (`gpt-6-astra` / medium) が書き、親は 1 byte も直接編集していない。

| 要素 | 実装 |
|---|---|
| 発火 | job script が `export IZANAGI_DISPATCH_JOB_SESSION_SWEEP="$REQUEST_SHA256"`。`_job_run` は検証済み request SHA-256 と一致するときだけ sweep (`_maybe_sweep_job_session`)。値は child_env から pop。ambient `1` / 別 sha / None は getsid より前に return |
| 配置 | `_job_run` の except 連鎖の後・`isolation_failed` の早期 return の前 (`stage in ("child", "child-launch")`)。result 書込み前なので `J` (`job-run-returned`) は sweep 完了後 |
| 列挙 | `/proc/<pid>/stat` (comm は最後の `)` で切る、session = field 6、starttime = field 22)。`session == os.getsid(0)` かつ pid ∉ {自分} ∪ 祖先鎖 (ppid を 1 まで) |
| 帰属 | `readlink(/proc/<pid>/ns/user) != 自分の ns/user` の process だけを workload とみなす (bootstrap は全 task の子を入れ子 user ns に置く。NQSV 側は init ns)。同 ns / 読めない / stat 不読は記録だけで signal しない |
| signal | `os.pidfd_open` → starttime 再照合 → `signal.pidfd_send_signal(SIGTERM)` → `select.poll` (POLLIN = 終了) で 5 秒 → 生存へ SIGKILL → 1 秒 → 再列挙 (後発 fork)。最大 2 巡、新規候補 0 で終了。候補 0 の巡は sleep も poll もしない |
| 記録 | `IZANAGI_DISPATCH_JOB_TRACE` の新事象: `session-sweep-start` (sid、own_user_ns、ancestors)、`session-residual` (round、process{pid, ppid, comm, state, uid, starttime, user_ns, attributed, readable})、`session-signal` (signal、result ∈ {sent, esrch, eperm, error, pidfd-unavailable, identity-changed, absent, zombie, unreadable}、time_ns)、`session-process-exited` (after ∈ {term, kill}、time_ns)、`session-process-remaining`、`session-sweep-complete` (status ∈ {clean, remaining, unknown}、rounds_used、found_total、attributed_total、unattributed_total、exited_after_term、exited_after_kill、remaining、zombies、session_unknown、elapsed_ms)、`session-sweep-error` |
| 不変 | result schema `pegasus-dispatch-result/v1` の field、`main`、bootstrap、`_is_bound_job_envelope` の substring 契約。subreaper / PID ns / setsid / `os.kill(pid)` / 非子 `waitpid` は使わない (reparenting を変えないので F973 の consumer 列挙義務は非該当) |
| 失敗時 | sweep の例外は `session-sweep-error` に記録し、`child_rc` / result / return を変えない |

テスト 14 nodeid (§5)。既存テストの期待値は変えていない。

## 2. 前提と、この wave で確定した事実

- D2124: NQSV は job の session に生きた process がある間 RUN に留める。session 離脱は待たない、pgid 変更は待つ。
- **job 内 dispatcher は session leader ではない** (T-2675 の trace: dispatcher pid 3010049 ≠ sid 3010029)。本 wave の trace で祖先鎖が採れた:
  `python3.10 (dispatcher) → bash → nqs_shpd (= session leader、uid 31609) → nqs_shpd (uid 65534) → nqs_shpd → systemd` (5015 / 5043 / 5077 / 5086 の 4 job で同形)。
  session leader は NQSV の `nqs_shpd` がユーザー uid で走る process。「自分以外を全部 kill」する走査はこれを殺す。祖先鎖の除外と ns 帰属述語の両方が守る。
- **job 内の全 process は SIGTERM を SIG_IGN で継承する** (request 5043、bnode145: nqs_shpd 252295 `SigIgn=fffffffe7ff8f4ef`、bash 252296 `0x4004`、python 系 `0x1005000`)。
  F1012 と同じ環境事実。handler を明示しない残存子は TERM で死なず、5 秒後の KILL で死ぬ (keep 走がそのとおりに振る舞った)。
- 入れ子 user ns の帰属述語は login で実測 (`verbatim/probe_ns_attribution.out.txt`): 同 uid の入れ子 ns 孤児の `ns/user` を外から readlink でき
  (`user:[4026537420]` ≠ 自分 `user:[4026531837]`)、pidfd の TERM → poll で 0.8 ms で終了を観測、その後 `/proc/<pid>` 不在。計算ノードの `own_user_ns` も `user:[4026531837]` (init ns)。
- 既存の in-process テスト (`_job_run_with_mocked_child` 等、`clear=True` でない `patch.dict`) は login node の pytest session を走査しうる → opt-in の値を request sha に束縛して塞いだ (段 3 A-2)。

## 3. 段 2〜4 (plan → 敵対相談 → 裁定)

- 段 2 plan (`verbatim/plan-out.md`): 5 関数・12 nodeid・6 変異、親 brief P1〜P7 に異議 0。
- 段 3 レンズ A (正しさ境界、`verbatim/consultA-out.md`): real 5 / refuted 4 / nit 2。must-fix = A-1 (同 session 所属は帰属証明でない → ns 帰属述語)、
  A-2 (ambient opt-in `=1` → 値を request sha に束縛)、A-4 (M6 の 1 行変異が赤にならない → 巡数固定に変更)。A-3 (pid 再利用の窓 → pidfd)。A-5 (heartbeat の条件 → `H ≤ G`)。
- 段 3 レンズ B (実効性・実測設計、`verbatim/consultB-out.md`): real 5 / refuted 4 / nit 2。must-fix = B-1 (= A-5)、B-2 (= A-4)、B-3 (総遅延の閾値 `J − W`、`E − W` を追加)、
  B-4 (テスト期限を絶対打切りに、production 定数は mock で検査)。B-5 (F-1 の祖先断定は未採取 → 訂正)。
- 段 4 裁定 (`verbatim/s4-ruling.md`): 所見はすべて real として採用 (refuted 8 件は同意)。plan v2 = §1 の実装仕様。変異 M0〜M7 と計算ノード判定表を事前登録。
  親 brief の訂正: P7 (uid フィルタ) は ns 述語に包含、F-2「唯一の経路」→「今回採る経路」、F-3 行番号。

## 4. 計算ノード実測 (事前登録 → 観測)

器具: T-2675 probe (`probe_t2675_run_membership.py`、sha256 `f781162298f8885bd8d73f9e5d65d0d763fa14cc7e1673dd9961d42f9dc5b3e1`、30,373 bytes、
**repo へは残さず** worktree に untracked で置いて投入後に削除、`cmp` で job dir の原本と同一を確認)。generic task、
`--walltime 00:03:00 --queue-wait-timeout 1800 --overall-grace 2100 --accounting-grace 120 --poll-interval 2`、`--parent-seconds 5 --child-seconds 75`。
順序 no-child → keep (直列、前走の確認後に投入)。記号: W = `supervisor-wait-complete`、S / C = `session-sweep-start` / `-complete`、T = TERM 送信、
G = `session-process-exited` (pidfd の POLLIN)、J = `job-run-returned`、E = `.e` の `Ended Request Time` (JST 秒精度)、H = 最終 heartbeat。

**事前登録の改訂 (§3′、2026-09-18 07:45、投入前):** request 5043 の SigIgn 採取 (07:43) で「job 内の process は SIGTERM を SIG_IGN で継承する」が分かり、
probe の子は SIGTERM handler を持たないので keep の期待を「TERM 終了」から「TERM 無視 → 5 秒 → KILL 終了、`J − W ≤ 8`、`E − W ∈ [−1, 13]`」に改めた。
改訂は結果を見る前 (keep の投入 07:49:01)。原文は `verbatim/s4-ruling.md` §3 と §3′ に並記。

| 指標 | no-child 期待 → 観測 | keep 期待 (§3′) → 観測 |
|---|---|---|
| residual (attributed) | 0 → **0** | 1、pid = evidence `fork` の child_pid、python3、ppid 1 → **1、pid 1230822 = child_pid、python3、ppid 1、ns `user:[4026535834]`** |
| session_unknown / unattributed | 0 → **0 / 0** | 0 → **0 / 0** |
| signal | 0 → **0** | TERM sent → KILL sent → **TERM sent 07:49:15.321、KILL sent 07:49:20.326** |
| 終了確認 | 対象なし → **対象なし** | `after=kill`、`G ≤ C ≤ J`、G < t0+75 → **after=kill 07:49:20.327 ≤ C 20.359 ≤ J 20.381、G − t0 = 10.035 秒** |
| complete | clean、rounds 1、待機なし → **clean、rounds_used 1、30.9 ms** | clean、remaining 0、exited_after_term 0 / kill 1、rounds 2 → **同、5054 ms** |
| `E − J` | [−1, 5] → **−0.468** | [−1, 5] → **−0.381** |
| `J − W` | ≤ 5 → **0.042** | ≤ 8 → **5.077** |
| `E − W` | [−1, 10] → **−0.426** | [−1, 13] → **4.696** |
| heartbeat | 子記録なし → **なし** | 0 件許容、あれば `H ≤ G` → **2 件、H 20.293 ≤ G 20.327** |
| `child-exit` | 該当なし | 不要 → **なし (KILL 終了)** |
| 適格性 | `scheduler-end-state`、`accounting_verified` (receipt `outcome`)、`qdel.attempted=false`、rc 0、`recording_errors=[]`、δ 5.001、orphan hold なし → **全部成立** | 同 → **全部成立** |

集計 script は job dir の `analyze.py`、出力は `verbatim/analyze-*.txt`。会計 `E` は秒精度なので負値は切捨てと整合する (T-2675 と同じ読み)。
生データ: `evidence/probe-*.jsonl` (probe)、`evidence/dispatcher-trace-*.txt` (dispatcher の `.e`)、`evidence/accounting-*.txt` (NQSV 会計)。
submission dir は wave worktree の `output/pegasus-dispatch/` (`5077` → `32ef6ca5c71c1bf2159d58411483e2f1`、`5086` → `ebb7857a8efab70dc3b6acdff6a59b72`)。

**2 軸の結論:** 会計・総遅延 = 合格、独立した消滅確認 = 合格 → 「当該条件で終了遅延短縮と残存子消滅を確認」。`E − J` の短縮だけを成果にしていない。
反復・別ノード・別時間帯は各 1 走 (前 2 wave の同器具で 70 秒窓が再現済みのため反復しない、段 4 P5)。

## 5. 段 5〜6 (実装 → 焦点走 → レビュー → fix)

- author (`verbatim/s5-author-out.md`): 6 関数、14 nodeid、hook が sandbox 内の pytest / import を拒否したため未実走 (正直申告)。
- 親の焦点走 1 (段 5 版、`run_tests.py` の自動 dispatch → 計算ノード `5015.nqsv`): **14 passed / 1 failed** — `test_session_sweep_terminates_attributed_orphan_and_preserves_others`
  (term mode の孤児が `after=term` で exited に無い)。login 再現 (`verbatim/probe_term_repro.term.out.txt`) は 0.5 ms で正常 → 計算ノード固有。
  仮説「祖先が SIGTERM を SIG_IGN で継承させている」を request 5043 の probe で確定 (§2)。**F1012 の再発** (fixture が signal の既定動作を継承状態に依存した)。
  同 job の job body sweep は本番経路で走った (evidence `dispatcher-trace-5015-focus-new1.txt`: found 0、clean、33.8 ms)。
- 段 6 レビュー A (`verbatim/reviewA-out.md`): real 3 / refuted 4 / nit 1、NO-GO。RA-1 (fixture が既定動作を確立していない)、RA-2 (session 不明の stat 不読が集計を汚す)、
  RA-3 (M2 は挙動を検出しない → diagnostic sensitivity pin)。
- 段 6 レビュー B (`verbatim/reviewB-out.md`): real 2 / refuted 4 / nit 1、NO-GO。RB-1 (期限・猶予の根拠)、RB-2 (finally が group 全員の終了を確認しない)。
- 段 6 裁定 (`verbatim/s6-ruling.md`) → fix (`verbatim/s6-fix-out.md`): F1 fixture の C / G に `SIG_DFL` + `pthread_sigmask(SIG_UNBLOCK)` を明示、失敗時に records を出す。
  F2 期限 = 準備 15 / sweep 20 / 回収 10 秒の絶対打切り、scanner は production wrapper を production 定数のまま走らせる。F3 finally は L / D / N / C / G の pidfd で
  回収期限内の全員終了を確認。F4 `unreadable` → `session_unknown`、status ∈ {clean, remaining, unknown}。
- 親の焦点走 2 (fix 後、login、file 全体): **353 passed / 27.19 秒** (既存 339 + 新規 14)。
- 全史 provenance 監査 (実装 commit 後): 11,207 件、新規違反なし。

テスト 14 nodeid: 実 process 3 本 (`…terminates_attributed_orphan_and_preserves_others` / `…kills_sigterm_ignoring_orphan` / `…rescans_for_late_orphan`) と
fake `/proc` / pidfd 11 本 (`…stat_parses_spaced_parenthesized_comm` / `…without_opt_in_does_not_touch_processes` / `…ancestry_unreadable_aborts` /
`…rechecks_identity_before_signal` / `…does_not_claim_unconfirmed_disappearance` / `…records_signal_errors_and_zombies` / `…stops_at_round_limit` /
`test_job_run_sweeps_before_result_and_strips_opt_in` / `…sweeps_after_isolation_failure_without_replacing_guard` / `…sweep_error_preserves_child_result` /
`test_session_residuals_filter_namespace_and_unreadable_stat`)、既存 job script 検査へ export 行の assert。

## 6. 変異 matrix

container = `.codex/worktrees/t2676-mutcontainer` @ `1e4d0bbd1` (submodule 再帰初期化済み)。`tools/mutation_harness.py --runner-mode dispatch --detached` を直接当て、
runner は `python3 tools/run_tests.py orchestrator/tests/test_pegasus_dispatch_compute.py -q -rf --force-dispatch`、D612 の queue-wait / grace 上書き 1800 / 600。
spec と台帳は job dir (`mutation-spec-probe.json` sha256 `9c1cf6e1…` / `mutation-spec-final.json` sha256 `b651bdbe…`、`mutation-probe.json` / `mutation-final.json`)。
事前登録は `verbatim/s4-ruling.md` §2 (意味と期待 nodeid)、1 行 anchor は `verbatim/s6-fix-out.md` の表 (fix 後に再照合、各 1 箇所)。
DW-M08 に従い probe 走 (全件 SURVIVED 登録) で観測 node の完全集合を採り、その集合を KILLED 期待に登録して本走した。drift mask (mutation と無関係に赤になる層) は
M0 が 0 件で **無し** (対象 file が `test_pegasus_dispatch_compute.py` 1 本で、dispatcher の HEAD blob pin を持つ test が同 file に無い)。

| id | 1 行の変更 (関数) | 事前登録の期待 nodeid | probe 観測 (完全集合) | 本走 |
|---|---|---|---|---|
| m0-equivalent-docstring | `_read_session_process` の docstring 言い換え | SURVIVED | SURVIVED (赤 0) | **SURVIVED** (赤 0、注入 diff sha 4dec384f…、48.0 秒) |
| m1-sweep-call-removed | `_job_run` の `_maybe_sweep_job_session(request_sha256)` → `pass` | `test_job_run_sweeps_before_result_and_strips_opt_in` | 同 + `…sweeps_after_isolation_failure_without_replacing_guard` + `…sweep_error_preserves_child_result` (3) | **KILLED**、期待 = 観測 (3) |
| m2-ancestor-exclusion-self-only-pin | `_maybe_sweep_job_session` の `excluded = {…ancestors}` → `{os.getpid()}` | **別枠 (diagnostic sensitivity pin)**: 除外集合の内容 assert | 実 process 3 本 + `…without_opt_in_does_not_touch_processes` (4) | **KILLED**、期待 = 観測 (4)、別枠 pin |
| m3-opt-in-ignored | wrapper 先頭の sha 判定 → `if False:` | `…without_opt_in_does_not_touch_processes` | 同 + `test_job_run_sweeps_before_result_and_strips_opt_in` (2) | **KILLED**、期待 = 観測 (2) |
| m4-kill-stage-removed | `_sweep_job_session` の SIGKILL 送信 → `pass` | `…kills_sigterm_ignoring_orphan` | 同 + `…does_not_claim_unconfirmed_disappearance` (2) | **KILLED**、期待 = 観測 (2) (所要 621 秒は queue 待ち 9.6 分、job の Elapse 32 秒) |
| m5-exit-confirmation-forged | `_poll_session_processes` の `poller.poll(…)` → 全 fd を POLLIN に捏造 | `…does_not_claim_unconfirmed_disappearance` | 同 + `…kills_sigterm_ignoring_orphan` (2) | **KILLED**、期待 = 観測 (2) |
| m6-single-round | `for round_index in range(rounds)` → `range(1)` | `…rescans_for_late_orphan` | 同 + `…stops_at_round_limit` (2) | **KILLED**、期待 = 観測 (2) |
| m7-attribution-always-true | `_list_session_residuals` の `attributed = …` → `True` | `…terminates_attributed_orphan_and_preserves_others` (N が死ぬ) | 同 + `…residuals_filter_namespace_and_unreadable_stat` + 実 process 他 2 本 (共有 fixture の N 非帰属 assert) (4) | **KILLED**、期待 = 観測 (4) |

baseline (container、計算ノード): probe 走 PASSED 47.8 秒 / 本走 PASSED 63.8 秒 (353 node)。**本走: M0 SURVIVED、M1〜M7 KILLED、期待 node 完全一致、MISMATCH 0** (`mutation/mutation-final.json`)。probe 走 8 変異は全件が事前登録の nodeid を含む赤を出し、追加の赤は同じ機構を別角度で検査する
新規 node だけ (既存 339 node は全変異で緑)。**M2 は挙動 (L の死) でなく内部状態 (除外集合) を pin する別枠**であり、「祖先の誤殺を検出した」とは書かない
(帰属述語が先に L を守る冗長 gate、段 6 RA-3)。

## 7. 言えないこと

| 項目 | 理由 |
|---|---|
| 実 workload (pytest / xdist の worker、FIFO で block した孫、TERM handler 付き、割込み不能 I/O) の回収 | generic 単一子で測った。受入全走の緑は「残存が無かった」ことしか示さない (sweep は失敗しても rc を変えない) |
| 計算ノードでの TERM 終了経路 | job は SIGTERM を SIG_IGN で継承するので、handler を持たない残存子は KILL でしか死なない。TERM 終了は login のテストでだけ確認 |
| 別 session へ移った process、sweep 到達前に直接の子が戻らない経路 (`communicate` / `wait` が返らない) | scope 外 (D2124: 元 session の列挙では拾えない) |
| pid 再利用の完全排除 | pidfd 取得後は固定されるが、列挙〜pidfd_open の窓は starttime 再照合に依る (二重再利用は排除できない) |
| session leader `nqs_shpd` の保護の一般性 | 4 job で同形の祖先鎖を観測。同 session の非祖先 NQSV process の有無は「見つからなかった」(found 0) まで |
| 時間上限 | 5 秒 / 1 秒 / 2 巡は設計値。kernel 内の停止や同期 stderr 書込みの閉塞までは保証しない。watchdog は新設していない |
| job 内 SIGTERM の扱い | `_SignalAbort` は `dispatch()` (login 側) の handler で、`--job-run` 経路には無い。job 内で SIGTERM を受けた場合の sweep の挙動は未測 |
| 反復性 | 各条件 1 走、別ノード (bnode073 / 080) |

## 8. 次の一手候補 (実装しない)

- dispatcher が `_job_run` の先頭で SIGTERM を `SIG_DFL` に戻し、子孫へ既定を継承させる案 — TERM 猶予 5 秒が効くようになるが、job body 全体の signal 環境を変え
  受入 suite の既存挙動 (F1012 で対処済みの fixture 等) へ波及しうる。別 wave の裁定。
- 受入全走の `.e` に残る `session-sweep-complete` を集計し、実 workload で残存が出た回数と種類を数える (今は 0 件しか観測していない)。

## 9. 一次資料の所在

job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2676-job-session-sweep/` に全成果物 (prompt、log、patch、probe、spec、台帳) を保全。
`verbatim/` は job dir の原文と byte 同一 (`cp`、正規化なし)。原文の同定:

| `verbatim/` の file | 中身 | 原文の SHA-256 | bytes |
|---|---|---|---|
| `s1-brief.md` | 段 1 brief (P1〜P7) | `7bfc123d017bd8a05148cf854356876ba878609c2757c594f4601d34104cc86f` | 5896 |
| `facts.md` | 親の実測事実 F-1〜F-6 (段 3 後に訂正) | `d9d023e65ce603415f07c55e9aa69ae4bf634b3ae2425e08bfbf3bab060677e7` | 5910 |
| `plan-out.md` | 段 2 plan | `0b3187f084f64806533ec79ebaa1291300d58af9ac5d9d5cdfc90c87371efcfc` | 21503 |
| `consultA-out.md` / `consultB-out.md` | 段 3 敵対相談 | `a8c8e21ad48afc7894371bbee75fd10f39a9774b9d951c41a651fd6ce5af0a08` / `eb740a78244d0dd63b8a0e9cc271f8b7222189d5a9915384f0eb9439bc5649b0` | 12854 / 17575 |
| `s4-ruling.md` | 段 4 裁定 (§3 事前登録、§3′ 改訂) | `7a6fed2823cd0e57a0cb52537c0f7b6b8d37bf0cb3e8dc08bb73b590ec9a3ee8` | 20685 |
| `s5-author-out.md` | 段 5 author 報告 | `dae06900d49d396a41e0c8b27bad5baf5e740cd839097b357a82c80cd3f08b87` | 9755 |
| `reviewA-out.md` / `reviewB-out.md` | 段 6 レビュー | `8998766b42c5eb9e86d73d3e961f9e02637acf2ce0cf577b94fdec9499d10468` / `0a04152be96150da589fb306298f12b32d44e6fe1998fd3f17f8a048bb053cf2` | 12483 / 11499 |
| `s6-ruling.md` / `s6-fix-out.md` | 段 6 裁定 / fix 報告 | `93a83a7e9cd7e929233d30ca5ec11ce656b684e74f45876ec92b78bec671336d` / `b70758e00572e6cf98880a75f14250e6ff26994c46e8e925b04769c85ee69bac` | 3551 / 3325 |
| `probe_ns_attribution.out.txt` | login 実測 (ns 帰属 / pidfd) | job dir 同名 | 480 |
| `probe_term_repro.term.out.txt` | login 再現 (term mode) | job dir 同名 | 1355 |
| `sigign-5043.txt` | 計算ノード SigIgn 採取 (request 5043) | `sigign.log` から dispatch 行を除いた射影 | 3923 |
| `analyze-no-child.txt` / `analyze-keep.txt` | 判定材料の集計 | job dir 同名 | 989 / 1441 |

probe 3 本 (`probe_ns_attribution.py` / `probe_term_repro.py` / `probe_sigign.py`) と T-2675 probe の複製は job dir にだけある (repo へ入れない)。

## 10. 段 3 / 段 6 で親が直したこと

**棄却した所見は無い。** 段 3 (A-1〜A-11、B-1〜B-11) と段 6 (RA-1〜RA-8、RB-1〜RB-7) の real 所見はすべて採用し、refuted は同意した。
1. 走査対象の帰属を「session 所属」から「session 所属 かつ 入れ子 user ns」へ (A-1)。2. opt-in の値を request sha に束縛 (A-2)。3. signal と終了観測を pidfd へ (A-3)。
4. M6 を巡数固定へ、M2 を別枠へ (A-4 / B-2 / RA-3)。5. heartbeat の条件を `H ≤ G` へ (A-5 / B-1)。6. `J − W` / `E − W` の閾値を追加 (B-3)。
7. テスト期限を絶対打切りへ、production 定数をそのまま走らせる (B-4 / RB-1)。8. F-1 の祖先断定を撤回し、実 trace で祖先鎖を採った (B-5)。
9. fixture に SIG_DFL + unblock を明示 (RA-1)。10. `session_unknown` と status の分離 (RA-2)。11. finally の全員終了確認 (RB-2)。
12. keep の期待を投入前に §3′ で改訂 (SigIgn の新事実)。
