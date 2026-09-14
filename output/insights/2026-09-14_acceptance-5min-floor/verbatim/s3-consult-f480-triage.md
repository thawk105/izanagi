## 総括

**推奨は、22 件の足場の上界を局所的に広げ、均等化を維持すること。**
21 件の launcher 外側 watchdog を **10 → 60 秒**、うち17 件の `max_wall` を **3／8／10／11 → 30 秒**へ変更する。
互換検査4 件の `max_wall=100` は据え置き、残る manifest lock 検査1 件の待機 watchdog は **2 → 30 秒**とする。
**`max_wall` 自体が検査対象の性質で、拡張禁止となる node は0 件。** ただし `thread_missing_after_grace` の **`evidence_grace=0.3` は変更禁止**。
manifest 生存中追記の1 件は、上界延長に加えて **0.5 秒の sleep を明示的な解放待ちへ変更**し、生存中という assert を保つ。
これはテスト入力・足場の局所修復であり、製品の受理規則変更ではない。実行はしておらず、緑・300 秒達成は未確認。

## A. 22 件の弁別

以下、`T` は [orchestrator/tests/test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_codex_worker_launch.py) を指す。node はすべて同ファイル内。

値の表記は **W＝launcher の `max_wall`、S＝外側の subprocess watchdog**。checker を起動する node は、その明示的な `timeout=10` も S の変更対象とする。

