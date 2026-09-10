## 落ちる正例の全数

**新検査で落ちる repository 内の正例は 0 件です。**

| 経路 | 実際の値 | 既約分母 | 判定 |
|---|---:|---:|---|
| production 自己検査 | `1000 + i`, `i=0..201` | `1` | 正例、通過 |
| ledger tests | `10000 + i`, `i∈{0..204,300..304,800,900}` | `1` | 正例、通過 |
| analysis-path tests | `100` | `1` | 正例、通過 |
| issuer tests | `10000 + i`, `i∈{0..200,700,701}` | `1` | 正例、通過 |
| raw producer・material report 共有 fixture | `(100001 + 10i, 10)`, `i=0..200` | `10` | 正例、通過 |
| 新規有限十進 control | `(1,10)` | `10` | 正例、通過 |
| 新規拒否 control | `(1,3)`, `(1,30)` | `3`, `30` | 意図した負例 |
| tracked JSON/JSONL | exact key `reference_tps` は 0 件 | 該当なし | 影響なし |

根拠は各生成元の [ledger helper](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_analysis_ledgers.py:23)、[analysis-path helper](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_analysis_path.py:77)、[issuer helper](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_prerun_issuer.py:30)、[raw fixture の置換式](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_raw_record_producer.py:109)、[production 自己検査](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:757)です。raw fixture の分子は常に末尾が `1` なので `gcd(100001+10i,10)=1`、既約分母は全201値で `10` です。

tracked な JSON/JSONL 3,836 files を再帰走査しました。3,835 files は parse でき exact key は 0 件、残る壊れた JSON 1件にも `reference_tps` の文字列はありませんでした。

`reference_tps=None` の全経路は次のとおりです。

- 正当な非 `SCHEDULED` row は [新規 test](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_analysis_ledgers.py:166) に1件あります。`_seal` が hash と seal の両方を通します。
- in-memory では `_exact_ratio(None)`、新 guard、normalization が順に `None` を保存します。[変換](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:263)、[新 guard](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:341)、[normalization](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:447)
- wire の `null` は `_ratio_from_payload` で `None` に戻り、非 `SCHEDULED` なら loader を通ります。[wire decode](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:288)、[registry load](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:710)
- 201件の有限値と非 `SCHEDULED` の `None` 1件を使った read-only probe では、hash、seal、JSONL load、manifest generation、completeness のすべてが成功し、`None` は load 後も保存、manifest は201行でした。
- [構造述語 test の `None`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_analysis_ledgers.py:514) は `SCHEDULED` row を `_attempt_is_eligible` へ直接渡す負例です。registry に渡せば従来どおり `scheduled candidate lacks a complete block reference` で落ちます。正例ではありません。

なお、現行 repository の registry fixture で実測できる既約分母は **`{1,10}`** です。親裁定と author 記録の `{1,2,10}` は再現できませんでした。

## 波及

`orchestrator/campaign` 配下の直接 consumer は全4 filesです。

- [p3_b4_analysis_path.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_path.py:46): registry load、completeness、binding。
- [p3_b4_analysis_prereg_consumer.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:38): 自己検査の hash、seal、manifest generation。
- [p3_b4_material_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_material_report.py:30): publication reload と `build_contract_binding`。
- [p3_b4_prerun_issuer.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_prerun_issuer.py:36): 新規 issuance と publication reload。

[p3_b4_raw_record_producer.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_raw_record_producer.py:41) は issuer reload 経由の間接 consumer です。

また、列挙された API 以外にも `_build_registry` への再構成を通じて、`assert_scheduled_registry_complete`、`append_registry_violation`、`derive_registry_violation_count`、`build_contract_binding` の in-memory registry 受理集合が同じように狭まります。[再構成](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:642)、[append](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:772)、[derive](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:814)、[binding](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:1209)

非有限十進の写像は次のとおりです。

| consumer | 最終的な error code / exception |
|---|---|
| 新規 issuance | `SCHEDULED_INPUTS_INVALID`。最初の scheduled hash で落ち、seed・publication は作られない。[issuer:724](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_prerun_issuer.py:724) |
| issuer publication reload | `ARTIFACT_MISMATCH`。registry loader が manifest loader より先です。[issuer:1046](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_prerun_issuer.py:1046) |
| analysis path registry load | verdict `PROTOCOL_VIOLATION`、reason `FIELD_MISSING_OR_ILL_TYPED`。[path:124](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_path.py:124) |
| prereg consumer 自己検査 | 現行値はすべて整数なので発火しない。強制すれば `B4LedgerError` がそのまま伝播し、専用 code はない。[consumer:788](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:788) |
| raw producer 経由の reload | issuer error を `EVIDENCE_BINDING` へ写す。[producer:561](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_raw_record_producer.py:561) |
| material report 経由 | `publication_rejected`、detail 内は `artifact_mismatch`。[report:183](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_material_report.py:183) |

