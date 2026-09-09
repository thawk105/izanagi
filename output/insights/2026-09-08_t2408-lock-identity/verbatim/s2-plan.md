## 読解結果

親の実測事実を覆す証拠はありませんでした。静的読解では次を確認しました。

- `decode_campaign_lock()` は現行 exact-63 authority だけを受理し、3 本の pre-T733 exact-24 lock は拒否する。
- `decode_historical_campaign_lock()` は別返却型で exact-24 を扱うため、D1653 に合う入口はこれだけである。
- `--prereg-commit <現行 HEAD>` のデータフローは、live v5 の binding/spec を report root、判定、出力へ渡す。ただし現物 exact-24 lock は `_assert_report_lock_binding()` で先に拒否されるため、現行コードと現物3本の組合せでは report 発行まで到達しない。親の「現行 era identity で発行しうる」は、lock decoder の障害を除けば正しい、という条件付きの読解になる。
- report/pytest は実走していない。ファイル編集もしていない。

## 採用する identity 構成

report 専用の `HistoricalSeriesIdentity` と `HistoricalReportIdentity` を同一 module 内に置き、live `Preregistration` と型を分ける。

各系列では `decode_historical_campaign_lock()` の返却値から次を読む。

- `identity["search_config"]["preregistration_path"]`
- `identity["search_config"]["preregistration_binding"]`
- `identity["search_config"]["preregistration_spec"]`
- `identity["search_config"]["workload"]`

受理条件は次に閉じる。

- lock は `campaign-lock/v2`。
- authority grammar は `PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS` exact-24。v1 と現行 exact-63 は report 限定受理では拒否する。
- workload は固定 dispatch の系列名と exact 一致。
- `preregistration_path == PREREG_REL`。
- `preregistration_binding` は対応する `_legacy_*_binding()` の module literal と dict の key 集合を含め exact 一致。
- `preregistration_spec` の canonical SHA-256 は、その exact binding の `spec_sha256`、すなわち歴史 literal `9c594114...` と一致。
- 3 系列から復元した spec の canonical JSON と path は相互に exact 一致する。系列別 binding は統合せず、3 本のまま保持する。

135 個の record digest literal と各 validator の digest 集合比較には触れない。

## lock spec の復元方針

`preregistration_spec` 全体から `PreregistrationSpec` を復元する report 専用入口を作る。汎用 `from_dict` は作らない。

復元入口は exact dict、schema v4、歴史 `spec_sha256` を先に検査し、その後、既存 dataclass の全 fieldを v4 dictから構築する。これにより次の全 consumer が同じ lock由来 objectを使える。

- `block_order_map`
- `workload_map`
- `_require_exact_workload_cells`
- `_require_exact_report_cells`
- `_verification_completeness`
- `_performance_cell_completeness`
- `load_calibration`
- `validate_runtime_physical_residual`
- `judge` / `cell_effects`
- report の spec、physical residual、外部参考幅、判定パラメータ

必要 field だけを個別に読む案は却下する。report は分析、欠測、CI、physical residual、参考幅まで spec の大部分を使うため、部分投影にすると複数の authority を作り、将来の取りこぼしも生む。

`parse_preregistration()` を v4対応へ広げる案も却下する。live v5入口の受理集合が広がるためである。v4 dict の schema を一時的に v5へ書き換えて同 parser に通す案も、測定時の文書を別 schema として解釈するため採らない。

## live依存箇所ごとの判断

