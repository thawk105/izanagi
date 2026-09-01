## 総括

新規追加は `orchestrator/campaign/p3_b4_material_report.py` と `orchestrator/tests/test_p3_b4_material_report.py` の 2 file に閉じ、既存 file は一切変更しない。  
レポートは publication を再ロードし、既存 4 API を順に合成して、201 block・402 arm を JSON と Markdown へ完全射影する。  
最大の反論点は `floor` である。D1060 の現状では正当な値も出所 artifact も存在せず、CLI 数値引数は caller に判断値を注入させるため採らない。  
現時点の正規コマンドは `floor=None` を既存評価器へ渡し、正直に `floor_domain_error` を伴う `protocol_violation` を報告する。未記入を独自に「判定不能」へ変える案も採らない。

## 実装プラン

### 新規 `orchestrator/campaign/p3_b4_material_report.py`

想定構成は次のとおり。

- `:1-55` — module 契約、import、直接 CLI 起動用 package shim。

  - `layer3_report.py:42-44` と同じく、file 直起動時だけ repository root を `sys.path` へ加える。
  - `SCHEMA_VERSION = "p3-b4-material-report/v1"`、`GENERATOR_IDENTITY`、固定出力名 `report.json` / `report.md` を定義する。
  - narrative、勝者 headline、グラフ生成、certified-selection connection は置かない。

- `:56-105` — error と dataclass。

  - `B4MaterialReportError`
  - `B4MaterialReportInputs`
    - `publication: B4PrerunPublication`
    - `assembly: B4RawAnalysisAssembly`
    - `contract_binding: B4ContractBinding`
    - `analysis_result: B4AnalysisResult`
  - `B4MaterialReportDocument`
    - `json_value`
    - `json_bytes`
    - `markdown_bytes`
    - `json_sha256`
  - `B4MaterialReportWrite`
    - `report_json_path`
    - `report_md_path`
    - `report_json_sha256`

- `:106-160` — `_load_and_evaluate(publication_root)`。

  1. `load_b4_prerun_publication(str(publication_root))`
     - loader は registry・manifest・receipt の固定 3 file を読む (`p3_b4_prerun_issuer.py:1007-1049`)。
     - descriptor、issuer commitment、完全性を既存実装が再検証する (`:1056-1158`)。
  2. `assemble_b4_raw_analysis(publication=publication)`
     - `B4RawRecordRejection` は partial report にせず `B4MaterialReportError` にする。
     - assembler 自身が全 manifest 行を走査し、planned artifact 欠落を拒否する (`p3_b4_raw_record_producer.py:1894-1917`)。
     - source を現物から再導出し、記録済み bytes と一致させる (`:1928-1948`)。
  3. `build_contract_binding(...)`
     - manifest の exact regeneration を経て binding を作る既存経路を使う (`p3_b4_analysis_ledgers.py:1201-1232`)。
  4. `evaluate_b4_artifacts(...)`
     - registry / manifest は publication が保持する canonical bytes、raw と source は assembly の bytes を渡す。
     - `floor=None` を渡す。既存実装はこれを `FLOOR_DOMAIN_ERROR` にする (`p3_b4_analysis_path.py:349-353`)。
     - 独自の分析、status、勝敗、floor fallback は作らない。

- `:161-215` — exact wire 変換。

  - `_wire_value()` は dataclass、Enum、tuple、`Fraction` を決定論的 JSON 値へ変換する。
  - `Fraction` は `[numerator, denominator]` とし、float 化しない。
  - `_canonical_json_bytes()` は key sort、compact separator、UTF-8、末尾 LF とする。
  - producer の decimal lexeme は再 serialize せず、各 `source_artifact_bytes` を exact UTF-8 string として埋める。復元時に `.encode("utf-8")` すれば元 bytes と一致する。

