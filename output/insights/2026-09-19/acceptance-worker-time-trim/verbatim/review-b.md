## 判定

**NO-GO。** U1 新正例が実測で失敗し、現物にも原因が残っている。
局所修正の範囲には概ね収まるが、focus1 の差を確定削減秒・保守的推定として扱えない。
decorator 修正、正例の整理、同条件 A/B・変異集合の確認後に再判定する。

## 所見

以下、F＝`orchestrator/tests/test_s8b_ratified_freeze.py`、V＝`orchestrator/tests/test_s8b_ratified_verify.py`、R＝`orchestrator/tests/test_run_tests_preflight.py`。行番号は適用後。pytest は実行していない。

1. **must-fix — F:1387：新正例が sealed-process 境界を満たさない。**

   `test_emitter_memo_copy_matches_fresh_build` に `@in_sealed_fixture_process` がない。focus1 の失敗本文も、最初の fresh 構築で `snapshot fork requires exactly one OS thread` と一致する。既存 builder consumer と同じ decorator を付ける修正が必要。

   **放置時の成果物への影響：新側だけ失敗 node が1本増え、memo 同値性の証拠は得られず、変異前の正常対照も成立しない。**

2. **must-fix — [focus1-summary.md:68](/home/SFC/tanab/.claude/jobs/28fa456a/tmp/focus1-summary.md:68)：異条件差を「保守的」と断定している。**

   段1は file 単独、focus1 は9 file 同走。同じ12 workerでも、競合・配置・共有memoの先行構築・待機時間が変わる。特に V は他fileが先に同じkeyを構築すれば、その初回費用を V の外へ移せる。「競合が強いから過小評価」とは決まらない。

   **放置時の成果物への影響：観測差601.428秒／133.725秒を、因果的な削減秒または下限として過大に主張する。**

3. **should — F:1427：正例は5回呼出しだが、prefix構築は3回。安全な削減はまず5→4回。**

   現在は「独立fresh → memo seed → hit → marker破壊後の再構築 → 再hit」。最後の `rebuilt-copy`（F:1440）は通常hitと重複する。削除すれば、独立対照・copy同値性・残骸回復を維持できる。

   「fresh＋hit＋marker破壊後」の3回だけにすると、独立freshとは別にmemoをseedする操作が不足する。freshをmemo missと兼用すると、裁定が要求する**memo迂回との独立比較**が消える。3回への無理な圧縮は勧めない。

   また F:1413 の tracked file ごとの `git cat-file blob` は、既に比較するHEAD・index entries・worktree bytesに対して重複が大きい。blob内容取得を省けば、4回でも多数のsubprocessを削れる。現行0.2秒は最初の構築失敗までなので、正常完走時の正例費用は未測定。

4. **should — R:1403：四象限の全除外は過剰。**

   既存コードは3種のparent preflightを既に差し替え、dispatchも `Mock`。LOCAL枝は実fingerprint→`run_scope`→CHILD_RC、DISPATCH枝も実repo内容を必要としない。`_small_login_repo` を全4枝へ付けても、既存の分岐・assert・parametrizeを維持できる。

   LOCAL 3 nodeはfocus1で計約42.68秒。現行対象の小repo費用から、**追加削減候補は約42.5秒**。これは見積りであり実測削減ではない。DISPATCH枝には小repo構築費だけ増える。

   他の除外は次の判断になる。

   | 旧行→現行 | 判定 | 根拠・追加削減候補 |
   |---|---|---|
   | R:477→498 | 条件付き候補 | 内側 `main` が記録開始へ到達する。auto-record無効化を明示するなら約14.5秒候補だが、fixture追加だけで安全とは確定しない |
   | R:1382→1403 | 含められる | 上記。約42.5秒候補 |
   | R:2314→2335 | 除外維持 | fingerprint非到達。実preflightを残すtestなので、小repo化だけでは同じ検査にならない。今回の方式による削減は見込まない |

