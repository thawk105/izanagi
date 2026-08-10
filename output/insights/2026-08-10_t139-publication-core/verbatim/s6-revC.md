結論は **NO-GO、blocker 4 件**です。数学式の主要な数値は再現しましたが、stress check の受理集合、同一データ再解析の閉鎖、台帳所有が閉じていません。

## Blocker

### B1. §7.4 が §3.3 で排除した `6×6` 正定値 gate を simulation だけへ再導入している

[§3.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:149) は「`6×6` の正定値を要求しない」と明記しています。一方、[§7.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:409) は、

> 「`6×6` 標本共分散が特異になる dataset」を「非棄却として数える」

としています。

これは意図的なモデル差ではなく、A1.2 で退けた category error の再導入です。`J≤6` では rank が高々 `J−1<6` なので、全 synthetic dataset が必ずこの枝に入り、`J=4,5,6` の `3×6×6=108` セルで `x=0` になります。`B=10^6` なら `x=0` の上側限界は約 `1.2794×10⁻⁵` で、`α_pub=0.025` の最小閾値 `0.025/6≈0.004167` を自動的に通ります。

実データでは workload 別 `3×3 S_w` が正定値なら計算できるのに、simulation は `6×6` 特異性だけで偽陰性へ送るため、型 I 誤りを下方に歪めます。

**成果物影響:** stress pass が偽陽性になり、材料レポートへ「固定 empirical model 下で FWER・同時被覆が支持された」という誤った受理表示が付く可能性があります。

### B2. §7.3 は seed が正しくても乱数列と `x_{Jkr}` を一意に再生成できない

seed の SHA-256 は正しいです。

```text
SHA-256("t139-publication-core-stress-v1")
= 7ba4ba27d67b66b3aa3e3be9e7b649a08b1025c773ef3dddf43f3f9d55305ad9
```

しかし [§7.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:397) の

> `SHA-256( seed || domain || uint64_be(counter) )`

では、少なくとも以下が未定義です。

- `seed` を64文字の hex ASCII とするか32 raw bytesとするか。
- `domain` の byte grammarと、`J,k,r,dataset,workload,cluster,block` の符号化。
- counter の開始値、reset 単位、reject 時の進め方。
- digest を5択へ写す整数の byte order。
- W1/W2 の residual 抽出を同じ index で結合するか独立に行うか。
- 60個の `(J,k)` streamを独立生成するのか、一つの6次元 datasetを成分間で共有するのか。
- 「対象成分を0に置く」以外の5成分をどの weak-null face に置くのか。

最後の複数点は、§7.4 が `6×6` 特異性を参照するため無害ではありません。W1/W2 の結合方法や成分間共有によって、特に `J≥7` の特異性判定が変わり、`x_{Jkr}` が変わります。

**成果物影響:** 同じ記載 seed から異なる `x_{Jkr}`、`U_{Jkr}`、stress pass/fail が生成され、材料レポートと試行台帳の stress 証拠を一意に再生成できません。

### B3. §0 の無効化条件が §8.3 の同一データ再解析禁止を迂回する

[§0](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:38) は、source §7 を変更する第2 erratumが既に予定されていると認識しながら、§3・§5・§7・§16への erratum で本書を無効にすると定めています。つまり、現在の草案は既知の予定済み erratum によって無効になる設計です。

さらに [§8.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:472) は同一データの第2 coreを禁じながら、

> 「本書が無効になる場合に限り、新しい公表 core を起こす」

と例外を開いています。erratumについて以下の制約がありません。

- 公表結果を見る前に必要性が確定していたこと。
- 統計手続きと独立の理由によること。
- substantive changeであり、§16等への無害な文面変更ではないこと。
- 新しい公表 core が既に観測済みの同一 raw datasetを再解析しないこと。

したがって結果後に source erratum を発行し、無効化を経由して同じデータへ第2手続きを当てる経路が残っています。

**成果物影響:** 同一 raw datasetに複数の公表 core・Holm棄却集合・同時下限を後選択でき、材料レポートの受理表と台帳の core参照が変わります。

