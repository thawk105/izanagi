## 1. 前提の裏取り

- N1 は支持する。`rg -l -g '*.json' '"schema"... "floor-pair-spec/v3"' .` は 0 件だった。insights 内には失敗ログ中の `FloorPairSpec(schema='floor-pair-spec/v3', ...)` があるが、spec instance ではない。insights を除く literal は [floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2423-floor-protocol-identity/orchestrator/campaign/floor_pair_driver.py:56) と [test_floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2423-floor-protocol-identity/orchestrator/tests/test_floor_pair_driver.py:484) の 2 箇所だけである。
- N2 は支持する。portable record は `PORTABLE_BUILT_KEYS`、receipt は `_RECEIPT_KEYS`、subject は `_SUBJECT_KEYS`、binding は `_BINDING_KEYS` の exact 集合で、protocol はない（`s8b_binary_admission.py:41-69`）。record と receipt は `validate_portable_binary_record` が exact key 一致を要求する（同 `309-319`）。driver はこの実 validator を呼ぶ（`floor_pair_driver.py:1052-1080`）。したがって issuer の現行 receipt 探索（`p3_b4_floor_artifact_issuer.py:755-781`）は production receipt では成功しない。
- N5 は字義どおりには反証する。`spec.schema` は成果物へ直接書かれず、HMAC 入力に使われる（`floor_pair_driver.py:1302,1316,1328`）。plan に書かれる schema は `PLAN_SCHEMA`（`1405-1419,3047-3055`）、window は `WINDOW_SCHEMA`（`2190-2198,2643-2651`）、summary は `SUMMARY_SCHEMA`（`3004-3010`）である。ただし `spec.schema` と `spec.spec_sha256` が plan 順序を変え、その sessions と plan hash が window／summary へ伝播するため、「v4 化で downstream bytes が変わりうる」という結論は正しい。
- 特に `test_mutation_11_hmac_rank_has_multiple_pair_sample_golden_order`（`test_floor_pair_driver.py:1072-1112`）は順序を hard-code しており、brief §4 から漏れている。

## 2. (P1)〜(P5) の裁定案

- P1 は支持する。(a) を採る。D1641 は成果物名に protocol を要求し、既存 between-run 命名も protocol を独立した識別子として扱う（`between_run_floor.py:196-207`）。4 要素へ減らすと、将来別 protocol の同一動作点を区別できない。
- P2 は支持する。top-level `protocol` が適切である。

  - `environment` は site、env_tag、clock、NUMA、timeout 等の実行環境である（`floor_pair_driver.py:653-697`）。
  - `artifacts[*]` は binary と receipt の artifact ごとの束縛である（`700-733`）。ここへ置くと複数 artifact 間の一致検査が必要になる。
  - protocol は spec 全体の測定対象に 1 値なので top-level とし、`_identifier` の canonical ID 検査だけを課す（`90-92,426-436`）。

- P3 は支持し、`floor-pair-spec/v4` へ進める。instance が 0 件でも、exact key 受理集合の変更を同じ v3 名で行うべきではない。live literal 閉包は定数と literal test の 2 箇所だけで、consumer 改修範囲も小さい。旧 v3 は fail-closed で拒否する test へ更新する。PLAN／WINDOW／SUMMARY と issuer の `floor-pair-summary/v3` pin は変えない。
- P4 は「`spec.protocol` を使う」は支持するが、brief の「threads 不一致・campaign 空は起こりうる」は反証する。成功した loader 出力では identity 欠落分岐はすべて到達不能である。詳細は §4 のとおり。
- P5 は支持する。`_identifier` を超える allowlist、CCBench source 束縛、artifact 間一致 validator は追加しない。D1696 の人手責任を維持する。

## 3. 編集面のアンカー表

