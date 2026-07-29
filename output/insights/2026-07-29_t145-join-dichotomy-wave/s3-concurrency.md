結論は **NO-GO** です。指定7ファイルは全行読了しました。編集、pytest、mutation は未実施で、green は主張しません。追加で段3規約、SignalRelay、protocol、WAL thread、xdist の現行契約を静的照合しました。

## real — 段5前の must-fix

### R1. `daemon_mod.select.select` patch は実際に process-wide

[daemon.py:15](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:15) の `select` は Python module object です。[plan:26](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s2-plan.md:26) の `mock.patch.object(daemon_mod.select, "select", wrapper)` は、その共有 module object の属性を書き換えます。

同一 interpreter で `select.select` を属性参照する別 thread/library も wrapper を通ります。事前に `from select import select` した参照や別 process には波及しませんが、「node 内だけ」という表現は誤りです。

実行時には、serve thread が post-roundtrip gate で停止したまま、main thread は [_wait_terminal](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1221) を進み、run thread と WAL thread が活動します。WAL は [ledger.py:765](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/ledger.py:765) で別 thread です。この重なる全期間、標準 module の属性が差し替わります。

最小修正は、標準 module の属性ではなく daemon module の名前だけを差し替えることです。

```python
real_select = daemon_mod.select.select
with mock.patch.object(
    daemon_mod,
    "select",
    mock.Mock(select=wrapper),
):
    ...
```

さらに wrapper は最初に target serve thread かを判定し、それ以外は即 `real_select` へ委譲する必要があります。

成果物影響: foreign thread の正当な `select(None)` を sentinel failure に変えると、T-145 の回帰結果が製品退行ではなく test harness 干渉になります。

### R2. xdist meta-test は新しい process-wide 所有を一切証明しない

対象 node は既に [marker:1181](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1181) と [threading.Thread:1208](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1208) を持ちます。したがって isolation meta-test は patch 追加前から `_RUNTIME_VOCABULARY` に taint されています。

[語彙:35](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_isolation_contract.py:35) と [照合:102](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_isolation_contract.py:102) が証明するのは marker の一致だけです。patch target、thread ownership、patch 復元、lingering thread、pytest/plugin thread は検査しません。

また loadgroup は同名 group を同じ worker に載せますが、worker 専有を与えません。[run_tests.py:288](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/run_tests.py:288) の既定は有効でも、別 scheduler 指定は警告だけで許されます。[run_tests.py:767](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/run_tests.py:767)

成果物影響: meta-test green を patch 隔離の証拠として記録すると、F21 型の「marker 配線と live ownership の取り違え」になります。

### R3. wrapper は listening socket の ready をまだ一意に識別できない

実 select は [daemon.py:1615](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1615) で `[bound.sock, relay.fileno()]` を同時監視します。listener は serve_forever の局所変数で、現 plan は test がその identity を得る方法を書いていません。

「何かが ready」では SignalRelay と混同します。「socket が ready」だけでも process-wide foreign call と混同します。必要なのは以下の全束縛です。

- `threading.current_thread() is serve_thread`
- readers が socket 1個と relay fd 1個、writers/errors が空
- 最初の target call で listener object を identity 保存
- client phase を arm した後、real select の戻り値にその同一 object が含まれた場合だけ roundtrip ready
- SignalRelay のみ ready、未知の call shape、foreign thread は状態を進めず実関数へ委譲

成果物影響: 誤った ready を roundtrip と数えると、無関係な select の次呼出しを park し、実 AF_UNIX roundtrip を通していない偽の検出力になります。

### R4. 全出口 cleanup は plan に存在しない

現 node は thread start 後、[socket existence assertion:1217](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1217)、exchange、response assertion、terminal wait、state assertionを経て、正常経路でのみ [shutdown:1223](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1223) へ到達します。

plan が追加する `_serve` 側の `serve_finished` finally は、wrapper 内で park 中の threadには実行されません。例えば次の interleaving が残ります。

