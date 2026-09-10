# 段 2 実装プラン

結論として scope 5 点は反映可能。ただし、(P3) の `owner` literal 案は機械的な段 5 除外にならないため採らず、gate ID で対象段を固定する。

## provisional 裁定への見解

- **(P1) 条件付き賛成。** §7.5 に namespace と exact schema を定める。ただし下位 revocation schema と同型の 7-key record、人間による明示 commit、live tip 失効時の fail-closed だけに限定する。cancellation は本 wave で定義しない。代案は policy と schema を別 gate に分離することだが、段 0 の schema 確定目的に反するため不採用。
- **(P2) 賛成。** `docs/calibration-freeze-authority-bundle-design.md:638-639` では段 6 が段 5 に依存している。段 5 だけの除外を段 6 へ暗黙拡張せず、`CFAB-STAGE6-COMPLETION-PREDICATE` を `owner=user,status=unresolved` で追加する。
- **(P3) 反対。** `calibration_freeze_authority_contract.py:401-402` は `owner` を非空文字列としてしか検査せず、`:747-755` の status 算出も owner を読まない。代わりに gate ID を `CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT` とし、3-key schema を維持する。
- **(P4) 賛成。** activation window は §7.2 の下位承認参照規則だけに置く。選ばれなかった発効後 lease や 19 consumer の use-time 再検査は書かない。

## 規則ごとの一意な正本

| 裁定 | 規範の正本 | 他節の役割 |
|---|---|---|
| U-A1 activation window | §7.2 `CFAB-7.2-01` | §8.1 は selection literal、§12 は索引のみ |
| rollback = forward compensation | §5.1 | §12 は索引のみ |
| revocation = no fallback / fail-closed | §7.5 | §1 は precedence から §7.5 へ dispatch |
| 下位 X_f は上位 X の後 | §5.2 | §5.1・§9.1・§12 は参照のみ |
| 段 5 fixture 除外 | §10 冒頭の fixture 閉包 | §12 は裁定索引のみ |

## docs 面

### 前文・§1

- `docs/calibration-freeze-authority-bundle-design.md:13`
  - 現行逐語: `**Q3 のうち lockstep 部分のみ**`
  - 置換後: 2026-08-11 裁定も反映済みとし、具体的な selection は §12 を参照させる。
- `:16-18`
  - 現行逐語: `**決まっていないこと:** §12 が正本である。ユーザー裁定待ちが 3 束`
  - 置換後: 4 ID と §8/§10 矛盾は裁定済み、残るユーザー gate は段 6 predicate、先送り S/G/B と他者手番 2 件は継続、と更新する。
- `:21`
  - 現行逐語: `**段 0 は \`incomplete\` である。** 上記が閉じるまで完了と宣言しない (§10)。`
  - 置換後: `incomplete` は維持し、理由の正本を §10.2 の機械算出へ一本化する。
- `:40`
  - 現行逐語: `毎回両方が交代することを含意しない — §12 Q3`
  - 置換後: stale な但し書きを削除し、lockstep の正本 §5 を参照する。
- `:52-54`
  - 現行逐語: `解決できない HEAD ... では、docs/freeze-permanent-design.md の記述がそのまま現行契約である。`
  - 置換後: 「上位 X が一度も成立していない HEAD」だけ下位 authority を使う。上位発効後の revocation は通常の未解決と区別し、§7.5 の terminal fail-closed state として扱う。壊れた record の存在だけでは precedence を切り替えない。

### §5 / §5.1 rollback

- `:174-181`
  - 現行逐語: `交代しなかった成分は、親束の同名成分と byte 一致することを要求する。` および `rollback ... は §12 Q3 の裁定に属し、本書は定めない。`
  - 置換後: lockstep 後は据置成分分岐を削除し、詳細を §5.1 に集約する。
- `:208-213` の lockstep 再計算 bullet の直後へ追加:
  - 祖先世代の参照へ戻す操作を rollback として受理しない。
  - 補償は、環境成分・凍結成分・上位束をすべて新しい世代番号で前進させ、E / G_f / A_f / Q / A / X の新しい列を作る。
  - 過去の approval や pointer を現行 tip として再利用しない。
