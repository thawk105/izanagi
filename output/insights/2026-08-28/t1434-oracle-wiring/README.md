# [T-1434] T-189 task-specific oracle wiring slice 実発火

- authority: none
- default_effect: no-state-change
- 実装 anchor: `56ae5e848`、safe-reader fix: `644695f7b`
- 可変状態の正本: worklog 末尾と `docs/phase3-t189-model-routing-preregistration.md`

## 結論

既存 task catalog の実在 plan 2 行を、互いに素な finding 集合を持つ限定 wiring sliceへ射影した。
blind verdictではmanifest unionを許し、mapping reveal後はtask自身の集合へ狭める。accept caseは通り、
T-1393 packetへT-1222 findingを置くcross-task caseはfull `verify` / `aggregate`でfail-closedになった。

これは§8の独立oracle ledger本体ではない。sliceは`oracle_content_review_status=not-established`、
`section8_complete=false`、task acceptance `unbound`、routing evidence `inconclusive`を固定する。
機械整合性やtest緑を意味的受理へ読み替えない。

## 実測

- portable/physical verifier: 2 task、integrity verified。physical modeはjobs rootのprompt/receipt bytesも照合。
- 焦点走: 698 passed / 2 existing growth-hold skips。fix3後のslice/OR関連40 caseは40 passed。
- node名付き再走: 6赤修正とfocus追加を合わせた9 caseが9 passed。
- mutation: baseline PASSED、OR-M1〜OR-M6 6/6 KILLED、完全集合一致、
  MISMATCH/PARSE_ERROR/SURVIVED/TIMEOUT 0。OR-M1はdiagnostic sensitivity、
  OR-M2〜OR-M6をcorrectness/integrity killとして数える。

## 変異 artifact

- `mutation-spec-final.json` — fix3後commitとtool transport pinへ束縛した最終spec。
- `mutation-final-report.json` — 最終matrix。repo head、spec SHA、各失敗node完全集合を持つ。
- `mutation-final-attempt.json` — collection、baseline、各変異のdispatch receipt所在を持つ試行台帳。

probe以前のinfra erratumと全Codex逐語は
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1434-oracle-realdata/` に保全した。最初の全file baselineは
nested submodule未初期化でPARSE_ERRORとなり変異0件で停止し、次のprobeは期待node採取用の
SURVIVED期待だったため6 MISMATCHになった。いずれも最終matrixへ数えていない。

## 限界・scope外

- §8完全ledger、独立content review、zero-finding negative cohort、coverage集計は未成立。
- task acceptance、stage2/stage5の意味境界、held-out採用lockは未成立。
- served-model attest、電力・margin、外部custodian/署名、汎用oracle platformは実装していない。
- repo内のgateとtestは同じ変更主体が編集でき、意図的弱体化への独立trust rootではない。
