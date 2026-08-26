# B-2 の判定規則に残っていた穴 — generation/search arm の出力単位が未凍結である

```
authority: none
default_effect: no-state-change
measured_at_commit: e29084e02d626d812281be6f97f45bb2dde3a843
supersedes: none
```

**この文書は可変状態の正本ではない。** 規範を新設せず、既存の凍結文書
(`docs/phase3-8b-descriptor-design.md` / `docs/phase3-8c-preregistration.md`) を
1 byte も変更しない。ここに書く「提案」はユーザー裁定を待つ候補であって、事前登録ではない。

## 0. この文書の位置づけ — 何を足し、何を足さないか

同日の先行 wave (worklog エントリ 981、commit `9463bcbc` 限定) が
`output/insights/2026-08-26_8b-b2-precheck-package.md` として、**B-2 が現 main で投入不能である
こと**を層 (a)〜(f) に分けて確定している。**本書はそれを繰り返さない。**

先行 package が扱ったのは、いずれも**実走の入口**の閉塞である — 発効判定に充足を返す終端が
無いこと、正式 profile の hard stop、artifact の不在、共有 freeze が active でないこと。

本書が足すのは、そこに含まれていなかった **判定規則そのものの穴** である。
すなわち「仮に入口が全部開いたとして、generation/search arm が出した成果を、
凍結済みの判定表のどこへ入れるのか」が決まっていない、という問題である。

|項目|先行 package (981)|本書|
|---|---|---|
|実走入口の閉塞 (a)〜(f)|**扱った**|扱わない (再測だけ行い、変化の有無を §2 に記す)|
|generation arm の出力単位の未凍結|扱っていない|**§1 (本書の中心)**|
|§5 判定パラメータの検証 consumer の実効性|扱っていない|**§3**|
|裁定パッケージ (4 件)|完了証明層の裁定 1 件|**§4 (別の 4 件)**|
|台帳の重複 (F369 / F631)|F631 を新設|**§6 で指摘**|

## 1. B-2 の判定規則には、generation/search 固有の読み替えが凍結されていない

### 1.1 何が無いか

8b 設計 §6 と、それを上書きする §10.1 の判定表は、3 条件の連言で結論を出す。
`orchestrator/campaign/s8c_result_judge.py` の条件 ID はそれに対応する
(`on_off_prediction_difference` / `swapped_follow_through` / `paired_repeat_contrast`)。

この 3 条件はいずれも **「その arm の予測構成」** を入力に取る。これは段階 1 の
**selector 実験**の語彙である — selector は固定 6 構成からちょうど 1 件を選ぶので、
arm の出力は構成 ID そのものになる。

ところが B-2 が要求するのは段階 2 の **generation/search 実験**であり、arm の出力は
選択ではなく **合成された variant** である。しかも 8c 事前登録 §4 は全 cell を厳密に `G=2` と
凍結しているので、1 つの arm が 2 世代ぶんの proposal を出す。
**「どの proposal を、その arm の構成として判定表へ入れるのか」が一意でない。**

8b 設計 §6 は「以下は selector 実験の最小判定表であり、generation/search 実験にも
**選択段の判定として**適用する」と書く。generation/search には「選択段」が無い arm 構成も
ありうるため、この 1 文は読み替えを与えていない。

### 1.2 現物で確かめたこと

- **judge 側は予測を構成 ID へ正規化して比較する。** `s8c_result_judge.py:538-725` が
  prediction を正規化し、on/off 差と swapped の exact 一致を評価する。
  単位と向きも定数で固定されている (`_PARAM_UNIT = "throughput_tps"`、
  `_PARAM_DIRECTION = "on_minus_off"`、同 `:38-39`)。
- **supervisor 側は予測写像を作らない。** `p3_autonomous_workload_trial.py:4063-4129` は
  世代ごとの proposal と `harness.variant` を記録するだけである。
  同 module が `s8b_prediction_runner` から import しているのは
  `_canonical_json_bytes` / `_sha256` / `_now_iso` / `ProviderResponse` などの補助だけで
  (同 `:90-98`)、予測生成の経路ではない。
- **`s8c_result_judge.judge()` には production の呼び手が無い。** 参照は test と
  静的 evaluator (`s8c_preregistration_evidence.py` の C07 到達性検査) だけである。
