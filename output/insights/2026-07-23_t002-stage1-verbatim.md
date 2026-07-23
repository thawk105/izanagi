# [T-002] P-A1(a) Stage 1 + P-C3 + T-006 — wave 逐語 (2026-07-23)

正本: D84、worklog 2026-07-23 (6)。code commit 0c2a573 + 34ce18b (基準 7b6d472)。
本ファイルは wave の brief・プラン・敵対相談・裁定・実装報告・レビュー・fix の逐語凍結である。
変異台帳 = 2026-07-23_t002-stage1-mutation-ledger.json (最終 run 3 が正本)。

---

# 親 brief (段 1)

# [T-002] wave brief — P-A1(a) Stage 1 + P-C3 ([T-006] 同梱)

## scope (承認済み: archive worklog 0721-0722 (2) 項6、実行順 D83 (1) の第 3 手)

1. **Stage 1 (D65 (6)):** 公式 report API を「検証済み manifest のみ受理」へ狭める。
   `build_observations` (orchestrator/campaign/s8b_oracle_report.py:1507) の受理 =
   {VerifiedManifest, LegacyManifest} exact。未検証 OfficialManifest の直接受理を廃止。
   CLI `main()` (同 :1613) は verify_manifest 必須化 (freeze 入力を追加)。
2. **P-C3 (D65 残存リスク):** 意味論 leaf を oracle manifest の generator pin へ入れる。
   `_GENERATOR_KEYS` (s8b_oracle_manifest.py:43) = {materializer, report, judge} に
   {outcome_stage_contract, artifacts} を追加 (source = s8b_outcome_stage_contract.py /
   s8b_oracle_artifacts.py)。
3. **[T-006] (D68 (8)(d)、F9 型):** 宣言済み・schedule row なし campaign の無言スキップ
   (report.py:1547-1548 `if grouped[campaign_id]:`) を fail-closed で可視化する。

## 前提の実測 (brief 前、基準 HEAD 7b6d472)

- 全走ベースライン **2842 passed / 18 skipped / 0 failed** (repo root、64s)。submodule init 済み。
- G1 生死確認 (実ファイル編集なし・API 直呼び): schema_version すら無い手組み dict に
  OfficialManifest marker を付けるだけで build_observations が受理。宣言済み `camp-ghost`
  (row なし) は observations に一切言及されず無言スキップ。→ 両欠陥は実在し、本 wave は
  受理集合を実際に変える (模擬でなく production API の実挙動)。
- pin 元列挙: FROZEN_MANIFEST 8 件に編集候補ファイルなし。凍結 JSON の generator pin は
  s8b_holdout_freeze.py / s1 系のみ。**generator hash pin**: oracle manifest は report.py 等の
  source SHA を pin するが、production emitter 未配線 (build_manifest の caller はテストのみ)・
  durable/凍結 oracle manifest 不在 → 編集・key 追加は凍結物を壊さない (D83 (6) から不変を再確認)。
- write-path 棚卸し: report の書込は observations JSON 1 種 (create-only) のみ。
- 波及範囲: generator_versions fixture は test_s8b_oracle_{manifest,report,driver}.py の 3 file。
  judge は manifest を受けない (observations のみ)。build_observations の production caller は
  report CLI main のみ。driver は verify_manifest/VerifiedManifest を既に使用 (:1099-1105)。

## 親の provisional 裁定 (攻撃対象 — 一件ずつ否認/採用を返せ。brief 自身の誤りも攻撃対象)

- **(P1)** 受理集合 = {VerifiedManifest, LegacyManifest} exact。VerifiedManifest からは
  .document/.sha256 を使う。legacy 受理の廃止は Stage 3 の裁定領域 — 本 wave で狭めない。
  manifest_kind="official" は verified 経由のみになる。
- **(P2)** CLI は `--freeze` を必須引数化し、load_verified_freeze (s8b_freeze_io) で read-once →
  verify_manifest(root=ROOT, freeze_document, freeze_sha256) を official 経路で必ず通す。
  legacy 分類 (load_official_manifest が LegacyManifest を返す) のみ verify を経ず受理 (Stage 0 維持)。
- **(P3)** P-C3 の追加は {outcome_stage_contract, artifacts} の 2 key のみ。wal.py 等へ広げない
  (族一般化は G3 — 独立 2 例の裁定があるのはこの 2 leaf のみ)。既存 3 key の意味不変。
- **(P4)** T-006 の可視化は fail-closed (無言スキップの継続だけは不可)。チャネル設計
  (manifest_issues → 全行 protocol_violation / campaign-level 観測) は codex 起草に委ねる。
  anti-masking: 既存 issue を消さない (D68 (4)/D83 (4) と同型)。
- **(P5)** 実装単位 = 一枚岩 1 単位。理由: _GENERATOR_KEYS exact-set 変更が 3 test file の
  fixture へ同時波及し、Stage 1 が report 本体+テストへ重なるため所有素集合に分割できない
  (分割検討の記録 = 本項)。
- **(P6)** 期待赤の集合 = 「fixture の 3-key 構成」由来のみ。それ以外の赤は回帰。
- **(P7)** SCHEMA_VERSION (8b-oracle-manifest/v1) は bump しない。v1 実文書は 0 件
  (emitter 未配線・durable 無し) — D79 (1) の「v1 の意味を確定」と同型。

## 不変条件

- FROZEN_MANIFEST 8 件の bytes 不変。official floor gate の無条件拒否集合・pilot 挙動不変。
- judge/verdict API 不変 (Stage 2 は scope 外)。driver の C2-9 共有 verify 経路の意味不変。
- 凍結成果物 (output/s1-freeze, output/s8b-freeze) は 1 byte も変えない。
- 規律 2/3: 検証を甘くする方向の変異は不採用。診断は構造化して保持 (anti-masking)。

## 成果物の形

- code + tests (codex 実装子は docs 編集・git commit 禁止)。統合 commit・変異 matrix 実測・
  受入全走・docs (D84・worklog・insights 逐語+変異台帳 JSON) は親。
- 変異事前登録は段 4 (裁定後) で確定。候補: 型 gate 緩和 / _GENERATOR_KEYS 縮退 /
  T-006 検査無効化 / CLI verify 呼び出し除去 — 各々単一理由性をコードで確認してから登録。


---

# codex プラン v1 (段 2)

# 実装プラン

## 0. P1〜P7 の裁定

| 項目 | 裁定 | 理由 |
|---|---|---|
| P1 | **OVERRIDE（一部）** | 受理集合 `{VerifiedManifest, LegacyManifest}` exact は採用する。ただし現行 `VerifiedManifest` は公開 dataclass constructor から自由に偽造でき、exact type gate だけでは「検証済みのみ」を満たさない。`verify_manifest()` だけが通常構築できる非公開 seal と、使用時の `document` canonical hash＝`.sha256` 照合を追加する。 |
| P2 | 採用 | `--freeze` を必須化し、official 分類時だけ `load_verified_freeze()` → `verify_manifest()` を通す。legacy は引数を構文上要求するが freeze を読まず、Stage 0 の受理意味を維持する。 |
| P3 | 採用 | 追加は `outcome_stage_contract` と `artifacts` の2 keyだけ。 |
| P4 | 採用 | top-level `manifest_issues` を構造化診断チャネルとし、同時に実在する全 schedule row を `protocol_violation` にする。row がゼロでも issue は残す。 |
| P5 | 採用 | 1実装単位。ただし下記の内部順序で段階的に緑へ戻す。 |
| P6 | **OVERRIDE** | 3-key fixtureだけではない。fixture更新後には report テスト内の未検証 OfficialManifest 100呼出し、CLI 4箇所、driver の direct report caller も赤になる。constructor を閉じる場合は driver の手組み `VerifiedManifest` 3箇所も赤になる。 |
| P7 | 採用 | `8b-oracle-manifest/v1` は据え置く。oracle manifest/observations の durable 実文書がなく、凍結物も変更しない。追加診断も observations v1 の additive field として扱う。 |

## 1. production code

### 1.1 VerifiedManifest の偽造防止と generator pin

[s8b_oracle_manifest.py:43](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_manifest.py:43)

- `_GENERATOR_KEYS` を exact 5-key にする。

  - `materializer`
  - `report`
  - `judge`
  - `outcome_stage_contract`
  - `artifacts`

- `_validate_generators()` の exact-set 条件は維持する。
- エラーを単なる「schema が不一致」から、決定的に整列した `missing=[...] / extra=[...]` を含む診断へ変える。これにより新2 keyのどちらが欠けたかを検査できる。
- 各 record の path/hash 検査は既存どおり共通ループへ通し、特例や fallback は作らない。

[s8b_oracle_manifest.py:50-69](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_manifest.py:50)

- `VerifiedManifest` は `.document` / `.sha256` の公開読取契約を維持する。
- public constructor による通常の手組みを拒否する。

  - module-private の identity seal を追加する。
  - dataclass は `init=False` とし、custom `__init__` が seal 不一致を `ManifestError("VerifiedManifest は verify_manifest の検証結果からのみ構築できる")` で拒否する。
  - `document` は `OfficialManifest` exact、`sha256` は lowercase 64桁であることも構築時に確認する。
  - Python 内部で `object.__new__` 等まで使う敵対 caller は信頼境界外と明記し、暗号学的 capability とは主張しない。

[s8b_oracle_manifest.py:733-821](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_manifest.py:733)

- `verify_manifest()` の全既存検査を通過した最後の return だけが private seal を渡して `VerifiedManifest` を作る。
- `.sha256` の算出方法、freeze read-once 引数、driver C2-9 の意味は変えない。

### 1.2 report API の受理集合

[s8b_oracle_report.py:32-38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:32)

