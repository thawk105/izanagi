単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight

必読事項の射影: 次を読む。読めなければ即停止し、読めなかった絶対パスを報告して終わる。

- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/brief.md` — 親の段 1 brief。**これ自身が検査対象である**
- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/verbatim.md` — 既裁定と契約文の逐語射影
- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/t2028-axis3-live-preflight/plan.md` — 段 2 のプラン。**これも検査対象である**
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-08-27-axis3-search-preregistration.md` — 旧登録 (凍結、95 KB)。§7 完走述語・§8 停止条件と予算・§13 未決項目を必ず読む
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-09-01-axis3-search-amendment.md` — 契約の正本 (凍結)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-09-01-axis3-registration-preflight.md` — 直近の実行記録 (凍結)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py` — 軸 3 実行器
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/README.md` — 7.7 の一般規則が正本。「7.7 主張軸別の調査状態と、不在主張の成立条件」を検索して読む

## 依頼

**レンズ A: 正しさ境界と契約適合。** 親の brief と段 2 プランを守らず、壊しに行け。
プランの改良案を書くのが仕事ではない。**通ってはいけないものが通る経路**を見つけるのが仕事である。

## 特に攻撃してほしい点

1. **(P1) 親の provisional 裁定を攻撃せよ。** 親は「live preflight は U11 裁定の対象外だから、
   本 wave は preflight を実走してよい」と読んだ。amendment §6 の U11 条項は「軸 3 の live 本走は
   開始できない」と書いてある。**「本走」に live preflight が含まれるかどうかを、契約本文の語法から
   決めよ。** 含まれるなら本 wave は 1 本も request を出せない。親の読みが自己都合でないかを疑え。
   同様に、09-01 記録 §6.1 の 4 つの hard stop (U11・control 評価器・resolver・independent pass
   executor) のうち、live preflight にも掛かるものが無いかを 1 件ずつ判定せよ。
2. **受理集合が動いていないかを行単位で確かめよ。** pacing は scheduling だけに触れると親は
   主張している。`ready` / `unavailable` / `blocked` の判定、完走述語 (§7.1 の条件 0〜6)、
   `declared_total`、evidence digest、checkpoint の合法な state/action 組のいずれかが
   プランの変更で動くなら、それは受理集合の変更である。
3. **§8.4 の潜脱を探せ。** 「429 を起こさない pacing」と「起きた 429 を retry で無かったことにする」の
   境界。プランが後者へ滑っていないか。cooldown・再送・待ち直し・`Retry-After` 待機のいずれかが、
   実質的に「その query を `未完走` にする」規則の回避になっていないか。
4. **N3 の記録が受理集合へ漏れていないか。** 観測値 (実測間隔・rate-limit header) を preflight
   report や page evidence へ書くと、seal・digest・schema・完走判定のどこかに入り込む恐れがある。
   **「記録するだけ」が本当に記録だけかを確かめよ。**
5. **凍結物の不可侵。** プランが `2026-08-27-*` / `2026-09-01-*` の 4 文書の bytes を変えうる経路
   (再生成・正規化・自動整形・hash 更新を含む) を持たないか。
6. **親自身の実測値とその一般化を攻撃せよ。** 親は「pacing 不在で流すと数百行が恒久的に `未完走` に
   なる」と主張した。この因果は本当に成立するか。`_probe_response` と `run_preflight` の実際の
   制御流れを読んで、親の主張が誇張または過小でないかを判定せよ。**親が誤っているなら、
   その方向を明示せよ** (「もっと悪い」でも「そこまで悪くない」でも構わない)。

## 出力規律

- 所見ごとに **real / refuted の判定を自分で下し、根拠の file:line を必ず添えよ。**
- 「〜かもしれない」だけの所見は書くな。成立条件を示せ。
- 成果物 (certified 選択・レポート・台帳・実行記録) の値・受理集合・参照がどう変わるかを
  1 行で書けない所見は、nit として分離せよ。
- scope 外だが real な所見は、実装案ではなく**裁定パッケージ候補**として返せ。

## 禁止

- 実装・編集・commit。read-only である。
- プランの穴を自分で埋めた改訂版を書くこと (それは段 4 の親の仕事)。
- 最小間隔を緩める提案。

## 実行環境の注意

書込可能な tmp が無いため pytest 緑を要求しない。静的検査でよい。テストの実測は親が行う。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 出力形式

以下の H2 見出しをこの順で使う。結合文字 U+0300〜U+036F を使うな。

## 契約語法の判定 (P1 への回答)
## real 所見
## refuted 所見
## nit
## 裁定パッケージ候補
## 総括