| file:line（現行） | 関数・面 | 計画 | 差分行見込み |
|---|---|---|---:|
| `floor_pair_driver.py:56` | `SPEC_SCHEMA` | v3 から v4 | 2 |
| 同 `263-278` | `FloorPairSpec` | `outputs` 後へ `protocol: str` | 1 |
| 同 `1194-1214` | `load_frozen_spec` | exact top-level 集合へ key を追加し、schema 検査後に `_identifier(top["protocol"])` | 2 |
| 同 `1240-1256` | constructor | `protocol=protocol` | 1 |
| `p3_b4_floor_artifact_issuer.py:736-804` | `_derive_identity` | `root` と receipt 探索を削除し `spec.protocol` を使用。到達不能な missing 分岐も除去 | 35〜45 |
| 同 `818-827,860` | `load_floor_pair_summary` | `_derive_identity` 呼出しと、missing が通常返るという docstring を修正 | 5〜8 |
| 同 `890-895` | `_authority_value` | `"summary-bound spec/receipt"` を `"summary-bound spec"` へ修正 | 2 |
| `test_floor_pair_driver.py:185-298` | `_valid_document` | top-level `"protocol": "silo"` | 1 |
| 同 `483-505` | schema tests | literal を v4、旧 v3 拒否へ更新 | 4〜6 |
| 同 `517-575` | `REQUIRED_FIELD_PATHS` | `("protocol",)` を追加 | 1 |
| 同 `662-680` | nested placement test | cell 内 protocol が unknown のままであることを維持 | 0〜2 |
| 同 `1072-1112` | HMAC golden | v4＋protocol を含む spec hash に対応した固定順序へ更新 | 12〜18 |
| 同、schema test 近傍 | protocol tests | parsed field と 3 種の非 canonical 値を追加 | 18〜25 |
| `test_p3_b4_floor_artifact_issuer.py:40-92` | `_synthetic_source` | `receipt_has_protocol` と validator monkeypatch を削除。spec protocol は識別しやすい `"mocc"` | 30〜35 |
| 同 `217-250` | real finalizer test | missing protocol 期待から、spec protocol で発行成功する正例へ | 12〜18 |
| 同 `473-594` | identity／発行／filename tests | missing spec の producer 拒否、内部 guard、filename と authority JSON の一致を検査 | 30〜40 |
| 同 `618-679` | resolver tests | obsolete な `receipt_has_protocol=True` を除去 | 8〜12 |
| `acceptance_duration_ledger.json` | 台帳 | 編集不要 | 0 |

不変面は `floor_pair_driver.py:1052-1080` の `_validate_build_receipt`、`s8b_binary_admission.py` の strict receipt 検証、PLAN／WINDOW／SUMMARY schema、issuer の summary pin である。

brief §4 の誤り・漏れは次のとおり。

- issuer module docstring `7-10` に receipt 言及はないため変更不要。
- 実際に修正が必要な docstring は `load_floor_pair_summary:823-827`。
- `REQUIRED_FIELD_PATHS`、旧 v3 拒否 test、cell 内 protocol 拒否 test、HMAC golden order が漏れている。
- issuer の全 `receipt_has_protocol` 呼出しが列挙されていない。
- acceptance ledger は必須編集面ではない。
- 総差分は追加＋削除で約 160〜180 行。brief の「150 行以下」は HMAC golden と負例再設計を数えておらず、やや小さい。

## 4. issuer の `_derive_identity` の新しい形

概形は次とする。

```python
def _derive_identity(spec, campaign_ids):
    env_tag = spec.environment.env_tag
    protocol = spec.protocol
    threads_values = {cell.perf_config.threads for cell in spec.cells}
    workloads = {cell.perf_config.workload for cell in spec.cells}
    workload_values = tuple(sorted(workloads))
    workload_identifier = _aggregate_identifier(
        "set", [dict(items) for items in workload_values]
    )
    campaign_identifier = (
        campaign_ids[0]
        if len(campaign_ids) == 1
        else _aggregate_identifier("set", list(campaign_ids))
    )
    return B4FloorArtifactIdentity(
        env_tag=env_tag,
        protocol=protocol,
        threads=next(iter(threads_values)),
        workload_identifier=workload_identifier,
        campaign_identifier=campaign_identifier,
    ), (), workload_values
```

各 missing 分岐の到達性は次のとおり。

- `threads`: 到達不能。cells は non-empty（`floor_pair_driver.py:759-776`）で、全 cell の threads は同じ単一 calibration の threads と一致しなければ loader が拒否する（`1136-1143`）。異なる threads が 2 値あれば少なくとも一方が先に拒否される。
- `workload_identifier`: 到達不能。cells が non-empty で、各 workload は exact 3 key から tuple 化される（`736-750,759-776`）。さらに全 cell は calibration workload と一致する必要がある（`1146-1147`）。
- `campaign_identifier`: 到達不能。summary campaigns は `allow_empty=False`（issuer `411-413`）で、各 campaign ID も canonical ID として追加される（`430-433`）。
- `protocol`: 新 loader の exact top-level key と `_identifier` が先に保証するため到達不能。

従って `_derive_identity` 内の missing 集積分岐は「producer loader と summary validator が恒真に保証する条件」として削除する。一方、`B4FloorIdentityError`、`missing_identity_elements` field、`_authority_value:891-895` の fail-closed guard は内部状態破損への最終防壁として残し、直接 test する。

