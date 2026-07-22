# [T-080] 一回限りの移行契約 wave — 逐語・裁定・変異台帳 (2026-07-22)

- **wave**: dev-wave 1 回 (branch worktree-dev-wave-ruling-ac)。[T-083] (a) 裁定の科学レーン第 1 手。
  [T-068][T-077][T-078] を統合する「一回限りの移行契約」の実装
- **成果 commit**: U0 = a0e090f、U1..U4 統合 = 689af34、fix ラウンド 1 = a1f2db6 (+ 本記録 commit)
- **工程**: brief (前提実測 + P1..P7 + G1..G5) → codex プラン v1 (max) → 敵対相談 2 並列 (max、両 NO-GO、
  C1×11 + C2×16 所見) → 親裁定 J1..J13 (refuted 0) → プラン v2 (max、異議 2 件は親採用) → 実装 5 単位
  (U0 直列 → U1..U4 worktree 並列、high) → 親統合 + 受入全走 → 敵対レビュー 2 並列 (max、両 NO-GO、
  A×8 + B×9 所見) → 親 fix 指令 F-1..F-8 → fix ラウンド 1 (high) → 焦点再レビュー (max) →
  変異 matrix 親実測 2 巡
- **本文書の構成**: §1 brief / §2 プラン v1 / §3 敵対相談 (正しさ境界) / §4 敵対相談 (整合・実効性) /
  §5 親裁定 J1..J13 / §6 プラン v2 / §7 実装報告 U0..U4 / §8 敵対レビュー A / §9 敵対レビュー B /
  §10 fix 指令 F-1..F-8 / §11 fix 報告 / §12 焦点再レビュー + fix 指令 2 + fix2 報告 / §13 変異台帳 (3 巡) / §14 受入記録
- **正本の分担**: 設計判断 = D78 (decisions.md)、可変状態 = worklog 末尾、運用手順 (receipt 発行) =
  worklog 末尾の引き渡しパッケージ。本文書は逐語の凍結アーカイブであり更新しない

- **hash erratum**: 実装中の逐語 (§7..§14) は積み直し前の旧 hash を含む。対応 = 64c13dc→a0e090f / 7b8e843→689af34 / 1c1b342→a1f2db6 / 68661b9→6767695 (AI-Agent trailer の段落分断を修正した message-only 積み直し。tree は全段階で同一 — `git diff` 空で機械確認済み)

---


## §1 brief (前提実測 + P1..P7)

# brief — [T-080] 一回限りの移行契約 wave (freeze gate 復旧の最小抽出)

## scope

[T-083] (a) 裁定 (worklog 2026-07-22 (9)、phase3 2026-07-22 改訂) が定めた「一回限りの移行契約」を実装する。
対象は公式 gate (`s8b_oracle_driver.gate_check`) が拒否する legacy freeze 2 点 — S-1 known_axes freeze
(`output/s1-freeze/known_axes_freeze.json`) と holdout freeze (`output/s8b-freeze/holdout_freeze.json`) —
の検証復旧。[T-068] (発効と同時に閉じる) / [T-077] (人間同席 receipt で再 pin) / [T-078] (外部固定 fixture
契約で positive control 再定義) を統合する。恒久一般化 (g1 bundle・active pointer・revocation・check
registry・writer CLI = W 列) は oracle 後 (D75/D76 は破棄しない — forward-compatible に作る)。

## 確定済みユーザー裁定 (前提)

- [T-083] (a): 科学レーン最短復帰。移行契約 = 「dangling ancestry の typed 化、D73 の ccbench_pin・
  機械再構成検査は維持、holdout 二重 drift は人間同席 receipt で再 pin。exact bytes / source closure /
  generator / protocol を固定」
- D75 R1..R16 全承認 (特に R7(b) blob 照合置換、R10/R11/R12 = T-068/T-077/T-078 の処理形、
  R11 は「design_source 再 pin + generator の M 化」、R13 発効系は人間 commit、R16 closure 限界受諾)
- D76 (s2 exact schema — observation/anchor 分類/g0 adapter/reason grammar。移行契約はこれと非衝突の最小形)
- D72 (8) 格下げ条件 = observation の構造化伝播先が要る / D73 (2)(3)(4) = 後段 2 検査の恒久マスク禁止・
  ancestry 判別の 4 分類・伝播先の不在
- [T-084] G1..G5 (下記適用)

## 前提実測 (brief 前、全て実物照合 — 模擬・monkeypatch なし)

- 公式 gate 拒否 4 件 (実測): holdout design_source drift / S-1 source drift (s8a_trigger_sweep.py) /
  floor-null / budget-null。後 2 件は floor 実測までの設計どおり状態
- S-1: source 63 record 中 12 record drift (3 ファイル: s8a_trigger_sweep.py・s6_sort_sweep.py・
  p3_s4_loop_sort.py)。frozen_at_head=2066ce6b 不存在 commit。generator 自己 hash OK・pairing OK・
  ccbench_pin OK。機械再構成は source drift により FAIL (D73 07-21 時点の「後段 2 検査 PASS」から悪化 —
  裁定時に見えていなかった劣化だが、裁定の前提 (source closure の固定が要る) を覆さず強める方向)
- holdout: design_source DRIFT (recorded=1829af7f/actual=5fbdd7ef)・generator DRIFT (recorded=1910fff3/
  actual=41c0b6a7)・known_axes_freeze hash OK・frozen_at_head=2e20d441 不存在 commit。unknownness
  search 再実行 = conjunction_hits 0 (層2 現在も成立)
- v2 ratified lane (`s8b_ratified_freeze._verify_generation_semantics`) は既に blob 照合
  (frozen_at_head の blob、worktree でなく blob) — 新世代 (v2 g1+) は健全設計。破損は legacy v1 の
  worktree 照合 + dangling anchor に限局
- gate 内の known verify は v1/v2 分岐の外で常時走る (`s8b_oracle_driver.py:249-261`、worktree resolver)。
  v2 移行後もここが直らない限り gate は開かない
- 受入 baseline: 2618 passed / 18 skipped / 0 failed (rc=0)
- pin 元全列挙 (Explore 子、file:line は子の報告): `FROZEN_MANIFEST`
  (orchestrator/tests/test_frozen_artifacts.py:33-50) が 3 freeze JSON を全 bytes pin — 現在全緑 =
  bytes 未変更。`V1_FREEZE_SHA256` (s8b_ratified_freeze.py:62) は同 file 約 20 箇所 + テスト 2 file
  40 箇所超が参照。real-repo gate の拒否 4 件は test_s8b_oracle_driver.py:531-541 が件数 + prefix で
  pin 済み。`load_legacy_freeze` (s8b_ratified_freeze.py:1329-1347) が「bytes 定数束縛で dangling
  ancestry を明示バイパス + docstring に理由記録」の実装済み先例。measurement_freeze.json は同じ
  dangling anchor 2066ce6b を持ち、`s1_measurement_freeze.py` は known_axes 検証を統合契約として内包
  (同:407-408) — **known verify の意味論変更は measurement lane へ漏れる** (プランで消費面を map する
  こと)。`output/freeze-migrations/` は未存在の新設パスで hooks 保護外。observation の受け皿は
  WAL campaign-start / oracle report / judge のいずれにも現状無い (D73 (4) を実測再確認)

## 不変条件

1. 規律 2/3 不変。内容検査 (source 内容照合・ccbench_pin・機械再構成・unknownness 層1/層2・schema/
   pairing/statics) は 1 つも落とさない。比較基盤を「進化する worktree」から「人間が受領した固定基準」へ
   移すだけ
2. 凍結成果物 3 JSON (known_axes/measurement/holdout) は 1 byte も変更しない。FROZEN_MANIFEST 既存 pin・
   `V1_FREEZE_SHA256`・旧許可表・equality chain 不変
3. ancestry 格下げは D73 (3) の 4 分類に従う — observation 化は「不存在 commit」「merge-base rc=1」のみ。
   git 操作障害・非 commit object は拒否のまま
4. observation の格納先 (受け皿) を gate 挙動変更と同 wave で用意する (D72 (8)、§8 step 2 の順序原則)
5. hooks の拒否は迂回しない。guard_write の防護 (output/s8b-freeze/ 直接書込拒否) はそのまま —
   receipt は保護外の新設パスに置く

## 親の provisional 裁定 (攻撃対象 — 一件ずつ否認/採用を返せ)

- (P1) 再 pin は sidecar の一回限り migration receipt (`output/freeze-migrations/` 新設) で表現し、
  freeze JSON は書き換えない。receipt は基準 commit H_mig を記録し、移行後の source 照合は
  「H_mig の blob bytes」に対して行う (R7(b) の blob 照合を legacy に前倒し適用。worktree 照合は廃止)
- (P2) receipt 不在時は現行挙動を完全保存 (拒否集合 4 件のまま)。receipt 実在 + 厳格検証合格時のみ
  移行後挙動。malformed / 検証不合格 receipt = 明示 refusal (fail-closed。silent legacy fallback 禁止)
- (P3) 人間同席の充足形 = receipt の confirmed_by/confirmed_at + 人間 commit (AI-Agent: none)。
  wave 内は「機構 + receipt draft 生成 + hermetic 実証」まで。実 receipt 発行はユーザー引き渡しで、
  wave 完了時点の公式 gate は 4 拒否のまま (期待状態)。発効 = ユーザーの receipt commit ([T-068] は
  その時点で閉じ、本 wave では「発効待ち」と記録)
- (P4) 検査意味論の移行: (a) source closure / design_source は receipt の再 pin 表 + H_mig blob 照合
  (drift 12 record は旧値→新値の対応を receipt に記録、旧値は typed observation として保存)。
  (b) generator (checker 自己 hash) field は両 freeze とも M 化 = gate から外し observation 化
  (R11・T-074 (a) の履行)。(c) ccbench_pin 照合は現行のまま維持。(d) 機械再構成は resolver を
  H_mig blob に差し替えて実行維持。(e) dangling ancestry は typed observation 化 (分類は不変条件 3)
- (P5) observation の受け皿 = GateDecision への observations field 追加 + oracle report / WAL
  campaign-start payload への構造化転記。s2 §S2-3 の将来 schema と衝突しない最小形 (名前空間を分け、
  将来 schema の先取り実装はしない)
- (P6) scope 外: measurement freeze の移行 (公式 gate が検証しない。歴史レーンのまま)、
  s1_verify_extime_calibration / s1_report の legacy caller (D72 (9) 既知の残存破損、現状維持)、
  g1 bundle 生成・active pointer・W-0 hooks 契約変更
- (P7) [T-078] は本 wave で実装 — positive control を外部固定 fixture の 3 点契約 (baseline pass /
  単一理由 mutant fail / revert pass、§10) で再定義する

## G1..G5 適用

- G1 (生死): 上記実測が生死確認。移行後の期待 gate 拒否集合 = {floor-null, budget-null} exact を
  hermetic fixture で実証する。大型機構 (LLM driver 等) は作らない
- G2 (blocker 限定): 拒否集合・正しさ判定・proof 参照を実際に変える欠陥のみ fix 対象。他は backlog
- G3 (族一般化禁止): 一回限り migration。receipt schema の汎用化・全世代対応はしない
- G4: 発火条件付き機能なし
- G5: レビュー must-fix には影響 1 行を必須とする

## 成果物の形

- production: `s1_known_axes_freeze.py` / `s8b_holdout_freeze.py` / `s8b_oracle_driver.py` の検証意味論
  変更 + migration receipt module (新設 1 file)
- receipt draft (未発効。ユーザー確認・commit 手順を最終報告に添付)
- テスト: hermetic 両状態 (receipt 不在 = 現行 4 拒否 exact / receipt 有効 = {floor-null, budget-null}
  exact) + real-repo golden 更新 + [T-078] positive control 3 点契約
- 変異 matrix (B-057 事前登録は段 4 でコード読解後に確定)、worklog/decisions/insights、AI-Agent trailer

## 並列分割方針

receipt module + observation 型を先行単位で完了 → (a) S-1 lane、(b) holdout lane、(c) gate 統合 +
[T-067] exact テスト更新 + [T-078] を素集合で並列。テスト所有が重なる場合は単位を統合して直列化する。


## §2 codex プラン v1

# [T-080] 一回限りの移行契約 wave 実装プラン

## 結論

実装可能。ただし、brief の想定どおり [s1_known_axes_freeze.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:718) 自体を編集すると、その checker の自己 hash 検査が receipt 判定より先に失敗し、P2 の「receipt 不在時は現行4拒否を完全保存」を破る。

したがって、既存 S-1 / holdout checker と凍結 JSON は一切変更せず、新設する T-080 専用 adapter が三状態を分岐する構成とする。receipt 有効時の S-1 再構成は `source_resolver` 差替えだけでは成立しないため、H_mig snapshot 上で `build_document` を実行し、12 source hash を射影した legacy document と比較する。

## P 裁定への異議

| 裁定 | 判定 | 実装上の扱い |
|---|---|---|
| P1 | 採用 | sidecar receipt と H_mig blob 照合を採用。freeze JSON は不変。 |
| P2 | 採用。ただし brief の変更ファイル案と両立しない | S-1 checker の generator 検査は source 検査より先にある（[721-727](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:721)）。checker 自体を編集すると receipt 不在時の最初の拒否が source drift から generator drift に変わる。既存 checker は無変更とし、oracle 側 adapter でのみ意味論を切り替える。これは [D72](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2781) が記録した自己 pin 問題とも整合する。 |
| P3 | 採用 | draft は未発効 path、canonical receipt は人間 commit のみ。 |
| P4(a)(b)(c)(e) | 採用 | source/design の H_mig blob 化、generator M 化、ccbench 維持、ancestry typed 化を実装する。 |
| P4(d) | 修正が必要 | `source_resolver` は [verify_document:729-741](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:729) の source hash にしか作用せず、[build_document:608-679](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:608) は module-global `ROOT` と imported module の `__file__` を読む。H_mig snapshot で builder 自体を実行する必要がある。 |
| P5 | 意図は採用、field 名は修正 | 汎用的な `observations` は将来の §S2-3 と衝突しやすい。`t080_freeze_migration_observation` という一回限りの名前を GateDecision/WAL/report で共通使用する。`freeze_identity` 等は実装しない。 |
| P6 | 採用 | measurement、extime calibration、S-1 report は現行 checker のまま。oracle adapter を import/call しないことをテストで固定する。 |
| P7 | 採用 | 外部固定 fixture の baseline/mutant/revert 三点契約へ置換する。 |

なお、holdout の現行 verifier は full `build_document` equality を持たない。[verify_document:683-823](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:683) が保証するのは、静的 schema・snapshot 再導出・binding・H_mig 時点と現在時点の unknownness 検査である。揮発する `file_count` 等について full builder equality を新設すると現行契約を不当に強化するため、`build_document` equality の維持は既にその検査を持つ S-1 に適用する。

## migration receipt の exact schema

### 配置

発効 receipt:

```text
output/freeze-migrations/t080-legacy-freeze-repin.receipt.json
```

未発効 draft:

```text
output/freeze-migrations/t080-legacy-freeze-repin.receipt.draft.json
```

恒久設計の `legacy-to-permanent-g1.receipt.json`、`freeze-family-transition-receipt/v1`（[§S2-1.3](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:93)）とは path、schema、field 名を共有しない。

### top-level

exact 8 fields、追加 field 禁止。

| field | 型・規則 |
|---|---|
| `schema_version` | string、exact `"izanagi-t080-legacy-freeze-repin/v1"` |
| `migration_id` | string、exact `"T-080"` |
| `migration_basis_commit` | lowercase 40hex。H_mig |
| `artifacts` | exact keys `known_axes`, `holdout` の object |
| `source_repins` | exact 13 element array |
| `metadata_fields` | exact 2 element array |
| `confirmed_by` | draft では null、active では非空 NFC string |
| `confirmed_at` | draft では null、active では UTC秒精度 `YYYY-MM-DDTHH:MM:SSZ` |

`confirmed_by` と `confirmed_at` は両方 null、または両方 non-null のみ許可する。mixed null、前後空白、空文字、日時 offset、少数秒を拒否する。他の field は一切 null 不可。

### `artifacts`

各値は exact 3 fields:

```text
path
raw_sha256
recorded_frozen_at_head
```

固定値:

| key | path | raw_sha256 | recorded head |
|---|---|---|---|
| `known_axes` | `output/s1-freeze/known_axes_freeze.json` | `354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516` | `2066ce6b47c6a5d43ca2c8ab3cc7728d32336be1` |
| `holdout` | `output/s8b-freeze/holdout_freeze.json` | `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688` | `2e20d441aaf7ae267e941ecda09e4b53050943cf` |

current bytes と H_mig tree 内の bytes の双方が上記 raw SHA-256 と一致しなければならない。

### `source_repins`

各 element は exact 5 fields:

```text
artifact                # "known_axes" | "holdout"
json_pointer             # artifact 内の sha256 field
path                     # repo-relative source path
recorded_sha256          # legacy JSON の値
migration_blob_sha256    # H_mig:path の bytes SHA-256
```

配列順は `artifact` 順を `known_axes`, `holdout` と固定し、その内側で `json_pointer` の Unicode code point 昇順。

exact 13件:

- known_axes 12件

  - `entries/{balanced,write-heavy,read-heavy}/system_gate/sources/4/sha256` → `orchestrator/campaign/s8a_trigger_sweep.py`
  - `entries/{balanced,write-heavy,read-heavy}/ident_all/sources/3/sha256` → `orchestrator/campaign/s8a_trigger_sweep.py`
  - `entries/{balanced,write-heavy}/sort_best/sources/5/sha256`、`entries/read-heavy/sort_best/sources/2/sha256` → `orchestrator/campaign/s6_sort_sweep.py`
  - `entries/{balanced,write-heavy}/sort_best/sources/6/sha256`、`entries/read-heavy/sort_best/sources/3/sha256` → `orchestrator/campaign/p3_s4_loop_sort.py`

- holdout 1件

  - `/design_source/sha256` → `docs/phase3-8b-descriptor-design.md`

実装では全63 source recordを列挙し、次を同時に要求する。

1. 12件の changed pointer 集合が receipt と完全一致する。
2. 各 changed record の legacy 値/H_mig blob hash が receipt と一致する。
3. 残り51件は legacy 値と H_mig blob hash が一致し、receipt に現れない。
4. surplus、duplicate、missing、path差替えを拒否する。

### `metadata_fields`

各 element は exact 6 fields:

```text
artifact
json_pointer
path
recorded_sha256
migration_blob_sha256
disposition
```

exact 2件、known_axes → holdout 順:

- known_axes `/generator/sha256`
- holdout `/generator/sha256`

`disposition` は exact `"metadata-only"`。これらは receipt integrity と observation 生成には使うが、pass/fail の generator equality には使用しない。

### canonical bytes

repo の canonical JSON hash 慣行（例: [s8b_holdout_freeze.py:130-134](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:130)）に合わせる。

```python
json.dumps(
    value,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
```

- UTF-8、BOMなし、trailing newlineなし。
- duplicate key、NaN、Infinity、top-level非objectを拒否。
- draft も同じ canonical encoding とする。
- active loader は parse結果の再canonical化 bytes が入力 bytes と完全一致しなければ拒否する。

## receipt CLI と検証契約

新設 module に以下を置く。

```text
draft --basis H_mig --out ...draft.json
validate-draft --path ...draft.json
finalize --draft ... --confirmed-by NAME --confirmed-at UTC --out ...receipt.json
verify --path ...receipt.json
```

`draft`:

- `H_mig == git rev-parse HEAD`。
- canonical active receipt が不在。
- freeze、checker、13 source path、ccbench に未コミット差分がない。
- H_mig が commit object。
- H_mig の `external/ccbench` gitlink が legacy `ccbench_pin` と一致。
- source closure、H_mig snapshot 再構成、holdout unknownness を実行。
- create-only で、confirmation 2 fields は null。

`validate-draft`:

- schema、canonical bytes、H_mig blob、closure、再構成を再検証。
- null confirmation pair を許す。
- receipt commit topology はまだ要求しない。

`finalize`:

- draft の H_mig が現行 HEAD と一致する状態で再検証。
- confirmation 2 fields だけを置換し、canonical active pathを create-only 生成。
- source hash 等を CLI 引数から上書きする機能は持たない。

`verify`:

- active schemaに加えて、receipt導入 commit Rを履歴から一意に導出する。
- R は non-merge、唯一の parent が H_mig。
- R の diff は canonical receipt 1 file の追加だけ。
- R の commit message trailer に exact `AI-Agent: none`。
- 現在の receipt blob が R の blob と一致し、R が validation HEAD の ancestor。
- `confirmed_by` と commit author の文字列一致は要求しない。

draft は H_mig を記録するため H_mig commit 自体には格納できない。wave commit後に生成する未追跡 handoff artifactとし、active loader は `.draft.json` を完全に無視する。

## 検査意味論の三状態

### 共通 receipt resolver

新設する `resolve_t080_receipt(root, validation_head)` は次を返す。

```text
state: "absent" | "valid" | "invalid"
receipt: parsed receipt | null
observation: object | null
refusal: string | null
```

- absent: canonical pathが存在しない。
- valid: schema、canonical bytes、blob、topology、再構成がすべて合格。
- invalid: pathが存在するが一つでも不合格。

invalid reason は fail-fast で一件に正規化する。

```text
migration-receipt-verify: [receipt-read|receipt-json|receipt-canonical|
receipt-schema|receipt-confirmation|receipt-basis|receipt-artifact|
receipt-repin|receipt-topology] ...
```

invalid 時も既存 legacy verifierを診断目的で実行し、floor/budgetを検査する。ただし migration refusal が必ず残るため、legacy 結果が authorization に使われることはない。

### S-1 known_axes

対象: [verify_document:718-766](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:718)。

#### receipt 不在

現在の `s1_known_axes_freeze.verify()` をそのまま呼ぶ。現状は `s8a_trigger_sweep.py` の source drift refusal。generator、pairing、ancestry、ccbench、再構成の順序も変更しない。

#### receipt 有効

`verify_t080_known_axes()` が以下を行う。

1. freeze raw bytes、strict JSON、schema、generator path、63 source record shapeを検証。
2. source 63件を H_mig blob と照合し、12/51 closureを検証。
3. `assert_s1b_pairing()` を無変更で実行。
4. legacy `frozen_at_head` を後述の4分類で判定。
5. current `external/ccbench` HEAD と legacy `ccbench_pin` の一致を維持。
6. H_mig treeの gitlinkも同じ pinであることを要求。
7. H_mig top-level treeと ccbench pinを一時 snapshotへ安全に展開。
8. snapshot 内の H_mig版 `build_document` を、legacy `frozen_at_head`、`ccbench_pin`、`python_version` を明示して実行。
9. legacy documentのdeep-copyに12 source hashだけを適用。
10. projected legacy / rebuilt H_mig document の双方から `/generator/sha256` だけを比較対象外にし、残りを canonical deep equalityで比較。

これにより、doc側の旧12 hashと builderが出すH_mig hashの差だけを明示射影し、selection rule、entry、pairing、reference field等の機械再構成は維持される。resolver差替えだけでは不十分。

#### receipt 不正

`migration-receipt-verify` を追加し、legacy verifierを診断実行する。migrated verifierは呼ばず、observationは null。

### holdout

対象: [verify_document:683-823](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:683)。

#### receipt 不在

現在の `s8b_holdout_freeze.verify()` をそのまま呼ぶ。現状の最初の refusal は design_source drift。

#### receipt 有効

`verify_t080_holdout()` が以下を行う。

1. raw artifact、strict schemaを検証。
2. H_mig の design blobを receipt の1 repinと照合。
3. known_axes raw hashは legacy recordとH_migで一致することを維持。
4. generator path/schemaを検査し、sha equalityはM化。
5. legacy ancestryを独立分類。
6. legacy documentをdeep-copyし、design hashとgenerator hashをH_mig値に射影。
7. H_mig snapshot上の既存 `verify_document` に projected documentを渡す。`current_head` にはlegacy headを渡し、ancestryだけは独立classifierの結果を使用する。
8. これにより schema、定数、confirmation、floor/budget/refreeze note、snapshot layer 1、positive control、variant bindingを既存コードで維持。
9. さらにH_mig版 `search_repository` を現在のrepo rootへ適用し、現在時点の conjunction 0 とpositive >0を再検査する。進化したcurrent checkerではなく、H_migで固定した検索プロトコルを使う。

holdout の記録済み `file_count` / per-axis count を現在値と完全一致させる検査は追加しない。現行 verifier 自身が [695-697](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:695) でそれを揮発値として区別しているためである。

#### receipt 不正

S-1と同様、明示 migration refusal + legacy診断。silent fallbackは禁止。

### ancestryの4分類

`classify_legacy_anchor(recorded, validation_head)`:

1. 40hex shapeを検査。
2. `git cat-file --batch-check` でobject存在とtypeを判別。
3. 不存在 → observation `missing-commit`。
4. objectは存在するがtypeがcommitでない → refusal。
5. commitなら `git merge-base --is-ancestor recorded validation_head`。
6. rc=0 → observation `ancestor`。
7. rc=1 → observation `not-ancestor`。
8. rc>1、spawn失敗、I/O失敗 → refusal。

stderr文字列による分類は行わない。[D73 (3)](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2879) の4分類をそのまま実装する。

H_mig 自体の不存在・非commit・非ancestorは migration receipt refusalであり、legacy ancestry observationには格下げしない。

## observation の exact 伝播

### envelope

field名は全層で exact `t080_freeze_migration_observation`。値は null または exact 6-field object:

```text
schema_version
migration_id
receipt
migration_basis_commit
validation_head
items
```

制約:

- `schema_version == "izanagi-t080-freeze-migration-observation/v1"`
- `migration_id == "T-080"`
- `receipt` は exact `{path, raw_sha256}`
- commitは40hex
- `items` は valid receipt時 exact 17件

各 item は exact 6 fields:

```text
artifact     # known_axes | holdout
kind         # source-repin | generator-metadata | legacy-ancestry
subject      # JSON pointer
recorded     # legacy hash/head
observed     # H_mig hash、validation_head、または null
status
```

順序:

1. receipt `source_repins` 13件
2. `metadata_fields` 2件
3. ancestry `known_axes`, `holdout` 2件

status:

- source: `repinned-to-basis-blob`
- generator: `metadata-only`
- ancestry: `missing-commit | not-ancestor | ancestor`

missing commit の `observed` だけ null。他は64hex hashまたはvalidation head。

### GateDecision

[GateDecision:81-85](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:81) を次へ拡張する。

```python
@dataclass
class GateDecision:
    allowed: bool
    refusals: list[str]
    t080_freeze_migration_observation: Optional[dict] = None
```

defaultを付けるため、既存の `GateDecision(True, [])` とmockは後方互換。`dataclasses.asdict()` の出力には新keyが常に現れるので、CLI exact期待値と[T-067]系テストは null/object を明記して更新する。

### WALとrun result

[run_blockのcampaign-start:1027-1034](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1027) に同名fieldを常に追加する。

- receipt absent: null
- valid: envelope
- invalid: gateが拒否するためcampaign-start自体を書かない

gate拒否resultと成功resultにも同fieldを含め、CLIの [asdict消費:1374](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1374) を含めて欠落させない。

### oracle report

[s8b_oracle_report.py:935-1289](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:935) で campaign assessment が row群とT-080 observationを返すようにする。

- 旧WALでkey不在、または全campaignでnull → report top-levelはnull。
- 全campaignで同一canonical envelope → そのobjectを転記。
- malformed、campaign間でobject不一致、null/object混在 → 関係rowを `protocol_violation` にし、top-levelはnull。
- report top-levelには同名keyを常に置く。

judgeの意思決定には使わず、extra fieldを無視できる現行性質をテストする。将来用の `freeze_identity`、`freeze_verification_observation`、legacy adapter registry（[§S2-3](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:989)）は追加しない。

## ファイル別変更一覧と実装単位

新規ファイルのlineは予定範囲。

### U0: receipt/adapter core（先行、単独所有）

| file:line | 変更 |
|---|---|
| [t080_freeze_migration.py:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1) 新設 | 1-90 constants/error/types、91-230 strict/canonical receipt、231-360 Git topology/ancestry、361-480 H_mig snapshot、481-600 S-1 adapter、601-740 holdout adapter、741-820 observation validator/CLI。 |
| [test_t080_freeze_migration.py:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_t080_freeze_migration.py:1) 新設 | schema、canonical bytes、draft/active、13+2 closure、human commit topology、ancestry4分類、snapshot再構成、M化をhermeticに検査。 |

### U1: official gate/WAL統合（U0後）

| file:line | 変更 |
|---|---|
| [s8b_oracle_driver.py:81-85](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:81) | GateDecision field追加。 |
| [s8b_oracle_driver.py:165-288](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:165) | receiptを一度だけresolveし、absent/valid/invalidを分岐。v1 holdoutだけを移行adapterへ切替。 |
| [s8b_oracle_driver.py:249-261](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:249) | v1/v2分岐外のknown_axes検証にも同じresolver結果を適用。measurementには伝播させない。 |
| [s8b_oracle_driver.py:848-877](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:848) | run result契約へfield追加。 |
| [s8b_oracle_driver.py:1027-1034](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1027) | campaign-startへ転記。 |
| [test_s8b_oracle_driver.py:57-81](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:57) | exact helperを維持し、hermetic三状態を件数+理由集合完全一致で追加。 |
| [test_s8b_oracle_driver.py:531-541](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:531) | real-repo testをreceipt状態別の二分岐exact goldenへ変更。invalidは許容しない。 |
| [test_s8b_oracle_driver.py:891](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:891) | campaign-start exact payloadとasdict期待値へnull/object追加。 |
| [conftest.py:47-89](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/conftest.py:47) | renamed real-repo gate nodeを更新。破損T-078 nodeを除去。 |
| [test_real_repo_serialization.py:30-63](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_real_repo_serialization.py:30) | conftestとは独立したgoldenを同じnode差分で更新。 |

### U2: report伝播（U0後、U1とファイル素集合）

| file:line | 変更 |
|---|---|
| [s8b_oracle_report.py:935-1235](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:935) | campaign-startからfield抽出、validation、protocol issue統合。 |
| [s8b_oracle_report.py:1238-1289](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1238) | campaign間canonical一致を確認しtop-levelへ転記。 |
| [test_s8b_oracle_report.py:145](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_report.py:145) | WAL fixtureにoptional fieldを追加し、旧欠測/null/valid/malformed/mismatchをexact検査。 |
| [test_s8b_oracle_judge.py:53](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_judge.py:53) | observation fieldの有無でjudge結果が変わらないことをpin。 |
| [test_s8b_oracle_artifacts.py:121](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_artifacts.py:121) | strict loaderが追加fieldを失わず保持することを検査。production artifact schemaは変更しない。 |

### U3: [T-078]（U0と並列可）

| file:line | 変更 |
|---|---|
| [t080_holdout_positive_control.txt:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/fixtures/t080_holdout_positive_control.txt:1) 新設 | 下記3行のexact bytes。 |
| [t080_fixture_roots.py:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/t080_fixture_roots.py:1) 新設 | path、baseline/mutant SHA-256、固定offsetとold/new byteをliteral pin。 |
| [test_s8b_holdout_freeze.py:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_holdout_freeze.py:47) | baseline/mutant/revert三点テスト。 |
| [test_s8b_repo_scan_invariant.py:21-35](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_repo_scan_invariant.py:21) | fixture追加後もholdout hit exact空、positive >0を維持。 |
| [test_s8b_oracle_driver.py:1209-1231](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1209) | generator driftで先に落ちる壊れたcharacterization testを削除。 |

fixture exact bytes:

```text
ycsb_rratio=50
ycsb_zipf_skew=0.9
ycsb_rmw=0
```

末尾LFあり。baseline SHA-256:

```text
caee6deabcf6209f5e8d59ee104a64b6bcf18a2a6054b1cefd6141709802faa7
```

`50` の `0` を `1` にした単一byte mutant:

```text
ycsb_rratio=51
```

mutant SHA-256:

```text
1f0bacf1fa9cc9571faebf5e8177c34c4bd3ee98a9ee381753bfbe73fac18d29
```

三点契約:

1. baseline: positive `hit_count == 1`、holdout conjunctionは双方空。
2. mutant: `_assert_search_pass` の理由が exact 1件、`rr50 陽性対照が 0 件...`。
3. revert: raw hashとcanonical reportがbaselineに完全一致し再pass。

### U4: scope漏れpin（U0後）

| file:line | 変更 |
|---|---|
| [s1_measurement_freeze.py:156-163](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:156) / [407-408](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:407) | production無変更。既存testへ「T-080 receiptがあってもlegacy known verifierを呼ぶ」pinを追加。 |
| [s1_verify_extime_calibration.py:193-200](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_verify_extime_calibration.py:193) | production無変更。T-080 moduleをimport/callしないことを既存testで固定。 |
| [s1_report.py:781-795](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:781) | production無変更。measurement経由の現行failure意味論が残ることを固定。 |

### U5: docs（全実装・親実測後）

- [docs/decisions.md:3113](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:3113): D78としてT-080 schema、H_mig、三状態、P4修正、発効待ちを記録。
- [docs/phase3-8b-descriptor-design.md:79](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3-8b-descriptor-design.md:79): T-068/T-077/T-078の状態を「機構実装済み・人間receipt待ち」へ更新。
- [docs/worklog.md:53](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:53): 親が実測値とcommitを記録。
- `output/insights/2026-07-22_t080-migration-contract.md`: 実装根拠と限界。
- `output/insights/2026-07-22_t080-mutation-preregistration.md`: 下記変異表と実測結果。
- [orchestrator/tests/README.md](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/README.md:57): 新規hermetic/real-repo testの走らせ方。

## テスト計画

### hermetic gate exact pin

| 状態 | expected refusal |
|---|---|
| canonical receipt不在 | exact 4件: holdout design_source drift、known source drift、floor-null、budget-null |
| valid receipt | exact 2件: `floor-null`、`budget-null` |
| invalid receipt | exact 5件: `migration-receipt-verify` 1件 + legacy 4件 |

hermeticでは全文完全一致に `_assert_exact_refusals` を使う。real-repoでは既存 helperの方針どおり、件数 + 理由prefix集合をexactにし、実worktree hash値だけを焼き込まない。

### real-repo golden

`test_real_freeze_gate_matches_t080_receipt_state` として二状態だけを許可する。

- active canonical path不在: exact 4 refusal、observation null。
- active canonical path存在かつ `verify` 合格: exact `{floor-null,budget-null}`、17-item observation。
- path存在かつinvalid: test自体を失敗させる。

wave中はcanonical receiptを発行しないので、不在branchの4拒否のままgreen。人間発行commit後は同じtestがvalid branchへ切り替わり、無関係な「golden更新commit」を追加で要求しない。

### その他

- S-1 63 source、12 changed、51 unchangedの件数をexact pin。
- H_mig generator値を変えたfixtureでもrefusalは増えず、metadata observationだけ変わる。
- current ccbench、H_mig gitlink、snapshot extractionを個別検査。
- ancestry `missing/nonancestor/ancestor/noncommit/git-error` を個別検査。
- WAL旧形式、null、valid、malformed、campaign間不一致。
- measurement/extime/reportへの漏れなし。
- [test_frozen_artifacts.py:61-81](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:61) を独立実行。
- 既存2618 nodeは削除・xfail・期待緩和せず全件再実行し、新規nodeを加えた総数で `0 failed` を要求。
- `check_codex_agents.py`、`check_docs.py`、commit後の`check_ai_provenance.py`は親が実行する。

## 変異テスト事前登録候補

| 変異 | 先行する同一入力検査 | 赤が一理由に絞れる根拠 |
|---|---|---|
| artifact raw hash検査を無効化 | path/JSON parseは通る。temp copyの空白1byte変更は内容検査に影響しない | `receipt-artifact` だけが消え、他内容は同一 |
| canonical receipt bytes検査を無効化 | strict parse/schemaは意味的に同一pretty JSONを通す | `receipt-canonical` のみ |
| `AI-Agent: none` trailer検査を無効化 | parent、diff、blob、confirmationは正しいcommitを使う | `receipt-topology` のtrailer理由のみ |
| receipt commitのsingle-file diff検査を無効化 | parent/trailer/blobを正しくし、無関係1fileだけ同commitへ追加 | topology diff理由のみ |
| surplus repin集合検査を無効化 | extra entryは既存51件のold/new同値pointerにし、個別hash/schemaを通す | closure surplus理由のみ |
| noncommit objectをmissing observation扱いに変異 | 40hex shapeとobject存在検査は通る | object type refusalのみ |
| merge-base rc>1をrc=1扱いに変異 | cat-fileはcommitとして成功するfault-injected runnerを使う | git障害 refusalのみ |
| current ccbench pin検査を無効化 | H_mig gitlink/snapshotは正しいまま、temp repoのcurrent submodule HEADだけ変える | current ccbench mismatchのみ |
| current unknownness層2を無効化 | H_mig snapshot/static/layer1を通し、current rootだけにrr80三軸fileを追加 | live conjunction refusalのみ |
| T-078 positive検査を無効化 | 50→51 mutantはholdout三軸に一致せず、他検査を通す | positive 0理由のみ |

候補から外すもの:

- `migration_blob_sha256` 直接照合の無効化: S-1再構成比較でも検出され、単一理由に分離できない。
- S-1 `build_document` equalityの無効化: exact 12 closureを保ったまま確実にbuilder出力だけを変える独立fixtureの根拠が現時点で不足。production builderのmonkeypatch/echoは恒久設計§10に反するため候補外。
- generator equality復活/削除: generatorはMでありallowed/refusalを変えない。mutation killではなく17-item observation exact testで固定する。
- WAL/report転記削除: gate判断を変えない診断面なので、mutation score対象ではなくexact propagation testで固定する。
- legacy headのraw値改変: artifact raw-root検査が先に落ち、ancestry分類の単一理由テストにならない。

## リスクと対策

| リスク | 対策 |
|---|---|
| holdout generator自己hashとdraft生成順 | 既存holdout checkerを編集しない。例外的変更が必要になった場合は、その変更を含む最終実装commitを先にH_migとし、その後にdraftを生成する。draftはHEAD不一致・dirty pathを拒否。 |
| S-1 checker編集でreceipt不在挙動が変わる | checkerを所有対象から外す。新adapterのみをoracleから呼ぶ。 |
| receipt発行後にreal-repo testが4→2へflip | invalidを許さない二状態exact goldenにする。canonical receipt不在/valid以外は赤。 |
| measurement/extime/S-1 reportへ意味論が漏れる | 既存checkerを変更せず、T-080 adapterをoracle専用にする。3 callerそれぞれにimport/call非発生pin。 |
| H_mig snapshotで過去コードを実行する | H_migをreceipt parentとして固定し、safe path検査後にtop repoとccbenchをtempへ展開。`python -I`、環境最小化、timeout、network不要、出力canonical parse。 |
| holdout fixture追加でrepository scan countが変わる | runtime countとの完全一致は元々要求されない。fixtureはrr50のみでrr80/rr20 conjunctionを作らないことをreal scanでexact確認。 |
| draftを誤って発効扱い | loaderはcanonical filenameだけを見る。draft拡張子は無視。 |
| 人間receipt commit後のhistory rewrite | Rの一意導出、parent H_mig、blob、ancestorを毎回検証し、rewrite時はfail-closed。 |
| 恒久D75/D76機構の先取り | pointer、generation、revocation、registry、g1 schema、freeze identityを作らない。T080 prefixに閉じる。 |
| FROZEN_MANIFEST/V1 pinへの波及 | 下記no-touch検査を受入に含める。 |

