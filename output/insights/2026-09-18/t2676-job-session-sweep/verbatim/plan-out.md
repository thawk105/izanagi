## 総括

- 実装・テストの変更は **2 files**。新規 production 関数は **5本**、新規 nodeid は **12本**、事前登録する変異は **6本**。
- 親の成果物である insight・worklog・decisions fragment は上記2 filesとは別。
- P1〜P7の方針への異議は **0件**。P4の「5秒／2回」は下記で時間上限を具体化する。
- 正しさゲート、result schema、bootstrap、reparenting は変更しない。
- 実アンカー補正：isolation失敗の早期returnは `tools/pegasus/dispatch_compute.py:1685–1687`。
- 指定資料による静的検査のみ実施。書込み・テスト・計算ノード投入は実施していない。

## 1. 走査の実装

`tools/pegasus/dispatch_compute.py:168` 付近にenv名と時間定数、`:719` の後に次の5関数を追加する。

| 新規関数 | 責務 |
|---|---|
| `_read_session_process(pid)` | statとuidを読み、process情報を返す |
| `_list_session_residuals(sid, excluded_pids, deadline)` | `/proc`の数値ディレクトリを列挙し、sessionと除外集合で絞る |
| `_signal_session_process(record, sid, sig)` | signal直前の同一性・session再確認、signal、結果のtrace |
| `_sweep_job_session(sid, *, term_grace_s, kill_grace_s, rounds, budget_s)` | 祖先除外、列挙、TERM/KILL、消滅確認 |
| `_maybe_sweep_job_session()` | opt-in無しのearly return、sid取得、例外のtrace化 |

祖先鎖の構築と消滅確認のループはsweep内に置き、一般的なprocess管理APIへ切り出さない。

**statのparse**

既存probeの `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2675-nqsv-run-membership/probe_t2675_run_membership.py:33–40` と同じfield配置を使う。

```python
left = raw.index("(")
right = raw.rindex(")")
pid = int(raw[:left].strip())
comm = raw[left + 1:right]
tail = raw[right + 1:].split()
```

| statのfield番号 | 意味 | `tail` index |
|---|---|---|
| 3 | state | 0 |
| 4 | ppid | 1 |
| 5 | pgrp | 2 |
| 6 | session | 3 |
| 22 | starttime | 19 |

`comm`全体を先に空白分割しない。短いfield列、不正整数、括弧欠落は読取り異常として記録し、そのprocessへsignalしない。

**選択と除外**

- productionでは `_maybe_sweep_job_session()` が `os.getsid(0)` を渡す。
- sweep実行process自身を除外する。そのstatのppidから祖先のstatを辿り、PID 1まで除外集合へ追加する。sessionが違う祖先でも辿る。
- PID 0、既訪問PIDで打ち切る。祖先鎖を読めず除外集合を確定できない場合は、当該sweepを診断付きで終了する。未知の祖先を候補へ混ぜない。
- session leaderをpid==sidという理由だけで扱うのではなく、実際の祖先鎖で除外する。実測dispatcher `3010049`、sid `3010029` に対応する。
- 列挙対象のENOENT／ESRCHは走査中の消失として継続する。EACCES／EPERMやparse異常は「残存ゼロ」の根拠にしない。

**同一性と記録**

追跡キーは `(pid, starttime)`。signal直前と確認時に再読し、starttimeが変われば古い対象は消滅、新しいprocessにはその記録からsignalしない。sessionが変われば `left-session` として以後signalしない。

`_job_trace` は既にトップレベルの `pid` を発行者に使うため、`:710–718` の意味を保ち、対象情報はネストする。

```text
session-residual:
  round, sid,
  process={pid, ppid, comm, state, uid, starttime, pgrp, session}
```

uidは `/proc/<pid>/status` の `Uid:` 先頭値を使用し、読めなければnullと読取り異常を記録する。uidはsignal可否のフィルタにはしない。cmdlineは今回不要で、追加しない。

starttime再確認と`os.kill`は原子的ではない。再確認からsignalまでのPID再利用・session変更の競合窓は残る。これは「同一性を完全に固定できる」とは報告しない。厳密なPID固定まで要求するならpidfd送信が追加設計になるが、本案はP1〜P7の局所的な`os.kill`方式とする。

## 2. signalと消滅確認