receipt という語の削除対象は `_derive_identity:755-781` と `_authority_value:894`、test fixture の `56-84` である。production docstring に receipt はなく、module docstring の変更は不要である。

## 5. 正例・負例の設計

変更・追加する nodeid は次のとおり。

- `test_all_four_semantic_schema_identifiers_are_bumped`
  - `SPEC_SCHEMA == "floor-pair-spec/v4"`、他 3 schema が不変であることを pin。
- `test_loader_rejects_v3_schema_on_v4_shaped_spec`
  - 現行 `test_loader_rejects_v2_schema_on_v3_shaped_spec` を改名し、直前版 v3 を拒否。schema 検査の削除や v3 据置きを殺す。
- `test_every_schema_field_is_required[protocol]`
  - REQUIRED_FIELD_PATHS に追加。protocol 欠落が exact key 不一致になることを殺す。
- 新規 `test_protocol_is_loaded_from_top_level_and_requires_canonical_id`
  - 正例で `parsed.protocol == "silo"`。同一 node 内で `""`、`"silo protocol"`、`"a" * 129` を個別に load し、いずれも `FloorPairSpecError` かつ `protocol` を含む理由で拒否。calibration へ到達したら失敗させ、schema 層への帰属を固定する。
- `test_removed_claim_only_schema_fields_are_rejected_as_unknown[protocol]`
  - 現行どおり `cells[0]["protocol"]` を unknown として拒否し、top-level 以外の配置を殺す。
- `test_mutation_11_hmac_rank_has_multiple_pair_sample_golden_order`
  - 新 spec bytes に対する session と measurement role の golden を固定し直す。
- 改名 `test_real_finalize_floor_summary_is_accepted_with_spec_protocol_identity`
  - 実 `finalize_floor` 出力を issuer が受理し、identity が非 null、`protocol == spec.protocol`、missing が空、発行が成功することを検査。
- 改名 `test_identity_is_not_a_caller_surface_and_missing_protocol_spec_is_rejected_by_producer`
  - caller 引数に identity がないことを維持。spec から protocol を削除し、その新 hash を summary に反映して `spec_hash_mismatch` を回避した上で、`issue_authoritative_floor` が `code == "spec_rejected_by_producer"`、cause が `FloorPairSpecError`、detail が `missing=['protocol']` であることを検査。
  - 同じ node 内で、受理済み summary を `identity=None, missing_identity_elements=("protocol",)` に置換し、`_authority_value` が `B4FloorIdentityError` を返すことも pin する。
- `test_authority_issue_is_create_only_exact_and_loadable`
  - fake receipt を使わず発行・再読込に成功し、authority JSON の `artifact_identity.protocol == "mocc"` を確認。
- `test_authority_filename_contains_all_five_derived_components`
  - `__protocol-mocc` と `authority.artifact_identity.protocol == spec["protocol"] == "mocc"` を同時に確認。env_tag は `"synthetic-env"` として source 取り違えも殺す。

`receipt_has_protocol`／validator monkeypatch 撤去による test 影響は次の全件である。

- 旧 nodeid が消えて改名される:
  - `test_real_finalize_floor_summary_is_accepted_before_missing_protocol_blocks_issue`
  - `test_identity_is_not_a_caller_surface_and_missing_protocol_is_named`
- call と期待値を書き換える:
  - `test_authority_issue_is_create_only_exact_and_loadable`
  - `test_authority_non_guarantees_pin_required_verbatim_limitations`
  - `test_authority_filename_contains_all_five_derived_components`
  - `test_resolver_returns_exact_fraction_from_valid_pin`
  - `test_m05_m06_resolver_fails_closed_without_absence_fallback[missing]`
  - 同 `[hash]`
  - 同 `[schema]`
- test 自体の無条件削除はない。receipt protocol を作る fixture 分岐だけを削除する。

## 6. pin 閉包の裏取り

`floor-pair-spec/v3` の live literal は次の 2 件だけで、両方変更が必要である。

- `orchestrator/campaign/floor_pair_driver.py:56`
- `orchestrator/tests/test_floor_pair_driver.py:484`

insights の mutation log と archive worklog 内の過去記録は変更しない。

`FloorPairSpec(` の構築は `floor_pair_driver.py:1240` の 1 件だけ。`test_all_floor_pair_dataclass_fields_have_no_defaults`（test `451-456`）は class を走査するが field 名の exact 集合は pin していない。新 field に default を付けないことで通る。