- `:216-315` — `_project_rows(inputs)`。

  - assembly の順序どおり manifest row ごとに on、off の 2 行を生成する。assembler がこの順序を作る根拠は `p3_b4_raw_record_producer.py:1989-2035`。
  - 各行は次を持つ。

    - `row_ordinal`, `block_ordinal`, `attempt_id`, `block_id`
    - §7.1 の必須項目。取得不能値も key を省略せず、`{"availability":"absent","value":null}` とする。
    - `reference_snapshot_hash`、`reference_receipt_hash`、`precursor_hash` など、必須 11 項目以外の既存値も保持する。
    - `planned_attempt_artifact_path`
    - `source_artifact_sha256`
    - `source_artifact_utf8`。producer の source object 全体を byte-lossless に保持する。
    - `verdict_scope: "experiment"`。`evaluate_b4_artifacts` の verdict は arm 個別 verdict ではないため、捏造した arm verdict を作らず、実験全体の値を各行へ明示的に参照させる。

  - anomaly class は、同一 `attempt_id` の sealed registry 行が持つ `digest_red_classes` 全要素を順序どおり載せる (`p3_b4_analysis_ledgers.py:123-144`)。単一 class を恣意的に選ばない。
  - throughput の数値 lexeme は `source_artifact_utf8#/raw/throughput` に保持し、行の必須項目には `performance_value_present` のみを機械導出する。

- `:316-355` — `_assert_complete_projection(inputs, rows)`。

  - 期待側は `assembly.source_artifact_bytes` 全件の SHA-256 multiset。
  - 実出力側は各行の `source_artifact_utf8` を再 encode して得た SHA-256 multiset。
  - 件数 `2 * len(publication.manifest.rows) = 402`、multiset 完全一致、block/arm 順序、各 source の 1 回だけの出現を検査する。
  - producer source hash は既存分析経路も重複と順序を検査している (`p3_b4_analysis_path.py:174-196`)。本検査は report view での脱落・複製・書換えを防ぐ完全射影検査であり、新しい分析規則ではない。
  - registry、manifest、issuer receipt、assembled raw も exact UTF-8 と SHA-256 を report provenance に埋め、埋込み bytes と publication/assembly bytes の一致を検査する。

- `:356-405` — `_build_report_value(inputs, reproduction_argv)`。

  - `certification_scope` は次のように機械可読にする。

    - `certifying: false`
    - `closed_world: false`
    - 検査済み範囲は publication loader、source rederivation、analysis byte binding。
    - 未保証範囲は publication と raw producer の `non_guarantees`、floor 不在、certified-selection connection 不在。
    - `certified` という名前や昇格 validator は新設しない。

  - provenance:

    - publication root
    - registry / manifest / receipt の path、SHA-256、exact UTF-8
    - raw analysis SHA-256、exact UTF-8
    - issuer commitment SHA-256
    - issuer と producer の non-guarantees
    - argv 配列の再現コマンド
    - `floor = {"availability":"absent","value":null,"source":null,"reason":"preregistration_section_5_unfilled"}`

  - analysis は `B4AnalysisResult` を全 field 射影する。4 verdict は `p3_b4_analysis_contract.py:85-91` の wire 値を変更しない。

- `:406-455` — `_render_markdown(report, json_sha256)`。

  - report JSON hash、provenance、認証水準、floor 不在、分析結果を先頭に置く。
  - 402 行すべての表を出す。勝った arm だけの headline は作らない。
  - unavailable は人間可読側で「不在」と表示し、null と「値 0」を混同しない。
  - `indeterminate` は「判定不能」とだけ表示し、「還流に価値なし」へ言い換えない。
  - report JSON の SHA-256 を Markdown に刻み、完全な機械可読射影の所在を明示する。
  - 比較図は生成しないため、材料レポート規約の `.dat/.plt/.png` 3 点セットは発生しない。グラフを追加する場合だけ同規約を適用する。

- `:456-525` — output path と writer。

  - `_resolve_output_root(publication_root, output_root)`:
    - 省略時は `<publication_root>/reports`。
    - 指定時は `--output-root PATH` をそのまま使う。
  - `_assert_output_disjoint_from_campaigns()`:
    - source に記録された WAL path (`p3_b4_raw_record_producer.py:1386-1393`) から arm campaign root を得る。
    - output root がいずれかの arm campaign root 自身または配下なら、書込み前に拒否する。
    - arm campaign layout の形は producer が `.../output/exploration/campaigns/<id>` と検査している (`:997-1011`)。
  - 全入力読取、評価、JSON/Markdown bytes の構築、完全射影検査を終えてから出力 directory を作る。
  - 2 file とも同一 directory の一時 file に全 bytes を書き、各 file を 1 回 `fsync` してから no-overwrite の hard link で公開する。
  - 2 本目の公開が失敗した場合は、この呼出しが公開した 1 本目だけを回収する。既存 file は上書きしない。
  - regular file の `fsync` は report.json と report.md の計 2 file だけ。

