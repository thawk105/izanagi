単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/s4-ruling.md

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の
停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/s4-ruling.md` — 段 4 裁定 (所見 21 件の裁定と plan v2)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/s6-diff-prereg.patch` — 事前登録への追記 diff (検査対象)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/docs/spool/decisions/2026-09-17-dev-wave-t2288-floor-spec-prereqs-1.md` — decisions fragment (D 3 件、検査対象)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/docs/spool/worklog/2026-09-17-dev-wave-t2288-floor-spec-prereqs-2.md` — worklog fragment (検査対象)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/output/insights/2026-09-17/t2288-floor-spec-prereqs/README.md` — insight README (検査対象)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/verbatim-rulings.md` — 既裁定と事前登録の逐語
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/s3-a-out.md` — 段 3 レンズ A の所見 (裁定で採用された訂正の元)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/docs/phase3-b4-reflux-ablation-preregistration.md` — 追記後の事前登録本文
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/docs/spool/README.md`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/docs/spool/decisions/README.md`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/docs/spool/worklog/README.md`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/CLAUDE.md` — 絶対規律

上記以外に repo 内を読んでよい (`docs/decisions.md`、`docs/worklog.md`、`docs/archive/`)。

## レンズ A — 裁定の逐語整合・授権・追記の形

段 5 で親が書いた 4 成果物 (事前登録の追記 2 箇所、decisions fragment、worklog fragment、insight README) を
敵対的に検査せよ。段 4 裁定 (`s4-ruling.md`) が採用した訂正がすべて成果物に入っているか、逆に裁定に無い主張が
紛れていないかを見る。次を攻撃する。

1. **既裁定の逐語を超えた断定。** 追記と D 本文の中で D1641 / D1695 / D1887 / D1936 / D1537 / D1538 / D1311 / D2044 項 11 /
   D1696 / D1854 / D1855 を引く箇所すべてについて、`verbatim-rulings.md` の原文と突き合わせ、引用が原文より強い・
   広い・違う向きになっている箇所を file:line で示せ。
2. **`reps=5` の記録形。** 「AI の選択」「calibrator 出力から導いたものではない」が D・worklog・insight・裁定パッケージの
   全部で保たれているか。どこかで「較正済み」「calibrator が決めた」に化けていないか。
3. **3 cell の記録形。** 「既裁定の転記ではなく新しい具体化」「十分性は主張しない」が保たれているか。
4. **C 群の事前性の記録。** 較正値の既知性の開示、床値結果の不在、「候補を落とした条件は既裁定だけ」が正確か。
   条件 5 の挙動基準化が規律 7 と整合するか。「結果を見る前に」の読み (床値結果) を D 本文が正直に書いているか。
5. **事前登録の追記は追記だけか。** diff に削除行・既存行の変更が無いこと (規律 7)。追記が §5.1 の解除条件・§6 の前提条件・
   発効・測定開始のいずれも緩めない文面になっているか。「採用証拠の受理」を受理済みと誤読させないか。
6. **fragment の文法。** decisions は `## {{D:slug}}. <題>` 形、題末尾に日付なし、D 番号を書かない、既存 D は実番号。
   worklog は `## 本文` / `## 次の一手差分` の 2 H2、action は `完了` → `更新` の順、`remaining: none`、`base:` 64 桁、
   title の `[T-2288]` が同 fragment の `更新` 対象であること。placeholder が 3 D の slug と一致すること。
7. **insight README。** `authority: none` / `default_effect: no-state-change` の宣言と本文が矛盾しないか (README が
   何かを「発効」「凍結」「記入」したと読める文が無いか)。「受入・検査」節が実測前の欄になっていないか。
8. **裁定パッケージ。** 5 項目が、本 wave の成果物を無効にせず、A-5 の値を起草していないか。

## 制約

- 書込可能 tmp が無いので pytest 緑を要求しない。静的検査でよい。テスト実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- 所見は real / refuted / nit に分け、根拠 (file:line または逐語) を必ず添える。攻撃が成立しなかった項目は正直にそう書け。
- 出力は NFC。U+0300〜U+036F を使わない。

## 出力形式

以下の H2 見出しをこの順で書く。**全部 `#` 2 個の H2** で、`###` は使わない。最後の節は必ず `## 総括` とする (`### 総括` と書いてはならない)。

## 逐語を超えた断定
## reps と 3 cell の記録形
## C 群の事前性
## 事前登録の追記
## fragment の文法
## insight README と裁定パッケージ
## 総括