明示的に無変更とするファイル:

- [s1_known_axes_freeze.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:1)
- [s8b_holdout_freeze.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:1)
- [test_frozen_artifacts.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:33)
- [s8b_ratified_freeze.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:62)
- `output/s1-freeze/known_axes_freeze.json`
- `output/s1-freeze/measurement_freeze.json`
- `output/s8b-freeze/holdout_freeze.json`

親の受入検査には次を含める。

```bash
git diff --exit-code -- \
  output/s1-freeze/known_axes_freeze.json \
  output/s1-freeze/measurement_freeze.json \
  output/s8b-freeze/holdout_freeze.json \
  orchestrator/tests/test_frozen_artifacts.py \
  orchestrator/campaign/s8b_ratified_freeze.py \
  orchestrator/campaign/s8b_approved.py
```

これによりFROZEN_MANIFEST既存8 entry、`V1_FREEZE_SHA256`、旧許可表、equality chainの無変更を同時に証明する。`output/s8b-freeze/` への書込み経路は一切追加しない。

## ユーザー引き渡し手順

AI実装・全受入・AI側commitが完了し、そのcommitをH_migとした後に実施する。

```bash
T080_BASIS="$(git rev-parse HEAD)"

python3 orchestrator/campaign/t080_freeze_migration.py draft \
  --basis "$T080_BASIS" \
  --out output/freeze-migrations/t080-legacy-freeze-repin.receipt.draft.json

python3 orchestrator/campaign/t080_freeze_migration.py validate-draft \
  --path output/freeze-migrations/t080-legacy-freeze-repin.receipt.draft.json

python3 -m json.tool \
  output/freeze-migrations/t080-legacy-freeze-repin.receipt.draft.json
```

人間が13 repin、2 metadata field、H_mig、artifact hashを確認した後:

```bash
T080_CONFIRMED_BY='確認者名'
T080_CONFIRMED_AT="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

python3 orchestrator/campaign/t080_freeze_migration.py finalize \
  --draft output/freeze-migrations/t080-legacy-freeze-repin.receipt.draft.json \
  --confirmed-by "$T080_CONFIRMED_BY" \
  --confirmed-at "$T080_CONFIRMED_AT" \
  --out output/freeze-migrations/t080-legacy-freeze-repin.receipt.json

python3 -m json.tool \
  output/freeze-migrations/t080-legacy-freeze-repin.receipt.json

rm -- output/freeze-migrations/t080-legacy-freeze-repin.receipt.draft.json

git add output/freeze-migrations/t080-legacy-freeze-repin.receipt.json
git diff --cached --name-only
git diff --cached
```

`git diff --cached --name-only` がreceipt 1 fileだけであることを確認して、人間がcommitする。

```bash
git commit \
  -m '[T-080] activate legacy freeze migration receipt' \
  -m 'AI-Agent: none'

git show -s --format='%H%n%P%n%B' HEAD

python3 orchestrator/campaign/t080_freeze_migration.py verify \
  --path output/freeze-migrations/t080-legacy-freeze-repin.receipt.json

python3 orchestrator/campaign/s8b_oracle_driver.py gate-check \
  --freeze output/s8b-freeze/holdout_freeze.json \
  --root .
```

最終gate期待値は exact 2件、`floor-null` と `budget-null`。pushは人間判断のままとする。

本プラン作成では、指定どおりファイル編集・テスト実行は行っていない。

## §3 敵対相談 — 正しさ境界レンズ (NO-GO)

総合判定は **NO-GO**。静的検査だけで、規律2/3に触れる BLOCKER が複数ある。

## 所見

[1] [BLOCKER] 対象 (brief 不変条件1 / plan §S-1・holdout)  
主張: 「内容検査は落とさず比較基準を移すだけ」は偽り。現行 S-1 は current worktree の全 source を照合し、holdout も current design/generator bytes を照合するが、新経路は H_mig blob だけを見る。[brief.md:54](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/brief.md:54)、[plan_v1.md:234](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:234)、[s1_known_axes_freeze.py:729](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:729)、[s8b_holdout_freeze.py:641](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:641)。恒久設計自身も、この変更で H_gen 後の current drift を受理しうると明記している。[freeze-permanent-design.md:479](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:479)  
影響: receipt 発行後に source 3ファイル、design doc、checker を改変しても H_mig が残る限り migrated gate は通り、現行なら拒否される状態が受理集合へ入る。  
修正案: current validation tree/worktree と H_mig closure の差を launch/audit gate に残すか、この受理集合拡大を明示損失として再裁定し、恒久設計の literal 二面・承認 report と同等の回収層を同時導入する。

[2] [BLOCKER] 対象 (brief P1/P4 / plan §S-1 step 8–10)  
主張: H_mig 上の generator に H_mig の source hash を生成させ、同じ hash を legacy 側へ overlay して比較するため、12 hash cell 自体は恒真的である。非 overlay field の比較は残るが、generator と期待値が同じ H_mig 由来なので独立 oracle ではない。[plan_v1.md:241](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:241)。さらに builder は `pipeline`・`model` 等を importし、`variant_id` を判定に使う一方、それらは63 source recordに含まれない。[s1_known_axes_freeze.py:24](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:24)、[s1_known_axes_freeze.py:222](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:222)、[freeze-permanent-design.md:60](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:60)。  
影響: H_mig の checkerまたは未列挙依存が legacy documentを読み返して期待値を返すよう改竄されても、receipt・overlay・再構成が同時に成立し、不正な再 pin が正当化される。  
修正案: H_mig checkerを実行 oracleにせず、別 origin の固定 reference implementation／goldenで再導出する。少なくとも adapter・reference実装・receipt hashを別 literal面へ pinし、H_mig全依存差分を人間向けreportとしてreceiptへ束縛する。

[3] [BLOCKER] 対象 (plan §receipt topology / §ancestry 4分類)  
主張: rc=0/1/>1 の分解自体は妥当だが、Git object viewのhardeningが欠落している。既存 ratified verifier は `core.useReplaceRefs=false` を全Git呼出しへ付け、replace refs・grafts・shallow repositoryを明示拒否している。[s8b_ratified_freeze.py:269](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:269)、[s8b_ratified_freeze.py:306](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:306)。プランの `cat-file --batch-check` / `merge-base` 契約にはこれがない。[plan_v1.md:281](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:281)。  
影響: replace/graftで非commitをcommitに見せる、Rのparent/treeを差し替える、shallow履歴で複数導入を隠すことで、本来 refusal のreceiptやanchorがvalid/observationへ変わる。  
修正案: 既存 hardened Git primitiveを共用し、replace refs・grafts・shallowを存在時点で拒否する。`GIT_DIR`、`GIT_WORK_TREE`、alternate object DB等も除いた環境で実行し、merge-baseだけはrcを保持する専用runnerにする。

[4] [MAJOR] 対象 (brief P2 / plan §共通resolver・real-repo golden)  
主張: `absent` を「worktree上でcanonical pathが存在しない」と定義したため、未発行と、発効後の削除・broken symlink・committed deletionを区別できない。[plan_v1.md:208](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:208)。さらにreal-repo testはその時点の不在branchを正解として受け入れる。[plan_v1.md:488](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:488)。  
影響: 発効済みreceiptを削除すると明示 refusal なしで legacy 4拒否へ戻り、17-item observationとreceipt参照が消える。  
修正案: validation historyにreceipt導入が一度でもあれば、現在path不在を必ず `invalid` にする。HEAD treeにblobがあるのにworktree不在、read/lstat失敗、delete/re-addも個別 refusal とし、発効後削除のnegative testを置く。

[5] [MAJOR] 対象 (brief 不変条件1・3 / plan §ancestry)  
主張: noncommit/git-errorをrefusalにするだけでは D73(2) の後段マスクは解消しない。現行は ancestry例外でccbench/reconstructionへ到達しない。[s1_known_axes_freeze.py:746](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:746)。プランもclassifierをccbench・再構成より前に置くが、classifier refusal後も独立検査を継続する契約を定めていない。[plan_v1.md:236](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:236)。  
影響: git障害またはnoncommit anchorが持続すると、後段のccbench drift・再構成破損が永続的に観測されず、proof reason集合が変わる。  
修正案: classifierを例外ではなくtyped resultにし、anchor refusalを蓄積した後も安全に独立実行できるccbench/H_mig reconstructionを必ず走らせ、全refusalを返す。

[6] [BLOCKER] 対象 (plan §H_mig snapshot実行)  
主張: `python -I`・環境最小化・timeoutはsandboxではない。[plan_v1.md:539](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:539)。実行対象は複数repo moduleをimportする任意Pythonである。[s1_known_axes_freeze.py:24](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:24)。またholdoutの `search_repository` はGit indexを要求するため、単なる安全展開snapshotでは動かない。[s8b_holdout_freeze.py:197](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:197)。  
影響: plain archiveなら検証不能、Git worktreeなら攻撃的H_mig codeがrepo/object DB・filesystem・networkへ副作用を起こし、draft/verify自体が攻撃経路になる。  
修正案: H_mig codeを実行しないpure tree reader方式へ変える。不可避ならread-only mount、network遮断、credentialなし、別UID、resource/output上限を持つOS sandboxとし、Git列挙は外側のtrusted codeが固定listとして渡す。

[7] [MAJOR] 対象 (brief P3 / plan §receipt verify・引渡し)  
主張: `confirmed_by` はcommit authorと一致不要で、`AI-Agent: none` も人間性を証明しない。[plan_v1.md:186](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:186)。既存hook自身が「AIがnone commitを作れる」と明記している。[guard_write.py:86](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/hooks/guard_write.py:86)。しかも新receipt pathはhook保護外であり、引渡しは13件のopaque hash確認しか要求しない。[brief.md:49](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/brief.md:49)、[plan_v1.md:588](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:588)。  
影響: AIまたは攻撃者が `confirmed_by` とtrailerを自己申告し、仕込んだsource driftを人間受領済みとして発効できる。  
修正案: allowlist済み署名鍵によるsigned commit、または少なくともH_migの全repin byte diff・導入commit・semantic projection reportをreceiptがhash束縛し、人間がそのreportを確認する契約にする。

[8] [BLOCKER] 対象 (brief P5/P6 / plan §observation伝播)  
主張: observationは実質必須にならない。旧WALでkey不在ならreportはnullのまま許容され、judgeはfieldを意図的に無視する。[plan_v1.md:370](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:370)。現行judgeも出力へfreeze/migration参照を持たない。[s8b_oracle_judge.py:259](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_judge.py:259)。さらに発効直後はfloor/budget拒否が残るので、driverはcampaign-startより前にreturnする。[s8b_oracle_driver.py:948](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:948)、[s8b_oracle_driver.py:1027](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1027)。calibrationも旧verifierを直接呼ぶままである。[s1_verify_extime_calibration.py:193](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_verify_extime_calibration.py:193)。  
影響: migration observation欠落の旧WALからもdeterminate verdictを作れ、発効時の格下げ記録は耐久化されず、最終proof chainからreceipt/anchor参照が消える。  
修正案: 発効後schemaではobservation欠落/nullを全row `protocol_violation`・judge `indeterminate` にする。gate拒否時もcreate-onlyのgate-attempt auditへ永続化し、verdictとcalibrationへ同一objectを必須転記する。

[9] [MAJOR] 対象 (brief P7 / plan §T-078)  
主張: 承認済み§10はfixtureをproduction root registryへpinし、fixtureと期待literalの同時更新を別面で検出する契約である。[freeze-permanent-design.md:379](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:379)。プランはtest側 `t080_fixture_roots.py` とfixtureを同じU3で追加するだけで、production rootも別commit面もない。[plan_v1.md:415](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:415)。なお、fixtureだけを検索対象にしてroot hash検査を外せば、50→51 mutantは `_assert_search_pass` のpositive-zero一理由になる。[s8b_holdout_freeze.py:412](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:412)。root検査も同じmutantへ掛ければhash mismatchとの二重理由になる。  
影響: fixture・hash literal・testを同一変更で追随または削除でき、T-078を閉じた後も恒真化を独立面が検出しない。  
修正案: production root literalとtest literalを別file・別commitで固定し、required-node manifestへ登録する。mutant試験はroot integrity試験と分離し、scanner入力だけを一時copyへ変異させてexact一理由を確認する。

[10] [BLOCKER] 対象 (plan §変異事前登録)  
主張: 最重要のS-1機械再構成equalityについて、negative controlを作れないとして変異対象から外している。[plan_v1.md:525](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:525)。しかしH_mig版checkerの `reference_values_note` だけを変更すれば、source63件・artifact・ccbench・generator M・topologyを通し、最後のdeep equalityだけを発火できる。現行の対応検査位置は [s1_known_axes_freeze.py:759](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:759)。  
影響: migrated equalityを削除・恒真化しても予定suiteが検出しない可能性が残り、selection/reference fieldを異なるbuilder出力で受理する。  
修正案: 上記H_mig checker literal差分fixtureで baseline pass / equality-only fail / revert passを作り、equality削除変異を必須killにする。

[11] [MAJOR] 対象 (brief 成果物所有 / plan §no-touch受入)  
主張: briefは自己pin済みchecker 2本をproduction変更対象にしているが、planは明示no-touchとしており所有表が矛盾する。[brief.md:99](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/brief.md:99)、[plan_v1.md:546](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:546)。加えてno-touchコマンドはchecker 2本を列挙せず、`git diff --exit-code -- ...` はcommit後ならwave内で変更済みでも成功する。[plan_v1.md:556](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:556)。テストについても一方で既存node削除を指示し、他方で「削除しない」と主張する。[plan_v1.md:423](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:423)、[plan_v1.md:505](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:505)。  
影響: briefに従った実装子がcheckerを変更してabsent時の拒否理由を変えても、commit後のno-touch受入と総node数主張が検出証拠にならない。  
修正案: 実装前にbriefの所有表をadapter-onlyへ訂正し、wave開始SHAを固定して `git diff $BEFORE..HEAD -- <全no-touch path>` を検査する。削除nodeは置換台帳として明示し、旧node数保存を主張しない。

## P1..P7 裁定

| 裁定 | 判定 | 根拠 |
|---|---|---|
| P1 | **否認** | H_mig blob化そのものは実装可能だが、current drift拒否を失い、H_mig bytesの正当性を独立に保証しない。[1][2] |
| P2 | **否認** | malformedは拒否できても、発効後のpath削除が `absent` へ落ち、conditional goldenもそれを正解化する。[3][4] |
| P3 | **否認** | `confirmed_*` と `AI-Agent:none` は人間性・semantic reviewの機械証明ではなく、現在のhandoffはopaque hash確認のみ。[7] |
| P4 | **否認** | (c) ccbench維持と4分類のrc方針は採用可能だが、(a)(b)(d)(e) はlive drift喪失、同源再構成、Git hardening欠落、後段maskを残す。[1][2][3][5][6][10] |
| P5 | **否認** | WALに届かない発効状態があり、旧WAL欠測を許し、judgeが捨てるため「受け皿」は装飾fieldに留まる。[8] |
| P6 | **否認** | D72条件が挙げたcalibration/report consumerを意図的に残しながらT-068を閉じるため、proof chainが分裂する。[8] |
| P7 | **否認** | 50→51 mutant自体は条件付きで単一理由にできるが、承認済み外部root・literal分離契約を実装していない。[9] |

## 総合判定

**NO-GO。**

最低でも、stickyなreceipt状態機械、既存同等のGit hardening、H_mig実行から独立した再構成oracle、発効時から必須となるWAL→report→judge/calibration伝播、人間承認に束縛されたsemantic review report、T-078の独立root面が揃うまで実装開始不可。テストは実行していない。

## §4 敵対相談 — 整合・実効性レンズ (NO-GO)

静的判定は **NO-GO**。テスト実行はしていない。所見は 8 BLOCKER / 7 MAJOR / 1 MINOR。

## 所見

[1] [BLOCKER] 対象 (plan §検査意味論の三状態・§real-repo golden / brief P2・P3) / 主張: `absent` を「現在 path がない」だけで決めるため、receipt 発行後の削除を未発行へ巻き戻せる。R 後に path を削除すると resolver は `absent`、real-repo test は exact 4 refusal で緑になり、`draft` の「canonical receipt 不在」条件も再び満たす。 / 根拠: [plan_v1.md:164](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:164)、[plan_v1.md:208](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:208)、[plan_v1.md:486](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:486)、D76 は追加一回と導入後の D/M/R/C/T 拒否を要求する [freeze-permanent-design-s2.md:570](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:570)。 / 放置した場合: 受理集合に「発行済みだが現在削除済み」が加わり、公式 gate が 2 refusal から旧 4 refusal へ黙って戻る。 / 修正案: `never-issued / active-valid / issued-but-missing / invalid` を H_v reachable historyから分類し、後二者を赤にする。real-repo test も履歴上の導入有無を exact pin する。

[2] [BLOCKER] 対象 (plan §receipt CLIと検証契約・§ancestry / brief P1・P3) / 主張: 現在 blob と R blob の一致、R の parent/diff/ancestor だけでは receipt の不変履歴を証明できない。R 後に別 bytesへ変更して元へ revert した履歴を受理するうえ、replace refs、grafts、shallow repository、単一 H_v 捕捉も未規定である。 / 根拠: [plan_v1.md:184](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:184)、[plan_v1.md:279](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:279)。正本は単一 H_v、replace/graft/shallow 拒否を要求する [freeze-permanent-design.md:187](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:187)。既存 ratified verifier は hardening と全 reachable commit の blob 列を実装済みである [s8b_ratified_freeze.py:269](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:269)、[s8b_ratified_freeze.py:456](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:456)。 / 放置した場合: 「過去に差替えられた receipt」とローカル Git graph で偽装した H_mig/blob が受理集合へ入る。 / 修正案: 検証開始時に H_v を一度だけ捕捉し、Git hardening、全 commit の `absent|R-blob`、導入一回、導入後 M/D/R/C/T 禁止を既存 ratified verifier 同等以上で実装する。

[3] [BLOCKER] 対象 (plan U1・§恒久設計先取りリスク / brief P1・P6) / 主張: valid T-080 receipt が存在する限り、v1/v2 分岐外の known 検証を常に legacy adapterへ切り替える設計で、将来 permanent g1 に載った後の停止条件がない。 / 根拠: [plan_v1.md:394](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:394)、[plan_v1.md:543](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:543)。D76 は g0/g1 を active pointerで明示分岐し、g1+ は permanent branchだけを受理する [freeze-permanent-design-s2.md:1298](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1298)。 / 放置した場合: W 列の g1 発効後も legacy known が proof 参照になり続けるか、新 known を legacy schemaとして拒否する。 / 修正案: T-080 adapter の発火条件を exact legacy holdout raw root＋legacy known path/hashに限定し、W-X 時に捨てる field、引き継ぐ receipt hash、adapter撤去条件を契約化する。

[4] [BLOCKER] 対象 (plan §配置・§observation / brief P1・P5) / 主張: 「恒久 receipt と filename/schema が違うから非衝突」は誤りである。D76 は `output/freeze-migrations/` の未知 fileを拒否し、将来 campaign-start/observations/verdict も exact key集合なので、T-080 fileと追加 fieldはそのままでは未知物になる。 / 根拠: [plan_v1.md:28](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:28)、[plan_v1.md:40](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:40)、[plan_v1.md:300](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:300)。未知 file拒否は [freeze-permanent-design-s2.md:570](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:570)、将来 exact payload/schema は [freeze-permanent-design-s2.md:1107](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1107)、[freeze-permanent-design-s2.md:1173](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1173)。 / 放置した場合: W 実装は正本どおりなら T-080 済み repositoryを拒否し、回避には D76 改訂か receipt 削除が必要になる。 / 修正案: T-080 を恒久専用 namespace 外の固定 pathへ隔離し、W-X による exact 消費・retirementを今の契約に記録する。D76 の一般機構自体は先取り実装しない。

[5] [BLOCKER] 対象 (plan §oracle report・U2 / brief P5) / 主張: observation は耐久 sinkになっていない。全 campaign から keyを削除しても「旧WAL」と判定されて nullが受理され、judgeは fieldを完全無視する。さらに既存 `8b-oracle-observations/v1` のまま keyだけ増やし、「schemaは変更しない」としている。 / 根拠: [plan_v1.md:368](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:368)、[plan_v1.md:409](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:409)。現行 schema literal は [s8b_oracle_artifacts.py:20](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_artifacts.py:20)、judgeは既存6 fieldだけで verdictを返す [s8b_oracle_judge.py:122](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_judge.py:122)。D73 の欠落条件は [decisions.md:2879](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2879)、D76 は欠落を全 row `protocol_violation`、verdict `indeterminate` とする [freeze-permanent-design-s2.md:1190](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1190)。 / 放置した場合: T-080 provenanceを全消去しても row受理・winner・verdictが一切変わらない。 / 修正案: R 導入前の legacy WALと導入後 WALを明示 grammarで分け、R 後の欠落/nullを violationにする。reportから verdictへ observationまたはその exact hash/reasonを転記し、欠測なら indeterminateにする。

[6] [MAJOR] 対象 (plan U1・§WAL/run result / brief P5) / 主張: resolverを `_gate_check_core()` 内で一度だけ呼ぶ設計では、core到達前の多数の return に observationを付けられない。default `None` が欠落を隠す。 / 根拠: planは core範囲だけを配線対象にする [plan_v1.md:394](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:394) 一方、全拒否resultへの転記を約束する [plan_v1.md:358](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:358)。実コードには gateの早期 return [s8b_oracle_driver.py:303](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:303)、[s8b_oracle_driver.py:347](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:347)、run_blockの早期 return [s8b_oracle_driver.py:882](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:882)、[s8b_oracle_driver.py:984](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:984) がある。 / 放置した場合: 同じ valid receiptでも失敗位置によって result参照が object/nullに変わり、absent状態と区別できなくなる。 / 修正案: `gate_check`/`run_block` の最外層で H_vとreceiptを一度捕捉し、全 GateDecision生成を observation必須の共通 factoryへ集約する。

[7] [BLOCKER] 対象 (plan U3・変異候補 / brief P7) / 主張: T-078 実装が D76 exact契約と正反対である。fixture pathが違い、正本が要求する「fixture bytes不変・検索predicate単独mutant」ではなく、`50→51` へ fixture bytes自体を変え、baseline/mutant hashを同じ test-side root fileで受け入れる。 / 根拠: [plan_v1.md:419](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:419)、[plan_v1.md:439](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:439)、[plan_v1.md:521](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:521)。D76 の exact path/root/hash と predicate-only mutant は [freeze-permanent-design-s2.md:2058](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2058)。 / 放置した場合: fixtureとrootを同時更新する変異が受理され、positive predicateが恒真でも T-078 を閉じた扱いになる。 / 修正案: D76 exact path・root key・bytesをそのまま使い、fixtureは一切変更せず、検索predicateだけを変異して 1→0→1 を証明する。

[8] [BLOCKER] 対象 (plan §receipt schema/finalize・§holdout / brief P1・P4) / 主張: 新 receipt 自身が holdout unknownness scanを汚せる。`confirmed_by` は任意の内部文字列を許すので、許可された一つの値に rr80 の三軸文字列を入れれば conjunction hitになる。finalizeは confirmation置換前に再検証し、置換後の active bytesで scanし直さない。 / 根拠: [plan_v1.md:54](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:54)、[plan_v1.md:178](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:178)、[plan_v1.md:271](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:271)。scanは tracked/untracked全 fileを列挙し [s8b_holdout_freeze.py:179](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:179)、除外は `output/s8b-freeze/` だけ [s8b_holdout_freeze.py:27](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:27)、一 file内の三軸存在を hitとする [s8b_holdout_freeze.py:270](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:270)。 / 放置した場合: schema/topology上 validなreceiptの発行直後に holdout refusalが復活し、期待 exact 2 が 3 以上へ変わる。 / 修正案: 検証済み canonical receiptの exact path＋raw hashだけを、既存 s8b prefix除外を維持したまま live scan入力から除く。final bytes生成後の scanと、悪性だがschema-validな `confirmed_by` の real-scan負例を追加する。

[9] [MAJOR] 対象 (brief P4(d) / plan §S-1・§holdout) / 主張: briefの「resolver差替えで機械再構成」は事実誤認であり、planのsnapshot修正も holdoutでは実行仕様が閉じていない。展開した単純 snapshotには `.git` がないが、`verify_document()` は `search_repository()` 経由で `git ls-files` を必ず実行する。 / 根拠: briefの主張は [brief.md:76](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/brief.md:76)、plan自身も knownの `source_resolver` 不足を認める [plan_v1.md:16](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:16)。known builderは module-global ROOT/importを使う [s1_known_axes_freeze.py:20](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:20)、resolverは source hash部分だけ [s1_known_axes_freeze.py:729](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:729)。holdout側は [s8b_holdout_freeze.py:197](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:197)、[s8b_holdout_freeze.py:683](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:683)。 / 放置した場合: valid branchが常に Git列挙エラーになるか、誤って現 working treeを読んで H_mig proof参照が崩れる。 / 修正案: detached read-only worktreeを作るか、H_mig tree modeから導いた exact file列を `files=` に注入するかを固定し、untracked、gitlink、symlink、ccbench treeの扱いまで schema化する。

[10] [BLOCKER] 対象 (plan §ユーザー引き渡し / brief P3) / 主張: 発行後受入手順が成立していない。briefは wave成果物に draft生成を含めるが、planはユーザーに初回生成させる。R 後は receipt verifyと gate-checkしか走らず、full suite・docs/codex/provenance checksを再実行しない。しかも期待どおり2 refusalの gate-checkは rc=2で終了するため、そのままでは成功コマンドにならない。失敗時に R をどう破棄し、新 H_migから再発行するかもない。 / 根拠: [brief.md:72](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/brief.md:72)、[brief.md:103](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/brief.md:103)、[plan_v1.md:572](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:572)、[plan_v1.md:619](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:619)。CLIの refused rc=2 は [s8b_oracle_driver.py:1345](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1345)。全走コマンドは [orchestrator/tests/README.md:16](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/README.md:16)、commit後検査は [AGENTS.md:26](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/AGENTS.md:26)。`AI-Agent: none` 自体は checkerが受理する [check_ai_provenance.py:67](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_ai_provenance.py:67)。 / 放置した場合: receipt-only R が作られた後に real-repo有効branchが赤でも検出せず、期待された rc=2を手順失敗と誤認するか、そのままpushできる。 / 修正案: AI commit後に draft生成・validateまで済ませてhandoffし、R 後に rc=2＋exact JSONを明示assert、full suite、3 check scriptを実行する。失敗時はpush前に R を履歴から除き、修正済み新 H_migで draft/Rを再生成する復旧線を明記する。

[11] [MAJOR] 対象 (plan U5・§handoff / brief P3) / 主張: canonical docsは R 発行後も「receipt待ち」のまま残る。R はreceipt 1 fileだけの commitでなければならず、handoff後に状態を更新するcommitも計画されていない。 / 根拠: [plan_v1.md:465](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:465)、[plan_v1.md:610](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:610)。正本は T-068 を発効時に閉じる [worklog.md:79](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:79)。 / 放置した場合: gateは2 refusalなのに worklog/phaseは4 refusal前提と T-068未了を指し続け、次 waveの参照状態が分裂する。 / 修正案: R とpost-R全受入後、push前に activation SHA・2 refusal・T-068/T-077/T-078状態を記録する専用docs commitを置き、receipt履歴検証をその descendant HEADでも再実行する。

[12] [MAJOR] 対象 (plan U1/U3・§テスト計画 / brief §並列分割) / 主張: ファイル所有は素集合でない。U1とU3がともに `test_s8b_oracle_driver.py` を所有し、U1の conftest/golden更新はU3による node削除に依存する。さらに「既存2618 nodeを削除しない」と書きながら、その nodeを明示削除する。 / 根拠: [plan_v1.md:390](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:390)、[plan_v1.md:415](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:415)、[plan_v1.md:505](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:505)。現 node は conftestと独立goldenの両方にある [conftest.py:79](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/conftest.py:79)、[test_real_repo_serialization.py:54](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_real_repo_serialization.py:54)。 / 放置した場合: 並列commit順で real-repo readerが非直列化され、最終成果物では既存検査nodeが一つ消える。 / 修正案: U1/U3を統合するか `test_s8b_oracle_driver.py` をU1だけに所有させる。既存node名は維持し、valid receipt下で真の単一理由tamper testへ書き換える。

[13] [MAJOR] 対象 (plan U4/U5 / brief P6・成果物一覧) / 主張: consumer/test/docsのファイル表が不完全で所有監査できない。U4はproduction fileだけを書き「既存test」と総称し、実際に編集する `test_s1_measurement_freeze.py`、`test_s1_verify_extime_calibration.py`、`test_s1_report.py` を列挙していない。`s1_direct_comparison.py` とそのtestも脱落している。新 `test_t080_freeze_migration.py` の自走harnessも明記されず、新 namespaceは `output/README.md` に追加されない。 / 根拠: [plan_v1.md:457](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:457)、[plan_v1.md:465](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:465)。direct comparisonはmeasurement verifierを直接消費する [s1_direct_comparison.py:115](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_direct_comparison.py:115)、D75の波及表にも明記される [freeze-permanent-design.md:338](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:338)。新 testの自走条件は [decisions.md:3041](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:3041)、meta-testは [test_plain_runner_coverage.py:60](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_plain_runner_coverage.py:60)。現 output地図に当該namespaceはない [output/README.md:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/README.md:5)。 / 放置した場合: legacy callerへの意味論漏れと偽緑 test fileが変更一覧外になり、repository地図もreceiptの正本pathを示さない。 / 修正案: production/testを一対一でexact列挙し、direct comparison系を追加する。新testには自走harnessを必須化し、output地図と保護外である境界を文書化する。

[14] [MAJOR] 対象 (plan §no-touch受入 / brief 不変条件2) / 主張: no-touchコマンドは不変証明にならない。`git diff` はworktree対indexだけなので staged/committed変更を見ず、V1を参照する `s8b_selector_freeze.py`、`test_s8b_ratified_freeze.py`、`test_s8b_ratified_verify.py`、`test_s8b_approved.py` も対象外である。 / 根拠: [plan_v1.md:546](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:546)。selectorのtrust root消費は [s8b_selector_freeze.py:735](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:735)、legacy root testは [test_s8b_ratified_freeze.py:958](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_freeze.py:958)、approved equalityは [test_s8b_approved.py:65](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_approved.py:65)。 / 放置した場合: V1 trust root・旧許可表・その検出testを同時変更しても「no-touch証明」が0終了し、参照値と受理集合を変えられる。 / 修正案: implementation base SHAを固定して `git diff BASE..HEAD -- <exact files>` を使い、`rg -l V1_FREEZE_SHA256` から確定したproduction/test全fileをmanifest化する。

[15] [MAJOR] 対象 (plan §変異テスト事前登録 / F28) / 主張: surplus repin変異はF28を満たさない。`source_repins` はschema段で exact 13件なのに、候補は14件目を追加するため、surplus closure検査より前にschema countで落ちる。 / 根拠: exact 13 schemaは [plan_v1.md:44](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:44)、[plan_v1.md:92](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:92)、変異候補は [plan_v1.md:516](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:516)。F28の二条件は [failures.md:343](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/failures.md:343)。 / 放置した場合: surplus検査を無効化しても入力はschema refusalのままで、受理集合を変えない変異をkill候補として数える。 / 修正案: この候補は削除する。13件を保った置換案もmissing/reconstructionの複数理由へ波及するため、実コードの検査順が確定するまで事前登録しない。

[16] [MINOR] 対象 (plan §source_repins exact schema) / 主張: `json_pointer` 表記が自己矛盾している。known 12件は先頭 `/` なし、holdoutとmetadataは先頭 `/` ありで、同一fieldをJSON Pointerとして一意に解釈できない。 / 根拠: field定義は [plan_v1.md:80](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:80)、known例は [plan_v1.md:96](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:96)、holdout/metadata例は [plan_v1.md:103](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:103)、[plan_v1.md:127](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v1.md:127)。 / 放置した場合: receipt canonical bytesと changed-pointer集合が実装ごとに異なり、同じartifactに対する参照identityが割れる。 / 修正案: RFC 6901形式の `/entries/...` に全件統一し、escape規則もschemaへ明記する。

## P1..P7 裁定

| 裁定 | 判定 | 根拠 |
|---|---|---|
| P1 | 否認 | sidecar/H_mig方向だけでは不十分。現在path依存、一回限り履歴不足、D76 namespace衝突がある（[1][2][4]）。 |
| P2 | 否認 | 「不在」が never-issued と deleted-after-issued を区別せず、後者を旧4拒否で受理する（[1]）。 |
| P3 | 否認 | human commit形式だけでは履歴不変・post-R全受入・復旧・状態記録を満たさない（[2][10][11]）。 |
| P4 | 否認 | (a)(c)(e)の方向は維持可能だが、複合裁定の(d) resolver案はコード上成立せず、snapshot実行仕様も未完。holdout scan汚染も残る（[8][9]）。 |
| P5 | 否認 | observationを全欠落させても受理され、judgeへ到達せず、現行v1/D76将来schema双方と整合しない（[4][5][6]）。 |
| P6 | 採用 | oracle専用adapterに限定し、measurement/calibration/reportをlegacy strictのまま残す境界自体はT-083のofficial-consumer限定と整合する。ただし direct comparisonを含む波及表の補完は必須（[13]）。 |
| P7 | 否認 | exact fixture pathを外し、禁止されたfixture-bytes mutantを採っているため、承認済みT-078充足形ではない（[7]）。 |

## 総合判定

**NO-GO。** 特に [1][2][4][5][7][8][10] を直さない限り、receipt発行後の受理集合、将来Wの参照、observationの耐久性、ユーザー受入のいずれも成立しない。

## §5 親裁定 J1..J13

# 段 4 親裁定 — [T-080] 移行契約 wave (plan v2 への指令)

相談 = consult_correctness.md (C1-1..C1-11) / consult_coherence.md (C2-1..C2-16)。両 NO-GO。
裁定: refuted 0 / 採用 (原形または適応形) 24 / scope 外へ回す 3。P1..P7 は全て改訂の上で維持または差替え。

## J1. 実行アーキテクチャの変更 (C1-2, C1-6, C2-9 採用 — snapshot 実行の全廃)

H_mig snapshot 上でのコード実行 (旧コード復元実行) は**全廃**する。代替:

- **draft 生成時は worktree == H_mig かつ clean を必須にする** (draft CLI が rev-parse HEAD 一致 +
  dirty 拒否)。この時点の機械再構成は「現行 in-tree コードの直接実行」になる — snapshot 不要:
  - S-1: 現行 `s1_known_axes_freeze.build_document(frozen_at_head=legacy, ccbench_pin=legacy,
    python_version=legacy, generator_sha=legacy記録値)` を実走し、legacy doc に receipt の 12 cell を
    overlay したものとの deep equality を検査する (generator cell は両側除外 = M 化)。**不一致なら
    draft 生成自体が fail-closed** — 再構成に合格しない限り receipt は存在し得ない
  - holdout: 現行 `verify_document` の静的部分 (schema/定数/層1/binding) を projected doc (design/
    generator cell を H_mig 値へ overlay) で実走 + 現行 `search_repository` の層2 実走
  - 実行結果 (pass + 対象 doc の sha256) は receipt の `reconstruction` field に束縛する
- **gate 検証時 (毎回) は静的検査のみ**: (a) freeze JSON raw bytes == receipt pin (byte-exact)、
  (b) S-1 63 cell + holdout design cell の H_mig blob 照合 (hardened git cat-file、コード実行なし)、
  (c) ancestry 4 分類 → observation、(d) **ccbench_pin == 現 submodule HEAD (live 維持)** + H_mig
  gitlink 一致、(e) **holdout unknownness 層2 の live scan (現行 in-tree コード) 維持**、
  (f) 現行 in-tree の schema 検査 + `assert_s1b_pairing` (pure 関数)
- 「機械再構成検査の維持」の充足形 = 移行時 1 回の実走 + 証拠の receipt 束縛 + 以後の byte-pin。
  gate 内で再構成を permanent に再実行しない理由 (再実行は旧コード実行を要求し C1-6 の攻撃面になる)
  を D78 に明文化する。ccbench_pin と層2 は gate 内 live のまま — D73 (2) の「後段恒久マスク」は
  起きない

## J2. receipt 状態機械 (C1-4, C2-1 採用)

4 状態: `never-issued / active-valid / issued-but-missing / invalid`。判定は H_v (検証開始時に 1 回
捕捉した HEAD) の reachable history から:

- history に導入 commit R が存在しない + path 不在 = never-issued → legacy 挙動 (現行 4 拒否)
- R が存在 + 現 blob == R blob + 全検証合格 = active-valid → 移行後挙動
- R が存在 + path 不在/blob 不一致/後続の M/D/R/C/T = issued-but-missing → **明示 refusal**
  (legacy へ戻さない)
- path 存在 + 検証不合格 = invalid → 明示 refusal
- draft CLI の前提「未発行」も history 検査で判定 (削除による巻き戻し不能)

## J3. Git hardening (C1-3, C2-2 採用)

`s8b_ratified_freeze` の hardened primitive (core.useReplaceRefs=false、shallow/graft/replace 拒否、
環境 sanitize、reachable history の blob 列検査) と同等以上を **同 module の関数再利用または同一
契約の T080 module 内実装**で使う。merge-base は rc 保持の専用 runner。ancestry 分類は
`cat-file --batch-check` で type 判別 (D73 (3) の 4 分類そのまま)。H_v は 1 回捕捉。

## J4. 検査継続契約 (C1-5 採用)

adapter は fail-fast しない — 全層 (bytes/closure/ancestry/ccbench/層2/schema) を実行して refusal と
observation を**蓄積**して返す。anchor refusal 後も ccbench/closure 検査は必ず実行される。

## J5. namespace 隔離と W-X retirement (C2-3, C2-4 採用)

- receipt path = `output/t080-migration/legacy-freeze-repin.receipt.json` (恒久 namespace
  `output/freeze-migrations/` を使わない — S2-1.13 未知 file 拒否と衝突するため)
- adapter 発火条件 = 「holdout raw bytes == receipt pin かつ known record が legacy path+hash」に
  限定。それ以外は現行 legacy 検証へ (fail-closed)
- D78 に W-X 時の retirement 契約を明文化: X 発効で T-080 adapter は撤去対象、receipt は歴史成果物
  として保持 (bytes 不変)、g1 bundle が pin を引き継ぐ