直接・間接の consumer test は全6 filesです。

- `test_p3_b4_analysis_ledgers.py`
- `test_p3_b4_analysis_path.py`
- `test_p3_b4_analysis_prereg_consumer.py`
- `test_p3_b4_material_report.py`
- `test_p3_b4_prerun_issuer.py`
- `test_p3_b4_raw_record_producer.py`

共有関係は、raw producer test が issuer test の `_eligible_attempts` を使い、material-report test が raw producer test の `_publication` を使う二段です。[raw import](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_raw_record_producer.py:54)、[material import](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_material_report.py:27)。値はそれぞれ既約分母 `1` と `10` なので、静的には赤になる consumer test はありません。

## 恒真化の検査

新検査は到達可能です。正しい型・正値・完全な scheduled metadata を持つ `(1,3)` は既存検査を通り、[新検査](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:344) だけで `reference_tps has no finite decimal expansion` になります。wire `[1,3]` も `_ratio_from_payload` を通った後、`_attempt_from_payload` 末尾の validator で落ちます。[decode と validate](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:395)

前後に同じ拒否層はありません。

- `scheduled_attempts_sha256` と seal は `_normalize_attempts` の validator が最初の有限十進判定です。
- registry load は reduced wire ratio を復元してから validator を呼びます。
- generate/completeness は registry の exact regeneration で初めて再検査します。
- producer の `_fraction_token` はさらに後段です。

既存検査も恒真化していません。

- `reference_tps=0` は引き続き `reference_tps is invalid` へ到達します。[既存検査](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:341)
- wire `[2,6]` は引き続き `wire reference_tps is not reduced` へ到達します。[reduced 検査](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:288)
- `SCHEDULED` の `None` や欠落 hash は新検査を素通りし、既存の complete-block 検査へ到達します。[complete-block 検査](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:358)

manifest-only の `(1,3)` は現在も受理されます。1行 manifest を canonical 化して reload する read-only probe で、`reference_tps == (1,3)` と byte equality を確認しました。`_manifest_row_payload` は正値 exact rational だけを検査し、有限十進述語を持ちません。[manifest row](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:939)、[manifest loader](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:1108)

M12 は実 `_fraction_token((1,3))` の例外と、patched 例外から `DECIMAL_NOT_TERMINATING` への production mapping を別々に検査しており、registry 拒否への単純移設にはなっていません。[M12](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_raw_record_producer.py:1140)

## closure と凍結境界

実計算値は次のとおりです。

- ledger member: `7476c81290a36346517968b375cad68cedf3620c8adc42807970c0115a23c152` → `71393e8d3ffc60e8af3421c1caf80abc1cf2395551173d96524b724ab5785cda`
- closure receipt: `57e84eeb4f8207ba9f4b6df704b2108c20592b2b129736d8462ec477bf4a384c` → `393fde87aa064fcced9d0a0bcb520994ba54dc6f2c2d12ad147845b3c88e68db`
- preregistration section: `0ceab4cd064eb8ff6c5dba22364fff04a6d708de8acb9d9cde52115f0891df30`
- semantic section: `5d0b189bd68391b4a6876bd24400230e7186f6bc1fe374ea298d44edebcfd1a7`

変更後の member hash と closure hashは、repository 全域の tracked file に literal で **0件**でした。closure は固定 member の bytes から動的生成されます。[member tuple](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_path.py:67)、[closure assembler](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_path.py:481)

事前登録 document、contract、adapter に HEAD 差分はなく、raw・semantic section hash は不変です。consumer result hashも `228ca7d3e4633c59528b5fae271f10fe64677e6367cbfd388d6ed10fa147a7d9` のままで、closure digest の変化要因は ledger member の1件だけでした。

tracked な B-4 `scheduled-attempt-registry.jsonl`、`analysis-manifest.json`、`prerun-issuer-receipt.json` は repository 内に0件です。したがって既存 artifact の repin 対象もありません。

旧版と新版を同一 process でロードし、既約分母 `1`、`2`、`10` と非 `SCHEDULED None` を含む positive batch を比較した read-only differential probe では、次がすべて byte-identical でした。

