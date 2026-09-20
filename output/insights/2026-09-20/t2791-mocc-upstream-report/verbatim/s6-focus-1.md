## 所見ごとの判定

指定資料の静的読解で判定した。ファイル変更・pytest・追加測定は行っていない。以下、A / C / D / F / R1 は evidence-map の記号、M は `transaction-e9e477ca.cc` を指す。

| 所見 | 判定 | 根拠 |
|---|---|---|
| must-fix 1 | closed | [S-03] は BACK_OFF=0 / 1 の両方へ訂正済み。C §3.2 の 2/120、D §2.2 の 1/60 と整合。 |
| must-fix 2 | closed | [S-02][S-41][S-57] は差 1 が 20 件、差 2 が 1 件へ訂正済み。C §3.4 B2/069、R1 log 16・24 行と一致。 |
| must-fix 3 | closed | [S-02] は表の実験に限定し、先行 pilot を除外。F「副次解析 (a)」135–137 行と整合。 |
| must-fix 4 | closed | [S-15] は 3/40 対 2/40、p=0.500 と「効果なしは確立しない」を明記。A §5.1 と整合。 |
| must-fix 5 | partial | [S-54] の write-set 条件、[S-55] の RLL 空・一要素条件は補完済み。ただし plan の曖昧な表現を「同義の英訳」と確定する根拠は不足。 |
| must-fix 6 | closed | [S-05] は静的比較を base commit の一ファイルへ限定し、追加 patch を区別。[S-14] と整合。 |
| must-fix 7 | closed | [S-27] は decode・abort・push・reserve と timing 未測定を明記。D §3 項 9 と一致。 |
| must-fix 8 | closed | [S-46] は誤った率の範囲を削除し、CP 上限と不在証明でない旨に限定。A §5.1–5.2、D §2.2 と整合。 |
| should 1 | closed | [S-30] は 09-18 の計装なし二行へ限定し、個別 trace の判定と説明。A §5.1 注と整合。 |
| should 2 | partial | [S-26] の判定語説明は改善。ただし `arms` の初出は [S-15]、定義は [S-20] で、初出説明の問題が残る。 |
| should 3 | closed | [S-33] は説明を区別できないとし、lock 保持中の出力を first witness に限定。A §1 項 4、D §3 項 1 と整合。 |
| should 4 | closed | [S-61] は runner 原本を archive、repo 内を写しと区別。A §2・§10、C §1.4・§6.2 と整合。 |
| should 5 | partial | [S-14] と evidence-map K5 の日付種別は訂正済み。ただし brief / 段 4 の修正現物は今回の射影外で、申告の独立確認はできない。 |
| nit 1 | closed | [S-16] は baseline と BACK_OFF=1 の置換を明記。C §1.3、D §1.5 と整合。 |
| 親発見 integrity | regressed | [S-40] の true 16 / false 5 はログと一致するが、「true 16 件は計装あり」が誤り。R1 は counter 全 0 の機械検査も実装していない。 |

## must-fix

**1. 所見 must-fix 5：[S-55] の前提を「原典で確定した同義の英訳」と扱えない。**

plan 24 行の「互いの read key」は、それだけでは「各自の read key」と一義的に同義ではない。ただし、同じ行の操作指定を集合で書くと、

- W：read y、write x
- R：read x、write y
- x ≠ y

となり、plan 34 行の「各 write set 一要素」と合わせれば、[S-55] の **R は x を書かず、W は y を書かない**という解釈は整合する。

一方、README §3 の「相手の read key を自分の write set に含めない」を文字どおり適用すると、W は x を書かず、R は y を書かないことになり、操作指定と矛盾する。「略記のずれ」と断定できるかは**不確実**である。

したがって、例を保持すること自体は可能だが、明示的な操作指定から再構成した条件として記す必要がある。また、現 [S-55] には plan 25 行の「双方の旧 payload 読取が相手の更新前に終了する」が明記されていない。「body inconsistency なし」を述べる例では補うべきである。M 1010–1025 行の二検査と 1195–1207 行の publish / unlock は、この条件付き説明と整合する。

修正案（英文、[S-55]）：

> Consider the following conditional reconstruction of our internal example. W reads the old value of y and writes only x; R reads the old value of x and writes only y, with x ≠ y. Both reads finish before the other transaction updates the corresponding record. Assume cold-record reads and empty read-lock lists. W locks x and validates y before R locks y. R then locks y and validates x: its version check precedes W's publication, while its counter check follows W's publication and unlock. Under these assumptions, ordering (ii) could allow both transactions to commit without a body inconsistency. We have not demonstrated this ordering in any reported signal run.

evidence-map S-55 の「略記のずれ」「英訳は plan の逐語に従う」は撤回し、操作指定からの再構成であること、README の表現との不一致を記録する。

**2. 親発見 integrity：[S-40] が履歴上の flag と計装条件を誤って対応づけている。**

