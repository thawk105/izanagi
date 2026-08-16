# レンズ B 所見

判定の読み方: `real` は攻撃成立、`refuted` は攻撃不成立。重大度は `blocker / high / medium / nit` で示す。

## 0. 読んだファイルと確認した行

確認した主な範囲:

- 親 brief、親実測ログ、段 2 プラン全体。
- `s8c_preregistration.py:38-65, 385-700, 1038-1493, 1594-1710`
- `s8c_preregistration_evidence.py:48-725`
- `s8c_preregistration_evidence_contract.v1.json` の C03、C08、C11。
- `test_s8c_preregistration_core.py`、`_predicates.py`、`_invariant.py`。
- `docs/decisions.md` の D96、D114、D410、D416-D418。
- `docs/spool/README.md:51-102`、`docs/dev-wave/operations.md:146-155`、`tools/dev_wave_land.py:2885-2903, 2217-2303`。
- `tools/check_docs.py`、`trial_registry.py`、8c runbook、`output/README.md`。

現在の freeze namespace には g1、g2 しかなく、g3 実体はまだない。HEAD は `10813338`。pytest は指示どおり実走していない。

**判定: real / 重大度: blocker / 成果物影響: certified 選択は保留。材料レポートには「g3 未生成、静的検査のみ」と記録し、試行台帳には新規試行を記録しない。**

## 1. g3 世代記録の field 別検証

以下は段 2 が設計した値を、`_record_document:1685-1710` と `validate_condition_freeze_at` に当てた静的判定である。実際の g3 bytes は未確認である。

1. `schema_version`

   `s8c-prereg-condition-freeze/v1` なら `_load_freeze_record:1038-1107` の exact schema 検査を通る。未知 key や欠落があれば `record-schema` 系で失敗する。

   **判定: refuted / 重大度: nit / 成果物影響: 正確な値を生成器から出す限り影響なし。**

2. `normalization_version`

   `s8c-prereg-markdown/v2` は現在の定数と一致する。別値なら履歴検査以前に拒否される。

   **判定: refuted / 重大度: nit / 成果物影響: g3生成時に定数から取得することを材料レポートへ記録。**

3. `generation_number`

   `3` は filename と record の双方で一致し、g1、g2、g3 が連続していれば `generation-gap` にはならない。現在は g3 ファイル自体がないため、現 tree は g2 のままである。

   **判定: real（未生成） / 重大度: blocker / 成果物影響: certified 選択を保留。**

4. `supersedes_sha256`

   g2 raw bytes の SHA-256 は次の値でなければならない。

   `d3c6a3dea39e8d05560091c1286f9a0b803e42b70512f7bf8cac009ed4244225`

   protected hash や g2 の protected 値を入れると `generation-supersedes` で失敗する。

   **判定: refuted（段 2 の値がそのまま使われる場合） / 重大度: high / 成果物影響: g2 raw bytes の hash を試行台帳へ固定記録する。**

5. `source_path`

   `docs/phase3-8c-preregistration.md` でなければならない。`SOURCE_PATH` と異なる値は記録と本文の対応を壊す。

   **判定: refuted / 重大度: high / 成果物影響: certified 選択への影響なし。ただし手入力禁止。**

6. `section5_field_names_sha256`

   §5 の field 名集合を算出した値であり、段 2 の設計では既存値の `4d082de6c6a19691dd8bad27127e9ebb03fdacc500aab555310c7883b7ba2635` を維持する想定である。§5 の値セルの変更はこの hash を変えないが、field 名、順序、重複は変える。

   **判定: refuted（§5 field 名を変えない場合） / 重大度: medium / 成果物影響: §5 値セルの変更だけで g3 を増やさないことを材料レポートに記録。**

7. `section6_conditions_sha256`

   §6 の条件 1-12 を正規化して再計算する。C03、C08、C11 の本文を変えるなら g2 と同値にはならない。

   **判定: refuted（最終本文から再計算する場合） / 重大度: blocker / 成果物影響: 手書き hash は禁止し、最終 doc bytes から生成した証拠を残す。**

