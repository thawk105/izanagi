# [T-2125] 歴史閲覧を記録 policy で読めるようにした

- wave: `dev-wave-t2125-historical-policy-version`
- branch: `worktree-dev-wave-t2125-historical-policy-version`
- base: `d97c423bd` (local main、2026-09-16)
- 実装 commit: `2a785eeb5` (実装子)、`630666603` (段 6 fix 子)
- 取り込み: `4b6a623e2` (local main `2b53fabbf` を取り込み)

## 何を解いたか

`CampaignReadPurpose.HISTORICAL_RAW` の閲覧が、campaign lock に記録された build admission
policy と**現行 policy の一致**を要求していた。この照合は purpose 分岐より手前
(`orchestrator/campaign/artifact_admission.py` の `_inspect_campaign`) にあり、歴史閲覧でも
発火していたため、policy の版が上がるとその前に記録された v2 campaign は purpose を問わず
読めなくなっていた。

v2 かつ `HISTORICAL_RAW` のときだけ、記録された policy を別型の専用 decoder
(`build_admission.decode_historical_build_admission_policy` → `HistoricalBuildAdmissionPolicy`) で読み、
**照合先を 2 つだけ**記録側へ向ける。

| 比較 | 現行入口 | 歴史入口 |
|---|---|---|
| receipt の `policy_sha256` | 現行 policy の sha256 | **記録 policy の sha256** |
| stock class の source commit | `CURRENT_PIN` | **記録 `repo_stock_pin`** |
| generator 登録 | 現行 `GeneratorId` | **現行のまま** |
| review 登録 | 現行 `ReviewId` | **現行のまま** |
| coder authority | `_AUTHORITY_KIND` | **現行のまま** |

診断は `classification="historical-policy-version"` に出す。`admission_status` は既存の
`historical-not-reclassified` を再利用するので、`layer3_report.py` と
`autonomous_trial_completeness.py` の certifying 条件 (`== "admitted"`、`== "admitted-new-schema"`) を
**構造的に**満たさない。`layer3_schema.json` は classification enum に新値を足し、
`certifying_input=true` 側では従来 2 値に制限して相殺した。epoch は 1 byte も触っていない (D1365)。

`wal.py` の exact 型境界 (`type(admission_policy) is not BuildAdmissionPolicy`) は現行型のまま残し、
歴史専用の topology 入口を隣接追加して検査本体を共有した。`wal._replay` の第 2 の現行 policy 照合は
production の歴史経路から到達しないので変更していない (段 2 plan・段 3 レンズ B・親の独立実測が一致)。

## 名乗ってよい範囲 (これを超えて書いてはならない)

**「記録 policy と記録 receipt が内的に整合する」までである。**

- **記録された policy が当時実在した policy であることは保証しない。** lock と WAL の両方を
  書ける者には満たせる。段 3 レンズ A がこの限界を real 所見として出し、親が不変条件の文言を
  訂正した。形検査 (独立 key literal / schema literal) は malformed object を弾くだけである。
- **現行適合は `unknown` である** (`HistoricalCampaignView.current_verifier_conformance`、D1365)。
- **図・材料レポートが全部通るようになったとは言わない。**
  - `tools/plotting/plot_s1_9pair.py` の歴史 view 受理は epoch `E0` / `v1-authority-absent` を要求するので、
    有効な v2 authority (E1) は到達しない。**この図の回復を成果に数えない。**
  - `layer3_report.py` の `_read_campaign_lock` は通常 decoder を使うため、旧 grammar の lock は
    report 投影で止まる (主題は [T-2483])。
- 変わる consumer: `critic/digest.py` (p2_2 経路)、`critic/online_digest.py`、`p2_2_report.py`、
  `layer3_report.py` の admission 段、`b10_backoff_static_tail_formal.py` の exploration 読取、
  `replay.discover_*` の歴史 purpose 経路。
- 変わらない consumer: `s1_report.py` (policy admission を呼ばない)、
  `replay.load_landscape` (certified 固定)、`plot_s1_9pair.py` (上記)。

## DW-G04 を満たしていない (明記する)

`DW-G04` は「条件付き機能は発火条件を満たす既存 artifact path か計測 ID を brief に書ける
場合だけ実装する」と定める。**本 wave はこれを満たしていない。**

