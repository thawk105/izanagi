## 所見

1. **real 候補 — 親 brief のアンカー表は一部不正確だが、段 2 プランは実装に必要な位置をほぼ修正済み。**

   - A1 `s8b_oracle_manifest.py:818`、A2 `:842`、A3 `:902`、A5 `s8b_ratified_freeze.py:3558`、A6 `:3303`、A7 `s8b_holdout_freeze.py:1865`、A8 `:1928`、A9 `:2053` は説明どおり。
   - A4 は定義が `s8b_oracle_manifest.py:1198`、gate が `:1205-1206`、構築が `:1245-1255`。
   - T1 `test_s8b_ratified_verify.py:834`、T2 `:854` は正しい。T3 の定義は `:872` で、brief の `:871` は空行。段 2 は `:872-886` と正しく扱う。
   - T4 は `test_s8b_holdout_freeze.py:1963`。brief の `:1985` は helper 内の `configuration_id` 行。
   - T5 は decorator が `:2155`、定義が `:2160`。
   - T6 の `test_s8b_oracle_report.py:268,391,402` は正しい。
   - T7 の既載行は正しいが、`test_s8b_oracle_manifest.py:1579,1595,1795,1836` と別 file の `test_s8b_oracle_driver.py:2336,2347` が欠落。段 2 の 25 caller 列挙は完全。
   - 成果物影響: brief だけで改名すると未修正 test caller が manifest fixture 構築前に落ちる。段 2 どおりなら certified 選択、report、台帳の production 値は変わらない。

2. **real 候補 — (d) fixture は実導出用として成立するが、「genuine な有効 official run」という説明は成立しない。**

   - プランは earlier result に `eligible_for_refreeze=False` を書き、別途 certificate を作るとしている。`s2-plan.md:75-81`。
   - admission inspector が `True` を導出した result の自己申告が `False` なら、full live verifier は `refreeze-eligibility-mismatch` で拒否する。`s8b_floor_stats.py:1069-1077`。
   - earlier 選択走査が実際に読むのは result の存在 bytes、manifest、journal の `session-start` / `session`、admission 台帳である。certificate は読まない。`s8b_holdout_freeze.py:1842-1853,1877-1909`。
   - full launch artifact と呼ぶには certificate、journal、result の hash・時刻鎖が必要だが、プランの journal は attempt lifecycle だけである。`s8b_ratified_freeze.py:3131-3245,3361-3391`。
   - 一方、既存 legacy rows を残したまま新 measurement-generation rows を追記すること自体は実装が許す。`s8b_holdout_admission.py:1742-1763`。inspector も campaign ごとに schema を選ぶ。`:5838-5859`。
   - 最小形は certificate 作成を削り、「production admission に裏付けられた earlier result」と明記すること。完全に有効な official artifact を要求するなら、自己申告を `True` にし、full journal と certificate hash chain まで再束縛する必要がある。
   - 成果物影響: 現プランでも選択 reason と mutation kill は得られるが、「有効 official run を被覆した」という insight / worklog の参照が事実より強くなる。certificate bytes はテスト結果に寄与しない。

3. **real 候補、nit — private 化後に stable runbook が陳腐化する。**

   - runbook は現在も `s8b_oracle_manifest.build_manifest` が実装済みであると記す。`docs/phase3-8b-restart-runbook.md:274-279`。
   - 段 2 の docs 面は worklog fragment と新 insight だけで、この更新を含まない。`s2-plan.md:98-106`。
   - 成果物影響: certified 値や受理集合は変わらないため nit。ただし利用者の API 参照が存在しない旧名へ向く。

4. **real 候補、nit — 焦点走の 13 file は直接参照集合として正しいが、「consumer 集合」という表現は広すぎる。**

   - 直接 source 検査は `test_s8b_oracle_artifacts.py:252-275` と `test_s8b_oracle_manifest_contract.py:39-84,107-127` にあり、どちらも 13 file に含まれる。
   - module 名を持たず全 production file を読む構造検査として、少なくとも `test_campaign.py:5258-5295`、`test_p3_b4_analysis_path.py:303-309`、`test_p3_exploration_namespace.py:131-144`、`test_p3_s4_loop.py:1385-1397`、`test_p3_build_authority_cli.py:1212-1218`、`test_s1_known_axes_freeze.py:638-647`、`test_s8b_floor_campaign.py:1624-1647,6768-6784`、`test_s8b_floor_stats.py:875-901`、`test_reflux_ir.py:292-298`、`test_t1286_commit_receipt.py:694-725`、`test_t338_submission_gate_unit5.py:490-515` がある。
   - 今回の三関数改名はいずれの探索 token、process site、perf predicate、issuer call も変えないため赤にはならない。焦点走を増やすより、「13 file は lexical/direct consumer 集合」と記述を狭めるのが妥当。
   - 成果物影響: 現差分ではなし。一般 scanner まで網羅したと誤記すると、将来の全受入との差を見落とすため nit。

5. **refuted 候補 — 指定された四つの構造検査に更新は不要。**

   - process inventory は全 campaign AST を読むが、改名対象三関数に process launch はない。`test_ccbench_spawn_sites.py:332-344,382-394,487-501`、対象本体 `s8b_oracle_manifest.py:818-869,902-907`。
   - perf closure は source を全走査するが、pin している holdout / ratified 関数を変更しない。`test_official_perf_closure.py:206-225,520-543`。
   - preregistration invariant が名指しするのは `s8b_ratified_freeze.load_ratified_freeze` で不変。`test_s8c_preregistration_invariant.py:54,81,88`。holdout scan `:623-644` に三軸 literal も増えない。
   - predicates も ratified path / loader token の検査である。`test_s8c_preregistration_predicates.py:29-34,528-538,1164-1166`。
   - 成果物影響: なし。関数名変更による構造検査の受理集合は不変。

