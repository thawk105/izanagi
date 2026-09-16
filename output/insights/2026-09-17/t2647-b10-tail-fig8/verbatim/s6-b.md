## 数値の再計算結果 (cell ごとの照合表、不一致の有無)

**24 cell 全件一致。数値の不忠実性という疑いは refuted。** 生成器を import・実行せず、標準ライブラリで実データ `.dat` の120行と JSON reps を照合し、整数カウンタから abort 率を再計算しました。

以下、`G` は [生成器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/tools/plotting/plot_b10_static_tail_formal.py)、`T` は [test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/orchestrator/tests/test_plot_b10_static_tail_formal.py) を指します。

計算は `abort = aborts / (aborts + commits)`、標本 SD（ddof=1）、`CI半幅 = t₀.₉₇₅,₄ × SD / √5`。t 分布の CDF から独立に求めた係数は **2.776445105197789** で、G:46 の値と浮動小数点精度内で一致します。provenance との最大相対差は **3.79×10⁻¹⁵** でした。

表の ± は95% CI半幅、CVは throughput / abort の順です。表示値だけ丸めています。

| workload | backoff µs | throughput平均 ± CI（tps） | abort平均 ± CI | CV（%） | 照合 |
|---|---:|---:|---:|---:|---|
| write-heavy | 1000 | 993106.4 ± 1784.4620 | .0423438577 ± .0000937232 | .144713 / .178259 | 一致 |
| write-heavy | 1250 | 905601.2 ± 2427.7982 | .0376615485 ± .0000987145 | .215909 / .211095 | 一致 |
| write-heavy | 1768 | 787038.8 ± 2213.4463 | .0311911672 ± .0000816496 | .226500 / .210823 | 一致 |
| write-heavy | 2500 | 684422.6 ± 3305.9999 | .0257636695 ± .0001273986 | .389022 / .398247 | 一致 |
| write-heavy | 3535 | 595824.8 ± 1905.1541 | .0212020257 ± .0000688397 | .257518 / .261491 | 一致 |
| write-heavy | 5000 | 520175.6 ± 2188.2401 | .0173568416 ± .0000750298 | .338798 / .348144 | 一致 |
| write-heavy | 7070 | 455649.6 ± 1237.1852 | .0141449640 ± .0000396735 | .218675 / .225889 | 一致 |
| write-heavy | 9999 | 401697.6 ± 3226.5492 | .0114345357 ± .0000932355 | .646897 / .656688 | 一致 |
| balanced | 1000 | 718264.8 ± 3445.0012 | .0587534842 ± .0002679031 | .386279 / .367232 | 一致 |
| balanced | 1250 | 659017.0 ± 1993.9585 | .0519364472 ± .0001463584 | .243677 / .226956 | 一致 |
| balanced | 1768 | 570909.6 ± 2905.7143 | .0431368178 ± .0001770016 | .409903 / .330465 | 一致 |
| balanced | 2500 | 496833.6 ± 2634.9097 | .0356015218 ± .0001983716 | .427121 / .448752 | 一致 |
| balanced | 3535 | 436522.8 ± 2529.2218 | .0290243985 ± .0001638670 | .466633 / .454699 | 一致 |
| balanced | 5000 | 387841.6 ± 1795.4454 | .0233570900 ± .0001081039 | .372832 / .372751 | 一致 |
| balanced | 7070 | 347912.8 ± 2475.8462 | .0185819333 ± .0001285190 | .573125 / .557022 | 一致 |
| balanced | 9999 | 317246.2 ± 2102.4102 | .0145233392 ± .0001009905 | .533724 / .560028 | 一致 |
| read-heavy | 1000 | 1703577.8 ± 5531.2497 | .0237486832 ± .0000728696 | .261491 / .247117 | 一致 |
| read-heavy | 1250 | 1545212.0 ± 5265.8095 | .0213237406 ± .0000801348 | .274456 / .302659 | 一致 |
| read-heavy | 1768 | 1322901.2 ± 2439.6959 | .0180268618 ± .0000227699 | .148527 / .101727 | 一致 |
| read-heavy | 2500 | 1133420.6 ± 3673.7890 | .0151786844 ± .0000665727 | .261047 / .353230 | 一致 |
| read-heavy | 3535 | 971805.2 ± 4828.6326 | .0127346504 ± .0000659929 | .400167 / .417355 | 一致 |
| read-heavy | 5000 | 834521.0 ± 4575.5347 | .0106308558 ± .0000573244 | .441571 / .434278 | 一致 |
| read-heavy | 7070 | 715417.0 ± 1987.0808 | .0088805541 ± .0000259404 | .223693 / .235252 | 一致 |
| read-heavy | 9999 | 618689.8 ± 6009.5510 | .0073345624 ± .0000694459 | .782285 / .762550 | 一致 |