P4を **TERM猶予5秒、最大2巡** と具体化する。各巡のKILL後確認は最大1秒、全体はmonotonic基準で最大13秒を処理上の予算とする。分布に基づく最適値ではなく、暫定の有限上限である。

1. 初回列挙を行い、各対象を `session-residual` に記録する。
2. 同一性・session・非zombieを再確認し、SIGTERMを送る。
3. 対象のstatを50ms間隔で確認する。全対象が消えれば5秒を待ち切らない。
4. TERM猶予後にsessionを**再列挙**する。
5. TERM済みでなお生きている同一対象へSIGKILLを送る。
6. 最大1秒、消滅を確認する。
7. KILL後にもsessionを再列挙する。新規対象があれば、残り1巡でTERMから扱う。
8. 最終列挙と追跡対象の確認を行い、残存・不明を含む集計を出して終了する。

後の列挙で初めて見つかったprocessを、TERM猶予なしで直ちにKILLしない。2巡目の後にも増殖・残存があれば未完了として記録し、無限に追わない。

**reparentingについて**

ppidが1へ変わってもsidは変わらないため、既存の孫は最初から列挙対象になる。再列挙が必要なのは、reparentingそのものより、列挙中のforkやTERM処理中に現れたprocessを拾うためである。KILL後の再列挙もこの窓に対応する。

**例外とzombie**

| 状態 | 処置 |
|---|---|
| `ProcessLookupError` | signal対象が消えた可能性として記録し、stat再読で確認 |
| `PermissionError` | `session-signal-error` にerrno、対象、signalを記録。継続する |
| その他のsignal／読取り異常 | 診断を残す。jobのrcを変更しない |
| state=`Z` | TERM/KILL対象から除外。消滅済みには数えない |
| `/proc`不在 | `session-process-gone`, reason=`absent` |
| starttime不一致 | 同事象、reason=`identity-changed` |
| 同一processが別sessionへ移動 | `session-process-left-session`。死亡・消滅とは区別 |
| deadline時に同一zombieが存在 | `zombie_remaining`。生存残存とは分け、消滅未確認には含める |

非子processへの`waitpid`は導入しない。

traceは `session-signal-attempt`、`session-signal-result`、`session-process-gone`、最後に `session-sweep-complete` を使う。最後の事象は処理終了を意味し、成功の同義語にしない。`status`、初回件数、累積対象件数、消滅件数、生存残存、zombie残存、session離脱、読取り異常、期限到達、経過時間を記録する。

## 3. 発火条件

env名は **`IZANAGI_DISPATCH_JOB_SESSION_SWEEP`**、有効値は厳密に `"1"` とする。

- `tools/pegasus/dispatch_compute.py:911` のSHA exportの隣に `export IZANAGI_DISPATCH_JOB_SESSION_SWEEP=1` を追加する。
- `:1627` のrequest hashのpop直後に `child_env.pop(_JOB_SESSION_SWEEP_ENV, None)` を追加する。
- `child_env.update(requested_env)` より後なので、最終的なchild環境から確実に除去する。
- requestのenv allowlistへは追加しない。
- `main:4485–4501` は変更しない。

`_maybe_sweep_job_session()` の先頭は次の形とする。

```python
if os.environ.get(_JOB_SESSION_SWEEP_ENV) != "1":
    return
```

この判定より前にgetsid、祖先読取り、`/proc`列挙、signalを行わない。これでenv不在の既存in-process呼出しは **列挙ゼロ・signalゼロ** になる。呼ばれるのは無処置のwrapperだけで、実sweepは呼ばれない。

`tests`／`provenance` はinherit（`:116–142`）なのでpopは必須。`generic`／`mutation`でも同じpopを通す。job scriptをテスト内で生成しただけではexportは実行されないため、既存helperのscript生成は発火原因にならない。

isolation失敗経路でも、子起動段へ到達した場合は走査する。guard生成失敗、request検証失敗など、子起動前の失敗では走査しない。

## 4. `_job_run`内の配置

`tools/pegasus/dispatch_compute.py:1684`、例外処理の後かつ `if isolation_failed:` の前へ置く。

```python
if stage in ("child", "child-launch"):
    _maybe_sweep_job_session()
```

`:1647` でstageがchildになるため、通常終了、子起動の一般例外、`_ChildIsolationError`を扱える。検証段の失敗は対象外となる。

