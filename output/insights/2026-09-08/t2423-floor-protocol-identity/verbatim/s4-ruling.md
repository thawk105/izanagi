# 段 4 裁定 — [T-2423] plan v2

日時: 2026-09-08 (JST 午前)。親 = dev-wave manager。入力: brief-s1.md、s2-plan.md、s3-lensA.md、s3-lensB.md。
wave worktree は local main c12e25078 へ `--ff-only` で揃えた (本 wave の対象 5 file は 34af5a571 と同一 bytes)。

## 0. 前提の訂正 — 依頼の択一 (a)/(b) は偽の前提に立っていた

依頼文と起票文 (T-2423) は「protocol は凍結 spec に無く、**build receipt からも導出できない**」を前提に
(a) spec へ足す / (b) D1641 を 4 要素へ訂正 の択一を置いた。段 3 レンズ A がこれを反証し、親が現物で確認した:

- build receipt = portable record (`s8b-binary-admission/v2`) の exact key に `binding` があり (`s8b_binary_admission.py:41-45`)、
  `binding.genome_canonical` は `Genome.canonical()` の `protocol|flags` 形式である (`model.py:56-59`、writer は
  `s8b_materialization.py:114-123` が `prepared.genome.canonical()` から書く)。
- validator は `source.genome_sha256 == sha256(genome_canonical)`、materialization binding との一致、`variant_id` の再計算、
  `binding_sha256` の再計算で genome_canonical を binary へ束縛する (`s8b_binary_admission.py:131-147, 356-369`)。
- protocol を取り出す共有 helper `protocol_from_floor_genome()` が既に在る (`genome.py:223-251`)。canonical 形でなければ `ValueError`。
- 現行 issuer が失敗するのは record の **top-level** に `protocol` key を探すからであり (`p3_b4_floor_artifact_issuer.py:770`)、
  「導出できない」からではない。テストは monkeypatch で偽 key を通しており (`test_p3_b4_floor_artifact_issuer.py:56-84`)、
  fixture の genome は非 canonical な JSON 文字列 (`test_floor_pair_driver.py:60-62`) なので、実 receipt に在る事実が隠れていた。

## 1. 裁定: **(c) を採る — receipt の `binding.genome_canonical` から protocol を導出する。spec も D1641 も変えない。**

- (a) は測定された binary の事実から protocol を切り離し、人手宣言値で成果物名を発行できるようにする (規律 2 の向きに反する。
  D1374 の却下欄「検査していないことを検査したと読ませる」型)。加えて spec schema・spec sha・HMAC 順序 golden・prereg の
  記述整合という不要な変更面を生む。
- (b) は D1641 の逐語を減らし、`between_run_floor` が既に silo / mocc を名前で分けている経路と矛盾し、別 protocol の
  2 件目を `_publish_create_only` の `artifact_exists` で発行不能にする。
- (c) は変更面が issuer 1 file とその test だけで、protocol が binary に束縛された値になる。D1696 (validator 拡張なし) にも
  D1373 (protocol は source/binary の事実へ束縛) にも整合し、新規 gate・許可リスト・schema 変更を伴わない。
- 依頼は「段 4 で択一を裁定」と親に委ねている。択一の前提が偽と実測で判明したため、親は (a)/(b) の外の最小案を採る。
  **ユーザーが (a) を望むなら再裁定で戻せる**ことを最終報告に明記する。

### (P1)〜(P5) の処分
- (P1) (a) 採用 → **撤回**、(c) へ。 (P2) top-level key → **不要 (撤回)**。 (P3) schema v4 bump → **不要 (撤回)**。
- (P4) 「spec.protocol を使う」→ **撤回**。issuer は各 artifact の receipt から `protocol_from_floor_genome(record["binding"]["genome_canonical"])`
  を取り、`_identifier` を課し、**全 artifact で 1 値**のときだけ identity に採る。canonical でない・読めない・sha 不一致・混在のいずれも
  `missing=("protocol",)` として fail-closed を維持する (この分岐は到達可能)。
  threads / workload_identifier / campaign_identifier の missing 分岐は loader と summary validator が先に保証し到達不能 (段 2 §4、レンズ A §2 が一致) →
  **削除**し、docstring にその保証の出所 (`floor_pair_driver.py:759-776, 1136-1147`、issuer `411-433`) を書く。`B4FloorIdentityError`・
  `missing_identity_elements`・`_authority_value` の guard は残す。
