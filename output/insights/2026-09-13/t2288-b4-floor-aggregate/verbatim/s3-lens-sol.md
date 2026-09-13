## 所見 (重い順)

以下、`P`＝指定の `s2-plan.md`、`B`＝`s1-brief.md`、`I`＝`orchestrator/campaign/p3_b4_floor_artifact_issuer.py`、`F`＝`orchestrator/campaign/floor_pair_driver.py`、`A`＝`orchestrator/campaign/p3_b4_analysis_contract.py`、`R`＝`orchestrator/campaign/p3_b4_material_report.py` と略記する。判定は静的検査による。

**所見1: spec への完全一致は、裁定された「3 workload × 2窓」への完全一致を保証しない。〔real：保証範囲の不足〕**

根拠: P:57、62、72、135。F:870 は窓を非空とするだけで、F:919 は窓の非重複だけを検査する。F:1085 の `closed_strata` 一致も、その spec が宣言した窓・pair への一致である。

反例は、各 spec が1窓だけを宣言し、その全セル・全標本を正常に報告する3 summary。plan の窓・層・セル・標本検査は全部通り得る。N入力なので、期待列と実入力を同時に2 specへ減らす場合も同様である。これは summary 内部だけの欠落とは別問題。

成果物への影響: 裁定対象の一部しか含まない最大を、裁定対象全体の最大と誤認できる。

推奨対応: 「明示された spec に対する完全性」と「D1936項7の採用条件」を区別する。既存の採用確認に残す条件を具体化し、機械的に3 workload・2窓を保証したと書かない。新しい台帳は不要。

**所見2: v2 の期待 spec 列は、loader では成果物内の自己申告に戻る。〔real：再構成保証の限界〕**

根拠: P:111、116、150、152。既存 loader の外部入力は成果物 path/hashだけ（I:1039）、resolverも同じ2値だけを渡す（I:1243）。

攻撃は、非最大 source と対応する `aggregation` の期待 spec pin を同時に削り、identity・非保証・名前・成果物hashも残った入力に合わせて再構成すること。期待列の独立した供給元が loader にないため、P:251 が排した循環は「成果物内の期待列」を経由して復活する。

ただし、**既存の§5 pinを固定すれば I:1052 のhash検査が止める**。外側pinも更新する攻撃まで拒否できる、という保証は成立しない。明示期待列を固定した発行APIの検査自体が恒真という意味ではない。

成果物への影響: P:116 の「非最大入力の脱落を拒否」は、期待列を維持した脱落に限定される。

推奨対応: 検出できる改変条件を明記し、「sourceだけ削除」と「期待列も削除して再pin」を区別する。後者は既存pinの採用責任の境界として扱う。

**所見3: campaign 内 strata の比較対象が文字どおりなら、正常な2窓入力を拒否する。〔real：実装前に解消すべき曖昧さ〕**

根拠: P:74 は campaign内strataも `spec.statistics.closed_strata` と一致させる。一方、F:2843、2852、2870 は各campaignにその窓のstrataだけを出力する。

全窓の `derivation[0].strata` は全 `closed_strata` と比較できるが、各campaignを全窓集合と比較してはいけない。

成果物への影響: 素直な実装では正規 producer の2窓summaryが通らない。

推奨対応: campaignごとの期待集合を `closed_strata` の当該 `window_id` への射影と明記し、campaign所属外のstratumも拒否する。

**所見4: 欠測の「重複なく」を record に適用すると、許容欠測の正例を壊す。〔real：会計単位の曖昧さ〕**

根拠: P:76–78。F:2824 は欠測を sample key の**集合**にするが、F:2900 はそのsampleに属する各sideのrecordを残す。F:3074と3075もsample数とrecord数を別々に出力する。

したがって、同じ `(window_id, pair_id, sample_index)` が `dropped` に複数回現れること自体は不正ではない。

成果物への影響: sample key重複を行重複と扱うと、正常な欠測を含む集約が拒否される。

推奨対応: retained sample集合と、recordから導出したdropped sample集合の非交差・完全分割を検査する。sample数・record数・stratum件数・campaign件数を区別し、`dropped_fraction` と `threshold` の照合も明記する。既存I:441は分数の型、I:442は文字列しか検査していない。

**所見5: Fraction は最大選択の下振れを防ぐ追加機構ではない。〔refuted：順序逆転の疑い／real：briefの説明過大〕**

根拠: P:94、205、I:817、B:36。

有限binary64値を `as_integer_ratio()` で変換する場合、値をそのまま有理数に埋め込むため大小順は保存される。`max` 自体も算術丸めをしない。この入力領域で順序が割れる値はない。

Fractionの意味は、選ばれたbinary64値のexact保存と、下流の有理数判定への受け渡しにある。I:579の除算・減算で既に生じた丸めは修復しない。

成果物への影響: 「Fraction比較だから全計算が保守側」という保証は成立しない。

