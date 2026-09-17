単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s6-ruling.md (親の段 6 裁定 F1〜F10、R3a〜R3c、追加 test、変異 M0〜M13。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s6-fix.md (fix 子の最終報告。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s6-fix-diff.patch (fix 差分 = commit 79dd07742 の `git show`。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s6-focus2.log (親の fix 後焦点走 log: 71 passed / 2 skipped。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s6-reviewA.md (段 6 レビュー A。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s6-reviewB.md (段 6 レビュー B。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s4-ruling.md (段 4 裁定 = plan v2 R0〜R4。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/tests/test_ccbench_spawn_sites.py (fix 後の対象 test。1728〜1830 (`_injected_check_unswallowed`)、2326〜2340 (R4 comment)、3050〜3400 (t2491 test 群)。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s1_direct_comparison.py (production。1151〜1153、1204〜1345 行。読むだけ)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s8b_oracle_driver.py (production。1655〜1665、1726〜1734、1774〜1825 行。読むだけ)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s8b_oracle_n_pilot.py (production。996〜1030 行。読むだけ)

## 依頼

あなたは dev-wave [T-2491] の段 6 統合後の**焦点再レビュー** (1 本、read-only)。fix を守らず検査せよ。pytest は走らせられない。静的検査だけでよく、緑を主張するな。
親の焦点走 log (71 passed / 2 skipped、Python 3.10 で n10/n14 skip) が実走の証拠である。

## 答えるべきこと

1. **所見ごとの対応表 (DW-O16、必須):** 段 6 裁定 F1〜F10 の各項目について closed / partial / regressed を判定し、根拠を file:line で書け。表なしで「閉じた」と言うな。
   特に F1 (R3a)、F2 (R3b)、F3 (R3c) はレビュー A の (a)(b)(c) の反例 source を自分で組み立て、fix 後の規則で「被覆に数えない」へ落ちることを追跡して示せ。
2. **regressed の探索:** R3a〜R3c が production 4 check (s1 1218 / 1295、s8b_oracle_driver 1801、n_pilot 1018) を誤拒否しないこと (fix 子の当て直し表を production 原文で独立に確認)。
   R3b が字句的親関数を含めたことで、入れ子関数内の sink (`<module>.outer.inner` 形) の扱いが変わっていないか。R3a の `local_names` 参照が `<module>` scope で空集合になるか。
3. **新負例の単一理由性 (DW-M01 / M03):** n13〜n17 と p8 が裁定の「各 1 理由」を満たすか。各負例について「その規則だけを外したときに受理へ反転するか」を静的に追跡し、
   fix 子の M11 予測 (n13 と n16 の両方が赤) と M12 / M13 の予測 (n15 / n17) を検算せよ。
4. **変異 anchor:** fix 報告の M0〜M13 の old が fix 後の file で 1 箇所か、new が構文的に成立するか (M4 の `region_nodes(handler.body)` は method 内の入れ子関数として参照可能か、M8 の 2 つ目の `return "none"` が到達可能か)。
5. **保証限界 comment:** 2326〜2340 行の comment が段 4/6 裁定の保証限界 (変換後の外側、MAYBE 未変換経路、with、guard、代入名、TryStar 未実走、finalbody 内 check、再束縛の射程) を漏れなく・名乗り過ぎなく書いているか。
6. **must-fix / nit:** 残る must-fix があれば DW-G05 の 1 行 (放置時に閉包検査の受理集合がどう変わるか) を添えて修正案を書け。示せないものは nit。既存テストの期待値変更は提案禁止。

## 出力形式 (見出しは全部 `##`)

## 所見対応表 (F1〜F10: closed / partial / regressed、根拠 file:line)
## regressed の探索 (production 4 check、入れ子 scope、module scope)
## 新負例の単一理由性と変異予測の検算
## 変異 anchor と comment の検査
## must-fix と nit
## 総括

最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