## J6. observation 伝播の実効化 (C1-8, C2-5, C2-6 採用 — 適応形)

- receipt 解決は gate_check / run_block の最外層で 1 回。全 GateDecision 生成を observation 必須の
  共通 factory 経由にする (早期 return も欠落させない)
- WAL campaign-start: key 常時書込 (null | envelope)。key-absent = R 導入前の歴史 WAL の grammar と
  して report builder が区別する
- oracle report: 既存 `8b-oracle-observations/v1` envelope には**触れない**。report の新設 sibling
  top-level field へ転記 + 「receipt active なのに campaign-start に envelope 欠落/null」は当該 row
  を protocol_violation 化 (judge は既存機構で indeterminate へ倒れる — judge 本体は変更しない)
- gate-attempt 台帳の新設は**不採用** (G2/G3 過剰。receipt commit 自体が発効の耐久記録。理由を D78 に
  明記)

## J7. 人間同席の実質 (C1-7 採用 — 適応形。署名は §14 限界で裁定済みのため不採用)

- receipt に `repin_report` を束縛: 13 repin の各件について「旧 hash が HEAD 履歴のどの commit の
  blob として実在するか (provenance_resolved: <commit> | provenance_unverified)」+ 旧→新の
  diff 行数概要。ユーザーは opaque hash でなくこのレポートを確認する (R14 の「digest + 添付レポート
  確認」と同型)
- `confirmed_by` は `^[A-Za-z0-9._-]{1,64}$` に制限 (C2-8 の scan 汚染も同時に殺す)
- 署名 commit は不採用 — §14 限界「人間承認は暗号署名ではない」の承認済み裁定を D78 で再掲

## J8. receipt の scan 非汚染 (C2-8 採用)

- schema で構造的に保証: 全 field は固定 literal / hex hash / repo path / 制限付き identifier のみ。
  自由文 field を置かない (repin_report の diff 概要も数値 + path のみ)
- EXCLUDED_PATHS は変更しない (凍結 doc 記録値のため変更不能)
- draft/finalize の最終 bytes 生成後に search_repository を実走して pass を assert + 「schema-valid
  だが軸文字列を含む receipt」の hermetic 負例テスト

## J9. T-078 の充足形 (C1-9, C2-7 採用 — D76 S2-4.6 の exact 契約へ差替え)

- fixture path/root key/bytes/sha256 は S2-4.6 の承認値をそのまま使う:
  `orchestrator/tests/data/freeze_holdout_positive_control_v1.txt` / `positive-control/rr50/v1` /
  caee6dea…。**fixture bytes の mutate は禁止 — mutant は検索 predicate 単独** (baseline 1 hit →
  predicate mutant 0 hit → revert 1 hit、fixture のみを検索対象にした direct test)
- literal 三面の恒久機構 (freeze_permanent_roots.py shell 等) は**先取りしない**。最小形 =
  production 側 literal 1 file (T080 scope、fixture path+root key+sha256 を pin) + test 側 golden を
  **別 file・別 commit** に分離。W-a 到達時に fixture/キーは同一値のまま吸収される
- 既存 node 名 `test_tampered_freeze_fails_source_verification` は**維持**し、valid-receipt fixture 下の
  真の単一理由 tamper 検査 (confirmed_by 改変 → holdout-freeze-verify 1 件のみ) へ書き換える
  (golden 2 面の node 名 literal を動かさない — C2-12)

## J10. 引き渡し手順の完全化 (C2-10, C2-11 採用)

- AI が wave 最終 commit (= H_mig) 直後に draft 生成 + validate まで実行して引き渡す
- ユーザー手順: repin_report 確認 → finalize → R commit (receipt 1 file、AI-Agent: none) →
  **post-R 受入 = gate-check が rc=2 かつ refusals == {floor-null, budget-null} exact の assert +
  full suite + check_docs/check_codex_agents/check_ai_provenance** を手順に含める
- 失敗時の復旧線: push 前なら `git reset --hard HEAD~1` で R を落とし、修正 → 新 H_mig → draft 再生成
  (push 後の履歴書換えはしない — その場合は新 receipt で supersede)
- docs は状態中立に書く (「機構実装済み・receipt 発行待ち。発効後の期待 = 2 拒否」) — 発効前後の
  どちらでも正。発効イベントの worklog 記録は発効後の次セッションが行う旨を引き渡しに明記

## J11. 所有・no-touch・列挙の完全化 (C1-11, C2-12, C2-13, C2-14 採用)

- brief の所有表を adapter-only へ訂正 (legacy checker 2 本は no-touch へ移す)
- no-touch 証明 = `git diff <wave開始SHA 0e7b081>..HEAD -- <manifest>` で、manifest =
  凍結 3 JSON + test_frozen_artifacts.py + s8b_ratified_freeze.py + s8b_approved.py +
  test_s8b_approved.py + test_s8b_ratified_freeze.py + test_s8b_ratified_verify.py +
  s8b_selector_freeze.py + s1_known_axes_freeze.py + s8b_holdout_freeze.py
- U4 のテスト file を exact 列挙 (test_s1_measurement_freeze.py / test_s1_verify_extime_calibration.py /
  test_s1_report.py / s1_direct_comparison 系)。output/README.md へ新 namespace を登録。
  新テストは自走 harness 対応 (test_plain_runner_coverage の対象規約に従う)
- test_s8b_oracle_driver.py の所有は 1 単位に限定 (U1)。node 追加/改名/削除の台帳を完了報告に必須化

## J12. 変異事前登録の扱い (C2-15 採用)

- surplus repin 変異は削除 (schema 件数検査が先行し F28 違反)
- plan v1 の候補は J1 のアーキテクチャ変更で失効するものがある — plan v2 で再登録し、B-057 確定は
  実装開始時のコード読解後 (candidate → confirmed の 2 状態、D76 と同じ)
- 新規必須: (i) draft の再構成 equality 無効化 → draft が不正 doc で成功する (kill 期待 =
  hermetic fixture で fail)、(ii) 状態機械の issued-but-missing → absent 化 → 発効後削除が受理される、
  (iii) predicate 単独 mutant (J9)

## J13. schema 細部 (C2-16 採用)

json_pointer は RFC 6901 (先頭 `/`、escape 規則明記) に全件統一。

## 承認済み損失の再掲 (C1-1, C1-7 — 新規裁定ではなく D75/D76 §14 の履行)

- 「G 後の current worktree source drift の受理」は §14 損失表 5 行目 (R7(b) 帰結) として承認済み。
  receipt と D78 に同表への参照を再掲する。移行契約はこの承認済み損失を legacy 2 成果物へ前倒し
  適用するものであり、受理集合の拡大は新規裁定事項ではない
- 「人間承認は暗号署名ではない」も §14 限界で承認済み

## scope 外 (裁定パッケージとしてユーザーへ返さず、W 列の既承認設計に既含のため記録のみ)

- S-1 再構成の独立参照実装 (R4 — oracle 後の W 列)
- calibration/report consumer の proof chain 統合 (D72 (8) の完全形 — W-d)
- gate-attempt 耐久台帳 (不採用理由は J6)


## §6 プラン v2 (確定版)

# [T-080] 移行契約 wave 実装プラン v2

結論は実装着手可能です。v1 の「legacy checker／凍結 JSON 無変更・oracle 専用 adapter・sidecar receipt・素集合単位」の骨格を維持しつつ、snapshot 実行は完全撤去します。再構成は clean な H_mig worktree 上で draft 時に一度だけ実走し、gate は静的 closure と live ccbench／unknownness 層2に限定します。[ruling_v2.md:6](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/ruling_v2.md:6)

read-only のため、この回答ではファイルを変更していません。

## 裁定への異議

2点だけ、裁定本文を逐語どおり同時充足できない箇所があります。正常系の実装は妨げませんが、D78 に限定解釈を記録します。

1. J8 の「schema-valid だが軸文字列を含む receipt」は、exact 13 path、固定 literal、`confirmed_by=^[A-Za-z0-9._-]{1,64}$` を含む完全な意味 schema を通った receipt では構成不能です。[ruling_v2.md:74](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/ruling_v2.md:74) [ruling_v2.md:83](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/ruling_v2.md:83)  
   v2 では「exact key/type/path 文法を通るが、closure の固定値照合前で止まる構造 schema-valid fixture」と解釈します。完全 verifier では closure 不一致でも拒否され、live scan でも軸汚染を拒否する二重負例です。もし「全 semantic 検証合格」を意味するなら J7/J8 自体の改訂が必要です。

2. J10 の push 後「新 receipt で supersede」は、J2 の導入後 M/D/R/C/T 拒否と J5 の単一固定 path に反します。[ruling_v2.md:29](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/ruling_v2.md:29) [ruling_v2.md:104](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/ruling_v2.md:104)  
   push 後は同 path を変更せず停止し、別 path/schema を持つ人間裁定済みの修復 wave を「supersede」と解釈します。T-080 CLI に in-place supersede は実装しません。

## 1. 検査意味論の exact 仕様

### 1.1 4状態の判定

正本 path は `output/t080-migration/legacy-freeze-repin.receipt.json`。検証開始時に hardened Git で HEAD を一度だけ H_v として捕捉し、その reachable DAG 全体を調べます。

判定順は次で固定します。

1. H_v の全 reachable commitについて receipt path の tree entryを batch `cat-file --batch-check` で列挙する。
2. 「自身で path が blob、全 parent で absent」の commit を導入 commit 候補とする。
3. 導入候補ゼロの場合:
   - H_v tree、worktree の双方で path absentなら `never-issued`。
   - worktreeに未追跡 pathがある、H_v treeがpresent、read/lstat不能なら `invalid`。
4. 導入候補が1件以上の場合:
   - 一意でなければ `issued-but-missing`。
   - 一意な候補を R とし、R blobをstrict parseする。
5. R 以後の全 descendantで path blobがR blobと同一であること、および `diff-tree -M -C` に receipt pathを対象とする M/D/R/C/T がないことを検査する。
6. H_v blob、R blob、nofollowで読んだworktree bytesが全て一致しなければ `issued-but-missing`。
7. Rが非merge、唯一のparentがreceipt記録のH_mig、diffがreceipt 1 fileのAだけ、trailerが逐語 `AI-Agent: none` でなければ `invalid`。
8. schema・canonical bytes・closure・H_mig・artifact・reconstruction証拠・全gate検査に合格すれば `active-valid`、それ以外は `invalid`。

状態ごとの挙動は次です。

| state | gate |
|---|---|
| `never-issued` | legacy verifierをそのまま使用。現実repoでは既存4拒否 |
| `active-valid` | T-080 adapterを使用。期待拒否はfloor/budgetの2件 |
| `issued-but-missing` | `migration-receipt-verify`を必ず追加。legacyへ戻さない |
| `invalid` | `migration-receipt-verify`を必ず追加。silent fallback禁止。可能な独立検査は継続 |

`draft` の発行前条件もこの状態機械を使い、`never-issued` 以外を拒否します。削除後の再発行はできません。

### 1.2 hardened Git

既存実装の次の契約をT-080 module内へ同型移植します。legacy checkerおよび ratified moduleは編集しません。

- `core.useReplaceRefs=false`を全Git呼出しへ付与する契約: [s8b_ratified_freeze.py:269-303](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:269)
- shallow／replace refs／grafts拒否と単一HEAD捕捉: [s8b_ratified_freeze.py:306-325](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:306)
- reachable graph: [s8b_ratified_freeze.py:410-426](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:410)
- commitごとのblob列挙: [s8b_ratified_freeze.py:429-453](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:429)
- immutable introduction／一意導入: [s8b_ratified_freeze.py:456-481](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:456)、[s8b_ratified_freeze.py:561-570](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:561)
- Rのdiff、parent、blob: [s8b_ratified_freeze.py:573-607](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:573)
- `AI-Agent: none`のraw＋parsed二重判定: [s8b_ratified_freeze.py:484-536](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:484)

T-080版はさらに次を追加します。

- `GIT_*`入力環境を全除去し、`GIT_CONFIG_NOSYSTEM=1`、global config無効、`GIT_TERMINAL_PROMPT=0`、`GIT_OPTIONAL_LOCKS=0`を固定。
- `.git/objects/info/alternates` の存在も拒否。
- `GIT_DIR`、`GIT_WORK_TREE`、`GIT_OBJECT_DIRECTORY`、`GIT_ALTERNATE_OBJECT_DIRECTORIES`等を継承しない。
- merge-base専用runnerはrcを潰さず、0/1/>1を返す。
- blob／commit型判定はstderr文言ではなくbatch-checkの型で行う。

legacy ancestryは以下の4分類です。

| 判定 | 結果 |
|---|---|
| object missing | observation `missing-commit` |
| object typeがcommit以外 | refusal |
| commitかつmerge-base rc=0 | observation `ancestor` |
| commitかつmerge-base rc=1 | observation `not-ancestor` |
| Git起動失敗、rc>1、I/O異常 | refusal |

anchor refusal後もclosure、ccbench、live scan、schemaを続行します。D73が記録した後段マスクは残しません。[decisions.md:2863](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2863)

### 1.3 draft時の再構成

新moduleの関数境界を次で固定します。

```text
draft_receipt()
 ├─ _capture_draft_basis()
 ├─ _derive_repins_and_metadata()
 ├─ _build_repin_report()
 ├─ _draft_reconstruct_known_axes()
 ├─ _draft_reconstruct_holdout()
 ├─ _encode_canonical_receipt()
 └─ _assert_receipt_does_not_pollute_scan()
```

`_capture_draft_basis()`:

- `rev-parse HEAD == --basis == H_mig`
- rootの `git status --porcelain=v1 -z --untracked-files=all --ignore-submodules=none` が空
- receipt history stateが`never-issued`
- H_migがcommit object
- H_mig treeの`external/ccbench`がmode 160000でlegacy `ccbench_pin`
- current submodule HEADも同じpin

`_draft_reconstruct_known_axes()`:

1. legacy documentをstrict loadする。
2. 現行in-treeの [build_document():608-679](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:608) を次の引数で直接実行する。

   ```python
   build_document(
       frozen_at_head=legacy["frozen_at_head"],
       ccbench_pin=legacy["ccbench_pin"],
       python_version=legacy["python_version"],
       generator_sha=legacy["generator"]["sha256"],
   )
   ```

3. legacy copyへreceiptのknown 12 cellだけをoverlayする。
4. projected／rebuilt両方から `/generator/sha256` だけを除外する。`generator/path`は残す。
5. [assert_s1b_pairing():575-605](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:575) をprojected側にも実行する。
6. deep equalityを要求する。不一致ならreceipt bytesを一切生成しない。
7.両比較viewのcanonical SHA-256をreceiptへ記録し、2値が同一であることを要求する。

`_draft_reconstruct_holdout()`:

1. legacy holdout copyへ `/design_source/sha256` と `/generator/sha256` のH_mig値をoverlayする。
2. clean worktreeがH_migそのものなので、現行 [verify_document():683-823](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:683) をprojected docへ直接実行する。
3. `current_head=legacy["frozen_at_head"]` とし、ancestryだけを別classifierの責務にする。
4. この呼出しによりschema、定数、unknownness層1、confirmation、binding、現行 [search_repository():297-377](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:297) の層2を一度実走する。
5. projected docのcanonical SHA-256とlive scan report SHA-256をreceiptへ記録する。

H_migのarchive、detached worktree、旧module import、`python -I` subprocessは一切作りません。

### 1.4 gate時の検査

`active-valid`かつ次を満たす場合だけT-080 adapterを発火します。

- 入力holdoutのraw SHA-256がreceiptのholdout pinと一致。
- `known_axes_freeze` recordがlegacy path
  `output/s1-freeze/known_axes_freeze.json`
  とhash
  `354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516`
  にexact一致。

それ以外は現在のlegacy/v2分岐へ渡します。ただしreceipt自体がissued/invalidなら、その明示refusalは消しません。

S-1 adapterは毎gateで次を全件実行します。

1. known raw bytesのreceipt pin照合。
2. H_mig blobによる全63 source cell照合。
3. changed 12／unchanged 51／duplicate・missing・surplusなし。
4. legacy ancestry分類。
5. current ccbench HEADとlegacy pinのlive一致。
6. H_mig gitlinkとlegacy pinの一致。
7. 現行in-tree `_validate_schema()` と `assert_s1b_pairing()`。
8. receiptのprojected reconstruction hashを静的再計算し、draft記録と一致。
9. generator SHA equalityは行わずmetadata observationだけ生成。

holdout adapterは毎gateで次を全件実行します。

1. holdout raw bytesのreceipt pin照合。
2. H_mig design blobとrepinの一致。
3. known_axes recordのlegacy raw root一致。
4. generator path・H_mig metadata hashの整合。current generator equalityは行わない。
5. legacy ancestry分類。
6. top-level schema、定数、floor/budget/refreeze note、search schema、unknownness層1、confirmation、bindingの静的検査。
7. D76承認済みpositive fixtureのraw root検査。
8. 現行in-tree `search_repository()`＋`_assert_search_pass()`による層2live scan。

再構成builderはgateから呼びません。receiptに記録された`status == "pass"`、projected hash、known側のprojected/rebuilt hash一致だけを静的検査します。

### 1.5 refusalとobservation

reason codeはD76の一ドットgrammarへ合わせます。[freeze-permanent-design-s2.md:1311](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:1311)

exact prefixは次です。

```text
migration-receipt-verify: [receipt.
known-axes-freeze-verify: [known_axes.
holdout-freeze-verify: [holdout.
floor-null:
budget-null:
manifest-verify:
```

主要reasonは以下です。

```text
receipt.issued_but_missing
receipt.invalid
receipt.history_mutated
receipt.multiple_introduction
receipt.canonical_mismatch
receipt.schema_invalid
receipt.confirmation_invalid
receipt.basis_invalid
receipt.repin_invalid
receipt.reconstruction_invalid

known_axes.artifact_bytes
known_axes.source_closure
known_axes.ancestry_object_type
known_axes.ancestry_git_error
known_axes.ccbench_current
known_axes.ccbench_gitlink
known_axes.schema
known_axes.pairing

holdout.artifact_bytes
holdout.design_closure
holdout.ancestry_object_type
holdout.ancestry_git_error
holdout.schema
holdout.unknownness_layer1
holdout.unknownness_layer2
holdout.binding
holdout.positive_control
```

active production repoのrefusalは順序も含め次の2件です。

```text
floor-null: freeze.floor が null
budget-null: freeze.budget が null
```

observation keyは全層でexact `t080_freeze_migration_observation`。値はnullまたはexact 6-field objectです。

```json
{
  "schema_version": "izanagi-t080-freeze-migration-observation/v1",
  "migration_id": "T-080",
  "receipt": {
    "path": "output/t080-migration/legacy-freeze-repin.receipt.json",
    "raw_sha256": "<64hex>"
  },
  "migration_basis_commit": "<H_mig>",
  "validation_head": "<H_v>",
  "items": []
}
```

`items`はactive時exact 17件です。

- source repin 13件: status `repinned-to-basis-blob`
- generator 2件: status `metadata-only`
- ancestry 2件: status `missing-commit | not-ancestor | ancestor`

各itemはexact `{artifact,kind,subject,recorded,observed,status}`。順はsource_repins 13、metadata 2、known／holdout ancestry 2。missing commitの`observed`だけnullです。

### 1.6 observationの全経路結線

[GateDecision:81-85](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:81) を3必須fieldにし、defaultを置きません。

```python
GateDecision(
    allowed=...,
    refusals=...,
    t080_freeze_migration_observation=...,  # nullも明示
)
```

productionでの直接構築は禁止し、`_make_gate_decision(resolution, ...)`だけを使います。AST testでfactory外の`GateDecision(...)`を拒否します。

resolverは `gate_check()` と `run_block()` の最外層で各1回です。現在の早期returnのうち、次を全てfactoryまたはfactory済みdecisionへ置換します。

- gate core終端: [s8b_oracle_driver.py:288](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:288)
- standalone gate: [303-318](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:303)、[325-365](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:325)
- validated gate: [373-384](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:373)
- ratified解決の2 return: [882-899](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:882)
- launch validationの2 return: [900-911](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:900)
- freeze read／root mismatch: [915-929](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:915)
- gate／manifest return: [948-960](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:948)
- prepareの2 return: [984-997](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:984)
- claim return: [999-1021](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:999)
- 成功／terminal result: [1306-1319](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1306)

campaign-startにはkeyを常時書きます。[s8b_oracle_driver.py:1027-1034](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1027)

reportは既存`8b-oracle-observations/v1`を変更せず、top-level sibling `t080_freeze_migration_observation`を追加します。[s8b_oracle_report.py:1238-1289](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1238)

- R未導入: key-absentをhistorical WAL、nullを現行never-issuedとして許容。
- R導入済み: key-absent、null、malformed、campaign間不一致は該当campaignの全rowを`protocol_violation`。
- 全campaignで同一canonical envelopeならsiblingへ転記。
- violation時のreason prefixはexact `t080-freeze-migration-observation: `。
- judge本体は変更しない。protocol rowにより既存ロジックが`indeterminate`を返します。[s8b_oracle_judge.py:220-267](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_judge.py:220)

## 2. receipt exact schema

### 2.1 配置

```text
active:
output/t080-migration/legacy-freeze-repin.receipt.json

untracked handoff draft:
output/t080-migration/legacy-freeze-repin.receipt.draft.json
```

恒久namespace `output/freeze-migrations/` は使いません。[ruling_v2.md:53](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/ruling_v2.md:53)

### 2.2 top-level

exact 10 fields、追加field禁止です。

| field | exact契約 |
|---|---|
| `schema_version` | `"izanagi-t080-legacy-freeze-repin/v1"` |
| `migration_id` | `"T-080"` |
| `migration_basis_commit` | lowercase 40hex H_mig |
| `artifacts` | exact keys `known_axes`,`holdout` |
| `source_repins` | exact 13 element |
| `metadata_fields` | exact 2 element |
| `reconstruction` | exact keys `known_axes`,`holdout` |
| `repin_report` | exact 13 element |
| `confirmed_by` | draft null、activeは指定regex |
| `confirmed_at` | draft null、activeはUTC秒精度 |

confirmationは両方nullまたは両方non-nullのみ。`confirmed_by`はexact `^[A-Za-z0-9._-]{1,64}$`。`confirmed_at`は実在日時をUTC parse／roundtripし、`YYYY-MM-DDTHH:MM:SSZ`以外を拒否します。

### 2.3 artifacts

各artifactはexact `{path,raw_sha256,recorded_frozen_at_head}`。

| key | path | raw_sha256 | recorded head |
|---|---|---|---|
| known_axes | `output/s1-freeze/known_axes_freeze.json` | `354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516` | `2066ce6b47c6a5d43ca2c8ab3cc7728d32336be1` |
| holdout | `output/s8b-freeze/holdout_freeze.json` | `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688` | `2e20d441aaf7ae267e941ecda09e4b53050943cf` |

既存rootは [test_frozen_artifacts.py:33-50](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:33) と [s8b_ratified_freeze.py:60-62](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:60) の値をそのまま使用します。

### 2.4 source_repins

各elementはexact 5 fieldsです。

```text
artifact
json_pointer
path
recorded_sha256
migration_blob_sha256
```

配列順はartifact=`known_axes`,`holdout`、その内側は`json_pointer`のUnicode code point昇順です。

| artifact / json_pointer | path | recorded_sha256 |
|---|---|---|
| known `/entries/balanced/ident_all/sources/3/sha256` | `orchestrator/campaign/s8a_trigger_sweep.py` | `3e94735a…` |
| known `/entries/balanced/sort_best/sources/5/sha256` | `orchestrator/campaign/s6_sort_sweep.py` | `0c7dcd30…` |
| known `/entries/balanced/sort_best/sources/6/sha256` | `orchestrator/campaign/p3_s4_loop_sort.py` | `9b64f34b…` |
| known `/entries/balanced/system_gate/sources/4/sha256` | `orchestrator/campaign/s8a_trigger_sweep.py` | `3e94735a…` |
| known `/entries/read-heavy/ident_all/sources/3/sha256` | `orchestrator/campaign/s8a_trigger_sweep.py` | `3e94735a…` |
| known `/entries/read-heavy/sort_best/sources/2/sha256` | `orchestrator/campaign/s6_sort_sweep.py` | `0c7dcd30…` |
| known `/entries/read-heavy/sort_best/sources/3/sha256` | `orchestrator/campaign/p3_s4_loop_sort.py` | `9b64f34b…` |
| known `/entries/read-heavy/system_gate/sources/4/sha256` | `orchestrator/campaign/s8a_trigger_sweep.py` | `3e94735a…` |
| known `/entries/write-heavy/ident_all/sources/3/sha256` | `orchestrator/campaign/s8a_trigger_sweep.py` | `3e94735a…` |
| known `/entries/write-heavy/sort_best/sources/5/sha256` | `orchestrator/campaign/s6_sort_sweep.py` | `0c7dcd30…` |
| known `/entries/write-heavy/sort_best/sources/6/sha256` | `orchestrator/campaign/p3_s4_loop_sort.py` | `9b64f34b…` |
| known `/entries/write-heavy/system_gate/sources/4/sha256` | `orchestrator/campaign/s8a_trigger_sweep.py` | `3e94735a…` |
| holdout `/design_source/sha256` | `docs/phase3-8b-descriptor-design.md` | `1829af7f…` |

`migration_blob_sha256`はH_mig treeの当該blobから導出します。全63 source recordを列挙し、changed集合がこの12件、unchangedが51件であることを要求します。

### 2.5 metadata_fields

各elementはexact `{artifact,json_pointer,path,recorded_sha256,migration_blob_sha256,disposition}`。

| artifact | pointer | path | recorded |
|---|---|---|---|
| known_axes | `/generator/sha256` | `orchestrator/campaign/s1_known_axes_freeze.py` | `1d4d45a3…` |
| holdout | `/generator/sha256` | `orchestrator/campaign/s8b_holdout_freeze.py` | `1910fff3…` |

`disposition`はexact `"metadata-only"`。current equalityのpass/failには使いません。

### 2.6 reconstruction

```json
{
  "known_axes": {
    "status": "pass",
    "projected_document_sha256": "<64hex>",
    "rebuilt_document_sha256": "<same 64hex>"
  },
  "holdout": {
    "status": "pass",
    "projected_document_sha256": "<64hex>",
    "live_scan_sha256": "<64hex>"
  }
}
```

`status`は`pass`以外をschema拒否し、失敗draftはそもそも生成しません。

### 2.7 repin_report

exact 13 entriesでsource_repinsと同順、各entryはexact次の7 fieldsです。

```text
artifact
json_pointer
path
recorded_sha256
migration_blob_sha256
provenance
diff_summary
```

`provenance`:

```json
{"status":"provenance_resolved","commit":"<40hex>","distance_from_basis":12}
```

または

```json
{"status":"provenance_unverified","commit":null,"distance_from_basis":null}
```

`diff_summary`:

```json
{
  "status": "diff_resolved",
  "path": "<same repo path>",
  "old_line_count": 100,
  "new_line_count": 110,
  "added_lines": 12,
  "deleted_lines": 2
}
```

unverified時はstatus=`diff_unverified`、旧側とadded/deletedの数値をnullにします。自由文やdiff本文は格納しません。

`provenance_resolved`の導出手順は次です。

1. H_mig reachable graphをhardened `rev-list --parents`で列挙。
2. unique pathごとに全commitのblob OIDをbatch取得。
3. blob bytesのSHA-256が`recorded_sha256`と一致するcommitを全件収集。
4. H_migからparent-edge最短距離をBFSで算出。
5. 最小`(distance,commit_hex)`を一意に選ぶ。
6. 候補ゼロなら`provenance_unverified`。
7. resolved時は旧／H_mig blobをstrict UTF-8で読み、`splitlines(keepends=True)`＋`difflib.SequenceMatcher(autojunk=False)`から数値だけを算出。

### 2.8 RFC 6901とcanonical bytes

全pointerはRFC 6901です。

- 先頭 `/` 必須。
- token中の`~`を`~0`、`/`を`~1`。
- array indexは先頭ゼロなし10進数。
- decode後のpointerが実際の`sha256` scalarへ到達し、再encodeが入力と一致すること。

既存RFC 6901実装契約は [s8b_ratified_freeze.py:614-634](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:614) に揃えます。

canonical bytesは次です。

```python
json.dumps(
    value,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
```

UTF-8、BOMなし、trailing newlineなし。duplicate key、NaN、Infinity、top-level非objectを拒否し、parse後の再canonical bytesとraw inputの完全一致を要求します。

## 3. CLI契約

新module:

```text
orchestrator/campaign/t080_freeze_migration.py
```

### `draft --basis H_mig --out DRAFT`

- 状態は`never-issued`のみ。
- `HEAD == H_mig`かつroot/submoduleを含めclean。
- H_mig blob closureとccbench gitlinkを確認。
- repin_reportを生成。
- S-1／holdout再構成を各1回実走。
- confirmationをnullでcanonical create-only生成。
- 出力後、実ファイルを含む`search_repository()`を実走。失敗なら自分がcreateした同一inodeだけを除去してrc=2。
- 成功rc=0。内部異常rc=1。

### `validate-draft --path DRAFT`

- H_migが現在HEAD。
- dirty許容は指定draft 1 fileだけ。
- null confirmation、canonical bytes、schema、H_mig blobs、63/12/51 closure、repin report、reconstruction hashを静的再検証。
- builderは再実行しない。
- draft bytesを含むlive scanを再確認。
- active pathが存在、またはhistoryがnever-issued以外ならrc=2。

### `finalize --draft DRAFT --confirmed-by ID --confirmed-at UTC --out RECEIPT`

- `validate-draft`を先に実行。
- confirmation 2 fieldだけを置換。
- active pathへcreate-only。
- final bytesを含めたlive scanを実行。
- source hash、report、reconstructionをCLI引数で上書きする機能は持たない。
- finalize直後・commit前の状態は意図的に`invalid`。R commit前に`verify`を成功させようとしない。

### `verify --path RECEIPT`

- H_vを一度捕捉。
- 4状態、R topology、static closure、ccbench、層2、schemaを実行。
- snapshot／builderは実行しない。
- 出力はexact `{state,refusals,t080_freeze_migration_observation}`。
- `active-valid`だけrc=0。他状態はrc=2。内部異常はrc=1。

## 4. ファイル別変更一覧と実装単位

以下は変更ファイルの完全列挙です。単位間のファイル積集合は空です。

### U0 — receipt／adapter core

- 新設 `orchestrator/campaign/t080_freeze_migration.py:1-980`予定
  - 1-110 constants、T-078 production literal、型
  - 111-260 strict/canonical/schema/RFC6901
  - 261-440 hardened Git／4状態
  - 441-570 closure／repin_report
  - 571-700 draft再構成
  - 701-860 static gate adapter／observation
  - 861-980 CLI
- 新設 `orchestrator/tests/test_t080_freeze_migration.py:1-900`予定
  - schema、state history、hardening、draft reconstruction、scan安全、CLI
  - 末尾に実テストを起動する`pytest.main([__file__])` harness

受入: 新testのpytest＋直接実行が緑、snapshot／subprocess old-code executionが0件。

### U1 — official gate統合

- [s8b_oracle_driver.py:81-85](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:81): GateDecision必須field、factory。
- [s8b_oracle_driver.py:165-288](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:165): resolver結果をcoreへ注入、legacy/adapter分岐。
- [s8b_oracle_driver.py:291-384](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:291): outer resolveと全早期return。
- [s8b_oracle_driver.py:848-1027](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:848): run_block最外層resolve、全拒否result、campaign-start。
- [s8b_oracle_driver.py:1306-1319](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1306): terminal resultへfield常設。
- [test_s8b_oracle_driver.py:531-541](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:531): real-repo 2状態golden。
- [test_s8b_oracle_driver.py:1209-1231](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1209): 既存node名を維持し、valid-resolution fixtureのconfirmed_by単独tamperへ書換え。
- 同test: factory外GateDecisionなし、全早期returnのnull/object検査。

`test_s8b_oracle_driver.py`はU1だけが所有します。`conftest.py`と`test_real_repo_serialization.py`はnode名を変えないため無変更です。[conftest.py:79-85](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/conftest.py:79)

### U2 — WAL／report伝播

- [s8b_oracle_report.py:935-1235](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:935): campaign-startのhistorical/current grammar、欠測時protocol化。
- [s8b_oracle_report.py:1238-1289](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1238): sibling field転記。`repo_root=ROOT`注入可能化。
- `orchestrator/tests/test_s8b_oracle_report.py:新規末尾`: pre-R absent/null、post-R missing/null/malformed/mismatch、judge indeterminate。
- [test_s8b_oracle_artifacts.py:121](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_artifacts.py:121): loaderがsiblingを保持するpin。

`s8b_oracle_judge.py`は変更しません。

### U3 — T-078 positive control

U0とは別commitにします。

- 新設 `orchestrator/tests/data/freeze_holdout_positive_control_v1.txt:1-3`
- 新設 `orchestrator/tests/t080_fixture_roots.py:1-30`
- [test_s8b_holdout_freeze.py:297-432](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_holdout_freeze.py:297): fixture-only baseline 1 hit → predicate-only mutant 0 → revert 1。

承認値は [freeze-permanent-design-s2.md:2058-2081](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2058) を逐語使用します。

```text
path: orchestrator/tests/data/freeze_holdout_positive_control_v1.txt
root key: positive-control/rr50/v1
bytes:
ycsb_rratio=50\n
ycsb_zipf_skew=0.9\n
ycsb_rmw=0\n
sha256: caee6deabcf6209f5e8d59ee104a64b6bcf18a2a6054b1cefd6141709802faa7
```

fixture bytesは一切変えず、`_scan_one()`へ渡すrratio predicateだけを50→51へ変異します。

### U4 — adapter漏れ防止

production 4 fileは無変更のまま、次のtestだけを編集します。

- `orchestrator/tests/test_s1_measurement_freeze.py`
- `orchestrator/tests/test_s1_verify_extime_calibration.py`
- `orchestrator/tests/test_s1_report.py`
- `orchestrator/tests/test_s1_direct_comparison.py`

固定対象consumerは次です。

- measurementがlegacy known verifyを直接呼ぶ境界: [s1_measurement_freeze.py:407-444](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:407)
- calibration: [s1_verify_extime_calibration.py:193-227](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_verify_extime_calibration.py:193)
- report: [s1_report.py:775-795](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:775)
- direct comparison: [s1_direct_comparison.py:115-127](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_direct_comparison.py:115)

各testでT-080関数を「呼ばれたら失敗するstub」にし、receipt存在下でもlegacy strict経路だけを通ることを固定します。

### U5 — docs／台帳

- [docs/decisions.md:3113](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:3113): D78追記。
- [docs/phase3.md:79-88](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3.md:79): 状態中立なT-080 checkpoint。
- `docs/phase3-8b-descriptor-design.md:新規status節`: design source repin対象としてH_mig前に確定。
- [docs/worklog.md:53](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:53): 実装結果を「receipt発行待ち」と記録。
- [output/README.md:5-27](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/README.md:5): `t080-migration/`、保護外namespace、history verifier境界。
- [orchestrator/tests/README.md:34-49](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/README.md:34): 新testの自走コマンド。
- 新設 `output/insights/2026-07-22_t080-migration-contract.md`
- 新設 `output/insights/2026-07-22_t080-mutation-preregistration.md`

### 依存順

```text
U0
 ├─ U1 → U2
 ├─ U3  （U0と別commit）
 └─ U4
U1+U2+U3+U4 → integration/full suite → U5 → final wave commit H_mig
H_mig → draft生成/validate → 人間R
```

## 5. テスト計画

### hermetic primary 3状態

| fixture | exact期待 |
|---|---|
| never-issued | legacy 4拒否、observation null |
| active-valid | `{floor-null,budget-null}` exact、17-item observation |
| invalid confirmation | migration refusal 1＋legacy 4 exact |

`issued-but-missing`は追加負例群として、R後delete、modify→revert、delete→re-add、rename、copy/type-change、worktree欠落、broken symlinkを個別に検査します。全てlegacy fallback禁止です。

### real-repo golden 2状態

既存node `test_real_freeze_gate_lists_floor_and_budget_null`を維持します。

- historyにRなし: 4 refusal prefixが1対1 exact、observation null。
- active-valid Rあり: 2 refusal全文exact、17-item observation。
- issued-but-missing／invalid: test自体を失敗。

### 負例群

- strict JSON: duplicate、NaN/Infinity、BOM、非UTF-8、pretty JSON、末尾LF、unknown key。
- confirmation regex、mixed null、日時offset／少数秒。
- 13/2件数、pointer duplicate/missing/surplus、RFC6901 escape不正。
- raw artifact、H_mig blob、51 unchanged、repin report cross-field不一致。
- reconstruction equality無効化を検出する`reference_values_note`だけの差。
- dirty／HEAD mismatch／submodule dirtyでdraft拒否。
- shallow、replace、graft、alternate、Git env注入。
- ancestry missing/nonancestor/ancestor/noncommit/git-error。
- anchor refusalとccbench mismatchを同時に与え、双方のrefusalが残ること。
- current ccbench drift、H_mig gitlink drift。
- live rr80 hit、positive root欠落、predicate mutant。
- structurally schema-validな悪性pathを持つreceiptがclosureとscan双方で拒否されること。
- campaign-start key absent/null/malformed/mismatchとjudge indeterminate。
- factory外GateDecision、全早期return、success resultのkey欠落。
- measurement/calibration/report/direct comparisonへのadapter漏れなし。

### 既存2618 node

実装前にBASEの`--collect-only` node一覧を保存し、完了時に集合差を取ります。

- `BASE_NODES ⊆ HEAD_NODES`
- rename/delete = 0
- 追加集合は完了報告のnode ledgerと完全一致
- `test_tampered_freeze_fails_source_verification`は同名
- xfail／skip／期待緩和で既存nodeを逃がさない
- full suiteは `2618 + 新規node数 passed / 18 skipped / 0 failed`

新 `test_t080_freeze_migration.py` は直接実行でも実テストを走らせます。[test_plain_runner_coverage.py:60-93](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_plain_runner_coverage.py:60)

## 6. 変異事前登録候補

全件を`candidate`として再登録し、実装開始時に実コード順を再読して初めて`confirmed`へ昇格します。F28の2条件は「先行検査なし」「無効化時の赤理由が1件」です。[failures.md:343-356](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/failures.md:343)