8. `section6_condition_hashes`

   1 から 12 までの全要素が必要で、`_assert_record_matches_contract:1243-1256` が個別値も照合する。C03、C08、C11 だけ変更し、他の 9 条件は g2 と同値になる想定だが、1 要素でも古い値を残すと `record-protected-mismatch` になる。

   **判定: refuted（全 12 件を生成器で再計算する場合） / 重大度: blocker / 成果物影響: 材料レポートに 12 件の算出完了を記録。**

9. `normative_body_sha256`

   §1、§2、§3、§4、§6、§7 を含む。§6 の本文を変更するため、通常は g2 と異なる。§6 条件以外の説明文だけを変更しても変わる。

   **判定: refuted（最終本文から再計算する場合） / 重大度: blocker / 成果物影響: doc の最終編集後に g3 を作り直す必要がある。**

10. `evidence_contract_sha256`

    JSON の空白や key 順は意味 hash に影響しないが、`machine_checkable`、path、field path、proof、negative control の値変更は影響する。C03/C08 の path 追加と C11 の path 入替えにより、現行の `c4f374...b264471` から変わる。

    **判定: refuted（semantic canonical JSON を使う場合） / 重大度: blocker / 成果物影響: 旧 g1/g2 pin は変更せず、新 g3 のみ新 hash を持たせる。**

11. `protected_sha256`

    `evidence_contract_sha256`、`normative_body_sha256`、§5 field 名 hash、§6 aggregate hash の canonical preimage から算出される。g2 の値を流用すると `record-protected-mismatch` になる。

    **判定: refuted（`contract.protected_sha256(evidence_sha)` を使う場合） / 重大度: blocker / 成果物影響: certified 選択は最終 doc、契約、g3 の三者一致まで保留。**

12. `revision_reason`

    現行 validator は非空・trim 済みかしか検査しない。段 2 の T-1132/T-1133/T-1134 の理由文は構文上通るが、D96 の新 D を実際に含むか、C11 の変更を正当に説明するかは検査されない。

    **判定: real（意味検査の欠落） / 重大度: high / 成果物影響: 材料レポートに人手確認を必須化し、機械検査済みとは記録しない。**

13. `ruling_reference`

    `D96` は `_RULING_RE:55` の `D[1-9][0-9]*` に一致する。`docs/decisions.md:4269` の非 fence 見出し `## D96.` も `_assert_rulings_exist:1352-1374` に一致するため、機械的には通る。

    ただし、これは D96 が本改訂を authorize したことを意味しない。D96 は「新しい設計判断を起こせ」「境界テストを同じ変更単位で更新せよ」という手続であり、本改訂の内容を承認する D ではない。

    **判定: real / 重大度: blocker / 成果物影響: certified 選択を止め、材料レポートには「D96 は手続参照のみ」と記録する。**

履歴遷移も攻撃対象である。`_assert_history_transition:1265-1311` は g2 から g3 が一世代差で、protected state が変わった場合だけ通常 successor と認める。protected state が変わらなければ `spurious-revision`、同一世代の後続 commit で保護対象だけが変われば `unrecorded-protected-change` になる。g3 生成後に doc を一行でも直せば、現 tip で `record-protected-mismatch` になる。

**判定: real / 重大度: blocker / 成果物影響: g3 は最終 doc、契約 JSON、境界テストの確定後に一度だけ生成する。**

## 2. (P1) D 採番の順序衝突と第 4 の案

`D96` の構文受理は成立する。しかし、D96 を本改訂の authorization として使う攻撃は成立する。

- D96 は `docs/decisions.md:4275-4279` で、新しい D と境界テストの同時更新を要求している。
- 現行 validator は D の存在、見出し、導入 commit 時点での可視性しか確認しない。D の本文が本改訂を authorize するか、D96 と別の新 D が存在するかは見ない。
- D96 の primary target は `s8b_selector_output.py` とされている。今回の受理集合変更は主に s8c の証拠契約と evaluator であり、D96 の手続を適用するとしても、D96 自体が s8c の内容を許可したことにはならない。

既存 D の流用も成立しない。

- D114 `:5331-5333` は承認済み generation 上限を 1 としている。
- D410 `:17207-17208` は s8c C11 を `machine_checkable:false`、`EVIDENCE_UNDEFINED` のまま残し、sample-plan / cap-lift を作らないことを明記している。D410 は cap 引き上げの authority には使えない。
- D416-D418 は還流、field、正式起動形の設計判断であり、C11 を SATISFIED にする authorization ではない。

