単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2321-b10-value-errata

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/99abd453/tmp/codex/dev-wave-t2321-b10-value-errata/brief.md (親 brief、検査対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/99abd453/tmp/codex/dev-wave-t2321-b10-value-errata/projection/proposed-edits.md (追記文言案、検査対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/99abd453/tmp/codex/dev-wave-t2321-b10-value-errata/projection/wal-ed8a676b-extract.tsv (一次資料 WAL の抜粋 33 行。列 = epoch 秒 / UTC 時刻 / stage / variant / tag / verdict / certified。JST は UTC + 9 時間。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/99abd453/tmp/codex/dev-wave-t2321-b10-value-errata/projection/scheduler-stderr-965996.txt (一次資料 scheduler.stderr の逐語。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2321-b10-value-errata/output/insights/2026-09-03/t1905-b10-road-and-balanced/README.md (訂正対象 A1。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2321-b10-value-errata/docs/b10-multinode-formal-run-design.md (訂正対象 A2 / B1 / B2。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2321-b10-value-errata/output/insights/2026-08-31_t1905-b10-formal-run/README.md (訂正対象 B2。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2321-b10-value-errata/output/insights/2026-09-02/t2229-t2230-verify-cost-erratum/README.md (訂正対象 B2。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2321-b10-value-errata/output/insights/2026-09-02/t1905-b10-multinode-design/README.md (訂正対象 B2。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2321-b10-value-errata/output/insights/2026-09-02_paper-story-a6-certification/README.md (訂正対象 B2、EOF 節形式。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2321-b10-value-errata/docs/archive/worklog-phase3-0904-1262.md (T-2202 の実績と T-2321 / T-2322 の起票文。scope の正本。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2321-b10-value-errata/output/insights/2026-09-04/t2202-missing-population-caveats/README.md (前回の但し書き wave の記録: 形の裁定 (主張直後の blockquote)、対象外の裁定。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2321-b10-value-errata/docs/skill-self-improvement.md (routing の正本。「同じ内容を複数の行き先へ全文複製しない」。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2321-b10-value-errata/CLAUDE.md (絶対規律 7 と「盛らない」(規律 5) の正本。読めなければ即停止)

## 目的
これは自分たちの研究記録 (材料レポートと設計文書) の docs-only 追記訂正の設計レビューである。B-10 read-heavy 正式走 (request `965996`、campaign `ed8a676b`) の記録に残る 2 つの値 —「24 反復」(一次資料は `verify_done` 22 = 初期確認 4 + 本規模 18、表の本規模は 18) と「5 時間 5 分」(計測区間が未確定) — を、絶対規律 7 に従う追記 (削除 0 行) で訂正する計画 (proposed-edits.md) と親 brief を、**レンズ B = 過剰・削除**で点検する。ユーザーの引数は「本題の追記訂正だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」である。計画を守らせるのではなく、過剰と scope 逸脱を指摘するのが役目である。親 brief 自身も検査対象である。

## レンズ B の問い (過剰・削除)
1. **実測欠陥への対応**: 各追記 (A1 / A2 / B1 / B2) は、起票された誤り (「24 反復」の値、「5 時間 5 分」の区間未確定) に直接対応しているか。対応に不要な記述 (時刻列の全列挙、解説、重複する免責文) を挙げ、意味を保ったまま削れる最短の文言を文字数付きで提案せよ。特に B1 (全文版、約 450 字) は各箇所の読み手に要るか、insight README へ寄せて各箇所は 2〜3 文で足りるかを判定せよ。
2. **(P1) 追記先の数**: 「5 時間 5 分」の追記を担い手 6 箇所全部に入れる親の provisional 裁定は scope 内か。ユーザー引数は file を 2 つ名指しし、「あわせて計測区間を一次資料から確定する」としか言っていない。(a) 設計文書 §1・§4 の 2 箇所だけ、(b) 6 箇所全部、(c) 設計文書 2 箇所 + insight README への集約 (残り 4 箇所は触らない) の 3 案について、放置時に成果物 (論文が引く値・読み手が届く但し書き) がどう変わるかを比べ、推奨を 1 つ示せ。T-2202 が「読み手が値を読んだ同じ節で但し書きに届く」ことを最重要所見にした経緯 (t2202 README) を踏まえよ。
3. **(P5) decisions への言及**: decisions fragment で「D1605 理由節の『24 反復ぶん』も同じ誤値で本 D が訂正する」と書く案は、T-2322 (decisions.md の同じ主張の担い手に但し書きを付けるか = ユーザー裁定待ち) の scope と衝突しないか。衝突するなら、decisions fragment は D1605 に触れずに済ませられるか、それとも「24 反復」の訂正を記録する D 自体が不要 (worklog fragment と insight で足りる) かを判定せよ。
4. **scope 膨張**: 成果物一覧 (対象 file の追記、insight README + verbatim、worklog fragment、decisions fragment) のうち必要最小は何か。insight README は「時刻列の根拠」の置き場として必要か、対象箇所の追記だけで自足するか。
5. **全文複製**: B1 (全文) + B2 (短文 × 5) の形は routing 5 「同じ内容を複数の行き先へ全文複製しない」に照らして妥当か。参照 (`docs/b10-multinode-formal-run-design.md` §1 の同名訂正) で足りる箇所を挙げよ。
6. **見出し語の過剰**: 「訂正」「区間の確定」という見出し語は、規律 7 (過去の値・判定は追記でのみ訂正) の範囲内か。「確定」が実際に確定できていない部分 (観測時刻の分単位) まで覆って読めるなら、より弱い語 (「区間の位置づけ」等) を提案せよ。
7. **段 6 レビュー子の省略**: brief の分割方針 (実装子なし、段 3 相談 2 本、段 6 レビュー子省略) は DW-C00 の軽量版として妥当か。docs-only で受理集合・正しさ防壁に触れないことを確認し、必要なら反証せよ。
8. **親の実測値とその一般化**: brief の「5 時間 5 分 ≈ 18,300 秒は走行中観測」を、他の箇所の値 (D1480 等の「約 23 時間」外挿、「CPU/経過 = 1.0」) の訂正へ一般化していないか。していれば scope 外として挙げよ。

## 制約
- 静的検査のみ。pytest を要求しない (書込可能 tmp が無い)。テスト実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- 出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
- 見出しは全部 H2 (`## `) で書く。`###` を使わない。
- 所見は 1 件ずつ「B-n / 対象 (file:line または brief の P 番号) / 主張 / 根拠 / 放置時に成果物 (論文が引く値・読み手が届く但し書き) がどう変わるか / 推奨 (採用・条件付き・却下)」の形で書く。根拠を示せない scope 外所見は起票せず「記録のみ」と印を付けよ。

## 出力形式
## 所見 (B-1 …)
## より短い文言の提案 (文字数付き、対象箇所ごと)
## P1 / P5 の推奨
## 総括