| candidate | 単独入力／先行検査 | 期待する単一kill |
|---|---|---|
| M01 draft S-1 equality無効化 | closure不変、`reference_values_note`だけ異なるH_mig | `known_axes.reconstruction_equality` |
| M02 issued-but-missingをnever-issued化 | R後deleteしたclean repoでdraft | state preconditionだけが消え、draftが誤成功 |
| M03 predicate-only 50→51 | fixture bytes/root不変 | positive hit `1→0→1` |
| M04 receipt canonical検査無効化 | semantic同値pretty JSONをR blob化 | `receipt.canonical_mismatch` |
| M05 R trailer検査無効化 | topology/blob正、trailerだけ不正 | `receipt.user_commit_trailer` |
| M06 R single-file diff検査無効化 | receipt＋無関係1fileをRで追加 | `receipt.introduction_diff` |
| M07 history immutable検査無効化 | R後別bytes→元bytesへrevert | `receipt.history_mutated` |
| M08 artifact raw検査無効化 | `verify` fixtureで空白1byte、semantic doc同一 | `*.artifact_bytes` |
| M09 noncommitをmissing扱い | shape/existence合格のblob OID | ancestry object typeだけ |
| M10 merge-base rc>1をrc=1扱い | cat-file commit、runnerだけrc128 | ancestry Git errorだけ |
| M11 current ccbench検査無効化 |同treeの別commitへsubmodule HEADだけ移動 | `known_axes.ccbench_current` |
| M12 H_mig gitlink検査無効化 | draft fixtureのgitlinkだけ不一致 | `known_axes.ccbench_gitlink` |
| M13 live層2検査無効化 | R後untracked rr80 3軸file | `holdout.unknownness_layer2` |
| M14 post-R WAL key検査無効化 | active resolver＋key欠落WAL | protocol rowが消えjudgeが誤determinate |

v1候補の失効判定:

- surplus repin:削除。exact 13 schemaが先に落とすためF28違反。
- H_mig snapshot展開／`python -I`／旧code実行: J1で実装面自体が消滅。
- fixture bytes 50→51:禁止。M03へ差替え。
- S-1 equality候補外:判断を反転し、M01を必須登録。
- `migration_blob_sha256`単独照合: repin report cross-equalityとprojected hashにも波及するため候補外。
- generator equality: generatorはMなのでacceptance mutationにしない。
- WAL/report転記削除: J6によりjudge indeterminateへ影響するためM14として再登録。
- legacy head raw改変: artifact raw rootが先行するため候補外。

## 7. ユーザー引き渡し手順

### AI側

final wave commitをH_migとした直後、AIが以下を実行済みにしてdraftを引き渡します。

```bash
T080_BASIS="$(git rev-parse HEAD)"

python3 orchestrator/campaign/t080_freeze_migration.py draft \
  --basis "$T080_BASIS" \
  --out output/t080-migration/legacy-freeze-repin.receipt.draft.json

python3 orchestrator/campaign/t080_freeze_migration.py validate-draft \
  --path output/t080-migration/legacy-freeze-repin.receipt.draft.json
```

### 人間確認

ユーザーは最低限、次を確認します。

1. 13件のold/new path・hash。
2. 各`provenance_resolved` commit、または`provenance_unverified`。
3. 各diffのadded/deleted行数。
4. knownのprojected/rebuilt hash一致。
5. holdout projected hashとlive scan hash。
6. H_mig、artifact raw roots、generator metadata。
7. D75 §14の承認済み損失。

確認後:

```bash
T080_CONFIRMED_BY='ascii_identifier'
T080_CONFIRMED_AT="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

python3 orchestrator/campaign/t080_freeze_migration.py finalize \
  --draft output/t080-migration/legacy-freeze-repin.receipt.draft.json \
  --confirmed-by "$T080_CONFIRMED_BY" \
  --confirmed-at "$T080_CONFIRMED_AT" \
  --out output/t080-migration/legacy-freeze-repin.receipt.json

rm -- output/t080-migration/legacy-freeze-repin.receipt.draft.json

git add -- output/t080-migration/legacy-freeze-repin.receipt.json
git diff --cached --name-only
git diff --cached
```

staged pathがreceipt 1 fileだけであり、HEADがH_migのままであることを確認してRを作ります。

```bash
git commit \
  -m '[T-080] activate legacy freeze migration receipt' \
  -m 'AI-Agent: none'
```

### post-R exact受入

gateのrc=2を成功条件として明示assertします。

```bash
python3 - <<'PY'
import json
import subprocess

proc = subprocess.run(
    [
        "python3",
        "orchestrator/campaign/s8b_oracle_driver.py",
        "gate-check",
        "--freeze",
        "output/s8b-freeze/holdout_freeze.json",
        "--root",
        ".",
    ],
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
assert proc.returncode == 2, (proc.returncode, proc.stdout, proc.stderr)
result = json.loads(proc.stdout)
expected = {
    "floor-null: freeze.floor が null",
    "budget-null: freeze.budget が null",
}
assert result["allowed"] is False
assert len(result["refusals"]) == 2
assert set(result["refusals"]) == expected
observation = result["t080_freeze_migration_observation"]
assert observation["schema_version"] == "izanagi-t080-freeze-migration-observation/v1"
assert len(observation["items"]) == 17
PY

python3 orchestrator/campaign/t080_freeze_migration.py verify \
  --path output/t080-migration/legacy-freeze-repin.receipt.json

python3 tools/run_tests.py
python3 tools/check_docs.py
python3 tools/check_codex_agents.py
python3 tools/check_ai_provenance.py
```

発効成功後の次セッションでworklogへR SHA、exact 2 refusals、T-068/T-077/T-078の状態を記録します。pushは人間判断です。

### 復旧線

push前だけ、まずHEADが失敗したRであることを確認してから:

```bash
git show --stat --oneline HEAD
git reset --hard HEAD~1
```

その後、修正commitを作って新しいH_migとし、draftから再生成します。

push後は履歴を書き換えず、現receiptも変更しません。前記「裁定への異議」のとおり、別path/schemaの修復裁定を起票します。

## 8. no-touch manifestと受入コマンド

BASEはexact:

```text
0e7b0818ee4af3e7633a26e7e9e2e92534ef8dc6
```

no-touch manifestはJ11の指定どおり次の12 fileです。

```bash
git diff --exit-code \
  0e7b0818ee4af3e7633a26e7e9e2e92534ef8dc6..HEAD -- \
  output/s1-freeze/known_axes_freeze.json \
  output/s1-freeze/measurement_freeze.json \
  output/s8b-freeze/holdout_freeze.json \
  orchestrator/tests/test_frozen_artifacts.py \
  orchestrator/campaign/s8b_ratified_freeze.py \
  orchestrator/campaign/s8b_approved.py \
  orchestrator/tests/test_s8b_approved.py \
  orchestrator/tests/test_s8b_ratified_freeze.py \
  orchestrator/tests/test_s8b_ratified_verify.py \
  orchestrator/campaign/s8b_selector_freeze.py \
  orchestrator/campaign/s1_known_axes_freeze.py \
  orchestrator/campaign/s8b_holdout_freeze.py
```

関連受入:

```bash
python3 orchestrator/tests/test_t080_freeze_migration.py

python3 tools/run_tests.py \
  orchestrator/tests/test_t080_freeze_migration.py \
  orchestrator/tests/test_s8b_oracle_driver.py \
  orchestrator/tests/test_s8b_holdout_freeze.py \
  orchestrator/tests/test_s8b_oracle_report.py \
  orchestrator/tests/test_s8b_oracle_artifacts.py \
  orchestrator/tests/test_s1_measurement_freeze.py \
  orchestrator/tests/test_s1_verify_extime_calibration.py \
  orchestrator/tests/test_s1_report.py \
  orchestrator/tests/test_s1_direct_comparison.py \
  orchestrator/tests/test_plain_runner_coverage.py \
  orchestrator/tests/test_frozen_artifacts.py

python3 tools/run_tests.py
python3 tools/check_codex_agents.py
python3 tools/check_docs.py
python3 tools/check_ai_provenance.py
```

完了報告には、BASE→HEADの変更file一覧、no-touch結果、nodeのadded/renamed/deleted exact台帳、mutationのcandidate→confirmed結果を添付します。

## 9. D78へ記録する設計判断

[decisions.md:3113](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:3113) の末尾へD78として次を記録します。

1. **再構成の充足形**  
   clean `worktree == H_mig`でdraft時に現行in-treeコードを一度だけ実走し、passとcanonical document hashをreceiptへ束縛する。gateは旧コードを再実行せず、byte pin、H_mig closure、live ccbench、live unknownness層2を検査する。

2. **gateで再構成を繰り返さない理由**  
   H_mig snapshot実行は任意の旧Pythonを実行する攻撃面になる。移行時実走＋receipt evidence＋以後のbyte pinが本waveでの「再構成維持」のexact意味である。

3. **receipt lifecycle／retirement**  
   pathは`output/t080-migration/legacy-freeze-repin.receipt.json`。W-X発効でadapterを撤去し、receiptは歴史成果物としてbyte不変で残す。g1 bundleがlegacy pinを引き継ぐ。

4. **gate-attempt台帳不採用**  
   gate拒否時はcampaign-startへ到達しないが、R commitが発効と人間確認の耐久記録である。専用台帳はG2/G3に対して過剰であり導入しない。

5. **承認済み損失**  
   H_mig後のcurrent worktree source driftを受理し得ることはD75 §14の既承認損失です。[freeze-permanent-design.md:479-488](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:479)

6. **人間承認の限界**  
   `AI-Agent: none`と`confirmed_by`は暗号署名ではない。真正性はreview過程に依存し、機械的な人間性証明を主張しません。[freeze-permanent-design.md:490-499](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:490)

7. **scope境界**  
   adapterはofficial oracleだけ。measurement、calibration、S-1 report、direct comparisonはlegacy strictのまま。独立S-1 reference implementation、完全consumer proof-chain、恒久registryはW列へ残します。

8. **状態中立な記録**  
   「機構実装済み・receipt発行待ち。発効後期待は2拒否」と書き、R前後どちらでも文書が虚偽にならない形にします。

## §7a 実装報告 U0

U0 を所有 2 ファイルのみで実装しました。docs・凍結成果物・既存 production は変更せず、commit も作成していません。

### 実装内容

[実装本体](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1)

- strict JSON／canonical bytes／RFC 6901:
  `_strict_load`、`_canonical_bytes`、`_load_canonical`、`_pointer_tokens`、`_resolve_pointer`、`_set_pointer`
- receipt schema:
  `validate_receipt_structure`、`validate_receipt_schema`
- hardened Git:
  `_git`、`_git_rc`、`_capture_head`、`_commit_graph`、`_blob_oid_by_commit`、`_tree_entry`
- 4 状態機械・ancestry:
  [`inspect_receipt_history`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1411)、`_classify_ancestry`
- closure／repin report:
  `_classify_source_closure`、`_verify_closure`、`_build_repin_report`
- draft 再構成:
  `_capture_draft_basis`、`_draft_reconstruct_known_axes`、`_draft_reconstruct_holdout`
- plan §1.3:
  [`draft_receipt`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1290)
- plan §3:
  `validate_draft`、`finalize_receipt`、[`verify_receipt`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1574)、[`main`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1720)
- static gate／observation:
  [`static_gate_adapter`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1651)、17-item envelope 構築

[hermetic テスト](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_t080_freeze_migration.py:1) は29 nodeで、自走 harness 付きです。

### Hardened Git

「同型実装」を選択しました。`s8b_ratified_freeze.py` の private 関数へ結合せず、同契約を移植したうえで以下を追加しています。

- 全 `GIT_*` 入力環境の除去と固定安全環境
- `core.useReplaceRefs=false`
- shallow／replace／graft／alternates 拒否
- batch-check による型判定
- merge-base rc 0/1/>1 を保持する専用 runner

### 実走結果

- `python3 tools/run_tests.py orchestrator/tests/test_t080_freeze_migration.py orchestrator/tests/test_plain_runner_coverage.py`
  - 32 passed / 0 failed / 0 skipped
- `python3 orchestrator/tests/test_t080_freeze_migration.py`
  - 29 passed / 0 failed / 0 skipped / 0 errors
- `python3 tools/run_tests.py`
  - 2639 passed / 0 failed / 26 skipped
- `python3 tools/check_codex_agents.py`
  - OK
- `python3 tools/check_docs.py`
  - 違反なし
- repository live scan
  - rr80=0、rr20=0、positive=55
- J11 no-touch manifest
  - 差分なし

`check_ai_provenance.py` は、commit 禁止のため対象となる新規 commit がなく未実行です。

### 逸脱

検査意味論・schema・CLI 契約からの逸脱はありません。

通常のクラス2作業で行う handoff/worklog 更新は、「所有2ファイル以外への書込禁止」に従って省略しました。既存の未追跡 handoff は開始時から存在したもので、変更していません。

### M01..M14 自己評価

U0 所有に関係する M01、M02、M04〜M13 は、各 mutation point を単独 reason で検出できる境界とテストを備えています。

- M01: deep equality のみで `known_axes.reconstruction_equality`
- M02: R後削除済み clean history で draft state precondition
- M04: canonical bytes のみ
- M05: R trailer のみ
- M06: R single-file diff のみ
- M07: 中間の別bytesを history mutation のみで検出
- M08: semantic parse前のartifact raw root
- M09: batch-check object type
- M10: merge-base rc>1
- M11: current ccbench HEAD
- M12: H_mig gitlink
- M13: live layer2 scan

M03 はU3のpredicate-only mutation、M14はU2のWAL/report mutationのため、U0ではproduction literal／接続境界のみ実装し、mutation 本体は扱っていません。変異自体は指示どおり実装・実走していません。

## §7b 実装報告 U1

U1（official gate 統合）を実装しました。変更は所有対象の 2 ファイルのみで、commit・docs 編集は行っていません。

## 変更点

- [s8b_oracle_driver.py:83](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/wt-u1/orchestrator/campaign/s8b_oracle_driver.py:83)
  - `GateDecision` に default なしの必須 observation field を追加。
  - receipt 解決の分類不能を明示 refusal に倒す fail-closed 処理を追加。
  - `_make_gate_decision` へ全 production 構築を統一。
- [s8b_oracle_driver.py:123](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/wt-u1/orchestrator/campaign/s8b_oracle_driver.py:123)
  - active-valid、holdout raw pin、legacy known path/hash の発火条件を実装。
  - 発火時は legacy verifier を呼ばず `static_gate_adapter` の結果を採用。
  - 発火後の raw 欠落・差替えも migration refusal に固定。
- [s8b_oracle_driver.py:273](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/wt-u1/orchestrator/campaign/s8b_oracle_driver.py:273)
  - never-issued は従来の legacy 検査順・4 refusal を維持。
  - issued-but-missing / invalid は migration refusal を保持しながら legacy 診断を継続。
- [s8b_oracle_driver.py:411](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/wt-u1/orchestrator/campaign/s8b_oracle_driver.py:411)、[s8b_oracle_driver.py:976](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/wt-u1/orchestrator/campaign/s8b_oracle_driver.py:976)
  - `gate_check` / `run_block` 最外層で `verify_receipt` を各 1 回だけ実行。
- [s8b_oracle_driver.py:1162](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/wt-u1/orchestrator/campaign/s8b_oracle_driver.py:1162)
  - campaign-start、全 run result、terminal result、CLI `asdict` に observation key を常設。
- [test_s8b_oracle_driver.py:699](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/wt-u1/orchestrator/tests/test_s8b_oracle_driver.py:699)
  - real-repo golden を never-issued / active-valid の exact 2 状態へ変更。
- [test_s8b_oracle_driver.py:728](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/wt-u1/orchestrator/tests/test_s8b_oracle_driver.py:728)
  - hermetic 3 状態の exact refusal と 17-item observation を追加。
- [test_s8b_oracle_driver.py:779](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/wt-u1/orchestrator/tests/test_s8b_oracle_driver.py:779)
  - factory 外構築と全 `run_block` return の observation 欠落を拒否する AST 検査を追加。
- [test_s8b_oracle_driver.py:1519](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/wt-u1/orchestrator/tests/test_s8b_oracle_driver.py:1519)
  - 既存 tamper node を valid-receipt fixture＋`confirmed_by` 単独改変へ変更。増加 refusal は holdout 1 件のみ。

## §1.6 早期 return 対応表

| plan v2 の経路 | 実装先 |
|---|---|
| gate core 終端 | `408` factory |
| standalone gate 全 return | `423–491` factory/core |
| validated gate | `500–512` factory/core |
| ratified 解決 2 return | `1013–1026` factory済み decision |
| launch validation 2 return | `1027–1040` factory済み decision |
| freeze read / root mismatch | `1044–1060` factory済み decision |
| gate / manifest return | `1079–1092` factory済み decision |
| prepare 2 return | `1116–1131` factory済み decision |
| claim return | `1133–1156` factory済み decision |
| campaign-start | `1162–1172` key 常設 |
| budget terminal | `1215–1228` key 常設 |
| success / terminal result | `1447–1462` key 常設 |

## Node 台帳

追加 6 node:

- `test_t080_gate_hermetic_primary_states_exact[never-issued]`
- `test_t080_gate_hermetic_primary_states_exact[active-valid]`
- `test_t080_gate_hermetic_primary_states_exact[invalid]`
- `test_gate_decision_is_built_only_by_factory_and_all_run_returns_propagate`
- `test_run_block_resolves_receipt_once_and_propagates_observation_to_wal_and_result[False]`
- `test_run_block_resolves_receipt_once_and_propagates_observation_to_wal_and_result[True]`

名前維持で書換:

- `test_real_freeze_gate_lists_floor_and_budget_null`
- `test_tampered_freeze_fails_source_verification`

削除: 0。基準 61 node → 最終 67 node。

## 検証結果

- `python3 -m pytest -q orchestrator/tests/test_s8b_oracle_driver.py`
  - `66 passed, 1 skipped`
- `python3 -m pytest -q orchestrator/tests/test_t080_freeze_migration.py orchestrator/tests/test_s8b_oracle_driver.py`
  - `95 passed, 1 skipped`
- `python3 -m pytest -q`
  - `2645 passed, 26 skipped`
- `python3 tools/check_codex_agents.py`
  - OK
- `python3 tools/check_docs.py`
  - 違反なし
- `git diff --check`
  - 問題なし

赤はありません。sandbox 起因疑い 0、回帰 0 です。

plan v2 からの逸脱はありません。所有制約どおり docs・commit・他ファイルは変更していません。

## §7c 実装報告 U2

U2（WAL/report 伝播）を実装しました。変更は許可された3ファイルのみで、driver・production judge・docs・git commit は無変更です。

## 変更点

- [s8b_oracle_report.py:88](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/wt-u2/orchestrator/campaign/s8b_oracle_report.py:88)
  - T-080 envelope の exact 6-field／17-item 検証を追加。
  - U0 の schema literal・固定値・canonical bytes helper を使用。
  - absent／null／envelope／malformed を fail-closed 分類。
- [s8b_oracle_report.py:1077](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/wt-u2/orchestrator/campaign/s8b_oracle_report.py:1077)
  - active receipt での key 欠落・null を campaign 全 row の `protocol_violation` に伝播。
  - reason prefix は exact `t080-freeze-migration-observation: `。
  - malformed、campaign 間 canonical 不一致、null/object 混在を全 row へ伝播。
- [s8b_oracle_report.py:1387](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/wt-u2/orchestrator/campaign/s8b_oracle_report.py:1387)
  - `repo_root=ROOT` を注入可能化。
  - `verify_receipt(root=repo_root)` を report 生成ごとに1回実行。
  - 同一 canonical envelope を top-level sibling に転記。既存 `8b-oracle-observations/v1` literal は不変。
- [test_s8b_oracle_report.py:2416](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/wt-u2/orchestrator/tests/test_s8b_oracle_report.py:2416)
  - pre-R absent/null、post-R missing/null/malformed/mismatch、canonical 一致、null/object 混在を追加。
  - M14 は「key 削除だけ」で sole reason の protocol row が生じ、judge が determinate→indeterminate へ倒れる構造。
- [test_s8b_oracle_artifacts.py:155](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/wt-u2/orchestrator/tests/test_s8b_oracle_artifacts.py:155)
  - official observations loader が sibling field を完全保持することを固定。

`test_s8b_oracle_judge.py` は変更不要でした。judge の既存 protocol-row 処理を report テストから実証しています。

## node 台帳

- 追加: 9
- 書換・改名: 0
- 削除: 0
- 所有テスト node 数: 194 → 203

追加 node:

- `test_observations_loader_preserves_t080_sibling_field_exactly`
- `test_pre_r_campaign_start_absent_or_null_is_allowed[historical-absent]`
- `test_pre_r_campaign_start_absent_or_null_is_allowed[null]`
- `test_post_r_missing_key_is_single_reason_and_makes_judge_indeterminate`
- `test_post_r_null_is_protocol_violation_for_every_campaign_row`
- `test_malformed_t080_envelope_is_fail_closed`
- `test_campaign_canonical_envelope_mismatch_is_protocol_violation`
- `test_matching_canonical_envelopes_are_copied_to_report_sibling`
- `test_pre_r_null_and_object_mixture_is_protocol_violation`

## 実走結果

- M14＋loader targeted:
  - `python3 -m pytest -q ...::test_post_r_missing_key... ...::test_observations_loader...`
  - `2 passed`
- 所有3テスト:
  - `python3 -m pytest -q test_s8b_oracle_report.py test_s8b_oracle_artifacts.py test_s8b_oracle_judge.py`
  - `203 passed`
- orchestrator 全体:
  - `python3 -m pytest -q orchestrator/tests`
  - `2648 passed, 26 skipped, 0 failed`
- `python3 tools/check_codex_agents.py`
  - OK
- `python3 tools/check_docs.py`
  - 違反なし
- `py_compile`、`git diff --check`
  - 成功

赤は0件で、submodule制約による偽赤もありません。

## plan v2 からの逸脱

実装仕様上の逸脱はありません。

運用面では、直接指示に従い docs／worklog／handoff／phase doc を編集せず、commit も作成していません。そのため commit 後専用の `check_ai_provenance.py` は未実行です。また、plan記載の旧 baseline `2618 passed / 18 skipped` に対し、U0実装済みの現worktree全体は `2648 passed / 26 skipped` でした。U2自身の node 差分は追加9・削除0です。

## §7d 実装報告 U3

U3 実装完了です。production・docs は変更せず、commit も作成していません。

### 変更点

- [freeze_holdout_positive_control_v1.txt](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/wt-u3/orchestrator/tests/data/freeze_holdout_positive_control_v1.txt:1)
  - S2-4.6 の exact 3行＋末尾 LF
  - SHA-256: `caee6deabcf6209f5e8d59ee104a64b6bcf18a2a6054b1cefd6141709802faa7`
- [t080_fixture_roots.py](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/wt-u3/orchestrator/tests/t080_fixture_roots.py:7)
  - test 側の path/root key/SHA-256 を独立 pin
- [test_s8b_holdout_freeze.py](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/wt-u3/orchestrator/tests/test_s8b_holdout_freeze.py:55)
  - fixture-only `files=` 検索
  - raw bytes hash と production literal 一致を別 node 化
  - baseline 1 → predicate-only rr51 mutant 0 → revert 1 を実証
  - skew/rmw predicate 不変も assert

Node 台帳（追加3、改名0、削除0）:

- `test_t080_positive_control_fixture_raw_bytes_match_test_pin`
- `test_t080_positive_control_test_pins_match_production_literals`
- `test_t080_positive_control_kills_predicate_only_rr51_mutant`

### 実走結果

- `sha256sum ...fixture...` → 承認 SHA-256 と一致
- 対象3 node → `3 passed`
- `test_s8b_holdout_freeze.py` → `22 passed`
- `test_t080_freeze_migration.py` → `29 passed`
- 実 repo scan → `rr80=[]`, `rr20=[]`、fails-closed 検査通過
- `python3 -m pytest -q orchestrator/tests` → `2642 passed, 26 skipped`
- `python3 tools/check_codex_agents.py` → OK
- `python3 tools/check_docs.py` → 違反なし
- `py_compile`、`git diff --check` → 成功

赤は0件です。submodule sandbox 起因の偽赤もありません。

### 逸脱

実装契約・S2-4.6 の承認値からの逸脱はありません。plan v2 の「U0とは別commit」だけは、今回の明示的な git commit 禁止に従い未実施です。また所有制約に従い、通常の class 3 handoff/worklog/phase 更新も行っていません。変更は指定された3ファイルだけです。

## §7e 実装報告 U4

U4 実装完了です。所有4テストだけを変更し、156行追加・削除0。production・docs・git commit は無変更です。

### 追加 node 台帳

- `orchestrator/tests/test_s1_measurement_freeze.py::test_receipt_exists_but_measurement_verify_stays_legacy_strict`
- `orchestrator/tests/test_s1_measurement_freeze.py::test_measurement_production_module_does_not_import_t080_adapter`
- `orchestrator/tests/test_s1_verify_extime_calibration.py::test_receipt_exists_but_calibration_target_stays_legacy_strict`
- `orchestrator/tests/test_s1_verify_extime_calibration.py::test_calibration_production_module_does_not_import_t080_adapter`
- `orchestrator/tests/test_s1_report.py::test_receipt_exists_but_report_freeze_gate_stays_legacy_strict`
- `orchestrator/tests/test_s1_report.py::test_report_production_module_does_not_import_t080_adapter`
- `orchestrator/tests/test_s1_direct_comparison.py::test_receipt_exists_but_direct_comparison_loader_stays_legacy_strict`
- `orchestrator/tests/test_s1_direct_comparison.py::test_direct_comparison_production_module_does_not_import_t080_adapter`

各動的 pin は receipt sentinel を実在させ、T-080 公開関数を呼出即失敗にした状態で、実 legacy verifier の既知 fail-closed 経路を実行します。builder の echo 置換はありません。

### 実走結果

- 追加8 node: `8 passed`
- 所有4ファイル全体:
  `python3 tools/run_tests.py <4 files>` → `66 passed`
- `test_plain_runner_coverage.py` + `test_frozen_artifacts.py` → `5 passed`
- `python3 tools/check_codex_agents.py` → rc=0
- `python3 tools/check_docs.py` → rc=0
- `py_compile`、`git diff --check` → rc=0
- plan v2 no-touch 検査 → rc=0
- production 4ファイルの `t080_freeze_migration` 検索 → 該当なし（rg rc=1 は期待結果）

赤は初回追加 node 実走の1件のみです。direct comparison が透過する既存例外を `DriverError` と誤認していたテスト期待の問題で、既存契約どおり `FreezeError` に修正後、全緑です。sandbox/submodule 起因の偽赤はありません。

### plan v2 からの逸脱

なし。wave-level の full suite と provenance 検査は未実走です。commit 禁止のため `check_ai_provenance.py` も実行していません。

## §8 敵対レビュー A — 正しさ境界 (NO-GO)

[1] [BLOCKER] / J1 の draft 実走は receipt から証明できず、再構成に失敗する H_mig でも `active-valid` を偽造できる / `_verify_reconstruction_static()` は projected hash を再計算するだけで builder を実行せず、`holdout.live_scan_sha256` は一度も比較しない。[t080_freeze_migration.py:954](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:954) `validate_draft()` も live scan を再実行するだけで stored hash と照合せず、履歴検査は任意の canonical/schema-valid R を受理する。[t080_freeze_migration.py:1363](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1363) [t080_freeze_migration.py:1467](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1467) / **放置すると、`live_scan_sha256` を任意値へ書き換えた draft、または builder equality を一度も通していない手製 receipt が active になり、legacy source 拒否が消えた偽の proof chain をレポート・後続 certified 選択が参照する。** / draft 実走結果を別の不変 commit E に格納して R がその blob hash を束縛する二段 topology にするか、R で変更可能な confirmation 以外の bytes を事前 commit 済み template と完全一致させること。自己申告の `status/hash` だけでは修正不能。

[2] [MAJOR] / 「clean worktree == H_mig」も実効的に証明されていない / Git 環境から system/global config は除くが repository-local config は生きており、`core.fsmonitor`、`core.worktree`、clean/smudge filter の影響下で `git status` だけを cleanliness 証明にしている。[t080_freeze_migration.py:540](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:540) [t080_freeze_migration.py:1191](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1191) その後に builder/verifier module を worktree から import する。[t080_freeze_migration.py:1101](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1101) / **放置すると、Git が clean と報告する別 bytes・別 worktree の Python を実行して生成した receipt が H_mig 実走証拠として台帳に残る。** / `--show-toplevel` の root 一致、fsmonitor/untracked-cache/filter の無効化に加え、実際にロードする全 source bytes・mode を H_mig blob と nofollow で照合し、検証済み source loader から実行すること。

[3] [BLOCKER] / production monkeypatch は lock があっても並行 gate を fail-open させる / live scan は lock の外で実行され、その後 module-global の `_verify_source`、`_verify_head`、`search_repository` を差し替える。[t080_freeze_migration.py:1509](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1509) [t080_freeze_migration.py:1515](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1515) Thread A の patch 中に Thread B が 1509 行へ入ると、B は A の別 root 用 report を取得してから lock を待ち、その report で B の verify を通す。lock を取らない通常の `verify_document()` caller は source/head 検査自体を飛ばす。`finally` による通常例外時の復元はあるが、この並行漏れは防がない。[t080_freeze_migration.py:1532](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1532) / **放置すると、holdout hit や source/head drift のある root が別 caller の clean report で受理され、その trial が WAL・oracle report・certified 選択候補へ入る。** / global patch を廃止し、holdout module に `verify_static(doc, known_doc, search_report)` のような pure APIを設けること。少なくとも callback injection を正式引数にし、将来 `_verify_source` に追加される第4検査も一括 no-op にならない構造にする。

[4] [BLOCKER] / report が receipt の4状態と campaign-time 状態を「report生成時に active か」の1 bitへ潰している / `issued-but-missing` と `invalid` を認識しても、`receipt_active = state == "active-valid"` に変換して refusal を捨てる。[s8b_oracle_report.py:1396](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1396) absent/null はその boolean が偽なら無条件で許される。[s8b_oracle_report.py:178](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:178) しかも current state 判定には live layer2 scan まで含むため、campaign 後の既知化だけでも `invalid` になり得る。[t080_freeze_migration.py:1614](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1614) / **放置すると、post-R の receipt 削除・改変後に observation 欠落/null WAL が completed row のまま通って judge が determinate を返す一方、正当な pre-R null WAL は後日の R 発行だけで protocol_violation に反転する。** / campaign-start に `state + validation_head` を常時耐久化し、各 campaign の H_v に対して history-only 検証を行うこと。report 時の live gate 状態を campaign-time 証明の代用にしてはいけない。

[5] [BLOCKER] / report が envelope の形だけを検査し、実 receipt／H_mig／観測値へ束縛していない / `receipt.raw_sha256`、`migration_basis_commit`、`validation_head`、各 `observed` は桁数だけを検査し、active resolution の observation と比較しない。[s8b_oracle_report.py:105](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:105) ancestry の `subject` も `/frozen_at_head` に固定されず、`ancestor/not-ancestor.observed == validation_head` も要求しない。同じ偽 envelope を全 campaign に置けばそのまま sibling へ転記される。[s8b_oracle_report.py:1455](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1455) / **放置すると、存在しない receipt hash・別 basis・偽 repin hashを指す report が completed rows を保ったまま生成され、judge/certified 選択が偽の proof reference を伴って determinate になる。** / envelope の H_v で R blob/historyを再検証し、raw hash・basis・13+2 observed・ancestryを実 Git 導出値と照合すること。campaign 間 equality は真偽検証の代替にならない。

[6] [MAJOR] / receipt の blob/worktree 一致検査と gate 利用の間に明確な TOCTOU がある / history 検査は R blob と worktree bytes を比較するが、後で observation 作成時に worktreeを再読し、その bytes が R blob と同じか確認しない。[t080_freeze_migration.py:1454](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1454) [t080_freeze_migration.py:1630](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1630) driver は resolution を一度取得した後、receipt/head を再確認せず campaign-start まで使用する。[s8b_oracle_driver.py:1008](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1008) / **放置すると、比較直後の receipt 削除・symlink化・差替えでも state は active-valid のままとなり、WAL/report の `receipt.raw_sha256` は検証していない bytes を参照し、v2 campaign の受理も継続する。** / R の immutable raw bytes/hash を `ReceiptResolution` に保持して observation に使い、HEAD・path inode/typeを gate return/campaign-start 境界で再検証すること。親 component も含む nofollow/openat 型の path lease が必要。

[7] [MAJOR] / merge commit 上の後続 C/M/T を履歴改変として検出できない / `_history_touches_path()` の `diff-tree` は `-m/-c/--cc` を付けていないため、merge commit の per-parent diff を出さない。[t080_freeze_migration.py:777](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:777) receipt OID が同じままの copy や mode change は OID 一致検査も通り、その後 active 候補になる。[t080_freeze_migration.py:1435](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1435) / **放置すると、R 後 merge で receipt を copy、または同一 blob の mode を変更した履歴が `issued-but-missing` でなく `active-valid` となり、`receipt.history_mutated` refusal が受理集合から消える。** / 全 descendant の全 parent edge を `diff-tree -m -r -z --raw -M -C --find-copies-harder` で検査し、OIDだけでなく modeも保持すること。

[8] [MAJOR] / J4 の「全層継続」と observation の事実性を満たしていない / known schema/pairing、layer2 scan、holdout static検査が一つの例外連鎖になっており、known schema failure は layer2 実行前に脱出する。[t080_freeze_migration.py:1495](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1495) `issued-but-missing` は全独立検査前に即 return する。[t080_freeze_migration.py:1580](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1580) 他の refusal があっても observation は receipt の自己申告値から無条件生成され、全 source を `repinned-to-basis-blob` と表示する。[t080_freeze_migration.py:1539](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1539) / **放置すると、同時に存在する layer2/binding/ccbench 異常が `GateDecision.refusals` から消え、invalid gate が17件の「clean observation」を返すため、規律3の次手シグナルと proof reference が事実と食い違う。** / 各層を独立 callable に分離して全例外を個別収集し、R blobが回収可能な issued-but-missing でも独立検査を続けること。observation は実測値から作り、未検証・失敗 item を clean status にしてはならない。

Nit（G5影響なし）: `_repo_relative()` は入力を `resolve()` してから canonical 判定するため、`output/x/../t080-migration/...` のような lexical `..` alias を受理する。[t080_freeze_migration.py:1279](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1279) 同じ最終 file を指すため現状の受理値は変わらないが、入力文字列を resolve 前に exact/canonical 検査すべき。

名指し点のうち、`inspect_receipt_history()` の `invalid + refusals空` は現行 production caller から直接は漏れていない。driver/report は `verify_receipt()` を使用し、draft/validate は `invalid` 自体を拒否する。また adapter 非発火時は holdout/known の legacy verifier、floor/budget、manifest が従来どおり走る。[s8b_oracle_driver.py:336](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:336) Ancestry の missing/non-ancestor と noncommit/git-error の分類、useReplaceRefs、GIT_* 除去、alternates、merge-base rc保持、batch type判定そのものには格下げを確認しなかった。

テストは指示どおり実行していない。

総合判定: **NO-GO**

## §9 敵対レビュー B — テスト誠実性 (NO-GO)

対象は `64c13dc..7b8e843`。テストは実行せず、差分・設計正本・node 集合を静的検査した。

[1] [BLOCKER] / report が WAL 生成時点ではなく report 生成時点の receipt 状態で pre-R/post-R を判定している / 根拠: 現在の HEAD に対して `verify_receipt()` を呼び、`active-valid` だけを真にする [s8b_oracle_report.py:1397](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1397)。key absent/null の扱いはその boolean のみに依存する [s8b_oracle_report.py:178](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:178)。これは「R 前の key-absent は歴史 WAL、R 後は violation」という契約 [plan_v2.md:284](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/plan_v2.md:284) を識別できない / **放置すると、R 前の正当な WAL が R 発行後に `protocol_violation` へ変わる一方、issued-but-missing/invalid または pre-R の `repo_root` を与えた post-R key 欠落 WAL は `completed` のまま受理され、judge が determinate になり得る。** / 修正案: campaign-start または manifest に producer HEAD を耐久記録し、その HEAD に R が祖先かで epoch を決める。envelope は記録された `validation_head` で receipt を再検証する。

[2] [BLOCKER] / real-repo golden の状態 oracle が production resolver と自己参照しており、「どちらでも緑」である / 根拠: テスト自身が `migration.verify_receipt()` の返値で期待分岐を選ぶ [test_s8b_oracle_driver.py:699](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:699) 一方、検査対象の `gate_check()` も同じ resolver を使う [s8b_oracle_driver.py:411](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:411)。active 分岐も observation は production 定数との schema 比較と件数 17 だけである [test_s8b_oracle_driver.py:721](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:721) / **放置すると、R 発行後に resolver が誤って `never-issued` を返し、gate が旧 4 拒否＋observation nullへ退行しても、この golden は旧分岐を選んで緑になる。** / 修正案: テスト側の独立した最小 Git 履歴検査で R の有無を確定し、never-issued は 4 prefix 1:1、post-R は 2 全文と独立 literal の exact 17 items を固定する。

[3] [BLOCKER] / report は WAL envelope を検証済み receipt observation に束縛していない / 根拠: canonical 検査は形と production 定数だけを検査し、receipt hash、H_mig、H_v、observed hash は任意の正規 hex を許す [s8b_oracle_report.py:105](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:105)。`receipt_resolution.t080_freeze_migration_observation` は比較に使われず、全 campaign の偽 envelope が同一なら sibling へ転記される [s8b_oracle_report.py:1455](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1455)。テストも resolver と WAL に同じ fixture を与える正例しかない [test_s8b_oracle_report.py:2551](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_report.py:2551) / **放置すると、全 campaign が同じ偽値を出せば receipt raw hash、H_mig、H_v、17件の observed 参照が虚偽でも rows は completed、judge は determinate のままになる。** / 修正案: envelope の `validation_head` で receipt を再解決し、得た observation と canonical bytes 完全一致を要求する。never-issued 時の object も拒否し、「全 campaign 同じだが resolver と異なる」負例を追加する。

[4] [MAJOR] / 1 campaign の malformed envelope が無関係な全 campaign を巻き添えにする / 根拠: `_assess_campaign()` は既に当該 campaign の row へ issue を付ける [s8b_oracle_report.py:1096](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1096) が、後段で malformed issue を全 `by_ordinal` row に再適用する [s8b_oracle_report.py:1441](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1441)。負例は単一 campaign だけである [test_s8b_oracle_report.py:2498](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_report.py:2498) / **放置すると、1 campaign の malformed WAL だけで正常な別 campaign の全 row も `protocol_violation` となり、受理済み観測集合と judge 結果が全体で失われる。** / 修正案: malformed は campaign-local の処理だけにし、valid/malformed の2 campaign負例で正常側の completed を exact pin する。

[5] [MAJOR] / 13+2 の exact golden が production 定数から動的生成され、primary active 経路では §1.4 の本体検査を全て stub 化している / 根拠: production の repin/metadata 表 [t080_freeze_migration.py:87](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:87) を U0 fixture [test_t080_freeze_migration.py:50](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_t080_freeze_migration.py:50)、U1 fixture [test_s8b_oracle_driver.py:102](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:102)、U2 envelope [test_s8b_oracle_report.py:70](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_report.py:70) が直接列挙する。active 正例では artifact、repin、positive、ccbench、closure、reconstruction、live/static の全関数を成功へ置換する [test_t080_freeze_migration.py:335](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_t080_freeze_migration.py:335)、[test_s8b_oracle_driver.py:213](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:213)。これは D68(7) 禁止形 [freeze-permanent-design.md:376](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:376) と同型 / **放置すると、repin pointer/hash/orderまたは §1.4 の closure・schema・pairing・ccbench・layer2 呼出しが production 側で同時にずれてもテスト fixture が追随し、異なる H_mig 証拠・受理集合のまま緑になる。** / 修正案: 13+2を test-side 独立 literal に固定し、全検査を実行する active-valid hermetic public-path 正例を作る。各 §1.4 項目は単独欠陥で exact refusal を要求する。

