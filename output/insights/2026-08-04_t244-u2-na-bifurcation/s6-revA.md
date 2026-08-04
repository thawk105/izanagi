# 段 6 敵対レビュー — レンズ A

**判定: NO-GO。**

先に争点を切り分けると、P4 必須化の帰結自体は成立する。D121 は P4 を「択一 3 で軸 (iii) を採る場合のみ」とし、ユーザーは択一 3 を「多世代開放の必須前提にする」と裁定しているためである。[docs/decisions.md:5846](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5846>) [worklog-phase3-0803-125-126.md:322](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/archive/worklog-phase3-0803-125-126.md:322>)

問題は、その帰結を記録する supersede の範囲と後続導線である。

### RA-B1 — supersede 範囲が自己矛盾し、旧 7 件列挙を残したまま 8 件を宣言している

- **主張:** 新 D は D121 の一文だけを置き換え、他は残すと宣言する一方、残る次文の「無条件義務 7 件」と矛盾する「8 件」を決定 (5) に置く。引用アンカーも Markdown bytes と終止符を含めて原文と一致しない。
- **根拠:** 新 D の限定宣言と保存宣言は [新 D:19](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:19>)、8 件宣言は [新 D:50](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:50>)。原文は `**P4 と P6 は条件付き義務**であり` と始まり [docs/decisions.md:5851](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5851>)、直後に 7 件を括弧列挙する [docs/decisions.md:5854](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5854>)。
- **成果物影響** — 読む文によって P4 を免責できるかが分岐し、cap-lift の受理集合、certified 探索世代数、proof chain の P4 status、試行台帳行数が変わる。
- **修正案:** 決定 (1) を次の趣旨へ変更する。

  > supersede は D121 決定 (7) の「P4/P6 条件付き義務」の一文と、直後の「無条件の義務 (P1・P2・P3・P5・P7・P9・P10)…」の一文に限る。前者は P6 だけを条件付き義務とする文へ、後者は「無条件の義務 (P1・P2・P3・P4・P5・P7・P9・P10)…」へ置き換える。未充足という述語、10 件の列挙、P8 の射程は維持する。

  置換対象は `**`、実際の改行、末尾の `。` を含む原文全文を逐語引用すること。

### RA-B2 — 段 3 blocker と V4 が canonical worklog へ返る成果物になっていない

- **主張:** 段 4 は worklog fragment 1 本と V1〜V4 の裁定パッケージを要求したが、現時点の `docs/spool/worklog/` には fragment がない。新 D が残すのも (a)〜(c)、すなわち V1〜V3 相当だけで、V4 と fold 後の参照更新が落ちている。
- **根拠:** worklog fragment は plan v2 の成果物である [s4-adjudication.md:63](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-04_t244-u2-na-bifurcation/s4-adjudication.md:63>)。V1〜V4 は [同:99](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-04_t244-u2-na-bifurcation/s4-adjudication.md:99>)、特に preregistration の stale は [同:106](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-04_t244-u2-na-bifurcation/s4-adjudication.md:106>)。新 D の返送事項は (a)〜(c) のみ [新 D:67](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:67>)。
- **成果物影響** — V2/V3/V4 が canonical 次タスクから消えると、空実装、receipt 不在、stale preregistration のまま将来 cap が開き、certified 集合と proof chain・正式試行台帳が無根拠に拡張される。
- **修正案:** 段 7 前に worklog fragment を作り、少なくとも次を逐語で pending 項目化する。

  - `NOT_CLAIMED` を global cap-lift 免責に使うか、per-run gate に限定するかの裁定
  - P6 の意味的充足契約を P6 実装前提の新規 T として起票
  - cap-lift receipt と producer/completeness/proof-chain consumer 結線を新規 T として起票
  - `docs/phase3-8c-preregistration.md` の stale を専用 wave へ送る
  - 新 D 採番後に runbook／phase doc の D121 単独参照を更新する

### RA-M1 — ユーザー裁定の一次記録を「逐語の正本」として参照していない

- **主張:** 新 D は親が生成した brief／裁定資料の directory を「逐語の正本」とするが、U2 の一次記録は worklog (153)、択一 3 の一次記録は archive worklog (126) である。
- **根拠:** 誤った正本指定は [新 D:17](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:17>)。U2 の逐語は [docs/worklog.md:568](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/worklog.md:568>)、択一 3 は [archive worklog:322](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/archive/worklog-phase3-0803-125-126.md:322>)。
- **成果物影響** — proof chain がユーザー裁定ではなく親の派生要約を authority として参照し、後続の受理判定が裁定内容を再検証できなくなる。
- **修正案:** 17 行目を次へ変更する。

  > ユーザー裁定の一次記録 = `docs/worklog.md` (153) U2。択一 3 の一次記録 = `docs/archive/worklog-phase3-0803-125-126.md` (126)。本 wave の導出資料 = `output/insights/2026-08-04_t244-u2-na-bifurcation/`。

