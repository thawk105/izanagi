## 所見

検査基準は HEAD `947fd160ab44e6ae82b6eab56ee8d70813fda31d`。必読射影はすべて読取可能。静的検査のみで、pytest・変異実行の合格は主張しない。以下、`test_*.py` は原則 `orchestrator/tests/` 配下。

**A-1 — must-fix：P1 の「項 5 優先」は成立しない。**

- 対象：`s1-brief.md:51`、`docs/decisions.md:68594`・`:68612`、`test_t1434_t1222_science_slice.py:409`。
- 項 5 は「確認できたものだけ削除し、確認できなければ残す」。項 6 は「確認済み 15 関数も未確認候補 246 関数も削らず」。`inventory/list-D.txt:283` が当該関数を含むことを現物確認した。項 5 に項 6 の supersede はない。
- plan の留保は正しいが、段 4 では **science-slice の module/test 対を保持**して解消するべき。
- **DW-G05：放置すると、凍結 artifact が要求する外部 jobs path 集合の exact pin が、維持裁定に反して受入から消える。**

**A-2 — must-fix：requested-us の test は「削除 module 専用」ではない。**

- 対象：`test_backoff_requested_us.py:183`・`:230`・`:297`・`:688`・`:1061`・`:1092`、`s1-brief.md:58`、`s2-plan.md:180`。
- 残す patch の既定値 0、preprocess/object 同一性、TLS 集計、unknown/overflow、適用先制限を直接検査している。`condition_meaning_gate.py:143` と `test_ccbench_spawn_sites.py:2885` の登録・define 照合は、これらの意味的被覆を代替しない。
- `test_generic_dispatch_clean_child_contract_drops_pbs_envelope` は live な `dispatch_compute._child_environment()` に PBS 3 変数を注入し、除去を確認する。既存 dispatch test の設定値確認だけでは同等にならない。
- `test_t1941_reuses_backoff_profile_without_changing_current_policy_registry` も、現行 registry の包含・非包含を直接検査する。同じ literal を守る残存 test は見つからない。
- 最小修正は **requested-us の対も今回は保持**。削除を続けるなら、既存被覆を残す変更を具体化してから scope を確定する。「被検体ごと消える」を根拠とした全削除は不可。
- **DW-G05：放置すると、残存 patch の動作変化と live dispatch の PBS 環境漏出を拒否する検査が失われ、残存実装に対する受入条件が弱まる。**

**A-3 — should：受理集合の説明を訂正する。**

- 対象：`s1-brief.md:48`、`s2-plan.md:194`。
- test node 集合の縮小と、実装状態の受理集合は別物。検査を削ることは、一般には後者を広げる。共有 exact 表も期待集合が変わるため、「残る test の受理集合は不変」は成立しない。
- plan の「残存 site に課す述語を維持する」は共有 gate の説明として適切。ただし A-2 の被覆喪失まで解消する表現ではない。
- **DW-G05：放置すると、削除記録が実際の被覆・受理境界の変化を過小表示する。**

**A-4 — nit：共有 pin の行数と削除量を確定集合に合わせる。**

- 対象：`s1-brief.md:27`・`:57`、`s2-plan.md:64`。
- 全17 file 案の共有変更は **pin 6 行＋付属コメント2行＋README 1行**。spawn 表の5行が表す launch 数7と、編集行数を混同している。
- **DW-G05：実装の受理境界には直接影響しないが、author 指示と削除実績の台帳が食い違う。**

## 削除 6 module の 3 条件の検証表

「一致」は調べた範囲で反証なしを意味し、任意の動的文字列や repo 外の稼働状態の不存在証明ではない。