**P1**

- 機械検査: 通る。
- 手続の意味: 通らない。`ruling_reference` の意味が「手続参照」なのか「内容 authorization」なのか曖昧なまま、D96 を後者として扱っている。

**判定: real / 重大度: blocker / 成果物影響: certified 選択は不許可。新 D の内容と導入時点を材料レポートに残すまで試行台帳を進めない。**

**P1b: spool fragment を受理する案**

現在の spool は `docs/spool/README.md:51-63` により、新しい D 番号を fragment に書けず、`{{D:slug}}` だけを許す。番号は fold 時に割り当てられる。

未 fold fragment を `_assert_rulings_exist` の authority にすると、canonical `docs/decisions.md` ではないものを D として受理することになる。fragment、fold 後の D 番号、g3 導入 commit、land transaction を結び付ける新しい検査が必要であり、単なる regex 拡張ではない。

**判定: refuted（現行制度のままでは不採用） / 重大度: blocker / 成果物影響: 新しい裁定パッケージと land 検査の対象にする。**

**P1c: D だけ先行 land**

D-only の land 後に改訂 wave を land すれば、次 wave の g3 は既存 D を参照できる。しかし D96 は新 D と境界テストを同じ変更単位で更新するよう要求している。現行の wave 単位では二 wave に分割されるため、そのままでは要件を満たさない。

**判定: real / 重大度: high / 成果物影響: human ruling が「二 wave を同一変更単位とみなす」と明示しない限り、certified 選択から除外。**

**第 4 案: land lock 内で decision pre-fold してから g3 を確定する**

理論上は次の順序なら成立する。

1. land lock 内で decision fragment を fold し、新 D を canonical ledger に入れる。
2. その D を含む main を基底に wave を再構成・再検査する。
3. g3 の `ruling_reference` を新 D にして commit する。
4. ff-only land する。
5. 後続の通常 fold を行う。

しかし現行は `tools/dev_wave_land.py:2885-2903` で先に tested tip を ff-only land し、`_fold_main_locked:2217-2303` でその後に fold commit を作る。新 D は g3 の導入 commit に存在できない。land protocol と再検査単位を変更する別 wave が必要である。

**判定: refuted（現行 land で可能という主張は不成立） / 重大度: blocker / 成果物影響: land lock 手続変更を別の裁定パッケージとして返す。**

## 3. 受入で赤になる nodeid の独立列挙

段 2 の 13 項目は、予定どおり「C11 のみ SATISFIED」「C03/C08 に各 1 path 追加」「C11 は 2 path 削除・1 path 追加」を実装した場合の既存 pytest nodeid として網羅している。

赤になる nodeid:

- `orchestrator/tests/test_s8c_preregistration_core.py::test_contract_path_inventory_has_expected_count`
- `orchestrator/tests/test_s8c_preregistration_core.py::test_current_evidence_contract_hash_is_frozen`
- `orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_snapshot_has_zero_satisfied_predicates`
- `orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_gap_reason_snapshot_requires_cross_wave_review`
- `orchestrator/tests/test_s8c_preregistration_predicates.py::test_satisfiable_predicate_requires_negative_control`
- `...::test_noop_and_token_only_fixtures_never_satisfy[nc_c01_perf_scale_regression-C01]`
- `...::test_noop_and_token_only_fixtures_never_satisfy[nc_c04_partial_crash_survives-C04]`
- `...::test_noop_and_token_only_fixtures_never_satisfy[nc_c09_acceptance_skips_layer3-C09]`
- `...::test_noop_and_token_only_fixtures_never_satisfy[nc_c10_raw_response_unbound-C10]`
- `...::test_noop_and_token_only_fixtures_never_satisfy[nc_c11_generation_cap_reverts_to_one-C11]`
- `...::test_noop_and_token_only_fixtures_never_satisfy[nc_c12_resume_or_multi_process_allowed-C12]`
- `orchestrator/tests/test_s8c_preregistration_predicates.py::test_c11_prohibition_ruling_blob_alone_is_not_compliance`
- `orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_is_not_effective_and_has_zero_satisfied_predicates`

特に段 2 の更新方針には注意が要る。

