結論：現状は受理不可です。schedule 算術・内部 receipt 被覆・canonical key・CLI/env・protocol schema は整合していますが、実際の R33 CLI 経路には reserve を停止させる不整合と、aggregate の受理集合を過大化する欠陥があります。

## 主所見

1. `[real] [must-fix]` protocol/freeze digest の canonicalization が不一致です。

   driver は改行付き JSON を hash します（`orchestrator/campaign/s8b_oracle_n_pilot.py:1826-1835`, `:495-497`）。一方 admission は改行なしを hash します（`orchestrator/campaign/s8b_holdout_admission.py:354-366`, `:1882-1906`）。reserve は driver 側の値を admission に渡します（`s8b_oracle_n_pilot.py:2854-2866`）。

   実測でも protocol hash は `431c...` と `e3bf...`、freeze hash は `315b...` と `5526...` で一致せず、`_r33_protocol_and_freeze()` が digest mismatch で拒否しました。したがって実際の reserve-only は receipt 発行前に停止します。既存テストは admission fixture 側で改行なし hash を生成しており（`orchestrator/tests/test_s8b_holdout_admission.py:417-434`）、この経路を検出していません。

2. `[real] [must-fix]` documented aggregate procedure は同一 manifest の重複拒否により実行不能です。

   procedure は 3 allocation に同じ `admission.json` を渡します（`output/insights/2026-08-16_t1142-n-pilot-prereg/r33-qsub-procedure.md:73-76`）。しかし aggregate は duplicate manifest hash を拒否します（`s8b_oracle_n_pilot.py:2189-2191`, `:2322-2324`）。

3. `[real] [must-fix]` reserve の外部出力が public manifest ではなく private receipt です。

   reserve は指定された admission manifest path に receipt を直接書きます（`s8b_oracle_n_pilot.py:2851-2873`）。receipt には `claim_digest`、claim/ledger の private hash が含まれます（`s8b_holdout_admission.py:2259-2262`）。本来の public projection は別形式で生成・公開されます（`s8b_holdout_admission.py:2263-2269`, `:2718-2725`）。

   テストは内部 transaction の manifest path だけを確認しており、CLI 外部ファイルを確認していません（`orchestrator/tests/test_s8b_holdout_admission.py:582-596`）。

4. `[real] [must-fix]` aggregate の manifest identity 検証が hash 存在確認に留まっています。

   `_manifest_hashes()` はファイル hash と任意の `receipt_sha256` を読むだけです（`s8b_oracle_n_pilot.py:2149-2165`）。aggregate は admission 側の厳密な manifest validator を呼びません（validator 自体は `s8b_holdout_admission.py:2378-2399` にあります）。

   そのため role、campaign、allocation、cell、global index、receipt との対応を検証せず、テストも `{"receipt_sha256": ...}` 程度の偽 manifest を使用しています（`orchestrator/tests/test_s8b_oracle_n_pilot.py:1667-1671`）。

5. `[real] [must-fix]` aggregate は binary の完全性を確認しません。

   binary list が空でないことと allocation 間の identity しか確認していません（`s8b_oracle_n_pilot.py:2331-2351`）。12 cell 全ての binary が存在すること、session の cell 集合と一致すること、各 binary の schema を確認していないため、欠落した binary list でも aggregate を通過し得ます。

6. `[real] [backlog]` legacy `--rounds 1` 経路が壊れています。

   submit wrapper は legacy `--rounds 1` を案内しています（`tools/pegasus/submit_oracle_n_pilot.sh:14-17`）。job script も mode flag なしで driver を呼びます（`tools/pegasus/oracle_n_pilot.sh:363-379`）。しかし現在の driver は mode flag がなければ拒否します（`s8b_oracle_n_pilot.py:2730-2749`）。

7. `[real] [backlog]` precommit abort は staged ledger append と staged manifest の完全検証をしていません。

   abort は base ledger、claims、任意の receipt までは確認しますが（`s8b_holdout_admission.py:2809-2829`）、`ledger-append.jsonl` の正当性・行数・manifest の完全性を検証せず quarantine へ進みます（`s8b_holdout_admission.py:2838-2850`）。

8. `[real] [backlog]` allocation cache の identity envelope がありません。

   allocation mode は cache directory の空性・inode・`cached=False` を検査します（`s8b_oracle_n_pilot.py:828-858`, `:933-986`）が、role/campaign/allocation/receipt/schedule に結び付いた envelope marker はありません。Unit 2 計画の cache binding 要件（`outputs/stage2-plan-v2b.md:431-437`）を満たしていません。

9. `[real] [backlog]` Unit 0 の temporal authority 検査は実装されていません。

   `check_docs.py` は role・decision・checker の整合性を確認しますが、base commit より前に承認されたことは確認しません（`tools/check_docs.py:1559-1631`）。ただしこれは Unit0-v3 が明示的に same-tip を許可し、temporal enforcement を対象外にした結果です（`outputs/stage2-unit0-v3.md:380-405`）。現行設計では既知の残余リスクです。

