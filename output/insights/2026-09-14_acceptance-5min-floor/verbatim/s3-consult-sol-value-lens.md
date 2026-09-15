## 総括

高コスト群を一括して「研究に不要」とは判定できません。ただし、成果物を直接守る検査と、開発運用・別の比較研究を守る検査は分かれます。  
元の JUnit で **100 秒以上の 37 node、直列和 7,896.801 秒**を確認しました。  
この 37 件で **B3 と証明できたものは 0 件・0 秒**です。B2 の完全な依存閉包も確定できず、毎走から外せる秒数は提示しません。  
**(a)〜(d) に関係し、B1 として保持する集合は 32 件**です。残りは開発運用の 1 件と、別の認証層比較研究を守る 4 件です。  
特に認証層比較は、現行 production の認証機構ではありません。「毎走の価値」を別途問う対象ですが、無価値とは判定していません。  
**D747 単独には頻度変更について空白があります。しかし D532 は skip・selection 縮小を、D700 は T-080 の別 gate 化を明示的に却下しています。**  
T-080 を既定実行から外して実際に腐らせた F485 があり、「高い少数だから外す」だけでは過去事故を再現します。

## A. 高コスト node が守る性質

以下、ファイル略号を使います。秒数は親の §5 の直列和であり、削減可能な wall ではありません。

**分類上の注意:** 「指定の CC 成果物に直接触れない」と「開発者の便宜だけ」は同義ではありません。認証層比較と文献検索には独立した研究成果物があります。この二つを件数稼ぎで (e) に入れず、分類保留としました。

| 略号・file／秒 | 守る性質――何が壊れると赤になるか | 成果物への影響 | 規律2・3の直接の担い手 |
|---|---|---|---|
| F：[test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_s8b_floor_campaign.py)／3,468.8 | 公式床値走の証明書、測定条件、再開、journal・result の対応が崩れると赤になる。 | **(b)(c)(d)**。床値の出所、数値の有効性、同一走への束縛が壊れる。 | admission・改変拒否部分は **2、毎走必須**。file 全件を一律には扱わない。 |
| O：[test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_s8b_oracle_driver.py)／3,414.1 | 不正な凍結・manifest・store 証拠が gate を通る、または検証不成立が正常 outcome になると赤になる。 | **(a)(b)(d)**。未検証の実行・判定を受理し、報告の証拠参照も壊れる。 | **2、毎走必須**。構造化理由の検査もあるが、LLM の次 iteration への入力までを本対象で確認していないため、3を一括認定しない。 |
| X：[test_p3_b4_producer_auth_experiment.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_p3_b4_producer_auth_experiment.py)／1,573.9 | 使い捨て prototype の guard 配置、増分 kill の帰属、比較報告が誤ると赤になる。 | **分類保留**。直接壊れるのは認証層比較の `comparison.json`。現行 CC 選択結果との直接接続はない。 | 現行 production の2・3を直接執行する機構ではない。比較実験の妥当性を守る。 |
| P：[test_run_tests_preflight.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_run_tests_preflight.py)／968.1 | 対象限定走を全走と扱う、削除・RuleOps の拒否を無視する、必要な submodule 準備を飛ばすと赤になる。 | **(a)(b)への間接影響**。検証集合が欠けたまま実装を受け入れる経路を開く。argv 表示・資源配分など運用部分も混在。 | 検査脱落防止部分は **2、毎走必須**。file 全体では混在。 |
| V：[test_s8b_ratified_verify.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_s8b_ratified_verify.py)／841.0 | source、世代、未知性、certificate・journal・result 間の改変を批准・launch 検証が見逃すと赤になる。 | **(a)(b)(c)(d)**。不正な床値・binary・実行証拠を正規の証拠として扱う。 | **2、毎走必須**。 |
| H：[test_check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_check_ai_provenance.py)／783.5 | commit の AI 作業者記録・訂正・免除の監査や、監査実行不能の扱いが崩れると赤になる。 | **(e)：開発運用**。CC の試行台帳そのものの同一性検査ではない。 | 本対象で2・3の直接執行は確認されない。 |
| Q：[test_t1259_qsub_env_delivery_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_t1259_qsub_env_delivery_probe.py)／779.4 | qsub の環境配送を誤って観測・束縛する、または未承認 driver の timeout を正常な拒否と誤認すると赤になる。 | **(e)：投入診断**。診断結果は certified 証拠を発行しない。 | CC 正しさ判定の直接執行ではない。未承認起動の検査は別の重要な境界。 |
| T：[test_t139_submission_path.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_t139_submission_path.py)／749.5 | approved manifest・projection の偽造や差替えが sealed binding を通ると赤になる。 | **(a)(b)(d)**。承認されていない事前登録に receipt を束縛・公開できる。 | **2、毎走必須**。 |
| R：[test_p3_b4_raw_record_producer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_p3_b4_raw_record_producer.py)／655.8 | WAL・terminal receipt からの再導出、on/off 対応、正確な小数、欠測分類が崩れると赤になる。 | **(a)(b)(c)(d)**。材料レポートの数値・採否・元試行との対応が壊れる。 | 判定値再導出・証拠束縛部分は **2、毎走必須**。 |
| L：[test_related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_related_work_search.py)／643.3 | 登録検索母集合、取得件数、応答証拠、再開履歴がずれる、または simulation を本番証拠として受け入れると赤になる。 | **分類保留**。直接守るのは文献調査の証拠と優先権主張。指定された CC 材料レポートとは別。 | CC の2・3を直接執行するものではない。検索実験自身の正しさゲートを含む。 |

