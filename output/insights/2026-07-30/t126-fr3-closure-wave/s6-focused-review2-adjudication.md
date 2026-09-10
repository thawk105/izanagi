<!-- parent-owned dev-wave artifact; 2026-07-30 JST -->

# T-126 FR3 closure — focused review 2 裁定

reviewはexit 0、Pegasus計算node `874359.nqsv`のoutput validator / fixed artifact /
source manifestが全rc=0、判定はNO-GO。必須8行はclosed 5 / partial 3 / regressed 0だった。
`DW-O16`の第2焦点reviewであり、以下3件をreal / scope内と裁定して最終fix 3へ限定する。

| ID | 裁定 | fix 3の最小条件 | 放置時の成果物影響 |
|---|---|---|---|
| FR2-1 / F2-1 | real / BLOCKER | create-stageを発行器が生成できるcanonical PID grammar `[1-9][0-9]*-[0-9a-f]{16}`だけに限定する。shared writer、atomic publisher、collector job-result reconciler、embedded publisherを同義化し、`0` / leading-zero suffixを全namespaceでnonmutating拒否する | current UID / 0600 / regular / nlink=1の生成不能stageを正規hard-crash残骸と誤認して消去し、receipt / ledger / snapshot / job-resultをcleanに発行できる |
| FR2-2 / F2-2 | real / HIGH | valid canonical attempt Aとstructural-validだがsemantic-invalidなearly Bが異なる場合も、Bの元path/lstat/hash/bytesをnonmutating preservationして二回collectへ収束させる。Aを削除・書換えず、exact conflict evidenceから`job-result-publication-failed` / retry=falseをpublic verifierが再導出でき、M10bの一般pointer-null拒否は維持する | preservation前のA/B差分raiseでrejected-evidence、receipt、outcome ledger、closureが永久に発行されずsubmitted stateが閉じない |
| FR2-3 / F2-4 | real / HIGH | M5a/M6c/M8a/M9d/M10a/M10dのmapped node survivorとM8b/M8c/M10bの前段false-killを解消する。M1〜M7のID・意味・node名は維持し、各replacementがmapped nodeの意図したproduction decision pointへ到達して成果物/authorityを誤らせるfixtureとする。M8d/M11bを含む既成立entryを壊さない | mutation matrixがFR3のauthority / retry / evidence境界を殺した証拠にならず、commit後の全greenを誤って受入証拠にできる |

mutation修正では、単なるerror文字列やreturncode差だけをkill根拠にしない。最低条件は次とする。

- M5a: tag-order gate自身を無効化したmutantをswapped-order nodeが殺す。
- M6c: scheduler / job-result RCの意味差を受理するmutantを既存M6c nodeが成果物分類で殺す。
- M8a:既存invocation claimから二回目qsubへ進むmutantをparallel nodeがqsub件数で殺す。
- M8b: raw stdoutからdurable bindingを再構成してledger bindへ進むmutantをprebinding-crash nodeが殺す。
- M8c: nonzero qsub後のclaimを失わせ、次回qsubへ進むmutantを再投入件数で殺す。
- M9d: target/stageをdifferent inodeかつ各nlink=2にしてinode比較をdecision pointにする。
- M10a: invalid→missing後のpublication failureをeligible classへ書換えるmutantをpublic verifier /
  retry validator / ledgerまで通すfixtureにする。
- M10b: valid canonicalのpointer-nullを許すmutantだけが、coherent publication-failure receiptへ
  書換えたfixtureを通るよう前段分類を整える。
- M10d: permanent classをretry可能にする同方向のmutantへ直し、四層の少なくとも対象layerで殺す。

F2-3、F2-5、C2-1〜C2-3はclosedを採用する。same-UID syscall間race、power-loss一般化、
system interpreter / LD_PRELOAD、arbitrary coherent rewrite、login-side collector isolationは
既裁定どおりscope外とする。fix 3後は計算node関連全走、focused review 3、commit後mutation
matrixで裏取りし、`DW-O16`の3巡上限を超えてfixを追加しない。