- `:526-575` — `main(argv)`。

  正規起動形:

  ```text
  python3 orchestrator/campaign/p3_b4_material_report.py PUBLICATION_ROOT [--output-root PATH]
  ```

  `layer3_report.py:786-808` と揃える点:

  - `main(argv: Optional[Sequence[str]]) -> int`
  - argparse
  - 空の path 引数拒否
  - domain error を `parser.error()` へ変換
  - `if __name__ == "__main__": raise SystemExit(main())`
  - 出力上書き禁止

  変える点:

  - 入力は campaign dir でなく publication root。
  - JSON と Markdown が一組なので `out_json` positional ではなく `--output-root`。
  - `--generated-from-head` は設けない。
  - `--floor`、`--floor-source` は設けない。
  - qsub、正式実走、性能測定、build への入口は一切持たない。
  - hook の sanctioned path allowlist には登録しない。

### 新規 `orchestrator/tests/test_p3_b4_material_report.py`

想定 node は次のとおり。

1. `test_build_material_report_projects_201_blocks_402_arms_and_all_sources_once`

   - 201 block、402 arm、manifest/on/off 順序を pin。
   - source UTF-8 の round-trip、SHA-256 multiset、registry / manifest / receipt / raw bytes の完全射影を検査。
   - 全行に下表の 11 key が存在することを検査する。

2. `test_required_row_fields_preserve_missing_rejected_and_unavailable_values`

   - terminal absent と ABORT の canonical source 行を renderer へ与える。
   - missing、rejected、terminal reason null、明示的「不在」が filter も正規化もされないことを pin。
   - unit fixture であり、status や verdict の再計算はしない。

3. `test_four_verdicts_render_without_relabeling_indeterminate`

   - `established`、`not_established`、`indeterminate`、`protocol_violation` の 4 wire 値を parameterize。
   - Markdown 表示が一対一で、`indeterminate` を否定的結論へ変えないことを pin。

4. `test_floor_absence_runs_existing_evaluator_and_reports_floor_domain_error`

   - public build 経路を通す。
   - floor 欠落を独自の判定不能へせず、既存 evaluator の
     `verdict=protocol_violation` と `analysis_invalid.reasons=[floor_domain_error]` を pin。
   - `--floor` に相当する Python API 引数も存在しないことを pin。

5. `test_projection_bijection_rejects_dropped_duplicated_or_rewritten_arm_rows`

   - parameter id を `drop-one-arm`、`duplicate-one-arm`、`rewrite-source-utf8` とする。
   - `_project_rows` の返値を mutation し、その後に public document builder が必ず呼ぶ `_assert_complete_projection` を通す。
   - exception が出ることを確認するため、mutation が validator を迂回したまま緑になる構造にしない。

6. `test_input_artifact_projection_rejects_rewritten_registry_manifest_or_receipt`

   - report 埋込み bytes の 1 byte mutationを、実際の provenance 完全性検査へ渡す。
   - path/hash だけが元のままでも拒否されることを pin。

7. `test_output_root_inside_arm_campaign_is_rejected_before_any_report_write`

   - output root を source の arm campaign root 配下へ向ける。
   - 2 出力とも存在しないまま失敗することを確認し、campaign evidence の配置を摂動させない。

8. `test_cli_clean_subprocess_writes_json_and_markdown_without_overwrite`

   - `sys.executable` と module file の直接起動を clean subprocess で 1 回だけ実行。
   - default `<publication_root>/reports` の 2 file、exit code 0、JSON hash binding を確認。
   - 同じ argv の 2 回目は既存出力を上書きせず失敗することを確認する。