追加の照合結果：

- throughput端点比は **0.44357008360854644 / 0.4813930444889889 / 0.40039153203573363**。caption の **0.444 / 0.481 / 0.400** と一致。
- JSON の L 範囲は **0.27379477196757174〜0.3704384253381395**。caption の **0.2738〜0.3704** と一致。全18区間で `L=1−2^qU`、`U=1−2^qL` も一致。
- [results 稿 §2.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md:228) の平均・abort率・CVの全表項目に不一致なし。§2.2 の18区間・108数値も丸め後に一致。
- provenance の report・workload state・saturation_location・local_flat_intervals・intervals は元 JSON と一致。15件の artist_series の数値・区間コピーも一致。
- 入力3件の SHA は pin と一致。着地 PNG/PDF の SHA は provenance と一致し、caption は README に収録されています。

## must-fix (番号、file:line、放置時の影響 1 行、根拠、修正案)

**1. real — M11 に診断文言だけで赤になる node が混在する。**

場所：G:173・178、T:255・257、[裁定:110](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-fig8/s4-adjudication.md:110)、[変異契約:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/docs/dev-wave/mutation.md:18)。

**放置時の影響：受理集合が変わっていない拒否経路を、SHA gate の検出力として誤計上する。**

M11 で G:173 の比較だけを除去すると、`test_pinned_hashes_are_used_when_no_override` の fixture は G:178 の completion artifact hash 検査で引き続き拒否されます。T:257 が要求する `"SHA-256"` がエラー文に無いため赤になりますが、これは DW-M03 が kill と認めない診断差です。

一方、T:247 の complete JSON への空白追加は、M11 後には受理されます。こちらは実効的な kill です。

修正案：既定pin testでは拒否事実と診断文言を分離し、後者を kill 根拠から外す。M11 は空白追加の単一理由 fixture を検出根拠にし、変更後の失敗 node 完全集合を probe で確定する。

**2. real — 変異 matrix の期待 node が完全集合ではない。**

場所：[author:108](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-fig8/artifacts/dev-wave-t2647-b10-tail-fig8/s5-author.md:108)、裁定 §4、T:356・402、[変異契約:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/docs/dev-wave/mutation.md:60)。

**放置時の影響：正しく検出した変異でも期待 node 完全一致を満たさず、変異受入の判定が誤る。**

最も明確なのは M9。先頭 `return` にすると `test_bbox_overlap_is_a_failure` に加え、`test_layout_failure_publishes_nothing` も赤になります。後者では layout 拒否が消え、公開が成功して `_reject` が失敗します。

ほかにも M2 の malformed test、M6 の固定文言 test、着地済み状態での M1/M4/M5/M6 の closure test が予想表から漏れています。

修正案：下節の集合を出発点に、最終着地状態で probe を行い、DW-M08 に従って完全集合を登録し直す。現時点の表は「予想」と明記されているため、未実施の kill 成功とは扱わない。

## nit