| 現在の依存 | 変更後 | 理由 |
|---|---|---|
| legacy binding | 各 lock の `search_config.preregistration_binding` を読み、対応する系列別 module literal と exact比較 | lockを authority にするだけでなく、有限 literal の境界を維持する |
| `prereg.spec.block_order_map` | `search_config.preregistration_spec.blocks.run_order` から復元 | spec digest literal に束縛された順序を使う |
| `prereg.spec.workload_map` | `search_config.preregistration_spec.workloads` から復元 | live文書の追加・修正から report対象を切り離す |
| `_require_exact_report_cells` | lock由来 spec の workload、block、point の直積 | 135 cell の exact集合は維持する |
| 各 legacy validator の order/cell gate | 対応する系列 lock から復元した spec | record とその測定時 identity を同じ lockへ束縛する |
| `report_root` の live `binding_sha256` | 3 lock共通の記録済み `spec_sha256[:16]` | binding SHA は系列ごとに異なり、1本を代表に選べない。新しい合成 digest も作らない |
| `load_calibration(..., prereg.spec)` | 共通の lock由来 spec | threadsなどの report前提を測定時specに合わせる |
| `validate_runtime_physical_residual(prereg.spec, ...)` | 共通の lock由来 spec | v4に記録された residual表と上限を使う |
| `_write_reports` / `judge` | 共通の lock由来 spec | live v5で歴史 recordを再解釈しない |
| report の preregistration表現 | 共通の path/spec/core値と、3系列の full bindingを別々に記録 | 単一 bindingでは3系列を正確に表現できない |
| 現行解析コード identity | submissionの current source commitと現行 module blob hashを別欄に記録 | 測定時bindingと、今回reportを生成した解析コードを混同しない |
| patch / applied-tree検査 | live文書からは取らず、現在のreport解析環境の evidence として別扱い | 歴史 patch SHAとは比較できないが、現行解析面の検査は維持できる |
| `search_config.block_run_order` 等の重複投影 | authorityにはせず、digestで束縛された `preregistration_spec` を正本にする | 新しい冗長整合 gateを追加せず、単一のlock内正本に寄せる |

`campaign_lock.py:508-612` は変更しない。通常 decoderをunion化せず、B-10 report側が歴史 decoderを明示的に選ぶ。

## file:line 実装プラン

対象は [b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py) だけである。

| 関数・位置 | 現状 | 変更後 |
|---|---|---|
| 現行 `:503` 直前、新規 `HistoricalSeriesIdentity` / `HistoricalReportIdentity` | 歴史lock由来 identity を表す型がなく、live `Preregistration` しかない | 系列名、path、exact binding、復元spec、authority commitを保持するreport専用型を追加する |
| 現行 `:1501` 付近、新規 `_preregistration_spec_from_historical_lock()` | v4 dictの復元入口がなく、v5文書parserはv4を拒否する | exact v4 schemaと歴史spec digestを検査して全fieldを `PreregistrationSpec` へ復元する |
| 現行 `:1618` 付近、新規 `_load_report_analysis_identity()` | `load_preregistration()` がlive文書検査と現行解析blob検査を一緒に行う | reportでは文書を読まず、既存のclean tree、HEAD、`ANALYSIS_REL` blob一致だけを分離して維持する |
| 現行 `:2670-2677` `_expected_block_cells()` | `Preregistration` からspecを取る | `PreregistrationSpec` を直接受け、live/report双方で同じexact cell集合を作る |
| 現行 `:2710-2721` `_require_exact_workload_cells()` | live `Preregistration.spec` を使う | 呼出元が渡したliveまたはlock由来specを使う。集合述語は不変 |
| 現行 `:2724-2743` `_require_exact_report_cells()` | live v5のworkload/orderで135 cellを作る | lock v4から復元した共通specで135 cellを作る |
| 現行 `:2863-2873` `_legacy_write_heavy_binding()` | 引数を無視してwrite-heavy literalを返す | 引数を削除し、同じ系列別literalをそのまま返す |
| 現行 `:2899-2912` `_assert_report_lock_binding()` | 通常decoderを使い、v1/current exact-63の一致bindingは受理するが現物exact-24を拒否する | 歴史decoderを使い、pre-T733 v2、系列workload/path、binding literal、v4 spec digestを検査し `HistoricalSeriesIdentity` を返す |
| 現行 `:2915-2998` `_validate_legacy_write_heavy_records()` | bindingはliteral、order/cellはlive specから取る | bindingとrecord digest literalは不変のまま、order/cellはwrite-heavy lock由来specから取る |
| 現行 `:3001-3010` `_legacy_balanced_binding()` | 引数を無視してbalanced literalを返す | 引数を削除し、balanced専用literalを維持する |
| 現行 `:3013-3101` `_validate_legacy_balanced_records()` | bindingはliteral、order/cellはlive specから取る | balanced lock由来specへ切替え、45 digestと系列別semantic gateは不変 |
| 現行 `:3104-3113` `_legacy_read_heavy_binding()` | 引数を無視してread-heavy literalを返す | 引数を削除し、read-heavy専用literalを維持する |
| 現行 `:3116-3206` `_validate_legacy_read_heavy_records()` | bindingはliteral、order/cellはlive specから取る | read-heavy lock由来specへ切替え、45 digestと系列別semantic gateは不変 |
| 現行 `:3441-3515` `_verification_completeness()` | live specのworkload数を使う | lock由来specを直接受けるだけに変更する。`:3359-3438` のWAL読取処理には触れない |
| 現行 `:3518-3608` `_collect_report_inputs()` | live specで系列を列挙し、records検証後に通常decoderでlockを検査する | 固定3系列ごとにlockを先に歴史decodeし、その系列identityでrecordsを検証し、共通specと3bindingを返す |
| 現行 `:3611-3624` `_performance_cell_completeness()` | live specから期待cell数を計算する | lock由来共通specから同じ135を計算する |
| 現行 `:3627-3806` `_write_reports()` | live binding/specを単一preregistrationとしてv2へ書く | lock由来共通specと3系列binding、現行report解析identityを分離して書く。推奨schemaはv3 |
| 現行 `:3917-3998` `run_formal()` report分岐 | 全phaseで先に `load_preregistration()` を呼び、live bindingをcalibration、root、writerへ流す | reportだけ歴史commit gate、lock収集、lock spec、現行解析evidenceの順へ分ける。非reportは既存live経路をそのまま維持する |
| 現行 `:4233-4242` `run_formal()` live perf完了部 | helperへ `Preregistration` を渡す | helperのspec直接引数化に伴い `prereg.spec` を渡すだけで、live意味は変えない |