推奨対応: P:205を採用し、B:36を修正する。ratio/hexの独立期待値は有効だが、近接値テストをfloat比較変異の検出証拠に数えない。

**所見6: tie増加の危険は最大演算そのものより、採用対象の取り違えにある。〔条件付きreal〕**

根拠: R:267は受理したfloorを評価器へ渡し、A:525–527は  
`abs(on_throughput - off_throughput) / reference <= floor`  
でtieにする。floorが大きいほどtie集合は広がる。

固定された正しい対象集合から最大を取ることによるtie増加は裁定どおりである。一方、余計な高いfloorのspecを期待列にも追加すると、所見1・2の境界では自己整合したままtieが増える。逆に高い層の欠落はfloorを下げるので、通常はtieを**減らす**向きである。この二つを混同してはいけない。

値域については、I:302がbool・非有限、I:718が負値・負のゼロ、I:823が1以上を拒否する。全入力を通すP:65を守れば、不正入力を除外して続ける経路はない。最大値tieの代表選択（P:94）は値を変えない。

成果物への影響: v2対応だけでは「裁定された対象のfloorである」ことは追加保証されない。

推奨対応: 既存の値域・全件拒否を維持し、採用対象の適合までresolverが検証するとは記述しない。

**所見7: 非保証は保存されるが、平坦化したレポートでは帰属が失われる。〔real：表示上の限界〕**

根拠: P:111–113は入力別section/itemsも保存するため、集約成果物内では情報は消えない。一方、R:952のsource表示は成果物path/hash等だけであり、平坦な非保証一覧から各文言の入力元は分からない。

`FREEZE_TIMING_NOT_PROVEN`（I:50）は、各specの凍結時点に加え、**集約対象spec列を結果前に選んだかも証明しない**と読む必要がある。重複した文言は独立した証拠数ではない。また「参照先を実在照合していない」（I:53）は、v2でspec等を再読込するP:116との関係が説明不足である。

成果物への影響: 非保証の欠落は防げても、保証範囲の読み違いは残る。

推奨対応: 入力別保存を維持し、平坦な一覧は原文の転記であること、raw windowの測定内容と選択時系列は未証明であることを説明する。

## 恒真・空回りの疑い

**所見8: 閉包検査は多くが有効だが、「期待値を固定した場合」という条件付きである。**

根拠: P:61–79、97、I:390、412、496、666、F:1060。

| 倒す対象 | 実際に止める検査／残る抜け道 |
|---|---|
| summaryを1件落とす・余計に入れる | 固定期待specとの一対一対応が止める。期待列も変えれば止まらない |
| summaryの窓を落とす・増やす | specの窓との対応が止める。spec自身が1窓なら別問題 |
| 窓ID・campaign・pathの帰属を替える | 形式上正常なら新しい帰属照合まで到達する |
| samplesとstrataから高い層を同時に消す | 既存I:661は通り得る。specの閉じた層との一致が止める |
| spec内に未使用cellを残す | F:1071はpair→cellしか検査しない。新しい各窓のcell被覆検査が有効 |
| 標本を消す・予定外indexに替える | 自己整合も更新すれば、spec由来予定keyとの分割検査が有効 |
| 件数や欠測率を偽る | 再計算した集合との件数・率照合が必要。既存検証は型中心 |
| 空stratumを残す | 既存I:627の非空検査で止まる。stratumごと消すなら閉包検査 |
| summaryの統計メタデータを替える | 新しいspec照合が有効。`upper_function`変更は既存I:649で止まる |

成果物への影響: 期待集合をsummaryから導かなければ層・標本検査は恒真ではない。ただし、検証済specをそのまま期待側・実側の両方に使う実装なら空回りする。

推奨対応: 実側はsummaryから抽出し、期待側はpinされたspecから抽出する。cell被覆については「specのpair配置自体の検査」と「summaryの層被覆」を別の述語として扱う。

**所見9: 負例計画には、手前の検査で赤になるものが複数ある。**

根拠: P:182–199。以下は未実装テストの到達性判定であり、実走結果ではない。