- `s8b_freeze_io` を import する。
- `OfficialManifest` を report の verified official 入力として扱う import・型注釈を残さない。

[s8b_oracle_report.py:348-399](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:348)

- `_validate_manifest()` が返す `manifest_issues` を文字列列から private な構造化 recordへ変える。固定形は次の3 fieldとする。

  - `code: str`
  - `campaign_id: str | None`
  - `message: str`

- 既存 run-contract 診断はメッセージを変えず、以下の安定 code を付ける。

  - `run-contract-not-object`
  - `run-contract-reps-not-positive-int`
  - `run-contract-reps-not-approved`

- `_validate_manifest()` の canonical hash 再計算値は引き続き返す。legacy の identity と、verified document の使用時整合性検査に共用する。

[s8b_oracle_report.py:1190-1194](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1190) および [同:1285-1503](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1285)

- `_assess_campaign(..., manifest_issues: Sequence[_ManifestIssue], ...)` に型を変更する。
- row の `reason` には各 issue の `message` を渡し、既存の WAL/lifecycle/correctness-red 理由と `dict.fromkeys()` で合成する。
- manifest issue があっても `_assess_window()` を先に評価する既存順序を維持し、correctness-red や既存 WAL issueを消さない。

[s8b_oracle_report.py:1507-1594](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1507)

- シグネチャを次の意味へ変更する。

  - `manifest: s8b_oracle_manifest.VerifiedManifest | LegacyManifest`
  - exact type 以外は `OracleArtifactTypeError`
  - エラー文は「`build_observations は VerifiedManifest/LegacyManifest exact type のみ受理する`」

- gate直後に入力を分岐する。

  - `VerifiedManifest`: `document = manifest.document`、`manifest_kind = "official"`、identity は `manifest.sha256`
  - `LegacyManifest`: `document = manifest`、`manifest_kind = "legacy"`、identity は既存 canonical 再計算値

- verified 経路では `_validate_manifest(document)` が再計算した canonical hash と `.sha256` を比較する。不一致は `ReportError("VerifiedManifest.document の canonical SHA-256 が VerifiedManifest.sha256 と不一致")` とし、receipt/Git/output-root 読取りより前に拒否する。
- observations の `manifest_sha256` と campaign-start 照合には、比較通過後の `VerifiedManifest.sha256` を使用する。

### 1.3 T-006 の campaign-level 診断

[s8b_oracle_report.py:1534-1559](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1534)

- `grouped` 構築後、空の campaign ID を sorted で列挙する。
- 各空 campaign について以下を既存 `manifest_issues` へ**追加**する。代入で置換しない。

  - `code = "campaign-without-schedule-row"`
  - `campaign_id = 対象ID`
  - `message = "manifest に宣言された campaign_id に schedule row がない: '<id>'"`

- 実在 row を持つ全 campaign の `_assess_campaign()` に拡張済み issue 全体を渡す。そのため一件でも ghost があれば、全実在 row は `protocol_violation`、`bench_values=[]` になる。
- 空 campaign に synthetic schedule row は作らない。`rows` と `expected_cells` の schedule 全単射を壊さないためである。
- 全 campaign が rowless の場合も report を空 rowsで返し、top-level issueで欠陥を可視化する。judge は既存の空 `expected_cells` gateにより `indeterminate` となる。
- ghost が一件でもあれば report-level T-080 siblingは `None` にする。宣言 campaign の一部しか観測していない状態から全体観測を作らない。

[s8b_oracle_report.py:1586-1594](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1586)

- observations top-level に `manifest_issues` を常時出力する。正常時は `[]`。
- 各要素は上記 exact 3-field record。
- judge は変更しない。既存入力互換のため、この field の欠落を judge 側で新たに拒否しない。

### 1.4 CLI freeze 入力

[s8b_oracle_report.py:1603-1610](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1603)

- `report` subcommand に `--freeze PATH` を `required=True` で追加する。
- help は official manifest 検証用であることと、Stage 1 中は legacy でも構文上必須であることを明記する。

[s8b_oracle_report.py:1613-1623](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1613)

- `load_official_manifest(args.manifest)` で先に分類する。
- exact `OfficialManifest` の場合のみ以下を行う。

  1. `load_verified_freeze(args.freeze)` を一度だけ呼ぶ。
  2. `verify_manifest(args.manifest, root=ROOT, freeze_document=verified_freeze.document, freeze_sha256=verified_freeze.sha256)` を呼ぶ。
  3. 戻った同一 `VerifiedManifest` を `build_observations()` へ渡す。

- exact `LegacyManifest` は `load_verified_freeze()` と `verify_manifest()` の双方を呼ばず、そのまま reportへ渡す。したがって `--freeze` の path が legacy 経路で新しい拒否条件にはならない。
- `FreezeIOError` と `ManifestError` を既存の CLI error catch に明示追加する。全失敗は `error: ...`、return code 2、`--out` 未作成。
- 既存利用者は official/legacy を問わずコマンド行へ `--freeze` を追加する必要がある。これは意図した CLI 非互換である。

## 2. 既存テストの修正

### 2.1 report fixture を本当に verify する

[test_s8b_oracle_report.py:21-34](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_report.py:21)

- `s8b_freeze_io` を import する。

[test_s8b_oracle_report.py:178-207](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_report.py:178)

- `_manifest()` の generator recordsへ、実ファイルを指す次の2件を追加する。

  - `outcome_stage_contract` → `orchestrator/campaign/s8b_outcome_stage_contract.py`
  - `artifacts` → `orchestrator/campaign/s8b_oracle_artifacts.py`

- `_manifest()` に run-contract override seamを追加し、検証可能な manifestを組み立てる前に値を変えられるようにする。build後の manifest mutationで偽の VerifiedManifest を作らない。
- test専用 `_verify_for_report(tmp_path, manifest)` を追加する。

  - manifestを `tmp_path` に書く。
  - `_freeze()` が作った freezeを `load_verified_freeze()` で読む。
  - production `verify_manifest()` を実行する。
  - 戻り値をそのまま返す。

- test専用 `_build_observations()` は exact `OfficialManifest` を必ず上記 helperで実検証してから reportへ渡し、LegacyManifest はそのまま渡す。
- raw/exploration/unverified rejectionテストだけは helperを使わず production APIを直接呼ぶ。

この方針により、未検証 documentを単に `VerifiedManifest(...)` で包むようなテスト緩和は禁止する。

### 2.2 direct API 既存テストの影響列挙

現状、[test_s8b_oracle_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_report.py) の101テスト・105呼出しが `build_observations()` を直接使い、そのうち `manifest=manifest` が100呼出しある。以下を実検証 helperへ移す。

- `:543-647` — success、reps、非有限値、run-contract診断
- `:685-905` — session issuer/env/T-080 anti-masking
- `:932-992` — namespace/symlink/resolved-root
- `:1024-2206` — outcome truth table、receipt、binding、retry/lifecycle、correctness-red、excluded reason
- `:2225-2663` — expected cells、WAL framing、terminal、screen marker
- `:2666-2922` — campaign ownership、T-080複数 campaign 集約

個別に意味を変える既存テストは次のとおり。

- `:611-647` の不正 run-contract 2テストは、schema-less `LegacyManifest` に変更して Stage 0 の防御検査として維持する。
- `:452-459` の `_two_campaign_manifest()` は現行 full verifierでは不正な2-block documentなので、schema-less legacy fixtureとして明示する。
- `:1543-1589` の registry/required receipt テストは、build前 overrideで正しい `manifest_id` を持つ official manifestを生成し、実 verify を通す。
- `:1593-1616` の binding欠落/partialテストは legacy fixtureへ移す。未検証 officialを偽 wrapper化しない。
- `:666-670` は拒否対象へ `OfficialManifest` 自体を追加し、raw dict、exploration、未検証 official の全てを exact type errorで固定する。
- `:2209-2222` の「改竄後も未検証 OfficialManifest を reportへ渡す」テストは反転し、未検証 OfficialManifest の即時拒否を検査する。別テストで、実 verify 後に `.document` を変更した場合の sha不一致拒否を検査する。
- `:650-663`、`:673-682`、`:749-767` の既存 legacy positive/negative testsは受理を維持する。

### 2.3 CLI 既存テスト

[test_s8b_oracle_report.py:908-1009](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_report.py:908) および [同:2281-2303](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_report.py:2281)

- 3つの `report.main()` 呼出しすべてへ `--freeze` を追加する。
- exploration manifest拒否テストにも freezeを渡し、argparseの欠落エラーではなく exploration分類拒否を検査し続ける。
- output-root拒否テストは valid official manifest＋対応 freezeで verifyを通過させ、namespace理由だけで落ちるよう単一理由性を維持する。
- non-mapping WAL CLI positiveは actual verifyを通った後に observationsが生成されることを確認する。

### 2.4 manifest tests

[test_s8b_oracle_manifest.py:84-109](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_manifest.py:84) および [同:227-246](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_manifest.py:227)

- 通常 fixtureと binding負例内のインライン fixtureを両方5-key化する。後者を更新しないと intended binding errorより generator schema errorが先行する。
- `:264-284` の generator hashテストを新 leafにも適用する。
- `:185-197` の既存 actual verify positiveを、private-seal経由で作られたことの positive controlとして維持する。

### 2.5 driver tests

[test_s8b_oracle_driver.py:787-832](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:787)

- `generator_paths` を positional tuple＋`zip()` から exact key mappingへ変更する。5-key化後の黙示 truncationを防ぐ。
- default mappingは本物の5 source pathを使う。
- hermetic emitter root (`:3005-3015`) は実repoのcampaign sourceを含まないため、既存のfixture内 source bytesを明示的な5-key mappingへ割り当てる。実source pathの意味検査は通常rootのmanifest testsが担当する。