- 提示できる証拠は、**発火事象の計測 ID** `fb5e74a17` (2026-08-12、`CURRENT_PIN` が
  `d706650` → `511c953` へ前進。policy 照合の導入 `a21bf413e` = 2026-08-03 より後) と、
  **不一致条件を満たす既存 artifact 2 件**
  (`output/insights/2026-08-04_wave-a-campaign-transport-smoke/evidence/` 配下の lock 2 件、記録 `d706650`)
  までである。後者は WAL を持たないため、より手前の別理由で落ちる。
- **現に停止している材料レポートは 0 件である。** 外部 official root 3 つ
  (`b10-backoff-grid-t2266-formal`、`b10-backoff-grid-t2418-explore`、`izanagi-measurements`) の
  v2 lock 20 件は、policy preimage の 5 field (`schema` / `repo_stock_pin` / `coder_authority` /
  `generator_registry` / `review_registry`) すべてが現行と一致する (親の再実測)。
- 親の判断: `DW-G04` は親が自発的に足す条件付き機構を止める gate であり、本件は台帳 [T-2125] として
  ユーザーが名指しした本題である。**gate を満たしたとは書かず、満たしていない事実を記録した
  うえで実装し、`DW-G04` の趣旨は scope の切り詰め (照合先 5 → 2) で守った。**

## 段ごとの攻め筋と裁定

- **段 2 plan が親 brief を反証した。** 親は「編集面は 1 module」と書いたが、policy hash だけ直しても
  `build_admission.py` の stock class が `CURRENT_PIN` と照合するため旧 pin の campaign は落ちる。
- **段 3 レンズ A の中心所見 (real)**: 記録 policy を照合先にすると、外部の登録・authority との
  照合が自己申告の整合確認へ変わる。→ **照合先を 2 つに削り、registry と authority は現行のまま
  残すことで応答した。** 偽造 policy が架空 generator / authority を名乗っても現行の登録簿が拒否する。
- **段 3 レンズ B の致命所見 (real)**: `DW-G04` 未充足。→ 上記のとおり明記して実装。
- **段 6 レビュー 2 本は独立に同じ must-fix 1 件へ収束した (real)。** 新しい fixture が旧 pin を
  2 箇所しか差し替えず、共有 helper `orchestrator/tests/commit_receipt_support.py` が自分の名前空間の
  現行 pin で proof source を作っていた。import 時に作られる `_PROOF_BUILD_CONTEXT` も差し替えが要る
  (レビュー B が指摘)。fix 子が 12 行で閉じ、共有 helper 本体は無変更。
- **段 6 レビュー A は、R2 の遵守・現行入口の恒真化なし・構造検査の脱落なし・certified への
  昇格経路なし・既存テストの削除 0 行を AST 比較まで含めて確認した。**
- **段 6 レビュー B は、変異 M2 が単一理由性を満たさないと指摘した (real)。** → 次節。

## certified 側の防壁が多層であることの発見 (変異 M2 を外した理由)

段 4 で事前登録した M2 は「certified 側も記録 policy 入口へ向ける」だった。
**certified 分岐の現行 policy 一致検査を 1 行消しても、certified の受理集合は変わらない。**
receipt の `policy_sha256` 照合と `wal.py` の exact 型境界が独立に拒否するためである。
変わるのは診断文言だけであり、`DW-M03` は診断文字列だけの赤を kill に数えない。
`DW-M01` / F28 に従い、**M2 は登録から外した。**

これは弱点ではなく多層防御だが、**「この 1 行が certified を守っている」とは言えない**という
意味で、主張の射程を縮める事実である。

## 親の実測の訂正 (段 3 レンズが指摘)

- M4 の「今日は発火していない」は当初 `repo_stock_pin` だけを見ていた。**全 preimage 5 field で
  測り直し、外部 20 件すべてが現行と一致することを確認した。**
- 「版上げは 2 事象」は網羅的でない。正しくは「preimage の 5 field のどれが変わっても版は上がる」。
- 「編集面は 1 module」は成立しない (上記)。
- 「`admitted` だけで certified へ昇格する実経路がある」は立証過剰。`layer3_report.py` と
  `autonomous_trial_completeness.py` の certified 再 admission が残るため、
  **非認証 status を理由にこれらを不要と判断してはならない。**

## 実測

すべて `tools/run_tests.py` 経由で計算ノードへ自動 dispatch された走行。