wrapper内でsweepの`Exception`を受け、`session-sweep-error`へ記録する。既存のchild実行を囲むtryへ入れると、sweep例外が`:1678–1681`で`INFRA_RC`へ変換されるため、それは避ける。

この配置には次の利点がある。

- isolation失敗では既存のguardと`INFRA_RC`をそのまま保持する。
- 通常経路では`:1704`のresult公開前に終了確認が終わる。
- `main:4490／4499` の `job-run-returned`、すなわちJはsweep後になる。
- `_is_bound_job_envelope:1519–1526` のsubstring契約は追加exportで壊れない。

ただし、**E−Jだけでは遅延をsweep内へ移しただけでも短縮して見える**。実測ではsweep所要時間と、`supervisor-wait-complete`からEまでの時間も併記する。会計終了と対象processの消滅は別の証拠で評価する。

## 5. テスト設計

追加先は `orchestrator/tests/test_pegasus_dispatch_compute.py:4157` のhelper付近。以下はすべて同fileのnodeidで、parameterizeによる増加を避けて **12 nodeid** とする。

| nodeidの関数名 | 検証内容 |
|---|---|
| `test_session_stat_parses_spaced_parenthesized_comm` | 空白・複数括弧を含むcomm、field index、壊れたstat |
| `test_session_sweep_without_opt_in_does_not_touch_processes` | env不在／`0`でgetsid・列挙・signalゼロ |
| `test_session_sweep_term_orphan_preserves_ancestors_and_other_session` | 実孤児のTERM消滅、祖先leader生存、別session生存 |
| `test_session_sweep_kills_sigterm_ignoring_orphan` | 実孤児のTERM無視、KILL送信、消滅 |
| `test_session_sweep_rechecks_identity_and_session_before_signal` | starttime変化・sid変化の候補へsignalしない |
| `test_session_sweep_rescans_for_late_orphan` | 再列挙で初めて出る孫へ次巡でTERM、その消滅 |
| `test_session_sweep_does_not_claim_unconfirmed_disappearance` | kill成功後もstatが残る場合、成功扱いしない |
| `test_session_sweep_records_signal_errors_and_zombies` | ESRCH、EPERM、読取り不明、Zの区別 |
| `test_session_sweep_stops_at_deadline` | 偽clockで2巡・全体予算を超えず未完了を記録 |
| `test_job_run_sweeps_before_result_and_strips_opt_in` | env有無、child環境、sweep→result順序、非ゼロchild rc保持 |
| `test_job_run_sweeps_after_isolation_failure_without_replacing_guard` | isolation失敗時もsweep、guard保持 |
| `test_job_run_sweep_error_preserves_child_result` | sweep例外が成功／失敗のchild rcとpayloadを変えない |

**実process fixture**

pytestは `Popen(..., start_new_session=True)` でleader Lを作る。Lがscanner Sと短命親Pをforkし、Pが孤児候補Cをforkして終了する。Sは同じsession内でsweepを実行する。これにより **Sのpid≠sid、LがSの祖先** という実測構造を再現できる。

- Cの準備完了とPの終了はpipeで同期する。固定sleepで孤児化を推測しない。
- 別sessionの対照Dはpytestから別途 `start_new_session=True` で起動する。pidとstarttimeをSへ渡す。
- Sが渡すsidは自身の `os.getsid(0)` のみ。pytest側でproduction sweepを実行しない。
- LはTERM既定動作とし、祖先除外削除の変異で実際に終了してテストが赤になる。
- S・Cのstdout/stderrはfileまたはDEVNULLへ向け、孫のPIPE保持でpytestのcommunicateが待ち続けないようにする。
- pytestのfinallyが、自ら作ったLのgroupとDを回収し、直接の子をwaitする。fixture内では追加のprocess groupを作らない。

通常の実processテストは各2秒以内を回復上限とし、TERM猶予0.1秒、KILL確認0.3秒を引数で指定する。2本の正常走行は合計数秒を目標とする。他の10本はfake `/proc`・fake clock・mock signalで実待機ゼロ。負荷下での時間上限の妥当性は親の受入全走で確認する。

`_job_run_with_mocked_child:4083–4157` は、任意のchild例外注入を追加すれば再利用できる。sweepのmockとenv設定は各テストの外側contextに置き、既存の `(rc, calls)` 契約を維持する。opt-inを有効にする統合テストは必ず実sweepをmockする。

