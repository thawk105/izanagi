## must-fix

1. **real — 下限の四捨五入により、図中の不等式が偽になる。**
   対象: `tools/plotting/plot_b10_static_tail_formal.py:290`。

   **放置時の成果物影響:** balanced / read-heavy の図中注記と provenance の `direct_label` が、実際の最小 L より強い下限を表示する。

   根拠: `fig8_b10_static_tail_not_observed.provenance.json` の値と表示は次のとおり。着地 PNG でも同じ表示を目視確認した。

   | workload | 最小 L | 図中表示 |
   |---|---:|---|
   | balanced | 0.2988871311967858（2615 行） | `L >= 0.299`（7309 行） |
   | read-heavy | 0.27379477196757174（4754 行） | `L >= 0.274`（7504 行） |

   修正案: `min L ≈ 0.299` のように丸めた最小値として表示するか、`>=` を維持するなら小数第3位で下方向へ丸める。分類や元の L は変更しない。親裁定 `s4-adjudication.md:50` 自身が「不等式＋小数3桁」を指定しており、実装だけの誤りではない。

2. **real — README の group id の参照先 field が存在しない。**
   対象: `docs/paper-story/figures/README.md:756`。

   **放置時の成果物影響:** README から group 束縛を追う参照が、存在しない `campaigns[].campaign_path` に到達する。

   根拠: 実 JSON の campaign 直下には `campaign_path` がなく、正しい位置は `campaigns[].admission.campaign_path`。生成器は `plot_b10_static_tail_formal.py:195–197` で正しい位置を検査している。

   修正案: README の field path を `campaigns[].admission.campaign_path` に訂正する。「top-level に group id は無い」は正しいので維持する。

## nit

- **real — caption に測定環境名がない。**
  `plot_b10_static_tail_formal.py:280` の条件列には Pegasus がなく、図にも表示されない。`FIGURE_CONVENTIONS.md:70–71` は環境を caption またはサブタイトルに要求する。provenance の `measurement_conditions[].measurement_env` は `pegasus`（131、267、403 行）、results 稿 `:114` と一致する。条件列へ `Pegasus compute nodes` を補う。現状から誤った機体への転移主張までは認定しない。

- **real — 「畳まない」と探索走除外は README にあるが caption にはない。**
  README `:740–745` は明示する一方、caption の末文（生成器 `:283`、README `:795`）は fig2c と別 cohort・続きではない、まで。`t2266-tail` / `t2418-explore` の標本除外と非混合を短く補えば単独引用時も境界が残る。現在の caption が混合を主張しているわけではないため nit。

- **real — 相互検算の説明が実装より広い。**
  README `:758–759` と `tools/plotting/README.md:153–154` は CI・端点比まで `statistics` と照合するように読める。実装 `:224–227` が照合するのは平均2種・CV2種・abort SD。再計算する量と照合する量を分けて書く。また README `:801`、tools README `:152` の「L の一致だけ」は、U も検査する実装 `:237–238` に合わせる。

- **real — correctness の保証範囲の展開が省略されている。**
  caption は検査条件と性能条件の相違を明言しているが、版 `2026-09-17.md:1736–1738` が求める「観測された YCSB point read/write trace」の限定はない。fig6 / fig7 の caption（README `:597`、`:700`）と同様に短く補える。性能認証への読み替えは既に防がれている。

## 親 brief・裁定への所見

- **real:** `brief.md:7` と `s4-adjudication.md:37` の `campaigns[].campaign_path` は誤参照。README に伝播したが、実装は正しい。must-fix 2 の根因。
- **refuted:** 「statistics に median がある」は実物でも確認できた。`statistics["1000"]` に `median` が存在する。生成器が平均を median と取り違えた形跡もない。
- **refuted（top-level の意味で）:** 「JSON に group id は無い」は専用 top-level field の不在として正しい。ただし文字列自体は admission 内の path にあるので、その意味を明記すべき。
- **refuted:** `declining` と “while the abort rate keeps decreasing” を過大主張とする疑い。事前登録 `:306–307` 自身が `L > 0.05` を「低下が続いている」と定義し、results 稿 `:279–283` も同じ帯の低下を記述している。caption は `From 1250 to 9999 us` と範囲を限定し、固定表現・機序否定・採用判断否定を伴う。域外の単調性や価値判断には進んでいない。
- **refuted:** 性能認証との混同。生成器 `:271` の `performance_certified: false`、`:281` の “not the performance configuration” と性能認証否定は、results 稿 `:336–353` と整合する。provenance の `claim_boundary` も性能認証・機序・採用判断をすべて false とする。
- **refuted:** caption の数値転記誤り。group、job ID 3件、18/18、120 certified・0 anomaly、L の範囲 0.2738〜0.3704、比 0.444 / 0.481 / 0.400、48 threads 等は results 稿 `:84–144`、`:164–214`、`:279–281` と一致。比と correctness 件数は実 JSON からも照合した。Bonferroni の説明も事前登録 `:269–279` と一致する。
- **refuted:** README の必要節欠落。fig6 / fig7 と比較し、何を示す図か・既存図との関係・入力・再現・caption・proof chain が揃う。値と bytes の再現の区別も `:772–777` にある。D1637 の引用は `docs/decisions.md:50221–50223` と一致する。
- **検証証拠の限界:** `focus-post-s5.log:16` は 27 passed / 1 skipped だが、`:1` は受入全走でないと明記する。着地 test の緑の証拠にはならない。本レビューでは再実走していない。

## 裁定パッケージ候補 (scope 外だが real なもの)

**fig8 着地後の入口・凍結稿の時点差を、後続 wave で案内する。**

版 `2026-09-17.md:1146–1147`、`:1161` と results 稿 `:48`、`:365–371` は図の不在を記す。これは当時の snapshot として成立し、今回の着地で過去の誤記になるわけではない。凍結稿の書換えは不要。

後続では `docs/paper-story/README.md` の既定の更新面に、図が後から成立したことと fig8 の入口を案内する。分類は「当時は真、後続で古くなった記述」とする（版 `:1964–1966`）。図の成立を性能認証・B-10 閉鎖・第2 cohort の実行許可には昇格させない。D2104 項7の延期も、図の成立だけで解除されたとは扱わない。

## 総括

**must-fix は2件：下限表示の過大な丸め、README の field 誤参照。** caption の主要数値・固定表現・性能未認証の境界は整合する。

指定資料を読み、PNG を目視確認した。入力3件・PNG/PDF・生成器の記録 SHA は現物と一致し、caption の README 包含も確認した。ファイル変更、pytest、生成器の実走は行っていない。