[test_s8b_oracle_driver.py:1025-1028](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1025)、[同:1099-1101](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1099)、[同:1642-1644](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1642)

- 手組み `VerifiedManifest(...)` 3箇所を廃止する。
- 対応 manifest pathとfreeze document/shaを使って actual `verify_manifest()` の戻り値を得る。subprocess fixtureにも実repo rootを明示する。

[test_s8b_oracle_driver.py:2064-2088](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:2064)

- retry後の report CLIへ `--freeze` を追加し、driver→verified reportの正規 positive controlとして維持する。

[test_s8b_oracle_driver.py:3178-3197](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:3178)

- `load_official_manifest()` の戻り値を直接 reportへ渡す経路を廃止する。
- emitter freezeを一度読み、`verify_manifest(root=fixture root, ...)` の戻り値を reportへ渡す。これは production callerの正規呼出し形を固定する統合 positive controlとなる。

## 3. 新規テスト

### Stage 1

- `test_build_observations_accepts_actual_verify_manifest_result`
- `test_build_observations_rejects_unverified_official_manifest`
- `test_build_observations_rejects_verified_document_hash_drift`
- `test_verified_manifest_public_constructor_is_rejected`
- `test_verified_manifest_subclass_and_raw_mapping_are_rejected`
- `test_cli_official_loads_freeze_once_and_calls_verify_manifest_once`
- `test_cli_verify_failure_returns_two_without_output`
- `test_cli_requires_freeze`
- `test_cli_legacy_skips_freeze_loader_and_manifest_verifier`
- legacy positive control: valid legacy入力が従来どおり `manifest_kind="legacy"` で observationsを生成する。

### T-006

- `test_declared_campaign_without_schedule_row_is_structured_and_taints_all_real_rows`

  - 実在 campaign＋ghost campaign
  - top-level issue exact一致
  - 全実在 rowが `protocol_violation`
  - bench値非公開

- `test_only_ghost_campaign_is_visible_without_synthetic_row`

  - `rows=[]`
  - `expected_cells=[]`
  - `manifest_issues` にghost ID
  - `judge_oracle()` は既存APIのまま `indeterminate`

- `test_ghost_campaign_extends_existing_manifest_issues`

  - run-contract issueとghost issueを同時注入
  - top-level両codeを保持
  - row reasonにも両方を保持

- `test_ghost_campaign_does_not_mask_definitive_correctness_red`

  - ghost global issueと既存 correctness-redの双方がreasonに残る。

- positive control: 全宣言 campaignにrowがあると `manifest_issues == []` で、既存 completed結果が不変。

### P-C3

- `test_generator_versions_accept_exact_five_semantic_sources`
- `test_generator_versions_reject_missing_outcome_stage_contract`
- `test_generator_versions_reject_missing_artifacts`
- `test_generator_versions_reject_extra_key`
- `test_generator_semantic_leaf_hash_mismatch_is_rejected_at_build_and_verify`
- positive controlで生成 documentの各新record pathと実byte SHAを独立に照合する。

## 4. 実装順

1. 3 test fileの generator fixtureを5-key化し、generator exact-set正負テストを追加する。
2. `_GENERATOR_KEYS` と generator schema診断を変更し、manifest targeted testsを緑にする。
3. `VerifiedManifest` constructor sealと使用時hash整合性テストを入れ、driverの手組み3箇所をactual verifyへ移す。
4. report test用 actual-verify helperを追加し、正常 official callerを一括移行する。
5. malformed manifest testsをlegacyまたはbuild前overrideへ分類し直す。偽 `VerifiedManifest` で緑化しない。
6. `build_observations()` の exact受理集合、unwrap、stored sha使用、hash drift拒否を実装する。
7. CLIへ `--freeze` と official/legacy分岐を実装し、report/driverのCLI testsを追随させる。
8. `_ManifestIssue`、ghost検出、全row taint、top-level `manifest_issues`、T-080 taintを実装する。
9. T-006のrow有り・row無し・anti-masking・positive controlを追加する。
10. 対象テスト、凍結不変検査、全走を順に実行する。docs、`output/`、commitには触れない。

## 5. 検証

実装子の対象検査:

```text
python3 -m pytest -q \
  orchestrator/tests/test_s8b_oracle_manifest.py \
  orchestrator/tests/test_s8b_oracle_report.py \
  orchestrator/tests/test_s8b_oracle_driver.py

python3 -m pytest -q orchestrator/tests/test_frozen_artifacts.py
python3 tools/check_codex_agents.py
python3 tools/check_docs.py
```

親統合で全走を実施し、基準 `2842 passed / 18 skipped / 0 failed` から新規テスト数だけ増え、既存失敗ゼロであることを確認する。`output/s1-freeze`、`output/s8b-freeze` と `FROZEN_MANIFEST` 8件は byte比較で不変を確認する。

## OPEN QUESTION

- **P1 blocker:** private constructor seal＋使用時hash照合を Stage 1 に含めるか、親裁定が必要。これを含めない場合、`VerifiedManifest(document=OfficialManifest(...), sha256=...)` を誰でも手組みできるため、成果を「検証済み manifest のみ受理」と呼ぶことはできず、「nominal VerifiedManifest markerのみ受理」へ主張を格下げする必要がある。

---

# 敵対相談 1 — 正しさ境界レンズ (段 3、NO-GO)

結論は **NO-GO**。Stage 1 の producer-side hardening として有益な部品はあるが、現プランは「検証済み」「official」「pin」を実際より強く表現し、legacy・freeze・downstream・campaign 集合に実効的な抜け道を残す。

## must

1. **must — `VerifiedManifest` の private seal は provenance ではなく、検証 authority も封じない。**

   現行 token は `document/sha256` しか保持せず、`verify_manifest()` は caller 指定の `root` と分離した `freeze_document/freeze_sha256` を受けます。[s8b_oracle_manifest.py:54](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_manifest.py:54) [s8b_oracle_manifest.py:733](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_manifest.py:733)  
   したがって seal を破らなくても、攻撃者 root＋自作 freeze で本物の `verify_manifest()` を呼べば正規 seal を得られます。さらに同一 Python プロセスの敵対 caller には module-private object、`object.__new__`、pickle 等は境界になりません。seal は事故防止にはなるが、D65 がいう runtime marker と同じく provenance 証明ではありません。[decisions.md:2451](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2451)

   修正は、公開 report API 自身が manifest path を受け、固定 production root＋承認済み freeze で検証すること。任意 root で作れる token を authority として受けてはいけません。

   **成果物影響:** 偽または別 root 由来の token が `manifest_kind="official"` を生成し、report の `manifest_sha256/expected_cells/rows`、judge の winner、certified 選択へ渡る oracle 値が任意内容へ変わる。

2. **must — legacy は Stage 1 の検証回避経路であり、`manifest_kind` は gate になっていない。**

   `schema_version` を削除、または official schema から `run_contract` を削除すれば loader は `LegacyManifest` を返します。[s8b_oracle_artifacts.py:131](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_artifacts.py:131) 直接 API なら任意 dict を `LegacyManifest(...)` で包むだけです。計画どおりなら freeze は読まれず、部分 validator だけで `OfficialObservations` に昇格します。

   judge は `manifest_kind` も `manifest_issues` も読まず、verdict ではその情報自体を落とします。[s8b_oracle_judge.py:122](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_judge.py:122) legacy 維持が必要なら、別 schema／別 namespace の診断成果物へ隔離するか、少なくとも judge/combined が機械的に拒否すべきです。単なるラベルでは足りません。

   **成果物影響:** schema/run_contract を落とした未検証 manifest が official observations と determinate oracle verdict を作れ、Stage 1 が拒否するはずの manifest が certified 選択の受理集合へ復帰する。

3. **must — `--freeze` は信頼根ではなく、任意の自己整合ペアを受理する。**

   `load_verified_freeze(path)` は期待 hash なしでは「渡された bytes 自身の hash」を計算するだけです。[s8b_freeze_io.py:41](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_freeze_io.py:41) `verify_manifest()` も、その caller 提供 hash が manifest 記載値と等しいことしか確認せず、`freeze_document` とその byte hash の対応を自身では証明しません。[s8b_oracle_manifest.py:757](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_manifest.py:757)

   よって自作 freeze＋その hash を記録した自作 manifest は通ります。これは「限界注記」で済むのは、その出力を official/certification chain が構造的に拒否する場合だけです。現状は `OfficialObservations` を出すため不可。report CLI も active `load_ratified_freeze()` に束縛し、指定 path の bytes がその active SHA と一致することを要求すべきです。なおこの loader は duplicate key も拒否しません。

   **成果物影響:** 自作 freeze により holdout/configuration、floor/budget、schedule 参照を差し替えられ、report の manifest SHA・expected cells・oracle median と combined verdict の結論が承認 freeze 使用時と異なる。

4. **must — Stage 1 は certified 境界を一切閉じず、現プランの保証表現は過大。**

   D65 自身が Stage 2 を observations→judge→combined の hash 再束縛として分離しています。[decisions.md:2468](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2468) 現在の observations/verdict loader は schema だけで公開 marker を作り、combined は `OfficialVerdict` marker を受けて opaque な `manifest_sha256` をコピーするだけです。[s8b_oracle_artifacts.py:37](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_artifacts.py:37) [s8b_verdict.py:556](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_verdict.py:556)

   Stage 1 が正直に言えるのは「改変されていない report CLI の official branch が、caller 指定 freeze と現 worktree に対する局所構造検査を実行する」までです。freeze 承認、WAL 真正性、保存済み observations/verdict の provenance、certified 選択は保証しません。この限定を docs と受入条件に明記し、Stage 2 前の成果物を certification に使えないよう機械的に隔離する必要があります。

   **成果物影響:** 手書き OfficialObservations/OfficialVerdict の受理集合は Stage 1 前後で不変なため、任意 `manifest_sha256` と oracle 値から combined status を作れ、certified 選択の実効受理集合は狭まらない。