| 負例 | 判定・必要な作り方 |
|---|---|
| nonmax value | floorだけ変更するとhexとの一致検査（I:1097）で先に止まり得る。hex等も整合させて再構成まで到達させる |
| rounded ratio | 不正ratioはI:1077、1082で先に止まる。丸めた正規ratioと対応hexの組を別ケースにする |
| spec closure `[missing,extra,duplicate,hash]` | missing/extraは実入力だけ変更すれば有効。duplicateは期待列検証、hashはF:1233で先に停止。全部を閉包検査の証拠とは呼べない |
| window binding `[missing,extra,duplicate,campaign,path]` | window行の変異は到達可能。campaign行の複製はI:467で先に停止。campaign/pathは形式上正常な別値を使う |
| partial strata | 有効。samples・strata・最大を整合させれば既存自己整合を通る |
| uncovered spec cell | 有効。未使用cell自体はF:1071で拒否されない。ただしspec hash、HEAD blob、較正束縛を正常にする必要がある |
| sample accounting `[missing,extra,overlap,count,threshold]` | missing/extraはvalues・upperも更新する。既存sample複製はI:529で先に停止。retainedとdroppedのoverlapは新検査へ到達可能。countは型を保つ。threshold超過は件数を整合させ、`generated`を保った変異にする |
| statistics mismatch | summaryの`difference_formula`なら有効。stratumの`upper_function`ではI:649で先に停止 |
| identity mismatch | P記載どおり単体有効な入力なら有効。env/threadsだけ変更すると較正検証で先に停止 |
| invalid member `[one,above_one,nonfinite,bool,not_generated]` | 全件拒否の証拠にはなる。producerが出す1以上の結果はF:3050により非生成statusとなり、I:678が先に止める。値域検査の証拠には自己整合した`generated`変異が必要。NaNはJSON段階でも止まり得る |
| dropped limitation | 成果物側だけ削れば有効。source自体とそのpinも整合して変更する攻撃まで拒否する保証ではない |
| source mutation `[missing,hash,path_alias,duplicate]` | missing/hashはsource読込の証拠。aliasはcanonical pathかspec出力path照合、duplicateは重複検査。各停止段階を分ける |
| existing target | create-onlyの有効な負例 |
| wrong filename identity | 独立期待名とのassertは有効。ただし入力拒否テストではなく実装変異テスト |
| schema dispatch | 有効。unknown版と版に対する欄集合不一致を区別する |
| incomplete CLI mode | 必須引数・排他性の有効な負例。集約閉包の証拠ではない |
| addendum at section end | raw pinの有効な負例 |
| invalid aggregate → report | エラー伝播の証拠として有効。どの集約検査が働いたかは別途assertが必要 |

成果物への影響: 「赤になった」だけでは、対象の集約機構が実装された証拠にならない。

推奨対応: P:203の方針を具体化し、上表の停止段階を負例ごとに記録する。共有ゲート変異が「対応testだけ」を赤にすることは要求しない。

## plan の採用可否

**条件付き採用。現状の文章をそのまま実装指示にするのは不可。**

必要な修正は、期待列と採用条件の保証境界、campaignごとの層集合、欠測の会計単位、負例の到達段階である。Fraction最大、全件検証、create-only、入力別出所・非保証の保存、v1/v2の明示分岐は採用できる。

新しい台帳や一般的な保証基盤は不要。P:135が既に残している人手の採用責任を、機械検査済みの事実と混ぜないことが重要である。

## 親 brief への反証

**所見10: 「機械的一致＝結果前に閉じていた証明」と「本waveで実測不可能」は、いずれも主張が強すぎる。**

根拠と判定:

- **B:29–33のP1:** 現在渡された期待列との一致では過去の選択時点を証明できない。F:1237のHEAD一致・F:1290の祖先検査も同様。planによる反証は妥当。
- **B:7の「足りないのは集約規則だけ」:** 正規の全体最大にはsummary被覆検査も必要。既存I:661はsummary内部の一致に留まる。規則・実装双方を含む短縮表現としても、無条件の主張にはできない。
- **B:3–5の「verdictが1種類、原因は未記入だけ」:** 評価器に到達する正常組立経路については支持される。しかしR:244では組立拒否により分析結果なしとなり、R:221ではfloor拒否で停止する。floorを埋めれば他の正しさ条件も成立する、とは言えない。
- **B:16–21の実測不可能:** 較正0件・spec0件という親の実測は再検証していない。そこから言えるのは「現状の入力では全体の測定を直ちに開始できない」。D1936項7:7は較正認可済み・取得の先行依存を述べ、D1855:30は較正取得を前進として挙げる。既存driverもF:2995に存在し、指定 `prereg-s11-2-tail.md:41` は実行機構不存在を訂正している。wave全期間で不可能という証明にはならない。
- **B:36のFraction説明:** 所見5のとおり過大。
- **B:10の「対応testだけ赤」:** 共有検証関数を持つ実装では一般に成立しない。P:203の訂正を採るべき。

成果物への影響: 現在の未充足条件、今回のscope選択、技術的不可能性を混ぜると、後続waveの着手条件を誤記する。

推奨対応: 「本waveは規則と配線に限定し、較正取得・測定はscope外」と記す。これは妥当な作業範囲の選択であり、実測が将来も不可能という結論を必要としない。

## 総括

最大演算は妥当だが、裁定対象への適合と結果前の固定は閉包一致だけでは保証されない。  
campaign層・欠測会計・負例到達性を修正すれば、planは条件付きで採用できる。  
静的検査のみ。編集・commit・pytest実行は行っていない。