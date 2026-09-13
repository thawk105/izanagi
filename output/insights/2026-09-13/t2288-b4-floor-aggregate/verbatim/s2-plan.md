## 追補の位置と条項

**追補は現行237行の直後、238行の `- **校正済み PerfConfig**` の直前に置く。** 現行228行から始まる floor 項目の継続段落として、同じインデントで追加する。以下の行番号は変更前のもの。

参照先の略号を次のように定める。

|略号|ファイル|
|---|---|
|D|[事前登録](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-aggregate/docs/phase3-b4-reflux-ablation-preregistration.md:228)|
|I|[floor issuer](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-aggregate/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:36)|
|F|[floor-pair driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-aggregate/orchestrator/campaign/floor_pair_driver.py:1197)|
|C|[prereg consumer](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-aggregate/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:301)|
|R|[material report](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-aggregate/orchestrator/campaign/p3_b4_material_report.py:211)|
|TI|[issuer test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-aggregate/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:53)|
|TR|[material report test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-aggregate/orchestrator/tests/test_p3_b4_material_report.py:77)|

凍結範囲の根拠は次のとおり。

- `C:301` `_locate_section` は level 4 の §5.1.1 見出しを一意に選ぶ。
- `C:318` は、その後に現れる最初の `heading.level <= 4` の **開始バイト位置**を終端にする。
- `C:342` が切り出すのは `document_bytes[h4.start:end]`。現行では **D:339から623行末まで**であり、終端見出しは `D:624` の §6。
- 237行直後への挿入は開始位置より前なので、位置のオフセットだけが変わり、切り出される bytes は変わらない。`C:394` が検査する raw・semantic の両 pin を維持できる。

「§5.1 の末尾」を §6 直前と解釈して追記すると、追記本文も339行からの切り出しに入る。空白やコメントだけでも raw pin を壊す。**§6 の前に新しい小節を付けて凍結範囲を調整する必要もない。** 237行直後という既存 floor 項目内の位置を使う。

親が書く本文は、以下をすべて満たすものとする。

1. D1936項7によるD1855案Bの採用を明示し、既存workload別3 specの結果を集約する。
2. 最大の対象は、事前に固定した3 specが表す凍結セル集合と各2時間窓の全部。途中結果による spec・セル・窓・標本の選別を認めない。
3. 各 summary を既存検証に通し、さらに後述する spec 対 summary の完全性を照合する。
4. 最大値は `Fraction` 同士で比較する。これは検証済み binary64 値の exact 保存であり、中間演算まで exact になるという保証ではない。
5. `env_tag`・`protocol`・`threads` は全入力で一致を要求し、workload・campaign は集合の和から識別子を導出する。
6. 空入力、欠落、重複、余剰、不一致、非生成 status、不正値は集約全体を拒否する。正常入力だけに間引いて続行しない。
7. `floor >= 1` は切り詰めず、「この動作点では床値を生成できない」とする。
8. 各入力の `proof_limitations` と既存 `NON_GUARANTEES` を保持する。
9. 出力は5要素の identity を名前に含む create-only JSON 1件。上書き・削除・改名による再発行を認めない。
10. §5の pin 文法は1件のまま維持し、集約成果物の path・sha256 を渡す。
11. 本追補は§5.1の解除条件を緩めず、記入の権限・測定開始・正式実走・事前登録の発効を新たに許可しない。
12. 閉包一致の機械検査と、結果を見る前に固定したことの証明を区別する。後者の非保証を消さない。

## 集約規則の設計

**同じ issuer 内に集約専用経路を追加し、単一入力の既存経路は維持する。**

API案は次の1本とする。

```python
issue_aggregate_authoritative_floor(
    *,
    repo_root: Path,
    summary_paths: Sequence[Path],
    expected_specs: Sequence[tuple[str, str]],
    output_dir: Path,
) -> B4AuthoritativeFloorWrite
```

`expected_specs` は相対path・sha256の列で、入力 summary から自動補完しない。APIは非空のN件を扱うが、**今回のB-4採用条件はworkload別3 spec**。N対応が3件以外の採用を認可するわけではない。

