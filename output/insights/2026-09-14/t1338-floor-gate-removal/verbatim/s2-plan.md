## 前提の確認

**B は key ごと撤去する案 (a)、8c は冒頭への追記を推奨します。A の全面撤去は、親の supersede 主張だけでは成立しません。C は他の receipt consumer が残り、撤去範囲によってはその前提を弱めます。**

以下の行番号は現 checkout のものです。`M` は `orchestrator/campaign/s8b_oracle_manifest.py`、`F` は `orchestrator/campaign/floor_pair_driver.py` を指します。

- D496 は比較の基礎から過去値を外す裁定です。
- D501 決定 8 は撤去による受理集合の拡大を認めています。「撤去対象の拒否入力がすべて他で拒否される」という完全同値の主張とは区別が必要です。
- D911 に従い、8c の条件契約・評価器・世代 record は変更しません。
- 編集・commit・pytest 実行はしていません。追記案の hash 比較だけを、既存 parser を使ってメモリ上で実施しました。

## 依頼 1 のプラン (file:line)

| 対象 | 編集候補 | 内容と留保 |
|---|---|---|
| A | `M:609–670`、呼出し `M:687–688` | 全撤去候補。ただし後述の未代替部分があるため、そのまま実装子へ渡すことは推奨しない |
| A の集合検査 | `M:615–631` | 少なくとも holdout 値の構造と `pairs == configurations − stock` は残す候補。schedule 検査はこの述語を代替しない |
| A の値・相関検査 | `M:632–670` | 有限正/null、`scale_ref` と null の相関、`scalar_alt == max(pairs)`。これも manifest API 単体では未代替 |
| A 専用 helper | `M:568–574` | A の数値検査を全部外す場合に限り、唯一の利用が消えるため削除 |
| 残す helper | `M:577–606` | `_holdout_configuration_ids` は `M:1078` でも使う。削除不可 |
| B の key | `M:58` | `floor_budget_snapshot_sha256` を `_MANIFEST_KEYS` から削除 |
| B の生成 | `M:807–809` | 部分 hash の生成 field を削除 |
| B の照合 | `M:1093–1096` | 部分 hash 比較を削除 |
| verdict の連動箇所 | `orchestrator/campaign/s8b_verdict.py:846–847` | 呼出し先の変更で連動する。残存する floor/budget 検査があるので、`_validate_execution_snapshot` 呼出し自体は消さない。コメントのみ実態へ合わせる |
| C | `F:1091–1119`、`F:1150–1152` | helper 全体と呼出しの削除候補。ただし binary 一致以外の receipt 検査も同時に消える |
| C の import | `F:51` | helper 全撤去なら import を削除し、テスト側の間接参照を同時に直す |
| C の残存参照読取 | `F:1143–1149` | tracked receipt の実在・bytes hash 束縛。名指された helper と別述語なので維持 |
| C の残存 binary 検査 | `F:1136–1142` | 現 binary と spec の hash 一致。維持 |
| 行番号参照 | `orchestrator/campaign/p3_b4_floor_artifact_issuer.py:758–765` | C の変更と同じ所有単位でコメントを訂正。既に参照先の説明が実装とずれている |

`M:674–686` と `M:689–703` の floor/budget null、holdout 集合、budget 値・共有性検査は残します。

**C の狭い撤去候補**は `F:1107–1115` の「receipt と今回の artifact の binary hash 一致」だけです。`F:1093–1106` の strict receipt 検証と `F:1116–1119` の trace 検査は既存述語として残せます。これは新設ではありません。ただし、依頼が helper 全撤去を意味するか、binary 束縛だけの撤去を意味するかは親へ返します。

## 依頼 2 のプラン (file:line)

**挿入位置は `docs/phase3-8c-preregistration.md:17`、既存の `## 0.` の直前です。**

追記案：

> **条件 2 (非干渉性) は未解決である。** 現行の条件 2 の証拠契約は production sink における arm binding の単射性を要求するが、非干渉性を表す field を持たない。arm 束縛の証明を非干渉性の充足と解釈しない。D911 に従い証拠契約は据え置き、周辺の確定後に一度だけ改訂する。