テスト fixture は既存 producer test の real seed + replica 方針 (`test_p3_b4_raw_record_producer.py:881-917`) を再利用する。real `invoke()` は seed の on/off 各 1 回、合計 **2 回だけ** (`:380-381`)。残り 200 block は production serializer/writer を使う byte replica で、`invoke()` は呼ばない。

fixture 作成と 201 producer artifact の耐久性は本 test の主張ではないため、setup 区間だけ `os.fsync` を no-op にする。実 fsync を払うのは clean subprocess が公開する report.json と report.md の **2 regular files**だけ。assembler の検証は再利用するが build・性能測定・qsub は無い。新規 test file 単独は保守的に **60 秒未満**、既存 B-4 関連 test と合わせても **2 分未満**を目標とし、5 分上限に十分収める。

### 既存 file

触らない。

- `p3_b4_analysis_path.py:67-73` の source closure 5 file
- `p3_b4_analysis_contract.py`
- `p3_b4_analysis_ledgers.py`
- `p3_b4_prerun_issuer.py`
- `p3_b4_raw_record_producer.py`
- `layer3_report.py`
- `docs/phase3-b4-reflux-ablation-preregistration.md`
- `__init__.py`、hook、schema、certified-selection 関連 file

## 事前登録 §7.1 の 11 項目 — 取得可否の表

ここでは複合の `model/prompt/projection hash` を 1 項目、`WAL path/hash` を path と hash に分け、11 行とする。

| 項目 | 取得可否 | report 行での形 | 根拠 file:line |
|---|---|---|---|
| 1. arm | 取れる | `arm: "on" / "off"` | producer が source identity に arm を出す (`p3_b4_raw_record_producer.py:1354-1362`)。assembler も on/off の固定順で射影する (`:1989-2014`) |
| 2. campaign id | 取れる | `campaign_id` | campaign lock と receipt から検査後、source identity へ出す (`:1055-1067`, `:1357-1362`) |
| 3. 初期 snapshot hash | 取れない | `{"availability":"absent","value":null}` | source の閉じた構成には identity、raw、receipt projection、evidence、issues、non-guarantees しかなく (`:1354-1434`)、`reference_snapshot_hash` は別概念として binding にある (`:1695-1705`)。これを「初期 snapshot」と改名しない |
| 4. model/prompt/projection hash | 複合項目としては取れない | `model_hash` は不在、補助的に `model_snapshot`、`prompt_sha256`、`projection_sha256` を載せる | producer は model hash が無く `model_snapshot` は非 hash と明記 (`:57-66`)。prompt/projection は取得可能 (`:1373-1379`) |
| 5. WAL path | 取れる | `wal_path` | source evidence の WAL descriptor (`:1386-1393`) |
| 6. WAL hash | 取れる | `wal_sha256` | 同上 (`:1386-1389`) |
| 7. 停止理由 | 取れる。ただし不在もある | `execution_disposition`、`terminal_stage`、`terminal_reason` を無加工で併記。null を「成功」へ補完しない | terminal absent/executed の区分 (`:1264-1292`)、ABORT reason (`:1307-1311`)、source raw (`:1363-1368`) |
| 8. 予算消費 | 取れない | `{"availability":"absent","value":null}` | source raw の exact key 集合は disposition、whiteboard、terminal、throughput、treatment、contamination、protocol のみ (`:1363-1372`, `:2000-2010`)。budget field は無い |
| 9. verdict | 取れる | `verdict_scope:"experiment"` と `analysis.verdict` を各行に参照 | `B4AnalysisResult` が 4 分類 verdict を持つ (`p3_b4_analysis_contract.py:206-218`)。分岐規則は `:692-752`。arm 個別 verdict は作らない |
| 10. anomaly class | ledger から取れる | `anomaly_class` は `digest_red_classes` の全要素。`source_scope:"scheduled_precursor"` を併記 | sealed scheduled row が closed enum の列を持つ (`p3_b4_analysis_ledgers.py:90-97`, `:123-144`)。attempt id の一意 binding は producer が検査 (`p3_b4_raw_record_producer.py:625-637`) |
| 11. 性能値の有無 | 取れる | `performance_value_present: raw.throughput is not null`。値の exact lexeme は `source_artifact_utf8` に残す | COMMIT の fitness を lexical token から得る (`:1320-1325`)、source raw へ保持 (`:1363-1369`)、assembly へそのまま射影 (`:2011-2024`) |