- (P5) protocol の許可リスト・source 束縛 gate を足さない → **維持**。derived protocol は `_identifier` 検査のみ。

## 2. 所見の裁定

| 出所 | 所見 | 判定 | 処分 |
|---|---|---|---|
| A§1,§3,§4,§7(N2) | receipt binding から protocol を導出でき、(a)/(b) は偽の択一 | real | must-fix → 本裁定 §1 |
| A§2 | P4 後は全 missing 分岐が到達不能。receipt 経路なら protocol だけ到達可能 | real | 採用: 3 分岐削除、protocol 分岐維持 |
| A§5 | (a) なら v4 は正しいが、(c) なら SPEC_SCHEMA 不変 | real | 採用: driver 無変更 |
| A§6 | fixture の genome を実 canonical 形へ直し、混在負例と receipt 由来正例を独立 nodeid で置く | real | must-fix → §3 |
| A§7(N6) | t2412 は commit 済み (4f8601fb7) だが main 未着地 | real | 受入直前に main を再読 (既定手順) |
| B§1 | 台帳の被覆は t2412 後を見ていない | real (但し scope 縮小) | (c) で driver test は不変。issuer の改名/追加 nodeid のみ。台帳は編集しない (F903 の衝突点を避ける)。受入で被覆 gate が赤なら正本 producer で更新 |
| B§2 | 隣接衝突 0 件、意味的衝突なし | refuted | (c) では driver test も触らず衝突面は issuer test だけ (t2412 は行 109・509 後) |
| B§3 M11 | `identity=None` の fixture は AttributeError に過剰決定 | real | 採用: guard 変異の正例は「有効 identity + 非空 missing」で組む |
| B§3 M2 | 期待 node が広い | real → (c) で対象外 | driver 変異は無し |
| B§4 | golden 再固定の手順 | real → (c) で対象外 | HMAC golden に触れない |
| B§5 N5 | `spec.schema` は成果物へ直接書かれず HMAC preimage 経由 | real | brief の表現を訂正 (記録時) |
| B§6 | 本 wave 単独では production 発行に至らない (t2412 の不動点・実 spec・実測が別途要る) | real | scope 外として明記。依頼文の「この 1 点だけで」は「コード上の identity の最後の欠落」の意味では真 |
| B§7 | 「instance 不在 → erratum 不要」の一般論は誤り。D1765 は prereg の陳腐化に対する規則 | real | 採用: 理由を「(c) は spec も prereg の記述も変えないので陳腐化が生じない」へ訂正 |
| A/B 共通 | protocol allowlist / source 束縛 | 裁定パッケージ候補 | D1696 再訪条件未成立、実装しない |

## 3. plan v2 (実装子への確定事項)

所有 path: `orchestrator/campaign/p3_b4_floor_artifact_issuer.py`、`orchestrator/tests/test_p3_b4_floor_artifact_issuer.py`、
`orchestrator/tests/test_floor_pair_driver.py` (fixture helper の**後方互換な引数追加だけ**。既存呼出しの bytes 不変)。
`floor_pair_driver.py` は**変更しない**。

1. issuer `_derive_identity(root, spec, campaign_ids)` (736-804):
   - receipt loop は維持 (path 解決・sha 照合・JSON load)。`record["binding"]["genome_canonical"]` を
     `genome.protocol_from_floor_genome()` に通し、`_identifier(..., label=f"build receipt {path}.binding.genome_canonical")` を課す。
     `record` が dict でない / `binding` が無い / `genome_canonical` が無い / `ValueError` / `B4FloorArtifactError` は protocol_failed。
   - `len(protocols) != 1` → `missing.append("protocol")` (混在・全失敗・artifacts 空)。
   - threads / workload_identifier / campaign_identifier の missing 分岐を削除。docstring に到達不能の根拠を書く。
   - import は `from . import floor_pair_driver` の隣に `from .genome import protocol_from_floor_genome` (循環 import が無いことを確認)。
2. issuer `_authority_value` の文言 `"summary-bound spec/receipt から全 identity 要素を導出できない"` は receipt 由来なので**維持**。
   `load_floor_pair_summary` docstring (823-827) は実態 (protocol は receipt binding 由来、欠落は canonical でない/混在) へ直す。