[6] [MAJOR] / U4 の「呼ばれたら fail」stub は receipt が実際に有効な consumer 経路へ配線されていない / 根拠: 4 test は tmp 下の `T080.ROOT` だけを差し替えるが、measurement は実 `M.FREEZE_PATH` [test_s1_measurement_freeze.py:266](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:266)、calibration は実 known freeze [test_s1_verify_extime_calibration.py:135](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_verify_extime_calibration.py:135)、report は `report.ROOT` [test_s1_report.py:423](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_report.py:423)、direct comparison は定義時に束縛された default path [test_s1_direct_comparison.py:130](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_direct_comparison.py:130) を使い、いずれも既知の legacy source drift で早期終了する。AST は同一ファイルの直接 `Import/ImportFrom` 名だけを見る / **放置すると、legacy verify 成功後の late adapter、helper 経由、動的 import による receipt-aware 経路が4 consumerの受理 freeze を変えても、stub到達前に既知 drift で終了して全 pin が緑になる。** / 修正案: consumer が読む同一 root に receipt と完全 valid な legacy fixture を置き、成功終端まで通す。import は依存 closure／参照 call graph を検査する。

[7] [MAJOR] / 書換 node `test_tampered_freeze_fails_source_verification` から旧 legacy generator 検出力が失われ、代替 node がない / 根拠: 旧 node は generator SHA、known source、floor、budget の4 prefixを固定していた（`64c13dc:orchestrator/tests/test_s8b_oracle_driver.py:1224-1231`）。現 node は holdout `_verify_source` と known verifier を patch し [test_s8b_oracle_driver.py:1543](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1543)、confirmed_by＋floor＋budgetだけを検査する [test_s8b_oracle_driver.py:1551](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1551)。floor/budget は維持、known source は他面に残るが、legacy generator mismatch の専用負例は消失 / **放置すると、never-issued/legacy verifier の generator 自己 hash 照合が退行して stale generator を受理しても、R 発行後の suite に検出 node が残らない。** / 修正案: J9 の書換 node は維持し、別の never-issued hermetic nodeで generator bytesだけを変え、generator refusal 1件を exact pin する。

[8] [MAJOR] / M01..M14 のうち M02・M05・M06・M07・M13 は現在の fixture/実装では F28 の acceptance kill として数えられない / 根拠: M02 の R後 repo は receipt以外の artifactを持たず [test_t080_freeze_migration.py:306](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_t080_freeze_migration.py:306)、登録どおり state を never-issued化すると後段 artifact readで再拒否される [t080_freeze_migration.py:1205](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1205)。M05 は `inspect` の refusal文字列消失を `[0]` で検出するだけで、mutant後も state は `invalid` [test_t080_freeze_migration.py:411](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_t080_freeze_migration.py:411)、[t080_freeze_migration.py:1467](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1467)。M06 は独立 ccbench mismatchを同時注入する [test_t080_freeze_migration.py:392](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_t080_freeze_migration.py:392)。M07 の receipt bytes は `{}` で schema invalidのまま [test_t080_freeze_migration.py:431](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_t080_freeze_migration.py:431)。M13 は最初の layer2 assertを外しても downstream `verify_document()` が同じ report を再検査する [t080_freeze_migration.py:1509](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1509)、[s8b_holdout_freeze.py:714](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:714) / **放置すると、拒否→拒否の診断変化を KILLED と数え、receipt再発行、R topology、履歴不変、live layer2 の受理集合退行を検出したという誤った mutation 成果物になる。** / 修正案: M02/M05/M07 は全検査を通る receipt repoで mutant時 `active-valid`/draft成功まで到達させる。M06 は ccbench mismatch を別 nodeへ分離する。M13 は冗長検査を保つなら invalid candidate と明記する。M11 は現状 kill 可能だが、`drift.txt` 追加ではなく登録どおり same-tree empty commitを使う。静的に成立するのは M01・M03・M04・M08〜M12・M14。

[9] [MAJOR] / §1.6 の AST 非回帰 test は名前どおり「全 factory／全 return」を検査していない / 根拠: constructor scan は `tree.body` の top-level function内にある裸の `ast.Name("GateDecision")` だけ [test_s8b_oracle_driver.py:779](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:779)。return scan は値が literal `ast.Dict` の場合だけ検査し、検査件数も `>=3` である [test_s8b_oracle_driver.py:794](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:794)。現行の早期 return 自体には observation があるが、変数・helper・conditional expressionへ書き換えると無検査になる / **放置すると、新しい早期 return だけ observation keyを落とし、post-R WAL/reportを欠落させても meta-testが緑のままになる。** / 修正案: result生成を単一 factoryへ集約し、全ASTの constructor callと `run_block` の全 return siteを exact allowlistで検査する。

所見外の突合結果: 12変更ファイルは U1〜U4 の所有表に全件収まり、追加 node は U0=29、U1=6、U2=9、U3=3、U4=8、合計55、消失0で単位報告と一致した。refusal helper は件数＋集合完全一致を維持しており [test_s8b_oracle_driver.py:58](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:58)、real payload の prefix helperも件数＋1:1対応である。実 HEAD/hash の期待値焼き込みは新規差分に見当たらない。§1.4 の production call列挙、§1.5 prefix/一ドット grammar、現行 §1.6 return結線は存在する。

post-R の `REAL_REPO_SERIAL_NODES`／serialization golden は node名固定だけ、repo scan invariantは holdout hit集合、`test_frozen_artifacts` は既存8ファイルだけを検査するため、receipt追加そのものでは赤くならない。受入不能なのは上記 report 時系列と self-oracle goldenである。なお `git status` には未追跡 `docs/handoff/2026-07-22-t080-migration-contract.md` が残り、draft前には clean化が必要。

総合判定: **NO-GO**。

## §10 親 fix 指令 F-1..F-8

# 段 6 fix 指令 (親裁定 — レビュー A/B 全所見の処理。refuted 0)

対象 = 統合 commit 7b8e843 の上。正本 = ruling_v2.md (J1..J13) / plan_v2.md。本指令が plan v2 と
矛盾する場合は本指令が優先する (レビュー反映)。

## F-1. gate 検証から verify_document 再利用と monkeypatch を全廃 (A3 根治)

- `_verify_live_and_static_documents` を削除する。**production コードから他 module の属性差替えを
  ゼロにする**
- draft 時の holdout 検証は `verify_document(projected, root=root, current_head=legacy_head)` を
  **無 patch** で呼ぶ (s8b_holdout_freeze.py:665-673 実測 — current_head 指定時は等価比較のみで
  git を呼ばない。worktree==H_mig なので _verify_source も自然に通る)。search_repository の再実行は
  そのまま許す (二重 scan は draft 時のみのコスト)
- gate 時 (verify_receipt) の holdout 検査 = (a) raw bytes == receipt pin (statics は byte-pin が
  含意 — 理由を docstring と D78 へ)、(b) 公開 API `search_repository` + `_assert_search_pass` の
  live 層2、(c) positive control raw root、(d) closure、(e) ancestry。known 側 = raw bytes pin +
  closure + `_validate_schema`/`assert_s1b_pairing` (pure 関数、patch 不要) + ccbench live/basis +
  ancestry

## F-2. receipt 証拠の決定論的再導出 (A1)

- `validate_draft` と `finalize` は再構成 (S-1 builder + holdout projected verify + live scan) を
  **再実行**し、stored `reconstruction` の全 hash (projected/rebuilt/live_scan_sha256) と exact
  一致を要求する (現状 validate-draft は builder 非実行 — 変更する。HEAD==H_mig 前提は既存どおり)
- `verify_receipt` は receipt の**決定論 field を H_mig から全再導出**する: artifacts、
  source_repins (13 件全値)、metadata_fields、repin_report (provenance/diff 数値含む)、
  reconstruction.projected_document_sha256 (静的射影で再計算)。再導出値と receipt 記録値の不一致 =
  refusal `receipt.derivation_mismatch`。rebuilt hash は schema で projected と同値強制 (known)。
  holdout live_scan_sha256 は post-R 再導出不能 — 64hex 形式のみ検査し、**残余 (builder 実走の実在は
  finalize の fail-closed + 人間確認に依存) を D78 へ明文化**
- 効果: 手製 receipt は「draft が出力するものと byte 同値」以外 verify を通らない

## F-3. draft 基盤の強化 (A2 — 部分採用)

- status/diff 系 git 呼び出しへ `-c core.fsmonitor=false -c core.untrackedCache=false` 等を付与、
  `rev-parse --show-toplevel` == root を確認
- builder 実行前に、import する checker 2 file (s1_known_axes_freeze.py / s8b_holdout_freeze.py) と
  13 repin path の worktree bytes を H_mig blob と nofollow で直接照合する (clean 判定への上乗せ)
- 検証済み専用 loader までは作らない (過剰 — 却下理由を D78 へ)

## F-4. TOCTOU / merge 辺 / 層継続 / observation の事実性 (A6, A7, A8)

- `ReceiptResolution` に R blob bytes (immutable) を保持し、observation の raw_sha256 はそこから
  計算する (worktree 再読を廃止)
- `_history_touches_path` の diff-tree に `-m -r` を付与。blob 比較に mode も含める
- verify_receipt の検査群を独立 callable に分離し、1 つの例外で後段が飛ばない形へ (checks list は
  既存 — bundle を分解する)。`issued-but-missing` でも独立検査 (closure/ccbench/ancestry/層2) を
  継続して refusal を蓄積する (J2 の refusal は必ず残す)
- **refusals が 1 件でもあれば observation = null** (拒否時に 17-item clean envelope を返さない)。
  AdapterResult / GateDecision / WAL / report まで一貫

## F-5. report の epoch 正常化と envelope 束縛 (A4, A5, B1, B3, B4)

- campaign-start の value grammar を変更: bare null を廃し、
  `{"state": "never-issued", "validation_head": H_v}` | full envelope (active-valid) の 2 形とする
  (driver 側 F-6 と対)。key-absent = R 導入前の歴史 WAL (許容、WAL 信頼境界 D68 (6) の残余として
  D78 に明文化)
- report は `inspect_receipt_history` (history-only、live scan なし) で R の有無と R blob を取得し、
  campaign ごとに: (a) envelope record → R が record.validation_head の ancestor であること +
  envelope 全 field が R blob からの再導出と canonical 一致すること、(b) never-issued record →
  R が record.validation_head の ancestor で**ない**こと、を検査。違反は**当該 campaign のみ**
  protocol_violation (B4 — malformed の全体巻き添えを廃止)
- report 生成時に receipt が issued-but-missing / invalid → R 後の全 campaign を violation とし、
  top-level sibling は null

## F-6. driver 側の対応 (F-4/F-5 の配線)

- campaign-start / run result / CLI の observation key 値を新 grammar に合わせる (never-issued 時は
  {state, validation_head})
- GateDecision の observation は active-valid かつ refusals 空のときのみ envelope、それ以外 null

## F-7. テスト修正 (B2, B5, B6, B7, B9 + F-1..F-6 追随)

- **B2**: real-repo golden の分岐選択を production resolver でなく**テスト内の独立最小 git 検査**
  (`git log --format=%H -- output/t080-migration/...receipt.json` の空/非空 + blob 読み) で行う。
  active 分岐の 17 items はテスト側独立 literal と比較
- **B5**: 13+2 の期待値をテスト側独立 literal に固定 (production 定数からの動的生成を廃止)。
  **stub なしの end-to-end hermetic 正例**を追加: temp repo に freeze 一式 + 疑似 submodule gitlink +
  実 draft → finalize → R commit → `gate_check` 公開経路で active-valid = {floor-null, budget-null}
  になるまで。§1.4 各項目の単独欠陥 → 単独 exact refusal の負例群を同 fixture 派生で
- **B6**: U4 の stub pin を「成功終端まで通る temp fixture」上で行う (既知 drift での早期終了に
  隠れない)。import 検査は直接 import + t080 識別子のソース走査へ拡張
- **B7**: never-issued 経路の legacy generator tamper 負例 node を新設 (generator refusal 1 件 exact)
- **B9**: AST meta-test を強化 — module 全体の GateDecision 呼び出し site を exact allowlist
  (factory 1 箇所) で検査、run_block の全 return site 列挙も allowlist 化

## F-8. 変異の再登録 (B8 + M07 — fix 後に親が再実測)

- M02/M05/M06/M07 を「mutant 適用で active-valid / draft 成功へ反転する full-valid fixture」形へ
  再登録 (受理集合の反転を kill 判定にする)。M06 の ccbench 同時注入を分離
- M13 は F-1 により gate 層2 が単層化するため**有効な変異として復活登録**
- M07 は F-4 の diff-tree 変更後に両層同時変異 (OID 等価 + touches-path) として再登録
- M11 は登録どおり same-tree empty commit fixture へ修正
- 変異は実装せず、spec (old/new/expected_red) の再登録案を完了報告に含める (実測は親)

## 不変条件 (変更なし — 再掲)

- 凍結 3 JSON / no-touch manifest 12 file は 1 byte も変更しない (s8b_holdout_freeze.py も
  no-touch のまま — F-1 は t080 側の変更だけで成立する)
- 既存 node の削除禁止。追加/書換は台帳必須
- 期待値の揮発 payload 焼き込み禁止。hermetic は全文 exact


## §11 fix ラウンド 1 報告

実装完了しました。F-1→F-7 を順番に適用し、最終結果は全体で **2683 passed / 26 skipped / 0 failed** です。docs・commit・no-touch 12 file は変更していません。

## F-1〜F-7

| 項目 | 実装内容 |
|---|---|
| F-1 | cross-module monkeypatch、lock、`_verify_live_and_static_documents` を削除。draft は legacy verifier と明示 scan、gate は schema・pairing・公開 live scan を直接実行。[draft reconstruction](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1254)、[gate schema](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1683)、[live scan](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1711) |
| F-2 | Hmig から artifact/source repin/metadata/repin report/reconstruction hash を再導出し、不一致を `receipt.derivation_mismatch` で拒否。validate/finalize で S-1 builder と holdout scan を再実行。[導出](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1040)、[照合](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1092)、[再構成](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1295)、[validate](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1527) |
| F-3 | Git hardening に `core.fsmonitor=false`、`core.untrackedCache=false` を追加。repo root を固定し、checker 2 file と全 repin target の nofollow bytes・実行 mode を Hmig と照合。[hardening](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:551)、[root](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:616)、[basis file検証](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1342) |
| F-4 | R blob raw を一度だけ保持。merge の path 履歴を `diff-tree -m -r` で検査し、OID・mode を descendants 全体で検証。issued-but-missing でも artifact/ancestry/ccbench/closure/schema/pairing/layer2 等を独立継続し、拒否時 observation は必ず null。[ReceiptResolution](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:154)、[履歴検査](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:791)、[resolver](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1577)、[verify](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1762)、[adapter](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1856) |
| F-5 | WAL grammar を never-issued record または完全 envelope に限定。bare null を拒否し、historical validation head の Git blobから envelope を再構成。campaign 間の canonical 一致要求を廃止し、違反は campaign-local 化。[never-issued grammar](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:179)、[historical envelope](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:195)、[campaign観測](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:219)、[report構築](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1457) |
| F-6 | campaign-start には never-issued record または active envelope を保存。gate decision は active-valid かつ merged refusal が空の場合だけ envelope を公開し、それ以外は null。[decision factory](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:110)、[campaign値](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:125)、[run接続](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1110) |
| F-7 | 独立 golden、stub-zero E2E、§1.4 各境界、F28 full-valid fixtures、B7 generator tamper、AST factory/return exact pin、U4 success-terminal/source closure を追加・更新。[stub-zero E2E](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:347)、[§1.4 defects](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:446)、[F28 history](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:532)、[AST pin](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1180)、[B7](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1996) |

指令からの逸脱はありません。

補足として、`live_scan_sha256` は draft file の生成などで変動する `search.file_count` を含めず、受理判定に関わる `match_convention`・`holdouts`・`positive_control` を hash 対象にしました。[実装](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1286) これは揮発 payload を期待値に固定しないための実装詳細です。

## node 台帳

収集 node は **342 → 360**、追加18、削除0です。追加18は parameter 展開後の数で、追加 test function は13個です。

追加:

- `test_t080_freeze_migration.py`: F1 production assignment、F2 derivation、F2 live scan、F3 basis、F4 issued-but-missing、F4 mode/merge、F4 static adapterの7個。
- `test_s8b_oracle_driver.py`: B7、F28 history、F28 post-R delete、stub-zero正例、stub-zero単独defect、§1.4残存境界の6個。parameter 展開により11 node。

書換21:

- `test_t080_freeze_migration.py`: `test_invalid_r_topology_keeps_independent_ccbench_refusal_j4`、`test_state_modify_then_revert_is_issued_but_missing`
- `test_s8b_oracle_driver.py`: gate factory AST、real freeze gate、run_block propagation、primary states、tampered freeze、v2 report adapterの6個
- `test_s8b_oracle_report.py`: pre-R absent/null、post-R missing、post-R null、campaign envelope mismatch、pre-R mixtureの5個
- U4各ファイル: receipt success-terminal 4個、production import/source closure 4個

削除: **0**

`test_s8b_oracle_artifacts.py` は許可対象でしたが変更していません。

## テスト結果

段階実走:

- F-1: core `30 passed`、driver `66 passed, 1 skipped`
- F-2: core `31 passed`、driver `66 passed, 1 skipped`
- F-3: core `32 passed`、driver `66 passed, 1 skipped`
- F-4: core `35 passed`、driver `66 passed, 1 skipped`
- F-5/F-6: report＋artifacts `180 passed`、driver `66 passed, 1 skipped`
- F-7 初回統合: `358 passed, 1 skipped`
- plain runner: `python3 orchestrator/tests/test_t080_freeze_migration.py` → `36 passed`
- 最終許可テスト群:

```text
python3 -m pytest -q \
  orchestrator/tests/test_t080_freeze_migration.py \
  orchestrator/tests/test_s8b_oracle_driver.py \
  orchestrator/tests/test_s8b_oracle_report.py \
  orchestrator/tests/test_s8b_oracle_artifacts.py \
  orchestrator/tests/test_s1_measurement_freeze.py \
  orchestrator/tests/test_s1_verify_extime_calibration.py \
  orchestrator/tests/test_s1_report.py \
  orchestrator/tests/test_s1_direct_comparison.py

359 passed, 1 skipped
```

- 最終全体: `python3 -m pytest -q` → **2683 passed, 26 skipped, 0 failed**
- `python3 tools/check_codex_agents.py` → OK
- `python3 tools/check_docs.py` → 違反なし
- `git diff --check` → clean
- no-touch 12 file → `sha256sum -c` 全件 OK

開発中の赤は2件でした。

- 全体初回の1件: U4 source scan のテスト文字列自身が禁止 conjunction を含んだため。literal を分割して解消。
- 追加した§1.4 test の1件: schema 拘束外の `what` を改変していたため。未知 top-level key `unexpected` に変更して解消。

skip 1件は slow real-build testで、initialized ccbench `.git` と pinned `cmake/gcc-13/g++-13/nm` が揃う場合のみ実行される既存条件です。sandbox/submodule 制約による偽赤はありません。

## F-8 再登録案

F-8 の mutant 自体は指令どおり実装していません。

### M02′

```python
# old
if state.state != "never-issued":

# new
if state.state not in {"never-issued", "issued-but-missing"}:
```

Fixture: full-valid R を発行後、receipt を削除して clean commit、`draft_receipt` 実行。  
expected_red: `receipt.invalid` 1件。mutant では draft 成功。

### M05′

```python
# old
if not _is_none_commit(commit, root):

# new
if False and not _is_none_commit(commit, root):
```

Fixture: full-valid R、trailer のみ `AI-Agent: codex`。  
expected_red: `receipt.user_commit_trailer` 1件。mutant では active-valid。

### M06′

```python
# old
if out.splitlines() != [f"A\t{RECEIPT_REL}"]:

# new
if False and out.splitlines() != [f"A\t{RECEIPT_REL}"]:
```

Fixture: R で receipt と無関係1 fileを同時追加。ccbench defectなし。  
expected_red: `receipt.introduction_diff` 1件。mutant では active-valid。

### M07′

```python
# old
if any(oids.get(commit) != expected_oid for commit in descendants):

# new
if False and any(oids.get(commit) != expected_oid for commit in descendants):
```

かつ同時に:

```python
# old
if any(
    commit != introduction and _history_touches_path(commit, RECEIPT_REL, root)
    for commit in descendants
):

# new
if False and any(
    commit != introduction and _history_touches_path(commit, RECEIPT_REL, root)
    for commit in descendants
):
```

Fixture: full-valid R → validだが別bytesのreceipt → 元bytesへrevert。  
expected_red: `receipt.history_mutated` 1件。両層同時 mutant で active-valid。

### M11′

```python
# old
if _current_ccbench_head(root) != pin:

# new
if False and _current_ccbench_head(root) != pin:
```

対象は gate 側 `_verify_ccbench_current`。Fixture は同じ tree の empty commitへ submodule HEAD のみ移動。  
expected_red: `known_axes.ccbench_current` 1件。mutant では active-valid。

### M13′

```python
# old
holdout_module._assert_search_pass(report)

# new
if False:
    holdout_module._assert_search_pass(report)
```

対象は `_verify_holdout_live_scan` 内の単層 gate 検査。Fixture は full-valid R と untracked rr80 3軸 conjunction。  
expected_red: `holdout.unknownness_layer2` 1件。mutant では active-validとなり、public gate は floor/budget だけを残す。

F28の2条件については、全候補で次を確認済みです。

- 「先行検査なし」: stub-zero full-valid正例が全検査を通り、各 defect fixture は対象理由ちょうど1件だけで拒否。
- 「predicate無効化で受理集合が反転」: 上記 old/new と同じ fixture から active-validまたはdraft成功へ到達する経路を静的確認。mutant の実適用・再実測はF-8を担当する親作業に残しています。

## B5 stub

B5 の end-to-end hermetic 正例で温存した stub は **0件** です。production の draft → validate → finalize → R commit → verify → public gate → historical report envelope を、実 freeze/source一式と実 ccbench gitlinkで通しています。

docs は編集せず、git commitも作成していません。既存の未追跡 `docs/handoff/2026-07-22-t080-migration-contract.md` も未変更です。

## §12 焦点再レビュー (fix ラウンド 1 の閉鎖判定、NO-GO)

## 所見対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| A1 | partial | repin 等は H_mig blob から導出するが、`rebuilt_document_sha256` は builder を走らせず projected hash を代入し、`live_scan_sha256` も gate 再導出対象外。`t080_freeze_migration.py:1040,1062,1072,1527` |
| A2 | partial | root 一致・Git cache 無効化・checker 2 本＋repin path の bytes/mode 照合は追加。ただし実ロード module／依存 closure は束縛されず、別 root の既ロード module を実行可能。`t080_freeze_migration.py:551,616,1342` |
| A3 | closed | production の cross-module attribute 差替えは消滅。draft は verifier を直接呼び、gate は search API を直接使用。`t080_freeze_migration.py:1254,1711` |
| A4 | regressed | structured record の per-head 判定は追加されたが、key-absent を現在の R 状態に関係なく許容。post-R key 削除を `completed`・judge `determinate` とするテストまで追加。`s8b_oracle_report.py:228`、`test_s8b_oracle_report.py:2448` |
| A5 | partial | receipt raw hash と ancestry は Git 由来だが、basis と 15 observed 値は R blob 内の receipt からそのまま observation 化。report は derivation を検証しない。`s8b_oracle_report.py:195,214,1467` |
| A6 | partial | observation の hash は immutable `receipt_raw` 由来になった。一方 driver は `verify_receipt()` 後、HEAD/path を再確認せず campaign-start まで使用。`t080_freeze_migration.py:147,1727`、`s8b_oracle_driver.py:1024,1185` |
| A7 | closed | `diff-tree -m -r`、copy/rename 検査、descendant の OID＋mode 照合を実装。`t080_freeze_migration.py:791,1622` |
| A8 | partial | issued-but-missing 後も検査を継続し、refusal 時 observation=null は成立。ただし live search が `MigrationError` へ包まれず、例外一件で後続検査が飛ぶ。`t080_freeze_migration.py:1719,1794,1811,1821` |
| B1 | regressed | A4 と同じ。full/never-issued record は改善したが、key-absent branch は以前より広く fail-open。`s8b_oracle_report.py:228`、`test_s8b_oracle_report.py:2465` |
| B2 | partial | R 有無の分岐は独立 `git log/show` になったが、active golden の observed 値は receipt からコピーし続ける。`test_s8b_oracle_driver.py:122,1062,1089` |
| B3 | partial | A5 と同じ。historical expected envelope は R blob を独立検算せず、同じ R blob の値を期待値へ転記。`s8b_oracle_report.py:195-216` |
| B4 | closed | malformed issue は `_assess_campaign()` 内の当該 campaign にだけ入る。二 campaign test も正常側 completed を固定。`s8b_oracle_report.py:1144,1165`、`test_s8b_oracle_report.py:2525` |
| B5 | partial | 13+2 の recorded 値は test literal 化し、stub なし正例も追加。ただし observed は literal でなく、§1.4 の多くの負例は public gate でなく private helper 直呼び。`test_s8b_oracle_driver.py:57,347,446` |
| B6 | partial | 成功終端には進むようになったが、3 consumer は verifier を lambda 注入で迂回し、静的検査も当該一ファイルの import/name scan に留まる。`test_s1_direct_comparison.py:146`、`test_s1_verify_extime_calibration.py:151`、`test_s1_report.py:437` |
| B7 | partial | 追加 node は never-issued driver 経路ではなく `_verify_source()` の直接単体テスト。consumer 配線退行を検出しない。`test_s8b_oracle_driver.py:1953,1996` |
| B8 | partial | M02′/M05′/M06′/M07′は成立。M11′/M13′の `old` は現物に各2箇所あり一意性違反。詳細は後述。 |
| B9 | closed | GateDecision constructor は exact 1 site、`run_block` の全 return を exact allowlist 化。`test_s8b_oracle_driver.py:1180-1244` |

## 新規所見

[1] [BLOCKER] / report の historical envelope 再構成が R blob に対して恒真 / 根拠: history resolver は schema/topology までしか検証せず、正常 topology でも `state="invalid", refusals=()` を返す。[t080_freeze_migration.py:1651](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1651) report はその receipt の repin/metadata/basis を `_make_observation()` へそのまま渡し、current invalid 判定も history refusal の有無だけを見る。[s8b_oracle_report.py:195](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:195) [s8b_oracle_report.py:1467](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1467) / **影響:** H_mig blob と一致しない15件の observed・偽 basis を持つ手製 R/WALでも completed rows と determinate judge を生成できる。 / 修正案: history-only validator でも `_verify_receipt_derivation()`、closure、projected hash を実行し、検証済み専用 state からだけ envelope を作る。

[2] [BLOCKER] / per-campaign epoch は key-absent と自己申告 `validation_head` で fail-open / 根拠: key-absent は無条件 `absent` で終了し、現在 R が active かを見ない。[s8b_oracle_report.py:228](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:228) テストは post-R envelope から key を削除した後も completed/determinate を明示要求する。[test_s8b_oracle_report.py:2448](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_report.py:2448) never-issued も WAL 自身が選んだ任意の pre-R SHA を検査するだけ。[s8b_oracle_report.py:237](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:237) / **影響:** post-R campaign が key を落とすか古い pre-R HEAD を申告すると、proof 欠落のまま正式観測へ入る。 / 修正案: campaign epoch を manifest/execution receipt と耐久的に束縛し、R 到達後の key-absent は拒否する。旧 absent を残すなら producer version と導入 commit を独立に証明する必要がある。

[3] [BLOCKER] / `_derive_deterministic_fields()` は一部 H_mig 独立導出だが、再構成実走の証明は恒真 / 根拠: source repin/metadata は確かに H_mig blob から導出する。[t080_freeze_migration.py:1185](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1185) 一方 known の rebuilt hash は builder 出力でなく `known_sha` をそのまま代入し、holdout live scan は比較対象から除外される。[t080_freeze_migration.py:1055](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1055) [t080_freeze_migration.py:1072](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1072) / **影響:** H_mig builder/verifierなら draft 自体が失敗する状態でも、正しい projected hashを書いた手製 Rは active-valid になれる。 / 修正案: R を事前 commit 済み draft/template bytesへ束縛する二段 topology、または検証済み H_mig loader による独立 builder 再実行を必要とする。

[4] [BLOCKER] / F-1 簡素化で live scan が「凍結済み検索式を検索した」ことを失った / 根拠: 新 gate は current `search_repository()` と `_assert_search_pass()` しか呼ばない。[t080_freeze_migration.py:1711](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1711) 旧 static verifier が行う frozen expressions と live report の一致、positive expressions、binding 照合は byte pin の範囲外。[s8b_holdout_freeze.py:773](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:773) [s8b_holdout_freeze.py:798](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:798) / **影響:** current scanner が別 holdout／別正規表現へ drift して0-hitなら、元の rr80/rr20 が既知でも gate を通す。 / 修正案: projected holdout の candidate/expression/match convention と live report を完全照合するか、凍結 document から直接 scan predicate を構築する。

[5] [MAJOR] / stub-zero 正例は文字どおり stub 0 だが hermetic ではない / 根拠: fixture は checker を temp repoへコピーするが、同一 process で既ロード production moduleを呼ぶ。[test_s8b_oracle_driver.py:279](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:279) S-1 builder の `ROOT` は module 自身の実 worktreeに固定され、入力 `root` ではない。[s1_known_axes_freeze.py:20](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:20) [s1_known_axes_freeze.py:99](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:99) / **影響:** temp H_mig の checker/module loader が壊れていても、host worktree の正常 moduleで draftを作って正例が緑になる。 / 修正案: temp repoを先頭 `sys.path` にした隔離 subprocessで実行し、全 moduleの `__file__`/ROOTが fixture root配下であることを固定する。

[6] [MAJOR] / A6 の campaign-start 境界 TOCTOU が残る / 根拠: `run_block()` は receipt を1024行で一度解決し、ratified/manifest/preflight/claim 後の1185行まで HEAD・receipt path・rawを再確認しない。[s8b_oracle_driver.py:1024](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1024) [s8b_oracle_driver.py:1185](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1185) / **影響:** branch切替やreceipt一時差替え後も、古い active-valid epochをcampaign-startへ耐久化できる。 / 修正案: campaign-start直前に再解決し、HEAD/introduction/raw/stateが最初の resolution と完全一致しなければ副作用前に拒否する。

[7] [MAJOR] / campaign-start grammar は直前 producer と後方互換でない / 根拠: 7b8e843 の producer は never-issued 時にも observation `None` をそのまま書いた（`7b8e843:orchestrator/campaign/s8b_oracle_driver.py:1162-1168`）。現 report は bare null を常時拒否する。[s8b_oracle_report.py:233](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:233) 「null」testも実際には never-issued objectへ差し替えられ、旧 null fixtureを検査していない。[test_s8b_oracle_report.py:2418](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_report.py:2418) / **影響:** 7b8e843 producerで既に書かれた pre-R null WALが、fix後に protocol_violationへ反転する。 / 修正案: producer schema/versionで旧 nullを識別するか、互換を切るなら既存WAL不存在の機械証明と明示migrationを追加する。

[8] [MAJOR] / J4 の全層継続は search infrastructure 例外で破れる / 根拠: `search_repository(root)` は try の外で、`FreezeError` 等を `MigrationError` に変換しない。[t080_freeze_migration.py:1718](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1718) 呼出側ループは `MigrationError` だけを捕捉する。[t080_freeze_migration.py:1811](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1811) / **影響:** 読取不能fileやGit列挙異常があると、後続closure/schema/derivation所見が消えて単一generic refusalになる。 / 修正案: search と assertion の両方を `holdout.unknownness_layer2` へ正規化し、各check境界で想定外例外も個別 refusal化する。

[9] [MAJOR] / F28 再登録案の M11′・M13′は `old` が一意でない / 根拠:

| 変異 | `old` 出現 | expected_red 単一理由 | 判定 |
|---|---:|---|---|
| M02′ | 1 (`t080_freeze_migration.py:1378`) | yes — `test_s8b_oracle_driver.py:558` | 成立 |
| M05′ | 1 (`:846`) | yes — full-valid fixtureでlen=1 (`:532`) | 成立 |
| M06′ | 1 (`:844`) | yes — 同上 | 成立 |
| M07′ | 1＋1 (`:1622`, `:1633`) | yes —重複reasonはdedup、fixture len=1 | 成立 |
| M11′ | 2 (`:1384`, `:1845`) | baselineは単一 | **old非一意** |
| M13′ | 2 (`:1421`, `:1721`) | baselineは単一 | **old非一意** |

加えて mutant 実適用は未実施と完了報告自身が認める。[fix1.md:178](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/fix1.md:178) / **影響:** raw置換harnessではdraft側まで同時変異するか、多重matchで停止し、狙ったgateのkill帰属を確定できない。 / 修正案: function-qualified AST locatorまたは前後context込みoldを登録し、match count=1を事前assertしてから実測する。

[10] [MAJOR] / F-1/F-2/F-3/F-5 が要求した D78 が現物に存在しない / 根拠: canonical decisions の末尾headingは D77。[decisions.md:3068](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:3068) 一方完了報告は「逸脱なし」としながら docs未編集を明記する。[fix1.md:15](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/fix1.md:15) [fix1.md:187](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/t080-migration/fix1.md:187) / **影響:** live_scan非再導出、verified loader不採用、key-absent残余という受理集合上の損失が正本に残らず、発効承認が過大保証になる。 / 修正案: R発行前にD78を追加し、各残余・回収層・後方互換境界を明記する。

## 総合判定

**NO-GO**

report の偽 proof 受理、post-R key 欠落の determinate 化、builder 実走証拠の恒真化、live scan の検索式未束縛がいずれも受理集合を広げる。静的監査のみで、read-only 指示に従いテスト・変異実走・変更は行っていない。

## §12b 親 fix 指令 2 (G-1..G-7)

# fix ラウンド 2 指令 (焦点再レビュー FR1..FR10 の親裁定)

対象 = commit 1c1b342 の上。FR3/FR7/FR10 と partial 残余 (A2/B2/B6) は D78 明文化で処理 (実装しない)。

## G-1. gate の live scan を凍結検索式へ束縛する (FR4 — BLOCKER 採用)

`_verify_holdout_live_scan` (t080) で、live `search_repository` の report を frozen holdout doc の
記録値と照合する: 各 holdout の `unknownness_check.expressions` == live report の expressions、
`match_convention` == doc 記録値、candidate 集合 (rr80/rr20) の対応。不一致 = refusal
`holdout.unknownness_layer2` (検索式 drift は層2 の実効性喪失)。_assert_search_pass はその上で実行。
比較は公開データ同士 (monkeypatch 禁止のまま)。

## G-2. report の歴史 envelope に derivation 検査を通す (FR1 — BLOCKER 採用)

report の historical R 解決経路で、R blob の receipt に対して `_verify_receipt_derivation` 相当
(H_mig blob からの決定論再導出 — git 履歴から可能) を実行し、失敗なら R 後の全 campaign を
protocol_violation とする。observation/expected envelope は検証合格後の値のみから作る。

## G-3. key-absent の全面拒否 (FR2 厳格化 — 親裁定変更)

- 「key-absent = 歴史 WAL 許容」を**廃止**する。公式 gate は一度も通っておらず (floor/budget null が
  発足以来続いている)、歴史 WAL は存在しない — campaign-start に T-080 key が無い record は epoch を
  問わず当該 campaign の全 row を protocol_violation とする
- fix1 で追加された「post-R key 削除 → completed/determinate を要求するテスト」は**削除でなく反転**する
  (key 削除 → violation/indeterminate を要求する形へ書き換え。node 名は保つ)
- never-issued record の validation_head 自己申告の残余 (producer 信頼 + WAL 改竄は D68 (6) 境界外) は
  D78 に明文化

## G-4. campaign-start 境界の再解決 (FR6 — MAJOR 採用)

run_block は campaign-start 書込み直前に receipt を再解決し、state / introduction_commit /
receipt raw sha256 / validation_head の**全一致**を要求する。不一致 = 副作用 (WAL 書込み・実行) 前に
fail-closed 拒否。

## G-5. 例外正規化 (FR8 — MAJOR 採用)

`search_repository` / `_assert_search_pass` を含む gate 内の各検査呼び出しで、MigrationError 以外の
例外 (FreezeError・OSError 等) を当該検査の reason へ正規化して蓄積し、後続検査を継続する。

## G-6. E2E の隔離強化と root 整合 assert (FR5 — MAJOR 採用)

- production: `draft_receipt` / `validate_draft` / `finalize_receipt` の冒頭で
  `Path(root).resolve() == ROOT.resolve()` (t080 の ROOT = s1/s8b module の ROOT と同一) を assert し、
  不一致は fail-closed (`receipt.basis_invalid`)。CLI は実 repo でのみ意味を持つことの機械化
- テスト: stub ゼロ E2E は subprocess (`sys.path` 先頭 = temp repo、cwd = temp repo) で draft →
  finalize → verify → gate を実行し、host module 混入を遮断する。subprocess 内で全 module の
  `__file__` が temp root 配下であることを assert

## G-7. B7 の driver 経路負例 (MAJOR 採用・小)

E2E fixture 派生で never-issued 状態の generator bytes tamper → gate refusal に
`holdout-freeze-verify` の generator 理由 1 件が現れることを pin する node を追加。

## 不変条件 (再掲)

no-touch 12 file 不変 / 既存 node 削除禁止 (G-3 の反転は書換) / docs 編集・commit 禁止 /
期待値へ揮発 payload 焼き込み禁止。


## §12c fix ラウンド 2 報告

実装完了です。G-1..G-7 はすべて実装し、逸脱 0、既存 node 削除 0、docs 編集・commit なしです。

## G-1..G-7

- G-1: 凍結検索式を live scan に exact 束縛。[t080_freeze_migration.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1758)
- G-2: historical R を H_mig blob から決定論再導出してから envelope 化。[t080_freeze_migration.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1121)、[s8b_oracle_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:195)
- G-3: campaign-start の T-080 key 欠落を epoch 非依存で全面拒否。[s8b_oracle_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:220)
- G-4: campaign-start 直前に再解決し、state / introduction commit / receipt raw SHA-256 / validation HEAD を照合。[s8b_oracle_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:139)、[s8b_oracle_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1196)
- G-5: gate 各検査の想定外例外を検査固有 reason に正規化し、後続検査を継続。[t080_freeze_migration.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1806)
- G-6: draft / validate / finalize の root 整合を fail-closed 化。[t080_freeze_migration.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:626)、呼出点は同ファイル 1516 / 1574 / 1603。temp repo を先頭 `sys.path` にした隔離 subprocess E2E は [test_s8b_oracle_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:279)。
- G-7: never-issued の generator tamper が public driver gate の holdout refusal に到達する負例を追加。[test_s8b_oracle_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:2157)

