# A-1 attempt-0004 — 実装と実走の記録

- authority: none
- default_effect: no-state-change
- D1936項3、source追補は output/insights/2026-09-11/t2397-a1-source-amendment/README.md。
- attempt-0004は全3 workload validで完走し、complete/materializeを完了した。
- mainへの取り込みは最終記録commitに対する受入・land手順で行う。

## 実装と独立検査

既存patchharnessと独立期待materializationで、canonical clean起点に指定patchだけを適用する。
関門・trace/perf build・初回collectionへ同じsourceを渡す。gflags/glog prefixと既存FetchContent
供給を接続し、exact argv consumerを整合した。旧policy/prereg/patchとT-2514のdetail保存は維持。

独立review-aはmust-fix0。review-bの「probe改行が二重escape」はfix1と親ASTで反証した。
文字列値は実改行ordinal10であり、fix1の変更は0。jobのstudy再選択はfix2で既存policy再利用へ直し、
focus1で同値性を確認した。新規直接Git subprocessはfix3で既存_gitへ置換し、deferred sinkは
同じlegacy呼出しの行番号だけ更新。focus2でHEAD/root/tree拒否の維持を確認した。

## 関連検査

- A-1: 203 passed / 45.71秒（commit bc9f5fbb6）。
- job契約: 171 passed / 10.09秒（commit fd04d70dc）。
- campaign: 414 passed / 3 skipped / 23.31秒、bnode001、request991839。
  親dispatcherはPRR長期化後の取消要求をstate-not-cancellableで見送りrc16。
  後にjobは自然起動してchild_rc0となった。resultのrequest_sha256は実request.jsonの
  e738f6456c10046ec488c61d8279828b81a993f9350e821fba13df107eedc805と一致。
  親のinfra終了と子の成功を区別する。受入receiptとしては使わない。
- 制約4fileと下記実機probe: 111 passed / 1 skipped / 213.72秒、親/子rc0、request991844。
- pytest/buildは全てtools/run_tests.py経由。skipは既存制約であり今回追加していない。

初回A-1の30赤は未commit loop.pyに対する既存loaderのHEAD束縛によるF764。
commit後に同じテストを通した。campaign初回の46赤は他者所有の/tmp/.gitによるF763/F781。
他者directoryを触らず、Git祖先のない専用TMPDIRを使った。
取消後にversioned/旧形式の2つのholdが残り、終端・request hash・clean/HEADを確認して両方を解除した。
手動qdelとF47解除は行っていない。制約単独走の1GiB scope OOMはテスト結果に数えず、computeで再検査した。

## 二つの停止原因の実機閉鎖

source commit: 066bc7a7c58dd425d933ce939d73f0a786076189。
request: 991844.nqsv、host: bnode001、scheduler実行219秒。
3 workload / 全6 armについて、供給・意味の12 recordがgreen、family admission3件がtrue。
trace build6件・perf build6件を既存builderで確認し、全armの既存verifierがcertified trueとなった。
検査は同じmaterialized source contextを保持したまま行った。benchは行っていない。
従って依存不足と未patch sourceの二つの停止原因をこの実走で閉じた。

耐久raw:
/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2397-a1-attempt4/source-probe/0_991844.nqsv/
（condition-records.json、builds.jsonl、source.json、completed.json、各workloadのWAL・検証記録）。
これはpilotの性能結果ではなく、投入前の正しさ・配線検査である。

## 変異検査の事前登録

unit-probe.jsonはM3/M4/M5/M6/M7/M8の初回probe用。期待nodeは観測後に固定して再走する。
M4は構造感度、M7は診断感度として別記し、意味的なkill率に含めない。
M1/M2は実依存を使うmanual probeで別に検査する。
単体群は既存D1358のtask=mutationで計算ノード1job内に束ね、内部のrunner-mode localは
同taskのcompute markerで認可される経路だけを使う。runnerはtools/run_tests.py。
外側dispatchと各テスト呼出しを同じscheduler request数として数えない。

