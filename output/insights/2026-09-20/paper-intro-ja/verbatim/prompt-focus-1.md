単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-intro-ja

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、それを理由に検査全体を打ち切っては
ならない (その path は「不在」と記録して先へ進め)。

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-intro-ja/review-out.md
  (**前巡の段 6 レビューの全文 = お前が閉じたかを判定する所見 8 件の正本**)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-intro-ja/output/insights/2026-09-20/paper-intro-ja/intro.md (fix 後の序論草稿)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-intro-ja/output/insights/2026-09-20/paper-intro-ja/contributions.md (fix 後の貢献節草稿)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-intro-ja/output/insights/2026-09-20/paper-intro-ja/limitations.md (fix 後の限界節草稿。§7 の表は
  README §5 へ移し、本文は散文にした)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-intro-ja/output/insights/2026-09-20/paper-intro-ja/README.md
  (wave の記録。§3 = 状態語の更新表 (pin 前進の行を追加)、§4 = 前巡の所見 8 件への親の裁定と fix の一覧、§5 = 限界節から移した別表)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-intro-ja/brief-s1.md (親の段 1 brief。P1 は前巡の所見 4 により不採用にした)

前巡との差分 (親の説明。信用せず現物で確かめよ):

1. 前巡のレビュー後に local main が `fec4a8187` から `482f19b88` へ進み (ccbench pin を `511c9538` から `e9e477ca` へ前進した [T-2304] wave の着地)、
   親はそれを ff-only で取り込んだ (`git -C <worktree> log --oneline -3`、`git -C <worktree> submodule status` で gitlink `e9e477ca` を確認せよ)。
   3 稿の採用時点は `482f19b88` へ更新し、pin 前進の事実 (mocc の trace v2 hook と TRACE 専用 lineage witness を含む 4 commit、較正・certified 系列・
   性能比較は含まず、旧系列は前進前の固定 checkout で継続、X/P 証明面計装は別 patch のまま) を限界 §6 と貢献の「書かないもの」へ足した。
   根拠は `output/insights/2026-09-20/t2304-pin-advance/README.md` §0〜§1 と `docs/spool/worklog/2026-09-20-dev-wave-t2304-pin-advance-1.md`、
   `output/insights/2026-09-17/t2756-pin-evidence/README.md` の 4 commit 表。**この行の状態語が D 本文・insight より強くも弱くもないことを検証せよ**
   (特に「pin が進んだ = mocc の証明面計装が pin に入った」と読ませていないか、「較正の再取得・certified 系列・性能比較は含まない」を落としていないか)。
2. 所見 1〜8 の fix は README §4 の表のとおり。

`docs/decisions.md` は 5.7 MB — 全文 `cat` 禁止。`grep -n "^## D<番号>\. "` で位置を出し `sed -n` で 60 行以内ずつ読め。
この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す (**出力は最終メッセージ本文に全文**)。
pytest・build・測定は走らせない (静的検査でよい)。予算が尽きそうなら途中までの結論を出力形式どおりに書いて終われ。無出力が最悪である。

## 検査

