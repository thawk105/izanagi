# A-1 attempt-0004 — 実装と実走の記録

- authority: none
- default_effect: no-state-change
- D1936項3、source追補は output/insights/2026-09-11/t2397-a1-source-amendment/README.md。
- この記録は進行中。pilotの投入・完走・main landを先取りしない。

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