5. **must — P-C3 は key 名を増やすだけで、指定 source を pin していない。**

   `_validate_generators()` は key 集合、root 内実在、自己申告 hash だけを検査し、key→期待 path の対応を検査しません。[s8b_oracle_manifest.py:351](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_manifest.py:351) `artifacts` を `CLAUDE.md` に、全5 keyを同一無関係ファイルに向けても hash が合えば通ります。したがって brief の「report.py 等を pin している」も verifier の保証としては偽です。

   `_GENERATOR_SOURCES = {key: exact-relative-path}` を authority とし、absolute path、cross-wire、同一ファイルへの alias を拒否する必要があります。新テストには「2つの正しい record を入れ替えても拒否」を含めるべきです。

   **成果物影響:** 実際の semantic leaf を変更しても無関係な安定ファイルを記録した manifest が受理され続け、manifest の generator 参照と report/judge の実行意味論が乖離する。

6. **must — T-006 は campaign 集合を検査せず、既に情報を失った `set/dict` の空要素だけを見る。**

   `_campaign_index()` は重複 campaign を `set` へ畳み、重複 block は上書きします。[s8b_oracle_report.py:402](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:402) また単一 campaign なら、未宣言 block の schedule rowも無条件にその campaignへ割り当てます。[s8b_oracle_report.py:432](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:432) したがって plan の `grouped[campaign_id] == []` では次を検出できません。

   - 同一 campaign/block の重複宣言
   - 複数 block→同一 campaign で、一方の block に row がない
   - 単一 campaign 下の未宣言 block row
   - `campaign_id` 直指定＋未知 block

   さらに `_assess_campaign()` の directory 欠落、WAL read error、terminal 不成立の早期 return は `manifest_issues` を合成しません。[s8b_oracle_report.py:1190](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1190) 正規化前に宣言の多重度と block↔campaign↔row 関係を検査し、最終 row 構築後に既存 `_force_protocol_violation()` で全 rowを後処理する必要があります。[s8b_oracle_report.py:280](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:280)

   **成果物影響:** 未宣言 block rowや重複宣言が issue なしの completed row／公開 bench 値になり得る一方、早期 return では ghost 理由が落ち、report status/reason と judge の determinate/winner が正しい fail-closed 結果から変わる。

7. **must — 変異候補の2件は現構造では単一理由の correctness kill にならない。**

   - 「CLI verify 呼出し除去」だけなら raw `OfficialManifest` は後段 exact type gate で拒否され、危険な受理ではなく出力不能になる。
   - `_GENERATOR_KEYS` を3 keyへ縮退するだけなら5-key正例が `extra` で落ち、旧3-key文書を危険に受理したことではなく availability failure で kill され得る。

   これは既発の F28 と同型です。[failures.md:343](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/failures.md:343) 前者は unsafe acceptance を作る変異へ再照準し、後者は baseline-rejected exact 3-key文書が mutation で受理される単一理由 fixtureを用意すべきです。

   **成果物影響:** mutation ledger が無効・過剰決定変異を `KILLED` と数え、kill 件数と「どの gate が受理集合を守ったか」の参照が虚偽になる。

## should

- **P-C3 の主張を「指定2 leafの pin」に限定する。** report の意味論は `wal`、`execution_guard`、`env_contract`、abort reason、experiment numbers、T-080、manifest verifier 等にも依存します。5 keyで transitive semantic closure を得たとは書けません。

- **P-C3 の CI 検査を persisted-artifact 型にする。** 同じ checkoutから動的に hashを作って直ちに検証する正例は恒真寄りです。root Aでmanifestを作り、root Bで leaf 1本だけ変更して旧manifestを検証し、拒否されることを確認すべきです。worktree byte差は意図した拒否であり、今回の5ファイルに submodule初期化状態は直接関係しません。

- **T-006 テストを legacy-only と明記する。** genuine VerifiedManifest は非空・単一block・campaign一対一を既に強制するため、ghost は到達不能です。mixed ghost、重複宣言、未知block、missing directory、WAL error、terminal早期return、detached row時のT-080 taintを別々に固定すべきです。

- **P5 の一枚岩理由は成立しない。** P-C3、Stage 1 authority、T-006 relational validation は別の受理述語です。共通fixtureを順に更新すれば直列3単位へ分割でき、変異帰属も明瞭になります。

- **P7 は条件付きでのみ採用。** repo内では実manifest/observations JSONは見つからず、pre-issuance確定という説明はあり得ます。ただし5-key exact化は additiveではなく、既存v1の受理集合を狭める変更です。「repo内0件」ではなく公式namespace・外部保管を含む発行台帳の0件確認を受入条件にしてください。

- **P6 の plan側 overrideは方向として正しいが、実測前に件数を固定しない。** helper移行前の赤を分類し、意図した型拒否・constructor拒否・CLI非互換と、本当の回帰を別集計にすべきです。

## nit

- `_GENERATOR_KEYS` は mutable `set` ではなく、期待 pathを値に持つ immutable mappingにする方が契約を直接表現できます。
- `argparse` の必須 `--freeze` 欠落は現在の `main()` 構造では return 2 ではなく `SystemExit(2)` です。テスト期待を明示してください。
- `VerifiedManifest` を残すなら、名前・docstringを「同一プロセス内の provenance capability」ではなく「局所構造検査結果・事故防止 token」へ格下げすべきです。

## P1〜P7 裁定

| 親項目 | 監査裁定 |
|---|---|
| P1 | **否認**。exact dispatch自体は可能だが、sealはauthorityを証明せず、legacyを同じofficial outputへ昇格させる。 |
| P2 | **否認**。read-once mechanicsは採用可。任意freezeとlegacy skipにより「verify必須」は成立しない。 |
| P3 | **否認**。2 keyというscope以前に、key→source pathが未束縛。修正後も「2 named leaves」に主張を限定する。 |
| P4 | **一部採用・現案否認**。構造化issue、synthetic rowなし、T-080 nullは採用。集合検査と全経路taintが不足。 |
| P5 | **否認**。fixture重複は不可分性の証明ではない。 |
| P6 | **親案を否認、codex overrideを採用**。ただし赤集合は実測分類し、変異の単一理由性を再設計する。 |
| P7 | **条件付き採用**。発行成果物0件を公式台帳まで確認できた場合のみ据え置き可。 |

**最終裁定: NO-GO。** 上記 must、特に legacy隔離、ratified freeze束縛、report内部の固定authority検証、generator key→path束縛、campaign関係の閉表化が入るまで着手不可です。

---

# 敵対相談 2 — 整合・実効性レンズ (段 3、NO-GO)

結論は **NO-GO**。Stage 1 の型ゲート自体は正しい方向だが、freeze の権威確認が欠落し、P-C3 は実質的な source pin になっておらず、T-006 は definitive red を `indeterminate` に弱める。

## must

1. **Stage 1 の CLI 検証経路が D65 より弱い**

   D65 の詳細条件は active ratified freeze の解決、`launch_validate()`、その同じ document/SHA を `verify_manifest()` へ渡すことを要求している。[D65 の詳細](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/insights/2026-07-20_wave2-adjudicated-package-loop.md:492)。プランの `load_verified_freeze()` は単なる read/hash/JSON parse で権威性を検証せず、duplicate key すら意図的に受理する。[loader](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_freeze_io.py:1)、[duplicate-key test](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_freeze_io.py:103)。任意の自己整合 freeze を渡せる設計は Stage 1 の過小実装である。

   放置すると: official の受理集合が「active ratified freeze に束縛された manifest」から「呼出者が渡した任意 freeze と自己整合する manifest」へ拡大し、`manifest_sha256` と certified 選択の根拠参照が変わる。

2. **module-private seal は direct API の偽造を止めない**

   通常の module global identity token は `module._SEAL` として取得できる。プランは `object.__new__` だけを信頼境界外としており、この通常属性アクセスを閉じていない。偽造者は任意の `OfficialManifest` とその canonical SHA を渡せば使用時 hash 照合も通る。seal を closure 内 capability にする、権威 freeze の証跡を型へ保持して API 境界で再検査する、または信頼境界を明示的に格下げする必要がある。

   放置すると: `build_observations()` の official 受理集合に `verify_manifest()` を一度も通っていない手組み document が残り、偽造 document の値が report と certified 選択へ流入する。

3. **legacy にも `--freeze` を必須化するのは未承認の受理縮退**

   `argparse(required=True)` は manifest 分類前に発火する。「legacy では読まない」は互換性維持にならない。Stage 1 は official 経路の必須検証であり、legacy 廃止・縮退は Stage 3 の裁定事項である。`--freeze` は parser 上 optional、Official 分類後のみ必須にすべきである。

   放置すると: 現在受理される `LegacyManifest` の CLI 呼出しから `--freeze` 無しの全コマンドが除外され、observations/report/台帳行が生成されず終了コード 2 へ変わる。

4. **5-key 化が key→source path を束縛していない**

   `_validate_generators()` は exact key set と「記載 path の bytes/hash」しか検査せず、key と正本 path の対応を検査しない。[validator](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_manifest.py:351)。現行実装では全 generator key を `CLAUDE.md` に向けても検査を通せる。`outcome_stage_contract` と `artifacts` を交換・別ファイルへ向ける負例が必要であり、hermetic fixture も canonical relative path を再現すべきである。

   放置すると: `generator_versions.artifacts.path` 等が無関係なファイルを指したまま受理され、その無関係 bytes から `manifest_id` が確定するため、意味論 leaf の変更が certified manifest の参照値へ反映されない。