**consumer の裏取り**

- **R → 材料レポートは直接接続**しています。[p3_b4_material_report.py:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/campaign/p3_b4_material_report.py:238) が `assemble_b4_raw_analysis` を呼び、その bytes と `source_artifact_bytes` を `evaluate_b4_artifacts` へ渡します。
- **T → receipt 公開も直接接続**しています。[_writer.py:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/submission_gate/_writer.py:71) は公開前に `binding.assert_intact` を呼び、意味検証後にも再検査します。
- **H の consumer は開発運用**です。`check_ai_provenance` の参照は land・wait・task check・dispatch・mutation harness 等にあり、`campaign`・`submission_gate`・`preregistration` の CC 成果物 consumer に同 checker の参照はありません。
- **Q の結果は `diagnostic-only`**です。[probe 本体:647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/tools/pegasus/probes/t1259_qsub_env_delivery_probe.py:647) は観測 JSON と補助 `result.json` を出し、`official_campaign_executed=False` を記録します。R1 は公式 driver を実行せず、R2 は未承認の早期拒否だけを検査します。上記 CC consumer 群には専用 schema・module の参照がありません。
- **X は production 認証層ではありません。** [実装冒頭](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/campaign/p3_b4_producer_auth_experiment.py:1) の宣言どおり、guard は disposable tree への prototype patch 後だけ呼ばれます。現行 issuer・raw producer・material report に同 module の参照はありません。
- **L の接続先は `tools/run_axis3_search.py`**です。CC consumer 群に参照はありませんが、ロードマップ §7 は文献調査を論文の位置付け・優先権主張に使うため、単なる開発便宜とは分類できません。

次が **37 node の具体的な判定**です。表中の node 名は先頭の `test_` を省略し、`{…}` は列挙した suffix の展開です。

