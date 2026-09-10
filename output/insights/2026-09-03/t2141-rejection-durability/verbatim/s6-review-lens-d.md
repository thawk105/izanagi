## must-fix

- [p3_b4_material_report.py:980](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2141-rejection-durability/orchestrator/campaign/p3_b4_material_report.py:980) — `producer_rejections` の無条件参照が既存 renderer-only 4 node を `KeyError` にし、旧 report dict の Markdown 生成互換性を壊している。
- [test_p3_b4_raw_record_producer.py:970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2141-rejection-durability/orchestrator/tests/test_p3_b4_raw_record_producer.py:970) — N08 の producer・report 両 fixture が全 result leaf 欠落済みであり、invalid ledger が正常な 201 leaf assembly を利用不能にする R6 回帰を検出できない。
- [test_p3_b4_raw_record_producer.py:936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2141-rejection-durability/orchestrator/tests/test_p3_b4_raw_record_producer.py:936) — batch test は有効 publication しか渡さないため validation 順序の反転を検出せず、pre-scan rejection の記録行 `producer.py:2144` と例外記録行 `:2192` を削除しても緑になり、対象 rejection が ledger から欠落し得る。
- [p3_b4_raw_record_producer.py:658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2141-rejection-durability/orchestrator/campaign/p3_b4_raw_record_producer.py:658) — root/ledger の `O_NOFOLLOW` (`:658,666`) と file/root `fsync` (`:699-701`) は全投影テストを緑のまま削除でき、symlink 転送と非耐久 return の回帰が受入を通る。
- [test_p3_b4_raw_record_producer.py:849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2141-rejection-durability/orchestrator/tests/test_p3_b4_raw_record_producer.py:849) — event の `schema_version` は存在しか見ず、writer/parser 共通定数を誤値へ変えても緑なので、公開 JSONL schema の無断変更を検出できない。

## 変異ごとの期待 node 集合

略号は `P=test_p3_b4_raw_record_producer.py`、`I=test_p3_b4_prerun_issuer.py`、`R=test_p3_b4_material_report.py`。

| 変異 | 期待 node の完全集合 | 帰属が一意か |
|---|---|---|
| N01 | `P::test_validated_rejection_is_appended_as_one_canonical_event`<br>`P::test_unterminated_tail_is_truncated_before_the_next_single_write`<br>`P::test_rejection_append_failure_adds_io_error_without_publishing`<br>`R::test_m01_m02_assembly_rejection_still_reports_201_blocks_and_missing_leaf` | 集合として一意。最初の node が単発 return の直接 anchor。他の3 nodeは N02、N03、N06/N07 と重なる。 |
| N02 | `P::test_unterminated_tail_is_truncated_before_the_next_single_write` | 一意。実 file に fragment を残して再 append し、fragment bytes の消滅まで検査する。 |
| N03 | `P::test_rejection_append_failure_adds_io_error_without_publishing` | 一意。append 関数を直接失敗させ、追加 `IO_ERROR` を検査する。ただし N01 でも同 node は落ちる。 |
| N04 | `P::test_m14_busy_campaign_with_no_terminal_record_is_deferred_without_publish` | 一意。実 Deferred 分岐到達後の ledger 不在を検査する。 |
| N05 | `I::test_fixed_artifact_descendant_is_rejected_before_rng_or_publication[raw-record-rejections.jsonl]`<br>`I::test_rejection_ledger_exact_path_and_publication_root_are_reserved[exact]`<br>`I::test_loader_rejects_fully_rebound_rejection_ledger_conflict[exact]`<br>`I::test_loader_rejects_fully_rebound_rejection_ledger_conflict[descendant]` | 一意。`[publication-root]` は旧固定 artifact 群だけでも拒否されるため集合に入らず、新しい名前の証拠ではない。 |
| N06 | `R::test_m01_m02_assembly_rejection_still_reports_201_blocks_and_missing_leaf` | node 単位では非一意。N07 と完全に同じ集合で、差は失敗 assertion の行だけ。 |
| N07 | `R::test_m01_m02_assembly_rejection_still_reports_201_blocks_and_missing_leaf` | node 単位では非一意。N06 と同一 node に相乗りしている。 |
| N08 | `P::test_invalid_rejection_history_does_not_replace_assembly_rejection`<br>`R::test_m01_m02_assembly_rejection_still_reports_201_blocks_and_missing_leaf` | 成果物保証に対して非一意。両入力とも result set が既に `INCOMPLETE_SET` で拒否され、正常 assembly の受理維持を証明しない。 |

N06 と N07 は単独 mutant のスタック行を保存すれば区別できるが、node 集合だけを mutation 証拠にすると区別不能。N08 は node 集合以前に、前後の拒否層が重なっている。

## 落ちないテスト・効かない実装

新設・拡張テストが直接守る箇所は次のとおり。

