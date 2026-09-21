単独段 dispatch: stage=focus-review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-b8

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。** この停止規則は列挙した射影 file に
だけ掛かる。自分で探した path が不在でも検査全体を打ち切らず「不在」と記録して先へ進め。

W = /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-b8 (対象は commit `5326ad4ab` に固定。作業ツリーは clean)

- W/output/insights/2026-09-21/paper-methods-ja/verbatim/s6-review.md (**1 巡目のレビュー報告の逐語**。所見 S1〜S4 / N1〜N9 の正本)
- W/output/insights/2026-09-21/paper-methods-ja/verbatim/s6-review-prompt.md (1 巡目の prompt。資料一覧・巨大 file の扱い・2 レンズは同じものを使え)
- W/output/insights/2026-09-21/paper-methods-ja/README.md §4 (親の裁定表。S1〜S4・N1〜N8 = 採用、N9 = 不採用)
- fix の差分: `git -C W diff 784db3f02 5326ad4ab` (対象 3 file と verbatim 2 file の追加)。fix 後の全文は W/output/insights/2026-09-21/paper-methods-ja/{methods,implementation,README}.md
- 一次資料は 1 巡目の prompt の一覧と同じ (B-8 結果稿、t2807-b8-effective README、B-8 事前登録 v1、t2795-k2-pair-attempt README、t2795-pair-repair README、
  B-5 事前登録 §0、decisions.md の D2158 / D2172 / D2175 / D2186 / D2187 / D2190 / D2194 / D2200 / D2202 / D2205 / D2206、worklog archive の該当 entry)。
  `docs/decisions.md` (70,675 行) は全文を読まず、`grep -n "^## D<番号>\. "` と 60 行以内の `sed -n` で読め。

この段では commit・push・file の書き込みを一切行わない。成果は最終メッセージの本文だけで返す。pytest・build・測定は走らせない。
git は read-only の log / show / diff だけ。予算が尽きそうなら途中までの結論を下記の形式で書いて終われ。無出力が最悪である。

## 何を確かめるか (焦点再レビュー、`DW-O16`)

お前は 1 巡目と別の独立 context の子である (Codex 利用上限のため Claude で代替。同系統モデル)。親の fix を信用せず確かめよ。

1. **対応表:** 1 巡目の所見 S1〜S4・N1〜N9 のそれぞれについて `closed` / `partial` / `regressed` / `不採用が妥当` / `不採用が不当` を
   判定し、根拠 (fix 後の file:行 と一次資料の節) を 1 行ずつ書け。表なしで閉じたと判定してはならない。
2. **fix が持ち込んだ新しい誤り:** fix で足した文 (K2 の checkout 手順・D1777・submit-tree `6a3e15809`・`ccbench_commit`、bench 失敗の規則の出所
   §5 / D2190 項 3 (b)、未確定の列挙と D2190 項 3 (c)、`effective` 節の内訳、D2202 項 2 の「各 1 値」、stub の範囲、件数 0 の併記、
   出所の並べ替え、README §3 の追加 2 行、README §4 の裁定表) を一次資料と 1 対 1 で照合せよ。
3. **親が書いた派生値・量化の再計算:** README §4 の件数 (must-fix 0 / should-fix 4 / nit 9 / refuted 24、所要 818 秒・道具 68 回は完了通知の値なので照合不要)、
   README §2 の「B-8 の 9 段落と判定の 3 項」(methods §3 の B-8 部分を実際に数えよ)、README §3 の表の「型」、implementation の確認点節の
   「should-fix 4 件と nit 8 件を反映」、「継承部分で『本稿の時点』と書いていた 2 箇所 / 4 箇所」の数を、現物から数え直して照合せよ。
4. **規律 2 の向き:** fix 後の B-8 の規則の記述が一次資料より弱くなっていないか、逆に一次資料に無い規則を足していないかを再確認せよ。
5. 1 巡目で refuted だった攻撃 (判定集合 30 枠の帰属、K2 の D2187 / D2205 の区別、B-5 の未認可、scope 越え) が fix で破れていないか。

## 出力形式

先頭行に `VERDICT: GO` または `VERDICT: NO-GO` (新規 must-fix か regressed が 1 件でもあれば NO-GO)。続けて対応表
(`| 所見 | 判定 | 根拠 |`)、次に新規所見を `[must-fix|should-fix|nit] <file>:<行> — <問題> / 根拠 / 直し方` で、最後に再計算した派生値の
一覧 (値・数え方・一致 / 不一致) を書け。
