単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2501-exploration-terms

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/f5ab0160/tmp/codex/dev-wave-t2501-exploration-terms/projection/commit-1.patch (レビュー対象 = commit a9ca20cbe の差分全文。runbook `### 7.9` 新設 + §8 の 1 句 + glossary 1 項目。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2501-exploration-terms/docs/pegasus-runbook.md (差分適用後の runbook。`### 7.9` と `## 8.` の該当項目を文脈ごと読む。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2501-exploration-terms/docs/glossary.md (差分適用後の glossary。§4 の新項目と前後の項目の書式を読む。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f5ab0160/tmp/codex/dev-wave-t2501-exploration-terms/projection/T-2501-origin.md (依頼文と起票行の逐語。scope の正本。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f5ab0160/tmp/codex/dev-wave-t2501-exploration-terms/brief.md (親 brief。親 brief 自身も検査対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f5ab0160/tmp/codex/dev-wave-t2501-exploration-terms/adjudication.md (段 4 裁定。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f5ab0160/tmp/codex/dev-wave-t2501-exploration-terms/projection/parent-measurements.md (親が grep で実測した根拠の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f5ab0160/tmp/codex/dev-wave-t2501-exploration-terms/projection/D1879.md (本 wave の根拠裁定。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f5ab0160/tmp/codex/dev-wave-t2501-exploration-terms/projection/D1813.md (「探索」の定義元。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f5ab0160/tmp/codex/dev-wave-t2501-exploration-terms/projection/D1848.md (探索走の実装裁定。理由 5 項目目と却下肢 3。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f5ab0160/tmp/codex/dev-wave-t2501-exploration-terms/projection/D528.md (`declared_use_class` の閉表と宣言由来の族。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f5ab0160/tmp/codex/dev-wave-t2501-exploration-terms/projection/D123.md (exploration namespace への前向き移行と族の列挙。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f5ab0160/tmp/codex/dev-wave-t2501-exploration-terms/projection/D158.md (exploration root の env seam。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f5ab0160/tmp/codex/dev-wave-t2501-exploration-terms/projection/D1859.md (広げてはいけない裁定。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2501-exploration-terms/docs/orchestrator-design.md (「campaign スコープの実際の root は namespace で 2 つある」の段落と次の段落。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2501-exploration-terms/output/insights/2026-09-09_t2418-backoff-static-explore/README.md (探索走の一次資料。§1 / §5 / §10 / §11。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2501-exploration-terms/docs/b10-backoff-static-tail-submission.md (第 2 段の投入手順。`--explore-campaign` の意味。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2501-exploration-terms/orchestrator/campaign/layout.py (use class と 2 つの env の解決規則の正本。read-only で読む。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2501-exploration-terms/tools/pegasus/submit_b10_backoff_grid.sh (`--explore-campaign` の受理条件。読めなければ即停止)

## 目的
これは自分たちの文書の設計レビューである。docs-only wave (T-2501) が、runbook の「exploration campaign」(campaign layout の use class) と
D1813 の「探索」(標本への帰属) が別語であることを、`docs/pegasus-runbook.md` の新節 `### 7.9` と `docs/glossary.md` の 1 項目に書いた。
親 (Claude) が一次資料 (code・裁定・insight) から事実を再抽出して起草した。**欠陥を指摘するのが役目で、差分を追認するものではない。**
レンズは 2 つを 1 本で担う:
(A) 正しさ境界・整合 — 新節と glossary 項目の事実命題 (関数名・環境変数名・module 名・field 名・裁定番号・「〜は official」「〜を export する」
「閉表は 4 値」「materialize できるのは 2 値」「D123 の列挙 6 driver には無い」「第 3 の RUN_KIND」「docstring が『探索専用 layout』と書く」
「検査文言 `mode source must be exploration`」など) が一次資料 (layout.py / backoff_extended_sweep.py / b10_backoff_static_tail_formal.py /
job script / D 各条 / T-2418 insight / 設計文書) と一致するか。裁定の引用 (D1879 / D1848 理由 5 項目目・却下肢 3 / D528 決定 5・7 / D158 / D123) が
原文の意味を変えていないか。
(B) 過剰・削除・規律 — 依頼の scope (語の整理だけ。凍結成果物・正式 consumer の受理集合・`run_kind` 必須化・コードに触れない。D1859 を
全経路の保証へ広げない。gate・検査・台帳・一般化を足さない) を超えた文 (新しい規則・要求・検査・「〜しなければならない」型の運用命令・
将来提案) が紛れていないか。逆に依頼が求めた「両語の定義と対応を 1 節で」が果たされているか (定義 2 つ・対応・読み分けが揃うか)。
規律 2 (正しさゲートを緩めない) に触れる文が無いか。glossary は専門外の読み手向けの横断文書なので、機体固有の path・値 (例: `/work/...`) が
入っていないか、runbook 節への委譲が適切か。

## 親が実行済みのこと
- 段 1 brief と段 4 裁定 (射影)。段 2・3 は軽量版で省略 (設計択一が割れず、正しさ防壁に触れず、受理集合も変わらない)。実装面の差分ゼロで
  変異 matrix 免除 (DW-S04)。受入全走は記録 commit 後の tip で親が 1 走する。
- `tools/check_docs.py` 違反なし、`check_ai_provenance.py` 全史 rc=0。差分は commit a9ca20cbe 済み (fix は別 commit にする)。
- 親の grep 実測は parent-measurements.md にある。**実測されていないのは**: 各 producer が実際に `run_campaign` へ渡す値の実行時の経路 (静的 grep のみ)、
  A-1 対測定の標本が「正式」か否か (本節では判定しない、と書いた)、`docs/b10-backoff-static-tail-preregistration.md` の第 2 段が投入済みか否か。

## 問い
1. **事実命題の逐語照合**: 新節 `### 7.9` の各段落と表の各 cell、glossary 項目の各文について、一次資料の逐語 (file:line または D の文) と
   突き合わせ、食い違い・過剰一般化・出所の取り違えを全部挙げよ。特に (a) 「`official` の base は明示引数か `IZANAGI_OFFICIAL_OUTPUT_ROOT` で
   repo 内への fallback は無い」、(b) 「`exploration` は明示引数 > env > repo 既定 (`output/`) で process 内で最初の解決値に pin」、
   (c) 「namespace marker で official consumer が拒否する側」、(d) 「A-1 対測定 `paper_story_a1_paired` は `exploration` を宣言し job script が
   `IZANAGI_EXPLORATION_OUTPUT_ROOT` を export」、(e) 「探索走の `declared_use_class` は `official`、job 本体は `IZANAGI_OFFICIAL_OUTPUT_ROOT` を export」、
   (f) 「`--explore-campaign` は `t2500-tail-formal` 限定で探索走の campaign directory を指し、本走は mode の比較にだけ使う」、
   (g) 「`mode source must be exploration` は `run_kind == "t2418-explore"` の要求」、(h) campaign directory の形
   `<output parent>/<group>-<workload>/campaigns/<id>/` (submit script と layout の official 形から導けるか)。
2. **裁定の引用の忠実性**: D1879 (採る 1 件・採らない 2 件)、D1848 (理由 5 項目目・却下肢 3)、D528 (決定 5・7、閉表 4 値と materialize 2 値)、
   D123 (列挙 6 driver)、D158 (env seam) の引用が、原文の主語・範囲・条件を落としたり足したりしていないか。
3. **scope 超過**: 新節・glossary・§8 の 1 句に、新しい運用規則・要求・検査・将来提案・「〜すべき」に当たる文があるか。D1859 の射程を広げる文が
   あるか。凍結成果物・受理集合・`run_kind` の扱いを変える読みができる文があるか。
4. **欠落と読みやすさ**: 依頼の「両語の定義と対応を 1 節で」に対し、定義 A・定義 B・対応表・読み分けのどれかが欠けたり、逆に 1 節に収まらず
   分散していないか。第 3 の表記 (`--explore-campaign`、code docstring の「探索」、検査文言) を入れたことは読み手の誤解を減らすか増やすか。
   glossary 項目が glossary の既存書式 (`**用語 (読み)** — 一般定義。*izanagi:* 固有の意味`) に沿うか、専門外の読み手に読めるか、機体固有値を
   含まないか。§8 の 1 句が checklist 項目の意味を変えていないか。
5. **親 brief と裁定自身**: brief.md / adjudication.md の前提 (段 2・3 省略の 3 条件、review 1 本の根拠、P1〜P3、「7 module」等の件数) に
   検証されていない一般化・件数の過信があれば挙げよ。

## 制約
- 静的検査のみ。pytest を要求しない (書込可能 tmp が無い)。テスト実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- 出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
- 見出しは全部 H2 (`## `) で書く。`###` を使わない。最後の節は必ず `## 総括` (`#` を 2 個) とする。
- 所見は 1 件ずつ「R-n / 対象 (file と節・cell) / 主張 / 根拠 (一次資料の file:line または D の逐語) / 放置時に成果物 (runbook・glossary の
  読み手の理解、論文 B-10 記述の正しさ) がどう変わるか / 分類 (must-fix・should・nit・記録)」の形で書く。must-fix は放置時の影響を
  1 行で書けるものだけにする (DW-G05)。
- 是正案は差分の逐語 (置換前 → 置換後) で書く。

## 出力形式
## 所見 (R-1 …)
## 逐語照合の対照表 (命題 / 新節・glossary の文 / 一次資料の逐語 / 一致・不一致)
## 裁定引用の忠実性 (問い 2)
## scope 超過と欠落 (問い 3・4)
## 総括
