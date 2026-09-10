# [T-2006] 非認証成果物型と A-1 投入器

## 結論

D1028/D1038/D1222 の非認証成果物型と A-1 投入器を同一変更単位で実装した。既存 certified gate、v1/v2 lock、環境契約、source binding、trace/perf 分離、anomaly reject は緩めていない。

## 実装した境界

- `campaign-lock/non-certifying/v1` は通常 lock decoder と lock-only certified gate から型で拒否され、A-1 専用 decoder だけが読む。
- trial registry の `registered-formal-non-certifying` と `certifying=false` を A-1 専用 sealed projectionへ接続した。S8C manifest/D510 lifecycleは複製していない。
- qsub前のcreate-only intent、submit-once、11-field submission receipt、one-shot scheduler completion receiptを既存A-1 CLIへ追加した。
- common bundle recordとworkload固有binding、intent由来disclosed-key HMAC tag、lock/WAL/COMMIT receipt/result/receipt digestを結合した。
- 既存result/receipt schemaを変えず、`paper-story-a1-non-certifying-observation/v1` sidecarとtoken-gated `NonCertifyingObservationView`を追加した。
- final viewはsubmission、job-terminal、completion、qstat raw request/state/exit、3 workload WAL、COMMIT receipt、anomalies=0を再検証する。
- legacy 4-file source bindingは不変。非認証sidecarだけがload-bearing 5fileを加えたexact 9-file closureを持つ。

## Threat boundary

本実装はsupported producer/consumer経路での型取り違え、field除去・付替え、record結合切断を防ぐ。同一Unix userがsource・lock・WAL・receipt・artifact全体を意図的に再生成する偽造耐性、外部trust root、秘密鍵custodyは保証しない。HMACはdisclosed-key identity binding tagであり、発行者認証とは主張しない。

## Review と fix

- 段3敵対相談2本、段6review2本、fix後focusを実施した。
- 初回reviewのreal 7件はcompletion chain、qsub cwd、NQSV `EXT`、legacy anomaly、source closure、volatile field、production fixture bridgeを修正して閉じた。
- focusで見つけたqstat raw/宣言不一致を共通parserと3負例で閉じ、最終focusは残るreal findingなし。
- D95 author初回はtoken上限で中断し、別authorが未監査差分を回収した。既存期待値の削除・反転、skip、xfailは行っていない。
- 初回全受入は共有fixtureとexact process inventoryの未追随4件だけが赤だった。D95 fixとread-only focusで、create-only intent、3 scheduler process site、`non_certifying=True`、admission-policy束縛済みconfig、eager 3-layout順序をexactに追随させた。productionとgateは変更していない。

## 検査

- 変更7 test files: 711 passed。
- source closure / fig4 / B-4 consumer meta tests: 207 passed。
- 初回全受入: tested main `c9f868ba8190911c5897dc8b6bdbd1da3d9cc259`、tested tip `41615c0b9c3b773e187ae696fd33962ee70d9398`、4 failed / 18,789 passed / 62 skipped。4件はすべて本waveの共有test fixture/inventoryへ帰属させ、免除せず修正した。
- 修正後全受入: tested main `93fcb4663b8d488c8f0b9095e29d4bff070288c5`、tested tip `0fad792a27b5e8b60d3799e498c99692d853d6d9`、`child-green`、18,828 passed / 67 skipped、red/flake 0、effective scheduler `loadgroup`、log SHA256 `c55e830b2628c94bbebf7636ed95eb0397f50258a14bf4b480ea7a78228ebd1c`。
- `check_codex_agents.py`: green。
- `check_docs.py`: green。
- provenance: 各commit前message検査とcommit後履歴監査がgreen。
- 変異matrix: final tip `fb7b8dbbafe1f07f91372d45b9f26ba00b9c706d`、baseline PASSED、9/9 KILLED、全expected node完全一致。
- 正式qsub、正式A-1測定、pushは実行していない。

## 変異成果物

- `mutation-spec.json`: 最終事前登録。
- `mutation-report.json`: baselineと9変異の判定、失敗node、実行artifact。
- `mutation-attempt.json`: dispatch attempt台帳。

## Commit

- production/review fix: `dd6ec73b9`、`c2136ece6`、`d7ccb67f3`、`4b5892bf0`、`fb7b8dbba`。
- acceptance fixture/inventory: `ebd7d3ff7`、`575617362`、`32953ac78`、`272cd14cc`。