| module | 一回限り | 結果凍結済み | 現行機構の実装でない／判定 |
|---|---|---|---|
| `orchestrator/campaign/backoff_requested_us.py` | 一致。`:2` の one-rep 診断。 | 一致。`output/insights/2026-08-28_t1941-backoff-requested-us/README.md:9`・`:14` に診断限定と成功 request。 | module 自体の現行 operational consumer は未検出。ただし **対削除は A-2 で崩れる**。`docs/decisions.md:50984` は将来実測経路になった場合の裁定を述べ、現行使用の証拠ではない。 |
| `orchestrator/campaign/s6_canary_rename.py` | 一致。`:2` の D52 canary。 | 一致。`output/insights/2026-07-13_s6-canary-rename.md:6`・`:52`、`docs/phase3.md:502` の追認完了。 | 一致。共有 spawn 表以外の live 呼出しを未検出。完了済み canary 記録を残せばよい。 |
| `tools/insights_date_layout.py` | 一致。`:2` に一回限りと明記。 | 一致。`output/insights/2026-09-10/insights-date-layout/README.md:11`・`:18` に移動実績と固定計画。 | 一致。専用 test の import 以外を未検出。README は今後の索引ではないことも明記。 |
| `tools/migrate_output_gzip.py` | 一致。`:2` の tracked bytes 移行。 | 一致。`docs/archive/worklog-phase3-0820-723.md:1`・`:48` に実施・完了記録。 | 一致。専用 test の file-location load 以外を未検出。残存 reader の gzip fallback を提供する module ではない。 |
| `tools/plotting/plot_t2266_tail_mechanism.py` | 一致。`:7`・`:16` の固定3 report に対する記述的解析。 | 一致。`output/insights/2026-09-07_backoff-tail-mechanism/fig_tail_mechanism.provenance.json:46` に現行 source と一致する SHA-256。 | 一致。現行 generator を照合する残存 test は未検出。`output/insights/2026-09-15/t2266-tail-band/README.md:178` は既存6点・v1への固定で、新規実行の要求ではない。 |
| `tools/t1434_t1222_science_slice.py` | 一致。`:2`、成果物 README `:4` の固定 family 回顧 slice。 | 一致。`output/insights/2026-08-28/t1434-science-slice/README.md:12`・`:27` に結果。 | **対削除として崩れる／保持**。通常の運用 caller は未検出だが、専用 test `:409` は項6の維持対象。module の歴史性だけでは対削除を正当化できない。 |

検索は対象の完全 path・stem・部分名を、`orchestrator/`、`tools/`、`hooks/`、`.claude/`、`.codex/`、docs・設定、output の Python/shell に対して実施。`import_module`、`__import__`、`spec_from_file_location`、`run_module`、`run_path`、Python glob の候補も調べた。削除対象の module SHA-256 は再計算して検索し、図 provenance 以外の hit はなかった。

`output/insights/2026-08-28_t1941-backoff-requested-us/job-body.sh:383` には driver 呼出しがある。これは残る歴史再現 script であり、削除後の現 checkout では再実行不能になる。「参照ゼロ」ではない。

R1 の6 file についても、同じ名前検索で現行 consumer・運用登録を未検出。probe 4本の blob を再計算し、`output/insights/2026-09-16/t2638-codex-worktree-retirement/data/reach2.tsv:90` および `reach_all.tsv:90` から続く4行と一致した。これらは射影された R1 裁定が明示的に想定した歴史台帳で、未見事実ではない。**R1 を止める反証はない。**

## 専用 test 5 本の被覆表

| file | 削除 module 以外を検査する関数・性質 | 他 test の重複被覆 |
|---|---|---|
| `test_backoff_requested_us.py` | `test_fixed_then_diagnostic_uses_production_git_apply_and_reverts_clean` (`:183`)、`test_measure_uses_real_isolated_checkout_for_fixed_then_diagnostic` (`:757`)：patchharness 実処理。 | 一般的な適用・復元・隔離は `test_campaign.py:12856`・`:13137`・`:13178` にあり。ただし fixed→requested の実 patch 二段適用は同等被覆を未検出。 |
| 同上 | `test_mu01_patch_layers_after_fixed_and_default_is_preprocess_and_object_inert` (`:230`)、`test_mu02_tls_registry_exit_aggregation_unknown_overflow_and_silo_callsite` (`:297`)、`test_patch_contains_no_combined_fixed_branch_or_non_silo_callsite` (`:1061`)：残存 patch の動作・範囲。 | **同等被覆なしを示す検索結果**。`test_condition_meaning_gate.py:2790` と `test_ccbench_spawn_sites.py:2885` は registry/domain 照合であり、object 同一性・集計結果・overflow を検査しない。 |
| 同上 | `test_mu07_requested_and_admitted_intersections_keep_f718_1000_separate` (`:638`)：live `backoff_extended_sweep.genomes()` の3000 endpoint。 | live 側 endpoint は `test_backoff_extended_sweep.py:441` で重複。旧固定格子との比較部分は削除 driver 固有。 |
| 同上 | `test_t1941_reuses_backoff_profile_without_changing_current_policy_registry` (`:688`)：`backoff-profile` 包含、`backoff-requested-us` 非包含。 | **同等 literal 検査を未検出**。`test_build_admission.py:91` は現行 policy からの round-trip で、この包含・非包含の独立 pin ではない。 |
| 同上 | `test_generic_dispatch_clean_child_contract_drops_pbs_envelope` (`:1092`)：PBS 3変数の除去。 | **設定値だけ部分重複**：`test_pegasus_dispatch_compute.py:6273`。同 file `:5990` は argv 等を確認するが環境除去を assert しない。 |
| 同上 | `test_reproduction_body_accepts_generic_clean_child_and_invokes_driver_once` (`:1074`)、`test_reproduction_body_binds_site_dispatch_budget_and_atomic_failure_log` (`:1104`)、`test_reproduction_body_clean_child_rejects_noncompute_and_publishes_schema` (`:1146`)。 | 歴史 job-body 自体の被覆。同等検査を未検出。P2 の削除は、この継続検査も失うと明記する必要がある。 |
| `test_insights_date_layout.py` | 該当なし。`:33` の移動保存、`:99` の consumer/pin、`:417` の歴史ログ検査なども temporary tree 上の削除 tool の検査。 | live repo code の被覆移管は不要。`:12` の repo import は削除 module のみ。 |
| `test_migrate_output_gzip.py` | 該当なし。`:168` の round-trip、`:320` の staged bytes、`:359` の rollback は削除 migrator を対象とする。 | live reader の gzip fallback を検査する file ではない。`:15` の動的 load 対象も削除 module のみ。 |
| `test_plot_t2266_tail_mechanism.py` | 残存 live code の独立検査は未検出。ただし `test_real_reports_match_primary_source_refuted_extrapolation_literals` (`:281`) と `test_provenance_records_input_report_digests` (`:390`) は実 report を読む。 | 生成器の継続再計算・provenance 生成検査が消える。凍結済み図の provenance と現行 source を独立照合する残存 test は未検出。 |
| `test_t1434_t1222_science_slice.py` | `test_pinned_jobs_requirements_are_exact` (`:409`) は残存 artifact の外部入力集合を pin。`:107`・`:125` も実 artifact／jobs を検証。 | **同じ artifact の exact pin は未検出**。`test_t189_oracle_wiring_slice.py:132` は別 artifact で代替しない。A-1 により対を保持。 |