### B4. 追補 B と追補 P の公表 ordinal 所有が未解決なのに C-4 が承認を推奨している

[package C-2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/package.md:120) 自身が、

> 「どちらが公表系列の ordinal を予約するのかを決める必要がある」  
> 「現 B から…外すか、追補 P 側を参照だけにするかの選択が残る」

と認めています。

ところが publication core [§9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:498) は、追補 P が source追補Bを「継承・参照・合成しない」としています。したがって「P側を参照だけにする」は草案と両立しません。残る「Bから予約規定を外す」は、今回禁止されている追補Bのbytes変更です。

その状態で [C-4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/package.md:144) が承認を推奨するのは早過ぎます。C-1との矛盾はありませんが、C-2は未閉鎖です。

**成果物影響:** 同じ `(family_root, individual_publication, ordinal=1)` の二重予約または予約元不在となり、公表表の受理と試行台帳の ordinal／追補参照を一意に確定できません。

## 段3全所見の対応表

`partial`／`regressed` では不足・悪化した逐語を記載します。

| 所見 | 状態 | 草案での対応・不足逐語 | 放置時の成果物影響 |
|---|---|---|---|
| A1.1 | closed | marginal正規・非退化だけを要求し、成分間独立を要求していない | なし。周辺p値とHolm集合は変えない |
| A1.2 | **regressed** | §3.3「`6×6`…正定値であることは要求しない」に対し、§7.4「`6×6`…特異…非棄却として数える」 | stressの受理集合を不当に広げ、FWER支持表示が変わる |
| A1.3 | closed | 3成分とも `H₀:μ≤0` 対 `μ>0` で固定 | なし。符号・p値を変えない |
| A2 | closed | Holm式、strict比較、tie-breakは正しい | なし。調整済みp値・棄却集合は一意 |
| A3.1 | closed | 数値例の `T₂`、`c_B`、`L₂` は一致 | なし |
| A3.2 | closed | 反例を否定する新しい不可能条件を入れていない | なし。反例は有効 |
| A4 | closed | 不採用理由を追加同時正規性と `α_pub/2` の保守化へ訂正 | なし。区間構成はBonferroniのまま |
| A5.1 | **partial** | §7.5「360セルは…覆う」という理論は正しいが、§7.4の特異性規則により108セルが恒常的 `x=0` | 理論上のFWER上界と実際に検査した受理集合が一致しない |
| A5.2 | **regressed** | 「非棄却として数える」で未定義枝は埋めたが、`6×6` 特異性を計算不能理由にしたため実データ枝と逆転 | stress pass/failが下方に偏り、支持表示が変わる |
| A5.3 | closed | 6,000万dataset・3.6億比較、実行時間未確認を明記 | 未完了なら支持表示不可。source certified選択は不変 |
| A5.4 | closed | source digestをseedから分離し、文書identityと乱数domainを区別 | 値・受理集合への直接影響なし。namespace喪失は後述nit |
| A6 | closed | 正規model条件付き、分布自由・permutation優越を明示的に否定 | 仮定不成立ならp値・区間はmodel-based記述に限定 |
| A7.1 | closed | 「全部非有意になりやすい」を採用していない | Holmを弱める根拠にならない |
| A7.2 | out-of-scope | C-1へ返し、凍結済みsource core／追補Aを変更していない | `d⁻` が不足すれば本走・certified選択・材料レポート・台帳が生成されない |
| BL-1 | **partial** | §11「文面からは検証できない」「運用手順によってのみ担保」 | freeze時点を証明できず、表と台帳の事前登録参照を受理できない |
| BL-2 | **partial** | §2.1「適格clusterの全件」としたが、§11「source validator…未実装」「複写元が無い」 | canonical dataset pointerがなく、公表表は生成不能または自己申告になる |
| BL-3 | **regressed** | §8.3「経路は閉じている」の直後に「本書が無効になる場合に限り、新しい公表core」と例外化 | 同一データのpost-hoc再解析と第2棄却集合を受理できる |
| BL-4 | **partial** | package「どちらが…予約するのかを決める必要」「選択が残る」 | main admissionと公表ordinal参照が閉じず、表・台帳を確定できない |
| BL-5 | **partial** | §8.1「呼び手が新しい値を名乗ることはできない」に対し、§11「公表台帳…実体なし」 | 現状では自己申告リセットを拒否できず、台帳が無ければ表は生成不能 |
| BL-6 | out-of-scope | C-3としてroadmap裁定へ返している | 裁定なしでは材料レポートを限定例外下の事前登録解析として受理できない |
| BL-7 | closed | seedとprovenance identityを分離した | core参照は結果側のcommit/path/blobで担うため、値・受理集合は変わらない |
| BL-8 | out-of-scope | §11でp exact-key実装なしを明記 | 実装されるまで追補Pを権威的に受理できず、公表表を生成できない |
| BL-9 | out-of-scope | producer→validator→consumer→ledger未接続を§11で明示 | `qualification_status`の権威値がなく、表・材料レポート・台帳を受理できない |