1. wrapper が post-roundtrip で `release_loop` を待つ。
2. main thread で exchange後 assertionまたは `_wait_terminal()` が失敗する。
3. main は `shutdown()` と release を通らず patch context を unwind。
4. module attribute は復元されても、既に wrapper 内で待つ daemon thread は残る。
5. [_isolated_process_environment](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:109) と TemporaryDirectory が先に復元・削除され、thread、lease、socket fd が次 node へ残り得る。

`shutdown()` 自体も `_shutdown.set()` 後の cancel/WAL 経路で例外化し得るため、release は `shutdown()` 成功に従属させられません。

main 側に外周 `try/finally` が必要です。正常経路は `shutdown → Event set確認 → release → join`、例外経路は primary exception を保持したまま emergency shutdown-set、release、回収、cleanup error 追記を独立に行い、thread 終了後にだけ patch を復元すべきです。

成果物影響: 失敗した node が後続 node の環境・socket・module lookup を汚染すると、受入結果と mutation の第一失敗帰属が失われます。

### R5. timeout 無し join の証明は sentinel 到達前を覆わない

sentinel が効くのは、serve thread が park へ到達し、main が release し、serve thread が再 scheduling され、その後もう一度 wrapper を呼んだ場合だけです。

次は sentinel に到達しません。

- roundtrip 後、loop が `select` を呼ばず spin
- wrapper 自身が condition lock 内で停止
- C extension 等による GIL starvation
- `shutdown()` が release 前に無界停止
- serve thread が park/finished のどちらも通知しない変異

plan はこれを [plan:56](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s2-plan.md:56) で外部 ceiling に委ねますが、受入コマンドには ceiling がありません。runner も [run_tests.py:714](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/run_tests.py:714) と [run_tests.py:785](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/run_tests.py:785) で timeout 無しの `subprocess.call` です。ceiling が書かれているのは mutation harness だけです。

正しい thread の無期限 starvation と壊れた thread の無期限停止を、時間・fairness 仮定なしで in-process 判別することは不可能です。外部 ceiling は解決ではなく containment です。timeout は KILLED や green でなく、`INFRA_TIMEOUT / acceptance incomplete` と記録する必要があります。

成果物影響: 現 plan のままでは mutation または受入全走が永久停止し、brief が懸念する受入結果・試行記録の喪失を別層で再現します。

### R6. 「timeout が None だけ赤」は製品受理集合を広げる

現行 `join(120)` は粗いながら、長大な有限 poll も停止退行として赤にします。plan は [plan:28](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s2-plan.md:28) で `None` だけを拒否し、長短は判定しないとしています。

`0.25 → 3600` の変異では、最初の select は client connection で返ります。次の呼出しを wrapper が park し、shutdown 後に synthetic empty-ready を返せば、実際の3600秒 pollを一度も踏まず test は通ります。production daemon は shutdown が最大1時間遅れる実装です。

これは brief の「製品 daemon の受理集合を変更しない」[brief:10](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s1-brief.md:10) と両立しません。

成果物影響: 停止不能に近い有限 poll 退行を certified green にし、T-145 自身の停止検出力を縮小します。

### R7. mutation matrix が harness 自身と containment を撃っていない

M1〜M5 は既知 production/test変異だけで、次を覆いません。

- M6: `0.25 → 3600`
- wrapper が target thread 判定前に `timeout is None` を拒否
- wrapper exception、release欠落、shutdown例外
- roundtrip後の no-select spin
- patch中に foreign thread が標準 `select.select` を呼ぶ
- primary assertion failure後の thread/patch/socket回収

no-select spin が外部 timeoutになった場合、それを functional KILL に数えてはいけません。T-136 preservation controls は state/reason 保存であり、この cleanup・隔離穴の代用になりません。

成果物影響: matrix が全件「KILLED」でも、実装した同期 harness の隔離・終了性・第一失敗帰属は未検証のままです。

## refuted