## `--prereg-commit` の扱い

reportでも必須のままにし、無視も別flag化もしない。

新規 `_require_report_prereg_commit()` で、入力が3つの系列別 binding literalそれぞれの `prereg_commit` とexact一致することを要求する。現在はいずれも `77b33e37d2d63b1f83d10652792c3c93eba9fe8f` である。

その値は `load_submission_identity()` にも渡し、report submission receiptの `prereg_commit` と一致させる。一方で `load_preregistration()`、歴史blobのgit再読、working tree上の事前登録文書とのbytes比較はreportでは行わない。非report phaseでは従来どおりlive文書を検査する。

## テスト計画

追加先は [test_b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py) の既存legacy/report fixture群、現行 `:393-520` と `:1898-2853` 周辺とする。

現物の外部絶対pathには依存しない。既存fixture方式に合わせ、既存の凍結v4 provenanceから共通specを読み、現物から確認した次の relevant fieldsを持つcanonical v2 exact-24 lockを `tmp_path` に構築する。

- pre-T733 ordered authority key集合
- 系列別 authority commit
- workload
- `preregistration_path`
- 系列別 exact binding
- 共通 v4 `preregistration_spec`

3本のraw lock全体は複製しない。これなら通常CIでも歴史decoderを実際に通し、外部evidence treeの有無に左右されない。

追加または置換するテストは次のとおり。

- `test_report_lock_identity_accepts_exact_pre_t733_three_series`
  - 正例。3系列をparametrizeし、exact-24 decoder、binding key差、v4 spec SHA、workloadを固定する。
- `test_report_lock_identity_rejects_v1_and_current_grammar_with_exact_binding`
  - 負例。同じbindingを入れてもv1とexact-63はB-10歴史report入口で拒否されることを示す。
- `test_report_lock_identity_rejects_recanonicalized_binding_drift`
  - 負例。bindingの各keyまたは系列を交換し、outer/inner JSONを正しく再canonical化してもmodule literal比較で拒否する。