- 現在の 6 negative control は契約が machine false なので、mutation 側も `EVIDENCE_UNDEFINED` になっている。machine true 後は C01/C04/C09/C10/C12 の mutation 側は具体的な `UNSATISFIED` reason に変わらなければならない。
- C11 の token-only fixture は新しい generation projection の不在を明示的に拒否しなければならない。単に artifact path を消すだけでは、token fixture が SATISFIED になるか、逆に判定不能のまま残る。
- `test_candidate_freeze_matches_contract_and_generation_chain` は、D96 が導入 commit に存在する限り追加の必然的な赤ではない。新 D を g3 から参照する実装に変えると `ruling-not-found` で赤になる。
- `test_record_schema_has_no_self_or_commit_hash_fields` と `test_effective_requires_all_twelve` は、P3 の binding fields を freeze record に入れず、C11 単独で effective にしない限り赤ではない。

pytest 外では、`tools/check_docs.py:4953-4969` が living docs 内の未知 D と不存在 path を検査する。land も `tools/dev_wave_land.py:2109` で docs checker を要求する。新しい binding path を living doc に書くのにファイルを同じ変更単位で追加しなければ、pytest の 13 nodeid 以外に docs acceptance が赤になる。

`docs/phase3-s8c-autonomous-trial-runbook.md` は living doc の glob 対象であり、現在も単一の `prereg_commit` を説明している。P3 の二つの識別子を実装するなら、ここを更新しないと意味的な受入漏れになる。`output/README.md` には現在 g2 の exact hash pin は見当たらないため、それ自体の必然的な赤は refuted。ただし binding artifact を追加するなら出力規約を追随させる必要がある。

**判定: real（pytest リストは網羅、周辺 acceptance は段 2 が未列挙） / 重大度: high / 成果物影響: 13 nodeid と docs-check、runbook、land acceptance を別々に試行台帳へ記録する。**

## 4. 凍結 hash を壊す経路

`normalization_version` は `s8c-prereg-markdown/v2` で、主な依存は次のとおり。

- 改行は CRLF/CR を LF に変換し、本文は NFC 正規化される。
- 連続空白、行折り返し、強調記法の一部は同じ canonical node になる。単なる見た目の折り返しでは hash が変わらない場合がある。
- 見出しの文言・階層、段落から list への変更、fence への変更は node kind を変え、`normative_body_sha256` が変わる。
- §6 の番号付き条件は空行とインデントで本文境界が変わる。継続行のインデントを落とすと、hash 変更だけでなく parse failure になる。
- §5 の値セルは protected preimage ではない。§5 field 名の変更だけが `section5_field_names_sha256` に入る。
- §6 の番号付き条件以外の説明文も `normative_body_sha256` に入るため、「条件本文を変えていない」という説明では保護を回避できない。
- evidence contract は semantic canonical JSON なので空白や key 順は吸収されるが、path、field path、machine flag、proof の変更は hash を変える。
- `protected_sha256` は evaluator module の hash を含まない。

したがって「doc は living なので自由に書ける」は誤りである。living は §5 の値セルを後で埋められるという意味であり、§6 の規範本文が凍結外という意味ではない。

**判定: real / 重大度: blocker / 成果物影響: g3 生成後の doc 修正は禁止し、修正時は新世代を作る。材料レポートに最終 bytes の hash 算出順を残す。**

## 5. 条件 3/8 の二段束縛の構成可能性

P3 は git の性質上、自己参照を避ける二 commit 形なら構成可能である。

1. 内容 commit `P` を作る。manifest bytes `M` を含めるが、`P` 自身や `C` の ID は manifest に入れない。
2. `P` の直接の子として binding-only commit `C` を作る。binding には `prereg_content_commit=P`、manifest path、`sha256(M)` を入れる。`C` 自身の ID は入れない。
3. ff-only land で main を `C` まで進める。
4. 実走開始・terminal report・receipt が `prereg_effective_commit=C` を記録する。
5. fold commit `F` は `C` の後続 commit になる。

`C` の親を `git rev-list --parents -n1 C` で検査し、親集合が `{P}` と完全一致することが必要である。main への ff-only merge や、その後の fold は `C` の親を変えないので、この要求とは両立する。

ただし次の理由で、現行実装へはまだ接続していない。

