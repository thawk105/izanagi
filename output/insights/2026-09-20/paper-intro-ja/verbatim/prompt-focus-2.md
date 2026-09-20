単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-intro-ja

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-intro-ja/focus-out.md
  (**前巡 (2 巡目) の焦点再レビューの全文。前々巡の所見 8 件は closed と判定済み。お前が閉じたかを判定するのは、その「新規所見」1・2 の 2 件と、
  所見 4 の「削ることを推奨」への親の対応だけ**)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-intro-ja/output/insights/2026-09-20/paper-intro-ja/limitations.md (fix 後の限界節草稿)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-intro-ja/output/insights/2026-09-20/paper-intro-ja/contributions.md (fix 後の貢献節草稿)

親の fix (信用せず現物で確かめよ):

1. 新規所見 1 (must-fix): 限界 §3 の「合成ループは現行の素材コーパスの下で certified の終端判定へ 4 度到達した」を
   「合成ループは、pin 前進前の CCBench `511c9538` の下で certified の終端判定へ 4 度到達した」へ直した (対案どおり)。
2. 新規所見 2 (should-fix): 貢献「貢献として書かないもの」の pin 前進の文に「その前進に較正の再取得・mocc の certified 系列・性能比較は含まれず」を足した。
3. 所見 4 の推奨のうち、限界 §5 の B-4 推定対象の細かな説明を 1 文に圧縮した。floor 案の絶対値 2 個と CV 3 値は、「配線下限で決まった」「3 つの量は別」を
   数値で示すために残した (親の判断。推奨は「再開理由にしない」とされているので、残したことを所見にするなら nit とせよ)。

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す (**出力は最終メッセージ本文に全文**)。
pytest・build・測定は走らせない。`git -C <worktree>` / `grep` / `sed -n` は使ってよい。予算が尽きそうなら途中までの結論を出力形式どおりに書いて終われ。

## 検査

1. 前巡の新規所見 1・2 が closed / partial / regressed のどれかを、fix 後の該当箇所の引用で判定せよ。fix が新しい過大・過小主張を生んでいないか
   (特に「pin 前進前の CCBench 511c9538 の下で」が、限界 §6 の pin 前進の記述と矛盾しないか、K2 3 巡の WAL の `build_start` pin と一致するか)。
2. fix の周辺 (限界 §3・§5・§6、貢献の「書かないもの」) に、fix によって崩れた文・二重表現・リンク不達が無いか。
3. `git -C <worktree> status --porcelain` で未追跡が `output/insights/2026-09-20/paper-intro-ja/` 配下だけ、`git -C <worktree> diff --stat` が空であること。

## 出力形式 (この見出しをそのまま使う)

## 所見対応表

前巡の新規所見 1・2 と、所見 4 の推奨への対応について `closed / partial / regressed` と根拠。

## 新規所見

無ければ「なし」。あれば番号付きで `real / refuted`、`must-fix / should-fix / nit`、該当箇所、一次資料、対案、放置時の影響 1 行。

## GO / NO-GO

3 稿をこのまま凍結してよいか。

## 総括

5 行以内。
