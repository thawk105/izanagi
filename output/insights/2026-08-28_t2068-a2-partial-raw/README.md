# T-2068 A-2 partial raw authority 実装・監査記録

## 結論

A-2のexact 2 workloadでdriver成功がexact 1のときだけ、成功workloadのraw authorityをpartial v4
chainとして保持する。full-successとauthority-noneは既存v3 writer / consumerを維持する。
failed siblingのraw、cell、effectは物理的に存在しても読まず、局所anomalyまたはeffect非正は
workload authorityを消さずouter `reject`にする。実装anchorは`e4cb2da9157696504405c3fa7526e167c04842d8`。

## 実装した境界

- partial raw manifestは成功workloadのraw 2件とcampaign lock、WAL、claimのexact 5 member。
- completion / acquisition / raw manifestはv4、resultはpartial v1。full/noneのv3 schemaとstatus語彙は不変。
- manifest、submission receipt、completion receiptはwriterのcanonical pathを内容読込前に再導出する。
- `workload_authority` mapとouter `status`を分離する。authoritative anomaly / effect `<= 0`は`reject`、
  正effectは`partial`、判定不能は`inconclusive`。
- materializeはacquisition chainからreport全体を再導出し、偽authority/status、failed fields、
  v3/v4 cross-chainを拒否する。

## 敵対reviewとfix

初回外来差分はauthor receiptが`f43_fragment`だったため完成扱いせず、D95 Codex authorのrefocus/fixで
全2fileを再監査した。敵対review 2本は、(1) v4 nested authority pathがattempt配下の任意位置を許す、
(2) strict negative effect負例不足、(3) valid partial positive / inconclusive materialize正例不足、
(4) M7/M8 expected nodeの誤帰属をreal must-fixとした。fix後focus reviewは
`ACCEPT`、closed 4 / partial 0 / regressed 0。

## 検査

- 対象file全走: `98 passed`。repo外TMPDIRを使用した。
- 必須checker: `tools/check_codex_agents.py`、`tools/check_docs.py`ともにrc=0。
- 正式受入: `18624 passed / 62 skipped`、red 0、`child-green`。
- 受入tested main: `c384a90a0de357b0b4b00cddd3bbeef85576fa3e`。
- 受入tested tip: `e4cb2da9157696504405c3fa7526e167c04842d8`。
- 受入log SHA-256: `3cf842d00e67a9cbc67abe164b416ed42dc532de44e583926770d9af3b66cebd`。
- `/tmp/.git`の断続出現によるF662が再発した。T-2068到達不能の既存nodeだけが赤となり、
  repo外TMPDIRで同じ対象file全走が98 passedになった。production gateは緩めていない。

## 変異matrix

固定anchorに対し`tools/mutation_worktree.py`と`tools/mutation_harness.py`を使用した。
attempt 1はrunner argvの`--force-dispatch`欠落によりbaseline `PARSE_ERROR`で変異0件。
attempt 2はM2/M4/M5/M6/M8がexact KILLED、M1/M3/M7はexpected node集合不足でMISMATCH。
attempt 3でM1/M3/M7を実測完全集合へ再登録し、3/3 exact KILLEDを得た。初回結果は消していない。

| ID | 最終結果 | 検出した弱化 |
|---|---|---|
| M1 | KILLED | exact-one partial分岐の無効化 |
| M2 | KILLED | failed workload rawのpartial closure混入 |
| M3 | KILLED | v4 collectorのglobal failed-driver early return |
| M4 | KILLED | anomaly rejectのpartial降格 |
| M5 | KILLED | strict negative effectのpartial化 |
| M6 | KILLED | legacy v3 receiptのpartial dispatch |
| M7 | KILLED | evidence再導出report全体比較の除去 |
| M8 | KILLED | failed workload cells/effectsだけを無視する狭域弱化 |

最終合成は`8/8 KILLED`、SURVIVED 0、TIMEOUT 0、artifact error 0。raw ledger、spec、attempt sidecarは
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2068-a2-partial-raw/`に保全した。

## 非変更・scope外

完走済み`output/insights/2026-08-24_paper-story-a2-certification/`のbytes、判定、公開先は変更せず、
再発行・遡及昇格もしていない。failed siblingのcompute/reservation evidence一般化、cross-attempt reuse、
別campaign、複数success subset、汎用fan-outは実装していない。