### RA-M2 — 「状態語は 2 語だけ」が D138 の P6 結果型 4 値と衝突して読める

- **主張:** 新 D は無修飾に「状態語は 2 語だけ」と書くため、D138 決定 (3) の「結果型は 4 値」を二値へ縮退したように読める。非適用理由と P6 実行結果は別層である。
- **根拠:** 2 語限定は [新 D:35](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:35>)。D138 は P6 の結果型を 4 値と固定している [docs/decisions.md:6744](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6744>)。二分は非適用についての別条項である [同:6760](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6760>)。
- **成果物影響** — consumer が P6 の 4 値結果を 2 状態へ畳むと、proof chain の結果値と cap-lift 受理集合が変わる。
- **修正案:** 「**非適用理由を表す状態語**は `NOT_IMPLEMENTED` / `NOT_CLAIMED` の 2 語だけ」と限定し、「D138 決定 (3) の P6 実行結果型 4 値は変更しない」を追記する。

### RA-M3 — 承認上限の consumer 側実装位置を、修正対象の living docs が落としたままである

- **主張:** living docs は D114 の機械化を 3 producer 入口と freshness だけで説明するが、同じ上限定数を読む completeness の 2 consumer gate がある。段 4 が採用した A-M2 の訂正が反映されていない。
- **根拠:** 段 4 は consumer 2 検査を含める訂正を採用した [s4-adjudication.md:45](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-04_t244-u2-na-bifurcation/s4-adjudication.md:45>)。しかし phase doc は 3 入口だけ [docs/phase3.md:467](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3.md:467>)、runbook も「3 入口 + freshness」とする [runbook:203](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-s8c-autonomous-trial-runbook.md:203>)。実装には run-envelope gate [autonomous_trial_completeness.py:414](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/campaign/autonomous_trial_completeness.py:414>) と campaign-chain gate [同:1003](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/campaign/autonomous_trial_completeness.py:1003>) がある。
- **成果物影響** — completeness consumer の共有定数依存を見落とすと、proof-chain verifier の受理集合が cap 変更と同時に変わる事実を変更審査から落とす。
- **修正案:** 両 living docs に次を追記する。

  > 上限は producer の 3 入口に加え、`autonomous_trial_completeness.py` の run-envelope / campaign-chain の 2 consumer gate でも同じ定数を読む。存在しないのは P1〜P10／receipt の evaluator である。

### RA-M4 — runbook は引き続き旧 D121 だけを cap-lift 手順として指す

- **主張:** 件数だけ更新しても、実行手順は「D121 の 10 条件」だけを参照する。D121 に旧 P4/P6 免責文が残る以上、新 D を知らない承認者の経路は閉じない。
- **根拠:** runbook の cap-lift 手順は D121 単独参照 [runbook:118](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-s8c-autonomous-trial-runbook.md:118>)。D121 には旧免責が残る [docs/decisions.md:5851](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5851>)。段 4 も採番後の参照更新が必要と認識していた [s4-adjudication.md:47](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-04_t244-u2-na-bifurcation/s4-adjudication.md:47>)。
- **成果物影響** — runbook 経由では obsolete な `P6=NA` が通り、多世代受理集合、proof 参照、正式試行台帳が新 D 経由と分岐する。
- **修正案:** 新 D 採番後、runbook を「D121 とその決定 (7) を supersede する Dxxx の双方」に更新し、`P4 は無条件、P6 は NOT_IMPLEMENTED=FAIL／NOT_CLAIMED のみ免責`を逐語化する。同じ後続作業を今 wave の worklog fragment に固定する。

## 総括

- **blocker: 2 件** — RA-B1、RA-B2
- **must-fix:** RA-B1、RA-B2、RA-M1、RA-M2、RA-M3、RA-M4
- 択一 3 の裁定内容・日付、択一 7 件の裁定済み、U2 の内容、D138 決定 (5) の列挙、承認上限 1 の維持は確認できた。
- `git diff --stat` の tracked 変更は `docs/phase3.md` と `docs/phase3-s8c-autonomous-trial-runbook.md` の 2 ファイルだけで、`docs/phase3-main-experiment.md` は変更されていない。
- pytest、docs check、その他のテストは実行しておらず、緑は主張しない。