- **`docs/decisions.md` に、この読み替えを裁定した D は存在しない。**
  主題 (generation 出力・予測構成・judge の 3 条件 ID) で検索して 0 件だった。

### 1.3 なぜこれが重要か

**どの proposal を arm の出力とするかで、3 条件・`selection_evaluation` 表・最終結論が
すべて変わる。** したがってこれは 8b 設計 §8 が列挙する「判定基準」そのものであり、
変更には**再凍結 + ユーザー承認**が要る。AI の wave が別文書で先に固定してよい事項ではない。

**本 wave はこれを実装していない。** §4 の裁定 1 として返す。

## 2. 実走入口の再測 (先行 package からの変化)

先行 package は commit `9463bcbc` 限定の snapshot であり、§10 に再訪条件を挙げている。
本 wave は commit `e29084e0` で `python3 -m orchestrator.campaign.s8c_gate_report` を走らせた
(先行 package §6 が「診断の正しい入口」と名指しした経路)。

```
authorization: authority=USER, decision_in_report=NOT_REPRESENTED, report_effect=DOES_NOT_AUTHORIZE
predicates: 12 件
  C03 UNSATISFIED         manifest-registry-proof-undefined
  C05 EVIDENCE_UNDEFINED  schedule-schema-absent
  C08 EVIDENCE_UNDEFINED  prereg-binding-proof-undefined
  他 9 件 EVIDENCE_UNDEFINED  completion-proof-not-machine-checkable
section5: 9 行中 8 行 UNFILLED (placeholder)、FILLED は「検定 4 点」1 行だけ
```

**先行 package の再訪条件は 1 つも成立していない。** `SATISFIABLE_CONDITION_IDS` は空のまま、
`trial-manifest.v1.json` / `prereg-effective-binding.v1.json` / `schedule.v1.json` は
`git ls-files` と `find` の両方で 0 件、批准の閂も閉じたままである
(closure 25 file の digest `dabeada30868a5f790b25b86a9f0a34fafb24946f0e73de48fb90d97d9332eb9` が
read-only 台帳に不在。`require_ratified_closure()` を現物で呼んで確認)。

**§5 の未記入は 8 行である** (先行 package は `9463bcbc` 時点を「8 欄中 7 欄」と記す。
本測定は 9 行中 8 行。行数が 1 増えている)。

## 3. §5 の判定パラメータ検証 consumer は、解除条件を満たしていない

8b 設計 §10.2 と 8c §5 の記入規約は、`n` / `delta_min` / `sd_max` を記入してよいのは
「型・有限性・符号・単位・向きを機械検証する consumer が実在するとき」に限ると定める。

**検査関数そのものは実在する。**

- `s8c_preregistration.py:874-945` — `n` は 2 以上の整数、`delta_min` は有限の正、
  `sd_max` は有限の非負、`unit` と `direction` を同時要求。
- `s8c_result_judge.py:217-239` — 同等の検査。

**しかし consumer としては機能していない。**

1. parser が作る違反は `MarkdownContract.section5_value_violations` に保存されるだけで、
   **発効判定 (`s8c_preregistration.py:1925-1956`) はその値を参照しない。**
   したがって §5 を誤って記入した場合でも、違反を無視したまま `all_filled` が成立しうる。
   現在この危険が顕在化していないのは、欄が空だからにすぎない。
2. `judge()` は private な `_ContrastParams` を直接要求し (`:1012-1019`)、
   §5 の記入値から構築する束縛が無い。production の呼び手も無い。

**成果物影響:** このまま §5 を記入すると、検証されない閾値が将来 `official_status` の
成立条件を左右しうる。8b §10.2 が「この制約の現在の担保は『欄が空であること』だけである」と
自ら書いているのは、まさにこの状態を指している。

## 4. 裁定パッケージ (ユーザー裁定を要する 4 件)

### 裁定 1. generation/search arm の「出力単位」をどう定義するか (§1 の穴)