10. `[real] [backlog]` テストは実運用経路を十分に覆っていません。

   schedule の単体検証や transaction recovery は実質的です（`test_s8b_oracle_n_pilot.py:1064-1095`, `test_s8b_holdout_admission.py:639-737`）。一方、run_sessions は 132 attempt ではなく 12 行の部分 schedule を使います（`test_s8b_oracle_n_pilot.py:1097-1144`）。新しい reserve/consume の qsub export テストもなく、shell 側は主に legacy export と `bash -n` です（`test_s8b_oracle_n_pilot.py:1758-1795`, `:1865-1871`）。実 manifest、同一 manifest 3 回の aggregate、CLI reserve→consume の正経路も未検証です。

## 検証結果

- `[refuted]` schedule 算術。実際の manifest は replicate 0–10 が index 0–131、11–21 が 132–263、22–32 が 264–395。driver の allocation slice も 0–131 / 132–263 / 264–395、各 132 行、local round 1–11 と一致します（`s8b_oracle_n_pilot.py:1028-1132`）。
- `[refuted]` 内部 receipt/claim/ledger の 396 index 被覆。receipt、claim、ledger は各 396 index を重複なく覆い、claim index と receipt index も一致しました（`s8b_holdout_admission.py:2277-2349`, `:2031-2088`）。
- `[refuted]` `_allocation_shift()` の delimiter attack。role/campaign は安全な identifier regex と `::` 拒否を通ります（`s8b_oracle_n_pilot.py:264-290`）。canonical key 自体も一意です。
- `[refuted]` job script の driver argv。reserve/consume の各 flag は argparse 定義と一致します（`s8b_oracle_n_pilot.py:2689-2711`, `tools/pegasus/oracle_n_pilot.sh:337-361`）。
- `[refuted]` qsub env。submit wrapper の `IZANAGI_PILOT_*` は job script の期待名と一致します（`tools/pegasus/submit_oracle_n_pilot.sh:313-331`, `oracle_n_pilot.sh:20-78`）。
- `[refuted]` protocol exact schema。実物は `load_protocol()` の exact key set を満たし、source driver/job hash も実ファイルと一致します（`protocol-r33.json:1-85`, `s8b_oracle_n_pilot.py:355-494`）。
- `[refuted]` shell policy/pin。R33 の reserve/consume と legacy/build 全てに policy と clean/pin 検査があります（`oracle_n_pilot.sh:183-335`）。

## 段2の14件との突合

- sol-1 `[real]`：v2b の temporal order は未実装。ただし Unit0-v3 で明示的に対象外。
- sol-2 `[refuted]`：role/source/decision/checker の exact 契約あり（`check_docs.py:1449-1631`）。
- sol-3 `[refuted]`：numeric D ではなく stable slug を採用。Unit0-v3 による上書き（`s8b_holdout_admission.py:102-115`, `stage2-unit0-v3.md:15-21`）。
- sol-4 `[refuted]`：append-only ledger、base prefix、foreign append を実装（`s8b_holdout_admission.py:2666-2710`）。
- sol-5 `[refuted]`：receipt/manifest は commit marker 前に guarded writer で作成（`s8b_holdout_admission.py:2963-2970`）。
- sol-6 `[real]`：内部 public projection はあるが、CLI 外部出力が private receipt。上記所見3。
- sol-7 `[real]`：commit recovery はあるが、abort 時の staged append/manifest 検証が不足。上記所見7。
- sol-8 `[refuted]`：attempt marker recovery を実装（`s8b_holdout_admission.py:3386-3428`）。
- luna-1 `[refuted]`：R33 consume は per-attempt token で、`_n_pilot_cell_state` に依存しない（`s8b_holdout_admission.py:3448-3627`）。
- luna-2 `[real]`：result identity はあるが、manifest/binary の semantic binding が不足。上記所見4・5。
- luna-3 `[refuted]`：`::` 禁止と canonical key 検証あり。
- luna-4 `[refuted]`：mode cardinality と forbidden option を検証（`s8b_oracle_n_pilot.py:2730-2840`）。
- luna-5 `[refuted]`：全 mode の policy/pin、consume のみ dependency build（`oracle_n_pilot.sh:246-335`）。
- luna-6 `[refuted]`：protocol の field copy、schema、source hash は一致（`protocol-r33.json:1-85`）。

## 総括

重複を除いた固有所見は次の通りです。

- (a) real 所見：10件
- (b) must-fix：5件
- (c) nit/backlog：5件

特に protocol digest mismatch は実行開始を阻止し、manifest/output/aggregate の3件は成果物の受理集合を直接壊しています。