A6 は草案で閉じていますが、段4裁定のレンズA表から項目自体が脱落しています。「全所見を裁定した」という追跡可能性は不完全です。

## 恒真・未発火の保証

現状、次の規定は対象となる producer／validator／台帳が存在しないため、違反入力を一件も受けず恒常的に成立します。

| 規定群 | 現在なぜ発火しないか | §11による打消し |
|---|---|---|
| dataset全件性、6行固定、`qualification_status`逐語複写、逆流禁止 | source/publication validatorとrendererがない | 明示されており概ね正直 |
| source判定不能を対角だけで救済しない | p値を生成するpublication validatorがない | §3.3と§11で明示 |
| `p01`〜`p03` exact-keyと閉集合 | resolver/checkerがない | §11で明示。ただし§9の「解決に失敗する」は現在形として過大 |
| root、create-only ordinal、閉じた`ledger_kind` | canonical ledgerがない | §8.2と§11で明示。ただし§8.1の「名乗ることはできない」は過大 |
| §10.4の11変異をkillする | 実装も変異検査もない | 「本waveは実装しない」と明示 |
| stressの除外・再抽出禁止 | stress runnerがない | 未完了なら支持表示不可として正直 |
| pilot前freeze | 外部時刻根拠と予約手順がない | §11が「証明していない」と明示 |

したがって `qualification_status` については論理矛盾ではありません。「複写元が無ければ表を生成しない」という未成立前提付きの fail-closed 規定です。ただし現在は実効保証ではなく、発火しない将来契約です。

§11はこの空白をかなり正直に打ち消しています。例外は、§8.1の「呼び手が名乗れない」、§8.3の「経路は閉じている」、§9の「解決に失敗する」という現在形の断言です。これらは実体のない防壁を既に閉じたように読ませます。

## §5.3 の数値検算

`a11` の式の第1項は、

\[
\left(1+\frac{q^2}{J-1}\right)^{-(J-2)/2}
\]

へ簡約できます。これと片側t tailを用いて数値的に解いた結果です。

| J | `q_primary(J,0.025)` | `c_B(J,0.025)` | 差 |
|---:|---:|---:|---:|
| 4 | 10.999552321 | 6.231543473 | 4.768008848 |
| 5 | 6.670582267 | 4.851008443 | 1.819573824 |
| 6 | 5.264618682 | 4.219309116 | 1.045309566 |
| 7 | 4.589935667 | 3.862990615 | 0.726945052 |
| 8 | 4.197925514 | 3.635807422 | 0.562118092 |
| 9 | 3.942872072 | 3.478879190 | 0.463992882 |
| 10 | 3.764081508 | 3.364203432 | 0.399878075 |
| 11 | 3.631963535 | 3.276841075 | 0.355122460 |
| 12 | 3.530428656 | 3.208122333 | 0.322306323 |
| 13 | 3.449997402 | 3.152681312 | 0.297316090 |

したがって、**`α₁=α_pub=0.025` なら全 `J=4..13` で主張は正しい**です。草案の端点値も再現します。

ただし一般には成り立ちません。`q_primary` は追補Aで `α₁=0.025` に固定されていますが、`c_B` は追補Pの `α_pub` で変わります。全候補で `q>c_B` とするには概ね