| 走 | checkout | 結果 |
|---|---|---|
| 基準 `test_artifact_admission.py` | `d97c423bd` | 146 passed |
| 基準 `test_build_admission.py` + `test_layer3_report.py` + `test_layer3_admission_diagnosis.py` + `test_t671_source_binding.py` | `d97c423bd` | 634 passed |
| 実装取り込み直後 (未 commit) | 作業木 | 19 failed / 794 passed — **contract-loader-drift による偽赤** |
| 実装 commit 後 | `2a785eeb5` | 14 failed / 799 passed — 既存は全緑、赤は新テストのみ |
| `test_historical_policy_version_reads_recorded_v2` 単独 | `2a785eeb5` | 1 failed / 2 passed (`[pin]` だけ赤) |
| fix 取り込み後 3 file | 作業木 (fix 未 commit) | 484 passed |
| local main 取り込み後 7 file (consumer test 含む) | `4b6a623e2` | **1362 passed** |

**未 commit 偽赤の型。** 変更した `artifact_admission.py` / `build_admission.py` / `wal.py` は
enforcement source closure の member で、未 commit だと
`contract-loader-drift: disk bytes が HEAD blob と不一致` で落ちる。pin は path であって内容 hash では
ないので、commit したら消えた。

## 変異台帳

harness: `tools/mutation_harness.py --runner-mode dispatch --detached`、
runner argv: `python3 tools/run_tests.py orchestrator/tests/test_artifact_admission.py orchestrator/tests/test_build_admission.py orchestrator/tests/test_layer3_report.py -q -rf --force-dispatch`、
固定 HEAD `630666603`。

### 1 回目 (probe) — erratum

spec: `mutation-spec-probe.json` (sha256 `a4a9403898be50a73a4513a805d9f09acae2e01aac51997e255de84b45646811`)、
結果: `mutation-probe-out.json`。

**baseline PASSED (484 passed)・KILLED 1 (M9)・MISMATCH 7。** 7 本とも赤になったが、
登録した期待 node が狭すぎた。変異の効果が広く波及し、観測 node 数は
M1 = 157、M3 = 6、M4 = 6、M5 = 22、M6 = 18、M7 = 6、M8 = 10 だった。
**`DW-M08` の「確定できない場合に限り初回を probe と明記し erratum を残して再登録・再走する」に
従い、観測 node 集合をそのまま期待 node として再登録した。** 初回結果は消さずにここへ残す。

### 2 回目 (本走)

spec: `mutation-spec-final.json` (sha256 `d8978ab23ffc8d327816ed62d548634749f60c90dda28a6df62c34cd97fa6e0a`)、
結果: `mutation-final-out.json`。

**baseline PASSED・8/8 KILLED・MISMATCH 0・SURVIVED 0・期待 node 完全一致。**

| # | 変異 | 結果 | 期待 node 数 |
|---|---|---|---|
| M1 | 歴史 dispatch を常に現行一致入口へ向ける | KILLED | 157 |
| M3 | 記録 policy decoder の exact key 集合検査を削除 | KILLED | 6 |
| M4 | 記録 policy decoder の schema literal 一致を削除 | KILLED | 6 |
| M5 | 歴史 receipt 照合で記録 policy SHA でなく現行 SHA を使う | KILLED | 22 |
| M6 | 歴史 stock 比較先を `CURRENT_PIN` に戻す | KILLED | 18 |
| M7 | 現行入口の stock 比較値を receipt 自身の source commit にする (恒真化) | KILLED | 6 |
| M8 | decision の classification を従来値に戻す | KILLED | 10 |
| M9 | `layer3_schema.json` の certifying 側 classification 制限を削除 | KILLED | 1 |

M2 は上節の理由で登録していない。

### F358 の共通核と delta (KILLED が意味に基づくことの証拠)

M1〜M8 が変異させる `artifact_admission.py` / `build_admission.py` / `wal.py` は enforcement source
closure の member であり、**変異の意味と無関係に 1 byte 変わっただけで落ちる node** が存在する (F358)。
F358 の恒久対応に従い、閉包 member を変異させた 7 本 (M1・M3〜M8) の `failed_nodes` の交差を核として取り、
変異ごとに核を差し引いた delta を確認した。**M9 は `layer3_schema.json` (閉包外) なので核の対象外。**