`load_frozen_spec` の production 呼出しは次の 2 件。

- driver CLI: `floor_pair_driver.py:3072`
- issuer: `p3_b4_floor_artifact_issuer.py:847`

test 呼出しは `test_floor_pair_driver.py:389,418,503,598,619,640,657,678,691,700,732,764,797,811,814,856,884,902,921,978,990,1008,1023,1040,1054,1085,1398,1937,2122` と issuer test `261`。大半は `_valid_document` を共有するため個別修正不要である。

spec top-level key を列挙・pin する面は次のとおり。

- loader exact 集合: `floor_pair_driver.py:1194-1201`、変更必要。
- 正例 document: `test_floor_pair_driver.py:185-298`、変更必要。
- required path 集合: 同 `517-575`、変更必要。
- unknown top-level key: 同 `645-659`、変更不要。
- cell 内 protocol unknown: 同 `662-680`、維持する。

全 test 定義の grep は 75 件だった。identity 変更と直接関係する pin は上記に加え schema 由来の HMAC golden `1072` だけであり、その他 69 件は共有 fixture 経由で追随する。

docs の grep 結果は、`docs/decisions.md` の D1696／D1759／D1774、`docs/phase3-b4-reflux-ablation-preregistration.md:1092-1101` の driver 実在記述、worklog／archive の T-2423 履歴、一般的な frozen spec 記述だった。`floor-pair-spec/v3` literal や現行 top-level key 表は docs にない。決定ログ・archive・事前登録本文はいずれも変更不要かつ scope 外であり、docs 編集は計画しない。

acceptance ledger は追加不要と確定する。

- 未登録 nodeid は `_acceptance_duration_for_item` が `None` を返す（`conftest.py:1534-1554`）。
- reorder はそれを error にせず既知 duration 由来の既定 cost を与える（`1594-1627`）。
- exact completeness gate はなく、別 test が collection 全体の 90% 被覆だけを要求する（`test_acceptance_schedule_order.py:704-714`）。
- ledger は現在 19,745 nodeid。数件の新 nodeidを追加しないこと自体で受入が赤になる契約ではない。`--add-only` は未登録値を追加する運用面であり（`update_acceptance_duration_ledger.py:83-94,413-441`）、本変更の必須成果物ではない。

## 7. t2412 との衝突面

指定 diff の stat は次のとおりだった。

```text
floor_pair_driver.py                 99
acceptance_duration_ledger.json     225
test_ccbench_spawn_sites.py           5
test_floor_pair_driver.py           310
test_p3_b4_floor_artifact_issuer.py   8
合計 579 insertions, 68 deletions
```

hunk の現行側開始行は以下。

- `floor_pair_driver.py`: `19,83,535,578,591,1083,1100,1152,1163,1187,1227,2173,2647`
- `test_floor_pair_driver.py`: `12,23,306,320,362,369,421,469,695,718,734,993,2000,2011`
- `test_p3_b4_floor_artifact_issuer.py`: `106,507`

本 wave の主要 anchor は driver `56,263-278,1194-1214,1240-1256`、driver test `185-298,483-505,517-575,662-680,1072-1112`、issuer test `40-92,217-250,473-594,618-679`。

衝突リスクと回避案は次のとおり。

- driver の t2412 hunk `-1187,9` は 1195 で終わり、本 wave の loader anchor が 1194 から始まる。ただし本 wave の実変更は top set の旧 1198 後への新行挿入と、schema check 後の protocol parse に限定する。t2412 が変える `_git_show_head` 呼出し／文言の行には触れない。
- t2412 hunk `-1227,15` は constructor 冒頭まで文脈を含む。本 wave の constructor 変更は旧 `outputs=outputs` の後、1251 後だけに置く。間に複数の未変更行を残す。
- issuer test の本 wave の `receipt_has_protocol=True` 削除は旧 505、本体 hunkは 507。旧 506 を未変更で残し、t2412 が 507-512 に追加する loaded-head assertion は触らない。新 protocol assertion は authority JSON を読む旧 537 後へ置く。
- driver test の schema literal 484 と t2412 の 469 hunkの間には旧 478-483 が残る。新 protocol test は schema test 後か旧 680 後に置き、t2412 の 695 hunkに隣接させない。
- brief N6 の「issuer line 66」変更は指定 branch diff では確認できなかった。確認できた issuer hunk は 106 と 507 のみ。