補助項目の `reference_snapshot_hash`、`reference_receipt_hash`、`precursor_hash` は削らず載せるが、「初期 snapshot hash」の代用品にはしない。

## 親 brief への反論

### (P1) 条件付きで賛成

`<publication_root>/reports` を既定にする方向には賛成する。publication loader は固定 3 leaf だけを読む (`p3_b4_prerun_issuer.py:1015-1033`)。planned attempt の完全性も directory 列挙ではなく attempt id と exact path の対応で検査される (`:335-403`)、assembler もその path 集合だけを全件確認する (`p3_b4_raw_record_producer.py:1902-1917`)。したがって reports directory は現行 publication の集合へ混入しない。

ただし publication root は任意の絶対 path を受理し、arm campaign root との非交差は issuer が保証していない。よって「既定位置だから常に安全」とは言えない。source WAL path から arm root を確定し、output root が campaign root 内なら書込み前に拒否する限定検査が必要である。

### (P2) 反対

親の「CLI 必須 floor 引数 + 出所記録」は採らない。

- 事前登録は floor を「§5 の凍結 artifact から読んだ値」と定義する (`docs/phase3-b4-reflux-ablation-preregistration.md:382-385`)。
- D1060 はその floor artifact が未成立で、校正 campaign が必要だと確定している (`verbatim/decisions-extract.md:227-251`)。
- CLI の `--floor 1/100` と自由記述の出所は、値も出所も caller の自己申告である。report に文字列を刻んでも正当性は増えず、「publication root だけを入力とし判断値を caller から受けない」という親 brief 自身の境界にも反する。
- 未記入を独自に「判定不能」へする案も既存契約に反する。既存 API は不在 floor を `floor_domain_error` (`p3_b4_analysis_path.py:349-353`)、その analysis invalid を `protocol_violation` とする (`p3_b4_analysis_contract.py:755-790`)。

従って現在は `None` を実際に評価器へ渡し、protocol violation をそのまま材料化する。将来、発効済み §5 artifact を publication から権威的に辿れる接続が実装された後にだけ、別 wave で loader を追加するべきである。

### (P3) 賛成

`python3 orchestrator/campaign/p3_b4_material_report.py ...` で十分である。既存 renderer も package shim と `main(argv)` の file 直起動形を持つ (`layer3_report.py:42-44`, `:786-808`)。本コマンドは qsub、build、性能測定、campaign 実行を起動しないため、計算ノード投入器の exact path allowlist へ追加しない。hook、launcher、producer は変更しない。

### (P4) 賛成。ただし取得可能性を細分化する

全必須 key を各行に置き、不明な key を落とさず明示的「不在」にする方針に賛成する。ただし「model/prompt hash は取れない」と一括してはいけない。取れないのは model hash であり、`model_snapshot`、prompt SHA-256、projection SHA-256 は producer が保持している。初期 snapshot hash と予算消費も不在である。一方 anomaly class は sealed registry の `digest_red_classes` から取れるが、producer の campaign evidence が独立再導出した class とは主張しない。

## 見落としと未解決

- D1060 が解消されるまで、正式な成立・不成立・判定不能 verdict を得られる report は作れない。現行 report の substantive な結論は floor 欠落による protocol violation である。
- issuer 自身が file-drawer risk の end-to-end 閉鎖を否定している (`p3_b4_prerun_issuer.py:52-64`)。report generator がこれを解消したとは書かない。
- model hash、初期 snapshot hash、予算消費は現行 artifact に無い。report wave で producer や ledger を増補しない。
- anomaly class は registry 由来であり、arm campaign の現物から詳細 class を再導出した証拠ではない。この source scope を report に明記する。
- certified-selection connection、昇格 validator、一般化した official-root admission は本 wave に含めない。
- read-only sandbox のため test は実走していない。上記は静的検査に基づくプランであり、緑とは報告しない。