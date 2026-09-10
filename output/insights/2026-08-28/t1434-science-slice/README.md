# [T-1434] T-1222 task-output science slice

- authority: D1235 と repo 外 `stage4-ruling.md`
- scope: availability-selected な `T-1222-population-closure` 1 family の retrospective task-output diagnostic
- artifact: `output/t189-routing-preregistration/task-oracle-science-slice-t1222-v1.json`
- artifact SHA-256: `c2afdb3614a4fa4ae8c81efe06f4656c4f1fcff1b4a1e6ecf168853561777d5b`
- validator anchor: `f24550a01`
- mutation anchor: `7cc5ce907`

## 結論

凍結前に独立導出・親裁定した6 findingを、plan/authorの両stageについて2 readerが評価した。
12/12 cellでreader verdictは一致したが、logical findingとして両stageでdetectedだったのはO1/O5の
2件だけだった。記述的coverageは`2/6 = 1/3`で、retrospective task-output acceptanceは
`not-accepted`である。

これはartifact破損ではなく、integrity validな科学的負結果である。`child-green`、test緑、physical
integrityをsemantic acceptedへ射影しない。same-owner・same-modelの別dispatchなので
`organizational_independence=not-established`、`section8_complete=false`を維持する。

## validatorと境界

- portable: canonical/closed schema、exact 6 finding、catalog 2-row projection、worklog bytes、git ancestryを
  検査し、semantic statusを`not-evaluated`に固定する。coverageとreader agreementは返さない。
- physical: jobs rootの23 dependency bytes、dispatch/acceptance receipt、reader matrix、artifact raw SHA、
  validator SHAを結線し、coverageとsemantic statusを再計算する。
- physical実走: rc=0、integrity valid、coverage `2/6`、reader `agreed-all-cells`、semantic
  `not-accepted`、organizational independence `not-established`、section8 complete `false`。
- portable実走: rc=0、integrity valid、semantic `not-evaluated`。

## 外来作業物と段6監査

最初のD95 authorは利用上限でfinal reportを生成せず、未追跡のtool/testだけを残した。元bytesをrepo外へ
同一SHA-256で保全し、別D95 authorが全文監査した。未定義名、verdict型、physical CLI rc、plain-runner
契約を修正した後、異なる2レンズの敵対reviewと3 fix巡を行った。

reviewの実効所見は、receipt provenance、reader-consensus/mutation mask、actual-bytes fixture、accepted正例、
非昇格2値、Git環境、型厳密性、attestation一意性だった。receiptに存在しない`prompt_path`を要求する所見は、
artifact descriptorのpath+SHA、pinned receipt raw SHA、receipt `prompt_sha256`の既存結線を実測してrefutedとした。
最終focusは全所見closed、新規must-fix 0、regressed 0だった。

## 実測

- 焦点走: 専用test fileとplain-runner meta-testの27 caseが27 passed。Pegasus request
  `955953.nqsv`、effective scheduler `loadgroup`。
- mutation baseline: 26 passed、status `PASSED`。
- mutation: SS-M1〜SS-M6が6/6 `KILLED`、期待/実測失敗node完全集合一致。
  `SURVIVED=0`、`MISMATCH=0`、`PARSE_ERROR=0`、`TIMEOUT=0`。
- ledger SHA-256: `8eb61633ec5b86f11baa1ee276352bddf78444b610a34c1b75d3177a929d0809`。
- attempt ledger SHA-256: `0fa42226bf1f955c6fa71f95b50326fa75351ad985992ec2be98ffb17534e088`。

## 変異artifact

- `mutation-spec-final.json`: commit `7cc5ce907`とspec SHA
  `d1750b75441faa7b7f8ad2faf2ffa2e118801b09ab7f1983dcc384b12d3920a8`へ束縛した6変異。
- `mutation-final-ledger.json`: baselineと6変異のstatus、失敗node完全集合、source/tool/runner束縛。
- `mutation-final-attempt.json`: collection、baseline、各mutationのdispatch request/receipt台帳。

## 限界・scope外

- 1 familyのavailability-selected retrospective diagnosticであり、catalog代表性やrouting効果を示さない。
- same-owner/same-model、session外情報、親projectionという共通trust root、multi-file atomic snapshotは未確立。
- §8全体、外部custodian、routing evidence、served-model attest、model既定化、汎用oracle基盤、別task familyは
  本waveへ追加していない。
- repo内gateとtestは同じ変更主体が編集でき、意図的弱体化への独立trust rootではない。