## (P1) の判定

**(a) 対を残す。** 項5の「確認できなければ残す」と項6の「削らず」を同時に満たし、優先順位の新設を要しない。  
`DW-S04` (`docs/dev-wave/core.md:101`) に照らし、既知の重複指定を「新事実」として承認済み裁定全体を止める必要はない。  
項5が項6を上書きしたとの逐語根拠はなく、親の優先断定を撤回して保持側で確定する。

## 親 brief / plan の実測値への所見

| 主張 | 検算・判定 |
|---|---|
| 8,623行 | **一致**。delete-set の17 file の現物合計。共有編集分は別。 |
| 162 node | **台帳登録数として一致**：36＋62＋12＋22＋30。現在の collection 数としては未測定。 |
| 11.58秒 | **一致**。台帳値は順に3.992／2.070／0.894／3.385／1.239秒、合計11.580秒。今回の実測時間ではない。 |
| 0.06% | **丸めとして一致**。台帳全24,379件、17,958.848秒に対して0.06448075%。wall短縮量には換算できない。 |
| 残る test の受理集合は不変 | **不成立**。共有期待集合の変更と A-2 の live 被覆喪失を分けて記録する。 |
| DW-O09 の live consumer はない | **調べた範囲の operational caller について支持**。ただし歴史 job-body、図 source hash、維持指定された artifact pin は実在する。包括的な「削除しても参照・被覆への影響なし」へ一般化できない。 |

共有 gate の追随について、**全17 file を削るという仮定なら** plan の pin6行・コメント2行・README1行は現物と一致する。

- `test_ccbench_spawn_sites.py:2840`・`:4100` は同じ Counter 表に追随する。
- `test_p3_build_authority_cli.py:1210` は `MACHINE_CALLERS` の file 読取なので当該1行削除で対応する。
- `test_plain_runner_coverage.py:77` の stale allowlist は README `:138` 削除で対応する。
- tracked AST 閉包 (`test_p3_build_authority_cli.py:649`) と受入 preflight (`tools/run_tests.py:784`) は staging が必要。targeted run は後者の代替にならない。
- materializer registry、import 例外台帳、provenance checker、living-doc path 検査に追加の対象登録は未検出。閉包47の変更根拠もない。
- 台帳 coverage (`test_acceptance_schedule_order.py:704`) は収集 node が分母。stale entry 保持は許されるが、現 HEAD の90%合格は静的検索だけでは確定しない。

したがって、**追加の削除由来 gate 赤は発見していないが、「すべて緑へ戻る」とは未実走のため断定しない。**

A-1・A-2 の対保持を採れば、削除量は **13 file／4,337行／台帳96 node／6.349秒**。共有変更も **canary の spawn4行と README1行だけ**になり、requested-us の pin・コメントは残す。

## 総括

**must-fix 2件**：science-slice の維持裁定との衝突、requested-us 専用扱いによる残存実装の被覆喪失。  
**判定：NO-GO。削除6対＋R1の6 file を、そのまま確定案として段4へ渡してはならない。**  
段4には本所見を渡し、science-slice／requested-us の2対を保持する13 file案を推奨する。  
R1の削除を止める未見事実、追加の共有gate追随漏れは未検出。静的検査のみで実走合格は未確認。