- **real：負例11件中、1・4・5・7・8番目は単一理由ではない。** T:371 のキー欠落は G:182 を除去しても G:250 の report コピーで拒否されます。T:374 の `abort_counts_=True` は型検査以外に再計算率・statistics・DATとの不一致、T:375 の NaN は有限性以外に正値検査、T:377 の rep重複は DAT対応、T:378 の backoff重複は statistics対応などでも拒否されます。これらは「不正入力を拒否する」testとして有効ですが、個別 gate の単独変異証拠には使えません。登録変異の直接の検出根拠にはなっていないため nit とします。

- **refuted：並べ替え・位置zipによる誤対応。** G:190・191 が campaigns と workloads の双方を名前込みで `WORKLOADS` 順に検査し、G:201 が rratio を束縛します。G:218 の sort 後も statistics は G:222 の backoff文字列keyで参照します。判定値は G:228・243・250 でコピーされ、再分類されません。

- **refuted：parse が SHA 不一致を隠す。** G:170で3ファイルすべてを検査してから G:175で parse します。CLI引数は root と prefix だけで、`expected_hashes` seam は argv から指定できません。着地test T:410も overrideなしです。

- **refuted：fixture の寸法不足。** T:57〜96 は定数から3×8×5、DAT120行、18区間、各pointのcorrectness5件、identity.grid8件を作ります。本物の Figure も検査します。ただし schema の完全な複製ではなく、実データにある statistics の `median`・`variance_term`、grid の `canonical_genome` 等は省略されています。作図寸法の契約は満たしています。

- **real、限定事項：公開処理は3ファイル一括の原子操作ではない。** G:462 の layout check は mkdir・保存より前なので、その失敗では新規成果物は出ません。G:476以降は rename失敗時に既存bytesを復元しますが、復元自体の I/O失敗やprocess停止まで保証しません。既存成果物を残すことと「新規成果物を出さない」ことを区別した説明が必要です。通常の失敗経路に具体的な破損は確認していません。

- **closure の射程。** G:453・454 は保存済み cells から artist/caption を再投影する整合検査です。外部pinや出力hashは検査しますが、cells自体を元repsから再計算する検査ではありません。同時に整合的に書き換えた provenance の数値まで独立に検証するものとは説明できません。今回、その不足分は上記の独立再計算で確認しました。

- **refuted：禁止句test・axes gate が恒真。** T:235 の `"saturates"` は `"saturated"` の部分文字列ではありません。source検査は裁定の「生成器にも禁止句を書かない」に沿いますが、将来の説明コメントまで制約します。また現物は `_require(len(plot_axes) != 6 ...)` ではなく、G:381 の `if len(plot_axes) != 6 or set(plot_axes) != set(fig.axes)` です。余分なaxesを拒否する有効な検査です。

- **skip・自走harness。** T:390 は root不在だけを明示的にskipし、存在する不完全rootはloaderが拒否します。T:406は3成果物とREADME記載がすべて無い場合だけskipし、部分着地を見逃しません。T:416は全25関数を拾い、引数は実際に「なし／tmp_path」の二種類です。SkipはPASSと分離され、plain-runner allowlist契約とも整合します。ただしroot不在時のrc=0を実データ検証済みとは扱えません。

## 変異 matrix の検査 (M0〜M12 の anchor 一意性・予想 node・mask の可能性)

author表の逐語anchorを文字列として数え、**M0〜M12すべて出現数1**でした。

以下は静的に予想する失敗 node 集合です。node名には共通して `orchestrator/tests/test_plot_b10_static_tail_formal.py::` が付きます。`landed` は `test_landed_fig8_repo_closure_and_caption_when_present`、`real-root` は `test_real_root_loads_and_matches_results_document_when_present` の略です。変異の実走結果ではありません。