job scriptのexportは既存script検査にassertを追加する。上記新規nodeid数へは含めない。

## 6. 変異事前登録

新規コードの行番号はauthor後に固定する。以下の**単一行編集**と期待nodeidを結果を見る前に登録する。期待はすべてKILLEDであり、実測済みではない。

| 変異 | 1行の変更 | 赤になるnodeid／判定 |
|---|---|---|
| M1 sweep呼出し削除 | `_maybe_sweep_job_session()` を `pass` に置換 | `test_job_run_sweeps_before_result_and_strips_opt_in`：有効env時のsweep呼出し欠落 |
| M2 祖先除外削除 | `pid in excluded_pids` の除外条件を `pid == os.getpid()` に縮小 | `test_session_sweep_term_orphan_preserves_ancestors_and_other_session`：Lが死亡 |
| M3 opt-in無視 | wrapper先頭のenv条件を `if False:` に置換 | `test_session_sweep_without_opt_in_does_not_touch_processes`：列挙等のmock呼出しが非ゼロ |
| M4 KILL段削除 | SIGKILLを送る1行を `pass` に置換 | `test_session_sweep_kills_sigterm_ignoring_orphan`：C生存、KILL記録欠落 |
| M5 消滅確認削除 | 最終確認用stat読取りを `current = None` に置換 | `test_session_sweep_does_not_claim_unconfirmed_disappearance`：残存を誤ってgoneと判定 |
| M6 再列挙削除 | TERM猶予後の再列挙代入を初回snapshotの再利用に置換 | `test_session_sweep_rescans_for_late_orphan`：初回snapshotにないCへのTERM・消滅記録欠落 |

M6は単なる「列挙関数の呼出し回数」ではなく、新しいprocessの処置をassertする。M5もtrace行の存在だけでなく、同じstatが残る間は`gone`件数ゼロ・未完了になることをassertする。

M2・M4が赤でもfixtureのfinallyで回収し、変異自体が受入runnerを残さない設計にする。

## 7. 計算ノード実測

親が投入前に、以下の手順・適格性・判定表を新しいinsightへ固定する。

1. 指定probeをworktreeの `tools/probe_t2675_run_membership.py` にuntrackedでコピーする。
2. SHA-256が `f781162298f8885bd8d73f9e5d65d0d763fa14cc7e1673dd9961d42f9dc5b3e1`、30,373 bytesであることを確認する。
3. `output/insights/2026-09-18/t2676-job-session-sweep/evidence/` を作り、no-child→keepの順に各1走する。
4. dispatcherを親のdetached実行経路から起動する。dispatcher CLI自体に`--detached`はない（`:4504–4540`）。

投入argvは次の形とする。`CONDITION`は親が各回 `no-child`／`keep` に置き換える。

```bash
python3 tools/pegasus/dispatch_compute.py \
  --task generic \
  --walltime 00:03:00 \
  --queue-wait-timeout 1800 \
  --overall-grace 2100 \
  --accounting-grace 120 \
  --poll-interval 2 \
  -- python3 -B tools/probe_t2675_run_membership.py \
  --condition CONDITION \
  --parent-seconds 5 \
  --child-seconds 75 \
  --evidence output/insights/2026-09-18/t2676-job-session-sweep/evidence/probe-CONDITION.jsonl
```

**適格性を成功条件から分離する。**

共通の適格性はrequest・host・J・Eの対応、完全なJSON記録、記録異常なし、予定したprobe引数、親終了がt0+4.5〜10秒、scheduler-end-state、会計検証済み、qdel不発火。keepではfork／child-startと対象のpid・starttime・sidが照合できることを追加する。欠測で適格性が崩れたら、その先の投入を止め、事後に基準を緩めない。

| 項目 | no-child期待 | keep期待 |
|---|---|---|
| 初回residual | 0件 | 1件、probe子と同一 |
| signal | 0件 | 対象へTERM成功、KILL不要 |
| 独立した消滅確認 | 対象なし、走査完了 | 対象の`absent`または`identity-changed`をJ以前に記録 |
| 最終状態 | 生存・Z・不明すべて0 | 同左 |
| `E − J` | [−1, 5]秒 | [−1, 5]秒 |
| sweep所要時間 | 全体予算内 | 全体予算内、TERM段で終了 |
| heartbeat | 子記録なし | 最終heartbeat時刻がTERM送信直前のattempt時刻以下 |
| 子の自然寿命 | 該当なし | t0+75秒より前に消滅 |

