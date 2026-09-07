# read-heavy acf840c8 系列の限定受理 (D1597 の形)

2026-09-07。wave `dev-wave-t1905-b10-readheavy-admit`、branch
`worktree-dev-wave-t1905-b10-readheavy-admit`、起点 local main `cf4273f5`。

## 何をしたか

B-10 の完走済み read-heavy 正式系列を、D1597 の形 —「その系列限りの有限な内容 digest 集合へ
exact に閉じた限定受理」— で集約に残した。先行例は balanced 45 セルの `e057af3bc`。
同じ形を read-heavy へ新しく書き下ろし、write-heavy と balanced の限定受理は 1 行も変えず、
任意 workload を受ける一般規則も作っていない (D1597 が明示的に却下している)。

## 対象系列の現物

| 項目 | 値 |
|---|---|
| campaign ID | `b10-backoff-shape-silo-read-heavy-formal-acf840c8` |
| job | `977647.nqsv` (2026-09-05 01:06 JST 投入) |
| record 件数 | 45 (内容 digest 45 件すべて相異) |
| execution host | 全 45 件 `bnode088` |
| analysis commit | 全 45 件 `2a338449bb2798b729c5bc2f9bfe76463a7fe347` |
| analysis code sha256 | `b15c35480f50e73a440be0a734e7247f9ca56f17df58d86a4cdb1752fb214dd9` |
| binding sha256 | `24d80d9a35122de1d6ecd8a7d0244c439434452e94418fa35d34a48169b9f483` |
| 45 digest の meta digest | `27195442abce632ffae7a7241abd3cd8e765fe63fb590a62a37d4166049400c8` |

meta digest は sorted した 45 digest を改行で連結し末尾にも改行を付けた ascii の sha256。

## なぜ今この変更単位で要るか (実測)

driver の現行 bytes の sha256 が、そのまま 45 record が記録する `analysis_code_sha256` である。
さらに campaign lock の `identity_preimage` は `preregistration_binding` を含む。したがって
**driver を編集して commit すると `ident.campaign_id()` が別 ID を返し、束縛照合も外れる。**
限定受理を同じ変更単位で書かなければ read-heavy 45 セルが集約から落ちる。

段 3 の敵対相談が正確に訂正した点: 「1 byte 編集した瞬間」ではない。未 commit の編集は
dirty 検査と HEAD blob 一致検査で先に拒否されるので、**valid に commit した変更**が条件である。
結論 (限定受理が要る) は変わらない。

## 形 (既存 2 系列との差)

- binding は **7 key** (`prereg_commit` / `prereg_blob_sha` / `spec_sha256` / `patch_sha256` /
  `formula_sha256` / `analysis_code_sha256` / `binding_sha256`)。campaign lock に記録された
  実 shape が 7 key であり、`analysis_commit` を含まない。write-heavy の限定受理は 8 key で
  `analysis_commit` を含むが、それは write-heavy 系列固有であり真似していない。
- `analysis_commit` は binding dict ではなく **record 単位の述語**で pin した。
- 変更前の read-heavy 経路 (`_validate_prior_block_records`) が持っていた `variant_id` の
  **二段検査** (型 + 12 桁小文字 hex) を落とさず移した。片方だけ移すと `None` が来たときに
  `PreflightError` でなく `TypeError` になり、挙動が後退する。
- 受理集合は狭くなる方向にしか動かない (campaign ID・`analysis_commit`・45 digest 集合が増える)。

## 恒真な保証として数えないもの (段 3・段 6 の敵対検証が指摘、親が採用)

- **validator 冒頭の campaign ID 比較は production の受理集合を狭めない。** 集約側が同じ定数を
  代入してそのまま渡すためである。実効の pin は集約側の定数による root 選択であり、
  validator 内の比較は独立の診断にすぎない。
- **record 自己 hash の再照合は二重である。** loader が先に同じ比較を行う。
- **`_require_exact_workload_cells` の呼出しは冗長である。** 件数 exact 45 + 登録済み
  `(block_id, index, point)` 対応 + 重複拒否を通った時点で key 集合は必ず一致する。
  balanced と形を揃えるため残したが、そこを狙う負例と変異は登録していない。
- **合成 fixture を使う正例の末尾 3 assert (件数 45・host 集合・variant 形式) は恒真である。**
  fixture 自身がその値を作っているためで、防壁の発火証拠には数えない。