- `:214-215`
  - 現行逐語: `下位 X_f ... をいつ置くかは未裁定である (§12 Q3)。`
  - 置換後: 時点を重複記載せず「§5.2 に従う」とだけ書く。

### §5.2 下位 X_f

- `:219-222`
  - 現行逐語: `したがって下位 X_f は段 3 の後にしか置けない。`
  - 置換後: この節を唯一の正本として、下位 X_f は段 3 consumer 移行完了後、かつ上位 X の strict descendant となる別 commit に置く。同一 commit・上位 X より前を拒否する。
- `:224-225`
  - 現行逐語: `E の健全性は環境候補 record の置き場の裁定 (§12 Q1) に依存する。`
  - 置換後: Q1 は確定済みなので、§6.1 の外部候補 namespace により健全性を保つ、と現在形へ直す。

### §7.2 U-A1

- `:312` の `CFAB-7.2-01`
  - 現行逐語: `上位束が参照できる凍結成分は人間承認を経た束 (approved-inactive 以上) に限り`
  - 置換後: 下位検証器による承認確認に加え、A_f から X_f までだけ expiry を検査し、X_f 後は expiry を理由に失効させない、と規定する。
  - 破る実装欄へ「X_f 後も lease を再検査する」「A_f→X_f 間の期限を検査しない」を追加。
  - 検査段は既存どおり段 4。row ID は変えないため `row_ids_sha256` と case pin は不変。

### §7.5 revocation

- `:391-401` の namespace 一覧へ `revocations/` を追加。
- `:403`
  - 現行逐語: `file 名は原則としてその record 自身の raw sha256`
  - 置換後: revocation だけ `revocations/<bundle_digest>.json` を例外として明記する。
- `:437-438`
  - 現行逐語: `revocation / cancellation record の namespace と schema は §12 Q3 (ii) の裁定待ちであり、本書は定めない。`
  - 置換後: revocation を exact 7 key で確定する。

Exact schema 案:

- `schema_version = "calibration-freeze-authority-revocation/v1"`
- `bundle_digest`
- `approval_raw_sha256`
- `revoked_by`
- `revoked_at` — exact int の UTC 秒
- `scope = "calibration-freeze-authority-bundle"`
- `reason`

さらに、bundle 当たり 0/1 件、対象は一度上位 X された束、1-file add・非 merge・逐語 `AI-Agent: none`・履歴不変を要求する。live tip に有効な revocation があれば resolver は authority 無しとして fail-closed にし、下位 authority を呼ばない。不正・重複 revocation は無視せず拒否する。cancellation は未定義のまま受理しない。

### §8 / §8.1

- §8 `:444-466` は変更しない。S/G/B の先送りと applicability の正本であり、段 5 除外をここへ重複記載しない。
- §8.1 `:482-489` を次へ更新する。

| ID | status | selection |
|---|---|---|
| `CFAB-Q3-ROLLBACK` | `resolved` | `forward-compensating-generation` |
| `CFAB-Q3-REVOCATION` | `resolved` | `no-lower-fallback-fail-closed` |
| `CFAB-Q3-XF-POSITION` | `resolved` | `after-upper-activation` |
| `FREEZE-U-A1` | `resolved` | `activation-window` |

`CFAB-S-SEAL` / `CFAB-S-GUARANTEE` / `CFAB-B-SIDE-EFFECT` の行は逐語どおり維持する。

### §9.1

- `:542`
  - 現行逐語: `発効 commit X を cutoff とする。`
  - 置換後: X は「上位 X」を指し、後続の下位 X_f は cutoff を更新しない、と明確化する。
- `:564-567` の bundle mode は、上位 resolver が §7.5 の revoked terminal state を返した場合に legacy mode へ降格しない、という参照だけを加える。fail-closed 本文は §7.5 に重複させない。

### §10 / §10.2