\[
\alpha_{\rm pub}>0.0144150
\]

が必要です。より小さい配分を `p02` が選べば限定は崩れます。

草案は証明途中で「`α₁=α_pub=0.025` のもとで」と書いていますが、§5.3の冒頭・結論とpackageは無条件の事実として書いています。一方、`p02`には `α_pub=0.025` という制約がありません。これは危険な文面欠陥です。ただし§5.2が値の再計算・拒否を禁じており、式そのものは一意なので、現状では誤値・誤受理を直接発生させるblockerではなく下記nitに分類します。

## stress check と追補Pの関係

`u_r=α_pub/r` をcoreに置き、数値 `α_pub` を追補Pで与える構成自体は両立します。`α_pub/r` は手続きの構成、`α_pub` は数値配分だからです。したがって、追補Pの解決後にのみstressを走らせる限り、この前方参照自体は欠陥ではありません。

欠陥は、§5.3がその可変値を事実上 `0.025` と仮定して無条件の結論へ広げていること、およびstressの乱数・縮退仕様が一意でないことです。

## package.md の検算

数値は一致しました。

- `q_primary(13,0.025)=3.449997401748`
- `c_B(13,0.025)=3.152681312170`
- `d=1` の成分primary power `=0.576279948558`
- `L_13=max(0,1−6(1−power))=0`
- `J=4..13` の `L_J` はすべて0
- `J=13` で `L_J≥0.80` に必要な共通standardized effectは `d≈1.56234073`

したがってC-1の `d≈1.5623` と `L_13=0` は正しいです。「親が独立に計算した」という行為自体は文書から検証できませんが、掲載値は独立検算と一致します。

C-4はC-1とは矛盾しません。推奨C-1(a)はsource bytesを変えないからです。しかしC-2の二重予約が未解決で、さらに既知の§7 erratumが草案を無効化するため、現在のC-4承認推奨は成立しません。

## 段4のseed裁定

A5.4を退け、BL-7側を採ってsource digestをseedから外したことは、統計的正当性の観点では過剰裁定でした。

- Aの「seedはprovenanceではなくdomain separator」という説明は正しいです。
- 同じ乱数列を異なる有効規則で用いても、各結果がcore commit/path/blobへ別途束縛される限り、再現性や型I誤りが壊れるわけではありません。
- raw digestを外すことで失ったのは、source core改訂間の**自動的な乱数stream namespace分離**です。
- ただし、これは直ちに誤値を生むものではありません。仕様変更時にliteralのversionを更新する契約があれば足ります。

従って、digest除去自体はblockerではありません。現在の再生成不能の原因はdigest除去ではなく、`domain`と抽出grammarが未定義なことです。

## Nits／非blockerの文面欠陥

- §5.3とpackageの「非整合はprimary fail枝だけ」は `α_pub=0.025` 限定です。`p02`の許容域を固定しないなら結論も条件付きにする必要があります。
- packageの「**本書には数値を書かない**」は事実ではありません。coreは `B=1,000,000`、`δ_MC=0.001`、seed、family root、数値例を固定しています。正しくは「`α_pub`等のspending数値は書かない」です。
- 段4裁定表からA6が脱落しています。草案本文は対応していますが、「全所見を裁定した」という監査参照が不完全です。
- seedからdigestを外したことで、将来core間の自動stream分離は失われました。ただしそれ単独では値・受理集合を変えません。

pytest、build、Monte Carlo simulationは実走していません。SHA-256と式の決定論的数値検算だけを行いました。ファイルは変更していません。

## 総括

**NO-GO — blocker 4 件。**

1. `6×6` 特異性をsimulationだけ非棄却へ写し、少なくとも108セルを恒常的に無力化している。
2. RNG domain・byte grammar・W1/W2結合・cell streamが未定義で、`x_{Jkr}`を一意に再生成できない。
3. 既知の予定erratumで自己無効化し、無効化を利用した同一データ再解析経路も残る。
4. 追補B／追補Pのordinal予約所有が未解決で、許されたbytes境界内にC-4承認経路がない。