| ID／node または node 群 | 件数 | 守る性質・壊れる成果物 | 規律2・3 |
|---|---:|---|---|
| G1 O：`t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5` | 1 | draft→発行→履歴検証→public gate→report の観測 envelope が接続し、receipt 消失が報告側でも不正になる。**(a)(b)** | 2・必須 |
| G2 O：`t080_stub_free_e2e_single_defects_have_single_exact_reason_b5` の4 parameter | 4 | known/holdout artifact、CCBench checkout、holdout 漏洩の各変異を、現行 hold／解除状態に従った単一理由で扱う。**(a)(b)** | 2・必須 |
| G3 O：`t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5` | 1 | source/design closure、metadata、schema、pairing、gitlink、陽性対照等の不正を対応する理由で拒否する。**(a)(b)** | 2・必須 |
| G4 O：`t080_full_valid_history_defects_have_one_baseline_reason_f28` の3 parameter | 3 | 不正な人間 trailer、発行 commit の余分な path、receipt 改変後の復元を拒否する。**(b)** | 2・必須 |
| G5 O：`t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28` | 1 | 発行済み receipt を削除しても「未発行」に戻して再発行できない。**(b)** | 2・必須 |
| G6 F：`real_output_snapshot_{detects_git_visible_real_output_changes,excludes_git_ignored_real_output_changes,git_index_fast_path_matches_reference}`、O：`t080_output_snapshot_excludes_git_ignored_real_output_changes` | 4 | Git-visible な変更を見逃さず、ignored な活動を誤検出せず、snapshot 最適化後も変更・復元・untracked 追加を区別する。実 output の非汚染検査を介し **(b)(c)(d)を間接保護**。 | 直接の verifier ではない |
| G7 F：`official_fresh_issues_certificate_and_binds_wall_ledger` | 1 | certificate hash と run ID・journal・wall ledger が一致する。**(b)(d)** | 証拠束縛を保護 |
| G8 F：`official_scan_rejection_has_zero_filesystem_side_effects` | 1 | clean scan 拒否後に測定・出力を開始しない。**(b)(d)** | 2・必須 |
| G9 F：`official_build_failure_leaves_durable_launch_start` | 1 | build 失敗でも launch-start と証明書を残し、同じ走として再開する。**(b)(d)** | 直接の verifier ではない |
| G10 F：`official_resume_validates_certificate_and_completes` | 1 | 正当な中断走が証明書を維持して完了し、再凍結適格へ誤昇格しない。**(b)(c)(d)** | 受理境界の正例 |
| G11 F：`official_resume_rejects_{tampered_certificate,renamed_run_dir,certificate_time_not_bound_to_run_id}` | 3 | 証明書 bytes、run 名、証明書時刻の各差替えを再測定前に拒否する。**(b)(d)** | 2・必須 |
| G12 F：`pilot_resume_rejects_launch_certificate_contamination` の3 parameter | 3 | pilot の証明書 file／launch-start／campaign-key への公式証拠混入を拒否する。**(b)(d)** | 2・必須 |
| G13 F：`pilot_path_has_no_launch_certificate_changes` | 1 | pilot に公式証明書・証明書参照を付けず、再凍結不適格を維持する。**(b)(c)(d)** | 受理境界を保護 |
| G14 X：`each_prototype_patch_anchor_is_unique_and_anchor_is_post_prototype`、`prototype_calls_each_guard_once_from_the_fixed_real_callsite` | 2 | 比較する各 prototype の実 bytes・guard 配置が登録どおりである。直接の成果物は認証層比較報告。 | 現行 production の直接防壁ではない |
| G15 X：`wave_mutant_kills_exactly_one_registered_node[w07]` | 1 | W07 変異が登録対象だけを殺し、別原因の失敗を kill と数えない。直接の成果物は比較実験の妥当性。 | 同上 |
| G16 X：`case_failure_records_aborted_and_remaining_cases_continue` | 1 | 13 case 中の1件の例外を ABORTED と理由付きで残し、残り12件を失わない。直接の成果物は比較報告。 | 同上 |
| G17 `test_s1_known_axes_freeze.py`：`historical_oracle_nonadapter_reaches_current_semantics` | 1 | historical 経路でも現行 generator の意味変更を oracle gate が検出する。**(a)(b)** | 2・必須 |
| G18 `test_s8c_preregistration_predicates.py`：`current_repository_snapshot_has_zero_satisfied_predicates`、`repository_candidate_uses_real_s8c_budget_module` | 2 | 現状の発効条件・未証明 budget を誤って充足済みにしない。**(a)(b)(d)**。前者の現行期待値は名前に反して **C10 のみ充足**。 | admission 防壁として2・必須 |
| G19 R：`positive_201_block_{all_terminal_records_absent,certified_preserves_decimal_and_all_pair_protocol_bindings}` | 2 | 201 block／402 arm の欠測分類・固有証拠・小数 lexeme・割付を保持し、実評価器まで通す。**(a)(b)(c)(d)** | 2・必須 |
| G20 H：`provenance_headroom_short_queue_unavailable_cap_oom_stops` | 1 | メモリ不足かつ queue 不可なら、監査を無理に再 dispatch せず実行不能として返す。**(e)** | 直接の2・3ではない |
| G21 `test_t2187_adaptive_const_probe.py`：`public_certification_creates_group_only_after_all_24_requests` | 1 | 24 workload/slot が揃う前に group 証明を発行せず、揃うまで trace を残す。**(a)(b)(d)** | 2・必須 |
| G22 T：`normal_resolver_binding_rechecks_projection_blobs` | 1 | binding 発行後に vector-index の digest を差し替えても再検査で拒否する。**(a)(b)(d)** | 2・必須 |

