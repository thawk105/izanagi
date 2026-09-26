単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/s1-brief.md — 親の段 1 brief ((P1)〜(P4)・(P2')、事前登録案、費用)。**brief 自身も検査対象である。**
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/verbatim/T-2273-origin.md — 依頼の逐語 (「本題だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」「5 分上限の超過は受容しない」「検査込みの合計が 2 node 時間以上ならユーザー確認」)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/verbatim/D2243-head-item1-2.md (項 2)、D2242.md、D1936-item35.md、D357.md — 既裁定の逐語。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/output/insights/2026-09-23/t2273-shard0-bottleneck-4/README.md — 第 4 回診断 (§3 の計測表と費用)。同 dir の verbatim/s4-ruling.md と verbatim/probe-source.md。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/output/insights/2026-09-26/t2273-shard0-local-copy-ab/README.md — 前回の実受入の隣接対 (§5 の infra 失敗、§6 の計算量)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/test_s8b_oracle_driver.py の 847〜1000 行と 1437〜1730 行、/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/conftest.py の 2368〜2460 行と 2583〜2615 行。

## レンズ B — 過剰・削除・費用と、結論の使い道

親 brief は、候補 (a) の効果を replica probe の隣接対 3 対で測り、同じ走で発行 subprocess の内訳も測る計画である。プランを守らず、次を攻撃せよ。

1. **削れるもの:** 3 job・3 対・smoke・発行内訳の同時計測・pre を揃える温め、のうち、依頼 (D2243 項 2) の結論 (「(a) を実装する / (b) へ移る」の推奨) に要らないものはどれか。逆に、削ると結論が言えなくなるものはどれか。第 4 回は 1 対で次の一手を選んだが、前回はその 1 対の −123.9 秒が実受入で再現しなかった — この経緯から対の数をどう決めるべきか。
2. **足りないもの (ただし仮想リスク向けの gate・検査・台帳は scope 外):** 「(a) が効いても W_0 が 300 秒を切らない」場合に、依頼の「5 分上限の超過は受容しない」へ結論をどう繋ぐか。P の走で、次の律速 (発行 subprocess 等) を同時に読めるか。
3. **費用:** brief の見積り (単価 1,100 秒 / job、3 job + 受入 + 取り直し 1 ≈ 1.5 node 時間) は第 4 回・前回の実測から妥当か。検査込み (受入全走・smoke・失敗走) の合計で 2 node 時間に届く現実的な経路はあるか。届くなら、どこで止めてユーザー確認に回すかを事前に決めるべきか。
4. **結論の読み方の過剰:** replica の値から「実装したら受入が何秒になる」と言える範囲、言えない範囲。前回の実装 (最初の builder が写しを作り他は待つ) と P の差 (写しが collection 中に完成しているか) を、結論でどう区別して書くべきか。
5. probe の変更量を最小にする形 (第 4 回の runner / plugin / analyzer のどこを変え、どこを変えないか) の提案。
6. brief の file:line の誤り、親の実測値の引用とその一般化の誤り。

read-only で書込可能 tmp が無いので静的検査でよい。テストの実測は親が行う。予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ。

## 出力形式

- `## 所見` — 各所見に ID (B1, B2, ...)、重大度 (must-fix / should / nit)、根拠 (file:line か資料の節)、放置時に診断の結論 (効果の値・推奨) がどう変わるかを 1 行、推奨する修正。
- `## brief への異議` — (P1)〜(P4)・(P2') ごとに 同意 / 修正 / 撤回。
- `## 総括` (3〜6 行、GO / 修正後 GO / NO-GO)
