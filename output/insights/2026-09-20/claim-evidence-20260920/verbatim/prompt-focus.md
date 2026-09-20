単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-claim-evidence-2026-09-20

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、それを理由に検査全体を打ち切ってはならない。

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-claim-evidence-2026-09-20/review-out.md (**前巡のレビュー所見 12 件の全文**。所見 1〜8 must-fix、
  9〜10 should-fix、11 nit、12 refuted)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-claim-evidence-2026-09-20/fix1.py (**親が当てた fix の逐語** — 各所見に対する置換の old / new。
  read-only で読むだけでよい。実行するな)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-claim-evidence-2026-09-20/docs/paper-story/claim-evidence/2026-09-20.md
  (**fix 後のレビュー対象**、209,728 bytes / 694 行。**全文 `cat` しないこと**。`grep -n` で該当箇所を出し `sed -n` で 20 行以内ずつ読め)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-claim-evidence-2026-09-20/docs/paper-story/README.md (claim-evidence 系列表の 1 行。
  `grep -n "2026-09-20" ` で位置を出せ)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-claim-evidence-2026-09-20/prompt-review.md (前巡の prompt。役割分担・不変条件・出力形式の正本)

一次資料 (`docs/decisions.md` の D 本文、`output/insights/…`、`results/…`、certification JSON、`output/s6-rounds/tally.json`) は前巡と同じく
自分で開け。**`docs/decisions.md` は 5.6 MB — 全文 `cat` してはならない。** `grep -n "^## D<番号>\. "` で位置を出し `sed -n` で 60 行以内ずつ読め。

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す (**出力は最終メッセージ本文に全文**)。
pytest・build・測定は走らせない。予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 役割

前巡の所見 12 件に対する親の fix を、**所見ごとに closed / partial / regressed で判定せよ** (DW-O16)。親が書いた派生値・量化
(「30 verify / 候補」「24 件 / 12 件」「36 記録」「5 つ」「53 個」「43 行」「1 件を除き」) は原データから数え直して照合するまで closed としない。
訂正で新しく入った文 (L51 / L52 / L53、L04 の復元、§7 冒頭の例外 1 件、C15c の書き換え、C5b / C5c の権威 bytes、C2 の (c)、G5、§5.2 の
2 段落、B-8 の状態語、C25 の (e)) にも同じ検算を掛け、**fix が新しい誤りや過大主張を持ち込んでいないか (regressed) を見よ。**

親の実走: fix 後に `tools/check_docs.py` rc=0、repo 内 path 93 件の実在 (欠 1 = 保存 branch 上の g1 候補、稿がそう書く)、`git diff --check` rc=0、
新規引用の D1529 / D1866 / D2020 / D2021 / D2026 / D2080 / D2090 の実在。

親の判定 (攻撃対象): 所見 1〜11 を real として採用し fix した。所見 12 (P1 / P3 の差し戻し不要) はレビュー自身が refuted としており、
親も構造を維持したうえで「上位互換」の文言だけを「別 attempt で正式 protocol を完走した観測」へ改めた。

特に確かめること:
1. 所見 1: §5.2 の fixed 5 µs の段落が `output/insights/2026-09-19_t1998-b7-fixed5-three-workload/certification.json` の
   `legacy_repetitions_observed` / `performance_repetitions_observed` と一致するか。C26 の (a)(d) と食い違わないか。
2. 所見 2: §5.2 と C2 (b) の件数が候補ごと / attempt ごとの母集合を正しく持つか (summary-B-fix1.json、A-2 4 cell × 6、A-6 2 cell × 6)。
3. 所見 4: C2 の (c) の変更が §1.3 の 7 値の説明、§7 の C2 行・末尾の「3 つ」、L01 の適用行と整合するか。C2 が「実証済み」の行から
   外れたことで §4.1 / §5.2 / §2.4 のどこかに矛盾が出ていないか。
4. 所見 5: C21 (d) と L34 の時系列が D2156 項 3 と一致し、C31 / L36 / §2.4 / §4.2 / §5.1 の A-1 の状態語と矛盾しないか。
5. 所見 7: §7 冒頭の例外 1 件の書き方が `output/insights/2026-09-16/layer3-screening-currency/README.md` の「3 つを混ぜない」と
   一致し、L49・C11 (d)・L18・§7 表の C11 行と整合するか。前稿の C11 の文 (`claim-evidence/2026-08-26.md` の C11 行) を実際に読み、
   「執筆時点で既に偽だった」の認定が一次資料 (commit `b8318b956` / `ed251424d` の日付 = 2026-08-25) で支持されるか
   (`git -C <worktree> log -1 --format=%ci b8318b956` を許す)。
6. 所見 8: L51 / L52 / L53 の本文が D1529 / D2090 / D2026 / D1637 / D1866 / D2080 の内容を逐語の範囲で正しく写しているか、
   L04 の復元文が前稿 L04 と同じ趣旨か。§3 末尾の「5 件」の列挙が所見 8 の表と一致するか。
7. 所見 9: B-8 の状態語 (§4.3) と C25 (e)・L40・§2.4・§6 が同じ状態を言っているか。
8. 所見 10: `output/s6-rounds/tally.json` の値 (0.11538461538461539 / 1.0、eligible_counts 20 / 17 / 20) と C5b / C5c の (b) の一致。
9. 所見 11: §3 末尾の表が 5 行 (L05 / L21 / L24 / L27 / L49) で、§6 の該当 bullet と一致するか。L の総数 53、欠番無し、行 43。
10. README の行が `L29`〜`L53` になっているか。版の履歴表に変更が無いか (`git -C <worktree> diff -- docs/paper-story/README.md`)。

## 守らせる不変条件 (前巡と同じ)

凍結物は 1 byte も変えない。旧 attempt の判定を取り消さない。protocol status は成否宣告ではない (D12)。規律 7。B-10 は事前登録 §4.5 の
固定表現に限る。B-7 は充足と書かない。3 走行・A-1・B-7 fixed5 を pool しない。「A-1 の値がある」「B-10 を閉じた」「mocc は第 2 成功例」
「床値が発効した」とは書かない。検証相は性能値を含まず既存判定を昇格させない。gate・検査・台帳・一般化・隣接 docs の訂正・英語化は scope 外。

## 出力形式 (この見出しをそのまま使う)

## 所見対応表

前巡の所見 1〜12 それぞれについて `closed / partial / regressed` と、その根拠 (照合した一次資料の path または D 番号、数え直した件数) を
1 行ずつ。partial / regressed には対案 (訂正後の文面) を書け。

## 新規所見

fix が持ち込んだ誤り・過大主張・不整合があれば番号付きで `real / refuted`、`must-fix / should-fix / nit`、該当箇所、一次資料、対案、
放置時の影響 1 行。無ければ「無し」と書け。

## 照合して一致を確認した範囲

消極的な証拠として列挙せよ。

## GO / NO-GO

fix 後の新稿をこのまま凍結してよいか。NO-GO なら残る must-fix の一覧。

## 総括

10 行以内。