実装から導ける編集境界は次のとおりです。

| 文書の行範囲 | 保護対象 | 根拠 |
|---|---|---|
| `25–56`、`57–71`、`72–88`、`89–193` | §1〜§4 の見出しを含む規範本文 | `s8c_preregistration.py:1032–1039` |
| `198–206` の左列 | §5 の欄名集合 | 同 `:788–835`、`:1044–1045` |
| `210–293` | §6 の条件 1〜12。条件 2 は `213–221` | 同 `:972–1012`、`:1046–1056` |
| `208–477` | §6 全体。条件列挙の後の説明・発効ポリシーも含む | 同 `:1032–1039` |
| `478–572` | §7 全体 | 同上 |
| `1–24` | 上記 hash の抽出範囲外 | 同 `:710–744` の section 境界と `:1039` の選択 |

したがって、親 brief の候補 `:96`、`:214`、`:443–449` は**いずれも触れません**。特に `:443–449` は説明文でも §6 規範本文 hash に入ります。

証拠契約の根拠：

- `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:46–95`
- `:51–79` の field は arm/digest/descriptor/namespace。
- `:91` の要求は明示的に injective arm binding。
- `s8c_preregistration_evidence.py:1968–2052` も call edge、field、namespace 消費を検査し、最後は `EVIDENCE_UNDEFINED / COMPLETION_PROOF_NOT_MACHINE_CHECKABLE` を返します。非干渉性の成立証明ではありません。

追記案をメモリ上で比較した結果、欄名 hash、条件全体 hash、条件別 hash、規範本文 hash、protected hash はすべて不変でした。protected hash は前後とも：

```text
1e325f9d9ce483b14d02e2c857f785007afa45005112127312b409d77cfee684
```

文書全体の bytes hash は変わります。`DECIDER_VERSION` と世代 record は変更不要です。

## 必ず答えること 1〜7 への回答

**1. supersede する既存述語の実在と発火**

`M:1053` はファイルを再 hash する処理ではなく、**caller が渡した `freeze_sha256` と manifest の記録値の比較**です。`freeze_document` の内部整合をこの場で導出しません。

| 入力の形 | 撤去後に拒否する既存述語 | 判定 |
|---|---|---|
| freeze bytes だけ変更し、manifest の freeze hash は旧値 | caller が新 bytes の hash を渡せば `M:1053–1054` | 代替あり |
| schedule から holdout を丸ごと落とす | `M:1070–1074` | 代替あり |
| 各 replicate から同じ構成を落とし、schedule 自体は完全ブロックにする | `M:1075–1084` | 代替あり |
| 特定 replicate だけ cell を欠落・重複させる | `M:364–371` | 代替あり |
| floor の `pairs` だけ欠落・余分・stock 混入。schedule は完全 | 上記 schedule 述語は参照しない | **代替なし** |
| floor が scalar、holdout 値の field が欠落・余分 | 全 byte hash は構造を検査しない | **manifest API 単体では代替なし** |
| pair が 0・負値、`scalar_alt` 不整合、null 相関違反 | 全 byte hash・schedule 集合とも検査しない | **manifest API 単体では代替なし** |
| `freeze_document` だけ変更し、渡す hash は旧値 | `M:1053` は通る | **A/B の検出力と同値ではない**。caller の snapshot 信頼境界に依存 |
| B の field だけ書換え、`manifest_id` は旧値 | `M:1160–1162` | 内容 ID 不一致で拒否 |
| B の field と `manifest_id` を整合的に書換え | B 撤去前は拒否。案 (b) では通り得る | **B 固有の拒否が消える** |
| 有効な別 binary の receipt を今回の spec に指定 | `F:1138` は今回の binary/spec 一致しか見ない | **C の対 receipt 一致は代替なし** |

実在する追加の上流検査もあります。

