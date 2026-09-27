## 所見

1. **削りすぎ / must-fix** — [plan:23](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1418-closure-mutation/out/s2-plan.md:23) は復元前に HEAD の *SHA* を確認するが、[既存の `_assert_head`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:1036) は detached かを確認しない。runner が M を指す branch に切り替えた場合、`reset --soft H` が branch ref を動かす。**推奨:** commit 前だけでなく、復元直前にも detached を確認し、attached なら ref を動かさず停止する。この正例・拒否例を一組で検査する。

2. **削りすぎ / must-fix** — [plan:21–27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1418-closure-mutation/out/s2-plan.md:21) のうち、runner 前の「M の変更 path と注入 bytes の一致・作業木 clean」、通常終了時の H と bytes への復元、dispatch orphan 時の M 保持は残す必要がある。既存 harness は [H のまま変異を残す契約](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:2361) なので、そのまま流用すると誤 KILLED／誤 SURVIVED または遅延 job の別木観測が起きる。**推奨:** これらを commit 分岐の最小安全境界とする。signal 中の H/M 判別も残す。

3. **既存策あり / should** — [plan:29、35](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1418-closure-mutation/out/s2-plan.md:29) の ledger v5、各 record の M SHA、履歴 object 再検証、wrapper terminal reader 改修は、(a)(b) の判定に必要な新しい値を生まない。既存 reader は [procedure の policy と H/spec/runner を照合](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:2728) し、[失敗 node と artifact から status を再計算](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:2634) する。**推奨:** 既定 v4 はそのままに、commit mode の source/restore policy 値を mode 固有にして resume を束縛する。M SHA の台帳追加と schema 上げは削る。

4. **既存策あり / should** — [brief:14、plan:35](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1418-closure-mutation/brief.md:14) の wrapper 中継は、dogfood に [既存の `--commit` 使い捨て detached 木](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_worktree.py:534) を使う場合に限って必要。**推奨:** wrapper の mode 引数、[harness argv](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_worktree.py:712)、[表示する resume command](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_worktree.py:1050) の中継だけに絞る。fanout 公開・改修は削る。

5. **削れる / should** — [plan:45–47、63–67](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1418-closure-mutation/out/s2-plan.md:45) は親・path・blob・cleanliness を個別の偽造 test と M2～M6 に展開している。特に M2 と M4 は同じ「予期しない commit path」を同じ test で検出し、新規検出力として二重計上できない。**推奨:** runner 前に正しい M だけを受理する一つの境界 test と、実際に別の受理結果を生む欠陥だけを matrix に残す。

6. **既存策あり / should** — [plan:47–51](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1418-closure-mutation/out/s2-plan.md:47) の既定 file-swap v4、一般的な HEAD/spec 不一致、orphan sidecar 拒否、signal 復元は、既存の [正常走行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/orchestrator/tests/test_mutation_harness.py:708)、[resume HEAD 拒否](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/orchestrator/tests/test_mutation_harness.py:1242)、[orphan 拒否](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/orchestrator/tests/test_mutation_harness.py:1304)、[signal 中の復元](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/orchestrator/tests/test_mutation_harness.py:2365) が持つ性質である。**推奨:** 新規 test は commit 特有の HEAD 遷移・復元・hold に集中し、既存 test は回帰として再実行する。

7. **削りすぎ / should** — [plan:43–50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1418-closure-mutation/out/s2-plan.md:43) には commit mode の *同一 mode で成功する resume* と、復元前に attached HEAD を拒否して branch ref を守る正例／拒否例の対がない。**推奨:** mode 不一致の拒否だけでなく、H へ復元後の正当な resume が通ることを確認する。

8. **削れる / should** — [plan:70、74–78](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1418-closure-mutation/out/s2-plan.md:70) の E1、単体 test のコメント変異、実 dispatch のコメント dogfood は同じ等価対照を重ねている。**推奨:** (a)(b) を示す実 dispatch の等価・値変異は残し、E1 を harness 変更の独立した変異 kill として数えない。既存 lock に H が pin された経路では commit でも drift が残るという [plan 自身の限定](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1418-closure-mutation/out/s2-plan.md:3) も結果の適用範囲に明記する。

9. **削れる / should** — [brief:15、43–45](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1418-closure-mutation/brief.md:15) の F424 恒久追記、mutation.md の一文、decisions/failures fragment は、今回の台帳値を変える本題実装ではない。**推奨:** 必要な実測結果の記録は既存の wave 手順に従い、追加の説明文書改修は本 scope から外す。

10. **削れる / should** — [brief:47–50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1418-closure-mutation/brief.md:47) は段 2・3 と段 6 review 子を各複数本とするが、[DW-C00](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/docs/dev-wave/core.md:10) が要求するのは該当時の独立した敵対検証であり、この本数までは要求していない。**推奨:** 必須の独立検証と実測を残し、追加の相談・review 本数を成果物影響なしに固定しない。

11. **裏取りなし / should** — [brief:6–8、20–24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1418-closure-mutation/brief.md:6) の「T-2850 M8 は commit 注入で 2 passed」「HEAD 以外に束縛された層は現存しない」は、この射影資料だけでは実測として確認できない。後者には [plan:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1418-closure-mutation/out/s2-plan.md:3) が既存 v2 lock の反例を挙げている。[T-2632 の script](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/output/insights/2026-09-21/t2632-b4-evidence-carrier/mutation/run-commit-group.sh.txt:25) は commit 手順の先例であり、T-2850 の結果そのものではない。**推奨:** 実測値に artifact を付け、HEAD 束縛の主張を「新規取得経路」に限定する。

## 総括

**条件付き GO。** 必要最小の変更集合は次のとおり。

1. harness に opt-in commit 注入を足し、既定 file-swap を維持する。
2. detached の使い捨て木で H から M を作り、runner 前に M の path・bytes・cleanliness を確認する。
3. runner 中は M を保持し、通常・signal 終了では detached を再確認して H と bytes に復元する。
4. dispatch orphan では M を保持し、既存 hold と sidecar に沿って停止する。
5. 既存 ledger の policy 値で mode を束縛し、正当な resume と mode 不一致を確認する。
6. 実 dispatch で同じ閉包 file の等価変異 SURVIVED と値変異 KILLED を示す。

静的レビューのみ実施。編集・テスト・dispatch は行っていない。