- active run/WAL thread がリポジトリコード上で直接 `select.select` を呼ぶ、という攻撃は refuted です。直接利用は [daemon.py:1615](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1615) の1箇所だけです。run thread は [daemon.py:1262](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1262) で `poll/sleep`、WAL は Queue/Event と [無期限 join:791](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/ledger.py:791) を使います。ただし外部 library/plugin の動的属性参照までは閉じていません。

- SignalRelay と listener は原理的には区別できます。select は入力 object を返し、listener は socket、[SignalRelay.fileno()](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/ledger.py:1347) は int です。また本 test の serve thread は main thread ではないため、[signal handler設置:1607](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1607) は通常発火しません。問題は区別不能ではなく、plan が identity 束縛を書いていないことです。

- planned runner の既定で同名 xdist group が同じ workerへ載る点は refuted です。現環境の pytest-xdist は3.8.0で、リポジトリにも同-worker live controlがあります。ただし、これは専有 process や patch ownership の証明ではありません。

- production seam が必須という攻撃も refuted です。`daemon_mod` の module binding を proxy に差し替えれば、production 0 byteのまま標準 `select` module を汚染せずに済みます。

## 裁定待ち

1. select timeout の契約を `None でない` とするのか、上限値を持つのか。推奨は wall測定ではなく引数値の明示上限を置き、M6で固定することです。

2. liveness 主張を「fair scheduling 下でM1〜M4を論理分類し、その他の無進捗は外部 containment」と弱めるか。絶対的な無時間・無hang保証は成立しません。

3. containment を全走の外部 ceilingだけにするか、対象 node を別 processへ隔離するか。全走 artifact を必ず返したいなら別 process隔離が必要です。

4. production shutdown wakeupをT-145へ広げるか。socketpair/self-pipe wakeupは実問題を製品側で閉じますが、FD lifecycle、shutdown-before-serve、重複serve、close/write raceまで増えるため別wave相当です。

## 代案比較

| 案 | 隔離 | 既知M1〜M4 | 任意hang containment | 判定 |
|---|---|---:|---:|---|
| 共有 `select` module属性patch | process-wide | 可 | 不可 | reject |
| `daemon_mod.select` bindingだけproxy化 + thread/fd束縛 | daemon module内 | 可 | 不可 | T-145最小推奨 |
| `SupervisorDependencies.select_fn` | Supervisor instance | 可 | 不可 | 明示seamを優先する場合の次点 |
| production socket wakeup | production lifecycle | M4を根本緩和 | while-true等は不可 | 別scope |
| test subprocess + 親ceiling | process完全分離 | 可 | kill/reap可能 | 強いcontainmentが必須なら採用 |

## plan v2 の必須修正

- 標準 module属性patchを廃止し、`daemon_mod.select` binding proxyまたはinstance dependencyへ変更する。
- target serve thread、exact listener identity、call shape、状態遷移を明示し、foreign callは必ず実関数へ委譲する。
- main側の外周 `try/finally` と primary-exception保存を設計し、全失敗出口でshutdown/release/reapを独立実行する。
- timeout引数の許容上限を裁定し、`0.25→3600` mutationを追加する。
- no-select spin、wrapper exception、shutdown exception、assert-after-park、foreign-selectをcleanup/isolation controlへ追加する。
- mutationと受入の外部 ceilingを実コマンドへ明記し、timeoutをKILL/greenに数えない。全走結果を失えない要件なら対象を別 processへ隔離する。
- xdist meta-testの主張を「同group同worker」に限定し、process-wide patch所有の証拠として引用しない。

## 総括

- **NO-GO**
- **段5前 blocker:** process-wide patch、全出口cleanup欠落、sentinel到達前の無界hang、受入ceiling不在、長大有限timeoutの受理集合拡大。
- **plan v2 必須:** module-local/instance-local seam、serve-thread＋listener identity束縛、外周cleanup、timeout上限＋M6、hang containmentの明示的裁定、外部timeoutを非green・非KILLとして記録。