G6 は test helper の検査ですが、その consumer は G7〜G13 等の実 output 非汚染 assertion です。**production から import されないことだけで (e) にはしていません。**

## B. 毎走必須／変更依存／走ごとに不変の三分

B1 への保守的分類と、規律2による毎走義務を区別します。**入力が走ごとに変わり得ることだけでは、検査の研究価値の高さまで証明できません。**

| node 群 | 判定 | 根拠の実体 | B2 の依存 path |
|---|---|---|---|
| G1〜G5 | **B1・毎走必須** | O の `_build_t080_stub_free_e2e_repo` は現行 `orchestrator`、Git-visible な `output`、発行済み receipt の歴史 blob、実 submodule を読み、Git と子 Python を起動する。hold の解除状態も検査する。 | 有限の完全閉包を確定していない |
| G6 | **B1へ倒す** | 実 Git ignore 規則、index、untracked、ファイル bytes／metadata が入力。O の snapshot は mtime・ctime 等も扱う。同じ commit だけでは状態が固定されない。 | `.gitignore` と helper だけでは閉じない |
| G7〜G13 | **B1**。拒否防壁は毎走必須 | 測定値・時計の一部は固定注入されるが、各 node は `_real_output_snapshot()` で実 `output` を前後比較する。certificate／journal の実ファイル入出力も通る。 | campaign file だけでは閉じない |
| G14〜G16 | **B1相当の入力依存**。ただし指定成果物との分類は保留 | `ScratchTree` は Git archive・tar・HEAD・作業ツリー overlay を読む。G15 は子 `run_tests.py`、G16 は `time.monotonic()` と実 repository status を読む。 | 閉包未確定。B3ではない |
| G17 | **B1・毎走必須** | 実 `DEFAULT_FREEZE_PATH` と現行 generator を oracle gate に渡す。historical 記録だけの比較ではない。 | 閉包未確定 |
| G18 | **B1・毎走必須** | `current_commit_snapshot` は実 HEAD の評価・Git archive を行う。候補 fixture は実作業ツリーの対象 path を別 index に add し、`commit-tree` する。 | 候補には `s8c_budget.py`、`s8b_ratified_freeze.py`、`p3_autonomous_workload_trial.py` 等があるが、全評価閉包は未確定 |
| G19 | **B1・毎走必須** | `_build_full_publication_evidence` は issuer が**乱数化した schedule**を使い、実証拠1 block と writer 経由の複製を作る。固定201件であることは固定入力の証明にならない。 | 閉包未確定 |
| G20 | **B1相当**、(e) | 資源判断は mock だが、`provenance.main` 内の `_tree_and_submodules_fingerprint` は実 Git status・diff・recursive submodule を読む。 | checker file だけでは閉じない |
| G21 | **B1・毎走必須** | fixture は build/run を置換するが **verifier CLI は実物**。Git diff、submodule、PBS/TMPDIR、trace・receipt の実入出力を使う。 | 閉包未確定 |
| G22 | **B1・毎走必須** | `_authority_fixture` は実 repo を clone し、Git commit と承認 blob 読取を行う。`assert_intact` は root の inode と現在 HEAD も検査する。 | `_binding.py` だけでは閉じない |
| 上位fileの Q・L | **file丸ごとのB2/B3は不可** | Q は module fixture の実 repo snapshot、subprocess、観測時刻を読む。L の seal は `enforce_head=False` でも HEAD を解決し、Python・jsonschema の版を記録する。 | file 単位の完全閉包は未確定 |