## 本物の証拠に当てた正例

段 6 レビュー A が「正例が合成 fixture の digest を注入していて、production の既定集合が
introspection でしか検査されていない」と指摘した (real、must-fix)。親が現物を確かめたところ、
repo 内の凍結 provenance
`output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json`
の `records` は 135 件の**完全な record 本体**で、`workload == "read-heavy"` で exact 45 件になり、
production の `_sha256_json` で自己 hash を 45/45 再現した。そこで、この本物 45 件に対して

- production の `_legacy_record_content_digest` を素のまま当てて申告 digest を再現させ、
- 得た 45 digest 集合を production の既定定数 `LEGACY_READ_HEAVY_RECORD_SHA256S` そのものと
  exact 比較し、
- 本物 record の `workload` / `execution_host` / `analysis_commit` / `analysis_code_sha256` /
  `preregistration_binding` / `variant_id` を凍結定数と照合する

正例を足した。注入・stub・monkeypatch・期待値の後追い書換えは無い。

**限界 (主張しない):** repo 内では validator の**全経路**を本物の証拠に通すことはできない。
`submission_receipt` の実 bytes 照合が repo 外の file を要求するためである。

## ユーザー裁定へ返す 2 件 (実装しない)

1. **WAL 側が digest に縛られていない。** 45 record の内容は exact に固定されるが、同じ campaign の
   WAL にある `anomalies` / `certified` / `verdict` は digest の対象外で、report 経路も検査しない。
   件数と tag を保ったまま WAL だけ差し替えると、同じ性能判定を持つ report を発行できる。
   これは read-heavy 固有ではなく report 経路そのものの既存の性質であり、本変更が新たに作る穴では
   ない。閉じるには新しい gate が要り、今回の裁定が scope 外としている。
   **現存系列に anomaly は無い** — 現物 WAL は 90/90 が `anomalies=0` / `certified=true` /
   `verdict=serializable` だった。
2. **集約が現在 CLI から到達不能である。** 事前登録文書に erratum を当てた結果、発効版
   `77b33e37…` を指すと `prereg-blob` で止まり (現行文書の blob は `a76bb75d…`、発効版は
   `ea910de3…`)、現行 commit を指すと legacy binding が live prereg の commit / blob を使うため
   campaign lock の旧値と exact 比較で落ちる。**これは read-heavy 固有ではない** —
   balanced も write-heavy も `prereg_commit` / `prereg_blob_sha` を live prereg から取るので、
   3 workload とも同じ理由で止まる。閉じるには 3 系列すべての binding の形を変える必要があり、
   本 wave の不変条件 (既存 2 系列を 1 行も変えない) と衝突する。
   D1597 の射程 (限定受理は事前登録文書の identity をどこまで縛るか) の問題として返す。

**帰結として、本 wave の成果は「D1597 の形で read-heavy の限定受理を書いた」ことであって、
「CLI から集約を通して read-heavy を残せることを実走で示した」ことではない。**

## 変異

事前登録は実装前 (段 4)、訂正は fix 前 (段 6)。spec は本 dir の
`mutation-spec-probe.json` と `mutation-spec.json`、台帳は `mutation-ledger.json`。

### 事前登録と訂正

事前登録は実装前 (段 4) に 15 件 — 負例 14 + 過剰拒否の正例 1。受理集合を縮小する wave なので
`DW-M01` が過剰拒否の正例を要求する。段 6 のレビューを受けて走らせる前に 3 件を訂正した。

- **m07**: `"read-heavy"` → `"balanced"` の反転をやめ、workload 節の**削除**に変えた。
  反転は過少拒否と過剰拒否を同時に起こし、正例まで赤にして帰属が壊れる。
- **m09**: `ident.campaign_id(cfg)` へ戻す表記は `cfg` が存在せず `NameError` になる。
  `config_for(...)` を inline で組む 1 行置換に改めた。1 行に収めたのは driver の行数を保つためで、
  行数が変わると行番号 pin も併発して帰属が単独でなくなる。
- **m11**: 期待 node は AST 集合試験だけでは足りない。probe 実測で 6 node に確定した。

### probe (全件 SURVIVED 期待) で期待 node を実測した

`DW-M07` に従い、期待 node を憶測で書かず probe で集めた。baseline PASSED、15 件すべてが赤を出した。