- `s8b_ratified_freeze.py:1070–1086`：凍結 floor と floor source の投影一致。
- 同 `:3291–3324`：floor artifact の再検証。
- `s8b_floor_stats.py:1080–1088`：再計算した `pairs`、`scalar_alt`、`scale_ref` と申告値の比較。
- `s8b_ratified_freeze.py:3687–3695`：published freeze の再検証が上記経路へ入る。

これは**その上流経路を通る入力についての代替**です。`_validate_execution_snapshot` や generic builder の直接入力まで覆う根拠にはできません。

既存の発火確認用テストは以下です。今回は未実行です。

- `test_s8b_oracle_manifest.py:797`
  `test_verify_detects_freeze_byte_tampering`
- 同 `:413`
  `test_subset_manifest_build_stays_accepted_but_verify_choke_point_rejects`
- 同 `:450`
  `test_missing_holdout_build_stays_accepted_but_verify_rejects`
- 同 `:324`
  `test_each_replicate_is_complete_product_and_each_cell_occurs_n_times`

**2. P2：B の受理形**

| 項目 | (a) key ごと撤去 | (b) key を残し照合だけ撤去 |
|---|---|---|
| 編集 | `M:58,807–809,1093–1096` | `M:1093–1096`。生成は残す必要がある |
| schema の受理形 | 旧 key 付き文書は `M:1043` で拒否 | key 必須のまま。値の意味検査は消える |
| 生成と key 宣言を別々に外す案 | 不可。生成物自身が exact key 検査に通らない | 同左 |
| manifest ID/hash | `M:736–737,814,1160–1162` と `manifest_sha256` の値が変わる | 生成を残せば既存正例の値は変わらない |
| 既存 artifact | 旧形の読み直しには影響する | 旧形を維持 |
| 推奨 | **採用** | 恒真な意味 field が残るため不採用 |

現 checkout には `output/s8b-oracle-manifest-candidates` と `output/s8b-oracle-spec` がありません。`test_s8b_oracle_manifest_contract.py:135` の `test_schema_v1_has_no_durable_manifest_candidate_or_reviewed_spec` もこの前提を固定しています。探索で見つかった schema 文字列入りの insight は、それだけで現行の凍結 manifest artifact とは数えません。

`_GENERATOR_SOURCES` (`M:65–75`) の 5 file は変わりません。したがって reviewed-spec の generator identity と、その独立 golden は据え置きです。

**3. P3：A の純減**

**`pairs` の key 集合検査は、D501 決定 4 の schedule 検査では覆われません。**

`M:1078` は `holdouts[h].variant_binding.entries` を読み、`floor.by_holdout[h].pairs` を読みません。両方が同じ構成集合を参照していても、比較対象が違います。

残す候補は `M:615–631`。さらに、brief の「別述語による拒否を示せなければ撤去しない」を API 単体にも適用するなら、数値・相関検査 `M:632–670` も保留になります。ここを「全 byte hash で完全代替」と説明して削除する計画にはできません。

**4. P4：receipt consumer はゼロにならない**

`validate_portable_binary_record` の他の production consumer：

| file | 呼出し行 |
|---|---|
| `s8b_oracle_driver.py` | `1034` |
| `s8b_holdout_freeze.py` | `1525` |
| `s8b_floor_stats.py` | `1252` |
| `s8b_ratified_freeze.py` | `1827` |
| `s8b_floor_campaign.py` | `4854,5769,5863,6494,8114` |

また `p3_b4_floor_artifact_issuer.py:775–805` は、module を import せず receipt record を読み、`binding.genome_canonical` から protocol を導出する**間接 consumer**です。

C 全撤去後、この issuer が読む record は、producer 入口で strict receipt 検証を受けたとは限らなくなります。issuer 自身の `:781` の hash 照合は receipt の意味検査の代替ではありません。

なお、oracle 側には `s8b_oracle_driver.py:1052–1063` の floor receipt 対 store binary hash 照合が残ります。**F の C を削除しただけで oracle 全体の過去 binary 束縛が消えたとは報告できません。**

**5. consumer・helper・fixture・test**

追跡した依存は次のとおりです。