6. **refuted 候補 — DW-O09 の bytes pin 閉包に取りこぼしは見つからない。**

   - generator role の閉集合は五つだけで manifest 自身を含まない。`s8b_oracle_manifest.py:65-74`。key の追加や path 差替えも拒否される。`:458-496`。
   - canonical holdout freeze が pin する source は `s8b_holdout_freeze.py` だけ。`output/s8b-freeze/holdout_freeze.json:13-15`、`t080_freeze_migration.py:113-123`。
   - 現 bytes は `7904d47b...` で記録値と不一致だが、対応 check は hold 中。`freeze_verification_hold.py:14-38`。
   - `acceptance_duration_ledger.json` は新 test node の source pin ではない。未知 node は duration 未解決となり、collection coverage は 90% 下限である。`conftest.py:1524-1544`、`test_acceptance_schedule_order.py:704-716`。
   - `_RUN_BASENAMES` の `manifest` role は artifact basename 束縛であり、source bytes pin ではない。`s8b_ratified_freeze.py:278-283`。
   - 成果物影響: なし。今回の production 編集から既存凍結成果物の再発行は導かれない。

7. **refuted 候補 — scope の盛りすぎは certificate 以外にはない。**

   - private 化は既存三迂回口だけを閉じ、seal framework、互換 alias、追加台帳を導入しない。`s2-plan.md:25-65`。
   - `sys.setprofile` は test-local で、導出関数を置換せず exact code frame を観測するための被覆証拠に限定される。`s2-plan.md:83-94`。
   - 成果物影響: certificate の不要 bytes 以外なし。production の受理集合や凍結 schema は増減しない。

## (b) 母集合の独立列挙

| 入口 file:line | 呼び方 | 選択 identity の強制 | 根拠 |
|---|---|---:|---|
| `s8b_oracle_report.py:2540,2547-2550` | `main` → load + reverify | なし | reverify は `result_type=ReverifiedFreeze`。`s8b_ratified_freeze.py:3658-3668`。選択分岐は `LaunchValidatedFreeze` のみ。`:3303-3321` |
| `s8b_oracle_judge.py:740,749-750` | `main` → load + reverify | なし | 同上 |
| `s8b_verdict.py:823,828-829` | `main` → load + reverify | なし | 同上 |
| `p3_autonomous_workload_trial.py:4399,4710-4725` | `run_trial` C06 → load only | なし | load 後は budget 入力へ直結し、狭い gate / launch を呼ばない |
| `s8b_oracle_manifest.py:1198,1205-1206` | `build_approved_manifest` → load + 狭い API | あり | load 直後に `assert_g1_floor_selection_identity` |
| `s8c_result_judge.py:2075-2081` | helper → load + 狭い API | あり | `:2078` で強制。実 consumer は `verify_floor_bytes:2129` と publish 再検査 `:2213` |
| `s8b_oracle_driver.py:402,496` | private `_gate_check_core` 内 self-load | 単独ではなし | この call 自身の後に launch はない。ただし production public v2 wrapper はこの形で到達させない |
| `s8b_oracle_driver.py:594,644,664` | public `gate_check` → load + launch | あり | 同じ candidate を `launch_validate` へ渡す |
| `s8b_oracle_driver.py:1293,1335,1351` | `run_block` → load + launch | あり | load 後に同一 ratified object を launch validation |
| `s8b_ratified_freeze.py:1399,3548,3658` | loader / launch / reverify 定義 | 定義側 | launch のみ `_launch_validate(... LaunchValidatedFreeze)` により `:3303` の選択分岐へ入る |

直接 call 数は `load_ratified_freeze` 9、`reverify_published_freeze` 3、`launch_validate` 2。未強制の production 母集合は report / judge / verdict / C06 の四群で、親の最終値と一致する。`tools/`、CLI wrapper、insight script に追加の実 callerはなく、動的 import / `getattr` 呼出しも見つからなかった。後二点は negative search のため file:line 根拠なし。

## 親 brief への反証

- T3 は `test_s8b_ratified_verify.py:872`、T4 は `test_s8b_holdout_freeze.py:1963`、T5 の定義は `:2160`。brief の行はそれぞれ空行、helper 内行、decorator。
- T7 は四 call 不足し、さらに caller file `test_s8b_oracle_driver.py:2336,2347` が丸ごと不足している。
- `s8b_oracle_driver.py:496` は選択強制点ではない。強制点は public wrapper の `:664` と run path の `:1351`。
- 四群という母集合、DW-O09 の source pin 閉包、holdout generator pin の着手前不一致という結論には反証なし。
- provisional P1-2 の「genuine official run」は、実導出を通すという意味なら成立するが、full official artifact validity を意味するなら反証される。

## scope 外の所見

earlier result の certificate、full journal、result schema 全体まで選択候補条件に加える変更は、現行の「共有 admission 台帳だけから再導出する」契約 `s8b_holdout_freeze.py:1865-1909` を変え、床値選択の受理集合を狭める。本 wave では実装せず、必要なら別裁定に送るべきである。

## 総括

- 最も危険なのは、admission-backed fixture を「full-valid official run」と記録してしまう証拠の過大表示である。
- 実装手順自体は成立し、legacy / measurement-generation 台帳の混在もコード上は許容される。
- (b) の未強制母集合は四群で確定し、親の最終結論に過不足はない。
- private API caller 25 箇所と凍結 pin 閉包にも漏れは見つからない。
- 段 4 では genuine 二 nodeについて、mixed-schema 台帳受理、導出 call が正確に `[earlier_rel]`、reason/cause、`return False` mutation の consumer clean kill を実測すべきである。
- 静的検査のみで、pytest は実行していない。