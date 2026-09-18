単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1878-mocc-trace-pilot-raw-artifact

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/02b17687/tmp/codex/dev-wave-t1878-mocc-trace-pilot-raw-artifact/projection/s5-diff.patch (レビュー対象 = 親が stage した docs 差分 5 file。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/02b17687/tmp/codex/dev-wave-t1878-mocc-trace-pilot-raw-artifact/brief.md (親 brief と段 1 実測の要点。親 brief 自身も検査対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/02b17687/tmp/codex/dev-wave-t1878-mocc-trace-pilot-raw-artifact/projection/T-1878-original.md (依頼の起点 entry 998 の原文。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/02b17687/tmp/codex/dev-wave-t1878-mocc-trace-pilot-raw-artifact/projection/claim-evidence-C14a-and-b-column-rule.md (凍結稿の C14a 行と (b) 欄の規則の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/02b17687/tmp/codex/dev-wave-t1878-mocc-trace-pilot-raw-artifact/projection/D1013.md (claim-evidence 系列の裁定の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/02b17687/tmp/codex/dev-wave-t1878-mocc-trace-pilot-raw-artifact/projection/mocc_trace_pilot.sh.2efe6282.txt (pilot 実走時点 outer commit 2efe6282 の job script 全文。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/02b17687/tmp/codex/dev-wave-t1878-mocc-trace-pilot-raw-artifact/projection/submit_mocc_trace.sh.2efe6282.txt (同時点の submit script 全文。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/02b17687/tmp/codex/dev-wave-t1878-mocc-trace-pilot-raw-artifact/projection/verifier-report.py.2efe6282.txt (同時点の verifier JSON 生成 `result_to_dict`。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/02b17687/tmp/codex/dev-wave-t1878-mocc-trace-pilot-raw-artifact/projection/verifier-cli.py.2efe6282.txt (同時点の verifier `--json` 経路。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1878-mocc-trace-pilot-raw-artifact/output/insights/2026-08-22_t755-mocc-trace-v2-pilot-serializability.md (C14a の一次資料 insight、凍結。読めなければ即停止)
- /work/1/SFC/tanab/dev-wave-jobs/t755-mocc-trace-execution/handoff.md (pilot を実走した wave の handoff、repo 外・凍結。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1878-mocc-trace-pilot-raw-artifact/output/insights/2026-09-18/t1878-mocc-trace-pilot-raw-artifact/README.md (本 wave の insight、差分 = 新規 file 全文。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1878-mocc-trace-pilot-raw-artifact/output/insights/2026-09-18/t1878-mocc-trace-pilot-raw-artifact/verbatim/search-934607-result.txt (走査結果の分類一覧。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1878-mocc-trace-pilot-raw-artifact/output/insights/2026-09-18/t1878-mocc-trace-pilot-raw-artifact/verbatim/search_934607.py.txt (走査 script の逐語。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1878-mocc-trace-pilot-raw-artifact/docs/paper-story/README.md (差分適用後の作業木。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1878-mocc-trace-pilot-raw-artifact/output/insights/2026-08-26_mocc-trace-pair.md (隣接物の一次資料、凍結。読めなければ即停止)

## 目的
これは docs-only の記録 wave のレビューである。論文の claim-evidence 表 C14a (mocc TRACE=1 pilot、PBS `934607.nqsv`) の
`[権威 bytes]`「未特定」について、親が限定範囲を探索し「探索した範囲での未特定」を insight と `docs/paper-story/README.md` の
claim-evidence 系列節へ記録した。**欠陥を指摘するのが役目で、差分を追認するものではない。** レンズは 2 つを 1 本で担う:
(A) 正しさ境界・整合・実効性 — 記録の事実命題が一次資料と逐語で一致するか、不在の断定に化けていないか、凍結物に触れていないか。
(B) 過剰・削除 — 依頼の scope (本題の所在記録だけ) を超えた記述・一般化・gate や台帳の追加が紛れていないか、逆に依頼が求めた要素
(path と sha256 / 範囲の明記 / 全体不在の非断定 / 後継記録と insight の 2 箇所) が欠けていないか。

## 親が実行済みのこと
- 段 1 実測 (brief.md と insight README §1〜§2)。走査は login node で read-only。
- 段 5 は親編集 (docs-only、DW-C00)。実装面差分ゼロで変異 matrix 免除 (DW-S04)。`tools/check_docs.py` と `spool_fold.py --dry-run` は
  本レビューと並行して親が走らせる (結果は本レビューの入力ではない)。
- 差分は未 commit (stage 済み)。commit 前にこのレビューの real 所見を反映する。

## 問い
1. **事実命題の逐語照合**: insight README §1 の表と README 追記の各命題 (PBS request、outer commit、ccbench OID、txns、出力 path、
   receipt が sha256 を持たないこと、qsub に `-o`/`-e` が無いこと、埋め込み JSON が欠く 3 key、投入 worktree 名) を、射影した
   2efe6282 時点の script / verifier と t755 insight / handoff の逐語と突き合わせ、食い違い・行番号の誤り・出所の取り違え
   (現行 script の事実を当時の事実として書いていないか) を全部挙げよ。
2. **不在主張の射程**: 「探索した範囲での未特定」が、本文のどこかで「存在しない」「失われた」という全体断定に化けていないか。
   逆に、探索した範囲の列挙 (§2 の 7 行) が依頼の限定範囲 (a)(b)(c) を過不足なく覆っているか。走査 script の除外条件
   (拡張子 allowlist、50 MB 超 skip、symlink 除外) が「範囲内なのに見ていない」領域を作っていないか。作っているなら、
   それを「探索していない範囲」へ書き足すべき文面を示せ。
3. **代替物の混入**: §3 (埋め込み JSON の sha256 を代わりに書けない) と §4 (pair wave の leg を C14a に流用しない) の論証が、
   一次資料 (verifier-report.py の `result_to_dict`、cli.py の `--json`、pair.md) で支えられているか。逆に、親が
   「流用しない」と書きながら README 追記が読者に流用を誘う書き方になっていないか。
4. **置き場 (P1) と D1013**: README の claim-evidence 系列節へ日付付き注記を積む置き方が、D1013 の「規則 2」と「却下した選択肢
   (README にポインタを 1 行足すだけ)」に抵触するか。抵触するなら、依頼の「凍結物は上書きせず新しい日付の記録」と D1013 の両方を
   満たす置き方を示せ。抵触しないなら、その理由を D1013 の逐語で示せ。
5. **凍結物と規律**: 差分が凍結物 (`claim-evidence/2026-08-26.md`、8 月の insight、pair receipt) を変えていないこと、規律 2
   (正しさゲート) と絶対規律 7 (当時の判定と現行の正しさ主張を分ける) に触れていないこと、C14a の判定値を弱めても強めてもいないことを
   差分の逐語で確認せよ。
6. **scope 超過**: 依頼は「本題の所在記録だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。差分に、将来の運用規則の
   提案・一般化 (例: 「以後は必ず退避せよ」)・新しい台帳や検査の追加に当たる文があれば挙げよ。
7. **親 brief 自身**: brief.md の前提 (稼働 wave t2775 が README の版系列 stale 節を編集中なので触れない、など) に検証されていない
   一般化があれば挙げよ。

## 制約
- 静的検査のみ。pytest を要求しない (書込可能 tmp が無い)。テスト実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- 出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
- 見出しは全部 H2 (`## `) で書く。`###` を使わない。
- 所見は 1 件ずつ「R-n / 対象 (file と節) / 主張 / 根拠 (射影 file:line または一次資料の逐語) / 放置時に成果物 (論文の C14a 行の読み方・
  記録の正しさ) がどう変わるか / 分類 (must-fix・nit・記録)」の形で書く。must-fix は放置時の影響を 1 行で書けるものだけにする (DW-G05)。
- 是正案は差分の逐語 (置換前 → 置換後) で書く。

## 出力形式
## 所見 (R-1 …)
## 逐語照合の対照表 (命題 / 記録の文 / 一次資料の逐語 / 一致・不一致)
## 探索範囲の被覆 (依頼 (a)(b)(c) と §2 の対応、抜け)
## 総括