3. `test_floor_pair_driver.py`: `_portable_build_record(..., *, tag, genome_canonical: str | None = None)` を追加し、None なら現行 JSON 形 (bytes 不変)。
   `_write_inputs(root, *, genome_canonicals: dict[str, str] | None = None)` で tag ごとに渡す。既存呼出しは引数無しのまま → HMAC golden と全 driver test は不変。
4. `test_p3_b4_floor_artifact_issuer.py`:
   - `receipt_has_protocol` と `validate_portable_binary_record` の monkeypatch を**完全撤去**。`_synthetic_source(..., genome_canonicals=...)` を追加し、
     正例は `Genome(protocol="mocc", flags={"FIXTURE": 1}).canonical()` / `{"FIXTURE": 2}` の 2 receipt (env_tag `synthetic-env` との取り違えを殺す値)。
   - 負例 1 (canonical でない genome): 既定 fixture (JSON 文字列) → `missing_identity_elements == ("protocol",)`、`issue_authoritative_floor` が `B4FloorIdentityError`。
     加えて **protocol 接頭辞を持つが canonical でない** 値 (例 `mocc|B=1,A=2`、未整列) でも同じ拒否になること (naive split 変異を殺す)。
   - 負例 2 (混在): candidate `mocc|FIXTURE=1`、reference `silo|FIXTURE=1` → `missing == ("protocol",)`、発行拒否。
   - 正例: 実 `finalize_floor` 由来の summary で発行成功、filename `__protocol-mocc`、`authority.artifact_identity.protocol == "mocc"`、
     `identity_derivation` は現行どおり。
   - guard 正例: 受理済み summary を `identity=<有効>, missing_identity_elements=("protocol",)` に差し替えて `_authority_value` が `B4FloorIdentityError` (B§3 の指摘どおり有効 identity で組む)。
   - `receipt_has_protocol=True` を渡していた全呼出し (段 2 §5 の 9 件) を `genome_canonicals=` へ書き換え。旧 missing-protocol 期待 test 2 本は改名。
5. 台帳・docs・driver・receipt schema は触らない。

## 4. 変異事前登録 (DW-M01。実装後に anchor と期待 node を再検証してから probe → 本走)

| ID | 対象 | 変異 | 期待 (殺す test) |
|---|---|---|---|
| M1 | issuer `_derive_identity` | derived protocol を `spec.environment.env_tag` に置換 | filename/identity 正例 (`mocc` ≠ `synthetic-env`) |
| M2 | 同 | derived protocol を定数 `"silo"` に置換 | 同上 (`mocc`) |
| M3 | 同 | `len(protocols) != 1` を `not protocols` に緩める (混在時に先頭採用) | 混在負例 |
| M4 | 同 | `protocol_from_floor_genome(...)` を `str(...).split("|", 1)[0]` に置換 | 非 canonical 負例 (`mocc|B=1,A=2`) |
| M5 | 同 | receipt sha256 不一致で `continue` せず読み進める | 既存の receipt 改変負例があればそれ、無ければ登録しない (帰属確認後) |
| M6 | issuer `_artifact_filename` | `__protocol-` segment を落とす | `test_authority_filename_contains_all_five_derived_components` |
| M7 | issuer `_authority_value` | `or summary.missing_identity_elements` を削除 | guard 正例 (有効 identity + 非空 missing) |
| M8 | issuer `_derive_identity` | 全 receipt 失敗時に `missing` へ入れず空 protocol で identity を組む | 非 canonical 負例 |

冗長 (帰属不成立) として登録しない: spec key 欠落 (loader が先に拒否)、threads/workload/campaign の missing (到達不能)、issuer 側 `_identifier` 緩和 (`protocol_from_floor_genome` が先に拒否しうる — probe で確認)。

## 5. scope 外 (裁定パッケージ候補・記録のみ)
- protocol の許可リスト / CCBench source 束縛 (D1696 再訪条件 = 人手見落とし 1 件、未成立)。
- 異 protocol の対照対を権威 floor として許すか (現行は fail-closed で拒否、意図どおり)。
- t2412 の loader 不動点、実 spec の作成、実測の実施。
- main c12e25078 に `.codex/worktrees/*` 111 件が gitlink (mode 160000) として commit されている異常 (T-2412 wave の docs commit)。本 wave は触らない。