- `trial_registry.py:62-65, 497-560` は manifest、registry、binding の全てで単一の `prereg_commit` を要求している。
- `load_trial_manifest` と `derive_trial_binding` も単一 ID を前提にしている。
- P3 の fields を契約 JSON だけ変更しても、実際の launch、registry、terminal report は P/C を消費しない。
- `prereg_commit` を互換 alias として残すと、D75 の同名識別子の二義化が残る。旧 field を廃止するか、「manifest content」「effective」「measurement ancestor」を別名で完全に分ける必要がある。
- fold commit を C に流用する案は危険である。現行 fold は canonical ledger、worklog、receipt などを含むため、binding-only commit という P3 の tree 契約を満たさない。

構成可能な第 2 案は、P3 を「専用 binding commit 方式」として明文化することである。内容変更と g3 を含む P の直後に、binding JSON だけを持つ C を必ず追加し、fold は C の後で行う。単一 commit に manifest と自分を指す ID を同居させる方式は構成不能なので採用してはならない。

**判定: refuted（git 構成自体は可能）かつ real（現行 consumer 未配線） / 重大度: blocker / 成果物影響: C03/C08 は certified 選択に使わず、P/C consumer 実装を裁定パッケージへ返す。**

## 6. scope に入っていない層

| 層 | 現状 | 判定・重大度 | 成果物影響 |
|---|---|---|---|
| 契約 | JSON の machine flag、path、proof を変更 | refuted / medium | 契約 hash と g3 を更新 |
| evaluator | 6 evaluator は存在するが、`s8c_preregistration_evidence.py` は freeze scope 外 | real / blocker | evaluator bytes が g3 に固定されず、後続変更で同じ g3 の判定が変わる |
| 判定器 | activation は commit 上の core/evaluator を読み、全 12 条件 SATISFIED を要求 | refuted / high | C11 単独では effective にならないことを維持 |
| 実験起動 | p3 supervisor が `activation_report_at` や P/C binding を必須呼出ししていない | real / blocker | 新しい gate は起動前 gate にならず、実験を止められない |
| registry / 受入 | `trial_registry.py` は旧 `prereg_commit` 方式。C03/C08 は machine false | real / blocker | manifest と実走結果の P/C 一致を certified できない |
| Layer 3 / cross-binding / environment | C09/C10/C12 は本 wave 後も未充足または undefined | real / blocker | C11 を SATISFIED にしても正式系列は発効しない |
| land / fold | 新 D は ff-only 後の fold で初めて採番される | real / blocker | g3 から新 D を参照できない |
| docs acceptance | check_docs は未知 D と不存在 path を検査する | real / high | 新 binding path を本文に書くと同時追加が必要 |
| arm / external anchor | brief が scope 外と明記 | real / high | 6 cell の arm 同一性や外部 immutable anchor は certified 不可 |

特に evaluator module hash が freeze record にない点は、freeze 履歴の防衛として見逃せない。activation report に evaluator hash は載るが、g3 の protected state には入らない。条件の受理集合を変える evaluator 改修を、g3 の新世代なしで行える経路が残る。

**判定: real / 重大度: blocker / 成果物影響: certified 選択は「C11 の静的判定が追加された」とだけ記録し、正式 gate 実装完了とは記録しない。未実装層は裁定パッケージへ返す。**

## 7. 親の実測とプランの誤り

- **M1** は現状確認として real。12 条件が machine false、6 evaluator が未到達という確認は正しい。ただしこれは現状の dispatch であり、g3 後の受理集合を正当化しない。  
  **影響:** 材料レポートの baseline として採用、certified 選択の根拠にはしない。

- **M2** は private evaluator を強制発火した診断として real。ただし `_ConditionProbe` の結果は現行コードの結果であり、新しい generation projection evaluator の正しさを測っていない。「machine true にしても受理集合が広がらない」という一般化は、C11 改訂後には無効である。  
  **影響:** 現行差分の診断材料に限定し、P2 の positive evidence としては不採用。

- **M3** は現行 6 evaluator の終端構造として real。しかし終端が `EVIDENCE_UNDEFINED` であることは、将来の C11 が SATISFIED にならない根拠ではない。  
  **影響:** 旧 g2 の状態説明には使うが、g3 authorization には使わない。