| node | assert している性質 | 上界は性質か足場か | 根拠 | 広げるなら値 |
|---|---|---|---|---|
| `test_failure_class_enum_and_receipt_recomputation_are_closed` | 未知・欠落・偽装された failure class と accepted attempt の不整合を拒否する。 | W・Sとも足場 | 判定は class と再計算結果。時間を無制限にしても偽装拒否の検査は残る。`T:3394` | W10→30、S10→60。2 回の launcher と3 回の checker が対象。 |
| `test_launcher_failure_diagnostic_is_wired_to_the_returncode_assertion` | run・Popen・in-process の3 経路が診断 formatter を正しいオブジェクトで呼ぶ。 | W・Sとも足場 | sentinel・呼出数・引数型を検査している。`TimeoutExpired` は期待する `CompletedProcess` を作れなかった足場の失敗。`T:2913` | 3 経路のW11→30、run／communicate のS10→60。 |
| `test_check_receipt_reads_v3_parent_attempt_field_sets_without_upgrade[wave-parent]` | failure class 付きv3 receipt を変更せず読める。 | W・Sとも足場 | schema と読み取り前後の bytes 一致が判定対象。`T:6500` | W100据置、S10→60。 |
| `test_check_receipt_reads_v3_parent_attempt_field_sets_without_upgrade[main-parent]` | failure class のないv3 receipt を変更せず読める。 | W・Sとも足場 | 上と同じ検査で、欠ける field が異なる。`T:6500` | W100据置、S10→60。 |
| `test_launcher_failure_diagnostic_reports_incomplete_evidence` | evidence 欠落が診断本文と末尾の truth summary に出る。 | W・Sは足場 | assert は `missing` と診断の構造。Wを無制限にしても evidence deadline が欠落を検出する。`T:2802` | W11→30、S10→60。evidence grace は維持。 |
| `test_max_attempts_never_spawns_extra_attempt` | 上限2 回で停止し、第3 attempt を生成しない。 | W・Sとも足場 | stop reason、counter、attempt 数、leader 数を検査する。Wを外しても回数制限の検査は残る。`T:5228` | W11→30、S10→60。`max_attempts=2` は維持。 |
| `test_checker_rejects_v3_acceptance_with_prior_invalid_attempt` | 先行 invalid attempt がある receipt の accepted 偽装を checker が拒否する。 | W・Sとも足場 | 改ざん後の rc2 と truth-table 診断が対象。`T:4208` | W既定3→明示30、launcher／checker のS10→60。 |
| `test_cumulative_limits_do_not_reset_between_attempts` | model-call 数が attempt を跨いで累積され、2 回目で上限2 に達する。 | W・Sとも足場 | assert は `max_model_calls`、累積2、各 attempt の trigger。壁時計の累積はこの node の assert ではない。`T:5172` | W11→30、S10→60。`max_calls=2` は維持。 |
| `test_check_receipt_reads_v4_without_evidence_issues` | `evidence_issues` のないv4 receipt を変更せず読める。 | W・Sとも足場 | schema4、rc0、bytes 不変を検査。`T:6536` | W既定3→明示30、S10→60。 |
| `test_all_v3_stages_reject_prior_invalid_attempt[author-None]` | author の最終 attempt が accepted でも、先行 invalid により job 全体を拒否する。 | W・Sとも足場 | `invalid, complete`、最後の accepted、全体 not_accepted の組合せが対象。`T:4180` | W既定3→明示30、S10→60。 |
| `test_check_receipt_recomputes_usage_actuals_from_sealed_artifacts` | receipt 内の model-call 数を0 に偽装しても、封印済み証拠から再計算して拒否する。 | W・Sとも足場 | rc2 と再計算診断が対象。`T:6623` | W既定3→明示30、S10→60。 |
| `test_authority_bound_job_rejects_prior_invalid_attempt` | authority に束縛された review job でも先行 invalid を全体受理で隠せない。 | W・Sとも足場 | attempt 列と job outcome の関係が対象。`T:4151` | W既定3→明示30、S10→60。 |
| `test_all_v3_stages_reject_prior_invalid_attempt[consult-sol]` | consult-sol の最終 attempt が accepted でも、先行 invalid により job 全体を拒否する。 | W・Sとも足場 | author と同じ拒否条件を別 stage/lane で検査。`T:4180` | W既定3→明示30、S10→60。 |
| `test_thread_missing_after_grace_kills_process_group` | thread evidence 欠落を grace 後に強制停止し、SIGTERM の発行と process group の消滅を確認する。 | **W・Sは足場、evidence grace は性質** | Wを無制限にしても0.3 秒の evidence deadline が作動する。逆に grace を無制限にすると `evidence_forced_stop=True` の検査経路が失われる。`T:7236` | W11→30、S10→60。**grace0.3・termination0.05 は維持。** |
| `test_check_receipt_detects_executable_identity_change` | receipt 発行後の fake executable 改変を checker が拒否する。 | W・Sとも足場 | executable の同一性とrc2 が対象。`T:7372` | W8→30、S10→60。 |
| `test_positive_p1_normal_job_is_accepted` | 正常 job の受理、authority・証拠・出力・manifest・終了状態が整合する。 | W・Sとも足場 | 時間の scope 名は検査するが、3 秒という数値や経過時間上限を assert していない。`T:3178` | W既定3→明示30、S10→60。 |
| `test_check_receipt_reads_v1_field_sets_with_explicit_skip_diagnostics[True]` | 旧v1 field 集合を読み、欠けた検査について4 個の互換診断を出す。 | W・Sとも足場 | schema と skip 診断を検査し、コメントも admission を律速にしない意図を明記する。`T:6362` | W100据置、S10→60。 |
| `test_launcher_failure_diagnostic_reports_nonzero_codex_exit_code` | fake の終了コード7 が失敗 predicate として診断される。 | W・Sとも足場 | 診断文字列が対象。所要時間を変えても終了コードの検査は残る。`T:2780` | W既定3→明示30、S10→60。 |
| `test_check_receipt_reads_v2_parent_attempt_field_sets_without_upgrade[main-parent]` | failure class のないv2 receipt を変更せず読める。 | W・Sとも足場 | schema2・rc0・bytes 不変を検査。`T:6416` | W100据置、S10→60。 |
| `test_f43_heading_missing_is_classified` | 正常終了しても必要見出しのない出力を validator が拒否し、`f43_fragment` に分類する。 | W・Sとも足場 | exit0・validator1・class の組合せが対象。`T:3249` | W10→30、S10→60。 |
| `test_manifest_is_appended_while_correlated_session_is_running` | 対応する fake process が生存している間に manifest entry が公開される。 | W・S・観測期限は足場。**生存中という順序条件は性質** | 観測期限を無制限にしても `/proc/<leader>` の生存 assert は残る。ただし現状の0.5 秒 sleep は観測窓を閉じる。`T:6998` | W8→30、S10→60、観測3→30。併せて解放待ちへ変更。 |
| `test_manifest_lock_covers_load_replace_critical_section` | 第1 job の critical section 中に第2 fd が実際に lock 競合し、解放後にだけ第2 job が進む。 | 待機上限は足場 | `LOCK_NB` の競合、未進入、因果 trace、最終2 entry が直接の検査。2 秒を無制限にしてもこれらは残る。コメントも watchdog と明記。`T:5927` | 5 箇所の待機2→30。lock・trace の assert は維持。 |

**数値の由来は設計上の余裕であり、実測 percentile ではない。**

