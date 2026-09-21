単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/stage6-ruling.md — 段 6 裁定 (§1 の所見表、§2 の fix 内容、§4〜§4.2 の erratum と訂正、§5 の変異方法)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s6-review-A.md — 段 6 レビュー A (NO-GO)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s6-review-B.md — 段 6 レビュー B (NO-GO)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/fix-a1.patch — fix 1 巡目の差分。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/fix-a2.patch — fix 2 巡目の差分 (test のみ)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/fix-a3.patch — fix 3 巡目の差分 (test のみ)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/fix-a4.patch — fix 4 巡目の差分 (test のみ)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/integrated-final-92f501c28.patch — 基準 `36fb14a3d` から最終 `92f501c28` までの統合差分。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/focus-f2.log — 焦点走 f2 (33 file、fix 1 巡目の後、production の最終形)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/focus-f5.log — 焦点走 f5 (test_p3_s4_loop.py 単独、最終 commit)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/probe_duplicate_fixed.py — 親の読み取り probe (§4.2 の根拠)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop.py — 最終形。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_s4_loop.py — 最終形。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_b4_closed_critic.py — 最終形 (launcher positive test の stub)。読めなければ即停止

## 焦点再レビュー (fix 後、全体へ 1 本)

段 6 レビュー A・B の所見のうち real と裁定したものを、最終 commit で閉じたかを検査する。攻撃面に `docs/failures.md` の型タグ
[恒真ゲート] [テスト代表性] [誤前提] [consumer 取り残し] [変異帰属] を含める。

1. **所見ごとの対応表 (必須):** 段 6 裁定 §1 の real 所見 (A2・A3・A4・A7/B6・A7/B4) それぞれを closed / partial / regressed で判定し、
   根拠 (最終形の file:line と、焦点走 log の該当行) を示す。表なしで閉じたと言わない。
2. **fix の副作用:** 4 巡の fix が、既存 test の期待値・production の受理集合・whiteboard / planner 射影・本番の attempt 検査を変えていないか。
   `test_p3_b4_closed_critic.py` の差分が stub 出力に限られるか。A2 の「mode を問わず hash=null で続行」が、B-4 bootstrap の registry 束縛
   (canonical hash を先に要求) と矛盾しないか。
3. **親の訂正の検算:** 段 6 裁定 §4 の診断は §4.1 で撤回され、§4.2 で拒否理由を probe で特定している。§4.2 の主張
   (拒否理由の文言、`tags` の既定値、修正後に duplicate・採用 attempt・refs 4 件) を最終形のコードと probe の中身から再計算して照合する。
4. **焦点走の量化:** 親が書く「f2 は 33 file で 1 failed / 4701 passed / 15 skipped、skip 15 件は全件既存理由」「f5 は 655 passed」を log の原文から再計算する。
   f2 の後の変更が test_p3_s4_loop.py だけであり、f2 の他 32 file の結果が最終形でも有効と言えるかを統合差分から判定する。
5. **変異設計:** §5 の割り振り (注入群 L は drift を受けない新設 test を `-k` で選ぶ、commit 群は drift を受ける test を持つ変異) で、
   各変異が単一の理由で落ちる設計か。S4 の再照準 (最初の start への置換) は最終 fixture で非等価か。

## 制約

- sandbox は read-only。**静的検査と log の読解だけでよい。** テストの実走は親が行う。実走していないことを「確認した」と書かない。
- scope 外 (admission 検査の追加、reference 欄、sort / trigger への展開) を提案する場合は scope 外と明記して分ける。
- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終える。

## 出力形式

項目 1〜5 を見出しで分け、項目 1 は表にする。新しい所見には real / refuted・must-fix / should-fix / nit・放置時の成果物影響 1 行を付ける。
最後に `## 総括` を置き、GO / NO-GO を明記する。