処理は次の順で固定する。

1. **期待値を先に確定する。**  
   `expected_specs` の型・相対path・lowercase sha256・重複を検査し、`F:1197` `load_frozen_spec` で全specを読む。期待する窓、campaign、pair、セル、標本集合、統計関数はこのspecから導出する。

2. **全summaryを既存経路で検証する。**  
   `I:828` の canonical JSON、summary schema/status、spec実体hash、producerによるspec検証、receipt由来identity、値域検査をそのまま使う。1件の失敗で全体を拒否する。

3. **集約専用の完全性検査を追加する。**  
   各specにsummaryがちょうど1件対応し、summary pathも `spec.outputs.summary_relpath` と一致することを要求する。そのうえで以下を照合する。

   |対象|照合内容|
   |---|---|
   |窓|`window_artifacts` と `campaigns` が、それぞれspecの全windowに一対一対応|
   |窓の帰属|`window_id`・`campaign_id`・window artifact path がspecと一致|
   |層|`derivation[0].strata`、campaign内strataが `spec.statistics.closed_strata` と過不足なく一致|
   |セル|各windowのpairをcellへ写した集合が、そのspecの全cellsを覆う|
   |標本|導出済みsample keyと欠測sample keyが、specの予定sample key集合を重複なく分割|
   |件数|planned・retained・droppedの各件数が上の集合から再計算した件数と一致|
   |欠測規則|campaign単位の `dropped * 20 <= planned`、admissible、空stratum拒否を保持|
   |統計|summaryの統計識別子をspecの対応値へ照合。`sample_max/v1` は既存再導出を使用|

   欠測は「入力summaryが欠けること」と区別する。producerが認める標本欠測は上記の会計で扱い、pairごとの新しい5%閾値や「必ず59件残る」という保証は追加しない。

4. **identityを合成する。**  
   `env_tag`・`protocol`・`threads` は完全一致。workloadは文字列辞書のcanonical表現、campaignはID文字列の和集合を、それぞれ決定的に整列して `I:732` の識別子生成へ渡す。`loaded_head`・`plan_sha256`・calibrationは入力ごとの出所として残し、異なるspec間で同一値を要求しない。

   `window_id`・`pair_id` の照合キーにはspecのpath・sha256を含める。別specで同じローカルIDを使うことと、同一specの行重複を混同しない。campaign識別子は和集合とするが、全入力の所属関係は成果物に残す。

5. **保守側最大を計算する。**

   ```python
   aggregate_floor = max(summary.floor_exact for summary in summaries)
   ```

   各 `floor_exact` は `I:817` により `Fraction(*candidate_floor.as_integer_ratio())` で生成された値。出力は既約 `[numerator, denominator]`。最大値の出所が複数ある場合は、spec path・sha256・summary path・sha256のcanonical順で先頭を選ぶ。tie規則は出所表示だけに作用する。

6. **全検証後に1件だけ発行する。**  
   入力の順序を成果物bytesへ反映させない。summary pathの重複、同じspecの複数summary、別pathへの同一summary複製、window出力pathの再利用を拒否する。既存 `_publish_create_only`（`I:941`）を再利用する。

命名は次に固定する。

```text
b4-floor-aggregate__env-<env_tag>__protocol-<protocol>__threads-<threads>__workload-<derived-id>__campaign-<derived-id>.json
```

`output_dir` は明示必須とし、入力順で保存先が変わる「最初のsummaryの隣」は使わない。repo配下・non-symlink・既存directoryを要求する。同じidentityで名前が衝突した場合はcreate-onlyで拒否し、連番や時刻suffixで回避しない。

**schemaは集約専用のv2を追加する。**

- `B4_FLOOR_ARTIFACT_SCHEMA_VERSION = ".../v1"`（`I:36`）は維持する。
- `B4_FLOOR_AGGREGATE_ARTIFACT_SCHEMA_VERSION = "p3-b4-authoritative-floor/v2"` を追加する。
- v2は既存の共通欄に `aggregation` を加えた閉じたobjectとする。`aggregation` は固定の最大演算識別子、期待spec pin列、全source summaryの出所・exact値・float hex・`proof_limitations` を保持する。
- 既存 `source_summary` は最大値を与えた代表入力を指す。全入力は `aggregation` に残す。
- `non_guarantees` は既存固定prefixに、canonical順の各summaryのitemsを**重複も含めて連結**する。`proof_limitations.section` も入力別欄に保持する。
- 外部manifestや別台帳は作らない。