**核 = 5 node、原因 = `contract-loader-drift`** (disk bytes が HEAD blob と不一致)。
いずれも実 checkout の live closure を capture する `test_layer3_report.py` の certifying 系である。

- `test_layer3_report.py::test_accepted_report_rejects_no_commit_campaign`
- `test_layer3_report.py::test_accepted_report_requires_e1_and_records_epoch`
- `test_layer3_report.py::test_certified_report_omits_current_verifier_conformance`
- `test_layer3_report.py::test_render_accepted_persists_certifying_report`
- `test_layer3_report.py::test_render_and_render_accepted_race_rejects_second_writer[render_accepted]`

| # | 全 node | 核 | delta | delta の中身 |
|---|---|---|---|---|
| M1 | 157 | 5 | **152** | 歴史閲覧を使う既存・新規テスト全般 |
| M3 | 6 | 5 | **1** | `test_historical_policy_shape_is_exact[extra-key 集合]` — 狙った node ちょうど |
| M4 | 6 | 5 | **1** | `test_historical_policy_shape_is_exact[schema-schema differs]` — 狙った node ちょうど |
| M5 | 22 | 5 | **17** | 旧 policy の歴史正例・構造検査・trigger 検査 |
| M6 | 18 | 5 | **13** | 旧 pin fixture を使う歴史正例・構造検査 |
| M7 | 6 | 5 | **1** | `test_receipt_rejects_invalid_current_comparison[current-stock-…]` — 狙った現行入口負例ちょうど |
| M8 | 10 | 5 | **5** | classification を検査する 5 node |
| M9 | 1 | — | 1 | `test_historical_policy_version_report_schema` |

**delta が空の変異は 0 本。8/8 KILLED は核を除いても成立する。** M3・M4・M7 は delta = 1 で、
その 1 node が唯一の killer であることの証拠になる (特に M7 は裁定 R3 の現行入口負例が
恒真化を捕まえることの直接の証拠)。

**親の手順漏れ (F358 再発、land 前に捕捉)。** 親は段 6 で「8/8 KILLED・期待 node 完全一致」と記録し、
核の差し引きを段 8 の自己改善で F358 を読み直すまで行わなかった。`DW-M08` の
「観測 node を期待 node として再登録」は核込みの集合を期待値にするので、**完全一致は核の有無を
否定しない。**

## 残余 (scope 外)

依頼は「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と定めている。
以下は**台帳の新規 T にせず**、ここに記録だけ残す。

1. registry からの member 削除・改名、`_AUTHORITY_KIND` / `POLICY_SCHEMA` literal の変更で
   歴史閲覧がまた塞がる (照合先を 2 つに削った代償。いずれも未実測の事象)。
2. `layer3_report.py` の通常 decoder による旧 grammar 拒否 (主題は既存の [T-2483])。
3. critic digest の出力に admission classification が届かない。
4. 記録 policy の真正性を検証する手段が無い (歴史閲覧の恒久的な限界)。
5. 「記録 policy に存在しなかった ID を通す」逆方向の誤り。受理を**狭める**追加検査であり、
   `DW-G05` により本 wave では足さない。

## 逐語

`verbatim/` に段 1 brief・実測・訂正、段 2 plan、段 3 レンズ 2 本、段 4 裁定、段 5 実装子報告、
段 6 赤の証拠・レビュー 2 本・fix 子報告、pin 閉包を置いた。

### 逐語の可逆最小正規化 (DW-S07)

`verbatim/s3-lensB.md` の 31 行目末尾に Markdown 改行用の ASCII 空白 2 個があり、
`git diff --check` に抵触したので除去した。可視文字は変えていない。

| 項目 | 値 |
|---|---|
| 原文 sha256 | `f7fd585c3c695e6d9d7667a5d80999740ee4da8c78ca561ae601d771169b23f3` |
| 原文 byte 数 | 18702 |
| 正規化後 sha256 | `8ad016179ac22b2014e8bf339f67d2658edea4fe70092feb5c829295b32abc0a` |
| 正規化後 byte 数 | 18700 |
| 変更 | 31 行目の行末 (`。` の直後) から U+0020 を 2 個除去 |
| 復元法 | 31 行目の行末に U+0020 を 2 個足す。原文は `/work/1/SFC/tanab/dev-wave-artifacts/t2125-historical-policy-version/s3-lensB.md` |
