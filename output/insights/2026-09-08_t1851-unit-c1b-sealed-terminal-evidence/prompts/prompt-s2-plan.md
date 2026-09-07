これは AGENTS.md の単独段例外である。あなたは dev-wave の段 2 (プラン起草) だけを行う。
段 2 以外の段へ進んではならない。

## あなたの立場

- sandbox は read-only である。**書込可能な tmp は無い。** pytest を走らせて緑を示す必要はなく、
  静的な読解と file:line の引用で足りる。テストの実測は親が行う。
- **file を 1 つも書けない。** 成果物は最終メッセージの本文にすべて書くこと。
  「別 file に書いた」と述べてはならない。
- commit・push・branch 操作・file の作成や編集は禁止である。
- 予算が尽きそうなら、途中までの結論を下の出力形式どおりに書いて終えること。無出力が最悪である。

## repository

repo root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a` である。
以下の path はすべてこの root からの相対 path として読むこと。

## 必読 (この順に全文を読む)

1. `output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.md`
   — **確定済みの契約 v3。これが仕様の正本である。再設計してはならない。**
2. `output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/parent-probes.md`
   — 親が各条項を束縛先へ通した probe の実測結果。
3. `output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/s1-brief.md`
   — 段 1 brief (scope・不変条件・変更面のアンカー・割れうる前提)。
4. `output/insights/2026-09-07_t1851-unit-c1b-contract-v2-defects/rulings-resolved.md`
   — 契約 v3 の 5 節 / 3 節 / 6.4 / 単位分割が、どういう理由で決着したかの正本。

読めない file があれば、そこで即座に停止し、読めなかった path を報告して終えること。
context 無しの推測で起草してはならない。

## 依頼

契約 v3 を実体化する実装プランを **file:line 粒度** で起草せよ。

実装は leaf / launcher / profile / core / adapter の縦 1 単位である。実装子は
**所有 file が素集合になる 3 本**に分ける。

- 単位 1: 新設 leaf `orchestrator/campaign/s8b_terminal_evidence.py` + その新設 test
- 単位 2: `orchestrator/campaign/s8b_floor_attempt_launcher.py` +
  `orchestrator/campaign/s8b_attempt_profile.py` + それぞれの既存 test
- 単位 3: `orchestrator/campaign/attempt_registry_core.py` +
  `orchestrator/campaign/s8b_attempt_registry.py` + それぞれの既存 test

単位 1 を先に閉じ、完了後に単位 2 と単位 3 を並列に置く。

見積りは production 約 +1,000〜1,600 行、test 約 +1,500〜2,400 行である。

## 起草の要件

1. **各単位について、触る file と関数を file:line で挙げ、何をどう変えるかを書く。**
   新設 file は公開する型と関数の署名を書く。
2. **契約 v3 の条項番号と実装箇所の対応表を作る。** 条項に対応する実装が無い、または
   実装が対応する条項を持たないものがあれば、それを名指しで挙げる。
3. **test の設計を書く。** 契約 v3 の 5.2 (通る 5 形) と 5.3 (閉じる 2 穴) には、
   受理と拒否の両方の test を置く。拒否 test は署名で書き、通る正例を必ず添える。
4. **既存 test への影響を数える。** v1 の受理集合が 1 bit も変わらないことを、
   どの既存 test がどう保証するかを file:line で示す。変更が要る既存 test があれば、
   その理由と、期待値を変えるのか新規に足すのかを書く。
5. **段 1 の割れうる前提 (P1)〜(P5) を検査せよ。** 特に (P4) の pin 閉包は、
   新設 file 名・新 field 名・新 path 名で自分でも引き直し、親が見落とした pin があれば挙げる。
6. **規模を判定せよ。** 起草した plan が 1 wave に収まるかを判定し、収まらないなら
   その根拠を行数と依存で示せ。**中途半端な分割は前回すでに却下されている。**
   収まらない場合の選択肢は「契約 v3 の文書だけで切る」だけである。

## 禁止

- 契約 v3 の条項を再設計・変更すること。誤りを見つけた場合は「所見」として挙げるにとどめ、
  plan 本体は契約 v3 のとおりに書くこと。
- runner の構造化 `execution_failure` と campaign の算出変更を plan に入れること
  (これは C2 の所有であり、本単位へ混ぜてはならない)。
- v1 の event key 集合・受理集合を変える設計。
- `observed` へ落とす逃がし道を作る設計。
- `attempt_registry_core.py` へ `aborted=False` の keyword 呼び出し、または
  `OriginSealed(False, ...)` を書く設計。
- 契約 v3 が 8 節で「採らない」と書いた 3 件 (claim v4 の新設、`_AttemptState` への `mode` 追加、
  core 公開 API 8 surface への capability 伝播) を plan に入れること。

## 出力形式

次の見出しを H2 (`##`) でこの順に置くこと。

- `## 単位 1 の plan`
- `## 単位 2 の plan`
- `## 単位 3 の plan`
- `## 契約 v3 条項と実装の対応表`
- `## test 設計`
- `## 既存 test への影響`
- `## 前提 (P1)〜(P5) の検査`
- `## 規模の判定`
- `## 所見` (契約 v3 自体の誤りや、親が見落とした事実があればここへ)
- `## 総括`