5. **brief の T-006 生死確認は Stage 1 後の到達可能性を証明していない**

   full verifier は official manifest の campaign と schedule block の対応を検査するため、verified official に「宣言済みだが row ゼロ」は作れない。brief の schema-less dict＋`OfficialManifest` marker は Stage 1 型ゲートで先に拒否される。Stage 1 後に T-006 が生きるのは受理継続される `LegacyManifest` 経路だけなので、新規 ghost テストは型を明記して legacy で構成しなければならない。

   放置すると: Legacy の ghost campaign が依然無言で消えても、Official の型拒否を T-006 成功と說認し、report の実在 rows と certified 判定が ghost 無しの値を維持する。

6. **全 row の `protocol_violation` 化は definitive correctness-red を隠す**

   judge は row status が `completed` 以外なら先に unknown 理由を積み、definitive correctness-red 判定より前に `unknown` を返す。[judge `_cell()`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_judge.py:40)。したがって plan の「ghost があれば全 row を protocol_violation」は anti-masking と正面衝突する。red row の status を保持するか、judge の優先順位変更を別途裁定する必要がある。

   放置すると: 同じ correctness-red 証拠を持つ campaign の oracle verdict が `disqualified` から `indeterminate` へ変わり、certified 選択の拒否集合が狭まる。

7. **`_assess_campaign()` の early return に ghost issue が届かない**

   missing campaign directory、WAL read failure、terminal 不在などは `manifest_issues` を合成する位置より前に return する。[early-return 群](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1190)、[issue 合成位置](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1285)。型変更と引数追加だけでは「全実在 row に反映」を実装できない。全 return の修正か、評価後の中央 post-process が必要である。

   放置すると: missing-output 等の row は `status` と `reason` に ghost campaign を持たず、top-level report と row-level 台帳の欠陥参照が食い違う。

8. **T-080 無効化に非自明な受入テストがない**

   計画の T-006 テストは sibling の exact 値を検査していない。既定 fixture が元から sibling `None` なら、実装を丸ごと削っても緑になる。まず実在 campaign だけで非 `None` の sibling を生成し、同一 fixture に ghost を追加した時だけ `None` になる metamorphic test が必要である。

   放置すると: report-level T-080 sibling が観測済み campaign の部分集合だけから生成され、存在しないはずの sibling hash/value 参照が report に残る。

9. **既存 tamper test の反転で Legacy の独立 hash 再計算 coverage が消える**

   現行の「改竄後も embedded/self-reported hash を信用せず canonical hash を再計算する」テストを、未検証 Official の型拒否と Verified の drift 拒否だけへ置換している。[現行テスト](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_report.py:2209)。Legacy は Stage 1 後も受理するため、元テストを Legacy 化して残す必要がある。

   放置すると: Legacy 経路が attacker-controlled `manifest_sha256` を信用する回帰を検出できず、observations の `manifest_sha256`、campaign-start binding、受理 row 集合が偽の hash に変わり得る。

## should

- 構造化 `manifest_issues` は observations で終端し、judge は field と row reason の内容を無視し、verdict/combined には code と campaign ID が残らない。「構造化して保持」が observations 限定なのか最終 certified chain までなのかを明文化すべきである。後者なら judge 不変条件との再裁定が要る。

- P6 は checkpoint ごとの期待赤集合になっていない。手順 1 は production が3-keyのまま fixtureを5-key化し、手順4は report gateが未対応のまま約100 callerを `VerifiedManifest` 化する。`1+2`、`4+6` をそれぞれ原子的 checkpoint にまとめるべきである。

- caller 数の主要棚卸しは概ね正しい。実測は production caller 1、report test の direct call 105回/101 test、driver test の direct call 1、`main()` 直接呼出し4、手組み `VerifiedManifest` 3。ただし driver helper を間接利用する `test_s8b_binding_driftguards.py` が検証対象から抜けている。

- targeted suite には少なくとも `test_s8b_binding_driftguards.py`、`test_s8b_freeze_io.py`、active-ratified freeze 系、`test_s8b_oracle_judge.py` を追加すべきである。現在の3ファイルだけでは authority chain と最終判定反転を局所化できない。

- CLI テストは全て `main(argv)` の直接呼出しで、subprocess caller は現存しない。`--freeze` 欠落は通常の catch による return 2 ではなく `argparse` の `SystemExit(2)` になるため、計画の「全失敗 return code 2」は不正確。少なくとも1本は実 CLI subprocess で確認すべきである。

- living instruction の [.claude/commands/dev-wave.md](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/.claude/commands/dev-wave.md:50) に3-key exact set が残る。親の docs 対象へ追加すること。D83 の歴史記述は改変せず D84 から supersede する。

- P-C3 の「transitive source bundle」の境界が曖昧である。Stage 1 で新たに信頼する manifest/freeze admission codeを generator pin の外に置くなら、その除外理由と脅威境界を D84 に残すべきである。

## nit

- 「公式 report API は検証済みのみ受理」は、API 全体が `LegacyManifest` を引き続き受理するため過大な見出しである。「official-manifest branch は verified のみ」と書くべき。
- `_GENERATOR_KEYS` について durable fixture、凍結 JSON、固定 `manifest_id` 期待値は見つからなかった。この部分の brief 実測は妥当。
- report CLI を subprocess で呼ぶ既存 script/runbook/文書コマンド例は見つからなかった。壊れる既存 caller は上記4つの直接 `main()` 呼出しで尽きる。
- v1 据え置き自体は可能だが、D84 には manifest の exact-key 意味変更と observations の additive field/hash変更の両方を明記すべき。

## P1〜P7 裁定

| 項目 | 裁定 |
|---|---|
| P1 | **条件付き採用**。`{VerifiedManifest, LegacyManifest}` exact、使用時 hash 照合、constructor 閉鎖は Stage 1 内。だが提案された module-private seal では不十分。 |
| P2 | **否認**。active ratified freeze＋`launch_validate` が欠落し、legacy への無条件 `--freeze` 必須化は未承認。 |
| P3 | **否認**。2 key追加だけでは key→正本 path が束縛されず、P-C3 の実効性がない。 |
| P4 | **原則のみ採用、具体案は否認**。可視化と anti-masking は正しいが、全row taintが definitive red を隠し、early returnも未処理。 |
| P5 | **否認**。同じファイルを触ることは一枚岩である根拠にならない。generator contract、Stage 1 admission、T-006 を直列の独立 checkpoint に分けられる。 |
| P6 | **親案を否認**。Codex overrideも方向は改善したが、checkpoint別赤集合、間接 helper consumer、judge/authority testsが不足。 |
| P7 | **条件付き採用**。durable v1文書と固定hashがないため bump不要。ただしD84への意味変更記録が条件。 |

# 最終判定

**NO-GO**

解除条件は、active-ratified freeze 経路への修正、偽造可能 seal の再設計、legacy の条件付き CLI 要件化、generator key→path 束縛、correctness-red を保持する T-006 設計、Legacy tamper coverage と非自明な T-080/early-return テストの追加である。

---

# 親裁定 v2 (段 4)

# [T-002] 親裁定 v2 — プラン v1 + 相談 2 本 (両 NO-GO) の消化

所見裁定: 相談 1 must 7 件 = 採用 6 / 一部採用 1。相談 2 must 9 件 = 採用 7 / 反証採用 1 (M6) /
消滅 1 (M3、--freeze 廃止により)。以下が実装契約 (プラン v1 との差分)。

## R1. CLI は active ratified freeze へ束縛 (D65 承認本文の逐語実装。--freeze 引数は作らない)

- D65 承認本文: 「CLI は active ratified freeze を解決して launch_validate を通し、その同一
  freeze document/sha256 を verify_manifest へ渡す」。親 brief P2 (--freeze 任意パス) は承認の
  過小実装だった (F31 型) — 否認。
- official 分類時: `load_ratified_freeze(root)` → `launch_validate(ratified, root)` →
  `verify_manifest(manifest_path, root=root, freeze_document=lv.ratified.document,
  freeze_sha256=lv.ratified.sha256)` → 同一 VerifiedManifest を build_observations へ。
  driver の実走経路 (s8b_oracle_driver.py:1090-1140) と同一機構を再利用し、第二の解決器を作らない。
- legacy 分類時: 従来どおり直接受理 (freeze 解決を一切呼ばない)。CLI 引数要件は legacy で不変。
- root seam: `--repo-root` (default = repo ROOT)。テストは fixture root を渡す (driver テストの既存作法)。
- 失敗 (RatifiedFreezeError / launch_validate 拒否 / ManifestError / FreezeIOError) は rc=2・--out 未作成。

## R2. VerifiedManifest seal は closure 保持 + 使用時 hash 照合 + 正直な docstring

- seal token を module 属性に置かない (module._SEAL 読取りで迂回されるため closure 保持)。
  `init=False` + custom `__init__` で未 seal 構築を ManifestError 拒否。
- build_observations の verified 分岐で canonical hash 再計算 == .sha256 を照合 (post-verify の
  in-place 改変の遮断。seal と別レイヤ、両方入れる)。
- docstring: 「verify_manifest の構造検査通過 token。provenance 証明ではない。freeze の権威性は
  caller の責務であり、公式 CLI は active ratified 束縛で担う」。in-process の object.__new__ 等は
  信頼境界外と明記 (D68 (6) と同枠)。

## R3. legacy 受理は不変 (Stage 3 領域)。ただし coverage を消さない

- schema_version 剥がしによる legacy 降格経路は Stage 3 まで残る (D65 残存リスクに既記載の既知事実 —
  新規裁定パッケージにはしない)。D84 に正直に再掲する。
