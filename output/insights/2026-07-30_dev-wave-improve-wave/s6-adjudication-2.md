# 段6 focused review 第2裁定

時刻: 2026-07-30 15:14 JST

fixed staged patch
`bda3aa8f76aa0ef8e3068c4e5fd96d8ae9148eee63d4cef340c7c8dd1b905b22`
へのfocused reviewは rc=0 / output format green / NO-GO。初回23所見は
12 closed / 11 partial、blocker 5 / must-fix 9だった。pytest/build/qsubは
未実走であり、greenとは扱わない。

## 採用

### U3

- canonical-looking `sys.modules` forgeを実probeで受理したR1を採用する。
  trusted pathのsource bytesをprivate module namespaceへ直接loadする等、
  ambient `sys.modules["pegasus_policy"]` / `sys.path`を信頼しない方式へ縮約する。
  ordinary import/reload互換ではなく、全production callerが同一trusted policy
  object/definitionsを使うことを正本とする。

### U2

- R2: selected testsだけでなく、snapshot実行tree全体のpath/mode/symlink/hash
  inventoryをmanifestへ束縛し、worker開始直前とrunner終了時に再検証する。
  テストがsource treeを書き換えた場合も成功artifactにしない。
- R3: repository既存 `validate_nqsv_accounting_epilogue` と同じseparator付き
  terminal footer、field順、末尾block、exact job IDを要求する。安定後の同じ
  stderr bytesからreceiptとaccountingを作る。
- R4: qsub受理不明となる全 `OSError` / timeout / signalを同じUNKNOWN照合へ
  送り、qsub-intent / result / submit / cancel / final各crash境界をresume可能にする。
  qdel成功はWALでlatchし二重qdelしない。
- R5: per-job qstatはRequest ID exact一致を必須化。lookup candidateはuser、
  queue/account、qsub開始以後のcreated time、job name、stateを束縛し、
  running hostをworker claim/runner hostと照合する。同名旧jobを採らない。
- R6: combined spool超過は必ず失敗outcomeへ固定し、valid child/accountingで
  成功へ戻さない。
- R7: task-run ledgerが成長した場合もproducer receipt sizeまでのprefix SHAを
  検証してからevent一意性を確認する。
- R8: lookup intent/result/matched candidate/submit/finalの一対一順序とIDを
  validatorで束縛する。全lookupはqsub absolute deadlineを共有し、成功した
  retry後は過去failure reasonを残さない。
- R9: computeの`-n auto/logical`をU1 APIへ渡してaffinity数へ解決する。
- M10/M12/M14/M15とfocused reviewのpost-terminal spool、crash、exact ID、
  ledger prefix、accounting footerを実branch testへ追加する。fsyncは注入seamで
  欠落を赤にし、qdel first failure→retry successを固定する。

## 却下 / 限定

- NQSV `Request Name` truncationはcurrent 35-byte nameが実上限63未満のため
  refutedを採用する。ただしunique nonceのentropyを縮めない。
- 通常userのforeign-user混入はNQSV `qstat -f`の所有request契約でrefuted。
  同一userの同名旧jobはR5で閉じる。
- output-limitによりaccepted IDを知れない場合、数学的にqdel不能な可能性は残る。
  bounded captureとjob name lookupを尽くした後の`SUBMIT_UNKNOWN`は
  fail-closed operational incidentであり成功artifactではない。system-wide
  exactly-once保証へ主張を広げない。

## gate

U2/U3 owner fixを統合後、blocker 5とmust-fix 9だけを対象に小さいread-only
focused再レビューを行う。GOまではlive qsubしない。