- `test_report_lock_identity_rejects_locked_spec_drift`
  - 負例。v4 specのorder、workload、分析値のいずれかを変え、lock自体を再canonical化しても歴史spec digest不一致で拒否する。binding側のdigestも変えた場合はbinding literal不一致で拒否する。
- `test_report_lock_v4_spec_is_reconstructed_without_live_parser`
  - 正例。`parse_preregistration()` と `load_preregistration()` をfail stubにしてもlock spec復元が成功し、block order、workload、residual、分析値がv4から得られることを固定する。
- `test_report_commit_gate_accepts_only_frozen_prereg_commit`
  - 正例は `77b33e...`。負例は現行HEAD、短縮hash、別の40桁hash。
- `test_report_collector_passes_each_series_its_own_locked_identity`
  - 正例。3validatorが対応するlock identityを1回ずつ受け、live `Preregistration` 引数が消えたことを固定する。
- `test_report_provenance_contains_three_locked_bindings_and_current_analyzer_separately`
  - 正例。共通spec、3つの異なるbinding SHA、write-heavyだけのbinding内 `analysis_commit`、current report analyzerが別欄であることを固定する。
- `test_report_root_uses_locked_common_spec_sha`
  - 正例。root segmentが `9c59411476018d51` であり、live binding SHAや特定系列のbinding SHAではないことを固定する。
- `test_legacy_record_digest_literals_remain_exact_135`
  - 既存3集合の各45件とmeta digestを固定し、今回の変更で1byteも変わらないことを示す。
- 既存のcontent再hash、46件目、campaign ID違い、semantic mutation注入テストは残す。これらが、lock経路追加後もrecord受理集合が広がらない負例になる。

現行 `test_report_lock_binding_reads_the_real_campaign_lock_codec` はv1を正例としているため、歴史report入口の新しい閉集合に合わせて上記exact-24正例とv1負例へ置換する。

## 変異候補

- `_assert_report_lock_binding()` を通常decoderへ戻す  
  → `test_report_lock_identity_accepts_exact_pre_t733_three_series` が落ちる。
- lock bindingと系列別module literalの比較を削除する  
  → `test_report_lock_identity_rejects_recanonicalized_binding_drift` が落ちる。
- `preregistration_spec` のcanonical digest検査を削除する、またはlive specを使う  
  → `test_report_lock_identity_rejects_locked_spec_drift` と `test_report_lock_v4_spec_is_reconstructed_without_live_parser` が落ちる。
- reportでも `load_preregistration()` を呼ぶ、または現行HEADを `--prereg-commit` として許す  
  → `test_report_commit_gate_accepts_only_frozen_prereg_commit` とlive parser fail-stub正例が落ちる。
- report rootまたはprovenanceを単一系列/live bindingへ戻す  
  → root testと3binding provenance testが落ちる。
- 135 digest literalの変更、またはdigest集合比較の削除  
  → exact-135 meta digest testと既存content mutation負例が落ちる。

## 段5実装子への分割

実装子は1単位とする。driver内のreport identity導線と同一test fileのfixture/signature更新が原子的であり、分割すると一時的にlive/歴史型が混在するためである。

## 総括

1. 採る設計: report専用の別型・別入口で3本のpre-T733 lockを歴史decodeし、系列別bindingをmodule literalへexact照合したうえで、digest固定されたv4 spec全体を復元する。これがlive文書依存を除きつつD1597とD1653の受理境界を保つ最小の一貫設計である。
2. 却下した設計: live parserのv4対応、歴史git blobの再parse、必要fieldだけの部分読出し、`--prereg-commit` の無視、新flag、通常decoderのunion化、特定1系列のbindingをreport全体の代表にする案。いずれもlive受理集合の拡大、死んだroute、authority分裂、または3系列identityの誤表示を招く。
3. 親が段4で裁定すべき残り論点: aggregate reportのprovenanceを、単一binding前提のv2のまま形だけ変えるか、推奨どおりv3へ上げて「共通spec＋3系列binding＋current analyzer」を明示するか。実装上はv3を推奨する。