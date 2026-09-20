# 段 6 レビュー 1 巡目 (s6-review-1.md) の所見ごとの対応表 — 親 (Claude) が docs-only で本文を直した (2026-09-20 14:2x JST)

| 所見 | 裁定 | 対応 | 状態 |
|---|---|---|---|
| must-fix 1 [S-03] BACK_OFF=0 のみ | real | S-03 を「witness off では BACK_OFF=0 / 1 の両方で signal、witness on では 0」に差し替え。evidence-map S-03 に C §3.2 bo1 2/120・D §2.2 nowit-bo1 1/60 を追加 | closed |
| must-fix 2 [S-02][S-41][S-57] 全件 tid 差 1 | real | 21 走の verifier.json を機械再計算 (job dir `artifacts/recheck_21_cycles.{py,log}`): 同 epoch 21/21、tid 差 1 = 20、差 2 = 1 (C §3.4 B2/069)。S-02 / S-41 / S-57 を「20 of 21」に書き換え。evidence-map S-02 / S-41 / S-57 に R1 (再計算) を追加 | closed |
| must-fix 3 [S-02] 「全走で 21 件」 | real | 「表にした 4 実験の合計 21、08-26 記録の先行 pilot 1 件は含めない」に限定 | closed |
| must-fix 4 [S-15] 非有意を「率を変えなかった」 | real | 「3/40 vs 2/40 (片側 Fisher p = 0.500)、効果なしは言えない」に差し替え | closed |
| must-fix 5 [S-55] 前提の英訳と RLL 条件 | real (ただし原典の解決あり) | 原典 = T-2774 段 2 plan 逐語 (`verbatim/s2-plan.md` 24 行「互いの read key は自分の write set に含めない」、34 行「cold・RLL 空・各 write set 一要素」)。README §3 の「相手の」は plan の「互いの」の略記ずれ。S-55 を「our internal derivation proposes …」の形にし、前提を plan の逐語に合わせて 4 つ全部 (x≠y、自分の read key を自分の write set に含めない = R は x を書かず W は y を書かない、cold + RLL 空 + 各 write set 一要素、W の y 検査が R の y 施錠より先) 明記、末尾に「実走で実証していない」。S-54 に `searchWriteSet(...) == nullptr` (1024–1025 行) を追加。evidence-map S-55 を plan 逐語の出所に差し替え | closed (例は撤去せず、原典で前提を確定して保持) |
| must-fix 6 [S-05] TRACE 内追加の検算を全 producer へ拡張 | real | S-05 を「master は走らせていない。S-14 は base fork commit e9e477ca の 1 file の静的比較で、計装 / 診断 / 軽量 witness は別に記述」に差し替え | closed |
| must-fix 7 [S-27] 軽量 witness の lock 保持中の処理 | real | decode + abort + push が publish〜unlock に残ること、初回・capacity 増大時の reserve が write lock 保持中であること、timing は未計測、を追記 | closed |
| must-fix 8 [S-46] 率の範囲 | real | CP 上限 3 値だけを残し、「率 0.02–0.06」と「unremarkable」を削除 | closed |
| should 1 [S-30] | real | 「09-18 の 2 行」に限定し、「個別 trace 検査の label で mocc の認証ではない」を追記 | closed |
| should 2 用語定義 | real | S-20 冒頭に arm / block の定義、S-26 に supported / contradicted の意味を追記 | closed |
| should 3 [S-33] equally consistent | real | 「compatible with … but also with sampling variability; the data do not distinguish」に差し替え、lock 保持中の出力を first witness に限定 | closed |
| should 4 [S-61] runner の所在 | real | 「checker は repo、runner は experiment archive (repo 内は写し)」に差し替え | closed |
| should 5 fetch 日付 | real | draft S-14 は commit 日時 + 「fetch date is not recorded」。brief / s4-ruling の「fetch」表現を「commit 日時、fetch 日は未記録」に修正 | closed |
| nit 1 [S-16] | real | 「Baseline configure defines, with the BACK_OFF=1 substitution described next」に差し替え | closed |
| (親の再計算で見つけた追加訂正) [S-02][S-40] integrity clean | 親発見 | 再計算で `integrity.clean` が true 16 / false 5 (T-2774 の X/P 無し 2 arm の 5 走。全 counter は 0、`clean()` は X/P の text evidence 存在も要求 — model.py `Integrity.clean()` / `certification_gate_satisfied()`)。S-02 を「every integrity counter at zero」、S-40 を counter 全 0 + clean flag の 16 / 5 内訳と理由に書き換え。evidence-map S-40 に L2 の該当関数と R1 を追加 | closed |

# 焦点再レビュー 1 巡目 (s6-focus-1.md: closed 11 / partial 3 / regressed 1、残 must-fix 2、NO-GO) への対応 (14:1x JST)

| 所見 | 裁定 | 対応 | 状態 |
|---|---|---|---|
| must-fix 1 (S-55 を「同義の英訳」と確定できない) | real | S-55 をレビューの差し替え案に沿って「plan の操作指定 (W は y を読み x だけ書く、R は x を読み y だけ書く、x ≠ y) からの条件付き再構成」に書き換え、plan 25 行 (両者の旧 payload 読取は相手の更新前に終了) を追加。evidence-map S-55 は「略記のずれ」「逐語に従う」を撤回し、操作指定 (24〜27・34 行) を出所にし、README §3 / plan 24 行末尾の文言との不一致を記録 | closed |
| must-fix 2 (S-40 の「true 16 = 計装あり」は誤り、R1 は counter を検査していない) | real | recheck script を v2 に改版 (integrity の数値 counter 11 個を全走で検査、`clean` とは別に報告、patch 有無を tag)。結果: counter 全 0 は 21/21、clean true 16 = 計装あり 11 + T-1892 計装なし 5、false 5 = T-2774 計装なし。S-40 をレビューの差し替え案に沿って「archive された flag は単一 verifier 版の再評価ではない、T-1892 の 5 件は X/P evidence 要件 (izanagi `e4c949f08`、2026-09-03) より前の verifier 出力」に書き換え。evidence-map R1 / S-02 / S-40 / S-41 / S-57 を v2 の sha256 と counter 検査の記述に更新 | closed |
| should 1 (arm / block の定義が初出 S-15 より後) | real | 定義を S-15 の冒頭へ移し、S-20 から削除 | closed |
| should 2 (brief / 段 4 の訂正の現物確認) | real | 親が sed で訂正済み (`s1-brief.md` P3、`s4-ruling.md` P3: 「commit 日時 2026-06-28、fetch 日は未記録」)。本表に現物を射影: brief 21 行、s4-ruling 11 行 | closed (親確認) |
