## 対応表

| 所見 | 判定 | 修正後の記述と現物による根拠 |
|---|---|---|
| 1：区間の「内側か境界上」 | **closed** | 題名・§2.4・§2.7 が「内側32／境界を跨ぐ4／区間全体が外側0」に修正済み。独立再計算も **32／4／0**。点推定36件がすべて内側という追記も一致。 |
| 2：throughput の単調性 | **partial** | §2.6 の abort 率18系列、read-heavy 6系列、最大μ、adaptive比較は一致。ただし追記した「balanced では μ2 または μ5 が最大で単調ではない」は不正確。balanced は **4系列が狭義単調減少、2系列が非単調**。 |
| 3：「別node」 | **closed** | §0.1・§1.3・限定6・15で write-heavy のhostを未記録と明記。JSONのhostは順に `not-recorded-legacy-v2`／`bnode015`／`bnode088`。限定15もprobeとwrite-heavyのhostが異なるとは断定していない。 |
| 4：READMEのD1097の主語 | **closed** | READMEは「待ち量についての**主張**は指示値の平均に限定し機序は述べず」。D1097と本文の限定3に整合。ただしinsightへの反映漏れは下記。 |
| 5：zero-loopの名目総待ち量 | **closed** | §2.6が「none・adaptiveはnull、zero-loopは0」に修正済み。JSONもそれぞれ **9件null／9件null／9件0**。 |
| 6：D1588の失敗系列 | **closed** | §1.4がD1588へ帰属させて「45件すべてSHA不一致で測定不能」「選択の余地は無い」を追記。D1588と一致し、「独立に監査していない」も明示。 |
| 7：「台帳ID未起票」 | **closed（反証受理）** | READMEの既存K2稿の行にも同じ運用欄がある。今回の結果命題の誤りは示せず、削除不要という裁定を支持する。 |

## 再計算

親のscriptは実行せず、provenance JSONを読み込む独立したPython計算で確認した。

| 検査 | 結果 |
|---|---|
| (a) abort率 | **一致**。μ＝2→5→10→25→50→100で、18系列すべて狭義単調減少。 |
| (b) read-heavy throughput | **一致**。6系列すべてμ2から狭義単調減少。 |
| (c) 最大throughputのμ | **一致**。下表のとおり。ただし「balancedが非単調」という追加説明には例外がある。 |
| (d) adaptiveと登録cell | **一致**。9 blockすべてでadaptiveが登録12 cellの最小値未満。 |
| (e) write-heavy μ2の区間 | **一致**。再計算値は **[−3.2873517223%, +4.7758087084%]**。小数第2位で[−3.29%, +4.78%]。 |
| (f) 全点推定が等価域内 | **一致**。constant 18件は0。symmetric-modulo 18件は **−0.9738229292%〜+1.3712287630%**で、すべて絶対値3%未満。 |
| (g) job script SHA-256 | **一致**。稿の全桁が4受領証の `job_script_sha256` と一致し、異なり数は3。read-heavyとreportは同一。 |

最大μは各欄block-1／2／3順。

| workload | constant | symmetric-modulo |
|---|---|---|
| write-heavy | 5／10／5 | 10／10／10 |
| balanced | 2／2／5 | 2／5／2 |
| read-heavy | 2／2／2 | 2／2／2 |

adaptiveの中央値と登録12 cellの最小値：

| workload | block-1 | block-2 | block-3 |
|---|---:|---:|---:|
| write-heavy | 1,354,088 < 2,346,648 | 1,356,456 < 2,353,744 | 1,375,023 < 2,355,560 |
| balanced | 1,253,516 < 1,860,266 | 1,232,300 < 1,862,902 | 1,229,420 < 1,863,479 |
| read-heavy | 2,323,131 < 4,459,835 | 2,327,468 < 4,452,598 | 2,326,305 < 4,458,944 |

照合したSHA-256：

- write-heavy：`c2c92b6c0a4d5487ec25895cdf42ca1243fe38094e470e81a2f3d3a401deebcc`
- balanced：`bc80b66684bfe2dd498b4587846964f7497337b5921bdda97b81d169634ae892`
- read-heavy／report：`6f633ad08579d020190bf76263c006774a2d548a48ccd3f99106f090df628f6b`

追加照合でも、§2.6の**135行×16列**はreportと一致し、JSONから組み立てた値とも一致した。§2.4の効果・区間、3 campaignのmeta digest、受領証の投入時刻、source commit・解析SHA・hostにも不一致なし。件数は**限定19／対差54／生標本135**で整合する。修正文にdocs間の行番号参照は見当たらない。checker・pytestは実行していない。

## 新規所見

1. **must-fix — §2.6の「balanced … 単調ではない」が過剰な一般化。所見2の未解消部分。**

   修正文：「write-heavyではμ5またはμ10、balancedではμ2またはμ5が最大で単調ではない」。

   JSON `records[].median_tps` の再計算では、balancedのconstant block-1・2とsymmetric-modulo block-1・3は狭義単調減少。例えばconstant block-1は
   **4,187,219 → 4,167,860 → 3,813,996 → 3,004,729 → 2,428,183 → 1,860,266**。

   「write-heavyは6系列すべて非単調、balancedは4系列が狭義単調減少、2系列が非単調」と分けるか、「単調ではない」を削除する。現在の文ではbalanced全系列が非単調と転記され得る。機序・採用根拠を否定する但し書き自体は適切。

2. **should-fix — 記録insightに修正前の説明が残っている。**

   [insight README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-waiting-grid-results/output/insights/2026-09-20/b10-waiting-grid-results-doc/README.md)の冒頭に「機序は指示値の平均に限定」が残り、修正後README・D1097と不整合。また§1・§4は「効果量」「境界4」と略し、区間と点推定の区別が曖昧なまま。

   現行の要約を「待ち量についての主張は指示値の平均に限定し、機序は述べない」「95%区間は内側32／境界を跨ぐ4／区間全体が外側0」に揃える。旧briefの記録として残すなら、採用しなかった表現であることを明示する。

## 総括

**closed 6／partial 1／regressed 0。新規所見2件（must-fix 1、should-fix 1。must-fixは所見2の継続）。判定：NO-GO。**

要求された再計算値はすべて一致したが、balancedの単調性の一般化とinsightの旧表現を着地前に直す必要がある。
