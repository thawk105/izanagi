単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/stage4-ruling.md — 段 4 裁定とプラン v2 (実装の正本)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s2-plan-r2.md — 段 2 プラン。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/d2194-item3.md — 裁定の逐語。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/prereg-s5.1.1-reference.md — 凍結事前登録の共通参照点。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/a.patch — 実装子 A の差分 (side channel)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/b.patch — 実装子 B の差分 (caller)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s5-author-A.md — 実装子 A の最終報告。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s5-author-B.md — 実装子 B の最終報告。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/focus-f1.log — 親の焦点走 (計算ノード、33 file) の生 log。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop.py — 統合後 (commit `ec6459863`)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_s4_loop.py — 統合後。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_b4_prerun_caller.py — 統合後。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_b4_prerun_caller.py — 統合後。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/campaign_lock.py — codec (読むだけ)。読めなければ即停止

## レンズ A: 正しさ・束縛・失敗の意味・test の検出力

実装を守らせず検査する。攻撃面に `docs/failures.md` の型タグ [恒真ゲート] [テスト代表性] [誤前提] [consumer 取り残し] [変異帰属] [防壁の射程誤認] を含める。
各項目を real / refuted で判定し、根拠 (file:line) を示す。

1. **束縛:** `_wal_attempt_provenance` は outcome ごとに正しい attempt を選ぶか (certified / duplicate は採用 commit、aborted は abort か start、
   rejected は今回の reject、ID 未確定は null)。rejected で「同 variant の最後の record が abort」を使う判定は、同じ diffq variant の過去の reject や
   retry があっても今回の attempt を指すか。`wal_refs` は attempt 境界で切れているか。
2. **受理集合の変化:** `main()` が非 B-4 走行でも `canonical_b4_proposal_sha256` を必ず計算するようになった。計算できない document
   (非有限値など) で、以前は通った走行が止まるか。止まる場合、既存の値検査 (`_assert_coder_value_domain`、`assert_closed_proposal_schema`) が先に
   拒否していて実害は無いか。`--b5-slot` 経路で hash 計算の例外が `_b5_proposal_rejected` (rc=3) に乗らず漏れるか。
3. **評価前の検証:** `_load_provenance(layout)` は B-4 認可の検査・消費と評価より前にあるか。入口停止で report を新設しないか。
   破損時に元 bytes を退避して止まり、`.corrupt.*` が残る限り再開を拒否するか。退避の `os.link` → `unlink` の間の失敗で元 bytes を失わないか。
4. **P4 の限定:** docstring の経路別帰結は実コードと一致するか (特に B-4 continuation の receipt 再利用拒否、bootstrap の履歴検査)。
5. **入力隔離 (D39 決定 3):** 新 report が planner / coder / critic の入力へ流れる経路が無いか。`agent_record` に足した `proposal_document` が
   live journal (`_append_live_agent_outputs`) の envelope へ混入しないか。
6. **caller:** codec 経由化で受理が広がるのは有効な v2 だけか。non-certifying lock・非 canonical v2・壊れた authority・invalid UTF-8 が
   `campaign_input_unreadable` になり issuer が呼ばれないか。v1 の trial 欠落で KeyError が漏れないか。
7. **test の検出力と代表性:** 新 test は実体 (`drive_iteration`・実 writer・実 issuer) を通しているか。期待値に揮発値を焼き込んでいないか。
   段 4 の変異 S1〜S14・C1〜C5 がそれぞれ単一の理由で落ちる設計か (実装子 A は S8 / S13 に後段 loader との重なりがあると報告)。
   v2 lock を作る fixture と `real_repo_fixture_lock` の使い方が、他の real-repo reader を長く止めないか (全体 5 分の上限)。
8. **焦点走の結果:** `focus-f1.log` の失敗・error・skip を読み、本 wave 起因か、既存の非帰属か、drift 由来かを分類する。

## 制約

- sandbox は read-only。**静的検査と log の読解だけでよい。** テストの実走は親が行う。実走していないことを「確認した」と書かない。
- scope 外 (admission 検査の追加、reference 欄、caller に side channel を読ませる、sort / trigger への展開) を提案する場合は、scope 外と明記して分ける。
- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終える。

## 出力形式

項目 1〜8 を見出しで分け、各項目に判定 (real / refuted)、must-fix / should-fix / nit の別、根拠、放置時に成果物 (B-4 の適格行・参照点・台帳・
certified 判定) がどう変わるかを 1 行で書く。最後に `## 総括` を置き、GO / NO-GO を明記する。