- batch hash: `57e371ffacb13e313495f088fdaf9fc2610cb4714c430eda7150121a8c8cdd6e`
- registry canonical SHA-256: `bf47115e91b9fcf2555da3bf7872d5a78e2ba3181b76f83b78fa22875f450774`
- manifest canonical SHA-256: `d61747d8847f72a1c0b8a1e57ecebf5565ae3e25b168ef0e6e9a1e1f6a2378b3`
- 選抜順: 最初の201行で一致
- completeness/report 値: `row_count=201`、`registry_violation_count=0` で一致

したがって、従来から受理される有限十進について canonical bytes、batch hash、選抜順、下流 report 値は変わりません。非有限十進だけは意図どおり artifact 生成・load の前に拒否されます。

## 裁定との整合

述語は D1424 決定4と一致します。`_exact_ratio` が `Fraction` により既約化し、その正の分母から2と5を除き、残余が1かを検査しています。[既約化](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:263)、[述語](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:344)

共有変換権威 `as_b4_exact_fraction`、adapter、contract には述語が漏れていません。[shared authority](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_contract.py:233)、[adapter 利用](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_adapter.py:129)

事前登録 §5.1.1 の4入力、入力検証先行、全 invalid reason 収集、`reference_value_domain_error` の「有限の正でない」という意味は変化していません。[事前登録](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/docs/phase3-b4-reflux-ablation-preregistration.md:385)、[contract 検証](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_contract.py:306)

HEAD `3be06d9ff` は提示 patch と一致し、変更は裁定どおり production ledger 1 fileと test 2 filesだけです。worktree は clean、`git diff --check HEAD^ HEAD` も異常なしでした。pytest は実走しておらず、緑とは報告しません。

## 所見一覧

- **F-1 — must-fix / refuted: repository 内の正例が新検査で落ちる。** 根拠: 全 registry input family の既約分母は `{1,10}` で、新 guard は `None` を除外して評価します。[validator:341](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:341)
  成果物影響: 既存の certified 選択・台帳・report の値と参照は変わりません。

- **F-2 — must-fix / refuted: 新検査または既存検査が恒真化した。** 根拠: `(1,3)`、`0`、wire `[2,6]` がそれぞれ新検査、既存 invalid、既存 not-reduced へ別々に到達します。[ratio decode:288](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:288)
  成果物影響: 各拒否署名の受理集合上の境界は維持され、非有限十進だけが縮小します。

- **N-1 — nit / real: fixture の既約分母を `{1,2,10}` とする記録は現物と不一致。** 根拠: [段4記録:127](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2102-b4-reference-tps-domain/artifacts/t2102-b4-reference-tps-domain/s4-ruling.md:127)、[author記録:38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2102-b4-reference-tps-domain/artifacts/t2102-b4-reference-tps-domain/s5-author.md:38) に対し、現行 fixture は `{1,10}` です。
  成果物影響: なし。記録上の列挙だけの不一致なので nit です。

- **N-2 — nit / real: 受理集合が狭まる public API の記録が非網羅。** 根拠: `append_registry_violation`、`derive_registry_violation_count`、`build_contract_binding` も registry 再構成を通ります。[append:783](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:783)、[derive:821](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:821)、[binding:1218](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:1218)
  成果物影響: 非有限十進を含む forged in-memory registry は append・count・binding でも拒否されます。repository 内に該当 producer/fixture はなく、既存成果物値は不変です。

- **N-3 — nit / real: prereg consumer 自己検査には非有限十進向けの error code mapping がない。** 根拠: `_behavior_registry` の `scheduled_attempts_sha256` 例外を上位が変換していません。[consumer:788](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:788)、[public check:1005](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:1005)
  成果物影響: 現行自己検査は整数しか生成しないため、closure receipt・certified 選択・report は変わりません。到達しない固定自己検査面なので nit です。

- **F-3 — must-fix / refuted: 裁定 scope を超えて contract/adapter/manifest codec を狭めた。** 根拠: production 差分は `_validate_attempt` の8行だけで、manifest-only `[1,3]` は実際に受理されました。[manifest codec:939](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:939)
  成果物影響: 分析契約の受理集合と `reference_value_domain_error` の参照意味は不変です。

## 総括

must-fix の real 所見はありません。
repository 内の正例は0件も落ちず、正当な非 `SCHEDULED None` は全 registry lifecycle を通ります。
新検査・既存 invalid・wire not-reduced はそれぞれ到達可能で、manifest-only `[1,3]` も維持されています。
closure digest だけが予定どおり変化し、新 digest の literal pin は0件です。
実装は D1424 と段4裁定に整合しますが、fixture 分母と transitive API 範囲の記録に nit が2件あります。
pytest は実走していません。