**高コスト37件の B3 は、確認できた範囲で0件・0秒です。**

なお V の `test_equality_chain_each_edge_{raw_tamper_rejected,coherent_island_rejected}` は、固定 adjacency と文字列辞書だけで判定する例です。JUnit では **58 node・合計0.058秒**でした。しかし証拠の束縛を壊す変異への直接検査なので、依頼の規律2優先条件により毎走側へ残します。高コスト群の反復負担を説明する B3 ではありません。

## C. D747 の射程

逐語の正本は [rulings-verbatim.md](/home/SFC/tanab/.claude/jobs/f7379c7e/tmp/wave-acceptance-5min-floor/rulings-verbatim.md) です。

| D747 の理由 | 今日への判定 |
|---|---|
| 「**全テストの54%を消しても wall は0.3秒しか縮まない**」 | **今日の高コスト37件への反論にはならない。** 当時の「0.01秒未満7750件、合計15.1秒」の算術であり、今回の対象集合が異なる。ただし安い集合についての当時の事実を否定するものではない。 |
| 「**削減した直列秒数の1/48しか wall に効かない**」 | **今日への適用条件が成立していない。** 前提は D746 後の makespan と work 下界の一致。今日の shard-0 は work/48 が約272.4秒、最大単体310.177秒、実行窓313.6秒で、一致していない。 |
| 「**削減で得られる余地は最大でも422秒＝wall 8.8秒**」 | **今日の上限ではない。** 5364.9秒の総workと102.98秒の排他鎖から導いた値。今日の総work・最大単体・shard配分へ流用できない。 |
| 「**高コスト側を実ファイルで確認したが、削除できるものは1件もなかった**」 | **算術ではなく、当時の意味的判断。現在の全対象への一般化は未証明。** 今回も中核の証拠・受理検査を外せる根拠は得られなかった。一方、認証層比較・開発運用・文献検索まで一律に同じ価値とは言えない。 |

したがって、**「安い大量削除への算術は、高い少数の検討を否定しない」という区別は成立します。しかし「D747の理由は算術だけ」は成立しません。** 第4理由と、次の却下理由が残ります。

> 「所要だけで削除候補を決める — subsume を証明できない削除は検出力を落とす。」

D747 は B2／B3 の実行頻度を明示的に論じていません。**D747 単独には新しい裁定が必要な空白があります。** ただし、既裁定全体が空白という意味ではありません。

- [D532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/docs/decisions.md:21928) は「**テストの削除・skip・selection の縮小で速くする — 規律2に反する。検討対象にしない**」と明記。
- [D700](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/docs/decisions.md:27653) は T-080 を既定全走へ戻し、「**受入とは別 gate で定期実行する**」も却下。
- D690 は「**緑のテストの退役はこの決定の対象外**」とし、別の人間裁定経路を指定。

頻度変更を裁定へ返すなら、**D747 の空白だけでなく、D532、対象によっては D700 との関係も明示する必要があります。**

D747 の限界、

> 「『安いテストを減らしても wall に効かない』は未証明」

も関係します。これは collection・送信・完了event等の費用を15.1秒に含めていなかったという留保です。**直列和だけで総wall効果を断言してはいけない**という点で今回にも適用されますが、高コスト検査を外す価値判断の根拠にはなりません。

## D. 触ってはいけない集合と、外すと再発する事故

**今回の37件中、保持する集合は G1〜G13、G17〜G19、G21〜G22 の32件**です。