5. **should — [ab_compute.sh:26](/home/SFC/tanab/.claude/jobs/28fa456a/tmp/ab_compute.sh:26)、`tools/mutation_harness.py:1967`：memo配置は整合するが、証拠の限界を明記する。**

   - **A/Bは整合する。** 新しいTMPDIR、`--basetemp`不使用なら、通常の `pytest-of-*/pytest-N` 配置をF:1003が拾える。空のpycache prefix、6 file同走、warmup後AB/BA/BA/ABも現物で確認した。コメントに残る「`--basetemp`を指定」は実装と不一致なので訂正する。
   - **変異spec単体にはrunner argv・TMPDIR設定がない。** harnessは各走を別 `Popen` で起動するため、通常配置なら走ごとに新pytest sessionとなる。一方、各mutationでfresh worktreeを作る実装ではなく、同じrepoへ注入・復元する（同:2275、2402）。「fresh session」は整合するが、「各mutationでfresh worktree」は裏付けられない。
   - harnessは `PYTHONPYCACHEPREFIX` を除去するが、注入先のpycacheを実行前にpurgeする。A/Bと同じpycache隔離方式だとは記録しない。
   - A/Bの `memo_keys` はディレクトリ数であり、hit数・構築回数・待機時間ではない。Fの新正例は6 file A/Bに含まれないため、その追加費用は別途受入差へ含める。
   - A/Bは非zero rcでも続行して `ab.done` を作る。完了印を成功判定に使わず、集計時に全走のrcを確認する。

6. **nit — F:1061：観測用metadataが恒常実装へ残っている。**

   `copied_files`／`copied_bytes` の4行はhit処理にもassertにも不要。現在のA/Bもこれを読まない。必要なら測定script側で数え、test helperから削除できる。

7. **nit／裏取り結果 — F:1387、R:101、V:686：authorのAST・caller数は一致。**

   HEADと現物のASTを照合した結果：

   - F **63→64**、V **105→105**、R **113→114**。
   - 既存testの本文・decorator・parametrizeは不変。Rの引数変更は報告どおり8関数。
   - Vの `_build_launch_repo` caller **70関数**、baseline caller **8関数**。
   - 所有外callerは報告どおりoracle_driver、oracle_report、oracle_manifest、verdict、t080 migration。holdoutに直接callerはない。
   - authorイベントログの `DIRECT_CALL_PASS` と終了コード0を確認した。ただし対象は**小git repoによるhelper検査**。本物のbuilder、新正例、worker間共有の成功を示さない。R側が直接呼出し未実行とする報告にも矛盾はない。

## 削減の実測突合表

JUnitを再集計。単位はtestcase時間合計秒、差は段1−focus1。**異条件の観測差**である。

| file | 段1 | focus1 | 差 | 未削減node／残る費用 |
|---|---:|---:|---:|---|
| ratified_verify | 825.316 | 223.888 | +601.428 | selector迂回18 node、g2・追加official run構築 |
| run_tests_preflight | 206.659 | 72.934 | +133.725 | 四象限LOCAL 3 node、警告伝達、full-cap dispatch |
| ratified_freeze | 未計測 | 134.9 | 算出不可 | 新正例失敗。v5 registry後段も各回実行 |
| floor_campaign | 1,319.539 | 未計測 | — | 無変更 |
| p3_b4_producer_auth_experiment | 398.389 | 未計測 | — | 無変更 |
| t1259_qsub_env_delivery_probe | 12.061 | 未計測 | — | 無変更 |
| codex_reasoning_ab | 345.735 | 未計測 | — | 無変更 |

Rのfixture適用14 nodeだけでは **144.714→0.889秒、差143.825秒**。file全体との差には、非対象nodeの増加と新正例約0.1秒が含まれる。

Vのselector迂回18 nodeは **117.655→120.876秒**で、削減されていない。`test_selector_` 以下の対象は：