- 既存 tamper テストの反転で消える「legacy の独立 hash 再計算」coverage は legacy 型テストとして残す
  (C2-M9 採用)。judge への legacy 拒否・namespace 隔離は Stage 2/3 — 実装しない。

## R4. generator pin は key→canonical path 束縛まで実装 (これが「pin する」の意味)

- `_GENERATOR_SOURCES` (immutable mapping、5 entry: materializer→campaign/s1_direct_comparison.py,
  report→campaign/s8b_oracle_report.py, judge→campaign/s8b_oracle_judge.py,
  outcome_stage_contract→campaign/s8b_outcome_stage_contract.py, artifacts→campaign/s8b_oracle_artifacts.py。
  いずれも `orchestrator/` 前置の repo 相対 canonical path) を authority とし、
  `_validate_generators` は record.path == canonical path (文字列一致、絶対 path 拒否) を検査へ追加。
- 負例: 2 record の path 入替え / 無関係ファイル指定 / 絶対 path。非恒真テスト: root A で build →
  leaf 1 本だけ違う root B で verify → 拒否。
- 主張は「指定 5 leaf の pin」に限定 (transitive closure を謳わない)。

## R5. T-006 検出は宣言レベル (集合潰し前)

- mapping 形 campaign_ids: block ごとに row 有無を検査 (値重複 collapse に影響されない)。
  list 形: campaign id ごと。検出 = 「宣言済みだが schedule row ゼロ」(F9 本体)。
- 隣接する row 側 leniency (単一 campaign fallback の未宣言 block 吸収等) は legacy Stage 0 設計の
  既知の寛容 — 本 wave 対象外、D84 に明記 (C1-M6 の当該弾は理由付き不採用)。
- ghost issue の row への反映は **全 row 構築後の中央 post-process** (`_force_protocol_violation`
  再利用) で行い、_assess_campaign の early return 経路にも届かせる (C1-M6 末尾/C2-M7 採用)。

## R6. 全 row taint は維持 (C2-M6 は先例により反証)

- ghost issue は既存 manifest_issues チャネル (run-contract issue と同じ全域 taint) に合流。
  correctness-red は reason 文字列に無条件併記 (anti-masking、D68 (4))。
- verdict が disqualified でなく indeterminate へ倒れるのは既存の意図的先例
  (judge binary-mismatch コメント「disqualify でなく unknown に倒す — 壊れた計測から結論を採らない」、
  既存 run-contract issue の全域 taint も同挙動)。indeterminate は受理でなく拒否。judge 優先順位の
  変更は Stage 2 領域 — しない。D84 に反証理由を記録。

## R7. T-080

- ghost があれば report-level sibling は None (D83 の unavailable taint と同型)。campaign-level
  観測は保持。metamorphic test 必須: 同一 fixture で ghost なし → sibling 非 None、ghost 追加 → None。

## R8. 変異事前登録 (B-057、全て「受理集合の期待方向変化」で kill 判定。可用性 kill は不可)

- MUT-1 report.py: build_observations 型 gate へ OfficialManifest を再受理 → 未検証 official の
  API 受理拒否テストが赤 (受理集合拡大)。
- MUT-2 report.py CLI: official 分類分岐を「LegacyManifest に包んで verify 迂回」へ →
  manifest_id 破損 official + 正規 ratified root の CLI テスト (期待 rc=2・出力なし) が赤。
  (verify 呼び出し単純除去は API gate にマスクされ不成立 — C1-M7 採用による再照準)
- MUT-3 manifest.py: _GENERATOR_SOURCES から新 2 entry 削除 → 3-key 文書の拒否テストが赤。
- MUT-4 manifest.py: path 束縛検査の除去 → cross-wire 拒否テストが赤。
- MUT-5 manifest.py: seal 検査の除去 → 公開 constructor 拒否テストが赤。
- MUT-6 report.py: 使用時 hash 照合の除去 → post-verify document 改変拒否テストが赤。
- MUT-7 report.py: ghost 検出の除去 → T-006 legacy ghost テストが赤。
- MUT-8 report.py: ghost→T-080 None guard の除去 → metamorphic テストが赤。
- anchor (old 逐語) は実装完了後の統合 commit で確定・再検証してから本走 (中間 commit 基準の spec は
  stale になる)。ハーネス: 単一走行 flock / 累積適用 + 一意性 assert / 復元は
  `read_text()==commit 済み内容` / 赤テスト名の機械記録 / SURVIVED は diff で注入実在確認。

## R9. 実装 = 直列 3 単位 (P5 一枚岩は両相談の否認を採用)

- 単位 A (P-C3): s8b_oracle_manifest.py の generator contract + 3 test file の fixture 5-key 化 +
  正負・非恒真テスト。production と fixture を同一単位で原子的に。
- 単位 B (Stage 1): seal + build_observations 受理集合 + CLI ratified 束縛 + report/driver テスト移行
  + 反転 + legacy coverage 維持 + subprocess CLI テスト 1 本。
- 単位 C (T-006): 宣言レベル ghost 検出 + 中央 post-process + T-080 guard + テスト群。
- 同一 impl worktree で A→B→C 直列 (所有ファイルが重なるため並列不可)。各単位末に対象スイート緑 +
  赤内訳 (意図した移行赤 / 回帰) の報告を義務付ける。

## R10-R13. その他

- 対象スイートへ test_s8b_binding_driftguards.py / test_s8b_freeze_io.py / test_s8b_oracle_judge.py /
  test_frozen_artifacts.py を追加 (C2-should 採用)。
- P6 v2: 最終状態の期待赤 = 0。中間赤は単位ごとに分類報告。
- P7 v2: bump なし。発行済み 0 件は output/ 全域 grep で機械確認済み (insights 引用のみ)。
  D84 に exact-key 意味変更 + observations additive field を記録。
- 正直な枠組み (C1-M4 採用): Stage 1 が閉じるのは「report official 分岐の構造検査必須化」まで。
  WAL 真正性・下流 (observations/verdict) の provenance・certified 境界は Stage 2、legacy 閉鎖は
  Stage 3。D84 と docstring に明記。


---

# 実装単位 A 完了報告 (P-C3)

実装完了です。commit は作成せず、docs/・output/ は未変更です。`SCHEMA_VERSION` は `8b-oracle-manifest/v1` のままです。

主な変更:

- `_GENERATOR_SOURCES` を immutable な 5-key mapping として追加し、key 集合をそこから導出。
- `_validate_generators` に以下を追加。
  - exact key set と決定的な `missing=[...] extra=[...]` 診断
  - key ごとの canonical path 文字列一致
  - 従来の root 内実在・実 byte SHA-256 検査は維持
- manifest/report/driver fixture を 5-key 化。
- driver の tuple＋`zip` を明示 mapping に変更。
- 欠落、extra、path 入替え、無関係ファイル、絶対 path、全 5 leaf の hash 不一致、root A→B の 1-byte 差分をテスト。

変更ファイルは [s8b_oracle_manifest.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/campaign/s8b_oracle_manifest.py:42) とテスト3ファイルのみです。

テスト結果:

- 指定された5ファイル一括: `305 passed, 1 skipped, 0 failed`（216.33秒）
- skip:
  - `test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2`
  - 初期化済み ccbench submodule と pinned toolchain がないための既定 skip
- 赤の内訳:
  - 意図した移行赤: 0
  - 回帰赤: 0
  - failed node: なし
- 追加検査:
  - `python3 tools/check_codex_agents.py`: OK
  - `python3 tools/check_docs.py`: 違反なし
  - `git diff --check`: 緑

所有外への静的波及:

- 強化した `_validate_generators` の直接 consumer は `build_manifest` と `verify_manifest`。
- `verify_manifest` の production caller は `s8b_oracle_driver.gate_check` と `s8b_oracle_driver.run_block`。従来の3-key manifest はここで拒否されます。
- `build_manifest` の repo 内 caller は現時点では指定したテスト fixture のみ。
- `generator_versions` を直接読む別 production consumer はありません。report API の `OfficialManifest` 受理面は変更していません。

---

# 実装単位 B 完了報告 (Stage 1)

実装完了しました。単位 A の既存差分を保持し、コード・テスト以外は変更していません。commit も作成していません。

主な変更:

- [s8b_oracle_manifest.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/campaign/s8b_oracle_manifest.py:64)
  - closure seal、公開 constructor 拒否、exact document/lowercase SHA-256 検査を実装。
  - `verify_manifest` の最終 return だけが sealed token を生成。
- [s8b_oracle_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/campaign/s8b_oracle_report.py:1509)
  - `VerifiedManifest` / `LegacyManifest` exact type のみに限定。
  - official の post-verify hash drift を外部読取り前に遮断。
  - CLI に `--repo-root` と active ratified → launch validation → verify 経路を追加。
  - legacy の検査順序・受理水準は維持。
- report 約100 call site、driver の手組み token 3箇所、CLI 経路を実 verifier/ratified fixture へ移行。
- official/legacy CLI、verify 失敗、hash drift、constructor seal、実 subprocess 等の新規テストを追加。

検証結果:

```text
指定7ファイル:
355 passed, 1 skipped, 0 failed in 236.15s
```

skip は `test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2`。初期化済み CCBench submodule と pinned GCC/CMake/nm が必要な既存の条件付き slow control です。

追加実行:

- report: `169 passed`
- driver: `81 passed, 1 skipped`
- `check_codex_agents.py`: OK
- `check_docs.py`: 違反なし
- `git diff --check`、対象ファイルの `py_compile`: OK

赤の内訳:

- 意図した移行赤: 0
- 回帰赤: 0
- sandbox/submodule 偽赤: 0
- failed node: なし

静的な所有外波及可能性:

- repository 外の Python caller が raw `OfficialManifest` を直接渡していれば、今後は `verify_manifest` の戻り値が必要です。
- official CLI は active ratified freeze と適合する Git root を必要とし、別 checkout では `--repo-root` の指定が必要です。
- report ソース自体が generator hash の対象なので、変更前に生成された official manifest は generator hash 不一致となり、再生成が必要になり得ます。
- judge・verdict・driver の共有 verify 意味、SCHEMA_VERSION、legacy の受理意味には変更なしです。
- repo-wide scanでは未移行の production direct callerは見つかりませんでした。docs・`output/` への変更もありません。

---

# 実装単位 C 完了報告 (T-006)

実装完了です。commit、docs、output、judge は変更していません。

主な変更:

- [`s8b_oracle_report.py`](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/campaign/s8b_oracle_report.py:358)
  - `manifest_issues` を `{code, campaign_id, message}` に構造化
  - run-contract 3 code を固定
  - mapping は block 単位、list/string は campaign 単位で ghost 検出
  - 全 row 完成後の中央 post-process で fail-closed taint
  - top-level `manifest_issues` を常時出力
  - ghost 時は report-level T-080 sibling を `None` 化
- [`test_s8b_oracle_report.py`](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/tests/test_s8b_oracle_report.py:3006)
  - 指定された legacy fixture 回帰テスト一式
  - campaign ID collapse 前の block 検出、list/raw string 形も追加固定

テスト結果:

- 指定された7ファイル: `365 passed, 1 skipped, 0 failed`（247.46秒）
- 焦点テスト: `5 passed`
- `check_codex_agents.py`: OK
- `check_docs.py`: 違反なし
- `git diff --check`: 問題なし

赤の内訳:

- 赤: 0
- 赤 node: なし
- sandbox 偽赤: なし
- skip: `test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2`。初期化済み CCBench と pinned toolchain が必要な既存環境依存テストです。

所有外への波及可能性:

- observations の top-level exact-key 閉表を持つ外部 consumer は、新しい `manifest_issues` field への追随が必要になり得ます。repo 内 judge は未知 field を拒否しません。
- ghost 時は既存 T-080 sibling が `None` になるため、その値を直接利用する外部 consumer に影響します。
- run-contract issue も中央適用されるため、directory 欠落・WAL read error・detached rowでも `protocol_violation` になります。
- LegacyManifest の raw string `campaign_ids` を単一 campaign 宣言として受理する範囲が広がりました。
- VerifiedManifest では ghost は構造上到達不能で、正常時は `manifest_issues == []`、completed 結果は不変です。

---

# 敵対レビュー 1 — 正しさ境界 (段 6、NO-GO)

## 所見

1. **must — verified 使用時 hash に明確なすり抜けがある。** [report.py:1591](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/campaign/s8b_oracle_report.py:1591) は legacy 用 `manifest_sha256()` を再利用するが、この関数は [manifest.py:146](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/campaign/s8b_oracle_manifest.py:146) でトップレベル `manifest_sha256` を除外する。一方、seal 時の `.sha256` は全 document hash である。verify 後に `verified.document["manifest_sha256"]="x"` を追加すると、全 canonical hash は変わるのに比較値は変わらず、build が通ることを実測した。既存 drift テストは nested field しか攻撃していない。

   影響: verifier の exact schema を破った post-verify OfficialManifest が受理集合へ入り、レポートの `manifest_sha256` が実際に使用した document を参照しなくなる。

2. **must — raw string `campaign_ids` の無承認受理拡大。** 親検出どおり [report.py:448](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/campaign/s8b_oracle_report.py:448) が新規受理し、非空 schedule なら単一-ID fallback で全 row を束縛できる。さらに [test_s8b_oracle_report.py:3093](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/tests/test_s8b_oracle_report.py:3093) がこの拡大を正として固定している。巻き添え修正対象はこのテスト1本。

   影響: 従来 `ReportError` だった legacy manifest が completed observations と determinate verdict を生成でき、certified 選択の入力集合が拡大する。

3. **must — ghost と terminal early return の組合せで correctness-red が消える。** [report.py:1326](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/campaign/s8b_oracle_report.py:1326) は terminal 不備時に window assessment より先に返る。その後の中央処理 [report.py:1672](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/campaign/s8b_oracle_report.py:1672) は status/reason しか更新しない。実測では、単独評価なら `outcome=correctness-red, legacy_verify=red` の完全な window が、terminal 欠落＋ghost では `outcome=None, legacy_verify=missing` になった。現テストは「red＋ghost」と「early-return＋ghost」を別々にしか試していない。

   影響: レポート行と試行台帳から実在した correctness-red 証拠・reason が消え、成果物が観測事実を誤記録する。

4. **must — legacy 独立 hash テストが別差分で恒真化している。** [test_s8b_oracle_report.py:2547](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/tests/test_s8b_oracle_report.py:2547) は official manifest で WAL を作った後、[helper:250](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/tests/test_s8b_oracle_report.py:250) で `schema_version` を剥がしてから report へ渡す。したがって対象の `allowed_excluded_reasons` 改変を hash から除外する mutant でも、schema 除去だけで manifest hash mismatch となりテストは緑のままになる。

   影響: legacy hash が改変 field を取り込まない回帰を見逃し、改竄された exclusion 許可集合を持つ行が受理され得る。

5. **must — MUT-3 の「受理集合方向 kill」が成立しない。** 契約は旧3-key文書の拒否テストを要求するが、[test_s8b_oracle_manifest.py:367](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/tests/test_s8b_oracle_manifest.py:367) は5-key fixtureから1 keyだけ除く4-key試験しかない。新2 entryを production から削除する mutant では、テスト本体へ入る前に5-key fixtureが「extra 2件」で拒否されるため、赤は3-key受理拡大ではなく5-key可用性縮退による。

   影響: 変異台帳は MUT-3 を誤って `KILLED` と記録し、outcome/artifacts の pin を欠く3-key manifest再受理を検証したという参照が偽になる。

6. **must — D84 と契約上の境界記録が欠落している。** 差分に docs はなく、現行 D83 は依然 `_GENERATOR_KEYS={materializer,report,judge}` と記録している [decisions.md:3558](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/docs/decisions.md:3558)。worklog も T-002 を未着手としている [worklog.md:528](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/docs/worklog.md:528)。5-key exact 化、`manifest_issues` additive field、Stage 2/3 残存境界、legacy 降格・row leniency の記録がない。

   影響: 正本台帳の generator 参照集合と task 状態が実成果物と食い違い、同じ observations/v1 を読む consumer が新旧どちらの exact-key 意味か判定できない。

7. **should — official CLI テストが「同一 ratified object」も第二 resolver 不在も固定していない。** [test_s8b_oracle_report.py:1104](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/tests/test_s8b_oracle_report.py:1104) は launch/verify の呼出回数しか確認しない。launch 結果を捨てて別 resolver から同値 bytes を渡しても緑になる。追加された subprocess 試験も legacy 経路だけである。

## 裏取り

- 指定7テストファイル: **365 passed / 1 skipped**
- `git diff --check`: clean
- 5ファイルすべて staged、unstaged/untracked なし
- exact型 gate、CLI production 鎖、P-C3 canonical path/root B、mapping/list ghost、T-080 metamorphic はコード上成立。
- seal は direct constructor/dataclasses.replace を拒否。closure introspectionやcrafted `deepcopy` では偽造可能だが、これは docstring が明示的に除外する in-process 偽造境界内なので所見化しない。

**裁定: NO-GO**

---

# 敵対レビュー 2 — 整合・退行 (段 6、NO-GO)

# 裁定: NO-GO

## must

1. R2 の使用時 hash 照合は閉じていない。[report.py:390](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/campaign/s8b_oracle_report.py:390) は、自己 hash field を除去する [manifest.py:146](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/campaign/s8b_oracle_manifest.py:146) を使う。verify 後に `verified.document["manifest_sha256"]` を注入しても `build_observations` は受理した。現テストは allowed-list しか変異しない。

   成果物影響: post-verify 改変済み文書が `manifest_kind=official`・改変前 `manifest_sha256` のまま受理集合へ入り、report/certified 経路の参照 identity が文書内容と乖離する。

2. 既知の raw string `campaign_ids` 受理拡大は実在し、依存テストもある。[report.py:448](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/campaign/s8b_oracle_report.py:448) が従来の `ReportError` を受理へ反転し、[test_s8b_oracle_report.py:3093](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/tests/test_s8b_oracle_report.py:3093) がその拡大を正として固定している。grep 上、この分岐を直接前提にする追加テストはこれ1件。

   成果物影響: 従来は report 未生成だった raw-string legacy manifest が observations を生成し、単一 campaign fallback で completed row・judge/certified 選択まで到達し得る。

3. manifest issue が二重反映される。[report.py:1354](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/campaign/s8b_oracle_report.py:1354) で通常評価へ入れた後、[report.py:1672](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/campaign/s8b_oracle_report.py:1672) で全件再適用している。helper は合成済み reason 全体しか dedup しない。ghost＋correctness-red で ghost 文言が2回出ることを再現したが、テストは包含だけを確認している。

   成果物影響: report/台帳の `rows[].reason` が `ghost; definitive-red; ghost` へ変わり、安定診断値と参照比較が壊れる。

4. 契約誤り: R6 の「既存 run-contract issue も全域 taint」という先例は HEAD 7b6d472 の実装事実と一致しない。基準 HEAD では campaign directory 欠落などが manifest issue 合流前に `campaign-incomplete` で return していた。新しい中央ループが ghost だけでなく既存 run-contract issue にも適用されるため、legacy 挙動まで変更した。matching-hash legacy・`reps=4`・directory 欠落で `campaign-incomplete` → `protocol_violation` を再現した。

   成果物影響: 既存 legacy report の `rows[].status` と `reason` が変更され、同じ WAL/manifest に対する report・台帳値が基準 HEAD と非互換になる。