- **W30 秒**：対象の小さい既存Wの最大11 秒に、親が報告した仕事密度約2 倍と追加余裕25%を置くと `11 × 2 × 1.25 = 27.5` 秒。切り上げて30 秒を選ぶ。密度から個別 latency を予測できると主張するものではない。
- **S60 秒**：W30 秒の内側判定に、起動・終了・証拠処理用としてさらに30 秒を持たせる有限 watchdog。これは全 lifecycle が必ず60 秒に収まるという保証ではない。
- **lock／観測30 秒**：足場の待機値を上記30 秒へ揃える局所的な選択。正常時に30 秒 sleep する変更ではない。
- **W100 秒**：既に互換検査を admission 上界から分離するために明示されている。今回さらに広げる理由はない。
- F766 の **120 秒をそのままコピーしない**。あちらの根拠は実 conftest をロードする子 pytest session の実測4.25 秒で、今回の各 launcher の所要分布とは別である。

## 上界の出所

**1 箇所を直せば22 件すべてに効く、という構造ではない。**

| 出所 | 対象・意味 |
|---|---|
| `T:1138` | `_run_launcher_subprocess` の `subprocess.run(timeout=10)`。22 件中20 件がこの経路を使用する。 |
| `T:1159` | `_communicate_launcher` の `communicate(timeout=10)`。diagnostic wiring と manifest 生存中追記が使用する。 |
| `T:1214` | unordered 用の別 watchdog。**今回の22 件には不要なので変更しない。** |
| `T:1598` | `_base_command` の `max_wall="3"` 既定値。 |
| `T:1654` 付近 | `max_wall` を `--wall-clock-admission-bound-s` として製品CLIへ渡す箇所。 |
| `T:1698` | `_run_case` が kwargs を `_base_command` へ渡し、外側の helper を呼ぶ。 |
| `T:3401,3441,3254` | W10 の明示箇所。 |
| `T:2806,2932,2939,2962,5183,5237,7241` | 対象nodeのW11 明示箇所。 |
| `T:7002,7376` | 対象nodeのW8 明示箇所。 |
| `T:6367,6420,6504` | 互換4 node のW100。 |
| `T:3412,3421,3431,4239,6395,6442,6528,6552,6638,7383` | 各nodeが直接呼ぶ checker の `timeout=10`。共通 launcher helper の修正では変わらない。 |
| `T:5967,5974,6030,6050,6051` | manifest lock の queue／Event／join の2 秒。launcher を起動しない独立した足場。 |
| `T:7012` | manifest 出現を待つ3 秒。 |
| `T:7242` | **維持する性質側の `evidence_grace="0.3"`。** |
| `T:2401` | `_assert_pid_gone` の3 秒。今回提示された失敗署名の修理対象には含めない。 |

製品側では [tools/codex_worker_launch.py:2267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/tools/codex_worker_launch.py:2267) が wall、model calls、tokens の制限を判定し、同ファイルの `2296` 付近で別途 evidence deadline を判定する。この分離が、thread 欠落検査で **Wだけを広げられる根拠**になる。

## B. 規模の判定

[DW-G03](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/docs/dev-wave/core.md:69) が対象にしているのは**族全体への制度一般化**である。同じ helper の単一欠陥を修正した結果22 caller に効くなら、件数だけで制度一般化にはならない。

ただし今回は、その仮定自体が成立しない。共通 subprocess watchdog、個別checker、CLI入力W、lock待機、manifest観測窓が混在する。したがって「1 箇所の修理」とは記録せず、**同じファイルの22 nodeを個別に監査した局所修復**と記録する。22 件の同時発火を「独立22 例」と数える必要もない。

[F766](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/docs/failures.md:21009) と同型なのは、検査対象でない watchdog を延長する部分である。CLI入力Wの変更も今回の17 nodeでは同じ区別に基づくが、**製品に渡すテスト入力を変える点は、単純な外側 timeout 延長と区別して記録する**。manifest の解放待ちはさらに別の、観測競争を除く修理である。

受理集合については、次を区別する。

- **製品の固定入力に対する受理規則は変わらない。** 製品コード、receipt truth table、回数・token制限、evidence deadlineの意味論を変更しない。
- **テスト実行の時間付き履歴の集合は広がる。** 従来10 秒超で足場が失敗していた履歴にも、本来のassertまで進む時間を与える。これはF766と同じ意味での変更である。
- CLIのW入力が変わるテストでは、そのfixture jobの許容時間も変わる。しかし各nodeの検査命題は時間値ではない。対して、`T:6455` のv2境界検査が持つ **100／100.001 の受理・拒否境界**は変更しない。

以上の限定なら、新しい受理規則の裁定は不要と判断する。

## C. 却下すべき案とその理由