- `:599-605`
  - 現行逐語: `したがって本書は各段の完了判定を exact に書かない。` および `各段の陽性 fixture ... 各段の陰性 fixture`
  - 置換後: 段 0 が固定する fixture 閉包を段 1〜4・6〜8に限定し、段 5 を除外する。この段集合が束 3(a) の唯一の正本。
- `:628-629`
  - 現行逐語: `未定義の段を「該当なし」として飛ばすこともしない。`
  - 置換後: 一般則は維持しつつ、ユーザー裁定による段 5 fixture 除外だけを明示的例外とする。段 6 へ例外を拡張しない。
- `:633`
  - 現行逐語: `§12 の全問 + 既存の未裁定 ... 各段の陽性・陰性 fixture`
  - 置換後: 完了条件を §10.2 の算出条件と、本節で定めた段集合の fixture closure へ参照させる。
- `:638` の段 5 は `未定義` のまま維持する。
- `:639` の段 6は段 5 依存を維持し、完了 predicate の扱いを `CFAB-STAGE6-COMPLETION-PREDICATE` として §12.3 へ送る。
- §10.2 `:666-675`
  - 現行逐語: `§10.1 の他者手番 gate ... が閉じていない。`
  - 置換後: manifest の `required_gates` に `unresolved` / `pending` / `nonconforming` が一件でもあれば `incomplete`、と実装に一致する一般形へ直す。
  - `complete` 要求には `blocking_gate_count == 0` も明記する。

### §12

- §12.1 `:735-742` を 2026-08-10/11 の確定済み索引へ更新し、上記 4 selection と §8/§10 裁定を「literal + 正本節」だけで追加する。規則本文は再掲しない。
- §12.2 `:744-749` は変更しない。
- §12.3 `:751-774` の旧 3 束を削除し、`CFAB-STAGE6-COMPLETION-PREDICATE` だけを残す。
- §12.4 `:776-782` に、既存の他者手番 2 件に加えて `CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT` の owner/status と §10 へのポインタを置く。

## 実装面

### `ruling-profile.v1.json:1`

上記 4 ID だけを `resolved` にし、selection を exact literal へ更新する。順序・12 ID・先送り 3 ID は変えない。

### `calibration_freeze_authority_contract.py`

- `:73-84` `_SELECTION_ENUMS`
  - 上記 Q3 3 ID の singleton enum を追加。
  - `FREEZE-U-A1` は `{"activation-window"}` に縮め、却下された `post-activation-lease` を受理可能値として残さない。
  - S/G の既存 enum は維持し、B の enum は追加しない。
- `:85` 付近へ `_EXPECTED_RULING_STATES` を追加し、裁定済み 4 ID の exact stateと、S/G/B の `(unresolved, None)` を独立 pin する。
- `:117-126` `_EXPECTED_REQUIRED_GATES` を後述の 9 entry へ更新。
- 同付近へ `_EXPECTED_REQUIRED_GATES_ENTRIES_SHA256 = "b5aae8d5cff4597208c6cf4156958bb06bab2ea762de9ee8368dadc686554ce5"` を独立 pin として追加。
- `:445-508` `_validate_ruling_profile`
  - applicability 検査後に `_EXPECTED_RULING_STATES` と exact 照合する。
  - これにより裁定済み ID の `unresolved` 回帰と、先送り ID の先行 `resolved` を拒否する。
- `:421-428` required gate hash 検査
  - parsed entries からの再計算値、manifest literal、module 内独立 SHA pin の三者一致を要求する。
  - `_EXPECTED_REQUIRED_GATES` の semantic set 照合も残す。
- `:752-760` status 算出ロジックは変更しない。新しい入力により `incomplete` が再計算される。

### `manifest.v1.json:1`

`required_gates` を次の固定順・`count=9` とする。

