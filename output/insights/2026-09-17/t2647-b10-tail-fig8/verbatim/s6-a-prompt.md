単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-fig8/brief.md` — 親の段 1 brief (**親自身も検査対象**)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-fig8/s4-adjudication.md` — 親の段 4 裁定 (**検査対象**。§2.4 の caption 仕様、§5 の受理集合)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-fig8/artifacts/dev-wave-t2647-b10-tail-fig8/s5-author.md` — 実装子の完了報告 (説明と実装の食い違いを疑う)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-fig8/focus-post-s5.log` — 親の焦点走 log (計算ノード dispatch、27 passed 1 skipped。skip は着地前の着地 test)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/tools/plotting/plot_b10_static_tail_formal.py` — 生成器 (519 行)。特に `_caption` 263〜285、`CLAIM_BOUNDARY` / `FIXED_WORDING` 47〜53、`_direct_label` 287〜293、`make_figure` 310〜362
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/docs/paper-story/figures/README.md` — 図の入口。一覧表の fig8 行 (20 行目付近) と末尾の fig8 節 (720 行目以降。何を示す図か・既存図との関係・入力・再現・作図規約への適合・キャプション正文・proof chain) が本 wave の追記。**fig6 節・fig7 節 (447〜715 行) と型を比べる**
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/docs/paper-story/figures/fig8_b10_static_tail_not_observed.provenance.json` — 着地 provenance (336 KB。**全文 cat しない**。`python3 -c` か `jq` で `caption`・`claim_boundary`・`report`・`correctness`・`campaigns`・`external_inputs` を見る)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/docs/paper-story/figures/fig8_b10_static_tail_not_observed.png` — 着地 PNG (目視できるなら見る。できなければそう書く)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/docs/paper-story/2026-09-17.md` — 版。§4「論文の図」(1141〜1262 行) の末尾表「B-10 右 tail 09-15 cohort の図 (未作成)」行が予定仕様。§6「言えないこと」(1629〜1723 行) と §7 (1724〜1971 行) の B-10 関連項も見る
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md` — results 稿。§2 (148〜327 行) の値と §3「限定」(329〜390 行) の 15 項、§4.1 (392〜420 行)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/docs/b10-backoff-static-tail-preregistration.md` — 事前登録。§3 (119〜141 行) と §4.5 (336〜366 行) の固定表現、§4.1 (144〜192 行)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/tools/plotting/FIGURE_CONVENTIONS.md` — 作図規約 (§1・§2・§5・§6・§9・§10)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/tools/plotting/README.md` — 「B-10 static-backoff right tail (09-15 formal cohort) figure」節 (135 行目付近) が本 wave の追記

repo root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8` (commit 4636181a9) とする。上記以外も repo 内を読んでよい (`docs/decisions.md` の D1637 は 50204 行目、D1678 は 51202 行目、D1724 は 52468 行目、D2050 は 62781 行目。D2104 項 7 は local main の 2 commit 先にあり本 worktree には無い — 逐語は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-fig8/d2104-item7.md` に置いた)。

**大きい file を全文 `cat` しないこと。** `grep -n <語> <file>` で位置を出し、`sed -n '<開始>,<終了>p' <file>` で 200 行以内ずつ読む。sandbox は read-only なので pytest や生成器の実走は要求しない。静的検査でよい。

## レンズ A — caption と claim の範囲、規律 2 / 7、事前登録の固定表現

plan を守らせるのではなく攻撃せよ。次を最優先で疑う:

1. **言い方の逸脱**: caption・README fig8 節・生成器の文字列・provenance の `claim_boundary` のどこかに、事前登録 §4.5 の固定表現 (「この事前登録の述語では、表現可能域である 9999 マイクロ秒までに飽和を観測しなかった」) より強い言い方 (「飽和しない」「飽和点が存在しない」「単調に減り続ける」「右へ行くほど急」の機序化、「望ましい」の価値判断、転移) が無いか。caption 中の "while the abort rate keeps decreasing" や "declining" が事前登録の分類語の範囲を越えていないか (§4.4 の `declining` の定義と `L > 0.05` の意味に照らす)。
2. **規律 2**: 図・caption・README が性能の認証や variant 採用の根拠として読める余地。`performance_certified: false` の literal の位置と、"Correctness comes from separate trace-enabled runs …" の記述が results 稿 限定 3・6 と一致するか (検査条件が性能条件と違うことを言い切っているか)。
3. **規律 7 / 既存図との関係**: fig2c・t2266-tail・探索走との関係の記述が版 §4 と results 稿 限定 7・8・11 と一致するか。「続きではない」「畳まない」が README と caption の両方にあるか。2 本目の論文 (D1637) への言及の正確さ。
4. **caption の事実命題**: job id・group id・件数 (18/18、120 記録、0 anomaly)・L の範囲 (0.2738〜0.3704)・比 (0.444 / 0.481 / 0.400)・条件 (48 threads 等) が results 稿 §2 と一致するか。一致しないものは名指しで書く。caption が言う "Bonferroni over 36 one-sided limits, familywise 0.05" は事前登録 §4.4 の記述と一致するか。
5. **README fig8 節の型**: fig6 / fig7 節が持つ節 (何を示す図か・既存図との関係・入力・再現・キャプション正文・proof chain) を欠いていないか。「再現できるのは値であってバイト列ではない」の扱い。proof chain の各項が実在する field / file を指しているか。
6. **版 (2026-09-17.md) との整合**: 版は「この版では作っていない」と書いたまま凍結されている。本 wave は版を触らないと裁定している (README 項目 3 の扱いは別 wave)。それで矛盾が生じないか、生じるなら何を後続に送るべきか (実装はしない。裁定パッケージ候補として書く)。
7. **親 brief・裁定自身の誤り**: 親が実測せずに一般化した値・断定 (「JSON に group id は無い」「statistics に median がある」等) が生成器や README の記述にそのまま入っていないか。

所見は real / refuted の判定材料 (根拠の file:line) を付け、must-fix は「放置したとき成果物 (図・caption・README・provenance) の値・受理集合・参照がどう変わるか」を 1 行で示す。示せないものは nit にする。修正案を書くとき、それが裁定より強い断定になっていないかを自分で確認する。

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け。** 見出しはすべて `##` (H2) で書き、最後の節は必ず `## 総括` とする。予算が尽きそうなら、その時点の結論を出力形式どおりに書いて終われ (無出力が最悪)。

節の順:

## must-fix (番号、file:line、放置時の成果物影響 1 行、根拠、修正案)
## nit
## 親 brief・裁定への所見
## 裁定パッケージ候補 (scope 外だが real なもの)
## 総括