## G-1 の exact field 比較

次を順に比較してから `_assert_search_pass(live_report)` を実行します。

1. `set(frozen_doc["holdouts"])`
   `== set(live_report["holdouts"])`
   `== {"rr80", "rr20"}`
2. `frozen_doc["match_convention"]`
   `== live_report["match_convention"]`
3. rr80 / rr20 の各候補について:
   - `frozen_doc["holdouts"][name]["candidate_id"]`
     `== live_report["holdouts"][name]["candidate_id"]`
   - `frozen_doc["holdouts"][name]["unknownness_check"]["expressions"]`
     `== live_report["holdouts"][name]["expressions"]`
4. その後、live の `conjunction_hits` が空、positive control が正であることを既存 `_assert_search_pass` で検査。

いずれの不一致も `holdout.unknownness_layer2` です。

## node 台帳

- 追加: 6 node
  - G-1、G-5 各 1
  - G-2 1
  - G-4 2
  - G-7 1
- 書換: 8 collected node
  - stub-zero E2E
  - post-R draft 再発行
  - GateDecision AST 台帳
  - run_block 二重解決 2 parameter node
  - pre-R key 欠落/null 2 parameter node
  - post-R key 削除反転
- 削除: 0
- 全受入 node: `2709 → 2715`
- 対象 3 ファイル: `265 → 271 collected`

## 実走結果

- 対象全走:
  - `python3 -m pytest -q test_t080... test_s8b_oracle_driver... test_s8b_oracle_report...`
  - `270 passed, 1 skipped`
- 受入全走:
  - `python3 -m pytest -q orchestrator/tests`
  - `2689 passed, 26 skipped, 0 failed`
  - fix1 親環境の 18 skip に対する追加 8 skip は既知の sandbox 差。追加 6 node の算術は一致。
- 最終の subprocess module-path assert 強化後:
  - G-6 E2E 単独 `1 passed`
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- 6 ファイル `py_compile`: OK
- `git diff --check`: OK

最終赤は 0 です。途中、裸の `pytest` が Python 3.9 を選び `dataclass(kw_only/slots)` の collection error 2 件を出しましたが、正規の `python3 -m pytest`（Python 3.10）で切り分け済みです。submodule 偽赤は発生せず、`external/ccbench` は `d706650` のままです。G-6 E2E は sandbox 内でも実行できたため skip 化していません。

`git diff --name-only 1c1b342` は許可された 6 ファイルのみです。no-touch 12 file は全て不変で、名指しの `s1_known_axes_freeze.py` / `s8b_holdout_freeze.py` も差分 0。開始時から存在した未追跡 handoff は触れていません。docs 編集・commit ともに実施していません。

## §13 変異台帳 (3 巡・親実測)

### §13.1 経過

- 1 巡目 (統合 7b8e843): 12 KILLED + M03 KILLED + M07 ATTRIBUTION_FAIL (OID 等価と touches-path の二重防御にマスク — 単層変異では 2 node が期待外の状態 invalid で赤。erratum として記録し両層再照準) + M13 除外 (gate 内で verify_document が同一 report を再検査する冗長ゲートの等価変異 — F28 不成立の正しい除外)
- 2 巡目 (fix1 1c1b342): spec 再登録 (M02/M05/M06/M07 を受理反転形へ、M07 両層累積、M13 は F-1 の gate 単層化で復活、M11 same-tree empty commit 化) → **14/14 KILLED、unexpected 0・missing 0**
- 最終 (fix2 68661b9): M15 (G-1 凍結検索式束縛の無効化) + M16 (G-3 key-absent 拒否の無効化) を追加 → **16/16 KILLED、unexpected 0・missing 0、rc=0**。全変異とも復元は内容比較で検証済み (F32 対策)、置換は累積適用 + 置換ごと一意性 assert (F33 対策)、flock 単一走行 guard 下で実測

### §13.2 最終 spec (事前登録の正本、wt-mut/t080_mutation_specs.py 逐語)

```python
#!/usr/bin/env python3
"""T-080 migration wave の変異事前登録を実コードへ固定する。

各 ``MutationSpec`` は通常の dict として扱える一方、インスタンスごとの
``__doc__`` に F28 の裏取りを保持する。ハーネスは ``SPECS`` だけを実走し、
``PENDING_NODE`` は必要な反転検証 node がないため実走対象にしない。
"""
from __future__ import annotations

from typing import Iterable


class MutationSpec(dict):
    """必須 field を持ち、F28 文書をインスタンス docstring に保持する mapping。"""

    def __init__(self, *, doc: str, **values: object) -> None:
        super().__init__(values)
        self.__doc__ = doc


_MIGRATION = "orchestrator/campaign/t080_freeze_migration.py"
_HOLDOUT = "orchestrator/campaign/s8b_holdout_freeze.py"
_REPORT = "orchestrator/campaign/s8b_oracle_report.py"
_TEST_MIGRATION = "orchestrator/tests/test_t080_freeze_migration.py"
_TEST_HOLDOUT = "orchestrator/tests/test_s8b_holdout_freeze.py"
_TEST_DRIVER = "orchestrator/tests/test_s8b_oracle_driver.py"
_TEST_REPORT = "orchestrator/tests/test_s8b_oracle_report.py"


def _node(file: str, name: str) -> str:
    return f"{file}::{name}"


M01 = MutationSpec(
    doc="""F28: 先行同一入力検査なし。現物では reconstruction 前段は schema・pairing
    だけで ``reference_values_note`` の深い不一致を拒否しない。deep equality と同じ入力を
    再拒否する hash equality も同時に外す。赤の単一理由は独立 kill node 1 件の
    ``known_axes.reconstruction_equality`` 欠落である。""",
    id="M01",
    kind="behavioral",
    file=_MIGRATION,
    old='''    if projected_view != rebuilt_view:\n        raise MigrationError("known_axes.reconstruction_equality", "projected document と rebuilt document が不一致")\n    projected_sha = _sha256(_canonical_bytes(projected_view))\n    rebuilt_sha = _sha256(_canonical_bytes(rebuilt_view))\n    if projected_sha != rebuilt_sha:\n        raise MigrationError("known_axes.reconstruction_equality", "reconstruction hash が不一致")''',
    new='''    # MUTATION M01: reconstruction equality を無効化。\n    projected_sha = _sha256(_canonical_bytes(projected_view))\n    rebuilt_sha = _sha256(_canonical_bytes(rebuilt_view))''',
    expected_red={_node(
        _TEST_MIGRATION,
        "test_draft_reconstruction_deep_equality_is_independent_m01_kill",
    )},
    expected_reason="reference_values_note だけ異なる rebuilt document が reconstruction equality を通過する",
    targeted_test_files=[_TEST_MIGRATION],
    hang_risk=False,
)


M02 = MutationSpec(
    doc="""F28: 先行同一入力検査なし。full-valid R の削除 commit は HEAD・clean
    worktree を通り、draft を止めるのは現物の state precondition だけである。mutant は
    issued-but-missing を draft 可能へ反転する。赤の単一理由は driver の post-R delete
    fixture 1 node における ``receipt.invalid`` 欠落である。""",
    id="M02",
    kind="behavioral",
    file=_MIGRATION,
    old='''    if state.state != "never-issued":\n        raise MigrationError("receipt.invalid", f"draft は never-issued でのみ許可: {state.state}")''',
    new='''    if state.state not in {"never-issued", "issued-but-missing"}:\n        raise MigrationError("receipt.invalid", f"draft は never-issued でのみ許可: {state.state}")''',
    expected_red={_node(
        _TEST_DRIVER,
        "test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28",
    )},
    expected_reason="post-R delete 後の issued-but-missing repository で draft basis capture が誤成功する",
    targeted_test_files=[_TEST_DRIVER],
    hang_risk=False,
)


M03 = MutationSpec(
    doc="""F28: 先行同一入力検査なし。fixture bytes と root hash は不変で、
    ``_scan_one`` まで ratio を再検査しない。赤の単一理由は7 nodeすべてで「固定 rr50
    positive-control に rr51 predicate が一致せず hit_count が0」であり、別理由ではない。""",
    id="M03",
    kind="behavioral",
    file=_HOLDOUT,
    old='''    positive_expressions = _expressions(\n        _POSITIVE_RATIO, _FIXED_SKEW, _FIXED_RMW,\n    )''',
    new='''    positive_expressions = _expressions(\n        "5" + "1", _FIXED_SKEW, _FIXED_RMW,\n    )''',
    expected_red={
        _node(_TEST_HOLDOUT, "test_t080_positive_control_kills_predicate_only_rr51_mutant"),
        _node(_TEST_HOLDOUT, "test_verify_rejects_source_hash_and_binding_tamper"),
        _node(_TEST_HOLDOUT, "test_verify_tolerates_per_axis_drift_and_rejects_snapshot_tamper"),
        _node(_TEST_HOLDOUT, "test_exact_exemption_matching_bytes_is_not_scanned_but_is_enumerated"),
        _node(_TEST_HOLDOUT, "test_exact_exemption_unknown_non_hit_file_is_still_scanned"),
        _node(_TEST_HOLDOUT, "test_verify_rejects_active_generation_worktree_drift"),
        _node(_TEST_HOLDOUT, "test_verify_rejects_unratified_generation_documents"),
    },
    expected_reason="固定 rr50 positive-control bytes に rr51 predicate が一致せず hit_count が 0 になる",
    targeted_test_files=[_TEST_HOLDOUT],
    hang_risk=False,
)


M04 = MutationSpec(
    doc="""F28: 先行同一入力検査なし。strict JSON parse 後に semantic 同値な pretty
    bytes を拒否するのは canonical bytes equality だけである。赤の単一理由は canonical
    専用 node 1 件の ``receipt.canonical_mismatch`` 欠落である。""",
    id="M04",
    kind="behavioral",
    file=_MIGRATION,
    old='''    if _canonical_bytes(doc) != raw:\n        raise MigrationError("receipt.canonical_mismatch", f"{what} が canonical bytes でない")''',
    new='''    if len(raw) < 0:\n        raise MigrationError("receipt.canonical_mismatch", f"{what} が canonical bytes でない")''',
    expected_red={_node(
        _TEST_MIGRATION,
        "test_canonical_rejects_pretty_trailing_newline_and_accepts_exact_bytes",
    )},
    expected_reason="semantic 同値な pretty/trailing-LF receipt bytes が canonical 検査を通過する",
    targeted_test_files=[_TEST_MIGRATION],
    hang_risk=False,
)


M05 = MutationSpec(
    doc="""F28: 先行同一入力検査なし。driver の full-valid fixture は R の parent と
    single-file diff が正しく、trailer だけが ``AI-Agent: codex`` である。mutant では
    active-valid へ反転し、赤の単一理由は parameter node 1 件の
    ``receipt.user_commit_trailer`` 欠落である。""",
    id="M05",
    kind="behavioral",
    file=_MIGRATION,
    old='''    if not _is_none_commit(commit, root):\n        raise MigrationError("receipt.user_commit_trailer", "R に AI-Agent: none が逐語でない")''',
    new='''    if False and not _is_none_commit(commit, root):\n        raise MigrationError("receipt.user_commit_trailer", "R に AI-Agent: none が逐語でない")''',
    expected_red={_node(
        _TEST_DRIVER,
        "test_t080_full_valid_history_defects_have_one_baseline_reason_f28"
        "[bad-trailer-receipt.user_commit_trailer]",
    )},
    expected_reason="AI-Agent: codex の R が user-commit trailer 検査を通過する",
    targeted_test_files=[_TEST_DRIVER],
    hang_risk=False,
)


M06 = MutationSpec(
    doc="""F28: 先行同一入力検査なし。driver の full-valid fixture は R の parent と
    trailer が正しく、receipt と extra file の同時追加だけが差である。mutant では
    active-valid へ反転し、赤の単一理由は parameter node 1 件の
    ``receipt.introduction_diff`` 欠落である。""",
    id="M06",
    kind="behavioral",
    file=_MIGRATION,
    old='''    if out.splitlines() != [f"A\\t{RECEIPT_REL}"]:\n        raise MigrationError("receipt.introduction_diff", "R が receipt 1 file の A だけでない")''',
    new='''    if False and out.splitlines() != [f"A\\t{RECEIPT_REL}"]:\n        raise MigrationError("receipt.introduction_diff", "R が receipt 1 file の A だけでない")''',
    expected_red={_node(
        _TEST_DRIVER,
        "test_t080_full_valid_history_defects_have_one_baseline_reason_f28"
        "[extra-r-path-receipt.introduction_diff]",
    )},
    expected_reason="receipt と extra.txt を同時追加した R が introduction diff 検査を通過する",
    targeted_test_files=[_TEST_DRIVER],
    hang_risk=False,
)


M07 = MutationSpec(
    doc="""F28: 先行同一入力検査なし。introduction 一意性後の現物三層検査のうち、
    modify→revert を拒否する descendant OID 層と path-touch 層を累積して外す。mode/tree層と
    最終 HEAD/worktree は通る。mutant では active-valid へ反転し、赤の単一理由は parameter
    node 1 件の ``receipt.history_mutated`` 欠落である。""",
    id="M07",
    kind="behavioral",
    file=_MIGRATION,
    old=(
        '''    if any(oids.get(commit) != expected_oid for commit in descendants):\n        _append_refusal(refusals, RECEIPT_PREFIX, "receipt.history_mutated")\n        issued_but_missing = True''',
        '''    if any(\n        commit != introduction and _history_touches_path(commit, RECEIPT_REL, root)\n        for commit in descendants\n    ):\n        _append_refusal(refusals, RECEIPT_PREFIX, "receipt.history_mutated")\n        issued_but_missing = True''',
    ),
    new=(
        '''    if False and any(oids.get(commit) != expected_oid for commit in descendants):\n        _append_refusal(refusals, RECEIPT_PREFIX, "receipt.history_mutated")\n        issued_but_missing = True''',
        '''    if False and any(\n        commit != introduction and _history_touches_path(commit, RECEIPT_REL, root)\n        for commit in descendants\n    ):\n        _append_refusal(refusals, RECEIPT_PREFIX, "receipt.history_mutated")\n        issued_but_missing = True''',
    ),
    expected_red={_node(
        _TEST_DRIVER,
        "test_t080_full_valid_history_defects_have_one_baseline_reason_f28"
        "[modify-revert-receipt.history_mutated]",
    )},
    expected_reason="R 後に別 bytes を commit して元 bytes へ戻した履歴が immutable と誤判定される",
    targeted_test_files=[_TEST_DRIVER],
    hang_risk=False,
)


M08 = MutationSpec(
    doc="""F28: 先行同一入力検査なし。artifact は nofollow read 後、semantic parse 前に
    raw root を比較し、``{ }`` は strict parse 可能なので後段でも同じ差を拒否しない。
    赤の単一理由は raw-bytes node 1 件の artifact hash 不一致欠落である。""",
    id="M08",
    kind="behavioral",
    file=_MIGRATION,
    old='''    if _sha256(raw) != expected_sha256:\n        raise MigrationError(reason, f"{what} artifact raw bytes 不一致")''',
    new='''    if len(raw) < 0:\n        raise MigrationError(reason, f"{what} artifact raw bytes 不一致")''',
    expected_red={_node(
        _TEST_MIGRATION,
        "test_artifact_raw_bytes_are_checked_before_semantic_parse_m08",
    )},
    expected_reason="semantic 同値だが空白 1 byte の異なる artifact が raw root 検査を通過する",
    targeted_test_files=[_TEST_MIGRATION],
    hang_risk=False,
)


M09 = MutationSpec(
    doc="""F28: 先行同一入力検査なし。object existence を通る blob OID で、commit type
    を別に拒否する前段はない。mutant は noncommit を missing に緩め、赤の単一理由は ancestry
    分類 node 1 件の ``ancestry_object_type`` 欠落である。""",
    id="M09",
    kind="behavioral",
    file=_MIGRATION,
    old='''    if kind is None:\n        return AncestryResult("missing-commit", recorded, None)\n    if kind != "commit":\n        return AncestryResult("object-type-error", recorded, kind, f"{prefix}.ancestry_object_type")''',
    new='''    if kind is None or kind != "commit":\n        return AncestryResult("missing-commit", recorded, None)''',
    expected_red={_node(
        _TEST_MIGRATION,
        "test_ancestry_missing_nonancestor_ancestor_noncommit_and_git_error",
    )},
    expected_reason="実在する blob OID が object-type-error でなく missing-commit と誤分類される",
    targeted_test_files=[_TEST_MIGRATION],
    hang_risk=False,
)


M10 = MutationSpec(
    doc="""F28: 先行同一入力検査なし。cat-file の commit 型検査後に merge-base rc=128
    となる fixture で、rc を再分類する前段はない。mutant は rc>1 を not-ancestor に緩め、
    赤の単一理由は ancestry node 1 件の ``ancestry_git_error`` 欠落である。""",
    id="M10",
    kind="behavioral",
    file=_MIGRATION,
    old='''    if completed.returncode == 1:\n        return AncestryResult("not-ancestor", recorded, validation_head)''',
    new='''    if completed.returncode != 0:\n        return AncestryResult("not-ancestor", recorded, validation_head)''',
    expected_red={_node(
        _TEST_MIGRATION,
        "test_ancestry_missing_nonancestor_ancestor_noncommit_and_git_error",
    )},
    expected_reason="merge-base rc>1 が Git error でなく not-ancestor と誤分類される",
    targeted_test_files=[_TEST_MIGRATION],
    hang_risk=False,
)


M11 = MutationSpec(
    doc="""F28: 先行同一入力検査なし。driver の full-valid fixture は current submodule の
    hardened HEAD capture を通り、同じ tree の empty commit への移動だけが差である。H_mig
    gitlink は正しく後段 basis 検査を通る。mutant では active-valid へ反転し、赤の単一理由は
    parameter node 1 件の ``known_axes.ccbench_current`` 欠落である。""",
    id="M11",
    kind="behavioral",
    file=_MIGRATION,
    old='''def _verify_ccbench_current(known: Mapping[str, object], root: Path) -> None:\n    pin = str(known.get("ccbench_pin"))\n    if _current_ccbench_head(root) != pin:\n        raise MigrationError("known_axes.ccbench_current", "current ccbench HEAD が legacy pin と不一致")''',
    new='''def _verify_ccbench_current(known: Mapping[str, object], root: Path) -> None:\n    pin = str(known.get("ccbench_pin"))\n    if False and _current_ccbench_head(root) != pin:\n        raise MigrationError("known_axes.ccbench_current", "current ccbench HEAD が legacy pin と不一致")''',
    expected_red={_node(
        _TEST_DRIVER,
        "test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5"
        "[ccbench-current-known_axes.ccbench_current]",
    )},
    expected_reason="current ccbench が同 tree の別 commit へ進んでも current-pin 検査を通過する",
    targeted_test_files=[_TEST_DRIVER],
    hang_risk=False,
)


M12 = MutationSpec(
    doc="""F28: 先行同一入力検査なし。H_mig の tree entry は一意に読め、mode/kind は
    正しく gitlink OID だけが不一致である。mutant は OID 比較だけを外し、赤の単一理由は
    M11/M12 独立性 node 1 件の ``known_axes.ccbench_gitlink`` 欠落である。""",
    id="M12",
    kind="behavioral",
    file=_MIGRATION,
    old='''    if (mode, kind, oid) != ("160000", "commit", expected_pin):\n        raise MigrationError("known_axes.ccbench_gitlink", "H_mig ccbench gitlink が legacy pin と不一致")''',
    new='''    if mode != "160000" or kind != "commit":\n        raise MigrationError("known_axes.ccbench_gitlink", "H_mig ccbench gitlink が legacy pin と不一致")''',
    expected_red={_node(
        _TEST_MIGRATION,
        "test_ccbench_current_and_basis_gitlink_have_independent_reasons_m11_m12",
    )},
    expected_reason="H_mig の ccbench gitlink OID 不一致が mode/kind 検査だけを通過する",
    targeted_test_files=[_TEST_MIGRATION],
    hang_risk=False,
)


M13 = MutationSpec(
    doc="""F28: 先行同一入力検査なし。driver の full-valid R と untracked rr80 三軸
    conjunction は artifact/schema/binding を通り、gate側 layer-2 scan の単層 assert だけが
    拒否する。mutant では active-valid へ反転し、赤の単一理由は parameter node 1 件の
    ``holdout.unknownness_layer2`` 欠落である。""",
    id="M13",
    kind="behavioral",
    file=_MIGRATION,
    old='''        holdout_module._assert_search_pass(report)''',
    new='''        if False and holdout_module._assert_search_pass(report):\n            pass''',
    expected_red={_node(
        _TEST_DRIVER,
        "test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5"
        "[unknownness-layer2-holdout.unknownness_layer2]",
    )},
    expected_reason="untracked rr80 三軸 conjunction が gate layer-2 scan を通り active-valid になる",
    targeted_test_files=[_TEST_DRIVER],
    hang_risk=False,
)


M14 = MutationSpec(
    doc="""F28: 先行同一入力検査なし。F-5 後の現物 grammar では bare null の専用分岐が
    canonical envelope parse より前の唯一の受理拒否点である。mutant は bare null を historical
    absent と誤分類して受理へ反転する。赤の単一理由は null 専用2 node とも
    ``bare null は現行 grammar で禁止`` の欠落である。""",
    id="M14",
    kind="behavioral",
    file=_REPORT,
    old='''    if value is None:\n        return _T080CampaignObservation(\n            "malformed", issue=_t080_reason("bare null は現行 grammar で禁止"),\n        )''',
    new='''    if value is None:\n        return _T080CampaignObservation("absent")''',
    expected_red={
        _node(
            _TEST_REPORT,
            "test_post_r_null_is_protocol_violation_for_every_campaign_row",
        ),
        _node(
            _TEST_REPORT,
            "test_pre_r_null_and_object_mixture_is_protocol_violation",
        ),
    },
    expected_reason="bare null が現行 grammar 違反でなく historical absent と誤分類される",
    targeted_test_files=[_TEST_REPORT],
    hang_risk=False,
)


M15 = MutationSpec(
    doc="""F28: 先行同一入力検査なし。凍結 holdout document の raw-byte pin は document
    側だけを固定し、live report 側の expressions・match_convention・candidate drift は拒否
    できない。後段 ``_assert_search_pass`` は hit/pass 条件だけを見る。赤の単一理由は G-1
    専用 node 1 件で frozen/live 束縛拒否が消えることである。""",
    id="M15",
    kind="behavioral",
    file=_MIGRATION,
    old='''        frozen_holdouts = holdout_doc.get("holdouts")\n        live_holdouts = report.get("holdouts") if isinstance(report, Mapping) else None\n        candidate_names = {"rr80", "rr20"}\n        if (not isinstance(frozen_holdouts, Mapping)\n                or not isinstance(live_holdouts, Mapping)\n                or set(frozen_holdouts) != candidate_names\n                or set(live_holdouts) != candidate_names):\n            raise MigrationError(\n                "holdout.unknownness_layer2", "rr80/rr20 candidate 集合が不一致",\n            )\n        if report.get("match_convention") != holdout_doc.get("match_convention"):\n            raise MigrationError(\n                "holdout.unknownness_layer2", "match_convention が凍結記録値と不一致",\n            )\n        for name in ("rr80", "rr20"):\n            frozen = frozen_holdouts[name]\n            live = live_holdouts[name]\n            unknownness = frozen.get("unknownness_check") if isinstance(frozen, Mapping) else None\n            if (not isinstance(live, Mapping) or not isinstance(unknownness, Mapping)\n                    or live.get("candidate_id") != frozen.get("candidate_id")):\n                raise MigrationError(\n                    "holdout.unknownness_layer2", f"{name} candidate 対応が不一致",\n                )\n            if live.get("expressions") != unknownness.get("expressions"):\n                raise MigrationError(\n                    "holdout.unknownness_layer2", f"{name} expressions が凍結記録値と不一致",\n                )''',
    new='''        # MUTATION M15: frozen document と live report の束縛を無効化。''',
    expected_red={_node(
        _TEST_MIGRATION,
        "test_live_scan_is_bound_to_frozen_expressions_match_convention_and_candidates_g1",
    )},
    expected_reason="live report の expressions/match_convention/candidate drift が凍結記録値との照合を通過する",
    targeted_test_files=[_TEST_MIGRATION],
    hang_risk=False,
)


M16 = MutationSpec(
    doc="""F28: 先行同一入力検査なし。campaign-start の T-080 key 欠落を epoch 非依存で
    拒否するのはこの分岐だけで、後段は ``absent`` を歴史 grammar として許容する。赤の単一理由は
    G-3 で反転された各 node とも key 欠落が protocol violation にならないことだけである。""",
    id="M16",
    kind="behavioral",
    file=_REPORT,
    old='''    if _T080_KEY not in start:\n        return _T080CampaignObservation(\n            "malformed", issue=_t080_reason("campaign-start に T-080 key がない"),\n        )''',
    new='''    if _T080_KEY not in start:\n        return _T080CampaignObservation("absent")''',
    expected_red={
        _node(
            _TEST_REPORT,
            "test_pre_r_campaign_start_absent_or_null_is_allowed[historical-absent]",
        ),
        _node(
            _TEST_REPORT,
            "test_post_r_missing_key_is_single_reason_and_makes_judge_indeterminate",
        ),
    },
    expected_reason="T-080 key 欠落 campaign が protocol violation でなく historical absent と誤分類される",
    targeted_test_files=[_TEST_REPORT],
    hang_risk=False,
)


SPECS = (
    M01, M02, M03, M04, M05, M06, M07,
    M08, M09, M10, M11, M12, M13, M14,
    M15, M16,
)

# 全 16 spec の反転 fixture は現物に存在する。
PENDING_NODE: dict[str, str] = {}


REQUIRED_FIELDS = frozenset({
    "id", "file", "old", "new", "expected_red", "expected_reason",
    "targeted_test_files", "hang_risk", "kind",
})


def validate_specs(specs: Iterable[MutationSpec] = SPECS) -> None:
    """import 時に軽量な schema 整合だけを確認する（file 内容はハーネスが確認）。"""
    seen = set()
    for spec in specs:
        missing = REQUIRED_FIELDS - set(spec)
        if missing:
            raise AssertionError(f"{spec.get('id', '<unknown>')}: field 欠落 {sorted(missing)}")
        if spec["id"] in seen:
            raise AssertionError(f"duplicate mutation id: {spec['id']}")
        seen.add(spec["id"])
        if spec["kind"] not in {"behavioral", "diagnostic-pin"}:
            raise AssertionError(f"{spec['id']}: unknown kind {spec['kind']}")
        if not spec.__doc__ or "F28" not in spec.__doc__:
            raise AssertionError(f"{spec['id']}: F28 docstring 欠落")
        for evidence in ("先行同一入力検査なし", "赤の単一理由"):
            if evidence not in spec.__doc__:
                raise AssertionError(f"{spec['id']}: F28 {evidence} の記録欠落")


validate_specs()

```

### §13.3 最終結果 JSON (逐語)