```text
CFAB-Q3-REVOCATION                         user                 resolved
CFAB-Q3-ROLLBACK                           user                 resolved
CFAB-Q3-XF-POSITION                        user                 resolved
CFAB-S8-S10-CONTRADICTION                  user                 resolved
CFAB-STAGE6-COMPLETION-PREDICATE           user                 unresolved
CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT  stage-fixture-waves  pending
FREEZE-AX-TOPOLOGY                         lower-impl-wave      nonconforming
FREEZE-CONFORMANCE-LITERAL                 lower-wa-wave        unresolved
FREEZE-U-A1                                user                 resolved
```

- `entries_sha256`: `b5aae8d5cff4597208c6cf4156958bb06bab2ea762de9ee8368dadc686554ce5`
- top-level `status`: `incomplete` のまま。
- `fixtures`、`row_coverage`、`pending_count=5`、case raw hashes は変更しない。

### 変更しない実装面

- `calibration_freeze_authority_execution.py:16-20,709-738` は ruling profile を実行せず、既存 executable cases だけを production entrypoint へ流すため変更しない。
- `test_calibration_freeze_authority_execution.py:30-124` は期待集合が不変なので変更しない。
- `cases/*.json:1` は全 10 件とも変更しない。
- `orchestrator/campaign/**`、`tools/**`、`output/**` の実体は変更しない。

## canonical bytes と hash 再計算

1. Codex author は段 4 で確定した上記 9-entry 表を入力として、manifest を読まない独立スクリプトで `json.dumps(sort_keys=True, ensure_ascii=True, separators=(",",":"), allow_nan=False).encode("ascii")` を作る。
2. `required_gates.entries_sha256` は entries 配列の canonical bytes **のみ**を SHA-256 に掛ける。LF は含めない。
3. manifest と profile の record 全体は同じ canonical JSON の後ろに LF をちょうど 1 byte 付ける。
4. author は算出 hash を manifest と module 独立 pin へ記録するが、自動更新 helper で両方を書き換えない。
5. 親は staged manifest の実 bytesから別途再計算し、上記 planning 値と module pin を照合する。不一致なら land しない。
6. case files は無変更なので、manifest の各 `raw_sha256`、実 case bytes、`_EXPECTED_RAW_SHA256_BY_FIXTURE` の三者と `_EXPECTED_FIXTURE_ENTRIES_SHA256` は一切再生成しない。ここを一括 refresh すると独立 pin が退化する。

## テスト面

追加位置は `test_calibration_freeze_authority_contract.py`。

### 陽性 node

- `:153` 後 `test_adjudicated_ruling_and_gate_projection_is_exact`
  - 4 selection、S/G/B の unresolved、9 gate の ID/owner/status/orderを exact assert。
  - 緩和ではなく、裁定と先送りを literal で固定する。
- `:165` 後 `test_required_gate_hash_has_independent_module_pin`
  - 実 manifest の canonical entries hash が manifest literal と module pin の双方に一致することを assert。
  - 自己整合だけの hash を受理しないため、受理集合を狭める。

### 陰性 node

- `:330` 前後 `test_adjudicated_ruling_cannot_regress_to_unresolved`
  - Q3 rollback を `unresolved/null` へ戻し、独立 state pin で拒否。
  - 裁定前状態への回帰を新たに拒否する。
- `:422` 前後 `test_rejected_post_activation_lease_is_rejected`
  - U-A1 を `post-activation-lease` に差し替え、selection enum 外として拒否。
  - 却下案の受理を閉じる。
- `:330` 前後 `test_deferred_seal_ruling_cannot_be_resolved`
  - S を `S1` または `S2` に変え、schema/applicability が整っていても state pin で拒否。
  - 先送り S の先行解決を閉じる。
- `:330` 前後 `test_guarantee_must_remain_unresolved_while_seal_is_unresolved`
  - G を `resolved/G-a` に変え、既存 applicability 拒否を直接固定。
  - 保証境界を先行決定できる経路を閉じる。
- `:360-405` 付近 `test_stage5_cannot_reenter_fixture_assignment_scope`
  - gate ID を旧 `CFAB-STAGE-FIXTURE-ASSIGNMENT` に戻し、manifest hash も更新した上で独立 gate pin により拒否。
  - 段 5 を黙って scope へ戻す変更を拒否する。