**m08 は probe で帰属不成立が露見し、実効 gate へ再照準した。** `execution_host` の非空検査だけを
削ると、隣に残る型検査が負例 (`execution-host-missing` = キー欠落) を先に捕まえるため、
赤くなるのは行番号 pin の 3 node だけになる。行番号 pin は行数を変える変異すべてで発火する
冗長 gate なので、機構が効いた証拠に数えられない (`DW-M03`)。host 検査 2 行をまとめて削る形へ
再照準し、m08 単独 probe で semantic 負例が発火することを実測してから本走へ登録した。
初回 probe の結果は消さず `mutation-ledger-probe.json` に残す (`DW-M02`)。

### 本走

**baseline PASSED、15 / 15 KILLED、期待 node 集合と完全一致、MISMATCH 0・SURVIVED 0・TIMEOUT 0。**
spec `5bf7befd…`、repo head `ebce51e95`、runner は
`tools/run_tests.py orchestrator/tests/test_b10_backoff_shape_sweep.py orchestrator/tests/test_ccbench_spawn_sites.py -q -rf -p no:cacheprovider --force-dispatch`、
`--runner-mode dispatch`。

| ID | 変異 | 期待 node 数 | 帰属 |
|---|---|---|---|
| m01 | binding を 8 key 化 (`analysis_commit` を足す) | 5 | 正例 2 本 + 行番号 pin 3 |
| m02 | `analysis_commit` の pin を削る | 4 | semantic 負例 1 + 行番号 pin 3 |
| m03 | `variant_id` の正規表現検査を削る | 4 | semantic 負例 1 + 行番号 pin 3 |
| m04 | `variant_id` の型検査を削る | 4 | semantic 負例 1 + 行番号 pin 3 |
| m05 | digest 集合照合の呼出しを削る | 4 | frozen 集合負例 1 + 行番号 pin 3 |
| m06 | 既定集合を balanced のものにする | 1 | **単独** (行数不変) |
| m07 | workload 節を削る | 4 | semantic 負例 1 + 行番号 pin 3 |
| m08 | `execution_host` 検査 2 行を削る (再照準後) | 4 | semantic 負例 1 + 行番号 pin 3 |
| m09 | 集約の campaign ID を動的計算へ戻す | 1 | **単独** (行数不変) |
| m10 | 集約の binding を live へ戻す | 1 | **単独** (行数不変) |
| m11 | 集約の validator を汎用版へ戻す | 6 | AST 2 本 + 結合 1 本 + 行番号 pin 3 |
| m12 | 定数 `ANALYSIS_SHA256` の 1 文字 | 2 | **合成正例 + 本物 45 件の正例** (行数不変) |
| m13 | 45 digest のうち 1 件の 1 文字 | 2 | **合成正例 + 本物 45 件の正例** (行数不変) |
| m14 | campaign ID 比較を削る | 4 | campaign 負例 1 + 行番号 pin 3 |
| m15 | host に `bnode015` を要求させる (過剰拒否) | 4 | 合成正例 1 + 行番号 pin 3 |

**冗長 gate の申告.** driver の行数を変える変異は `test_ccbench_spawn_sites.py` の 3 node
(`test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink`、
`test_define_sink_cross_product_has_no_unreviewed_ungated_member`、
`test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`) も赤にする。
これは帰属の破れではなく冗長な gate であり、単独変異の証拠から外す。
**行数を変えない m06 / m09 / m10 / m12 / m13 の 5 件は、この冗長 gate を巻き込まずに単独で赤になった。**

m12 と m13 が fix で足した「本物 45 件の正例」を赤にしたことが、その正例が実際に効いている実測である。

## 一次資料

- 実装 commit: `23a99673e`
- 変異 probe spec commit: `23404bc3b`、probe 実測と本走 spec commit: `ebce51e95`
- 対象系列の現物: `izanagi-job-evidence/b10-backoff-shape/official-output/campaigns/b10-backoff-shape-silo-read-heavy-formal-acf840c8/`
- 先行例: `e057af3bc` (balanced 45 セル)、`output/insights/2026-09-05_t1905-b10-trial-cell/README.md`
- 正式走の判定: `output/insights/2026-09-05_t1905-b10-report/README.md`
- 裁定: D1597 (系列ごとに有限集合へ閉じる)、D95 (実装面は Codex author)
