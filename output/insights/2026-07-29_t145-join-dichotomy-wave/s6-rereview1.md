結論は **NO-GO** です。指定9ファイルと段6関連規約を全文確認し、最終 tracked diff 全体を静的監査しました。pytest・mutation・編集は行っておらず、green/KILL は主張しません。

最終差分は `orchestrator/tests/test_dev_waves_integration.py` だけで **+411/-26**、production差分は0です。親ceilingは直下childのhangを有限化し `INFRA_TIMEOUT` の赤にしますが、process tree全体のcontainment、構造化結果、relay identity、割込み帰属がまだ閉じていません。

## 新所見

### `[blocker][real]` 直下childしかsignal/reapせず、worker/grandchildがcontainment外へ逃げる

親は [`integration.py:1531`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1531) で `start_new_session=True` によりchildを新session/groupのleaderにします。しかしtimeout時のsignal targetは [`integration.py:1546`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1546) の `process.terminate()` と [`integration.py:1557`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1557) の `process.kill()`、すなわち直下PIDだけです。`os.killpg()` は使われず、新sessionはcontainmentに利用されていません。

さらにSupervisorが起動するworkerは [`worker.py:623`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/worker.py:623) で再度 `start_new_session=True`、fake childも [`worker.py:368`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/worker.py:368) で別process groupを作ります。

```text
pytest worker
└─ harness child        session/group H  ← 現在はPID HだけTERM/KILL
   └─ worker wrapper    session/group W  ← Hから離脱
      └─ fake child     process group C
         └─ grandchild  group Cまたはさらに離脱
```

`PR_SET_PDEATHSIG` は直系PIDの死には有効ですが、grandchild全体のgroup kill/reapを保証しません。直下childの `poll() is not None` は、W/Cが消えた証拠ではありません。

成果物影響: timeout変異後のorphan worker/grandchildが後続node・temp repo・試行台帳を汚染し、受入結果の独立性を失います。

### `[must-fix][real]` structured resultは基本exit対応だけで、JSON envelopeがfail-closedではない

[`integration.py:1585`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1585) はprefix行が1本であることを確認しますが、[`integration.py:1596`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1596) 以降に次の検証がありません。

- dictのexact key集合
- fieldの型
- PASS時の `exception_type=None / args=[] / traceback=""`
- FAIL/SKIP時の非空type・traceback
- SKIPの非空reason
- extra key、duplicate key、非canonical値

したがって、stdoutに1本だけ

```text
T145_SERVE_RESULT={"outcome":"PASS"}
```

がありexit 0ならPASSとして受理されます。JSON破損やmissing `outcome` は例外になり赤なので、その部分はfail-closedです。またPASS/SKIPはexit 0を要求しています。しかしshape全体は束縛されていません。

成果物影響: abnormal childが最小の偽PASS envelopeを出すと、対象nodeとmutation台帳を偽緑で認証します。

### `[must-fix][real]` reader roleは型までで、実SignalRelayへ束縛されていない

[`integration.py:1296`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1296) は「socket 1個＋int 1個」を確認しますが、intが実 `SignalRelay.fileno()` かは確認しません。

次のproduction mutationは通過可能です。

```python
[bound.sock, relay.fileno()]
# →
[bound.sock, lease._fd]
```

`lease._fd` は有効なintで、型検査を通ります。request socketは引き続き処理でき、テストはAPI経由で `_shutdown` Eventを直接setするため終了できます。一方、production main threadのSIGINT/SIGTERMはrelay pipeへ書くだけなので、relayをpollしないdaemonはsignal shutdown不能になります。serve thread実行の本テストでは、そもそも [`daemon.py:1607`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1607) のsignal handler設置経路へ入りません。

成果物影響: SIGINT/SIGTERMを無視する製品daemonをlong-path受入がPASSとして受理します。

### `[must-fix][real]` KeyboardInterrupt/SystemExitの型帰属は保持されない

[`integration.py:1507`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1507) は全 `BaseException` を `FAIL/rc=1` に変換し、親は [`integration.py:1601`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1601) で `pytest.fail()` に変換します。

child payloadには元型名が文字列として残りますが、pytestが観測する第一例外型は `KeyboardInterrupt` / `SystemExit` ではなくpytestのfailureです。裁定の「AssertionErrorへ変換しない」は実質的に閉じていません。

成果物影響: mutation/受入台帳の第一失敗型が変わり、primary・cleanup・外部割込みの帰属を誤記します。

### `[must-fix][real]` M7はcleanup成功を観測できない

primaryがある場合、[`integration.py:1491`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1491) はcleanup errorを抑制します。payloadにもcleanup結果がありません。M7でprimary assertionを注入すると、cleanupが成功しても、patch restoreやthread cleanupを削除しても、親から見えるのは同じprimary FAILです。child process終了がpatch/threadを消すため、親から内部finallyの実効性を区別できません。

