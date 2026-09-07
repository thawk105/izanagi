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

## あなたのレンズ — 整合・実効性・所有範囲

**「この plan は、書いたとおりに実装したとき本当に動くのか。そして書いた分量で終わるのか」を疑え。**

具体的に次を探せ。

1. **file:line の実在。** plan が引用した file:line が現物と食い違う箇所を全部挙げよ。
   行番号のずれ、関数名の綴り違い、存在しない引数、存在しない属性を名指しせよ。
   特に `_AttemptState` の 3 digest の綴り (`observation_event_sha256` であって
   `observation_start_event_sha256` ではない) は必ず確かめよ。
2. **呼出し規約の取り残し。** plan が署名を変える関数について、**全呼出し箇所を数えよ。**
   plan が挙げていない呼び手があれば file:line で挙げよ。test 側の呼び手も数に入れよ。
3. **所有 file の素集合性。** plan の 3 単位が本当に素集合か。同じ file を 2 単位が触る、
   または単位 1 が閉じないと単位 2/3 が書けない依存が plan に書かれていない箇所を挙げよ。
4. **凍結 gate と pin 閉包。** 新設 file 名・新 field 名・新 path 名で自分でも pin 閉包を引き直せ。
   親は「該当 0 件」と書いた (`parent-probes.md` の P-7)。**その否定を自分で検査せよ。**
   file 全体 hash の golden、role 名や xdist group 名など path 以外を key にする pin、
   件数 assert つきの登録簿 (例: `test_reflux_formal_consumer.py` の `WAVE_PRODUCTION_FILES`) も
   対象に含めよ。
5. **規模の判定。** plan の見積り (production +1,000〜1,600 行、test +1,500〜2,400 行) が
   実際の変更面と合っているか。過小・過大なら、どの単位が何行ずれるかを根拠つきで書け。
   **1 wave に収まるか収まらないかを、あなた自身の判定として書け。**
   収まらない場合、前回すでに「効果のある分割は存在しない」と実測されているので、
   中途半端な分割案を出してはならない。選択肢は「契約 v3 の文書だけで切る」だけである。
6. **C2 との境界。** plan が runner の構造化 `execution_failure` や campaign の算出変更へ
   踏み込んでいないか。踏み込んでいれば file:line で挙げよ。
7. **変異候補の再照準。** 前 wave は変異候補 M1〜M18 の可否を記録したが、設計が
   「観測後の理由を別 field に載せる」形へ変わったので照準し直しが要る。
   plan の実装面に対して、**殺せる変異と殺せない変異**を具体的に挙げよ。
   殺せない変異 (どの test も落ちない改変) があれば、それが最も価値のある指摘である。

## 禁止

- 契約 v3 の条項を作り直した代案を書くこと。誤りは所見として挙げるにとどめよ。
- 「一般に危険である」型の指摘。**必ず file:line と、破れる具体的な入力または手順を添えよ。**
- 実測していない否定を断定すること。読解に基づく推定なら「読解」と明記せよ。

## 出力形式

次の見出しを H2 (`##`) でこの順に置くこと。所見には `B-01` から通し番号を付け、
各所見に「real か refuted か」「blocker か否か」「file:line」「破れる具体例」を必ず書くこと。

- `## 所見`
- `## plan の判定` (この plan で契約 v3 を実体化できるか。yes / no と理由)
- `## 規模の判定` (1 wave に収まるか。収まらないなら根拠)
- `## 変異の照準`
- `## 親の実測への反証`
- `## 総括`
