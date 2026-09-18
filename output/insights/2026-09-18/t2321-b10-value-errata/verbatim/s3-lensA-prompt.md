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
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2321-b10-value-errata/docs/archive/worklog-phase3-0902-1187.md (同時代記録: 撤去判断時の観測値「5 時間 5 分」「CPU 時間 17,909 秒 / 経過 18,196 秒」。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2321-b10-value-errata/output/insights/2026-09-02/b10-missing-iterations-scope/README.md (WAL 集計の先行一次資料: verify_done 22、空白 264 秒、Elapse 表。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2321-b10-value-errata/docs/archive/worklog-phase3-0904-1262.md (T-2202 の実績と T-2321 / T-2322 の起票文。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2321-b10-value-errata/CLAUDE.md (絶対規律 7「測定時点の事実と、現行コードへの適合を分ける」の正本。読めなければ即停止)

## 目的
これは自分たちの研究記録 (材料レポートと設計文書) の docs-only 追記訂正の設計レビューである。B-10 read-heavy 正式走 (request `965996`、campaign `ed8a676b`) の記録に残る 2 つの値 —「24 反復」(一次資料は `verify_done` 22 = 初期確認 4 + 本規模 18、表の本規模は 18) と「5 時間 5 分」(計測区間が未確定) — を、絶対規律 7 に従う追記 (削除 0 行) で訂正する計画 (proposed-edits.md) と親 brief を、**レンズ A = 正しさ境界・整合・実効性**で点検する。計画を守らせるのではなく、欠陥を指摘するのが役目である。親 brief 自身も検査対象である。

## レンズ A の問い (正しさ境界・整合・実効性)
1. **一次資料との一致 (再計算)**: proposed-edits.md の全数値 (22 / 4 / 18 / 5+5+5+3、JST 時刻、開始からの秒数 16,387 / 17,906 / 19,253 / 20,682、時分秒表記、Elapse 20950S、Remaining 22250S) を WAL 抜粋と scheduler.stderr から独立に再計算し、1 秒でも違うもの、丸めの向きが不明瞭なもの、表記ゆれを挙げよ。「開始」の基準を Started Request Time 01:07:49 に置いていることが妥当か (WAL 先頭 01:08:17 や Created 01:07:40 を基準にすると各値がどう変わるか) も示せ。
2. **「5 時間 5 分」の位置づけの論理**: 「WAL のどの記録境界とも一致しない → 撤去判断時の走行中観測での request 経過時間」という推論は妥当か。18,300 秒 (± 30 秒) に一致する区間が、別の起点・終点の組合せ (WAL 先頭、3 変種目 commit、4 変種目 build_start、各 verify_done、Ended、CPU 時間 17,909 秒との関係など) に存在しないか、全組合せを検算せよ。存在すれば「走行中観測」の断定は誤りである。
3. **「確定」の語と凍結但し書きの両立**: 追記の見出し「区間の確定」は、T-2202 の凍結但し書き「計測区間は現記録から確定できない」と矛盾して読めないか。確定できたもの (3 変種完了までの秒数、最後の記録までの秒数、request 全体) と確定できないもの (観測時刻の分単位) の書き分けは十分か。過剰に「確定」と言っている部分があれば指摘し、規律 7 に沿う言い方を提案せよ。
4. **範囲の書き分け (22 と 18)**: 「24 → 22」の一律置換になっていないか。road-and-balanced README L29 の表「24 反復ぶん」と L42「全 24 反復が certified」、設計文書 L136-137「24 反復ぶん」が、それぞれ文脈上「本規模 (18)」を指すのか「campaign 記録全体 (22)」を指すのかを判定し、訂正文の対応 (A1 / A2) が各箇所の文脈と合っているかを示せ。L42「全 24 反復が certified」を「22 反復すべてが certified」と訂正するとき、legacy 4 反復も certified=true であることを WAL 抜粋で確認せよ。
5. **規律 7・D1529 との整合**: 各追記に「値を無効にしない」「欠測 attempt を除いた再計算はしていない」「既存行は書き換えない」が入っているか。追記が T-2202 の但し書きの意味を変える (書き換えに当たる) 箇所がないか。「訂正」と「但し書き」の関係 (但し書きが「誤りのまま」と書いたことは今も真で、訂正はその後の追記である) が読み手に伝わるか。
6. **親の実測値とその一般化**: brief の「担い手 6 箇所」「24 反復 3 箇所」の閉包は完全か。worktree 内で同じ「5 時間 5 分」「24 反復 (read-heavy の反復数の意味で)」を本文に持つ file が、brief が挙げたもの・`docs/decisions.md` D1605・`docs/archive/`・`verbatim/` 以外に無いか (`docs/paper-story/`、`output/insights/layout-index/`、他 insight を検索せよ)。あれば file:line を挙げよ。
7. **成果物影響**: 各所見について、放置したとき成果物 (論文が引く材料レポートの値、certified の数、所要の見積り) がどう変わるかを 1 行で示せ。示せない所見は nit とせよ。

## 制約
- 静的検査のみ。pytest を要求しない (書込可能 tmp が無い)。テスト実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- 出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
- 見出しは全部 H2 (`## `) で書く。`###` を使わない。
- 所見は 1 件ずつ「A-n / 対象 (file:line または brief の P 番号) / 主張 / 根拠 (一次資料の行・値) / 放置時に成果物がどう変わるか / 推奨 (採用・条件付き・却下)」の形で書く。

## 出力形式
## 再計算表 (proposed-edits の各数値 / 独立再計算値 / 一致・不一致)
## 所見 (A-1 …)
## 修正文言の提案 (対象箇所ごと)
## 総括