| ID | anchor位置・件数 | 予想される失敗 node | mask・注意 |
|---|---|---|---|
| M0 | G:2、1件 | なし | 無害な文言変更なら図・受理集合上は等価。`__doc__`由来のCLI helpと記録generator hashは変わる。置換後diff未提示なので等価確定ではない |
| M1 | G:36、1件 | `test_pinned_input_hashes_match_results_document`、real-root、landed | 実データloaderと着地external pinも赤。合成fixtureはoverrideする |
| M2 | G:182、1件 | `test_performance_certified_true_is_rejected`、`test_malformed_fields_and_counterpart_mismatches_are_rejected` | malformedの2番目、`performance_certified=0`が受理される |
| M3 | G:152、1件 | `test_dat_abort_rate_disagreeing_with_counters_is_rejected` | reseal済みでpinにmaskされない |
| M4 | G:299、1件 | `test_artist_series_have_exact_x_and_boundary_reference_is_separate`、landed | 着地artist_seriesと新しい投影も不一致になる |
| M5 | G:271、1件 | `test_caption_contains_fixed_expression_and_certification_literal`、landed | 着地captionとの比較も赤 |
| M6 | G:53、1件 | `test_caption_avoids_forbidden_saturation_claims`、`test_caption_contains_fixed_expression_and_certification_literal`、landed | author表は固定文言testを落としている |
| M7 | G:228、1件 | `test_interval_states_are_copied_not_recomputed` | fixtureのindeterminateを上書きするため有効。実データは全decliningで変わらない |
| M8 | G:46、1件 | `test_fixture_has_production_shape_and_recomputes_statistics` | test側係数はliteralで独立。closureは保存済みCIから投影するため通常は赤にならない |
| M9 | G:376、1件 | `test_bbox_overlap_is_a_failure`、`test_layout_failure_publishes_nothing` | 後者が登録漏れ |
| M10 | G:139、1件 | `test_dat_with_missing_row_is_rejected` | 最終行削除は残行のmembership・一意性を壊さず、別の全件数gateもない。単一理由 |
| M11 | G:173、1件 | `test_external_input_hash_drift_is_rejected`、`test_pinned_hashes_are_used_when_no_override` | 前者は実効kill、後者はG:178にmaskされた診断差のみ |
| M12 | G:124、1件 | `test_uncertified_correctness_record_is_rejected` | certified=Falseのみ変更しanomalies=0を保つため単一理由 |

M1とM11は同じ層の検査ではありません。M1は「期待pin値の正しさ」、M11は「実bytesとの比較の存在」です。M11の空白fixtureはその区別を保っています。問題は、既定pin fixtureをM11の単一理由証拠にも数えようとしている点です。

## 親 brief・裁定への所見

- **refuted：median不存在・DAT列順誤認。** [brief:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-fig8/brief.md:7) の median存在とDAT列順は現物どおりです。例えば write-heavy/1000 の `median=0.04232391959566579` が存在します。
- **real、nit：campaign_path の階層表記が不正確。** briefおよび裁定§2.2手順3の `campaigns[].campaign_path` は、現物では `campaigns[].admission.campaign_path`。G:197は正しい階層を読んでいます。「group idはJSONに無い」は専用fieldが無いという意味なら正しく、文字列自体はこのpathに含まれます。
- **real：受理集合の説明が揺れる。** brief P2はCV相互検算を要求しますが、裁定§2.2手順6は平均だけを列挙し、author:99はCV検査を追加制約として説明しています。G:224は平均・両CV・abort SDを検査します。親側でこれを正式要件として明示すべきです。
- **closure seam追加は妥当。** 合成fixtureの成功とproduction pinを両立し、T:331で既定closureの拒否、T:332でoverride時の成功を分けています。着地testの意味は弱まっていません。
- **焦点走logの射程を限定する必要があります。** 指定logは計算ノードdispatch、child rc=0、27 passed・1 skippedを記録しますが、受入全走ではないと明記しています。これを現在の着地test成功や変異検査成功の証拠にはできません。今回もpytest・生成器・変異は実走していません。

## 総括

**図・provenance・results稿の数値は24 cellすべて一致し、現行production入力の誤受理や誤描画は確認しませんでした。**

must-fixは変異受入契約の2点です。**M11の診断差だけの赤を検出力から分離し、着地済み状態で期待node完全集合を再登録してください。** 負例の過剰決定箇所は、個別gateの単独変異証拠として扱わないことが必要です。