| test / case | 1 箇所壊すと落ちる場所 | 検出しないもの |
|---|---|---|
| `test_validated_rejection_is_appended_as_one_canonical_event` | `producer.py:2077` の単発 durable-record 呼び出し | schema version の正値、`flock`、`fsync`、`O_NOFOLLOW`、単一 `write` |
| `test_unterminated_tail_is_truncated_before_the_next_single_write` | `producer.py:694` の `ftruncate` | 並行 append |
| `test_rejection_append_failure_adds_io_error_without_publishing` | `producer.py:723-730` の `IO_ERROR` 追加 | file/root `fsync` 失敗の個別伝播 |
| `test_batch_records_only_rejections_after_publication_validation` | `producer.py:2187-2190` の per-item `_Reject` 記録 | validation 呼出順、pre-scan `:2144`、例外枝 `:2192` |
| `test_invalid_rejection_history_does_not_replace_assembly_rejection` | `producer.py:2217,2376-2382` の独立 history 保持 | 正常な complete assembly の受理維持 |
| issuer の ledger descendant/exact/loader cases | issuer 固定名集合への追加 | `[publication-root]` parameter は追加名を守らない |
| material-report の recorded scenario | `material_report.py:740-810` の event join、unresolved、非保証 | N06/N07 を別 node に帰属させない |
| material-report の 202/201 scenario | `material_report.py:760-778,1177-1179` | 母数の意味を独立した小 node では検査しない |
| material-report の invalid-ledger scenario | producer の history 独立保持と report 投影 | complete assembly の positive |

反実仮想結果:

- `fcntl.flock` (`producer.py:690`) を削除しても全投影テストは緑。裁定どおり diagnostic であり kill 証拠ではない。
- root/ledger の `O_NOFOLLOW` と regular-file 検査を削除しても緑。既存 M18 は evidence symlink の検査で、ledger symlink には到達しない。
- file/root `fsync` を削除しても緑。呼出回数、順序、失敗時の戻り値を検査する test がない。
- tail の `ftruncate` は削除すると専用 node が赤になり、有効。
- `B4RawRecordDurableRejection.rejection_history_fragment_discarded` は専用 assertion があり有効。
- `B4RawAnalysisRejection.rejection_history` は検査されるが、既に assembly-rejected の入力だけ。
- `B4RawAnalysisAssembly.rejection_history` は正常 report 構築が実際に参照するため有効。
- `B4RawRecordRejectionEvent` と `B4RawRecordRejectionHistory` の具体的な型 identity は未検査。event schema の値と invalid history の `detail` も削除・誤値化して緑。
- `_assert_report_provenance` の producer-history 再照合 (`material_report.py:933-934`) は削除しても投影テストは赤にならない。
- Markdown 新設行のうち event count と rate 以外の history status、各 caveat、unresolved、not-selected 表示は削除しても緑。

実装非依存で緑になる代表は `P::test_mutation_node_mapping_is_complete_and_one_to_one`。これは globals 上の test 名だけを検査し、production code を一切呼ばない。また N05 の `[publication-root]` は新しい固定名を削除しても旧固定名との祖先衝突で緑を維持する。

正例について、N05 の別名 leaf は実際の issue と reload を呼ぶので public API の正例としては有効。ただし gate helper を両側で no-op にしても正例単体は緑で、負例 node が実体を担う。writer/parser は同じ schema 定数を共有し、両側を同じ誤値へ変えても canonical-event test が緑になる coupled oracle がある。N08 には complete assembly + invalid ledger の独立した正例がない。

## 既存テスト期待値の変更有無

- 既存 assertion の変更、反転、緩和、削除、skip、xfail は差分にない。
- material report は既存 `test_m01_m02_...` の旧 assertion 群を維持したまま、同一 node の末尾へ3 scenarioを追加している。
- issuer は既存固定 artifact parameter 4件を維持し、ledger 名を1件追加した。
- producer の既存 M14 は Deferred、planned leaf 不在の期待を維持し、ledger 不在 assertionだけを追加した。
- `test_real_repo_serialization.py` 自体は差分に含まれず、期待値は変更されていない。
- 親実測の既存 M09 4 parameter の赤は期待値変更ではなく、実装側 `report["producer_rejections"]` の後方互換性回帰である。

## nit

- 新しい期待値に working-tree hash、commit、現在時刻の焼き込みはない。issuer commitment は fixture 実値との比較で、renderer の `"0" * 64` は既存の局所 dummy 値。
- canonical-event test は issue の `artifact`、`field`、`detail` を同じ戻り値から作るため、return と ledger が同じ誤値へ動く回帰には独立 oracle がない。
- `test_batch_records_only_rejections_after_publication_validation` は名前が保証する validation precedence より検査範囲が狭い。
- material report の新規検査を既存 M01/M02 node に109行相乗りしたため、失敗局所化と duration attribution が悪い。
- 新設 raw 5 node は `_evidence_scope` を呼ばず、issuer 新設分も pre-RNG または publication 再束縛だけ。material 追加分も3 publicationを作るが assembly は最初の absent leaf で止まり、新しい 201 回 evidence 生成はない。
- 105.78秒のうち本 wave 増分は静的には低い数秒から低い数十秒で、既存 module fixture、201-block publish/assembly、`test_real_repo_serialization` が大半と推定する。単一 aggregate 値から厳密な内訳は出せない。

## 総括

- 現状は既存 renderer 4 node が確実に赤で、受入可能ではない。
- N01〜N05 は直接 anchor があるが、N06/N07 は同一 node、N08 は既存拒否層と重なる。
- N08 は complete 201-leaf positive を追加しない限り R6 の成果物保証を証明しない。
- batch の pre-scan、validation precedence、例外記録には検出力がない。
- tail 修復と fragment field は実効的に検査されている。
- `flock` は裁定どおり diagnostic、`O_NOFOLLOW` と `fsync` は未検査の重要面である。
- 揮発値の焼き込みと既存期待値の改変は見つからない。
- 新設分に重い evidence 生成の反復はない。