- `parser_classification_boundary_at_ratified_launch`
- `payload_is_not_exempt_and_conjunction_is_scanned`
- `launch_projection_ignores_current_choice_semantics`
- `launch_rejects_journal_row_decision_drift` の3 parameter
- `launch_rejects_wrong_journal_schema_value`
- `exact_exemption_` 以下の `accepts_declared_three_axis_evidence`、`rejects_nonancestor_pre_oracle_head`、`rejects_executable_h_mode`、`rejects_self_declared_wrong_protocol_sha`、`rejects_declared_sha_mismatch`、`rejects_coherent_wrong_raw_sha`、`rejects_h_worktree_bytes_mismatch`、`rejects_worktree_symlink`、`rejects_prediction_source_blob_hash_mismatch`、`rejects_duplicate_key_document`、`rejects_journal_rows_mismatch`。

静的な呼出し分布を、JUnitのparameter展開数で重み付けすると：

| 範囲 | memo対象呼出し | key／prefix構築の見積り | hit見積り |
|---|---:|---|---:|
| V | default 98回 | 1 key・1構築 | 97/98＝99.0% |
| F既存 | default 27回、perf=False 3回 | 2 key・2構築 | 28/30＝93.3% |
| F＋V既存 | 128回 | 共通default＋degradedの2 key | 126/128＝98.4% |

Vには別にselector迂回18回があり、こちらは都度構築。Fにはreceipt経路7 nodeがあるが、欠落入力の早期拒否を含むため「7回完走構築」とは数えない。

これは正常構築・通常pytest配置を仮定した静的見積り。focus1にはhitカウンタがなく、**実際の構築回数との数値照合は未成立**。Vの大幅短縮と迂回18 nodeの横ばいは見積りと整合する。

所有外では、`test_t080_freeze_migration.py:2152` の `TemporaryDirectory(prefix="t080-layer2-")` はpytest祖先を持たず、memoを迂回する。g2構築や追加official runもU1の共有対象外なので、Vの約7〜9秒の残存nodeをすべてmemo不発と扱ってはいけない。

## 削除候補

| 箇所 | 判断 | 理由 |
|---|---|---|
| F:1061–1064 `copied_files/bytes` | **削除可** | 恒常処理には不要。測定側で代替可能 |
| F:1440 再構築後の再hit | **削除可** | 通常hitと回復を既に別に検証 |
| F:1413 各blobの `cat-file` | **削除可** | HEAD・index・tracked bytes比較で要求を満たせる |
| F:1420 `str(g1)`／`str(topology)` | **直接比較へ簡素化可** | 内容比較に文字列表現は不要 |
| F:1057／1070 key保存・比較 | **削除候補** | digestでentryを選ぶため二重確認。ただし裁定の指定項目なので、削るならplanとの差を明記 |
| F:1003 置き場解決・対象外fallback | **残す** | session寿命とfork間共有を成立させる |
| F:1048 flock | **残す** | 同keyの同時構築・残骸削除競合を防ぐ |
| F:1049–1067 marker・残骸回復・原子的公開 | **残す** | 中断した構築をhitとして扱わない |
| F:1034 全木copy・symlink保持 | **残す** | caller間の変更隔離。whitelist化は不可 |
| F:1036 refresh・status一致 | **残す** | コピー後のgit可視状態を維持する証拠 |
| F:1178 metadataの返却状態、1199再束縛、1376 source needles | **残す** | 後段再実行と構築元path漏洩検出に必要 |
| F:1191 receipt／selector迂回 | **残す** | receiptの別基底と未証明のselector決定性を扱う境界 |
| R:94 function fixture・R:101正例 | **残す** | 約0.1秒で実fingerprintと変更感知を確認。過剰ではない |

新gate・汎用framework・互換層への拡張は確認できない。U1は同一入力構築の共有とcopy、U3/Rは裁定済みの外側入力seamの変更に収まる。

## 総括

まず新正例のsealed-process漏れを直す。
正例は5→4回とblob subprocess削除で整理できる。
四象限の除外は再検討に値するが、selector／receipt迂回は残す。
601.428秒・133.725秒は観測差としてのみ報告し、確定削減秒はA/Bで出す。
authorの静的報告は概ね正確だが、memo実hit率と変異集合の同一性は未証明。