```json
{
  "generated_at_utc": "2026-07-22T11:13:00.419548+00:00",
  "pending_node": {},
  "results": [
    {
      "actual_red": [
        "orchestrator/tests/test_t080_freeze_migration.py::test_draft_reconstruction_deep_equality_is_independent_m01_kill"
      ],
      "command": [
        "python3",
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "orchestrator/tests/test_t080_freeze_migration.py"
      ],
      "elapsed_seconds": 1.384,
      "expected_reason": "reference_values_note だけ異なる rebuilt document が reconstruction equality を通過する",
      "expected_red": [
        "orchestrator/tests/test_t080_freeze_migration.py::test_draft_reconstruction_deep_equality_is_independent_m01_kill"
      ],
      "file": "orchestrator/campaign/t080_freeze_migration.py",
      "id": "M01",
      "kind": "behavioral",
      "missing_expected_red": [],
      "output": "........F.............................                                   [100%]\n=================================== FAILURES ===================================\n_______ test_draft_reconstruction_deep_equality_is_independent_m01_kill ________\n\n    def test_draft_reconstruction_deep_equality_is_independent_m01_kill():\n        legacy = {\n            \"frozen_at_head\": \"a\" * 40, \"ccbench_pin\": \"b\" * 40,\n            \"python_version\": \"3.11\", \"generator\": {\"path\": \"g.py\", \"sha256\": \"c\" * 64},\n            \"reference_values_note\": \"legacy\",\n        }\n    \n        def builder(**_kwargs):\n            rebuilt = copy.deepcopy(legacy)\n            rebuilt[\"reference_values_note\"] = \"mutated\"\n            return rebuilt\n    \n>       _expect_reason(\n            lambda: migration._draft_reconstruct_known_axes(\n                legacy, (), builder=builder, pairing=lambda _doc: None,\n            ),\n            \"known_axes.reconstruction_equality\",\n        )\n\norchestrator/tests/test_t080_freeze_migration.py:299: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\ncall = <function test_draft_reconstruction_deep_equality_is_independent_m01_kill.<locals>.<lambda> at 0x7fce62145090>\nreason = 'known_axes.reconstruction_equality'\n\n    def _expect_reason(call, reason: str) -> migration.MigrationError:\n        try:\n            call()\n        except migration.MigrationError as exc:\n            assert exc.reason == reason, (exc.reason, reason, exc)\n            return exc\n>       raise AssertionError(f\"{reason} の拒否が発生しなかった\")\nE       AssertionError: known_axes.reconstruction_equality の拒否が発生しなかった\n\norchestrator/tests/test_t080_freeze_migration.py:129: AssertionError\n=========================== short test summary info ============================\nFAILED orchestrator/tests/test_t080_freeze_migration.py::test_draft_reconstruction_deep_equality_is_independent_m01_kill - AssertionError: known_axes.reconstruction_equality の拒否が発生しなかった\n1 failed, 37 passed in 1.17s\n",
      "pytest_returncode": 1,
      "status": "KILLED",
      "timeout_seconds": null,
      "unexpected_red": []
    },
    {
      "actual_red": [
        "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28"
      ],
      "command": [
        "python3",
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "orchestrator/tests/test_s8b_oracle_driver.py"
      ],
      "elapsed_seconds": 188.22,
      "expected_reason": "post-R delete 後の issued-but-missing repository で draft basis capture が誤成功する",
      "expected_red": [
        "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28"
      ],
      "file": "orchestrator/campaign/t080_freeze_migration.py",
      "id": "M02",
      "kind": "behavioral",
      "missing_expected_red": [],
      "output": ".........F.............................................................. [ 88%]\ns........                                                                [100%]\n=================================== FAILURES ===================================\n__ test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 __\n\ntmp_path = PosixPath('/dev/shm/pytest-of-tanab/pytest-1507/test_t080_full_valid_post_r_de0')\n\n    def test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28(tmp_path):\n        root, receipt_path, _document = _t080_stub_free_e2e_repo(tmp_path)\n        receipt_path.unlink()\n        _run_git(root, \"add\", \"-u\", migration.RECEIPT_REL)\n        _run_git(root, \"commit\", \"-q\", \"-m\", \"delete receipt\", \"-m\", \"AI-Agent: none\")\n        basis = _run_git(root, \"rev-parse\", \"HEAD\")\n        child = textwrap.dedent(\"\"\"\n            import json\n            import sys\n            from pathlib import Path\n            root = Path(sys.argv[1]).resolve()\n            sys.path[0] = str(root)\n            from orchestrator.campaign import t080_freeze_migration as migration\n            try:\n                migration.draft_receipt(\n                    basis=sys.argv[2], out=migration.DRAFT_REL, root=root,\n                )\n            except migration.MigrationError as exc:\n                print(json.dumps({\"reason\": exc.reason, \"detail\": exc.detail}))\n            else:\n                raise AssertionError(\"post-R 再発行が拒否されなかった\")\n        \"\"\")\n>       completed = subprocess.run(\n            [sys.executable, \"-I\", \"-B\", \"-c\", child, str(root), basis],\n            cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,\n            text=True, env={**os.environ, \"PYTHONPATH\": \"\", \"PYTHONNOUSERSITE\": \"1\"},\n        )\n\norchestrator/tests/test_s8b_oracle_driver.py:651: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\ninput = None, capture_output = False, timeout = None, check = True\npopenargs = (['/usr/bin/python3', '-I', '-B', '-c', '\\nimport json\\nimport sys\\nfrom pathlib import Path\\nroot = Path(sys.argv[1])...-R 再発行が拒否されなかった\")\\n', '/dev/shm/pytest-of-tanab/pytest-1507/test_t080_full_valid_post_r_de0/t080-stub-free-e2e', ...],)\nkwargs = {'cwd': PosixPath('/dev/shm/pytest-of-tanab/pytest-1507/test_t080_full_valid_post_r_de0/t080-stub-free-e2e'), 'stdout': -1, 'stderr': -1, 'text': True, ...}\n\n    def run(*popenargs,\n            input=None, capture_output=False, timeout=None, check=False, **kwargs):\n        \"\"\"Run command with arguments and return a CompletedProcess instance.\n    \n        The returned instance will have attributes args, returncode, stdout and\n        stderr. By default, stdout and stderr are not captured, and those attributes\n        will be None. Pass stdout=PIPE and/or stderr=PIPE in order to capture them,\n        or pass capture_output=True to capture both.\n    \n        If check is True and the exit code was non-zero, it raises a\n        CalledProcessError. The CalledProcessError object will have the return code\n        in the returncode attribute, and output & stderr attributes if those streams\n        were captured.\n    \n        If timeout is given, and the process takes too long, a TimeoutExpired\n        exception will be raised.\n    \n        There is an optional argument \"input\", allowing you to\n        pass bytes or a string to the subprocess's stdin.  If you use this argument\n        you may not also use the Popen constructor's \"stdin\" argument, as\n        it will be used internally.\n    \n        By default, all communication is in bytes, and therefore any \"input\" should\n        be bytes, and the stdout and stderr will be bytes. If in text mode, any\n        \"input\" should be a string, and stdout and stderr will be strings decoded\n        according to locale encoding, or by \"encoding\" if set. Text mode is\n        triggered by setting any of text, encoding, errors or universal_newlines.\n    \n        The other arguments are the same as for the Popen constructor.\n        \"\"\"\n        if input is not None:\n            if kwargs.get('stdin') is not None:\n                raise ValueError('stdin and input arguments may not both be used.')\n            kwargs['stdin'] = PIPE\n    \n        if capture_output:\n            if kwargs.get('stdout') is not None or kwargs.get('stderr') is not None:\n                raise ValueError('stdout and stderr arguments may not be used '\n                                 'with capture_output.')\n            kwargs['stdout'] = PIPE\n            kwargs['stderr'] = PIPE\n    \n        with Popen(*popenargs, **kwargs) as process:\n            try:\n                stdout, stderr = process.communicate(input, timeout=timeout)\n            except TimeoutExpired as exc:\n                process.kill()\n                if _mswindows:\n                    # Windows accumulates the output in a single blocking\n                    # read() call run on child threads, with the timeout\n                    # being done in a join() on those threads.  communicate()\n                    # _after_ kill() is required to collect that and add it\n                    # to the exception.\n                    exc.stdout, exc.stderr = process.communicate()\n                else:\n                    # POSIX _communicate already populated the output so\n                    # far into the TimeoutExpired exception.\n                    process.wait()\n                raise\n            except:  # Including KeyboardInterrupt, communicate handled that.\n                process.kill()\n                # We don't call process.wait() as .__exit__ does that for us.\n                raise\n            retcode = process.poll()\n            if check and retcode:\n>               raise CalledProcessError(retcode, process.args,\n                                         output=stdout, stderr=stderr)\nE               subprocess.CalledProcessError: Command '['/usr/bin/python3', '-I', '-B', '-c', '\\nimport json\\nimport sys\\nfrom pathlib import Path\\nroot = Path(sys.argv[1]).resolve()\\nsys.path[0] = str(root)\\nfrom orchestrator.campaign import t080_freeze_migration as migration\\ntry:\\n    migration.draft_receipt(\\n        basis=sys.argv[2], out=migration.DRAFT_REL, root=root,\\n    )\\nexcept migration.MigrationError as exc:\\n    print(json.dumps({\"reason\": exc.reason, \"detail\": exc.detail}))\\nelse:\\n    raise AssertionError(\"post-R 再発行が拒否されなかった\")\\n', '/dev/shm/pytest-of-tanab/pytest-1507/test_t080_full_valid_post_r_de0/t080-stub-free-e2e', '71b2cadd116fdef44d15a8bc75bc626b62e4fdf6']' returned non-zero exit status 1.\n\n/usr/lib/python3.10/subprocess.py:526: CalledProcessError\n=========================== short test summary info ============================\nFAILED orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 - subprocess.CalledProcessError: Command '['/usr/bin/python3', '-I', '-B', '-...\n1 failed, 79 passed, 1 skipped in 187.99s (0:03:07)\n",
      "pytest_returncode": 1,
      "status": "KILLED",
      "timeout_seconds": null,
      "unexpected_red": []
    },
    {
      "actual_red": [
        "orchestrator/tests/test_s8b_holdout_freeze.py::test_exact_exemption_matching_bytes_is_not_scanned_but_is_enumerated",
        "orchestrator/tests/test_s8b_holdout_freeze.py::test_exact_exemption_unknown_non_hit_file_is_still_scanned",
        "orchestrator/tests/test_s8b_holdout_freeze.py::test_t080_positive_control_kills_predicate_only_rr51_mutant",
        "orchestrator/tests/test_s8b_holdout_freeze.py::test_verify_rejects_active_generation_worktree_drift",
        "orchestrator/tests/test_s8b_holdout_freeze.py::test_verify_rejects_source_hash_and_binding_tamper",
        "orchestrator/tests/test_s8b_holdout_freeze.py::test_verify_rejects_unratified_generation_documents",
        "orchestrator/tests/test_s8b_holdout_freeze.py::test_verify_tolerates_per_axis_drift_and_rejects_snapshot_tamper"
      ],
      "command": [
        "python3",
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "orchestrator/tests/test_s8b_holdout_freeze.py"
      ],
      "elapsed_seconds": 0.596,
      "expected_reason": "固定 rr50 positive-control bytes に rr51 predicate が一致せず hit_count が 0 になる",
      "expected_red": [
        "orchestrator/tests/test_s8b_holdout_freeze.py::test_exact_exemption_matching_bytes_is_not_scanned_but_is_enumerated",
        "orchestrator/tests/test_s8b_holdout_freeze.py::test_exact_exemption_unknown_non_hit_file_is_still_scanned",
        "orchestrator/tests/test_s8b_holdout_freeze.py::test_t080_positive_control_kills_predicate_only_rr51_mutant",
        "orchestrator/tests/test_s8b_holdout_freeze.py::test_verify_rejects_active_generation_worktree_drift",
        "orchestrator/tests/test_s8b_holdout_freeze.py::test_verify_rejects_source_hash_and_binding_tamper",
        "orchestrator/tests/test_s8b_holdout_freeze.py::test_verify_rejects_unratified_generation_documents",
        "orchestrator/tests/test_s8b_holdout_freeze.py::test_verify_tolerates_per_axis_drift_and_rejects_snapshot_tamper"
      ],
      "file": "orchestrator/campaign/s8b_holdout_freeze.py",
      "id": "M03",
      "kind": "behavioral",
      "missing_expected_red": [],
      "output": "..F.......FFF.F....FF.                                                   [100%]\n=================================== FAILURES ===================================\n_________ test_t080_positive_control_kills_predicate_only_rr51_mutant __________\n\nmonkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7fcf8f298550>\n\n    def test_t080_positive_control_kills_predicate_only_rr51_mutant(monkeypatch):\n        baseline = _positive_fixture_report()[\"positive_control\"]\n>       assert baseline[\"hit_count\"] == 1\nE       assert 0 == 1\n\norchestrator/tests/test_s8b_holdout_freeze.py:78: AssertionError\n______________ test_verify_rejects_source_hash_and_binding_tamper ______________\n\ntmp_path = PosixPath('/dev/shm/pytest-of-tanab/pytest-1508/test_verify_rejects_source_has0')\n\n    def test_verify_rejects_source_hash_and_binding_tamper(tmp_path):\n        root, files, head = _synthetic_freeze_root(tmp_path)\n        freeze = tmp_path / \"freeze.json\"\n>       doc = M.generate(\n            confirmed_by=\"reviewer\", confirmed_at=\"date\", output_path=freeze,\n            root=root, files=files, frozen_at_head=head,\n        )\n\norchestrator/tests/test_s8b_holdout_freeze.py:252: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \norchestrator/campaign/s8b_holdout_freeze.py:585: in generate\n    doc = build_document(\norchestrator/campaign/s8b_holdout_freeze.py:522: in build_document\n    _assert_search_pass(report)\n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\nreport = {'match_convention': 'file-level conjunction: 同一ファイルが rratio/skew/rmw の三軸正規表現すべてに一致した場合だけ 1 hit と数える', 'search': {'fil...b_rmw\": \"0\"|\"ycsb_rmw\":\"0\")'}, 'per_axis_counts': {'rratio': 0, 'skew': 1, 'rmw': 1}, 'hit_count': 0, 'hit_paths': []}}\n\n    def _assert_search_pass(report: Mapping) -> None:\n        errors = []\n        holdouts = report.get(\"holdouts\")\n        if not isinstance(holdouts, Mapping):\n            raise FreezeError(\"search report に holdouts がない\")\n        for name in HOLDOUTS:\n            result = holdouts.get(name)\n            if not isinstance(result, Mapping):\n                errors.append(f\"{name}: 検索結果がない\")\n                continue\n            hits = result.get(\"conjunction_hits\")\n            if not isinstance(hits, list):\n                errors.append(f\"{name}: conjunction_hits が list でない\")\n            elif hits:\n                errors.append(f\"{name}: holdout hit {len(hits)} 件: {hits}\")\n        positive = report.get(\"positive_control\")\n        hit_count = positive.get(\"hit_count\") if isinstance(positive, Mapping) else None\n        if not isinstance(hit_count, int) or isinstance(hit_count, bool) or hit_count <= 0:\n            errors.append(\"rr50 陽性対照が 0 件: 検索式の偽保証を排除できない\")\n        if errors:\n>           raise FreezeError(\"; \".join(errors))\nE           campaign.s8b_holdout_freeze.FreezeError: rr50 陽性対照が 0 件: 検索式の偽保証を排除できない\n\norchestrator/campaign/s8b_holdout_freeze.py:432: FreezeError\n_______ test_verify_tolerates_per_axis_drift_and_rejects_snapshot_tamper _______\n\ntmp_path = PosixPath('/dev/shm/pytest-of-tanab/pytest-1508/test_verify_tolerates_per_axis0')\n\n    def test_verify_tolerates_per_axis_drift_and_rejects_snapshot_tamper(tmp_path):\n        root, files, head = _synthetic_freeze_root(tmp_path)\n        freeze = tmp_path / \"freeze.json\"\n>       doc = M.generate(\n            confirmed_by=\"reviewer\", confirmed_at=\"date\", output_path=freeze,\n            root=root, files=files, frozen_at_head=head,\n        )\n\norchestrator/tests/test_s8b_holdout_freeze.py:278: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \norchestrator/campaign/s8b_holdout_freeze.py:585: in generate\n    doc = build_document(\norchestrator/campaign/s8b_holdout_freeze.py:522: in build_document\n    _assert_search_pass(report)\n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\nreport = {'match_convention': 'file-level conjunction: 同一ファイルが rratio/skew/rmw の三軸正規表現すべてに一致した場合だけ 1 hit と数える', 'search': {'fil...b_rmw\": \"0\"|\"ycsb_rmw\":\"0\")'}, 'per_axis_counts': {'rratio': 0, 'skew': 1, 'rmw': 1}, 'hit_count': 0, 'hit_paths': []}}\n\n    def _assert_search_pass(report: Mapping) -> None:\n        errors = []\n        holdouts = report.get(\"holdouts\")\n        if not isinstance(holdouts, Mapping):\n            raise FreezeError(\"search report に holdouts がない\")\n        for name in HOLDOUTS:\n            result = holdouts.get(name)\n            if not isinstance(result, Mapping):\n                errors.append(f\"{name}: 検索結果がない\")\n                continue\n            hits = result.get(\"conjunction_hits\")\n            if not isinstance(hits, list):\n                errors.append(f\"{name}: conjunction_hits が list でない\")\n            elif hits:\n                errors.append(f\"{name}: holdout hit {len(hits)} 件: {hits}\")\n        positive = report.get(\"positive_control\")\n        hit_count = positive.get(\"hit_count\") if isinstance(positive, Mapping) else None\n        if not isinstance(hit_count, int) or isinstance(hit_count, bool) or hit_count <= 0:\n            errors.append(\"rr50 陽性対照が 0 件: 検索式の偽保証を排除できない\")\n        if errors:\n>           raise FreezeError(\"; \".join(errors))\nE           campaign.s8b_holdout_freeze.FreezeError: rr50 陽性対照が 0 件: 検索式の偽保証を排除できない\n\norchestrator/campaign/s8b_holdout_freeze.py:432: FreezeError\n_____ test_exact_exemption_matching_bytes_is_not_scanned_but_is_enumerated _____\n\ntmp_path = PosixPath('/dev/shm/pytest-of-tanab/pytest-1508/test_exact_exemption_matching_0')\n\n    def test_exact_exemption_matching_bytes_is_not_scanned_but_is_enumerated(tmp_path):\n        root = _empty_search_repo(tmp_path)\n        rel = \"output/s8b-freeze/active.json\"\n        positive_rel = \"fixtures/positive.txt\"\n        path = root / rel\n        _write(path, _three_axis_text(_axis_value(\"rr80\", \"rratio\")))\n        _write(root / positive_rel, _positive_text())\n    \n        report = M.search_repository(root, exempt_exact={rel: M._sha256(path)})\n    \n        assert M.enumerate_repository_files(root) == (positive_rel, rel)\n        assert report[\"search\"][\"file_count\"] == 2\n        assert report[\"search\"][\"excluded_paths\"] == []\n        assert report[\"holdouts\"][\"rr80\"][\"conjunction_hits\"] == []\n>       M._assert_search_pass(report)\n\norchestrator/tests/test_s8b_holdout_freeze.py:357: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\nreport = {'match_convention': 'file-level conjunction: 同一ファイルが rratio/skew/rmw の三軸正規表現すべてに一致した場合だけ 1 hit と数える', 'search': {'fil...b_rmw\": \"0\"|\"ycsb_rmw\":\"0\")'}, 'per_axis_counts': {'rratio': 0, 'skew': 1, 'rmw': 1}, 'hit_count': 0, 'hit_paths': []}}\n\n    def _assert_search_pass(report: Mapping) -> None:\n        errors = []\n        holdouts = report.get(\"holdouts\")\n        if not isinstance(holdouts, Mapping):\n            raise FreezeError(\"search report に holdouts がない\")\n        for name in HOLDOUTS:\n            result = holdouts.get(name)\n            if not isinstance(result, Mapping):\n                errors.append(f\"{name}: 検索結果がない\")\n                continue\n            hits = result.get(\"conjunction_hits\")\n            if not isinstance(hits, list):\n                errors.append(f\"{name}: conjunction_hits が list でない\")\n            elif hits:\n                errors.append(f\"{name}: holdout hit {len(hits)} 件: {hits}\")\n        positive = report.get(\"positive_control\")\n        hit_count = positive.get(\"hit_count\") if isinstance(positive, Mapping) else None\n        if not isinstance(hit_count, int) or isinstance(hit_count, bool) or hit_count <= 0:\n            errors.append(\"rr50 陽性対照が 0 件: 検索式の偽保証を排除できない\")\n        if errors:\n>           raise FreezeError(\"; \".join(errors))\nE           campaign.s8b_holdout_freeze.FreezeError: rr50 陽性対照が 0 件: 検索式の偽保証を排除できない\n\norchestrator/campaign/s8b_holdout_freeze.py:432: FreezeError\n__________ test_exact_exemption_unknown_non_hit_file_is_still_scanned __________\n\ntmp_path = PosixPath('/dev/shm/pytest-of-tanab/pytest-1508/test_exact_exemption_unknown_n0')\n\n    def test_exact_exemption_unknown_non_hit_file_is_still_scanned(tmp_path):\n        root = _empty_search_repo(tmp_path)\n        rel = \"output/s8b-freeze/unknown.json\"\n        ratio = _axis_value(\"rr80\", \"rratio\")\n        _write(root / rel, M.concrete_axis_encodings(\"rratio\", ratio)[0] + \"\\n\")\n        _write(root / \"fixtures/positive.txt\", _positive_text())\n    \n        report = M.search_repository(root, exempt_exact={})\n    \n        assert report[\"holdouts\"][\"rr80\"][\"per_axis_counts\"] == {\n            \"rratio\": 1, \"skew\": 1, \"rmw\": 1,\n        }\n        assert report[\"holdouts\"][\"rr80\"][\"conjunction_hits\"] == []\n>       M._assert_search_pass(report)\n\norchestrator/tests/test_s8b_holdout_freeze.py:383: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\nreport = {'match_convention': 'file-level conjunction: 同一ファイルが rratio/skew/rmw の三軸正規表現すべてに一致した場合だけ 1 hit と数える', 'search': {'fil...b_rmw\": \"0\"|\"ycsb_rmw\":\"0\")'}, 'per_axis_counts': {'rratio': 0, 'skew': 1, 'rmw': 1}, 'hit_count': 0, 'hit_paths': []}}\n\n    def _assert_search_pass(report: Mapping) -> None:\n        errors = []\n        holdouts = report.get(\"holdouts\")\n        if not isinstance(holdouts, Mapping):\n            raise FreezeError(\"search report に holdouts がない\")\n        for name in HOLDOUTS:\n            result = holdouts.get(name)\n            if not isinstance(result, Mapping):\n                errors.append(f\"{name}: 検索結果がない\")\n                continue\n            hits = result.get(\"conjunction_hits\")\n            if not isinstance(hits, list):\n                errors.append(f\"{name}: conjunction_hits が list でない\")\n            elif hits:\n                errors.append(f\"{name}: holdout hit {len(hits)} 件: {hits}\")\n        positive = report.get(\"positive_control\")\n        hit_count = positive.get(\"hit_count\") if isinstance(positive, Mapping) else None\n        if not isinstance(hit_count, int) or isinstance(hit_count, bool) or hit_count <= 0:\n            errors.append(\"rr50 陽性対照が 0 件: 検索式の偽保証を排除できない\")\n        if errors:\n>           raise FreezeError(\"; \".join(errors))\nE           campaign.s8b_holdout_freeze.FreezeError: rr50 陽性対照が 0 件: 検索式の偽保証を排除できない\n\norchestrator/campaign/s8b_holdout_freeze.py:432: FreezeError\n_____________ test_verify_rejects_active_generation_worktree_drift _____________\n\ntmp_path = PosixPath('/dev/shm/pytest-of-tanab/pytest-1508/test_verify_rejects_active_gen0')\n\n    def test_verify_rejects_active_generation_worktree_drift(tmp_path):\n        # v1 単一 filename freeze は唯一の発効中 (active) 世代。生成後に設計本文を worktree で\n        # 改変すると、frozen_at_head 時点の blob が recorded sha256 と一致していても、verify は\n        # worktree 完全一致を要求して拒否する (active 世代のドリフト検知)。blob 救済は世代別\n        # 不変 filename + 承認束縛を伴う v2 の旧世代専用であり、唯一の active 世代へ適用すると\n        # 設計本文の worktree 改変が骨抜きになる (fail-open) ため、ここでは通してはいけない。\n        root, files, _ = _synthetic_freeze_root(tmp_path)\n        head1 = _commit_all(root)\n        freeze = tmp_path / \"freeze.json\"\n>       doc = M.generate(\n            confirmed_by=\"reviewer\", confirmed_at=\"date\", output_path=freeze,\n            root=root, files=files, frozen_at_head=head1,\n        )\n\norchestrator/tests/test_s8b_holdout_freeze.py:432: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \norchestrator/campaign/s8b_holdout_freeze.py:585: in generate\n    doc = build_document(\norchestrator/campaign/s8b_holdout_freeze.py:522: in build_document\n    _assert_search_pass(report)\n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\nreport = {'match_convention': 'file-level conjunction: 同一ファイルが rratio/skew/rmw の三軸正規表現すべてに一致した場合だけ 1 hit と数える', 'search': {'fil...b_rmw\": \"0\"|\"ycsb_rmw\":\"0\")'}, 'per_axis_counts': {'rratio': 0, 'skew': 1, 'rmw': 1}, 'hit_count': 0, 'hit_paths': []}}\n\n    def _assert_search_pass(report: Mapping) -> None:\n        errors = []\n        holdouts = report.get(\"holdouts\")\n        if not isinstance(holdouts, Mapping):\n            raise FreezeError(\"search report に holdouts がない\")\n        for name in HOLDOUTS:\n            result = holdouts.get(name)\n            if not isinstance(result, Mapping):\n                errors.append(f\"{name}: 検索結果がない\")\n                continue\n            hits = result.get(\"conjunction_hits\")\n            if not isinstance(hits, list):\n                errors.append(f\"{name}: conjunction_hits が list でない\")\n            elif hits:\n                errors.append(f\"{name}: holdout hit {len(hits)} 件: {hits}\")\n        positive = report.get(\"positive_control\")\n        hit_count = positive.get(\"hit_count\") if isinstance(positive, Mapping) else None\n        if not isinstance(hit_count, int) or isinstance(hit_count, bool) or hit_count <= 0:\n            errors.append(\"rr50 陽性対照が 0 件: 検索式の偽保証を排除できない\")\n        if errors:\n>           raise FreezeError(\"; \".join(errors))\nE           campaign.s8b_holdout_freeze.FreezeError: rr50 陽性対照が 0 件: 検索式の偽保証を排除できない\n\norchestrator/campaign/s8b_holdout_freeze.py:432: FreezeError\n_____________ test_verify_rejects_unratified_generation_documents ______________\n\ntmp_path = PosixPath('/dev/shm/pytest-of-tanab/pytest-1508/test_verify_rejects_unratified0')\n\n    def test_verify_rejects_unratified_generation_documents(tmp_path):\n        root, files, head = _synthetic_freeze_root(tmp_path)\n        freeze = tmp_path / \"freeze.json\"\n>       doc = M.generate(\n            confirmed_by=\"reviewer\", confirmed_at=\"date\", output_path=freeze,\n            root=root, files=files, frozen_at_head=head,\n        )\n\norchestrator/tests/test_s8b_holdout_freeze.py:453: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \norchestrator/campaign/s8b_holdout_freeze.py:585: in generate\n    doc = build_document(\norchestrator/campaign/s8b_holdout_freeze.py:522: in build_document\n    _assert_search_pass(report)\n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\nreport = {'match_convention': 'file-level conjunction: 同一ファイルが rratio/skew/rmw の三軸正規表現すべてに一致した場合だけ 1 hit と数える', 'search': {'fil...b_rmw\": \"0\"|\"ycsb_rmw\":\"0\")'}, 'per_axis_counts': {'rratio': 0, 'skew': 1, 'rmw': 1}, 'hit_count': 0, 'hit_paths': []}}\n\n    def _assert_search_pass(report: Mapping) -> None:\n        errors = []\n        holdouts = report.get(\"holdouts\")\n        if not isinstance(holdouts, Mapping):\n            raise FreezeError(\"search report に holdouts がない\")\n        for name in HOLDOUTS:\n            result = holdouts.get(name)\n            if not isinstance(result, Mapping):\n                errors.append(f\"{name}: 検索結果がない\")\n                continue\n            hits = result.get(\"conjunction_hits\")\n            if not isinstance(hits, list):\n                errors.append(f\"{name}: conjunction_hits が list でない\")\n            elif hits:\n                errors.append(f\"{name}: holdout hit {len(hits)} 件: {hits}\")\n        positive = report.get(\"positive_control\")\n        hit_count = positive.get(\"hit_count\") if isinstance(positive, Mapping) else None\n        if not isinstance(hit_count, int) or isinstance(hit_count, bool) or hit_count <= 0:\n            errors.append(\"rr50 陽性対照が 0 件: 検索式の偽保証を排除できない\")\n        if errors:\n>           raise FreezeError(\"; \".join(errors))\nE           campaign.s8b_holdout_freeze.FreezeError: rr50 陽性対照が 0 件: 検索式の偽保証を排除できない\n\norchestrator/campaign/s8b_holdout_freeze.py:432: FreezeError\n=========================== short test summary info ============================\nFAILED orchestrator/tests/test_s8b_holdout_freeze.py::test_t080_positive_control_kills_predicate_only_rr51_mutant - assert 0 == 1\nFAILED orchestrator/tests/test_s8b_holdout_freeze.py::test_verify_rejects_source_hash_and_binding_tamper - campaign.s8b_holdout_freeze.FreezeError: rr50 陽性対照が 0 件: 検索式の偽保...\nFAILED orchestrator/tests/test_s8b_holdout_freeze.py::test_verify_tolerates_per_axis_drift_and_rejects_snapshot_tamper - campaign.s8b_holdout_freeze.FreezeError: rr50 陽性対照が 0 件: 検索式の偽保...\nFAILED orchestrator/tests/test_s8b_holdout_freeze.py::test_exact_exemption_matching_bytes_is_not_scanned_but_is_enumerated - campaign.s8b_holdout_freeze.FreezeError: rr50 陽性対照が 0 件: 検索式の偽保...\nFAILED orchestrator/tests/test_s8b_holdout_freeze.py::test_exact_exemption_unknown_non_hit_file_is_still_scanned - campaign.s8b_holdout_freeze.FreezeError: rr50 陽性対照が 0 件: 検索式の偽保...\nFAILED orchestrator/tests/test_s8b_holdout_freeze.py::test_verify_rejects_active_generation_worktree_drift - campaign.s8b_holdout_freeze.FreezeError: rr50 陽性対照が 0 件: 検索式の偽保...\nFAILED orchestrator/tests/test_s8b_holdout_freeze.py::test_verify_rejects_unratified_generation_documents - campaign.s8b_holdout_freeze.FreezeError: rr50 陽性対照が 0 件: 検索式の偽保...\n7 failed, 15 passed in 0.36s\n",
      "pytest_returncode": 1,
      "status": "KILLED",
      "timeout_seconds": null,
      "unexpected_red": []
    },
    {
      "actual_red": [
        "orchestrator/tests/test_t080_freeze_migration.py::test_canonical_rejects_pretty_trailing_newline_and_accepts_exact_bytes"
      ],
      "command": [
        "python3",
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "orchestrator/tests/test_t080_freeze_migration.py"
      ],
      "elapsed_seconds": 1.456,
      "expected_reason": "semantic 同値な pretty/trailing-LF receipt bytes が canonical 検査を通過する",
      "expected_red": [
        "orchestrator/tests/test_t080_freeze_migration.py::test_canonical_rejects_pretty_trailing_newline_and_accepts_exact_bytes"
      ],
      "file": "orchestrator/campaign/t080_freeze_migration.py",
      "id": "M04",
      "kind": "behavioral",
      "missing_expected_red": [],
      "output": "..F...................................                                   [100%]\n=================================== FAILURES ===================================\n____ test_canonical_rejects_pretty_trailing_newline_and_accepts_exact_bytes ____\n\n    def test_canonical_rejects_pretty_trailing_newline_and_accepts_exact_bytes():\n        doc = _valid_receipt()\n        raw = migration._canonical_bytes(doc)\n        assert migration._load_canonical(raw) == doc\n        for bad in (json.dumps(doc).encode(), raw + b\"\\n\"):\n>           _expect_reason(lambda bad=bad: migration._load_canonical(bad), \"receipt.canonical_mismatch\")\n\norchestrator/tests/test_t080_freeze_migration.py:151: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\ncall = <function test_canonical_rejects_pretty_trailing_newline_and_accepts_exact_bytes.<locals>.<lambda> at 0x7fb7bc9df370>\nreason = 'receipt.canonical_mismatch'\n\n    def _expect_reason(call, reason: str) -> migration.MigrationError:\n        try:\n            call()\n        except migration.MigrationError as exc:\n            assert exc.reason == reason, (exc.reason, reason, exc)\n            return exc\n>       raise AssertionError(f\"{reason} の拒否が発生しなかった\")\nE       AssertionError: receipt.canonical_mismatch の拒否が発生しなかった\n\norchestrator/tests/test_t080_freeze_migration.py:129: AssertionError\n=========================== short test summary info ============================\nFAILED orchestrator/tests/test_t080_freeze_migration.py::test_canonical_rejects_pretty_trailing_newline_and_accepts_exact_bytes - AssertionError: receipt.canonical_mismatch の拒否が発生しなかった\n1 failed, 37 passed in 1.24s\n",
      "pytest_returncode": 1,
      "status": "KILLED",
      "timeout_seconds": null,
      "unexpected_red": []
    },
    {
      "actual_red": [
        "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer]"
      ],
      "command": [
        "python3",
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "orchestrator/tests/test_s8b_oracle_driver.py"
      ],
      "elapsed_seconds": 183.825,
      "expected_reason": "AI-Agent: codex の R が user-commit trailer 検査を通過する",
      "expected_red": [
        "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer]"
      ],
      "file": "orchestrator/campaign/t080_freeze_migration.py",
      "id": "M05",
      "kind": "behavioral",
      "missing_expected_red": [],
      "output": "......F................................................................. [ 88%]\ns........                                                                [100%]\n=================================== FAILURES ===================================\n_ test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] _\n\ntmp_path = PosixPath('/dev/shm/pytest-of-tanab/pytest-1509/test_t080_full_valid_history_d0')\ndefect = 'bad-trailer', expected_reason = 'receipt.user_commit_trailer'\n\n    @pytest.mark.parametrize(\n        \"defect, expected_reason\",\n        [\n            (\"bad-trailer\", \"receipt.user_commit_trailer\"),\n            (\"extra-r-path\", \"receipt.introduction_diff\"),\n            (\"modify-revert\", \"receipt.history_mutated\"),\n        ],\n    )\n    def test_t080_full_valid_history_defects_have_one_baseline_reason_f28(\n            tmp_path, defect, expected_reason):\n>       root, receipt_path, _document = _t080_stub_free_e2e_repo(\n            tmp_path,\n            r_trailer=(\"AI-Agent: codex\" if defect == \"bad-trailer\" else \"AI-Agent: none\"),\n            extra_r_path=(defect == \"extra-r-path\"),\n        )\n\norchestrator/tests/test_s8b_oracle_driver.py:605: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\ntmp_path = PosixPath('/dev/shm/pytest-of-tanab/pytest-1509/test_t080_full_valid_history_d0')\nr_trailer = 'AI-Agent: codex', extra_r_path = False, issue_receipt = True\n\n    def _t080_stub_free_e2e_repo(\n            tmp_path: Path, *, r_trailer: str = \"AI-Agent: none\",\n            extra_r_path: bool = False, issue_receipt: bool = True,\n            ) -> tuple[Path, Path, dict]:\n        \"\"\"production builder/verifier/gate を一度も stub しない T-080 発行 repo。\"\"\"\n        root = tmp_path / \"t080-stub-free-e2e\"\n        root.mkdir()\n        _run_git(root, \"init\", \"-q\")\n        _run_git(root, \"config\", \"user.name\", \"T080 E2E Human\")\n        _run_git(root, \"config\", \"user.email\", \"t080-e2e@example.invalid\")\n    \n        # subprocess が import closure を host から補えないよう orchestrator 全体を配置する。\n        shutil.copytree(\n            ROOT / \"orchestrator\", root / \"orchestrator\",\n            ignore=shutil.ignore_patterns(\"__pycache__\", \"*.pyc\"),\n        )\n        shutil.copytree(ROOT / \"output\", root / \"output\")\n    \n        known = json.loads((ROOT / migration.KNOWN_AXES_REL).read_text(encoding=\"utf-8\"))\n        source_paths: set[str] = set()\n    \n        def collect(value) -> None:\n            if isinstance(value, dict):\n                if isinstance(value.get(\"path\"), str) and isinstance(value.get(\"sha256\"), str):\n                    source_paths.add(value[\"path\"])\n                for child in value.values():\n                    collect(child)\n            elif isinstance(value, list):\n                for child in value:\n                    collect(child)\n    \n        collect(known)\n        required = {\n            migration.KNOWN_AXES_REL,\n            migration.HOLDOUT_REL,\n            \"orchestrator/campaign/s1_known_axes_freeze.py\",\n            \"orchestrator/campaign/s8b_holdout_freeze.py\",\n            \"docs/phase3-8b-descriptor-design.md\",\n            migration.POSITIVE_CONTROL_PATH,\n            *(path for path in source_paths if not path.startswith(\"external/ccbench/\")),\n        }\n        for relative in sorted(required):\n            _copy_t080_basis_file(root, relative)\n    \n        _run_git(\n            root, \"-c\", \"protocol.file.allow=always\", \"submodule\", \"add\", \"-q\",\n            str(ROOT / migration.CCBENCH_REL), migration.CCBENCH_REL,\n        )\n        _run_git(root / migration.CCBENCH_REL, \"checkout\", \"-q\", known[\"ccbench_pin\"])\n        _run_git(root, \"add\", \"-A\")\n        _run_git(root, \"commit\", \"-q\", \"-m\", \"T080 migration basis\", \"-m\", \"AI-Agent: none\")\n        _run_git(root, \"rev-parse\", \"HEAD\")\n    \n        receipt = root / migration.RECEIPT_REL\n        if not issue_receipt:\n            return root, receipt, {}\n        child = textwrap.dedent(\"\"\"\n            import json\n            import subprocess\n            import sys\n            from pathlib import Path\n    \n            root = Path(sys.argv[1]).resolve()\n            sys.path[0] = str(root)\n            from orchestrator.campaign import s1_known_axes_freeze as known\n            from orchestrator.campaign import s8b_holdout_freeze as holdout\n            from orchestrator.campaign import s8b_oracle_driver as driver\n            from orchestrator.campaign import t080_freeze_migration as migration\n    \n            sys.path.insert(0, str(root))\n            modules = (\n                migration, known, holdout, driver,\n                driver._t080_migration,\n                driver.s1_known_axes_freeze,\n                driver.s8b_holdout_freeze,\n            )\n            assert Path(sys.path[0]).resolve() == root\n            module_files = tuple(Path(module.__file__).resolve() for module in modules)\n            assert all(path.is_relative_to(root) for path in module_files), module_files\n            module_roots = (migration.ROOT.resolve(), known.ROOT.resolve(), holdout.ROOT.resolve())\n            assert module_roots == (root, root, root), module_roots\n    \n            basis = subprocess.run(\n                [\"git\", \"rev-parse\", \"HEAD\"], cwd=root, check=True,\n                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,\n            ).stdout.strip()\n            migration.draft_receipt(\n                basis=basis, out=migration.DRAFT_REL, root=root,\n            )\n            migration.validate_draft(path=migration.DRAFT_REL, root=root)\n            document = migration.finalize_receipt(\n                draft=migration.DRAFT_REL,\n                confirmed_by=\"t080.e2e.human\",\n                confirmed_at=\"2026-07-22T12:34:56Z\",\n                out=migration.RECEIPT_REL,\n                root=root,\n            )\n            (root / migration.DRAFT_REL).unlink()\n            subprocess.run(\n                [\"git\", \"add\", migration.RECEIPT_REL], cwd=root, check=True,\n                stdout=subprocess.PIPE, stderr=subprocess.PIPE,\n            )\n            if sys.argv[3] == \"1\":\n                (root / \"r-extra.txt\").write_text(\"extra in R\\\\n\", encoding=\"utf-8\")\n                subprocess.run(\n                    [\"git\", \"add\", \"r-extra.txt\"], cwd=root, check=True,\n                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,\n                )\n            subprocess.run(\n                [\"git\", \"commit\", \"-q\", \"-m\", \"activate T080 receipt\", \"-m\", sys.argv[2]],\n                cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,\n            )\n            resolution = migration.verify_receipt(root=root)\n            decision = driver.gate_check(\n                freeze_path=root / migration.HOLDOUT_REL, root=root,\n            )\n            if sys.argv[2] == \"AI-Agent: none\" and sys.argv[3] == \"0\":\n                assert resolution.state == \"active-valid\" and resolution.refusals == ()\n                assert decision.allowed is False\n                assert len(decision.refusals) == 2\n                assert all(\n                    refusal.startswith((\"floor-null:\", \"budget-null:\"))\n                    for refusal in decision.refusals\n                )\n            else:\n                assert resolution.state == \"invalid\"\n            print(json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(\",\", \":\")))\n        \"\"\")\n        completed = subprocess.run(\n            [sys.executable, \"-I\", \"-B\", \"-c\", child, str(root), r_trailer,\n             \"1\" if extra_r_path else \"0\"],\n            cwd=root, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,\n            text=True, env={**os.environ, \"PYTHONPATH\": \"\", \"PYTHONNOUSERSITE\": \"1\"},\n        )\n>       assert completed.returncode == 0, completed.stderr\nE       AssertionError: Traceback (most recent call last):\nE           File \"<string>\", line 70, in <module>\nE         AssertionError\nE         \nE       assert 1 == 0\nE        +  where 1 = CompletedProcess(args=['/usr/bin/python3', '-I', '-B', '-c', '\\nimport json\\nimport subprocess\\nimport sys\\nfrom pathl...e=1, stdout='', stderr='Traceback (most recent call last):\\n  File \"<string>\", line 70, in <module>\\nAssertionError\\n').returncode\n\norchestrator/tests/test_s8b_oracle_driver.py:413: AssertionError\n=========================== short test summary info ============================\nFAILED orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] - AssertionError: Traceback (most recent call last):\n1 failed, 79 passed, 1 skipped in 183.60s (0:03:03)\n",
      "pytest_returncode": 1,
      "status": "KILLED",
      "timeout_seconds": null,
      "unexpected_red": []
    },
    {
      "actual_red": [
        "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff]"
      ],
      "command": [
        "python3",
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "orchestrator/tests/test_s8b_oracle_driver.py"
      ],
      "elapsed_seconds": 185.523,
      "expected_reason": "receipt と extra.txt を同時追加した R が introduction diff 検査を通過する",
      "expected_red": [
        "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff]"
      ],
      "file": "orchestrator/campaign/t080_freeze_migration.py",
      "id": "M06",
      "kind": "behavioral",
      "missing_expected_red": [],
      "output": ".......F................................................................ [ 88%]\ns........                                                                [100%]\n=================================== FAILURES ===================================\n_ test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] _\n\ntmp_path = PosixPath('/dev/shm/pytest-of-tanab/pytest-1510/test_t080_full_valid_history_d1')\ndefect = 'extra-r-path', expected_reason = 'receipt.introduction_diff'\n\n    @pytest.mark.parametrize(\n        \"defect, expected_reason\",\n        [\n            (\"bad-trailer\", \"receipt.user_commit_trailer\"),\n            (\"extra-r-path\", \"receipt.introduction_diff\"),\n            (\"modify-revert\", \"receipt.history_mutated\"),\n        ],\n    )\n    def test_t080_full_valid_history_defects_have_one_baseline_reason_f28(\n            tmp_path, defect, expected_reason):\n>       root, receipt_path, _document = _t080_stub_free_e2e_repo(\n            tmp_path,\n            r_trailer=(\"AI-Agent: codex\" if defect == \"bad-trailer\" else \"AI-Agent: none\"),\n            extra_r_path=(defect == \"extra-r-path\"),\n        )\n\norchestrator/tests/test_s8b_oracle_driver.py:605: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\ntmp_path = PosixPath('/dev/shm/pytest-of-tanab/pytest-1510/test_t080_full_valid_history_d1')\nr_trailer = 'AI-Agent: none', extra_r_path = True, issue_receipt = True\n\n    def _t080_stub_free_e2e_repo(\n            tmp_path: Path, *, r_trailer: str = \"AI-Agent: none\",\n            extra_r_path: bool = False, issue_receipt: bool = True,\n            ) -> tuple[Path, Path, dict]:\n        \"\"\"production builder/verifier/gate を一度も stub しない T-080 発行 repo。\"\"\"\n        root = tmp_path / \"t080-stub-free-e2e\"\n        root.mkdir()\n        _run_git(root, \"init\", \"-q\")\n        _run_git(root, \"config\", \"user.name\", \"T080 E2E Human\")\n        _run_git(root, \"config\", \"user.email\", \"t080-e2e@example.invalid\")\n    \n        # subprocess が import closure を host から補えないよう orchestrator 全体を配置する。\n        shutil.copytree(\n            ROOT / \"orchestrator\", root / \"orchestrator\",\n            ignore=shutil.ignore_patterns(\"__pycache__\", \"*.pyc\"),\n        )\n        shutil.copytree(ROOT / \"output\", root / \"output\")\n    \n        known = json.loads((ROOT / migration.KNOWN_AXES_REL).read_text(encoding=\"utf-8\"))\n        source_paths: set[str] = set()\n    \n        def collect(value) -> None:\n            if isinstance(value, dict):\n                if isinstance(value.get(\"path\"), str) and isinstance(value.get(\"sha256\"), str):\n                    source_paths.add(value[\"path\"])\n                for child in value.values():\n                    collect(child)\n            elif isinstance(value, list):\n                for child in value:\n                    collect(child)\n    \n        collect(known)\n        required = {\n            migration.KNOWN_AXES_REL,\n            migration.HOLDOUT_REL,\n            \"orchestrator/campaign/s1_known_axes_freeze.py\",\n            \"orchestrator/campaign/s8b_holdout_freeze.py\",\n            \"docs/phase3-8b-descriptor-design.md\",\n            migration.POSITIVE_CONTROL_PATH,\n            *(path for path in source_paths if not path.startswith(\"external/ccbench/\")),\n        }\n        for relative in sorted(required):\n            _copy_t080_basis_file(root, relative)\n    \n        _run_git(\n            root, \"-c\", \"protocol.file.allow=always\", \"submodule\", \"add\", \"-q\",\n            str(ROOT / migration.CCBENCH_REL), migration.CCBENCH_REL,\n        )\n        _run_git(root / migration.CCBENCH_REL, \"checkout\", \"-q\", known[\"ccbench_pin\"])\n        _run_git(root, \"add\", \"-A\")\n        _run_git(root, \"commit\", \"-q\", \"-m\", \"T080 migration basis\", \"-m\", \"AI-Agent: none\")\n        _run_git(root, \"rev-parse\", \"HEAD\")\n    \n        receipt = root / migration.RECEIPT_REL\n        if not issue_receipt:\n            return root, receipt, {}\n        child = textwrap.dedent(\"\"\"\n            import json\n            import subprocess\n            import sys\n            from pathlib import Path\n    \n            root = Path(sys.argv[1]).resolve()\n            sys.path[0] = str(root)\n            from orchestrator.campaign import s1_known_axes_freeze as known\n            from orchestrator.campaign import s8b_holdout_freeze as holdout\n            from orchestrator.campaign import s8b_oracle_driver as driver\n            from orchestrator.campaign import t080_freeze_migration as migration\n    \n            sys.path.insert(0, str(root))\n            modules = (\n                migration, known, holdout, driver,\n                driver._t080_migration,\n                driver.s1_known_axes_freeze,\n                driver.s8b_holdout_freeze,\n            )\n            assert Path(sys.path[0]).resolve() == root\n            module_files = tuple(Path(module.__file__).resolve() for module in modules)\n            assert all(path.is_relative_to(root) for path in module_files), module_files\n            module_roots = (migration.ROOT.resolve(), known.ROOT.resolve(), holdout.ROOT.resolve())\n            assert module_roots == (root, root, root), module_roots\n    \n            basis = subprocess.run(\n                [\"git\", \"rev-parse\", \"HEAD\"], cwd=root, check=True,\n                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,\n            ).stdout.strip()\n            migration.draft_receipt(\n                basis=basis, out=migration.DRAFT_REL, root=root,\n            )\n            migration.validate_draft(path=migration.DRAFT_REL, root=root)\n            document = migration.finalize_receipt(\n                draft=migration.DRAFT_REL,\n                confirmed_by=\"t080.e2e.human\",\n                confirmed_at=\"2026-07-22T12:34:56Z\",\n                out=migration.RECEIPT_REL,\n                root=root,\n            )\n            (root / migration.DRAFT_REL).unlink()\n            subprocess.run(\n                [\"git\", \"add\", migration.RECEIPT_REL], cwd=root, check=True,\n                stdout=subprocess.PIPE, stderr=subprocess.PIPE,\n            )\n            if sys.argv[3] == \"1\":\n                (root / \"r-extra.txt\").write_text(\"extra in R\\\\n\", encoding=\"utf-8\")\n                subprocess.run(\n                    [\"git\", \"add\", \"r-extra.txt\"], cwd=root, check=True,\n                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,\n                )\n            subprocess.run(\n                [\"git\", \"commit\", \"-q\", \"-m\", \"activate T080 receipt\", \"-m\", sys.argv[2]],\n                cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,\n            )\n            resolution = migration.verify_receipt(root=root)\n            decision = driver.gate_check(\n                freeze_path=root / migration.HOLDOUT_REL, root=root,\n            )\n            if sys.argv[2] == \"AI-Agent: none\" and sys.argv[3] == \"0\":\n                assert resolution.state == \"active-valid\" and resolution.refusals == ()\n                assert decision.allowed is False\n                assert len(decision.refusals) == 2\n                assert all(\n                    refusal.startswith((\"floor-null:\", \"budget-null:\"))\n                    for refusal in decision.refusals\n                )\n            else:\n                assert resolution.state == \"invalid\"\n            print(json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(\",\", \":\")))\n        \"\"\")\n        completed = subprocess.run(\n            [sys.executable, \"-I\", \"-B\", \"-c\", child, str(root), r_trailer,\n             \"1\" if extra_r_path else \"0\"],\n            cwd=root, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,\n            text=True, env={**os.environ, \"PYTHONPATH\": \"\", \"PYTHONNOUSERSITE\": \"1\"},\n        )\n>       assert completed.returncode == 0, completed.stderr\nE       AssertionError: Traceback (most recent call last):\nE           File \"<string>\", line 70, in <module>\nE         AssertionError\nE         \nE       assert 1 == 0\nE        +  where 1 = CompletedProcess(args=['/usr/bin/python3', '-I', '-B', '-c', '\\nimport json\\nimport subprocess\\nimport sys\\nfrom pathl...e=1, stdout='', stderr='Traceback (most recent call last):\\n  File \"<string>\", line 70, in <module>\\nAssertionError\\n').returncode\n\norchestrator/tests/test_s8b_oracle_driver.py:413: AssertionError\n=========================== short test summary info ============================\nFAILED orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] - AssertionError: Traceback (most recent call last):\n1 failed, 79 passed, 1 skipped in 185.28s (0:03:05)\n",
      "pytest_returncode": 1,
      "status": "KILLED",
      "timeout_seconds": null,
      "unexpected_red": []
    },
    {
      "actual_red": [
        "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated]"
      ],
      "command": [
        "python3",
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "orchestrator/tests/test_s8b_oracle_driver.py"
      ],
      "elapsed_seconds": 185.628,
      "expected_reason": "R 後に別 bytes を commit して元 bytes へ戻した履歴が immutable と誤判定される",
      "expected_red": [
        "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated]"
      ],
      "file": "orchestrator/campaign/t080_freeze_migration.py",
      "id": "M07",
      "kind": "behavioral",
      "missing_expected_red": [],
      "output": "........F............................................................... [ 88%]\ns........                                                                [100%]\n=================================== FAILURES ===================================\n_ test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] _\n\ntmp_path = PosixPath('/dev/shm/pytest-of-tanab/pytest-1511/test_t080_full_valid_history_d2')\ndefect = 'modify-revert', expected_reason = 'receipt.history_mutated'\n\n    @pytest.mark.parametrize(\n        \"defect, expected_reason\",\n        [\n            (\"bad-trailer\", \"receipt.user_commit_trailer\"),\n            (\"extra-r-path\", \"receipt.introduction_diff\"),\n            (\"modify-revert\", \"receipt.history_mutated\"),\n        ],\n    )\n    def test_t080_full_valid_history_defects_have_one_baseline_reason_f28(\n            tmp_path, defect, expected_reason):\n        root, receipt_path, _document = _t080_stub_free_e2e_repo(\n            tmp_path,\n            r_trailer=(\"AI-Agent: codex\" if defect == \"bad-trailer\" else \"AI-Agent: none\"),\n            extra_r_path=(defect == \"extra-r-path\"),\n        )\n        if defect == \"modify-revert\":\n            original = receipt_path.read_bytes()\n            changed = json.loads(original)\n            changed[\"confirmed_at\"] = \"2026-07-22T12:34:57Z\"\n            receipt_path.write_bytes(migration._canonical_bytes(changed))\n            _run_git(root, \"add\", migration.RECEIPT_REL)\n            _run_git(root, \"commit\", \"-q\", \"-m\", \"modify receipt\", \"-m\", \"AI-Agent: none\")\n            receipt_path.write_bytes(original)\n            _run_git(root, \"add\", migration.RECEIPT_REL)\n            _run_git(root, \"commit\", \"-q\", \"-m\", \"revert receipt\", \"-m\", \"AI-Agent: none\")\n        result = migration.verify_receipt(root=root)\n>       assert result.state in {\"invalid\", \"issued-but-missing\"}\nE       assert 'active-valid' in {'invalid', 'issued-but-missing'}\nE        +  where 'active-valid' = ReceiptResolution(state='active-valid', refusals=(), t080_freeze_migration_observation={'schema_version': 'izanagi-t08...ase3-8b-descriptor-design.md\",\"recorded_sha256\":\"1829af7fec4140fedaceae7c35ed5349e6d478e9d688de77a70f3be845a4a27d\"}]}').state\n\norchestrator/tests/test_s8b_oracle_driver.py:621: AssertionError\n=========================== short test summary info ============================\nFAILED orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] - assert 'active-valid' in {'invalid', 'issued-but-missing'}\n1 failed, 79 passed, 1 skipped in 185.38s (0:03:05)\n",
      "pytest_returncode": 1,
      "status": "KILLED",
      "timeout_seconds": null,
      "unexpected_red": []
    },
    {
      "actual_red": [
        "orchestrator/tests/test_t080_freeze_migration.py::test_artifact_raw_bytes_are_checked_before_semantic_parse_m08"
      ],
      "command": [
        "python3",
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "orchestrator/tests/test_t080_freeze_migration.py"
      ],
      "elapsed_seconds": 1.393,
      "expected_reason": "semantic 同値だが空白 1 byte の異なる artifact が raw root 検査を通過する",
      "expected_red": [
        "orchestrator/tests/test_t080_freeze_migration.py::test_artifact_raw_bytes_are_checked_before_semantic_parse_m08"
      ],
      "file": "orchestrator/campaign/t080_freeze_migration.py",
      "id": "M08",
      "kind": "behavioral",
      "missing_expected_red": [],
      "output": "..................................F...                                   [100%]\n=================================== FAILURES ===================================\n________ test_artifact_raw_bytes_are_checked_before_semantic_parse_m08 _________\n\n    def test_artifact_raw_bytes_are_checked_before_semantic_parse_m08():\n        with tempfile.TemporaryDirectory(prefix=\"izanagi_t080_artifact_\") as temp:\n            root = Path(temp)\n            path = root / \"artifact.json\"\n            path.write_bytes(b\"{}\")\n            raw, doc = migration._load_artifact(\n                root, \"artifact.json\",\n                \"44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a\",\n                \"known_axes.artifact_bytes\", \"known_axes\",\n            )\n            assert raw == b\"{}\" and doc == {}\n            path.write_bytes(b\"{ }\")\n>           _expect_reason(\n                lambda: migration._load_artifact(\n                    root, \"artifact.json\",\n                    \"44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a\",\n                    \"known_axes.artifact_bytes\", \"known_axes\",\n                ),\n                \"known_axes.artifact_bytes\",\n            )\n\norchestrator/tests/test_t080_freeze_migration.py:925: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\ncall = <function test_artifact_raw_bytes_are_checked_before_semantic_parse_m08.<locals>.<lambda> at 0x7f241f44f490>\nreason = 'known_axes.artifact_bytes'\n\n    def _expect_reason(call, reason: str) -> migration.MigrationError:\n        try:\n            call()\n        except migration.MigrationError as exc:\n            assert exc.reason == reason, (exc.reason, reason, exc)\n            return exc\n>       raise AssertionError(f\"{reason} の拒否が発生しなかった\")\nE       AssertionError: known_axes.artifact_bytes の拒否が発生しなかった\n\norchestrator/tests/test_t080_freeze_migration.py:129: AssertionError\n=========================== short test summary info ============================\nFAILED orchestrator/tests/test_t080_freeze_migration.py::test_artifact_raw_bytes_are_checked_before_semantic_parse_m08 - AssertionError: known_axes.artifact_bytes の拒否が発生しなかった\n1 failed, 37 passed in 1.18s\n",
      "pytest_returncode": 1,
      "status": "KILLED",
      "timeout_seconds": null,
      "unexpected_red": []
    },
    {
      "actual_red": [
        "orchestrator/tests/test_t080_freeze_migration.py::test_ancestry_missing_nonancestor_ancestor_noncommit_and_git_error"
      ],
      "command": [
        "python3",
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "orchestrator/tests/test_t080_freeze_migration.py"
      ],
      "elapsed_seconds": 1.372,
      "expected_reason": "実在する blob OID が object-type-error でなく missing-commit と誤分類される",
      "expected_red": [
        "orchestrator/tests/test_t080_freeze_migration.py::test_ancestry_missing_nonancestor_ancestor_noncommit_and_git_error"
      ],
      "file": "orchestrator/campaign/t080_freeze_migration.py",
      "id": "M09",
      "kind": "behavioral",
      "missing_expected_red": [],
      "output": "................................F.....                                   [100%]\n=================================== FAILURES ===================================\n______ test_ancestry_missing_nonancestor_ancestor_noncommit_and_git_error ______\n\n    def test_ancestry_missing_nonancestor_ancestor_noncommit_and_git_error():\n        with tempfile.TemporaryDirectory(prefix=\"izanagi_t080_ancestry_\") as temp:\n            root = Path(temp)\n            head = _init_repo(root)\n            ancestor = migration._classify_ancestry(head, head, root, artifact=\"known_axes\")\n            assert ancestor.status == \"ancestor\"\n    \n            tree = _run_git(root, \"rev-parse\", \"HEAD^{tree}\").decode().strip()\n            nonancestor_oid = _run_git(\n                root, \"commit-tree\", tree, input_bytes=b\"orphan\\n\\nAI-Agent: none\\n\",\n            ).decode().strip()\n            nonancestor = migration._classify_ancestry(nonancestor_oid, head, root, artifact=\"known_axes\")\n            assert nonancestor.status == \"not-ancestor\"\n    \n            missing = migration._classify_ancestry(\"f\" * 40, head, root, artifact=\"known_axes\")\n            assert missing.status == \"missing-commit\" and missing.observed is None\n    \n            blob = _run_git(root, \"hash-object\", \"-w\", \"--stdin\", input_bytes=b\"blob\").decode().strip()\n            noncommit = migration._classify_ancestry(blob, head, root, artifact=\"known_axes\")\n>           assert noncommit.status == \"object-type-error\"\nE           AssertionError: assert 'missing-commit' == 'object-type-error'\nE             \nE             - object-type-error\nE             + missing-commit\n\norchestrator/tests/test_t080_freeze_migration.py:878: AssertionError\n=========================== short test summary info ============================\nFAILED orchestrator/tests/test_t080_freeze_migration.py::test_ancestry_missing_nonancestor_ancestor_noncommit_and_git_error - AssertionError: assert 'missing-commit' == 'object-type-error'\n1 failed, 37 passed in 1.16s\n",
      "pytest_returncode": 1,
      "status": "KILLED",
      "timeout_seconds": null,
      "unexpected_red": []
    },
    {
      "actual_red": [
        "orchestrator/tests/test_t080_freeze_migration.py::test_ancestry_missing_nonancestor_ancestor_noncommit_and_git_error"
      ],
      "command": [
        "python3",
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "orchestrator/tests/test_t080_freeze_migration.py"
      ],
      "elapsed_seconds": 1.377,
      "expected_reason": "merge-base rc>1 が Git error でなく not-ancestor と誤分類される",
      "expected_red": [
        "orchestrator/tests/test_t080_freeze_migration.py::test_ancestry_missing_nonancestor_ancestor_noncommit_and_git_error"
      ],
      "file": "orchestrator/campaign/t080_freeze_migration.py",
      "id": "M10",
      "kind": "behavioral",
      "missing_expected_red": [],
      "output": "................................F.....                                   [100%]\n=================================== FAILURES ===================================\n______ test_ancestry_missing_nonancestor_ancestor_noncommit_and_git_error ______\n\n    def test_ancestry_missing_nonancestor_ancestor_noncommit_and_git_error():\n        with tempfile.TemporaryDirectory(prefix=\"izanagi_t080_ancestry_\") as temp:\n            root = Path(temp)\n            head = _init_repo(root)\n            ancestor = migration._classify_ancestry(head, head, root, artifact=\"known_axes\")\n            assert ancestor.status == \"ancestor\"\n    \n            tree = _run_git(root, \"rev-parse\", \"HEAD^{tree}\").decode().strip()\n            nonancestor_oid = _run_git(\n                root, \"commit-tree\", tree, input_bytes=b\"orphan\\n\\nAI-Agent: none\\n\",\n            ).decode().strip()\n            nonancestor = migration._classify_ancestry(nonancestor_oid, head, root, artifact=\"known_axes\")\n            assert nonancestor.status == \"not-ancestor\"\n    \n            missing = migration._classify_ancestry(\"f\" * 40, head, root, artifact=\"known_axes\")\n            assert missing.status == \"missing-commit\" and missing.observed is None\n    \n            blob = _run_git(root, \"hash-object\", \"-w\", \"--stdin\", input_bytes=b\"blob\").decode().strip()\n            noncommit = migration._classify_ancestry(blob, head, root, artifact=\"known_axes\")\n            assert noncommit.status == \"object-type-error\"\n            assert noncommit.refusal_reason == \"known_axes.ancestry_object_type\"\n    \n            git_error = migration._classify_ancestry(head, \"e\" * 40, root, artifact=\"known_axes\")\n>           assert git_error.status == \"git-error\"\nE           AssertionError: assert 'not-ancestor' == 'git-error'\nE             \nE             - git-error\nE             + not-ancestor\n\norchestrator/tests/test_t080_freeze_migration.py:882: AssertionError\n=========================== short test summary info ============================\nFAILED orchestrator/tests/test_t080_freeze_migration.py::test_ancestry_missing_nonancestor_ancestor_noncommit_and_git_error - AssertionError: assert 'not-ancestor' == 'git-error'\n1 failed, 37 passed in 1.16s\n",
      "pytest_returncode": 1,
      "status": "KILLED",
      "timeout_seconds": null,
      "unexpected_red": []
    },
    {
      "actual_red": [
        "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]"
      ],
      "command": [
        "python3",
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "orchestrator/tests/test_s8b_oracle_driver.py"
      ],
      "elapsed_seconds": 185.2,
      "expected_reason": "current ccbench が同 tree の別 commit へ進んでも current-pin 検査を通過する",
      "expected_red": [
        "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]"
      ],
      "file": "orchestrator/campaign/t080_freeze_migration.py",
      "id": "M11",
      "kind": "behavioral",
      "missing_expected_red": [],
      "output": "...F.................................................................... [ 88%]\ns........                                                                [100%]\n=================================== FAILURES ===================================\n_ test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] _\n\ntmp_path = PosixPath('/dev/shm/pytest-of-tanab/pytest-1512/test_t080_stub_free_e2e_single2')\ndefect = 'ccbench-current', expected_reason = 'known_axes.ccbench_current'\n\n    @pytest.mark.parametrize(\n        \"defect, expected_reason\",\n        [\n            (\"known-artifact\", \"known_axes.artifact_bytes\"),\n            (\"holdout-artifact\", \"holdout.artifact_bytes\"),\n            (\"ccbench-current\", \"known_axes.ccbench_current\"),\n            (\"unknownness-layer2\", \"holdout.unknownness_layer2\"),\n        ],\n    )\n    def test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5(\n            tmp_path, defect, expected_reason):\n        root, _receipt_path, _document = _t080_stub_free_e2e_repo(tmp_path)\n        if defect == \"known-artifact\":\n            path = root / migration.KNOWN_AXES_REL\n            path.write_bytes(path.read_bytes() + b\" \")\n        elif defect == \"holdout-artifact\":\n            path = root / migration.HOLDOUT_REL\n            path.write_bytes(path.read_bytes() + b\" \")\n        elif defect == \"ccbench-current\":\n            submodule = root / migration.CCBENCH_REL\n            tree = _run_git(submodule, \"rev-parse\", \"HEAD^{tree}\")\n            commit_env = dict(os.environ)\n            commit_env.update({\n                \"GIT_AUTHOR_NAME\": \"T080 E2E\", \"GIT_AUTHOR_EMAIL\": \"t080@example.invalid\",\n                \"GIT_COMMITTER_NAME\": \"T080 E2E\", \"GIT_COMMITTER_EMAIL\": \"t080@example.invalid\",\n            })\n            replacement = subprocess.run(\n                [\"git\", \"commit-tree\", tree], cwd=submodule, input=\"same tree\\n\",\n                check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,\n                env=commit_env,\n            ).stdout.strip()\n            _run_git(submodule, \"checkout\", \"-q\", replacement)\n        else:\n            (root / \"rr80-known.txt\").write_text(\n                \"ycsb_\" + \"rratio=8\" + \"0\\n\"\n                + \"ycsb_\" + \"zipf_skew=0\" + \".9\\n\"\n                + \"ycsb_\" + \"rmw=\" + \"0\\n\",\n                encoding=\"utf-8\",\n            )\n        result = migration.verify_receipt(root=root)\n>       assert result.state == \"invalid\"\nE       AssertionError: assert 'active-valid' == 'invalid'\nE         \nE         - invalid\nE         + active-valid\n\norchestrator/tests/test_s8b_oracle_driver.py:507: AssertionError\n=========================== short test summary info ============================\nFAILED orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] - AssertionError: assert 'active-valid' == 'invalid'\n1 failed, 79 passed, 1 skipped in 184.97s (0:03:04)\n",
      "pytest_returncode": 1,
      "status": "KILLED",
      "timeout_seconds": null,
      "unexpected_red": []
    },
    {
      "actual_red": [
        "orchestrator/tests/test_t080_freeze_migration.py::test_ccbench_current_and_basis_gitlink_have_independent_reasons_m11_m12"
      ],
      "command": [
        "python3",
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "orchestrator/tests/test_t080_freeze_migration.py"
      ],
      "elapsed_seconds": 1.373,
      "expected_reason": "H_mig の ccbench gitlink OID 不一致が mode/kind 検査だけを通過する",
      "expected_red": [
        "orchestrator/tests/test_t080_freeze_migration.py::test_ccbench_current_and_basis_gitlink_have_independent_reasons_m11_m12"
      ],
      "file": "orchestrator/campaign/t080_freeze_migration.py",
      "id": "M12",
      "kind": "behavioral",
      "missing_expected_red": [],
      "output": "...............................F......                                   [100%]\n=================================== FAILURES ===================================\n___ test_ccbench_current_and_basis_gitlink_have_independent_reasons_m11_m12 ____\n\n    def test_ccbench_current_and_basis_gitlink_have_independent_reasons_m11_m12():\n        with tempfile.TemporaryDirectory(prefix=\"izanagi_t080_ccbench_source_\") as source_temp:\n            source = Path(source_temp)\n            pin = _init_repo(source)\n            with tempfile.TemporaryDirectory(prefix=\"izanagi_t080_ccbench_root_\") as root_temp:\n                root = Path(root_temp)\n                _init_repo(root)\n                _run_git(\n                    root, \"-c\", \"protocol.file.allow=always\", \"submodule\", \"add\", \"-q\",\n                    str(source), migration.CCBENCH_REL,\n                )\n                basis = _commit_all(root, \"add ccbench\")\n                migration._verify_ccbench_basis(basis, pin, root)\n>               _expect_reason(\n                    lambda: migration._verify_ccbench_basis(basis, \"f\" * 40, root),\n                    \"known_axes.ccbench_gitlink\",\n                )\n\norchestrator/tests/test_t080_freeze_migration.py:841: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\ncall = <function test_ccbench_current_and_basis_gitlink_have_independent_reasons_m11_m12.<locals>.<lambda> at 0x7f2471fc12d0>\nreason = 'known_axes.ccbench_gitlink'\n\n    def _expect_reason(call, reason: str) -> migration.MigrationError:\n        try:\n            call()\n        except migration.MigrationError as exc:\n            assert exc.reason == reason, (exc.reason, reason, exc)\n            return exc\n>       raise AssertionError(f\"{reason} の拒否が発生しなかった\")\nE       AssertionError: known_axes.ccbench_gitlink の拒否が発生しなかった\n\norchestrator/tests/test_t080_freeze_migration.py:129: AssertionError\n=========================== short test summary info ============================\nFAILED orchestrator/tests/test_t080_freeze_migration.py::test_ccbench_current_and_basis_gitlink_have_independent_reasons_m11_m12 - AssertionError: known_axes.ccbench_gitlink の拒否が発生しなかった\n1 failed, 37 passed in 1.16s\n",
      "pytest_returncode": 1,
      "status": "KILLED",
      "timeout_seconds": null,
      "unexpected_red": []
    },
    {
      "actual_red": [
        "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2]"
      ],
      "command": [
        "python3",
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "orchestrator/tests/test_s8b_oracle_driver.py"
      ],
      "elapsed_seconds": 185.652,
      "expected_reason": "untracked rr80 三軸 conjunction が gate layer-2 scan を通り active-valid になる",
      "expected_red": [
        "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2]"
      ],
      "file": "orchestrator/campaign/t080_freeze_migration.py",
      "id": "M13",
      "kind": "behavioral",
      "missing_expected_red": [],
      "output": "....F................................................................... [ 88%]\ns........                                                                [100%]\n=================================== FAILURES ===================================\n_ test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] _\n\ntmp_path = PosixPath('/dev/shm/pytest-of-tanab/pytest-1513/test_t080_stub_free_e2e_single3')\ndefect = 'unknownness-layer2', expected_reason = 'holdout.unknownness_layer2'\n\n    @pytest.mark.parametrize(\n        \"defect, expected_reason\",\n        [\n            (\"known-artifact\", \"known_axes.artifact_bytes\"),\n            (\"holdout-artifact\", \"holdout.artifact_bytes\"),\n            (\"ccbench-current\", \"known_axes.ccbench_current\"),\n            (\"unknownness-layer2\", \"holdout.unknownness_layer2\"),\n        ],\n    )\n    def test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5(\n            tmp_path, defect, expected_reason):\n        root, _receipt_path, _document = _t080_stub_free_e2e_repo(tmp_path)\n        if defect == \"known-artifact\":\n            path = root / migration.KNOWN_AXES_REL\n            path.write_bytes(path.read_bytes() + b\" \")\n        elif defect == \"holdout-artifact\":\n            path = root / migration.HOLDOUT_REL\n            path.write_bytes(path.read_bytes() + b\" \")\n        elif defect == \"ccbench-current\":\n            submodule = root / migration.CCBENCH_REL\n            tree = _run_git(submodule, \"rev-parse\", \"HEAD^{tree}\")\n            commit_env = dict(os.environ)\n            commit_env.update({\n                \"GIT_AUTHOR_NAME\": \"T080 E2E\", \"GIT_AUTHOR_EMAIL\": \"t080@example.invalid\",\n                \"GIT_COMMITTER_NAME\": \"T080 E2E\", \"GIT_COMMITTER_EMAIL\": \"t080@example.invalid\",\n            })\n            replacement = subprocess.run(\n                [\"git\", \"commit-tree\", tree], cwd=submodule, input=\"same tree\\n\",\n                check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,\n                env=commit_env,\n            ).stdout.strip()\n            _run_git(submodule, \"checkout\", \"-q\", replacement)\n        else:\n            (root / \"rr80-known.txt\").write_text(\n                \"ycsb_\" + \"rratio=8\" + \"0\\n\"\n                + \"ycsb_\" + \"zipf_skew=0\" + \".9\\n\"\n                + \"ycsb_\" + \"rmw=\" + \"0\\n\",\n                encoding=\"utf-8\",\n            )\n        result = migration.verify_receipt(root=root)\n>       assert result.state == \"invalid\"\nE       AssertionError: assert 'active-valid' == 'invalid'\nE         \nE         - invalid\nE         + active-valid\n\norchestrator/tests/test_s8b_oracle_driver.py:507: AssertionError\n=========================== short test summary info ============================\nFAILED orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] - AssertionError: assert 'active-valid' == 'invalid'\n1 failed, 79 passed, 1 skipped in 185.42s (0:03:05)\n",
      "pytest_returncode": 1,
      "status": "KILLED",
      "timeout_seconds": null,
      "unexpected_red": []
    },
    {
      "actual_red": [
        "orchestrator/tests/test_s8b_oracle_report.py::test_post_r_null_is_protocol_violation_for_every_campaign_row",
        "orchestrator/tests/test_s8b_oracle_report.py::test_pre_r_null_and_object_mixture_is_protocol_violation"
      ],
      "command": [
        "python3",
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "orchestrator/tests/test_s8b_oracle_report.py"
      ],
      "elapsed_seconds": 3.0,
      "expected_reason": "bare null が現行 grammar 違反でなく historical absent と誤分類される",
      "expected_red": [
        "orchestrator/tests/test_s8b_oracle_report.py::test_post_r_null_is_protocol_violation_for_every_campaign_row",
        "orchestrator/tests/test_s8b_oracle_report.py::test_pre_r_null_and_object_mixture_is_protocol_violation"
      ],
      "file": "orchestrator/campaign/s8b_oracle_report.py",
      "id": "M14",
      "kind": "behavioral",
      "missing_expected_red": [],
      "output": "........................................................................ [ 47%]\n........................................................................ [ 94%]\n...F...F                                                                 [100%]\n=================================== FAILURES ===================================\n________ test_post_r_null_is_protocol_violation_for_every_campaign_row _________\n\ntmp_path = PosixPath('/dev/shm/pytest-of-tanab/pytest-1514/test_post_r_null_is_protocol_v0')\nmonkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7f99f1cc2170>\n\n    def test_post_r_null_is_protocol_violation_for_every_campaign_row(\n        tmp_path, monkeypatch,\n    ):\n        envelope = _t080_envelope()\n        _mock_t080_resolution(monkeypatch, \"active-valid\", envelope)\n        manifest = _manifest(tmp_path)\n        layout = campaign_layout(\"oracle-b0\", output_root=str(tmp_path)).ensure()\n        _campaign_start(layout, manifest, t080_observation=None)\n        _finish_campaign(layout, manifest)\n    \n        observations = report.build_observations(\n            manifest=manifest, output_root=tmp_path, repo_root=tmp_path / \"repo\",\n        )\n    \n>       assert {row[\"status\"] for row in observations[\"rows\"]} == {\"protocol_violation\"}\nE       AssertionError: assert {'completed'} == {'protocol_violation'}\nE         \nE         Extra items in the left set:\nE         'completed'\nE         Extra items in the right set:\nE         'protocol_violation'\nE         Use -v to get more diff\n\norchestrator/tests/test_s8b_oracle_report.py:2550: AssertionError\n___________ test_pre_r_null_and_object_mixture_is_protocol_violation ___________\n\ntmp_path = PosixPath('/dev/shm/pytest-of-tanab/pytest-1514/test_pre_r_null_and_object_mix0')\n\n    def test_pre_r_null_and_object_mixture_is_protocol_violation(tmp_path):\n        never_issued = {\"state\": \"never-issued\", \"validation_head\": \"0\" * 40}\n        manifest = _two_campaign_manifest(tmp_path)\n        by_campaign = {\n            \"oracle-b0\": (\"b0\", [manifest[\"schedule\"][\"rows\"][0]], never_issued),\n            \"oracle-b1\": (\"b1\", [manifest[\"schedule\"][\"rows\"][1]], None),\n        }\n        for campaign_id, (block_id, rows, value) in by_campaign.items():\n            layout = campaign_layout(campaign_id, output_root=str(tmp_path)).ensure()\n            _campaign_start(\n                layout, manifest, campaign_id, block_id=block_id,\n                t080_observation=value,\n            )\n            _finish_campaign_rows(layout, rows)\n    \n        observations = report.build_observations(\n            manifest=manifest, output_root=tmp_path, repo_root=tmp_path / \"repo\",\n        )\n    \n        assert observations[\"t080_freeze_migration_observation\"] is None\n>       assert [row[\"status\"] for row in observations[\"rows\"]] == [\n            \"completed\", \"protocol_violation\",\n        ]\nE       AssertionError: assert ['completed', 'completed'] == ['completed',...ol_violation']\nE         \nE         At index 1 diff: 'completed' != 'protocol_violation'\nE         Use -v to get more diff\n\norchestrator/tests/test_s8b_oracle_report.py:2659: AssertionError\n=========================== short test summary info ============================\nFAILED orchestrator/tests/test_s8b_oracle_report.py::test_post_r_null_is_protocol_violation_for_every_campaign_row - AssertionError: assert {'completed'} == {'protocol_violation'}\nFAILED orchestrator/tests/test_s8b_oracle_report.py::test_pre_r_null_and_object_mixture_is_protocol_violation - AssertionError: assert ['completed', 'completed'] == ['completed',...ol_vio...\n2 failed, 150 passed in 2.77s\n",
      "pytest_returncode": 1,
      "status": "KILLED",
      "timeout_seconds": null,
      "unexpected_red": []
    },
    {
      "actual_red": [
        "orchestrator/tests/test_t080_freeze_migration.py::test_live_scan_is_bound_to_frozen_expressions_match_convention_and_candidates_g1"
      ],
      "command": [
        "python3",
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "orchestrator/tests/test_t080_freeze_migration.py"
      ],
      "elapsed_seconds": 1.377,
      "expected_reason": "live report の expressions/match_convention/candidate drift が凍結記録値との照合を通過する",
      "expected_red": [
        "orchestrator/tests/test_t080_freeze_migration.py::test_live_scan_is_bound_to_frozen_expressions_match_convention_and_candidates_g1"
      ],
      "file": "orchestrator/campaign/t080_freeze_migration.py",
      "id": "M15",
      "kind": "behavioral",
      "missing_expected_red": [],
      "output": "............F.........................                                   [100%]\n=================================== FAILURES ===================================\n_ test_live_scan_is_bound_to_frozen_expressions_match_convention_and_candidates_g1 _\n\n    def test_live_scan_is_bound_to_frozen_expressions_match_convention_and_candidates_g1():\n        holdout = json.loads((_ROOT / migration.HOLDOUT_REL).read_text(encoding=\"utf-8\"))\n        report = {\n            \"match_convention\": holdout[\"match_convention\"],\n            \"holdouts\": {\n                name: {\n                    \"candidate_id\": entry[\"candidate_id\"],\n                    \"expressions\": copy.deepcopy(entry[\"unknownness_check\"][\"expressions\"]),\n                    \"conjunction_hits\": [],\n                }\n                for name, entry in holdout[\"holdouts\"].items()\n            },\n            \"positive_control\": {\"hit_count\": 1},\n        }\n        original = holdout_module.search_repository\n        current = copy.deepcopy(report)\n        try:\n            holdout_module.search_repository = lambda _root: copy.deepcopy(current)\n            migration._verify_holdout_live_scan(_ROOT, holdout)\n            mutations = (\n                lambda value: value.update(match_convention=\"drifted\"),\n                lambda value: value[\"holdouts\"].pop(\"rr20\"),\n                lambda value: value[\"holdouts\"][\"rr80\"].update(candidate_id=\"H2\"),\n                lambda value: value[\"holdouts\"][\"rr80\"][\"expressions\"].update(rratio=\"drifted\"),\n            )\n            for mutate in mutations:\n                current = copy.deepcopy(report)\n                mutate(current)\n>               _expect_reason(\n                    lambda: migration._verify_holdout_live_scan(_ROOT, holdout),\n                    \"holdout.unknownness_layer2\",\n                )\n\norchestrator/tests/test_t080_freeze_migration.py:466: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\ncall = <function test_live_scan_is_bound_to_frozen_expressions_match_convention_and_candidates_g1.<locals>.<lambda> at 0x7fb35a6c9630>\nreason = 'holdout.unknownness_layer2'\n\n    def _expect_reason(call, reason: str) -> migration.MigrationError:\n        try:\n            call()\n        except migration.MigrationError as exc:\n            assert exc.reason == reason, (exc.reason, reason, exc)\n            return exc\n>       raise AssertionError(f\"{reason} の拒否が発生しなかった\")\nE       AssertionError: holdout.unknownness_layer2 の拒否が発生しなかった\n\norchestrator/tests/test_t080_freeze_migration.py:129: AssertionError\n=========================== short test summary info ============================\nFAILED orchestrator/tests/test_t080_freeze_migration.py::test_live_scan_is_bound_to_frozen_expressions_match_convention_and_candidates_g1 - AssertionError: holdout.unknownness_layer2 の拒否が発生しなかった\n1 failed, 37 passed in 1.17s\n",
      "pytest_returncode": 1,
      "status": "KILLED",
      "timeout_seconds": null,
      "unexpected_red": []
    },
    {
      "actual_red": [
        "orchestrator/tests/test_s8b_oracle_report.py::test_post_r_missing_key_is_single_reason_and_makes_judge_indeterminate",
        "orchestrator/tests/test_s8b_oracle_report.py::test_pre_r_campaign_start_absent_or_null_is_allowed[historical-absent]"
      ],
      "command": [
        "python3",
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "orchestrator/tests/test_s8b_oracle_report.py"
      ],
      "elapsed_seconds": 2.993,
      "expected_reason": "T-080 key 欠落 campaign が protocol violation でなく historical absent と誤分類される",
      "expected_red": [
        "orchestrator/tests/test_s8b_oracle_report.py::test_post_r_missing_key_is_single_reason_and_makes_judge_indeterminate",
        "orchestrator/tests/test_s8b_oracle_report.py::test_pre_r_campaign_start_absent_or_null_is_allowed[historical-absent]"
      ],
      "file": "orchestrator/campaign/s8b_oracle_report.py",
      "id": "M16",
      "kind": "behavioral",
      "missing_expected_red": [],
      "output": "........................................................................ [ 47%]\n.......................................................................F [ 94%]\n.F......                                                                 [100%]\n=================================== FAILURES ===================================\n____ test_pre_r_campaign_start_absent_or_null_is_allowed[historical-absent] ____\n\ntmp_path = PosixPath('/dev/shm/pytest-of-tanab/pytest-1515/test_pre_r_campaign_start_abse0')\nt080_value = <object object at 0x7faee3676530>\n\n    @pytest.mark.parametrize(\n        \"t080_value\",\n        [\n            pytest.param(_T080_ABSENT, id=\"historical-absent\"),\n            pytest.param(\n                {\"state\": \"never-issued\", \"validation_head\": \"0\" * 40},\n                id=\"null\",\n            ),\n        ],\n    )\n    def test_pre_r_campaign_start_absent_or_null_is_allowed(tmp_path, t080_value):\n        manifest = _manifest(tmp_path)\n        layout = campaign_layout(\"oracle-b0\", output_root=str(tmp_path)).ensure()\n        _campaign_start(layout, manifest, t080_observation=t080_value)\n        _finish_campaign(layout, manifest)\n    \n        observations = report.build_observations(\n            manifest=manifest, output_root=tmp_path, repo_root=tmp_path / \"repo\",\n        )\n    \n        assert observations[\"t080_freeze_migration_observation\"] is None\n        if t080_value is _T080_ABSENT:\n>           assert {row[\"status\"] for row in observations[\"rows\"]} == {\"protocol_violation\"}\nE           AssertionError: assert {'completed'} == {'protocol_violation'}\nE             \nE             Extra items in the left set:\nE             'completed'\nE             Extra items in the right set:\nE             'protocol_violation'\nE             Use -v to get more diff\n\norchestrator/tests/test_s8b_oracle_report.py:2445: AssertionError\n____ test_post_r_missing_key_is_single_reason_and_makes_judge_indeterminate ____\n\ntmp_path = PosixPath('/dev/shm/pytest-of-tanab/pytest-1515/test_post_r_missing_key_is_sin0')\nmonkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7faee1eec220>\n\n    def test_post_r_missing_key_is_single_reason_and_makes_judge_indeterminate(\n        tmp_path, monkeypatch,\n    ):\n        envelope = _t080_envelope()\n        repo_root = tmp_path / \"temporary-repo\"\n        roots = _mock_t080_resolution(monkeypatch, \"active-valid\", envelope)\n        manifest = _manifest(tmp_path)\n        layout = campaign_layout(\"oracle-b0\", output_root=str(tmp_path)).ensure()\n        _campaign_start(layout, manifest, t080_observation=envelope)\n        _finish_campaign(layout, manifest)\n    \n        baseline = report.build_observations(\n            manifest=manifest, output_root=tmp_path, repo_root=repo_root,\n        )\n        assert baseline[\"t080_freeze_migration_observation\"] == envelope\n        assert judge.judge_oracle(baseline)[\"status\"] == \"determinate\"\n    \n        lines = Path(layout.wal_file).read_text(encoding=\"utf-8\").splitlines()\n        rewritten = []\n        for line in lines:\n            record = json.loads(line)\n            if record.get(\"payload\", {}).get(\"event\") == \"campaign-start\":\n                record[\"payload\"].pop(\"t080_freeze_migration_observation\")\n            rewritten.append(json.dumps(record, ensure_ascii=False, separators=(\",\", \":\")))\n        Path(layout.wal_file).write_text(\"\\n\".join(rewritten) + \"\\n\", encoding=\"utf-8\")\n    \n        damaged = report.build_observations(\n            manifest=manifest, output_root=tmp_path, repo_root=repo_root,\n        )\n        assert roots == [repo_root, repo_root, repo_root]\n        assert damaged[\"t080_freeze_migration_observation\"] is None\n>       assert {row[\"status\"] for row in damaged[\"rows\"]} == {\"protocol_violation\"}\nE       AssertionError: assert {'completed'} == {'protocol_violation'}\nE         \nE         Extra items in the left set:\nE         'completed'\nE         Extra items in the right set:\nE         'protocol_violation'\nE         Use -v to get more diff\n\norchestrator/tests/test_s8b_oracle_report.py:2492: AssertionError\n=========================== short test summary info ============================\nFAILED orchestrator/tests/test_s8b_oracle_report.py::test_pre_r_campaign_start_absent_or_null_is_allowed[historical-absent] - AssertionError: assert {'completed'} == {'protocol_violation'}\nFAILED orchestrator/tests/test_s8b_oracle_report.py::test_post_r_missing_key_is_single_reason_and_makes_judge_indeterminate - AssertionError: assert {'completed'} == {'protocol_violation'}\n2 failed, 150 passed in 2.77s\n",
      "pytest_returncode": 1,
      "status": "KILLED",
      "timeout_seconds": null,
      "unexpected_red": []
    }
  ],
  "schema_version": "t080-mutation-results/v1"
}

```