1. **所見ごとの closed / partial / regressed 対応表** (DW-O16、D78)。前巡の所見 1〜8 それぞれについて、fix 後の該当箇所を引用し、閉じたか、
   部分か、悪化 (別の過大・過小主張を生んだ) かを判定せよ。特に:
   - 所見 1: A-1 の文が観測値の存在を認め、かつ「正式な結果・要件充足」への昇格を否定しているか。「A-1 の値がある」(L34 が禁じる形) へ滑って
     いないか。
   - 所見 2: 貢献稿の certified の定義が L01 の保証範囲 (point read / write の観測 trace、述語・phantom・公平性・未観測実行は対象外、性能優越を
     保証しない) と一致し、限界 §2 への参照を持つか。序論第 3 幕の参照が付いたか。
   - 所見 3: 限界 §2 の検証相の文が「本走 24 + 校正完走 6 = 判定集合 30 / 候補」「校正 10 秒の未完走 2 件 / 候補は verdict を持たず集合に含まれない」
     を書き、確率主張・昇格・B-8 充足を否定しているか (`docs/paper-story/results/2026-09-20-verify-phase-adopted-backoff.md` §2〜§3、D2160 項 4〜5)。
   - 所見 4: 限界 §7 が散文になり、表が README §5 へ移ったか。§2・§4・§5・§6 から個別実験の細部 (成果物に残らない情報の列挙、後継図・未測帯、
     批准手続、準備作業件数) が減ったか。残った細部があれば列挙し、論文全体の限界として要るか (残す) / 結果稿へ委ねるべきか (削る) を判定せよ。
   - 所見 5: 貢献稿の見出しと結果ごとの角括弧が claim-evidence §1.3 の 7 値の語彙になっているか。§4 の 4 結果に別々の値が付いたか。
   - 所見 6: 出所 2 の +147.4% の説明が P2-4 稿 §3 項 7・§5.4 の記述と一致するか。
   - 所見 7: 序論 §2 と貢献 §1 が「1 文 + 3 条件 + 調査状態」に留まり、先行の比較説明・「後追いに見える」が消えたか。限界 §6 の「2 wave」が消えたか。
   - 所見 8: 限界 §4 の固定表現の直後に同じ格子の性能低下 (3 workload とも半分以下) が併記されたか。
2. **親の派生値・量化語の再検算** (DW-O16)。fix で親が新しく書いた数値・量化語 (「4 commit」「141 行」「判定集合 30」「本走 24」「校正完走 6」「未完走 2 件 / 候補」
   「3 workload とも半分以下」「1250 → 9999 µs」「4 度到達」「0 件」「2 件」「1 件」など) を、新稿の出所が指す一次資料から再計算・再照合せよ。
3. **主張の強さの整合 (レンズ B の再走)。** 3 稿の言うこと / 言わないこと / 実証状態 / 限界が fix 後も食い違っていないか。fix が新しい過大主張
   (例: 「pin が進んだ」を「クロスプロトコルへ広げた」に近づけていないか) や過小主張 (例: 「床値が取れていない」「A-1 の測定が無い」に近づけて
   いないか) を生んでいないか。
4. **凍結物と変更範囲。** `git -C <worktree> status --porcelain` で、未追跡が `output/insights/2026-09-20/paper-intro-ja/` 配下だけであること、
   `git -C <worktree> diff --stat` が空であること (版・図・results・claim-evidence・README・既存 methods / results 稿に差分が無い)。
5. **新規所見。** 前巡に無かった問題 (事実誤り、L01〜L53 / §7 チェックリストの違反、内部用語の漏れ、リンク不達) があれば所見として出せ。

## 守らせる不変条件 (これを緩める所見は refuted として扱う)

- 凍結物 (版・図・他の稿・insight・campaign 成果物) は 1 byte も変えない。図の作り直し・再測定・関連研究節・英訳は scope 外。
- 論文値は同一 sweep 内の無 backoff 対照との median 比の 3 値のままとし、他の分母の値と混ぜない。+38.5% を headline にしない (D20)。
- 当時の判定を取り消さず、新しい判定器の結果で遡って昇格もさせない (規律 7)。protocol status は成否宣告ではない (D12)。
- 現行環境の 3 走行・A-1・B-7・B-10 と pool しない (D1993 項 6)。旧 3 値の但し書き 1・3 は外れない。
- 仮想リスク向けの gate・検査・台帳・一般化は scope 外。

## 出力形式 (この見出しをそのまま使う)

## 所見対応表

前巡の所見 1〜8 について、番号ごとに `closed / partial / regressed` と根拠 (fix 後の該当箇所の引用と一次資料)。

## 新規所見

番号付き。各所見に `real / refuted`、`must-fix / should-fix / nit`、該当箇所、一次資料、対案、放置時の影響 1 行。無ければ「なし」。

## 再検算した派生値・量化語

一致 / 不一致を列挙する。

## GO / NO-GO

3 稿をこのまま凍結してよいか。NO-GO なら must-fix の一覧。

## 総括

10 行以内。
