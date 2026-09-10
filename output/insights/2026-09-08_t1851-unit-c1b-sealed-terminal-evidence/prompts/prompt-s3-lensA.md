これは AGENTS.md の単独段例外である。あなたは dev-wave の段 3 (敵対相談) だけを行う。
段 3 以外の段へ進んではならない。

## あなたの立場

- sandbox は read-only である。**書込可能な tmp は無い。** pytest を走らせて緑を示す必要はなく、
  静的な読解と file:line の引用で足りる。テストの実測は親が行う。
- **file を 1 つも書けない。** 成果物は最終メッセージの本文にすべて書くこと。
  「別 file に書いた」と述べてはならない。
- commit・push・branch 操作・file の作成や編集は禁止である。
- 予算が尽きそうなら、途中までの結論を下の出力形式どおりに書いて終えること。無出力が最悪である。
- **plan を守る立場ではない。攻撃する立場である。** plan だけでなく、親が書いた契約 v3、
  親の brief、親自身の実測値とその一般化も検査対象である。

## repository

repo root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a` である。
以下の path はすべてこの root からの相対 path として読むこと。

## 必読 (この順に全文を読む)

1. `output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.md`
2. `output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/parent-probes.md`
3. `output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/s1-brief.md`
4. 段 2 の plan (絶対 path):
   `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b-v3/artifacts/s2-plan.md`

読めない file があれば、そこで即座に停止し、読めなかった path を報告して終えること。

## あなたのレンズ — 正しさ境界

**「この設計は、正しさの防壁をどこかで緩めていないか」だけを疑え。**

具体的に次を探せ。

1. **`observed` へ落とす逃がし道。** 契約 v3 は「相互整合が 1 つでも破れたら拒否する」と書いた。
   plan の実装で、破れているのに `observed` になる経路、または拒否が発火しない経路はあるか。
2. **新 field `measurement_retry_reason` の導入で、既存の受理集合が広がっていないか。**
   契約は「v1 の受理集合は 1 bit も変わらない」と主張する。plan の変更が v1 の経路へ
   漏れる箇所を file:line で挙げよ。`_assert_null_matrix` の `reason_field` 既定値、
   `record_attempt_terminal` の条件付き emit、`DomainProfile` の新 field 既定値の 3 点は必ず見よ。
3. **親の probe の一般化が過剰でないか。** `parent-probes.md` の P-1 は一時変異を当てた実コードで
   測っている。その変異と plan の実装が同じ意味になっていない箇所はあるか。
   親が「通った」と書いた 5 形が、plan の実装では通らない、または plan の実装では
   別の理由で通ってしまう箇所を挙げよ。
4. **拒否の署名と正例。** 契約 v3 の 5.3 が足す 2 条項について、plan の拒否が
   「通る正例を持つ」ことを確かめよ。恒真な拒否 (どんな入力でも落ちる) や、
   逆に到達不能な拒否 (どんな入力でも発火しない) があれば名指しせよ。
5. **封印の発行経路。** 契約 v3 の 6.2 は「interface を真似ただけの偽 registry は
   validated capability を作れない」形を要求する。plan の実装がそれを満たすかを
   `_launch_floor_attempt_for_test()` の注入経路から実際に辿って判定せよ。
   満たさないなら、偽装が通る具体的な手順を書け。
6. **crash 後の権威 (契約 v3 の 7 節)。** row と file の不一致を検出できない組合せはあるか。

## 禁止

- 契約 v3 の条項を作り直した代案を書くこと。誤りは所見として挙げるにとどめよ。
- 「一般に危険である」型の指摘。**必ず file:line と、破れる具体的な入力または手順を添えよ。**
- 実測していない否定を断定すること。読解に基づく推定なら「読解」と明記せよ。

## 出力形式

次の見出しを H2 (`##`) でこの順に置くこと。所見には `A-01` から通し番号を付け、
各所見に「real か refuted か」「blocker か否か」「file:line」「破れる具体例」を必ず書くこと。

- `## 所見`
- `## plan の判定` (この plan で契約 v3 を実体化できるか。yes / no と理由)
- `## 親の実測への反証`
- `## 総括`