heartbeatが1件も残らない可能性は、親終了と初回heartbeatがともにt0+5秒なので事前に許容する。その場合は「heartbeat比較は該当なし」とし、child-start・residualの生存状態・signal・消滅確認で評価する。heartbeatが存在する場合は上表の時刻条件をそのまま適用する。

probeはSIGTERM handlerを設けず、自然終了時だけ `child-exit` を出す（probe`:221–264`）。したがって **TERMで終了したkeepにchild-exitを要求しない**。これは今回の投入前に決める観測契約で、旧waveの適格性を事後変更するものではない。

判定は次のように固定する。

- 両条件が適格かつ全期待を満たす：限定したgeneric probeで対策成立。
- E−Jのみ短縮、消滅未確認：回収成功とは判定しない。
- 消滅確認あり、E−Jが窓外：回収と会計遅延を分離し、目的未達。
- residual件数違い、EPERM、期限到達：期待外の結果として対象情報を残す。除外して成功扱いしない。
- 証拠不足：判定不能。追加走は新たな事前登録後に扱う。

sweep開始・終了、supervisor終了、J、E、最終heartbeatを並べ、E−J短縮だけを成果にしない。probeはcommit対象から除外する。

## 8. F973の再発検知

**production変更については、reparenting変更に伴うconsumer列挙義務は非該当といえる。**

`tools/pegasus/dispatch_compute.py:282` のfork、`:328` の正のpidに対するwaitpid、`:1131` のPopenを変えず、subreaper・PID namespace・setsidを追加しない。既知consumerの `tools/codex_worker_launch.py` と `tools/dev_waves/worker.py` の計数契約も変更しない。

新規fixtureのsetsid相当は独立したテスト子のsession分離であり、production jobのreparenting変更ではない。

job内pytestのassertionは、pytestとrunner、supervisorが戻る前に実行される。本sweepはその後なので、`test_sigterm_ignoring_child_is_killed` の実行中に本sweepがzombie回収の時機を変える経路はない。envのpopがその順序を守る前提である。

ただし、**相互作用が一切ないとは断定しない**。pytest終了後に残った補助processは本変更の対象になり得る。焦点走だけでは閉じず、親が受入全走で既存の残存group計数テストを含めて確認する。F973で問題となった`Z`を既存consumerから除外する変更は行わない。

## 9. リスク

| リスク | 本案の扱い・限界 |
|---|---|
| NQSVのroot／nqs process | 祖先は除外する。同sessionの非祖先はP1どおり対象となり、EPERMを記録する。uidフィルタは追加しない |
| NQSV側の同uid非祖先 | signal可能なら終了対象になる。実測資料は祖先の存在を示すが、全非祖先がworkloadだとは証明していない。no-childで残存0という期待を必ず検証する |
| testsへのenv漏れ | `child_env.update`後のpopで遮断し、inherit経路を統合テストで検証する。runner内の環境を別途再構築する必要はない |
| 走査の長時間化 | 各列挙entry・signal・pollで共通deadlineを確認し、sleepも残予算以下にする。期限到達時は未完了で終了する |
| 厳密な時間上限 | 13秒は協調的な処理上限。`/proc` syscallや既存`_job_trace`の同期stderr書込みがkernel内で止まる場合まで保証できない。新しいwatchdog機構は導入しない |
| stdout／stderr | 残存processの終了でfdは閉じるが、未flushの出力は失われ得る。trace自身も同じstderrを使う。fd保持をNQSV遅延の必要条件とは説明しない |
| provenance | inherit envからopt-inを除去する。checkerの直接終了後に残った同session processだけが対象。監査rcを上書きしない |
| mutation | wrapperが戻った後の同session残存を対象とする。別sessionのdetached processには触れず、mutationの成否や既存markerを変えない |
| PID再利用・session離脱 | signal直前の再確認で扱うが、確認とsignalの競合窓は残る。session離脱を消滅と数えない |
| job bodyが戻らない経路 | `_run_isolated_child:1151` のcommunicateや`:1194`のwaitが戻らなければ本sweepへ到達しない。本変更は「直接の子が戻った後」の対処に限定する |

親による焦点走・6変異・計算ノード2走・受入全走が完了するまでは、実装案の成立と実測上の解決を区別する。