初回probeはrequest991850で全6変異を実行。baseline374件が通り、各変異が予定した
test nodeを失敗させた。ただしwrapperの共有木事後比較がfalseとなり、外側rc125。
完了扱いにせず、観測nodeをunit-final.jsonへ固定した。生の台帳はunit-probe-out.json.gz、
wrapperの拒否はunit-probe-wrapper.jsonに保存する。
F785の既存手順に従い、最終走のsource-repoはmainから独立したcloneにし、
共有木検査を弱めずに並行セッションの状態変化を分離する。

最終単体群はrequest991859、code3124f65c5でbaseline通過、M3〜M8の全6件がKILLED・期待node完全一致、
wrapper rc0/shared_snapshot_matches=true/teardown_completed=true。
このうちM3/M5/M6/M8は判定の挙動、M4は構造、M7は診断の感度である。

実機群の初回request991860はclean環境のPBS_JOBID欠落でbaseline FAILED、変異未開始。
既存task markerのvalidatorが確認した実IDをprobeへ渡す8行だけを追加し、
不正markerの拒否と共通environment allowlistを維持した。focus4の独立確認は指摘なし。
出力は同じjob内の呼出しごとにcreate-onlyなrun-*へ分離し、過去の出力を保存する。

新scratchでのrequest991865（code a9d20d701）はbaseline PASSED、M1/M2ともKILLED・期待node完全一致。
wrapper rc0/shared_snapshot_matches=true/teardown_completed=true。M1はprefix欠落による
supply configure-failed、M2は未patch rootによるconfigure-failedとdecoder/branch-invalidを観測した。
基準のrun-bynq05p0は全arm成功、run-d5ckwgi3がM1、run-pej5ii46がM2。
rawはsource-probe/0_991865.nqsv配下。生台帳・attempt・wrapperを本directoryへ保存した。

## attempt-0004 投入

既存submit経路、source a9d20d7016794fb60df1926e71747a7353210eaf、
同study、既存hydrate出力だけを使って投入した。親rc0、stderr空、group submission発行、
submission-failureなし。intent SHAは7432ff68fd725f5319083baa8c54c4cd1b130fbee8fda7a7477150ef4f1c579a。

| workload | request | node |
|---|---|---|
| write-heavy | 991875.nqsv | bnode023 |
| balanced | 991876.nqsv | bnode026 |
| read-heavy | 991877.nqsv | bnode027 |

全jobのreadyとbench-startを確認した。build/verifyが揃ってから登録済み測定へ進んだ。
全3jobはdriver_rc0で終了。complete/materializeもrc0で、
complete=true、all_workloads_terminal=true、各workloadのvalid=true/errors=[]を確認した。
各workload60対、全体180対であり、既存のsizing-pilot.jsonを生成した。
成果物は output/insights/2026-09-01_paper-story-a1-balanced5-pilot/。
pilotから性能の優劣やheadlineを主張せず、sizing入力に用途を限定する。
投入元submit-treeは記録用waveと分離し、実行中のsourceは変更していない。

## 逐語の保存

reviews/にauthor・独立review・fix・焦点reviewを保存した。review-b.mdだけ表示用に行末spaceを除去。
原文はreview-b.original.gzに保持し、gzip -dcで復元できる。原文1657 bytes、
SHA-256は647417b98f69e3f08c9b1c1fe31814829d2b893202244119ef0ab540a428f603。
このreviewのescape所見は上記のとおり反証され、実装変更には採用していない。

## 終端

sourceの二原因を実機で閉じ、登録済みattempt-0004だけを投入した。追加試行・次wave・pushなし。
最終受入は記録commit固定後の既存acceptance経路で行い、その耐久receiptをlandが検証する。
スキル自己改善は候補の記録だけとし、改善実装はしない。

改善候補: DW-O19から既存F785の独立clone手順へ、並行waveの変異開始前に辿れる参照を明確にする。
今回は共有木事後比較の拒否を実測してからF785を引いた。新しいgateやframeworkではなく既存手順の導線候補であり、
本waveではskill/command/operationsを変更していない。