v2 loaderは全source summaryを記録hashで再読込し、上記検証と集約値の再構成を行い、成果物の各欄とcanonical bytesで一致を要求する。値だけを変更して成果物hashも再計算する改変、非最大入力の脱落、非保証欄の削除も拒否できる。

これはv2に限りsource summary・spec・既存spec検証の参照先の保存を必要とする設計である。raw windowの実測内容や凍結時系列まで証明するものではなく、既存非保証欄は維持する。

## (P1) の評価

**P1は方向として必要だが、記述どおりでは不十分であり、window集合のcaller入力は冗長である。**

理由は3点ある。

1. **spec pinだけでは、summaryがその全体を報告しているとは限らない。**  
   `I:848` はspec bytesをhashへ照合するが、`I:871` 以降は主にidentityを導出する。`I:661` の完全一致は「summary内のsamplesとstrata」の一致であり、specの `closed_strata` との一致ではない。両方から高い層を消して上限を再計算すれば、窓IDが残っていても部分集合化できる。

2. **windowの正本は既にspecにある。**  
   `F:220` にID・campaign・時刻・標本数・pair・出力pathがあり、`F:937` が統計をpinし、`F:1079` が全予定層との一致を検査する。callerからwindow集合を重ねて受ける必要はない。特に全specのwindow IDを平坦な集合にすると、spec別の欠落を隠せる。

3. **現在渡された期待値との一致は、過去の固定時点を証明しない。**  
   `F:1237` のHEAD blob一致と `F:1285` のsource commit祖先検査も、結果を見ていないことを証明しない。`FREEZE_TIMING_NOT_PROVEN`（`I:50`）は正しい限界として残る。

採用する修正P1は、**callerから明示spec pin列を必須で受け、窓・層・標本の期待閉包をそのspecから導出し、summary由来の実閉包と照合する形**である。期待spec列自体を結果前に既存の凍結記録へ固定する義務は、追補で明記する。その履行と§5のセル集合との意味的一致を、新設の機械保証として宣言しない。

親briefの「specをpinすればcell集合は閉じる」はspecの内容については正しいが、summaryの被覆と§5の対象集合への適合まで含めるなら不足している。briefの較正不足・実spec不存在については本プランの測定停止前提として扱い、今回再調査した事実とは報告しない。

## file:line 変更計画

|位置|追加・変更|
|---|---|
|D:237直後|上記12条項の追補。親が担当。D:339以降の凍結bytesと§5値セルは変更しない|
|I:36|v1定数を維持し、集約v2定数と最大演算識別子を追加|
|I:828|読込処理を内部helperへ抽出し、検証済summary・元document・読み込んだspecを集約経路でも利用可能にする。公開単一loaderの戻り値・受理条件は維持|
|I:890直前|`_load_expected_specs`、`_validate_aggregate_summary_coverage` を追加。期待spec検証と窓・層・セル・標本・欠測の照合を担当|
|I:901周辺|単一 `_authority_value` を維持。`_aggregate_authority_value` を追加し、identity和集合・Fraction最大・出所・非保証を合成|
|I:931周辺|`_aggregate_artifact_filename` を追加。単一成果物の既存名は維持|
|I:1015直後|`issue_aggregate_authoritative_floor` を追加。全検証完了後に既存create-only publisherを1回呼ぶ|
|I:1039|共通のpath/hash/canonical検査後、v1/v2をexact dispatch。v1検証を内部helperに保持し、v2には閉包再検証・再構成比較を追加|
|I:1192|返却 `schema_version` を実際に検証した版にする。v2をv1と誤表示しない|
|I:1216|resolverの引数・pin文法・sentinel処理を維持。既存loader呼出しでv2へ到達する|
|I:1252|旧 `--summary PATH` と新 `--summaries PATH ...` を排他にする。新経路のみ反復指定 `--expected-spec PATH SHA256` と `--output-dir` を必須化|
|TI:53周辺|既存fixtureは維持し、複数spec・全予定層を持つ集約fixtureを別helperとして追加|
|TI:785直前|後述の集約・凍結・consumer接続テストを追加|