- **M4** は機構の存在確認として real。ただし `MAX_APPROVED_GENERATIONS=2` は D114 の承認上限 1 と衝突し、D410 も C11 を未充足のまま残している。artifact 検査を外すだけなら旧 evaluator は SATISFIED ではなく終端 undefined に到達するだけである。  
  **影響:** C11 SATISFIED の根拠から外し、新 D と閉じた projection proof を要求する。

- **M5** の D410 が g2 導入前に存在したという履歴測定は real。誤りは、同じ方法で D96 を引けば本改訂も authorize できると扱う点である。D96 は新 D を要求している。  
  **影響:** land 順序 blocker として試行台帳へ記録。

- **M6** の既存境界テストの特定は real。ただし D96 の新 D 内容、D96 と authorization D の分離、g3 導入 commit での D 可視性を検査するテストがない。  
  **影響:** 既存 13 nodeid の更新に加え、land-order negative control を追加要求。

- **M7** は exact pin の検索として不十分。`tools/check_docs.py` の動的 D/path 検査、runbook の旧 `prereg_commit`、land/fold の採番順、evaluator/core bytes の freeze 非拘束を pin 閉包に含めていない。  
  **影響:** 「pin 閉包済み」という結論は refuted。材料レポートの scope closure を撤回。

- **M8** の 4 wave と編集面重複ゼロは real だが、land lock、spool fold、docs lint、trial registry との非衝突を証明しない。  
  **影響:** 競合回避の補助材料に限定し、受入可能性の証明にはしない。

## 8. must-fix / nit の仕分け

### must-fix

1. D96 と別に、本改訂を authorize する新 D を起こす。C11 の cap、projection、C03/C08 の P/C 分離、却下案を本文に書く。新 D が g3 導入 commit に存在しない現行 land 順序も同時に解く。

   **判定: real / 重大度: blocker / 成果物影響: certified 選択、材料レポート、試行台帳を全て保留。**

2. C11 は D114、D410 と整合する authorization と、closed projection の実証が揃うまで SATISFIED にしない。token-only、call bypass、projection key 改変、validator 順序改変の負例を追加する。

   **判定: real / 重大度: blocker / 成果物影響: C11 の positive claim を材料レポートへ書かない。**

3. evaluator/core の bytes を freeze にどう束縛するか決める。少なくとも、g3 と同じ変更単位での D96 boundary test、commit blob hash、後続変更時の新世代要求を明文化する。

   **判定: real / 重大度: high / 成果物影響: freeze history の certified claim を保留。**

4. P/C を `trial_registry.py`、p3 launch、terminal report、receipt、acceptance まで配線し、単一の `prereg_commit` alias を残さない。

   **判定: real / 重大度: blocker / 成果物影響: C03/C08 を certified 選択から除外。**

5. 最終 doc、contract JSON、境界テスト、g3 の全 bytes を確定してから g3 を生成する。g1/g2 の pin は変更しない。

   **判定: real / 重大度: blocker / 成果物影響: g3 raw bytes、protected hash、generation chain を材料レポートと試行台帳へ固定。**

6. `tools/check_docs.py`、runbook、output path、land/fold 手順を受入面に含める。新 D を g3 で参照するなら、現行 fold 後採番との矛盾を解決する。

   **判定: real / 重大度: high / 成果物影響: docs acceptance が緑になるまで certified 選択を禁止。**

### nit

- `ruling_reference` は authorization と procedure の意味を分け、必要なら `procedure_reference=D96` と `authorization_reference=<新D>` を別 field にする。
- `revision_reason` は現在非空検査だけなので、D96 と新 D の関係を人手確認する記録欄を設ける。
- path inventory の 38 から 39 への更新は機械的だが、hard-code 更新だけでなく C03/C08/C11 の個別 path 検査を追加する。
- `output/README.md` の現行 exact pin 不在は問題ではないが、新 binding artifact を追加するなら出力規約を明記する。

## 総括

D96 は構文上 g3 の `ruling_reference` として受理されるが、本改訂の authorization ではない。  
現行 land は ff-only 後に fold するため、新 D を g3 導入 commit で参照できない。  
P3 の P→C 二 commit 自体は構成可能だが、registry・起動・受入は未配線である。  
段 2 の pytest 13 nodeid はほぼ網羅しているが、docs lint、runbook、land 順序を落としている。  
従って現時点の選択は certified 不可、材料レポートは blocker として返却、試行台帳は停止である。