| 起点 | helper／fixture 経由 | 影響 |
|---|---|---|
| A/B | `test_s8b_oracle_manifest.py:161,210,297,918–932` | builder、freeze fixture、verifier、snapshot 直接テスト |
| 共有 floor fixture | `s8b_v2_freeze_fixture.py:31–74` → manifest/driver/report | 正例の値は変更不要。`:7–8` の撤去 helper を指す説明は訂正候補 |
| reviewed spec fixture | `s8b_oracle_spec_fixture.py:38–99` → manifest/driver/report | floor 部分 hash を持たない。bytes/hash の変更不要 |
| report fixture | `test_s8b_oracle_report.py:205,232,281,322` → judge `:27`、verdict `:35` の import | manifest は再生成され、派生 hash も追随。直接の期待赤は確認していない |
| driver fixture | `test_s8b_oracle_driver.py` → `test_s8b_binding_driftguards.py:43,232–245` | manifest 生成を間接利用 |
| v2 candidate fixture | `test_s8b_holdout_freeze.py:28`、`test_s8b_ratified_freeze.py:51` | floor producer 用の正例形は維持 |
| C | `test_floor_pair_driver.py:62` → `_portable_build_record` → `_write_inputs:157` → `_document_only:475`／`_prepare_spec:443` | production import を消すなら test 自身から admission module を直接 import する変更を同時に行う |
| C の二段目 | `test_p3_b4_floor_artifact_issuer.py:19,65,212–221,794` | driver test helper を再利用。receipt fixture の単純化は波及するので行わない |
| conftest | `orchestrator/tests/conftest.py:395,424–430,701–730` | driver test の hold/memo 分類。撤去述語の注入ではない |
| さらに間接 | `test_real_repo_serialization.py:2383,5115` | driver/driftguard/memo の identity・保留契約を読む。変更不要 |

**A 全削除で期待赤になる既存テスト**は `orchestrator/tests/test_s8b_oracle_manifest.py` の次の 8 関数です。

- `:957 test_snapshot_rejects_null_pair_with_nonnull_scalar_alt`
- `:977 test_snapshot_rejects_scalar_v1_floor`
- `:986 test_snapshot_rejects_stock_key_in_pairs`
- `:994 test_snapshot_rejects_missing_pair`
- `:1003 test_snapshot_rejects_extra_pair`
- `:1011 test_snapshot_rejects_scale_ref_null_with_finite_pair`
- `:1020 test_snapshot_rejects_scalar_alt_not_max`
- `:1037 test_snapshot_rejects_nonfinite_pair_value`

集合・構造部分を残す場合、`:977,986,994,1003` の拒否期待は維持します。

**C 全削除で意味上の期待赤になる関数**は：

- `test_floor_pair_driver.py:1198`
  `test_build_receipt_binary_sha_and_trace_mutations_fail_closed` の `record-binary-sha`、`receipt-trace` 両 parameter。

同 `:1176 test_build_receipt_uses_real_binary_admission_validator_and_binds_sha` は test 本体が自分で validator を呼びます。fixture import を直せば、production で検証しなくても通り得るため、既存のまま撤去後の証拠には使えません。

`F.s8b_binary_admission` 参照を放置して import だけ削除すると、上記 helper 利用テストが広く `AttributeError` になります。この機械的な破損は helper の直接 import 化と同時に解消する計画です。**その中間状態で赤になる全関数名の列挙は未完了**です。

**6. pin 閉包**

確認できた pin と追随方針：