|案|内容|評価|
|---|---|---|
|**A (推奨)**|`G=2` の proposal sequence 全体を arm の outcome とし、3 条件を set / sequence 用に再凍結する。selector 語彙を流用しない|合成の因果を直接測る。8b §8 の再凍結と 8c 改訂が要る。実装量は最大|
|B|最終世代の canonical variant を arm 出力に固定する|実装は小さい。ただし世代 1 を捨てる意味と、独立生成どうしの swapped exact 一致が何を意味するかに追加裁定が要る|
|C|合成の後に決定論的 selector を置き、現 judge をそのまま使う|流用しやすいが、**合成効果と選択効果が交絡する**|

**推奨は A。** 理由は 3 つ。(i) B-2 の主張は「合成が workload に特化する」であり、
測るべきは合成の産物そのものである。(ii) C は交絡により、8b §1 が
「selector 実験は descriptor 条件付き合成の証拠に数えない」と宣言した境界を実質的に壊す。
(iii) B は `G=2` を凍結した意味 (世代を跨いだ改善を見る) を捨てるため、世代予算の凍結と整合しない。

**B / C を実装子の既定値として採ってはならない。**

### 裁定 2. `n` / `delta_min` / `sd_max` を決める対計画用 pilot をいつ設計するか

8b §10.2 は、値の記入条件として (i) schedule generator・manifest・反復束縛の固定、
(ii) 対計画用 pilot が完全 block として成立、(iii) judge の実装、(iv) 結果を見る前に決めること、
(v) §8 の再凍結 + ユーザー承認、をすべて要求する。

**本 wave はこの pilot の事前登録を書こうとして取り下げた。** 理由は 2 つある。

1. pilot の因子・セルは裁定 1 が決まるまで書けない。裁定前に書けば
   「因子・セルを凍結した」という誤読を生む。
2. 裁定 1 を別文書で先取りして固定する形は、8b §8 の再凍結手続きの迂回になる
   (段 3 の敵対検証 2 本が、異なるレンズから独立に同じ指摘をした)。

**したがって順序は「裁定 1 → 8b 再凍結 + 8c 改訂の land → pilot 事前登録」とする。**

既存の `output/insights/2026-08-16_t1142-n-pilot-prereg/` はこの pilot の代替にならない。
同 pilot の estimand は **oracle の argmax 用 `n`** (6 構成の median-of-medians 完全一致 argmax)
であって §10.1 の対比パラメータではない。さらに同文書自身が
「certified 成果物・floor・oracle・`n` の決定のいずれの入力でもない」と宣言しており、
実測も R=11 で、事前登録が要求した R>=32 (分散の相対標準誤差 <=25%) に未達である。
**新 pilot を作るときは、これを既知結果台帳 (HARKing 境界) へ載せ、前向き導出から除外する。**

### 裁定 3. 導出関数の恒真化をどう防ぐか

「値を結果閲覧前に commit する」だけでは足りない。段 3 の敵対検証が具体的な悪用手順を示した —
candidate `n` ごとの prefix から平均 / SD 比が最大の `n` を選び、`delta_min = pilot 平均 / 2`、
`sd_max = pilot 標本 SD + ε` とする関数を事前 commit すれば、形式は満たしたまま
**好都合な prefix と、その pilot が必ず通る境界を結果から選べる。**

**推奨:** `delta_min` は pilot と独立な「実質的に意味のある差」から固定し、
pilot は固定済みの α / β・効果量・分散上側限界から `n` と `sd_max` を導く用途に限定する。
導出関数は欠測・prefix・丸め・上限到達・候補不成立時の `null` を含む完全な純関数として凍結し、
データ依存の候補選択を禁止する。

### 裁定 4. 「pilot を B-2 の証拠に数えない」をどう機械強制するか

現在この非算入は、**全系列共通の `certifying=False` によって恒真的に成立しているだけ**である。
`trial_registry.py:4027` が `certifying is not False` を無条件に拒否し
(「this wiring wave cannot issue certifying launches」)、受入 receipt も `certifying: False` を
焼く (同 `:6120`)。**pilot 固有の拒否経路は無い。**
承認権限の閂が将来開いたとき、pilot 行を正式 6 cell・三表・B-2 レポートから拒否する機構が無い。

**推奨:** pilot 専用の namespace と不変な `experiment_role` を設け、
正式 manifest・result judge・受入がその role を必ず拒否するよう結線し、
pilot artifact を正式入力へ差し込む positive control を置く。
それまでは事前登録本文へ「非算入は未機械強制である」と正直に書く。