成果物影響: cleanupを壊した変異をM7 KILLとして誤記し、harness cleanupの検出力を過大認証します。

### `[nit][real]` child import環境は完全には射影されていない

同じPythonを使う [`integration.py:1532`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1532) 点と、repo rootをcwdにする点は妥当です。実作業前には [`integration.py:1376`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1376) でisolated environmentへ入るため、親pytest環境も変更しません。

ただしchild import自体はenv未指定で行われ、`PYTHONPATH`、`PYTHONSAFEPATH`、sitecustomize、coverage/pytest系環境を継承します。現時点で偽緑を作る具体的consumerは立証できないためnitです。

### refuted

- ceiling timeoutがgreen/KILLになる攻撃はrefutedです。[`integration.py:1575`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1575) は明示的 `pytest.fail("INFRA_TIMEOUT...")` です。
- Python executableやcwdを別物へ変える攻撃はrefutedです。同じ `sys.executable` と `_REPO` を使用しています。
- nodeのxdist marker喪失はrefutedです。[`integration.py:1610`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1610) に維持されています。

## 初回review対応表

ここでの `closed` は静的root causeが閉じたという意味だけで、実走greenではありません。

### correctness review

| 初回所見 | 状態 | 現在の根拠 |
|---|---|---|
| B1 sentinel前・outcome後・joinの無期限hang | **partial** | 親の180秒ceilingは [`integration.py:1541`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1541) で全child内hangを有限化し、timeoutは赤。ただしnested session/process treeを回収しない |
| MF1 `daemon=False` mutation生存 | **partial** | start前assertは [`integration.py:1411`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1411) に追加。ただしcapability skipが先なのでM5未実証 |
| MF2 reader shapeの過剰拒否・偽緑 | **partial** | list/tuple・順序変更を許しduplicate listenerを拒否する [`integration.py:1287`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1287)。実relay identityは未束縛、追加wake FD等も拒否 |
| MF3 exact `0.25` pin | **partial** | `0 < timeout <= 0.25` は [`integration.py:1314`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1314) で短縮を許す。M4はfunctional KILLでなくdiagnostic pinのまま、未実走 |
| N1 最小性不足 | **regressed** | +291/-24から最終+411/-26へ増加。helper群は [`integration.py:1188`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1188)〜`:1612` |
| happy-path trace順序 | **partial** | 静的順序は [`integration.py:1413`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1413)〜`:1463` で成立。ただしdedupとreal node未実走 |
| early return / while True / Event除去の専用赤 | **partial** | sentinel経路は存在するが [`integration.py:1352`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1352)、M1〜M3未実走 |
| primary保持・serve exception・restore順 | **partial** | regular exceptionのargs変更は除去されたが、BaseExceptionの親帰属とM7観測が未閉鎖 |
| capability skipの正直な報告 | **closed** | gateは [`integration.py:1381`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1381)、記録もSKIP/NOT_RUNを明記している [`s6-fix1.md:19`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s6-fix1.md:19) |
| T-136/T-138 no-touch | **closed（静的）** | tracked diffはlong-path node周辺のみ。preservation実走は未確認でgreenではない |

### concurrency review

| 初回所見 | 状態 | 現在の根拠 |
|---|---|---|
| 1 outcome非観測・通知後未終了hang | **partial** | 直下childは有限化したが、worker/grandchild containmentが未閉鎖 |
| 2 real thread/long-path未実走 | **partial** | capability gate [`integration.py:1381`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1381) より後はSKIP。author記録もNOT_RUNを明記 |
| 3 cleanupがprimary/BaseExceptionを変換 | **partial** | regular primaryのargs mutationは除去。KI/SystemExitはstructured FAIL→pytest failureへ変換 |
| 4 patch/thread ownershipの穴 | **partial** | patch開始はtry内、join後restore [`integration.py:1403`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1403)。ただし `Thread.start()` 割込み時の `ident is None` 窓とtimeout killによるfinally未完了が残る |
| 5 module bindingのprocess-global波及 | **closed** | patchは独立child内だけで [`integration.py:1404`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1404)、pytest workerへは波及しない |
| 6 trace dedup・shutdown/release二重実行 | **partial** | dedupは [`integration.py:1253`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1253)、mainとfinallyの二重操作も残る |
| 7 relay fd再利用 | **partial** | int値比較だけ [`integration.py:1308`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1308)。実relay objectへの束縛なし |
| 8 xdist meta-testの射程 | **partial** | AST marker検査は維持 [`isolation_contract.py:102`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_isolation_contract.py:102)。scheduler overrideは警告だけ [`run_tests.py:767`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/run_tests.py:767) |
| 9 test-only shadow contract | **regressed** | reader数・型、timeout上限、loop順、private Eventを411行差分でshadow |
| target identity race | **closed/refuted** | threadをstart前にbind [`integration.py:1401`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1401) |
| listener publication / Condition lost wakeup | **closed/refuted** | trace更新とwait predicateは同じCondition [`integration.py:1253`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1253) |
| Event lost wakeup | **closed/refuted** | exchange/park/releaseはlevel-triggered Event |
| lock inversion / trace list破損 | **closed/refuted** | Condition保持中にSupervisor lockを取らず、trace read/writeは同じCondition下 |
| outcome発行済み経路のcleanup | **partial** | normal pathは成立するが、割込み・process timeout・M7観測不足を除外できない |