旧 `issue_authoritative_floor(repo_root, summary_path)` のsignature、単一 `--summary` の成功・失敗条件、v1 bytes、出力先、命名を維持する。**同じ `--summary` の反復を新しい集約文法として流用しない。** 新しい完全性検査を単一経路へ無条件適用すると、TI:53の「spec全体を再現しない合成summary」を含む既存受理集合が縮むためである。

schemaに関係する既存期待値の扱いは次のとおり。

|既存期待値|扱い|
|---|---|
|TI:499の単一API引数集合|変更不要。集約APIを別にする|
|TI:198のsummary schema exact pin|変更不要。producer入力は引き続きv3のみ|
|TI:603、613、649の単一loader・非保証期待|変更不要。v1を保持|
|TI:674の5要素命名期待|変更不要。単一名を保持|
|TI:754の「v2は不正」変異|**意味が変わる。** 未対応版検査は `.../v999` に変更。既存v1 payloadのschemaだけv2へ替えるケースは、v2必須欄欠落の別負例として追加|
|TR:99のv1 fixture schema|変更不要。既存定数をv2へ付け替えない|
|TR:114の単一sourceと架空参照先|変更不要。v1には参照先再読込を追加しない|
|TR:920のreport schema期待|変更不要。既存fixtureはv1。新規集約接続テストではv2を期待|
|TR:991の非保証3行 exact期待|変更不要。既存fixtureを維持|
|TR:56、59、831のfloor不在golden|変更不要|

R本体とC本体の変更は不要である。集約consumer接続の新規テストはTIへ置き、TRの既存fixtureやgroup所属node集合を増やさない。

## テスト計画 (正例・負例の対)

以下は**今後実装するテスト**。現在は静的確認のみで、実走結果ではない。追加位置は原則TI:785直前。