実装開始前に t2412 の main 着地を確認して新しい行番号を取り直す。未着地の同一 base へ並行実装する場合も、上記 exact insertion point を守る。

## 8. 変異候補の事前登録案

| ID | 対象（実装後見込み） | 変異 | 殺す test nodeid |
|---|---|---|---|
| M1 | `floor_pair_driver.py:56` | `SPEC_SCHEMA` を v3 に戻す | `test_all_four_semantic_schema_identifiers_are_bumped` |
| M2 | 同 `1200` | expected top-level 集合から protocol を落とす | `test_protocol_is_loaded_from_top_level_and_requires_canonical_id` |
| M3 | 同 `1206` | `_identifier` を `_exact_text` に変える | 同上。空白入りと129文字が殺す |
| M4 | 同 `1203-1206` | schema equality check を削除・緩和する | `test_loader_rejects_v3_schema_on_v4_shaped_spec` |
| M5 | 同 `1255` | `protocol=protocol` を `protocol=environment.env_tag` にする | `test_protocol_is_loaded_from_top_level_and_requires_canonical_id` |
| M6 | issuer `750` 前後 | `spec.protocol` を `spec.environment.env_tag` にする | `test_authority_filename_contains_all_five_derived_components` |
| M7 | 同 | `spec.protocol` を `"silo"` に固定する | 同上。fixture の `"mocc"` が殺す |
| M8 | 同 `750-775` | spec 参照を旧 receipt 探索へ戻す | `test_real_finalize_floor_summary_is_accepted_with_spec_protocol_identity` |
| M9 | issuer `_identity_value:850` 前後 | JSON protocol を別 field にする、または key を落とす | `test_authority_issue_is_create_only_exact_and_loadable` |
| M10 | issuer `_artifact_filename:890` 前後 | `__protocol-...` segment を落とす | `test_authority_filename_contains_all_five_derived_components` |
| M11 | issuer `_authority_value:860` 前後 | incomplete identity guard を削除する | `test_identity_is_not_a_caller_surface_and_missing_protocol_spec_is_rejected_by_producer` |

除外する冗長候補:

- 親 M6「protocol 欠落時に issuer が silo を推測」は loader の exact key 検査が先に拒否するため、issuer 分岐へ到達せず帰属不成立。
- threads／workload／campaign の missing 分岐に対する変異は §4 の upstream 保証で到達不能。
- issuer 側で protocol の canonical 性を緩める変異も loader が先に拒否するため帰属不成立。
- `.get(..., "silo")` 型の fallback は exact key 検査に加え `test_module_source_has_no_frozen_fallback_or_publish_bypass:3091-3100` にも先に拒否される。

## 9. 事前予測

これは静的予測であり、pytest は実行していない。

- 焦点走では、HMAC golden を更新する前の `test_mutation_11_hmac_rank_has_multiple_pair_sample_golden_order` が最も確実に赤になる。schema と spec hash が双方変わるためである。
- 旧 schema test、旧 missing-protocol 期待、`receipt_has_protocol` keyword を残した test は確実に赤になる。
- issuer の自走 harness `697-703` はファイル全体を pytest collection するだけなので一覧更新は不要。fixture monkeypatch 撤去後も追加 node を自動収集する。
- `test_ccbench_spawn_sites.py` は本 wave が subprocess spawn site を増減しないため、本 wave 単独では変更不要。t2412 が同 file を変更するので着地後の値を正本とする。
- acceptance 全走では新 nodeid が未知 duration 扱いになるが、それ自体は失敗ではない。唯一の可能性は集約 90% coverage gate が境界を割る場合だが、数件追加だけで割る可能性は低く、ledger は事前編集しない。
- `tools/check_docs.py` に floor-pair schema literal／source同期規則は見つからず、docs 無変更による赤は予測しない。履歴 docs は更新対象外である。
- schema v4 によって plan/window/summary の schema ID 自体が変わる赤は予測しない。ただし plan順序、plan hash、spec hash に依存する hard-coded bytes が他にあれば受入全走で検出される。

## 総括

- 採る方向: top-level canonical `protocol` を持つ `floor-pair-spec/v4`、issuer は `spec.protocol` のみを使用。
- 編集面: production 2 file＋test 2 file、追加＋削除で約160〜180行。receipt、台帳、docs は変更しない。
- 最大の不確実点: v4＋spec hash変更後の HMAC golden と、t2412 着地後の loader周辺行位置。
- 裁定パッケージ候補: protocol allowlist／source束縛のみ。ただし D1696再訪条件未成立のため本 waveでは提案・実装しない。