| file | 該当ID | node数 |
|---|---|---:|
| `test_s8b_oracle_driver.py` | G1〜G5、G6のO | 11 |
| `test_s8b_floor_campaign.py` | G6のF、G7〜G13 | 14 |
| `test_s1_known_axes_freeze.py` | G17 | 1 |
| `test_s8c_preregistration_predicates.py` | G18 | 2 |
| `test_p3_b4_raw_record_producer.py` | G19 | 2 |
| `test_t2187_adaptive_const_probe.py` | G21 | 1 |
| `test_t139_submission_path.py` | G22 | 1 |

これは依存閉包未確定による保守的保持を含みます。32件すべてが anomaly verifier そのもの、という主張ではありません。

**除外との因果が最も直接的な事故は F485 です。**

- **F485［テスト代表性］［手順漏れ］**：T-080 stub-free E2E 11 node をコスト理由で opt-in 化。11日後の実行で2件の赤が発覚し、凍結検証保留への追随漏れを隠していました。G1〜G5を「歴史的fixtureだから別走でよい」とする判断への直接の反証です。
- **F240［恒真ゲート］［テスト代表性］**：凍結同一性検査と、holdout漏洩・陽性対照・admission・pairing が同じ関数に同居していました。G2・G3を「保留中のpin検査」として一括退役すると、保留対象外の防壁まで消す型です。
- **F487／F488／F620［測定の交絡／計測汚染］**：fixture・変異走行・正例test自身が実 `output` を汚染しました。G6と、G7〜G13の前後snapshotには実事故由来の目的があります。
- **F739［TOCTOU］［恒真ゲート］**：lockの分類とreceipt検証を別々に読み、G4未実行のCOMMITを受理できました。Rの `test_m05_campaign_lock_classification_and_receipt_share_one_byte_buffer` 等を含む束縛検査は、この実在型に対応します。**201-block正例だけでF739を止めるとは認定していません。**
- **F899［恒真ゲート］［未実測］**：Qのqstat解析がSTTでなくPriを読み、合成fixtureも同じ誤りを共有していました。現在の `test_request_receipt_accepts_measured_qstat_layout` は実機出力を使う再発検査です。診断専用でも、外せば無害とは言えません。
- **F521［手順］［関門順］**：参照関係による焦点走がrepo全体checkerを拾わず、受入全走を浪費しました。単純な「変更fileを参照するtestだけ」でB2を実装できる、という根拠を否定します。

逆に **F961 の再発防止を、上位の公式走testだけで証明したとは言えません。** G7等の `_official_test_seam` は clean scan をstubしています。実際のversioned protocolとallowlistの接続まで守るという過大評価はしません。

## E. 読めなかった file／確かめられなかったこと

必読2fileと上位10file、37 nodeの本体は読めました。調査中に仮定した次のpathは存在せず、読めませんでした。

- `orchestrator/preregistration/approved_manifest.py`
- `orchestrator/campaign/s8c_preregistration_core.py`
- `orchestrator/submission_gate/_receipt.py`
- `orchestrator/campaign/t2187_adaptive_const_probe.py`

対応する実体は `_manifest.py`、`s8c_preregistration.py`、`_writer.py`、`tools/pegasus/probes/t2187_adaptive_const_probe.py` で確認しました。

残る限界は次です。

- **pytest・性能測定は実行していません。緑の認定はありません。**
- nodeと秒数は指定sessionの3つのJUnitから取得しました。測定tipは `abbef52…`、読んだHEADは `9de7385…`。対象13 test fileには両commit間の差分がありませんが、productionの全依存閉包の同一性までは監査していません。
- 上位10fileの全nodeについて、個別の依存閉包を完全証明した調査ではありません。したがって **B3がrepo全体に存在しない、とは主張しません。**
- §6の「最小268.9秒」と「57走すべて300秒以上」は矛盾しています。57走分の原資料は再集計していません。
- 37件の秒数にはfixture費用も含まれます。**費用をそのnodeのassert自体の価値と対応付けたり、削除時のwall短縮量へ換算したりしていません。**
- 認証層比較4 nodeは合計 **643.743秒**ですが、これは研究支援検査の費用です。直接consumerの不在は確認できても、退役可能性・代替検出力・毎走を止める利益までは証明できていません。