R1 log の true 16 件の内訳は、**08-26 の 5 件＋T-2774 の計装あり 2 件＋T-2779 の 7 件＋witlight の 2 件**である（log 1–21 行）。最初の 5 件は本文表 A 自身が「Instrumentation patch: no」としている。したがって、

> true for the 16 runs from arms built with the instrumentation patch

は誤りであり、上流の読者に「全 21 件を同じ現行 gate で評価し、計装有無だけで 16 / 5 に分かれた」と読ませうる。

現行 `clean()` は違反 counter 全 0 に加え、X/P evidence と commit witness 条件を要求する（model.py 450–467 行）。X/P gate は source assessment の二 field が `EVIDENCE_PRESENT` であることを検査する（77–82 行）。A §5.1 注は false 5 件についての説明と整合するが、この定義を歴史的 true 5 件へ遡及適用できる根拠はない。

さらに R1 script は `integrity['clean']` を読むだけで（57 行）、違反 counter、proof-surface、commit witness を検査していない。したがって、[S-02][S-40] の「counter 全 0」を**R1 が機械確認した**という evidence-map の説明は成立しない。A §5.1、C §3.4、F「副次解析 (b)」には counter に関する記録があるが、全 21 件の全 field を R1 が再検算したとの申告は閉じていない。

修正案（英文、[S-40] の flag 説明部分）：

> Across the archived outputs, `integrity.clean` is true in 16 runs and false in five. The true outputs include the five August 26 runs without the instrumentation patch. The five false outputs are from the two uninstrumented arms of the first September 18 experiment, for which the source report identifies missing X/P evidence. Under the current checker definition, zero violation counters alone do not imply `clean`; the X/P evidence gate and commit-witness condition must also be satisfied. These archived flags are not a uniform re-evaluation under the current checker.

counter 全 0 の部分は、実際に counter を検査する再計算記録を添えるか、確認済み資料の記述範囲へ限定する必要がある。

## should

**1. should 2：用語定義の位置がまだ初出より後である。**

対象は [S-15] の `most arms` と [S-20] の定義。意味自体は A §4、C §0.2 に沿うが、親の「初出説明を閉じた」という申告は不十分。[S-26] の `supported` / `contradicted` の説明は閉じている。

修正案（英文、[S-15] より前へ移動）：

> An arm is one build/runtime configuration; a block is a group of runs executed on one node.

**2. should 5：本文は訂正済みだが、所見全体の closed は未確認。**

[S-14] は commit 日と fetch 日を区別しており、今回確認した本文に残る誤りはない。ただし、前巡所見が求めた brief / 段 4 の訂正は対応表の申告しか確認できない。修正済みかは**不確実**。

本文をさらに限定する場合の英文：

> The comparison uses our local mirror at `50c7946d`, committed on 2026-06-28; the supplied artifacts do not establish the mirror's fetch date.

残作業は、その表現が brief / 段 4 にも反映されたことの現物確認である。

## nit

残る nit はない。[S-16] の baseline 表現で前巡 nit 1 は閉じている。

## evidence-map と回帰点検

指定された対応行はすべて存在する。次の区別が必要である。

| 対象行 | 点検結果 |
|---|---|
| S-03 / S-05 / S-14 / S-15 / S-20 / S-26 / S-27 / S-30 / S-33 / S-46 / S-54 / S-61 | 修正文に対応する出所・限定へ更新されている。S-20 の問題は本文での配置。 |
| S-41 / S-57 | 20/21 と B2/069 を反映済み。ただし fix-table が申告する R1 参照の追加は実際にはない。既存の出所でも数値は支持される。 |
| S-42 | R1 の最大 key・二理由辺の集計と一致。 |
| S-55 | 原典の追加はあるが、「略記のずれ」と確定する説明は過大。上記 must-fix 1。 |
| S-02 / S-40 / R1 | counter 全 0 を R1 の機械集計結果とする説明が script と不一致。上記 must-fix 2。 |

R1 の script / log の SHA-256 は対応表記載値と一致した。これはファイル同一性の確認であり、記載された検査項目を script が実施していることの証明ではない。

指定された差し替え文について、上記以外に新たな根因確定・修正提案・不在証明・同等性・性能・同一 binary・master 再現・対応要求への拡張は認めなかった。[S-04][S-25][S-44] の三分岐、[S-45] の出所照合未達、[S-51] の binary 限定も維持されている。ただし、[S-40] の新しい誤対応は検査器側の確認範囲を過大に見せる回帰である。master の挙動、静的候補の実行順序、witness の時間効果は引き続き**未実測**。

## 総括

**closed 11 件 / partial 3 件 / regressed 1 件。**

**残る must-fix は 2 件：** [S-55] の前提を同義の英訳として確定する扱いと、[S-40] の計装別内訳・R1 の counter 検算範囲を訂正する必要がある。

**NO-GO** — 現状は、人間が送信判断へ進める本文案として記録する条件を満たさない。