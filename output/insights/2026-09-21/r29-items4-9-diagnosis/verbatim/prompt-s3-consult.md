単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-r29-items4-9-diagnosis

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief (検査対象): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-r29-items4-9-diagnosis/brief.md
- 段 2 plan (検査対象、read-only codex の起草): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-r29-items4-9-diagnosis/codex/s2-plan.md
- 親の追加観測 (検査対象): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-r29-items4-9-diagnosis/parent-notes.md
- 裁定の控え: /work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-21-rulings-full29-verdicts.md (項 3・4・9)
- 相談 A の原文 (前回裁定の根拠): /work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260921c/artifacts/consult-a-out.md (項 1・2・4)
- 契約・裁定の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-r29-items4-9-diagnosis/verbatim/contract/ の全 file
- 前回診断 (repo 内、worktree path、read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-r29-items4-9-diagnosis/output/insights/2026-09-21/focus-run-count-diagnosis/README.md と同 dir の verbatim/
- t2797 の焦点走 launcher と log: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/focus/run-focus.sh、同 dir の focus-1.log〜focus-3.log
- コード (worktree、read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-r29-items4-9-diagnosis/ の tools/run_tests.py、tools/pegasus/dispatch_compute.py、orchestrator/campaign/site_policy.py、hooks/guard_bash.py

## 前置き — この依頼の性質

自分たちの開発運用手順 (dev-wave) の診断である。実装はしない (repo の runner・dispatcher・test・docs を変えない、新しい harness・目録基盤・gate・台帳も作らない)。
セキュリティでも攻撃でもなく、外部入力も扱わない。**親 brief・plan・親の追加観測を検査対象とし、守らずに点検すること。**
書込可能 tmp が無いので静的検査でよい — テスト・計算ノード job の実測は親が行う。git の読み取りは使ってよい。
予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

# 依頼 — レンズ A (契約解釈・算術・同条件性) と レンズ B (過剰・削除・見落とし) を 1 本で

所見ごとに **real / refuted / 判定不能** と、real なら **must-fix / should / nit**、file:line (または資料の節)、
「放置時に再提示の何がどう変わるか」を 1 行で書け。

1. **項 4 (a) 残件数の定義と数え方。** brief (P2) と plan §4 の「置き換えられる既存走」の定義は、D325 (「既に回す走行のうち 1 本を単独走に」「追加 dispatch 原則 0 本」) と
   相談 A 項 2 (「既存走の置換で満たせない残件数」) の読みとして妥当か。置き換えると失う契約条件 (初回診断・赤の fix 入力・契約追随・held・集合の最終確認) を
   正しく数えているか。事後情報でしか冗長と分からない走 (緑で後続 fix が続いた走) を c に数えるのは妥当か。標本 12 wave (07:38 固定) を使う (P1) は妥当か。
2. **項 4 (b) 最小改修範囲。** plan §1 の列挙は runner・dispatcher・記録・held opt-in・受入形判定の各層を漏れなく押さえ、過大にも過小にもなっていないか。
   既存 test・docs pin の追随件数の根拠 (grep の条件) は再現できるか。「改修なしの既存経路 G (generic)・L (login bounded local)」の判定 (plan §2) は正しいか —
   特に G の env 正規化 (D130 決定 (4))、site 判定、guard の可否、実装面該当性、失われる記録。L について D325 の理由欄の前提が現行コードで成り立つか。
3. **項 4 (c) 同条件の実測設計。** brief (P3)(P4) と plan §3 の腕 C / 腕 S は「同条件」と言えるか (同 SHA・同集合・同時刻開始、node 差、warm cache、腕どうしの資源競合、
   腕 S の直列 8 job が時間的に腕 C より後ろへ伸びること)。腕 S の各 job で「固定費 = wall − RUN」を測れば、腕 C 無しでも効果を示せるのではないか (実測を減らせるか)。
   腕 C を generic の `bash -c` で渡すことは「新しい harness を作らない」(依頼) と両立するか、実装面 (docs/ai-provenance.md) に当たらないか。
   試行回数 1 回の結果を効果として書く場合の限定 (待ちの二峰分布) の書き方。held を走らせない (P) の妥当性。
4. **項 9。** 「2 例とも `test_ccbench_spawn_sites.py` の node で、既裁定 T-2820 (D2194 項 8) の inventory 群追加が両 wave で発火する」は plan §5 と生 log・git から支持されるか。
   T-2820 が未実装のまま、項 9 の「局所策」として何を再提示すべきか (新しい択を作らず既裁定の実装で足りるか)。追加実行時間の測り方 (単独走、集合から抜く / 入れるの差) は妥当か、
   所要台帳の整数値 (47 node 中 5、最大 100 / 43 / 41 / 13 秒) を実測の代わりに使えない理由は十分か。列挙型探索 (130 file) を局所策から外す根拠は十分か。
5. **brief・plan の誤りと過剰。** file:line・数値・引用の誤り、scope 超過 (新 harness・一般化・gate・台帳)、逆に依頼 (項 4 の 3 点、項 9 の 2 点) の取りこぼし。
   研究前進の書き方 (土台) は DW-S01 を満たすか。

## 出力形式
- `## 所見` (番号、real/refuted/判定不能、must-fix/should/nit、根拠、放置時の影響 1 行)、`## brief・plan への訂正` (箇所と訂正文)、`## 実測を減らせる所`、`## 総括` (必須)。