|正例テスト名・観点|対応する負例テスト名・壊すもの|
|---|---|
|`test_aggregate_exact_max_roundtrip`：異なる3値からFraction最大を選び、loader/resolverまで往復|`test_aggregate_rejects_nonmax_value`：成果物を最小値・平均値へ変更し外側hashも更新。再構成不一致で拒否|
|`test_aggregate_preserves_binary64_ratio`：非十進有限表現を含む値のratio・hex・型を確認|`test_aggregate_rejects_rounded_ratio`：十進桁丸め・不正ratioへ置換。exact値比較で拒否|
|`test_aggregate_expected_specs_match`：明示した3 pinと3入力が一致|`test_aggregate_rejects_spec_closure_mutation[missing,extra,duplicate,hash]`：期待／実specを1件だけ変更。閉包検査で拒否|
|`test_aggregate_windows_match_each_spec`：全specの窓・campaign・pathが対応|`test_aggregate_rejects_window_binding_mutation[missing,extra,duplicate,campaign,path]`：1箇所だけ破壊。窓対応検査で拒否|
|`test_aggregate_covers_all_closed_strata`：複数cell・pairを全窓で被覆|`test_aggregate_rejects_partial_strata`：samplesとstrata双方から高い層を消し、summary最大も整合させる。既存自己整合検査を通ってもspec閉包検査で拒否|
|`test_aggregate_covers_every_spec_cell`：全cellに各窓のpairがある|`test_aggregate_rejects_uncovered_spec_cell`：spec内の1cellをどの予定pairも参照しない形にする。cell被覆検査で拒否|
|`test_aggregate_accounts_for_allowed_drops`：許容範囲の欠測を含む全標本の分割が成立|`test_aggregate_rejects_sample_accounting_mutation[missing,extra,overlap,count,threshold]`：標本keyまたは件数を1点破壊。標本会計／campaign閾値で拒否|
|`test_aggregate_statistics_match_spec`：統計識別子がspecと一致|`test_aggregate_rejects_statistics_mismatch`：summaryの式識別子だけ変更。統計照合で拒否|
|`test_aggregate_identity_union_is_deterministic`：共通3要素とworkload/campaign和集合を確認|`test_aggregate_rejects_identity_mismatch[env_tag,protocol,threads]`：入力単体として有効な1件だけ別identityにする。集約間照合で拒否|
|`test_aggregate_accepts_zero_and_subunit_max`：ゼロ・1未満の値を受理|`test_aggregate_rejects_invalid_member[one,above_one,nonfinite,bool,not_generated]`：1入力だけ不正にする。除外続行せず未発行を確認|
|`test_aggregate_preserves_all_limitations`：各入力の固有文言・重複items・sectionを保持|`test_aggregate_rejects_dropped_limitation`：非最大入力の非保証を1件削除し再hash。再構成比較で拒否|
|`test_aggregate_source_pins_are_verified`：全summaryの実体hashを確認|`test_aggregate_rejects_source_mutation[missing,hash,path_alias,duplicate]`：sourceだけ破壊。全件検証で拒否|
|`test_aggregate_publish_is_create_only`：初回発行・staging残骸なし|`test_aggregate_existing_target_is_unchanged`：同じ対象へ再発行。`artifact_exists` と既存bytes不変を確認|
|`test_aggregate_filename_and_bytes_ignore_input_order`：入力順の全置換と最大値tieで名前・bytes一致|`test_aggregate_filename_rejects_wrong_identity`：内部命名実装から要素を落とす変異で、独立に組み立てた期待名のassertが失敗|
|`test_aggregate_v2_and_legacy_v1_are_loadable`：両版と旧CLIの互換を確認|`test_aggregate_schema_dispatch_is_closed[unknown,v1_as_v2,v2_as_v1,unknown_key]`：版または欄集合を破壊。schema検査で拒否|
|`test_aggregate_cli_requires_explicit_expectation`：新CLIの全必須引数で成功|`test_aggregate_cli_rejects_incomplete_mode[no_specs,no_output,mixed_modes]`：必須引数／排他性を壊す。発行前に拒否|
|`test_floor_addendum_preserves_both_section_pins`：237行直後へメモリ上で追記し、両pin不変|`test_floor_addendum_at_section_end_breaks_raw_pin`：§6直前へ同じ本文を挿入。raw pin検査で拒否|
|`test_aggregate_floor_reaches_material_report`：実resolver→Rの公開builder→評価器にFraction最大が届き、sourceがv2となる|`test_invalid_aggregate_stops_material_report_before_evaluation`：集約内容のみ破壊しpinを再hash。`authoritative_floor_rejected`、評価器未呼出し、成果物未発行を確認|

集約正例fixtureは、TI:206が使う実 `finalize_floor` の方式を基礎とし、測定結果だけを合成する。既存TI:53の一層fixtureを複製するだけでは、全層閉包の正例にならない。

負例では、狙う検査まで到達するよう、無関係なhash・schema・自己整合は正しく更新する。各error codeまたは検査段階をassertする。ただし、親briefの「対応testだけを赤にする」はそのまま完了条件にしない。共有ゲートの変異は複数の正当なテストを失敗させうるため、**狙った負例が指定ゲートを検出したこと**を記録する。

また、入力がすべてbinary64由来なら、floatの直接比較とFraction比較の大小順は同じである。近接値だけで「float比較への置換を必ずkillした」とは主張しない。比較型はコードの静的確認、丸め禁止はratio・hexの独立期待値で確認する。

## 波及

参照関係から直接影響する経路は次である。

```text
I:1216 resolver
  → I:1039 loader
  → R:215 floor解決
  → R:267 評価器へFractionを渡す
  → R:952 / 963 出所・非保証をレポートへ写す
```

この経路を既に検査するTRのテストは以下。

- `TR:851` `test_m9_four_authority_and_assembly_states_project_exactly`
- `TR:958` `test_present_floor_projects_required_verbatim_non_guarantees`
- `TR:1001` `test_m7_non_sentinel_resolver_failure_never_falls_back_or_calls_evaluator`
- `TR:1043` `test_m08_floor_absence_runs_existing_evaluator_as_protocol_violation`
- `TR:731` `test_m8_absent_authority_public_bytes_match_pre_change_golden`
- `TR:266` `test_normal_path_assembles_binds_evaluates_and_builds_document`