## §14 受入記録 (親環境)

- baseline (wave 開始 0e7b081): 2618 passed / 18 skipped / 0 failed、collected 2636
- U0 後 (64c13dc): 2647 passed / 18 skipped / 0 failed
- 統合後 (7b8e843): 2673 passed / 18 skipped / 0 failed、node 三点比較 = 消失 0 / 追加 55
- fix1 後 (1c1b342): 2691 passed / 18 skipped / 0 failed、base からの消失 0 (+73)
- fix2 後 (68661b9): **2697 passed / 18 skipped / 0 failed**、base からの消失 0 (+79)、collected 2715
- no-touch manifest 12 file: 全段階で git diff (0e7b081 起点) により無変更を機械確認
- check_docs / check_codex_agents: 全段階緑。task-run 台帳は pilot 凍結により start 拒否 (fail-closed 仕様、[T-012] 裁定どおり) のため本 wave は台帳なし
- 実装子の sandbox 全走は一貫して +8 skipped (submodule index.lock 制約) — 親環境の独立全走で毎回 18 skipped に収束することを確認 (偽赤/偽 skip の切り分け実績)
- plan v2 U5 の orchestrator/tests/README.md 追記は省略 (二重 runner 節が新テストの走らせ方を既に汎用に覆う — 逸脱として記録)
