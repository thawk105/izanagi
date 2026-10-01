静的レビューの結果、**must-fix 2 件**です。書込み・テスト実行・委任・禁止された本走結果の閲覧はしていません。

1. **must-fix — K の一部に IR がなく、骨格による分類が定義できない**

   **場所・主張:** [草稿 §9.2–9.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/docs/workload-description-critic-intervention-preregistration.md:289) は、受理候補の分類を「機械的に決まる」とし、K に「T-2867 本走で評価された全 arm の方策」を含める。

   **根拠:** [T-2867 登録 §4.2、137行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/docs/silo-policy-generator-contrast-preregistration.md:137) は C++ arm を「`implementation` … の本文」と定義する。一方、草稿295行の骨格比較は「IR の定数を型付きの placeholder に置き換えた骨格」である。C++ arm の本文には対応する IR が保証されず、逆変換も定義されていない。

   **放置した影響:** 同じ候補が「既知の骨格の新しい定数」か「新しい骨格」かを、登録した規則だけでは決められない。

   **直し方:** 本文一致用の K と、元 IR がある方策だけの骨格比較集合を区別する。placeholder 化する定数の範囲も固定する。C++→IR の一般変換機構を追加する必要はない。

2. **must-fix — 露出を「全 cell で同じ bytes・値」とする開示が誤っている**

   **場所・主張:** [草稿 §3.4、149–150行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/docs/workload-description-critic-intervention-preregistration.md:149) と改版 insight §2 は、露出を全 cell に同じ bytes で運ぶと説明し、草稿は「全 cell で同じ値なので、cell の間の差の偏りにはならない」と結論する。

   **根拠:** [T-2867 登録 §5.4、220行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/docs/silo-policy-generator-contrast-preregistration.md:220) は「各系列の job 1 で 1 session。LLM の baseline に使う」。baseline は系列ごとの実測値で、同一値ではない。また草稿156行自身が critic の材料を「critic あり」に限定している。棚卸しの生出力も、[inventory-log.md 45–48行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/output/insights/2026-10-01/t2852-p5-s3-prereg-revision/verbatim/inventory-log.md:45) にある **1 系列・1 機会**の確認である。

   **放置した影響:** 必須の露出開示が、測定値と情報経路の cell 間同一性を過大に保証する。

   **直し方:** 「段階 D の射影は同じ bytes」「baseline は同じ規則で系列ごとの実測値」「critic の材料は on のみ」と分ける。「偏りにはならない」の断定は削る。また、共通情報との整合・矛盾は表示の効果を弱めるだけでなく強める可能性もある、と限定する。

3. **should — 棄却済みの配置と追加介入を、通常の発効確認へ戻している**

   **場所・主張:** 草稿 §6・§14、改版 insight §5 は、6 cell、性能の別 key、段階 D の射影の除去を選択肢として並べる。草稿 §3.3 の「6 cell … は、費用の比較のため §7 の表にだけ並べる」とも一致しない。

   **根拠:** [D2322 項5、9行](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-p5-s3-prereg/materials/d2322-item5.md:9) は6 cellを「却下した選択肢」に置く。[request.md 11–12行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/output/insights/2026-10-01/t2852-p5-s3-prereg-revision/verbatim/request.md:11) は「本題の改版だけ」。

   **直し方:** 6 cell は棄却理由・費用の参考に縮め、§6 の対比と通常の確認事項から外す。性能の写し・射影除去は、本登録の射程外という説明で足りる。n の最終確認は残す。

4. **should — fallback と固定 δ による分類の意味を補足する**

   **場所・主張:** [草稿 §5–§6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/docs/workload-description-critic-intervention-preregistration.md:196) は共通 fallback を含めて分類する。改版 insight §4 は固定 δ の理由を、等価域を広げると同等になりやすいことだけで説明する。

   **根拠・反例:** 草稿196行は fallback が「全 cell の不採用系列に共通」。比較する双方の全4系列が fallback なら、全対差が0、標準偏差も0となり、式上は区間 `[0,0]` で「実用上同等」になる。[T-2867 登録275行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/docs/silo-policy-generator-contrast-preregistration.md:275) が定義するのは「候補を採用できなければ stock を使う」運用の性能である。

   また、例えば区間 `[0.04,0.06]` は固定 δ＝ln(1.03) なら優越だが、CV_stock＝0.08 に由来する δ＝ln(1.08) なら同等になる。固定幅は、同等を難しくする一方、優越・退行の閾値も小さくする。

   **直し方:** fallback 込みの**運用 score**の分類であり、生成能力の同等を意味しないと明記する。固定 δ の説明も両方向を書く。新しい gate や fallback 除外解析の追加は不要。

5. **should — 最初の提案が拒否された場合と、読める提案がない場合が未定義**

   **場所・主張:** [草稿 §8 項1、265行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/docs/workload-description-critic-intervention-preregistration.md:265) は「IR を読み取れる最初の原提案」に §9.2 の **(i)** の分類を付ける。

   **根拠:** 草稿279行の (i) は「pipeline に投入された機会」に限る。読める IR が auditor に拒否された場合は (ii) である。また [S1版 §8、257行](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-p5-s3-prereg/materials/s1-version.md:257) の「全機会で読み取れる v が無ければ欠測とし、件数を示す」が落ちている。

   **直し方:** 採否に応じて (i)/(ii) を記録するとし、全機会で読めなければ欠測・件数報告とする。

6. **nit — docs 地図の「族 3」は「1族・3対比」**

   **場所・主張:** [docs/README.md 103行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/docs/README.md:103) の「族 3 の同時区間」。

   **根拠:** 草稿210行は「族 M = 3」の3対比を Bonferroni 補正する。3つの別族ではない。

   **直し方:** 「3対比の Bonferroni 同時区間」に替える。

照合して一致：

- D2322 の「4 cell × n＝4 を向き」と、発効前の n＝3〜5 の最終確認
- 未発効・実装未承認・投入未承認の保持
- 規律2・3、欠測と fallback の優先、n を結果で増減しない規則
- 予備観察の開示、2 node 時間以上の確認
- critic off の定義と「解釈＋性能の還流」という推定対象
- C/H/S 共通の表示形式、親への表示なし、T-2867 系列の標本不採用
- Bonferroni 区間・自由度・k(n)・s_d 上限・計画半幅の必要条件としての説明
- n＝4 の片側符号反転検定の最小 p＝1/16
- 独立性を支えない要因の列挙
- D2256・D2272項5との整合

D2283・D2305項3・D2212項4・D2249追加項は、射影資料内の引用との照合に限ります。原決定本文を直接照合したとは扱いません。

## 総括

**NO-GO — must-fix 2件。** K の骨格比較の定義と、露出の同一性に関する開示を修正してください。