## 5. 依存順に並べた後続作業 (先行 package §9 への追加)

先行 package §9 は最上流を「完了証明層の設計をユーザー裁定にかける」と置いた。**それは変わらない。**
本書はそれと**並行して進められる別線**を 1 本足す。

1. **裁定 1 (generation outcome 単位) のユーザー裁定** — 完了証明層とは独立に決められる。
   これが無いと 2 以降が 1 つも動かない。
2. **8b §8 の再凍結 + 8c 条件契約世代の改訂** — 裁定 1 を正本へ載せる。旧 freeze と変更理由を残す。
3. **§5 判定パラメータの発効結線** — `section5_value_violations` を発効判定の連言へ入れ、
   発効版 §5 から `_ContrastParams` を構築する束縛と、supervisor → judge → 三表の
   production 呼び手を実装する。受理集合を変えるため decider の版上げと 8c 世代 record が要る。
4. **対計画用 pilot の事前登録** — 2 と 3 が land した後。裁定 2 / 3 / 4 の推奨を反映する。
5. **pilot の実走** — 批准の閂が開いた後。
6. **B-2 正式系列 6 cell の実走** — 先行 package §9 の最上流と 1〜5 がすべて閉じた後。

## 6. 台帳の重複 — 同じ欠陥に F369 と F631 の 2 件がある

判定器を CLI 形式で起動すると 12 条件すべてが `evaluator-exception` へ潰れる欠陥は、
**`docs/failures.md` に 2 度登録されている。**

- **F369** 「判定器を `-m` で走らせると全条件が同じ理由へ潰れ、その出力を brief の一次資料にした」
  — 恒久対応は「診断 vector は library 経路で取る」、CLI 側の修理は [T-1288]。
- **F631** 「同じ判定を CLI 経由と library 経由で呼ぶと答えが変わる道具を、現在地の一次資料に
  使った」 — 先行 wave (981) が新設。

機序 (二重 import による `isinstance` 判定の失敗と包括 except)、道具、帰結 (現在地の誤読) が
同一である。`docs/skill-self-improvement.md` の routing 規則は「同型再発なら新しい F を作らず、
既存 F に『再発: 日付』を追記する」と定めており、**F631 の新設はこの規則に反している。**

**本 wave では台帳を直さない** (F の統合は台帳の既存 bytes を動かす操作であり、
fold の不変条件と衝突しうる)。§5 の後続作業とは別に、裁定として返す。

**本 wave も同じ罠を一度踏んだ。** 親は最初に CLI 形式で測り、全件 ERROR を得て、
library 経路で測り直した。先行 package §6 が名指しした正しい入口
(`python3 -m orchestrator.campaign.s8c_gate_report`) を後から知り、
§2 の数値はその入口で取り直して library 経路の結果と一致することを確認した。

## 7. 本 wave が確かめていないこと (正直な現在地)

- 本 wave は文書しか変更していない。実走・計測を 1 件も行っていない。
- 裁定 1 の 3 案について、A を実装した場合の工数・必要な機構は見積もっていない。
  推奨は判定の意味論だけを根拠にしている。
- §3 の「production 呼び手が無い」は参照関係の検索で確かめたもので、
  動的 dispatch 経由の呼び出しがないことまでは証明していない。
- 8c 事前登録 §6 の現在地記述が現物より遅れている件は、先行 package §8 が既に扱っている。
  本 wave では触れていない (同書の本文は条件契約の保護 hash 対象であるため)。

## 8. 逐語

- `plan.md` — 段 2 のプラン起草 (read-only codex)
- `consult-a.md` — 段 3 敵対検証 レンズ A「既存被覆と二重登録」
- `consult-b.md` — 段 3 敵対検証 レンズ B「正しさ防壁・凍結手続きの迂回・恒真な保証」
- `measured-activation-report.txt` — 発効判定の実測出力 (library 経路)
- `gate-report-summary.txt` — `s8c_gate_report` の status vector (§2 の数値の出所)
- `brief.md` — 段 1 brief。**§5 の未記入を「7 欄」と書いた誤りと、
  「判定パラメータの機械検証 consumer は既に実在する」という過大評価を含む。**
  段 2 と段 3 がどちらも独立に訂正した。訂正の経緯を残すため原文のまま置く。