## 実証不足の範囲

real long-path nodeは [`integration.py:1381`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1381) でSKIPした記録です。したがって次はすべて実証不足です。

- patchと実 `Supervisor.serve_forever()` の結合
- listener/relay readerとtimeoutのproduction call
- real bind、exchange、`RunState.COMPLETED`
- post-exchange park、shutdown、release、serve return
- daemon assertion
- primary/cleanup exception、thread join、patch restore
- PASS payload/parser経路
- M1〜M7の検出力

[`s6-fix1.md:25`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s6-fix1.md:25) の追加controlはtracked testではなく、今回も再実走していません。受入証拠やKILLには数えられません。

## +411/-26 shadow contract

行数自体だけならblockerではありませんが、現状のままは許容できません。private実装を411行で固定しながら、肝心のreal nodeがSKIPし、group cleanupとresult envelopeに新しい穴があるためです。

同じ検出面を小さくするrealな案は次です。

- 8状態Enum＋dedup trace＋Conditionを、`listener_ready`、`parked`、`release` の3 Eventと単一outcome queueへ縮約する。mainの逐次処理自体が順序を束縛するため全8状態の保存は不要。
- stdout prefixではなく専用pipe/result FDを使い、exact JSON schemaを検査する。
- `SignalRelay` constructorをchild内でtest wrapperへ差し替え、実生成されたrelay FDとreaderをidentity比較する。
- containment launcherを独立させ、Linux cgroupまたは専用subreaperでdescendantを列挙・TERM/KILL・`waitpid`する。PID単体やouter process groupだけではnested sessionを閉じない。
- structured parser、timeout、descendant cleanupをcapability非依存のtracked controlに分け、real long-path nodeは実transport証拠に専念させる。

これならproductionを変えず、M1〜M7の検出面を保ちながらshadow stateを大きく削れます。

## M1〜M7前の訂正

| ID | 訂正すべきanchor/fixture |
|---|---|
| M1 | `conn.shutdown(socket.SHUT_WR)` はHEAD/finalともexact 1件、[`daemon.py:1638`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1638)。挿入bytesと期待failure型を逐語登録 |
| M2 | `while not self._shutdown.is_set():` はexact 1件、[`daemon.py:1613`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1613)。sentinel赤はdiagnostic/latency pinとして扱う |
| M3 | `_shutdown.set()` 単体は2件あるため非一意。[`daemon.py:1643`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1643) の `shutdown()` method全体をold anchorにし、signal-handler側`:1622`を触らない |
| M4 | select call全行はexact 1件、[`daemon.py:1615`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1615)。KILLでなくdiagnostic sensitivity pin |
| M5 | thread constructorはHEAD/finalともexact 1件、[`integration.py:1401`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1401)。capability skipならNOT_RUN |
| M6 | target-thread guardはfinalだけexact 1件、[`integration.py:1335`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1335)、HEADには存在しない。旧新両走の純増証拠から外し、final-only harness controlへ再分類 |
| M7 | 「注入したassertionで赤」をKILLにしない。HEAD/final共通のpost-status anchor [`integration.py:1431`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1431) に揃え、primary型とcleanup invariantsを別field/controlで観測する |

外部ceilingは以下が必要です。

- final nodeの内部180秒＋reap grace＋pytest起動時間より長い外周ceilingを置き、内部 `INFRA_TIMEOUT` failureを先に回収する。
- old版の固定`join(120)`も外周内に包含する。
- 外周timeoutはKILLでなく `INFRA_TIMEOUT/NOT_EVIDENCE`。
- timeout targetは直下PIDではなくdescendant全体。
- `flock`単一走行guard、置換数1、mutated diff、復元後のbyte equalityを毎回確認する。
- capability skipならM1〜M7をすべて `NOT_RUN` とし、matrixを完了扱いしない。

## 総括

- 判定: **NO-GO**
- 残るfix:
  1. nested sessionを含むworker/grandchild containment
  2. exact structured-result schemaと専用結果channel
  3. 実SignalRelay FDへの束縛
  4. KeyboardInterrupt/SystemExitとcleanup帰属
  5. M7 cleanup観測fixture
- real long-path非skip証拠: 未取得
- mutationへ進めるか: **進めない**。anchorの静的dry確認までは可能ですが、上記fix、process-tree control、capabilityのある環境が揃うまでM1〜M7のKILL/SURVIVEを記録してはいけません。