| 種類 | 所在 | 扱い |
|---|---|---|
| A 拒否理由の regex | `test_s8b_oracle_manifest.py:962–1044` | 上記 8 テスト。残す述語と削る述語を分ける |
| C 拒否理由の regex | `test_floor_pair_driver.py:1227` | 全撤去なら期待を変更 |
| exact top-level keys | `M:55–60,1043` | B の生成・照合と一体で変更 |
| 内容由来 ID/hash | `M:181–189,736–737,814,1160–1162` | 新文書から既存方式で再導出 |
| reviewed-spec 独立 literal | `test_s8b_oracle_manifest.py:66–106,1159–1179` | 対象 3 module は generator 集合外。更新不要 |
| source repin golden | `test_s8b_oracle_driver.py:149–258` | 今回の編集 source を pin していない。更新不要 |
| source 全体 hash | `output/insights/2026-09-09/t2344-closure-reachability/trace-freeze.json:429–430` | 現 M の `2e357512…729f10`。過去実測記録なので書換えない |
| verdict 全体 hash 記録 | `output/insights/2026-09-08/t2067a-oracle-selection-enforcement/verbatim/review-b.md:18` | 現 `16b69743…27cd8e`。過去記録として維持 |
| production 内の行番号参照 | `p3_b4_floor_artifact_issuer.py:760–762` | 訂正対象。現在の記述も参照先と一致しない |
| consumer 集合 pin | `test_s8b_oracle_manifest_contract.py:19–36,93–134` | verifier 呼出しや signature は消さないので維持 |
| schema alias AST pin | `test_s8b_oracle_artifacts.py:252–282` | 維持 |
| perf 述語／guard pin | `test_official_perf_closure.py:54,76,176–179,428–430` | 対象外の性能判定を維持するため更新不要 |
| subprocess inventory | `test_ccbench_spawn_sites.py:121–124` | C は subprocess call を消さないので更新不要 |
| 8c hash 世代契約 | `s8c_preregistration.py:1475–1484` | 冒頭追記で値不変。更新不要 |
| test node 名の記録 | `acceptance_duration_ledger.json:1500–1502`、関連 manifest node 群 | 改名・削除時の参照。新しい実測時間を捏造しない |

現 F の全体 hash `6f84ddaf…792dd5`、8c 文書の `556c4d27…25d30a` の literal 検索では hit はありませんでした。ただし、**それだけを根拠に pin なしとはしていません**。上記の regex・AST・行番号・独立 golden も確認しています。

撤去 identifier を含む過去の mutation ledger／段成果物も見つかっています。これらは過去の証跡であり更新対象ではありません。**過去 artifact 全件についての行番号 pin の完全列挙までは閉じていません。**

**7. 所有分割**

編集 path を素集合にする分割：

| 所有 | 編集 path |
|---|---|
| 実装子 1 | `s8b_oracle_manifest.py`、`s8b_verdict.py`、`test_s8b_oracle_manifest.py`、`s8b_v2_freeze_fixture.py` の説明 |
| 実装子 2 | `floor_pair_driver.py`、`test_floor_pair_driver.py`、`p3_b4_floor_artifact_issuer.py` の関連コメント。issuer test の変更が必要なら同じ子 |
| 親 | `docs/phase3-8c-preregistration.md`、採用理由の decision、insight、統合記録 |

`test_s8b_oracle_manifest_contract.py` と共有 spec fixture は、現計画では編集不要です。追加編集が必要になった場合は実装子 1 の所有とします。

## 未解決・親へ返す点

1. **A の全面撤去と brief の非代替部分を残す条件は、現状のままでは両立しません。** schedule 集合維持と floor 内部整合の撤去を分けて扱う必要があります。少なくとも `pairs` key 検査は残す候補です。
2. **C の helper 全削除は binary 束縛だけの削除ではありません。** strict receipt・trace 検査も落ち、issuer が受け取る record の前提が変わります。狭い削除は `F:1107–1115` です。
3. **oracle の過去 binary 束縛が別に残ります。** `s8b_oracle_driver.py:1058–1063`。本 wave の scope は広げませんが、完了報告の主張を限定する必要があります。
4. 中間状態の helper import 破損に対する全 test 関数名と、過去 insight の全行番号 pin の列挙は未完了です。静的調査だけで「閉包完了」とは報告しません。
5. 既存拒否述語の実測発火は親へ引き継ぎます。ここで報告した hash 不変確認は pytest の緑ではありません。

## 総括

**B(a) と 8c 冒頭追記は具体化できています。A/C は名指された helper に複数の検査が混在しており、全面削除を無条件に渡せる状態ではありません。** 上記の残存候補・間接 consumer を段 3 の主要争点としてください。