事前登録の凍結を直接読むconsumer testは、`orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py` の以下。

- `:95` `test_current_document_contract_literals_match_implementation` — 独立切出し・raw hash・repository consumer・receiptを検査。
- `:215` `test_formatting_equivalent_raw_byte_changes_are_rejected`
- `:234` `test_semantic_change_with_identical_literals_is_rejected_by_section_hash`
- `:256` `test_duplicate_h4_or_h5_anchor_fails_closed`
- `:271` `test_fenced_and_html_commented_heading_decoys_are_ignored`

間接参照も確認した。

- `test_p3_b4_analysis_path.py:596` の `test_private_closure_assembler_is_stable_and_binds_consumer_result` と `:637` の欠落member負例は、§5.1.1切出しをreceiptへ束縛する。issuerは既存5 memberの分析source閉包に含まれず、その閉包の変更は不要。
- `test_p3_b4_raw_record_producer.py:1013` は `test_unterminated_tail_is_truncated_before_the_next_single_write`（`:962`）からRの公開builderを呼ぶ。
- 同`:1228` の `recorded_rejection_report` fixtureは、`:1234` `test_unresolved_absent_attempts_exclude_matching_recorded_rejection` と`:1246` `test_unresolved_absence_retains_current_reason_non_guarantee` に使われる。
- `test_p3_b4_producer_auth_experiment.py:791` と`:821` はRの `_load_and_evaluate` を参照するprototype配置検査。R本体を変更しないのでアンカー更新は不要。
- `test_real_repo_serialization.py:356` はTRのtest名集合を固定している。本案はTRに新規test関数を追加しないため、その集合の更新は不要。TIへ置く新規接続テストは合成fixtureで構成する。

**`acceptance_duration_ledger.json` は、新規nodeidの追加を後続実装の作業に含める。** ただし現在のrunnerは未登録nodeを拒否せず、`conftest.py:1657` が未知コストを返し、`:1738` が代替コストで配置する。台帳登録は集約成果物の正しさゲートではない。

実装段では、実際のテスト結果に基づき既存 `tools/update_acceptance_duration_ledger.py:82` の `--add-only` で新規nodeidだけを登録する。parametrizeの各IDも対象とし、既存durationは維持する。本段で架空の秒数を記入しない。

## 採らない案

- **P1のwindow ID集合をそのままcaller必須値にする。** specに既存の正本があり、平坦な集合ではspec別の被覆を検査できない。
- **入力summaryから期待spec集合も導出する。** 欠落した入力を期待集合からも消せる循環検査になる。
- **summary内の最大だけを再計算する。** specの高い層を丸ごと落とした自己整合summaryを防げない。
- **v1定数を単純にv2へ変更する。** 既存v1成果物とTRの単一source fixtureを壊す。
- **同じv1に任意の複数入力欄を追加する。** `I:1058` のexact key集合契約を曖昧にする。
- **最大入力だけを出所として保存する。** 非最大入力の欠落・差替え・非保証削除を検査できない。
- **全入力でworkload・calibration・plan hashまで同一にする。** workload別3 specを使う裁定と矛盾する。
- **平均・中央値・最小、上限1未満へのclamp。** 保守側最大と値域の裁定に反する。
- **workload一致要求の撤去、multi-calibration schema、別manifest・台帳・汎用集約器。** D1936項7の不採用範囲に入る。
- **hash一致を結果前凍結の証明と表示する。** 既存コードが証明していない時系列を保証してしまう。

## 総括

最も壊れやすい前提は、明示spec pin列が結果前に固定され、§5の対象集合を正しく表すこと。閉包一致だけでは証明できない。  
次に、summary内部の自己整合をspec全体の被覆と取り違えないこと、v2検証をv1へ漏らして既存受理集合を縮めないこと。  
本段は静的調査とプラン起草のみ。編集・実装・commit・pytest実行は行っていない。