5. legacy 移行した負例が別理由を混入させている。例えば WAL は official manifest で構築した後、呼出時だけ [test_s8b_oracle_report.py:771](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/tests/test_s8b_oracle_report.py:771) で schema を剥がすため canonical hash が変わる。同型は run-contract 2群、registry contract、required receipt、binding、CLI non-mapping の6群。required receipt テストでは `receipt_matches_contract=False` を無視する mutant でも、無関係な hash mismatch が status を赤にする。

   成果物影響: 正しく hash を合わせた legacy 入力で receipt/binding gate が退行してもテストが緑になり得て、completed row が judge/certified 受理集合へ戻る。

6. 反転した tamper テストは旧 coverage を保存していない。[test_s8b_oracle_report.py:2547](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/tests/test_s8b_oracle_report.py:2547) は schema 剥離自体で hash mismatch になる。allowed-list tamper を削除しても同じ `protocol_violation` を再現できた。embedded hash 不信の信号は偶然残るが、allowed-list を canonical hash に含める検査意図は失われた。

   成果物影響: allowed-list が hash 対象から脱落して tamper が受理されてもテストが緑となり、excluded-reason の受理集合と report identity が改変可能になる。

7. R8 の mutation detector 3本が「受理集合の方向変化」を検査していない。

   - MUT-1: 型 gate に `OfficialManifest` を加えるだけでは [legacy 専用初期化:1614](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/campaign/s8b_oracle_report.py:1614) を通らず、未束縛変数で落ちる。
   - MUT-3: [missing-key test:380](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/tests/test_s8b_oracle_manifest.py:380) は最初に5-key manifestを構築するため、production authority を3-keyへ変える mutant では fixture setup が「extra key」で赤になる。
   - MUT-6: [hash-drift test:703](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/tests/test_s8b_oracle_report.py:703) の未設定 `Mock` は hash gate 除去後に T-080 state 分類で落ちる。受理ではなく別診断による kill である。

   成果物影響: mutation 台帳が KILLED と記録しても、未検証 official、3-key manifest、post-verify tamper の受理集合・generator 参照退行を検出した証拠にならない。

8. 必須 D84 がなく、現行正本 D83 は実装と衝突している。[decisions.md:3559](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/docs/decisions.md:3559) は generator authority を3-keyと記す一方、実装は [5-key:44](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/campaign/s8b_oracle_manifest.py:44)。`manifest_issues` additive field、legacy downgrade、row leniency、Stage 1境界の記録もない。

   成果物影響: decision 正本に従う3-record manifest は実装の受理集合から外れ、official report/certified 選択を生成できず、台帳の参照 authority も誤ったままになる。

## should

- CLI 実装自体は active ratified → `launch_validate` → 同一 document/sha の verify、legacy skip、既定 root の順になっている。ただし真の subprocess テストは [legacy success 1本だけ](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/tests/test_s8b_oracle_report.py:1205)。official/ratified/launch/破損/argparse の stderr と出力非生成は in-process または未検査で、success test も同一 object/sha の受渡しを assert していない。

## nit

- [verify_manifest の docstring](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/campaign/s8b_oracle_manifest.py:816) が依然 `load_verified_freeze` を唯一の caller 像としており、公式 CLI の active-ratified 経路を反映していない。

## 実走・列挙結果

5ファイルの staged 差分全量を HEAD 7b6d472 基準で確認した。unstaged/untracked 差分はない。`build_observations`、`build_manifest`、直構築 `VerifiedManifest`、`load_official_manifest`、CLI caller を全列挙し、上記以外の取り残しは見つからなかった。`test_s8b_binding_driftguards.py` を含む指定7ファイルは **365 passed / 1 skipped**。したがって実装子の「対象7ファイル全緑」は再現したが、全 suite 緑の証拠ではなく、上記の意味的退行を検出していない。

最終裁定: **NO-GO**。

---

# fix 完了報告 (fix1)

実装完了です。指定 7 ファイルは **369 passed / 1 skipped / 0 failed** でした。

### 実走・赤内訳

- 指定の pytest 7 ファイル一括実走: 369 passed、赤 0
- skip 1: CCBench 初期化と pinned GCC/CMake/nm を要する既定の slow real-build control
- `check_codex_agents.py`: OK
- `check_docs.py`: 違反なし
- staged / unstaged とも `git diff --check`: OK

### 所見対応

| 所見 | 判定 | 対応 |
|---|---|---|
| FIX-1 | closed | verified document を全 canonical hash で照合。nested・top-level 注入・削除を実 verify→drift で固定 |
| FIX-2 | closed | raw string 分岐を削除し、指定の従来エラーへ復元 |
| FIX-3 | closed | 中央処理を ghost のみに限定。run-contract early-return は `7b6d472` の status/reason を復元。ghost 文言は1回のみ |
| FIX-4 | closed | 対象 legacy fixture を schema 剥離後の hash で WAL 作成。independent-hash は baseline 緑＋allowed-list tamper 単独赤 |
| FIX-5 | closed | 3-key generator の直接 build 負例、実 drift witness、CLI document identity/sha wrapper を追加 |
| FIX-6 | closed | active ratified CLI 経路を `verify_manifest` docstring に追記 |

FIX-3 の未評価 sentinel は基準 HEAD と同じ `outcome=None` / `legacy_verify="missing"` を維持しています。

### 所有外波及

なし。fix の unstaged 差分は [manifest.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/campaign/s8b_oracle_manifest.py:811)、[report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t002-impl/orchestrator/campaign/s8b_oracle_report.py:1581) と対応テスト2ファイルのみです。既存 staged 差分は保持し、docs・`output/`・judge・commit には触れていません。

---

# 焦点再レビュー (NO-GO、closed 4 / partial 2 / regressed 0)

# 裁定: NO-GO

## Must 所見

1. **must — FIX-5 は partial。MUT-1 の wrong-direction kill が commit 内では残存。**  
   [型拒否テスト](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_report.py:692>) は未変更。元の MUT-1 のように許可型へ `OfficialManifest` だけ追加すると、[legacy 専用初期化](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1607>)を通らず、未束縛 `schedule` を [直後に参照](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1610>)して `UnboundLocalError` になる。テストは赤になるが受理方向ではない。三箇所を同時変更する compound mutant なら方向化できるが、その修正は commit のコード・テストには存在しない。

   成果物影響: 現実装は拒否できているが、mutation ledger が未検証 official 再受理への防壁を実証したことにならず、将来の official observations 受理拡大を見逃し得る。

2. **must — FIX-4 は partial。6 群中 run-contract approved-leaf 群が単一 tamper になっていない。**  
   [当該テスト](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_report.py:766>) は `run_contract.reps=4` に加え、TPS も4件で生成する。宣言 tamper だけを5へ戻しても、[official reps=5 の件数検査](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1060>)で依然 `protocol_violation` になる。テストも理由の包含しか見ず、単一理由性を固定していない。

   成果物影響: hash mismatch による恒真化自体は消えたが、この負例を一原因の監査証拠として扱えず、row 診断の退行を誤認し得る。

## 対応表

| Fix | 判定 | 根拠 |
|---|---|---|
| FIX-1 | closed | verified 分岐は[全 document canonical hash](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1581>)を比較。nested・top-level 注入・削除を[実 verify 後 drift](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_report.py:699>)で固定している。 |
| FIX-2 | closed | raw string 分岐はなく、mapping/array 以外を拒否。[依存テストも拒否へ反転済み](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_report.py:3158>)。 |
| FIX-3 | closed | run-contract message は `_assess_campaign` に残し、early return は `global_issues` 合流前という `7b6d472` の順序を維持。中央処理は[ghost のみ](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1614>)で、重複回数もテスト済み。 |
| FIX-4 | partial | legacy hash 生成順は6群すべて修正。malformed run-contract、registry、required receipt、binding、CLI non-mapping と independent-hash は tamper 除去で緑へ戻る。approved-leaf 群だけ上記の二重欠陥が残る。 |
| FIX-5 | partial | MUT-3 の3-key直接 witness、MUT-6 の実 verify/drift、CLI の同一 object/sha は closed。MUT-1 は上記のまま。 |
| FIX-6 | closed | [docstring](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_manifest.py:814>)に active ratified → `launch_validate` →同一 document/sha 経路が反映された。 |

なお、[「中央で全 issue を再適用する」というコメント](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1344>)は実装と逆であり、**should**。現時点の成果物影響はないが、FIX-3 の退行を誘発する記述になっている。

fix による新たな受理集合拡大は見つからなかった。AST parse と `git diff --check` は通過。pytest は read-only 環境に利用可能な一時ディレクトリがなく実走できなかった。

---

# fix2 完了報告 (partial 2 + should 1 の残余)

実装完了しました。受理集合・judge・コード挙動は変更していません。

変更ファイル:

- [test_s8b_oracle_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_report.py:766)
  - 実測 TPS を5件に修正
  - 宣言不一致を唯一の理由として完全一致で固定
  - TPS／return code 件数理由の非包含を追加
- [s8b_oracle_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_report.py:1342)
  - ghost issue のみ中央適用する実装にコメントを整合

テスト結果:

- 対象単体: `1 passed`
- run-contract 周辺: `6 passed, 176 deselected`
- 指定完了スイート: `237 passed in 7.58s`
- 赤 node: **0件**
- `git diff --check`: 問題なし
- `check_codex_agents.py` / `check_docs.py`: 問題なし

差分は2ファイル、`11 insertions / 9 deletions`。commit、docs、`output/` の編集は行っていません。開始時からあった未追跡 handoff 1件と `output/insights` 2件はそのまま保持しています。