- 同所 `test_required_gate_reorder_with_refreshed_manifest_hash_is_rejected`
  - entries を並べ替えて manifest hash も再計算し、module SHA pin で拒否。
  - manifest 内の自己再計算だけで pin を動かせない。

### 既存 node の更新

- `:121-136` `test_real_repository_contract_is_consistent_but_incomplete`
  - `unresolved_count: 6 → 2`。S と B の applicable unresolved だけが残り、pending 5 と status `incomplete` は維持。
  - 4 裁定分の帳簿更新であり、complete を受理しない。
- `:156-165` `test_current_repository_is_rejected_as_stage0_incomplete`
  - 診断を `applicable_unresolved=2, blocking_gates=4` へ更新。
  - 例外期待は維持し、緑化しない。
- `:392-404` `test_required_gate_resolved_without_evidence_is_rejected`
  - 配列 index ではなく `CFAB-STAGE6-COMPLETION-PREDICATE` を選び、`resolved` 改変を拒否。
  - 未裁定 gate の先行解決拒否を維持する。
- `:439-452` `test_not_applicable_outside_applicability_rule_is_rejected`
  - index 4 依存をやめ、ID 検索で Q3 rollback を選ぶ。期待理由は不変。
- `:455-468` は `test_deferred_ruling_without_design_selection_enum_is_rejected` へ改名し、`CFAB-B-SIDE-EFFECT` を対象にする。
  - Q3 に enum が追加されたことによるテスト消失を避け、未裁定 B の fail-closed を維持する。

## 不変条件の機械的保証

| 不変条件 | 落とす node |
|---|---|
| S/G/B が unresolved のまま | `test_adjudicated_ruling_and_gate_projection_is_exact`、`test_deferred_seal_ruling_cannot_be_resolved`、`test_guarantee_must_remain_unresolved_while_seal_is_unresolved`、更新後の `test_deferred_ruling_without_design_selection_enum_is_rejected` |
| 段 0 status = incomplete | `test_real_repository_contract_is_consistent_but_incomplete`、`test_current_repository_is_rejected_as_stage0_incomplete`、`test_manifest_status_cannot_claim_complete_while_gates_remain` |
| 裁定前 ID へ resolved を書けない | `test_required_gate_resolved_without_evidence_is_rejected` と上記 S/G/B 負例。enum の無い新 ID は既存 validator が拒否 |
| production 無変更 | **保証なし**。恒久的な no-reference test は将来の段 1 実装を不当に禁止するため追加しない。親が `git diff --name-only` で `orchestrator/campaign/**`・`tools/**`・`output/**` の差分 0 を確認する |

## リスク

- §1 が revocation を「上位 resolver が解決できない HEAD」とだけ扱うと、既存の下位 fallback が復活する。`never activated` と `revoked after activation` の状態分離が最重要。
- §7.5 exact schema は将来の受理集合を固定する。target、0/1 件、人間 commit、immutability を欠く schema は黙った受理拡大になる。
- gate ID は owner literal より強いが、現行 status 算出は段番号自体を解釈しない。段 5 除外は exact pin された宣言であり、stage fixture inventory から導出される保証ではない。
- manifest hash と module pin を同じ更新 helper で生成すると三者照合が自己再計算へ退化する。author と親の入力・計算を分ける必要がある。
- `unresolved_count` と `blocking_gates` の減少を理由に `status=complete` へ変えると段 0 関門が緩む。pending 5、S/B、段 6 gate、他者手番 2 件を残す。
- production 無変更には test node がないため、最終的には親の diff scope 検査が唯一の防壁となる。

## 総括

- 裁定 4 点は §7.2・§5.1・§7.5・§5.2へ一意に配置し、段 5 除外は §10 だけを正本にする。
- profile は 4 ID を resolved、S/G/B を unresolved のまま独立 pin する。
- manifest は 9 gate、status `incomplete`、予測 hash `b5aae8d5…54ce5` とする。
- 最大のリスクは、revocation 後を通常の未解決として下位 authority へ fallback させる実装である。