| 案 | 判断・理由 |
|---|---|
| 22 件を hold 登録 | **採らない。** 足場を修理できるのに検査を実行対象から外す理由がない。現物の [flaky_test_holds.py:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/flaky_test_holds.py:146) はcanonical F節に関数名だけでなく failure signature も要求する。新しい証拠がfragmentにしかない場合のF766の循環は残っている。ただし「22 件すべて登録不能」とまでは確認していない。 |
| 削除・skip | **採らない。** [D532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/docs/decisions.md:21928) が明示的に却下しており、今回の個別assertにも保持すべき検出対象がある。 |
| worker 数を減らす | **採らない。** 足場の問題に受入全体の並列度変更を持ち込む必要がない。D532も増減を提案しないと定め、D1620の測定面は既定worker数を含む。今回の構成で減らせば何秒になるかは未測定なので、必ず遅くなるとの実測主張はしない。 |
| 均等化をやめる | **採らない。** 親の報告では最遅shardを27.3 秒短縮した変更であり、足場修復を先に行う合理性がある。撤回後に正確に334.2 秒へ戻るとは断定しない。 |
| 22 件を同一xdist groupへ入れる | **第一選択にしない。** そのgroup内の同時実行は減らせても、他worker由来の負荷を隔離できず、直列鎖を新設する。 |
| graceや生存assertも一括緩和 | **採らない。** evidenceによる停止、終了前のmanifest公開という検査命題を変えてしまう。 |

## D. お前の推奨

親が実装する変更は **テストファイル内に限定**し、次の形にする。

1. **対象callerに明示的な外側予算を渡せるようにする。**  
   `T:1124` と `T:1151` のhelperへ `timeout: float = 10.0` を追加し、`T:1138,1159` で使用する。`T:1698` の `_run_case` にも同引数を追加し、`_base_command` のkwargsへ流さず subprocess helperへ渡す。対象21 nodeの呼出しだけ `timeout=60.0` を指定する。共通既定値の一括変更はしない。

2. **表の17 nodeでWを明示30へ変更する。**  
   `T:1598` の既定3は据え置き、既定を使用する対象callerには `max_wall="30"` を明示する。W100 の4 nodeは保持する。checkerの直接呼出しも、表の対象nodeに限って `timeout=60.0` とする。v1の`False`、v2の`wave-parent`まで今回の変更を広げない場合は、parameterに応じて60／既定10を選ぶ。

3. **manifest lockの5 箇所を30 秒へ変更する。**  
   `T:5967,5974,6030,6050,6051`。既存コメントを「順序期待ではなく失敗回収のwatchdogである」旨と数値根拠に更新する。非blocking競合probeと完全な因果traceは保持する。

4. **manifest生存中追記の観測競争を除く。**  
   `_write_fake_codex` の `mode == "manifest_while_running"` にある `time.sleep(0.5)` を、**このmode専用の解放marker待ち**へ変更する。待ちは30 秒で失敗終了させる。`T:6998` の親testはmanifestとleader生存を確認した後にmarkerを作り、fakeを終了させる。`T:7012` の観測上限も30 秒へ変更する。例外時にも子を回収する。**manifestを子終了後にしか追記しない実装では失敗する構造を保つ。**

5. **性質側の値とassertは保持する。**  
   `evidence_grace=0.3`、termination grace、model-call／attempt上限、failure-class拒否、sealed-artifact再計算、互換bytes不変、PID消滅、manifestの生存条件を緩めない。互換testの「W > 10」コメント・assertは、明示watchdogを参照する形へ整える。

実装後は、manifestの「子終了後に追記する」負例とlockの「排他を外す」負例が引き続き落ちることを重点確認し、対象テストとcanonical受入を `tools/run_tests.py` 等の既定経路で確認する。**上界の延長自体は高速化ではないため、300 秒達成は受領証で別途判断する。**

## E. 読めなかった file / 確かめられなかったこと

- 必読の `rulings-verbatim.md` は16 件すべて読めた。
- 調査中に誤って開いた `orchestrator/flaky_test_holds.py` は存在しなかった。正しい `orchestrator/tests/flaky_test_holds.py` を読み、契約を確認した。
- pytest・性能測定・編集は行っていない。
- 54 走、今回の22 件の全失敗artifact、shard所要の一次資料は再確認していない。これらは親の提示した観測として使用した。
- **30／60 秒で全22 件が緑になること、grace競争が残らないこと、最遅shardが300 秒以内になることは未確認。** 推奨値は有限の修理予算であり、測定済みの保証値ではない。