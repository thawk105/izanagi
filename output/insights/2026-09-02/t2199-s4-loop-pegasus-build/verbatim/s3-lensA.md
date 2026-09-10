## 総括

最重大所見は、plan の CMake wrapper が condition gate と後続 build の双方を支配する一方、その bytes と実効 configure argv が gate record や campaign 証拠へ束縛されないことです。これは `condition_meaning_gate.py` を変更しなくても実質的な受理集合変更になります。
親 brief の (P1) は「Pegasus entry が登録済み」という狭い意味では正しいものの、D59 の 4 条件が対象 job について完了済みという一般化は誤りです。
(P4) の「env_tag と実機の不一致を block しない」は現行の安全防壁と正面衝突し、許せば Pegasus 値を `linux-baremetal` として永続化します。
通常経路の trace/perf 分離は確認できましたが、wrapper が trace と strip を同時注入できると既知の `nm` 限界を通る経路があります。
判定は **条件付き**です。現時点で実装せず停止する plan の第 1 項だけは採用可ですが、第 3 項以降は下記条件を閉じるまで採用不可です。

## 所見

1.

- 種別: real
- 対象: `s2-plan.md:272-274`、`condition_meaning_gate.py:1402-1415,1479-1490,1956-2001,2064-2085,2236-2283`
- 内容: PATH 先頭の CMake wrapper は source-dir、compiler launcher、任意の `-D`、さらに `compile_commands.json` 自体を変更できます。gate はその wrapper を CMake 実体として実行しますが、green record は CMake path、wrapper hash、configure argvを保存しません。従って code を変えなくても実質的な受理集合変更です。
- 成果物影響: job-private wrapper が作った build graphで supply greenを発行でき、受理集合と再現用証拠が食い違います。
- 再現・確認の手順: 同じ source/requestを実 CMake と予定 wrapper の2条件で実行し、supply reasonを比較する。次に wrapperを「実 CMakeを呼ばず、必要な owner entryだけを持つ `compile_commands.json` を生成する」変異へ替え、gateがgreenにならないことを確認する。canonical recordに wrapper hash/configure argvが無いことも照合する。

2.

- 種別: real
- 対象: `s2-plan.md:272-278`、`buildcache.py:1212-1218,1936-1971,3437-3464`、`pipeline.py:717-745`
- 内容: wrapperはtrace/perf buildにも使われ、元argvの後ろへ `-DCCBENCH_TRACE=1` を追加できます。通常は `izanagi_trace` symbol検査が止めますが、`buildcache.py:3445` が明記する通りstrip済みbinaryは素通りします。wrapperにtrace有効化とlinker stripを同時注入させない機械条件がplanにありません。
- 成果物影響: traceのI/Oとbufferを含むbinaryのthroughputがperf値としてWAL、fitness、レポートへ入る可能性があります。
- 再現・確認の手順: 計算ノード上の変異wrapperでconfigure末尾へ `-DCCBENCH_TRACE=1` とstrip用linker flagを追加する。perf binaryについて `nm -C` のrcと出力、実行時のtrace生成、pipelineがbenchへ到達するかを確認する。

3.

- 種別: real
- 対象: `brief.md:45-50`、`s2-plan.md:274-276`、`p3_s4_loop.py:130-163,1424-1449,2027-2037,2052-2114`
- 内容: briefは「`preprocess-failed`より後の停止」をterminal verdictと並列の成果物にしています。またCLIはbuild後に`outcome=aborted`でも、checkpoint等の一般検査が通ればrc=0を返します。condition gate recordは返却dictにだけ入り、CLIはcanonical recordを表示・保存しません。
- 成果物影響: build-error等の停止を「前進」または成功receiptとして扱え、terminal gate証拠の無いレポートが成立します。
- 再現・確認の手順: condition gate通過後に`cmake --build`だけ失敗させる。CLIのrc、表示された`outcome`、WALの`ABORT`、`VERIFY_DONE`の不在を照合する。またstdout、stderr、campaign dirのどこにもcondition canonical recordが保存されないことを確認する。

4.

- 種別: real
- 対象: `brief.md:32-34`、`p3_s4_loop.py:107-113,1347-1349,1428-1433`、`execution_guard.py:107-170`
- 内容: 現行実装はPegasus compute上の`linux-baremetal` authorizationを意図的に拒否します。従って(P4)の「不一致をblockしない」は成立しません。これを非block化すると、WALとcampaign identityは`linux-baremetal`のまま物理Pegasusの値を保持します。安全なsite-aware配線は `orchestrator/campaign/**` 所有なので **scope 外**です。
- 成果物影響: 防壁を保てばbuild未到達、防壁を緩めればPegasus throughputが`linux-baremetal`系列へ混入します。
- 再現・確認の手順: bnode上で`authorize("linux-baremetal")`を渡し、`require_certified_writer_authorization()`が137-159行で拒否することを確認する。拒否を変更せず、t2145側の配線着地まで停止する。

