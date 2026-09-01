---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-01
wave: dev-wave-t1806-prereg-c10-fieldpaths
seq: 2
---

## {{D:c10-field-paths-single-binding-table}}. C10 の契約 field と判定器を単一対応表と完全一致で束縛する

**決定:** 事前登録契約 C10 の `field_paths` へ `proposal.build_source_bindings` を足すと同時に、
判定器側の `_C10_FIELDS` も `proposal_build_source_bindings` へ広げる。両者は
`(実装 literal, 契約 field path)` の**単一の対応表**から導出し、契約との整合検査は
`frozenset(requirement("cross_binding_verifier").field_paths) == 期待集合` の**完全一致**で行う。
片方向の包含 (`all(x in y)`) は採らない。失敗時は新しい reason code を作らず既存の
`cross-binding-verifier-incomplete` を返す。判定器版を `s8c-decider/v7` へ上げ、
条件凍結を第 12 世代として再発行する。

**理由:**
- 契約 JSON は `_evaluate_c10` に読まれておらず、判定器が照合するのは Python 定数だけである。
  契約だけを広げても正式 gate の検知集合は 1 件も増えず、D967 が理由に挙げた
  「後から実装を弱めても正式 gate が検知できない」は解消しない。
- 片方向の包含は契約側に余分な field が増えても通る。C06 が既に持つ `field_paths` の idiom は
  実際には完全一致であり、片方向の `all` は `reachable_from` 用の別 idiom であった。
  段 3 の 2 レンズが独立に同じ欠陥を指摘した。
- 対応表を 1 つにすると、表を縮めて gate を静かに弱める経路が契約との不一致として露見する。
  独立した 2 つの手書き集合では、両方を同時に縮めれば検査が通ってしまう。
- 契約が要求するのに判定器が見ていない状態を恒真に近い関門として是正する方向は、
  同族の D1292 が C04 について既に採っている。

**却下した選択肢:**
- 契約 JSON だけを広げる — 記述は整うが検知力は増えず、D967 の理由を満たさない。
- 片方向の包含で整合を見る — 契約側の余剰 field を許し、drift 検査の名に値しない。
- 汎用の drift framework を新設する — 対象は C10 の 13 field だけで足り、既存 idiom で閉じる。

**限界 (主張せず明記する):** この検査が証明するのは
`verify_s8c_cross_binding` の AST に当該 literal が存在することまでである。
到達しない枝に literal を残したまま、その field が守る照合だけを無効化する弱体化は
この gate を通る。field の生成・再読・値の束縛は producer 側の functional test の責務であり、
本 gate はそこを保証しない。事前登録した条件版の変異が実際に生存することでこの射程を機械化した。

## {{D:d967-e1-stale-premise-superseded}}. D967 が想定した既存 campaign の失効は発生しないと記録する

**決定:** D967 は「既存 campaign が `E1-stale` になることを正直な migration として記録する」と
定めているが、その前提は現行コードでは成立しない。D967 の 3 つの行動 (契約を広げる・
凍結を再発行する・判定器版を bump する) は**すべてそのまま実行**し、記録だけを事実へ合わせる。

**理由:**
- D967 の翌日に下された D1163 (絶対規律 7 の新設) が、
  `artifact_admission._require_verifier_epoch_for_purpose` の
  `recorded-current-closure-mismatch` による拒否経路を名指しで撤去した。
  現行実装は現在の閉包が取得可能かだけを見る。
- 実測: tracked な `campaign.lock` は 32 件で、`contract_loader_blob_sha256s` を持つものは 0 件。
  よって本件で新たに失効する campaign は 0 件である。
- D967 の指示は「隠さず正直に記録する」ことであり、
  **起きなかったことを起きたと書くのは同指示への違反**である。
- 作業ツリーが汚れている間の一時的な `current-closure-unavailable` は従来どおり残る。
  これは失効ではなく取得不能である。

**却下した選択肢:**
- D967 の字面どおり失効を記録する — 事実に反し、台帳を読む者を誤らせる。
- 前提が崩れたことを理由に D967 の実装自体を止める — 3 行動はいずれも前提に依存しない。
