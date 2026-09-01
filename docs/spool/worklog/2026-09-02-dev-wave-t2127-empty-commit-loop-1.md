---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2127-empty-commit-loop
seq: 1
title: [T-2127] certified view の全称保証と存在保証を分けた — 起票の欠陥記述は不正確で、値が変わるのは certifying Layer3 の 1 箇所だった (コード + テスト、branch worktree-dev-wave-t2127-empty-commit-loop、変異 10/10 KILLED・生存 0)
---

## 本文

- **起票の欠陥記述は不正確だった。** 「commit 0 件で検査 loop が空回りし証拠なしで certified view が
  発行される」とあるが、「存在する全 commit の証拠が妥当」という全称命題は 0 件でも真である。
  空走そのものは欠陥ではない。欠陥はその全称保証を存在保証として読む consumer 契約の曖昧さにあり、
  段 3 のレンズ A が指摘して親が採用した。閉じ方は {{D:certified-view-universal-vs-existential}}。
- **値が変わる箇所は 1 つだけだった。** `layer3_report.build_accepted_report` は acceptance receipt の
  certifying、trial 一致、admission_status=admitted、decision 不変、epoch E1 を要求するが、
  どこも commit の存在を要求しない。1 件も commit されず 1 件も検証されていない campaign から
  `certifying_input: True` の Layer3 report が出せる。**これは親の推測ではなく、
  既存の passing test (`test_layer3_report.py` の build_start 1 件だけの fixture) が現に固定していた。**
- **依頼が名指しした `certified_writer_*` は本欠陥の閉包外だった。** 全文検索で
  `artifact_admission`・`CertifiedCampaignView`・`CERTIFIED_ACCEPTANCE`・`STAGE_COMMIT` の
  参照が 0 件。編集面から外して段 4 で再裁定した。
- **admission 層で commit 0 件を一律拒否する案は却下した。** 受理集合を等価に縮小する probe を
  当てると baseline 全緑の consumer テストが 126 node 赤になる。中身は全試行 abort の campaign の
  棄却を報告する正当な経路である。さらに `autonomous_trial_completeness` の
  failure campaign 負例制御は「certified 受入で拒否されること」に依存しており、
  一律拒否はこれを abort-only campaign に対して恒真化する。受理集合を締めたつもりで
  正しさ検査を 1 本殺す型である。
- **非ゼロ要求の配線は段 2 プランの 6 箇所から 2 箇所へ縮小した。** 外した 4 箇所は反実仮想で
  「既存 gate が同じ入力で先に赤を出す」ことを確認した。判断規範は
  {{D:nonzero-wiring-needs-counterfactual}}。段 3 のレンズ A・B が親と独立に同じ結論を出した。
- **段 2 プランの consumer 共通化は不採用にした。** 外部 consumer へ segment / window だけを
  渡す案だったが、単数 helper は `records[:commit_index]` を証拠母集合とし receipt との
  完全一致を要求するため、母集合を狭めると receipt に載らない verify が見えなくなり
  **受理集合が広がる**。段 3 のレンズ A の指摘を採用した。
- **件数 field の限界を記録する。** `__post_init__` の件数一致検査は records から導出できる値の
  二重導出であり、独立した証拠検査ではない。件数は誤った値を発行できないことだけを保証し、
  各 commit が検査を通ったことは証明しない。docstring にも明記した。
- **consumer 閉包は名前検索の和集合 22 file では足りなかった。** 意味的 consumer として
  `orchestrator/verifier/commit_receipt.py` (関数内 import) が加わり 23、さらに
  `replay.load_landscape` 経由の間接 consumer 2 file (`search_baselines.py`、`guided.py`) がある。
  後者は `CERTIFIED_ACCEPTANCE` も helper 名も持たない。非ゼロ要求を共有入口へ置いたのは
  この取りこぼしを避けるためである。
- **変異は冗長 gate に過剰決定されていた。** 初回 probe では `artifact_admission.py` を触る
  9 変異すべてで `test_p3_b4_wiring_probe.py` の 21 node と `test_layer3_report.py` の 5 node が
  落ちた。contract-loader drift と作業ツリー汚染の gate であり機構の証拠にならない。
  この 2 file を選択から外して実効 gate へ再照準し、機構固有の node 集合を完全集合として
  本走した。結果は 10/10 KILLED・生存 0・MISMATCH 0、baseline 緑。
- **段 6 の焦点走で 2 度、contract-loader drift を実装の赤と取り違えかけた。**
  `artifact_admission.py` は exact 24 path の member なので、未 commit のままでは
  certified 経路の焦点走が `current-closure-unavailable` で赤くなる。commit すれば消える。
  実装の回帰ではない。
- **自己 SHA の波及は本 wave の blocker ではないと裁定した。** `artifact_admission.py` は自分の
  SHA を `validator_sha256` へ、`layer3_report.py` は自分の SHA を `meta.generator.sha256` へ
  成果物に埋める。段 3 のレンズ B が「保存済み report と fresh rebuild が byte 不一致になる」と
  指摘したが、repo 内の保存済み report 7 件の `generator.sha256` は既に現在値とずれており
  (`705508de…` / `89aa98e8…` に対し当時の現物は `362fb98f…`)、`validator_sha256` は field 自体が無い。
  本 wave が持ち込む破れではなく、両 file を編集するあらゆる wave に共通する既存の設計性質である。
  互換層の新設は scope 外として却下した。
- **「既存 certified 成果物の値は変わらない」の射程を限定する。** tracked corpus に E1 certified
  campaign がそもそも無いため、ほぼ空集合についての結論である。正しくは
  「tracked repository corpus では未発火」である。段 3 のレンズ A の指摘を採用した。
- **126 という数の使い方を限定する。** これは一律 admission gate 案を却下する証拠にだけ使う。
  実装で赤くなる node 数の上界ではない (必須 field 追加や test support の追従など
  probe に含まれない変更面がある)。
- 段 6 の fix は 2 巡した。1 巡目は fixture の commit だけ env_tag を契約値へ直したため、
  WAL の env_tag が一意でなくなって赤が残った。親が `layer3_report` の一意性要求と
  契約値 `linux-baremetal` を測って 2 巡目へ渡し、全 record を揃えて閉じた。
- 実測環境は Pegasus login node の bounded local と計算ノード dispatch。
  段 1 の probe は repo 外の pytest plugin を使ったが、dispatch 経路は `PYTHONPATH` を
  伝播しないため局所実行に収まる小分けでしか走らない。
- 変異走行は 1 度、並行 wave の land で共有木の観測 bytes が変わり rc=125 で中止した。
  出力 path と wrapper-attempt を新しくして再走し完走した。自分の差分の赤ではない。

## 次の一手差分

### 完了

- [T-2127] 全称保証と存在保証を分けて閉じた。共通入口 `admit_persisted_certified_commits` と
  件数 field、`require_certified_commit_evidence` を新設し、`replay.load_landscape` と
  `layer3_report.build_accepted_report` の 2 箇所へ配線した。変異 10/10 KILLED・生存 0。
  remaining: none
  base: 47776f2e91fc5cc8dc239a92d650533eee2109c82252a58b06e843c86598637a
