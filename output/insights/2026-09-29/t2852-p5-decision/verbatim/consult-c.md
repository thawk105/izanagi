## 主張

**(c) 今は投入せず、S3 の生成器対照後に別の事前登録で介入を設計する**ことを推す。P5 は結果の「なぜ」を説明する実験だが、現行 S1 の受理コードは `double now_backoff = <数値>;` の１行に限られる。受理候補で機構の違いを分類する余地は構造上ない。[草稿 §9.4](</work/1/SFC/tanab/izanagi/docs/workload-description-critic-intervention-preregistration.md>)。関数本体を書ける空間を優先する方針は、[差分分析 §0・§4](</work/1/SFC/tanab/izanagi/output/insights/2026-09-21/vldb-direction/gap-analysis.md>)と[D2259](</work/1/SFC/tanab/izanagi/docs/decisions.md>)にも沿う。

規模を増やしても、この分類の限界は解けない。6 cell・各 n＝3／4／5 の中央値見積りは **72.3／96.4／120.5 node 時間**、LLM 直列 **48／64／80 時間**、原提案機会 **198〜420**。`s_plan` を当てた半幅 **0.049〜0.172** は、同等分類の計画上の目安 **0.0148** に届かない。ただし `s_plan` は新しい cell の分散ではなく、半幅は精度の予測ではない。[草稿 §7・§12](</work/1/SFC/tanab/izanagi/docs/workload-description-critic-intervention-preregistration.md>)。LLM の待ちは試走で LLM 系列 job 時間の **69.9%**、block 込みの **60.8%** を占めた。429 の発生時期は推定できないが、上限に当たれば欠測と node 占有が重なる。[起草 insight §3・§4](</work/1/SFC/tanab/izanagi/output/insights/2026-09-28/t2852-p5-intervention-prereg-draft/README.md>)。

## 成立しなかった論点

- T-2869 の「LLM 手法だけが機会を失う**手法間の不公平**」は、全 cell が LLM の本案にはそのまま成立しない。修正は全 cell に入る。修正後の拒否率が cell ごとに違えば介入効果と混ざりうる、という限定的な懸念は残る。[草稿 §12](</work/1/SFC/tanab/izanagi/docs/workload-description-critic-intervention-preregistration.md>)。
- D2259 は「値１個での **LLM 対非 LLM**」を見送った裁定であり、workload 記述 × critic の介入が無価値だと直接証明しない。[D2259](</work/1/SFC/tanab/izanagi/docs/decisions.md>)。
- S3 に移せば P5 の問いが自動的に解ける、とは言えない。S3 の単価は未測定で、生成器対照の arm 構成も別である。[草稿 §12](</work/1/SFC/tanab/izanagi/docs/workload-description-critic-intervention-preregistration.md>)。

## (c) の損失と、その抑え方

延期すれば、**P5 の「なぜ」が論文に載らない**危険がある。S3 自体が遅れ、別登録・実装・実験・評定まで進めなければ、2027-03-01 の最終締切に間に合わない。[差分分析 §0・§4](</work/1/SFC/tanab/izanagi/output/insights/2026-09-21/vldb-direction/gap-analysis.md>)。抑えるには、S3 の生死確認と費用見積りが揃った時点を再提示の期限にし、P5 の実施可否と必要な時間をその場で決める。S1 の草稿は手順の素材として残し、S3 の分散・費用・露出経路を測らずに規模だけ移さない。

## T-2852 の持ち越し項の案

S3（T-2867）の生成器対照の生死確認・実測単価を待つ。
結果が揃った時点で、P5 の介入・分類を S3 で別登録する案と費用を再提示する。
2027-03-01 から逆算して実施・分析が収まらなければ、P5 を未取得の限界として明記する。

## 総括

S1 本走は高い費用を掛けても、受理コードの機構分類という P5 の重要部分を得られない。
一方、延期は P5 を失う現実的な危険を伴うため、S3 の実測後に期限を設けて再判断すべきである。
推す案: (c)