5.

- 種別: real
- 対象: `roadmap.md:364-372`、`pegasus-runbook.md:731-771`、`p3_s4_loop.py:1950-1956`、`p2_2.py:291-310`、`calibrator/runner.py:327-414,432-508`
- 内容: D59条件3は実行ごとの単独性・静定確認、条件4は対象jobのtoolchain、pin、script追跡です。対象p3経路はcanary付き`composite_competing_probe()`ではなくplain `pgrep`を使います。さらに新job scriptは未作成で、そのhashをcondition recordやcampaignへ束縛する経路もplanにありません。
- 成果物影響: 不完全なPID可視性や差し替え`pgrep`の下でもPegasus throughputを採用でき、対象jobの4前提を満たしたと誤報します。
- 再現・確認の手順: PATH先頭に「stdout/stderr空、rc=1」のfake `pgrep`を置き、別の`ycsb_*.exe`を稼働させた状態で`_assert_single_tenant()`が通るか確認する。canary付きprobeなら同条件を拒否することを対照確認する。

6.

- 種別: 未確認
- 対象: `s2-plan.md:53-73,275`、`condition_meaning_gate.py:1632-1704`、`p3_s4_loop.py:154-158`
- 内容: `config.h`未生成という推定は静的連鎖に整合しますが、元stderrが無いため未確定です。さらにp3終了後はgateの`TemporaryDirectory`が削除済みで、保存したcompile entryのcwdも消えます。plan記載の「失敗後にexact argvを再生」は別のENOENTを観測する可能性があります。
- 成果物影響: 実原因と異なる再生失敗を`preprocess-failed`の原因としてinsightへ記録する恐れがあります。
- 再現・確認の手順: wrapperでcompile entryとcwdを保存し、p3終了後にcwdの実在を確認してから同argvを再生する。元preprocessと同じcwd/tree lifetime内で得たstderr以外は原因確定に使わない。

7.

- 種別: refuted
- 対象: `Options.cmake:13-19,58-68`、`trace.hh:25-124`、`transaction.cc:145-180,557-595`、`pipeline.py:1197-1263,1378-1382`、`buildcache.py:3432-3464`
- 内容: wrapperによる第2所見の変異が無ければ、trace処理は`#if TRACE`内で、trace/perfは別build、throughputはperf binaryから取得されます。通常経路にランタイム`if(tracing)`は残っていません。
- 成果物影響: なし。忠実なwrapper実装では絶対規律1は維持されます。
- 再現・確認の手順: trace/perf双方のcompile commandで`TRACE=1/0`を確認し、perf binaryの`nm -C`と実行後trace directoryが空であることを確認する。

## 親 brief の前提検査

(P1) 専用env-tagは存在し、active g1も登録されています。active g1の較正成果物には`env_tag="pegasus"`、acceptedなcalibrationとnoise floor、module/compiler/pin/job-script SHAがあります。ただしこれはD59条件1、2と較正jobの条件4を示すだけです。条件3は各測定時に再成立させる義務で、対象p3経路はcanary付きprobeを使っていません。新しいp3 job自身の条件4も未実装です。「registry登録済み」という狭い主張は支持されますが、「4前提が対象jobについて充足済み」は反証されます。

(P2) `config.h`未生成説はコード上もっともらしいものの未確認です。また「job側だけで解く」はcode fileを変更しないという意味では可能でも、CMake wrapper、PATH、ambient `CMAKE_PREFIX_PATH`、compiler launcher、生成されたcompile commandがgate判定を動かすため、受理集合に中立ではありません。安全に扱える正式入力面をp3側へ追加する必要があるならscope外なので停止条件です。

(P3) Pegasus選択は支持されます。`docs/worklog.md:543-553`にはcygnusは使えるが使わず、新規evidenceはPegasusで得るというユーザー裁定があります。planの「cygnusが直ちに安い」は、過去4 certified iterationと目的・時点の異なるPegasus 6投入を費用として比較しており、この裁定を覆しません。SSH設定不在について親は`handoff.md:57-58`で明示的に一般化を避けており、過大一般化という疑いはrefutedです。

(P4) 反証されます。現行guardは物理Pegasusと`linux-baremetal`契約の不一致をblockすることで混入を防いでいます。「blockしないが混ぜない」を実装する別の隔離consumerは示されていません。planの第1、2項が要求するsite-aware contract着地後なら、`pegasus` identityへ分離できるためP4問題は解消します。

## 未確認・限界

- read-only静的検査のみで、pytest、CMake、preprocess、build、PBS実測は行っていません。
- 予定wrapperとjob scriptはまだ存在しないため、第1、第2所見はplanが許す入力面に対する経路検査です。
- `config.h`原因は元stderrが無く未確定です。
- t2145側のsite-aware変更はこのworktreeに無いため、着地した実装は別途再検査が必要です。
- cygnusの現在の到達性、混雑、toolchainは確認していません。