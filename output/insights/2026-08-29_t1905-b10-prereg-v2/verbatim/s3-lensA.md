参照略号: `B`=brief、`P`=plan、`J`=probe JSON、`PR`=probe README、`Doc`=現行事前登録文書。検査・式の再導出だけを行い、書き込みと pytest は行っていない。

## R1 と事後選択

- `refuted` — binary の平均式に計算違いはない: 高い arm の頻度を `p` とすれば `C=μ/2+Bμ` なので `E[C]=μ/2+pμ=μ+μ(p−1/2)` であり、`B:42-43` は正しい。影響: この式は選択台帳と報告にそのまま使える。
- `real` — symmetric-modulo は厳密な p 不変ではない: `C=r+B(2μ−2r)`、`m=E[r]` とすると、`Cov(B,r)=0` の仮定下で `E[C]−μ=(1−2p)(m−μ)=−2(p−1/2)(m−μ)` となり、p だけについて見れば一次である。一般にはさらに `−2Cov(B,r)` が残るため、`B:44-48` の「一次で不変」「二次項だけ」は過大で、`P:264-265` の訂正が正しい。影響: R1 と報告は独立性仮定、積としての二次性、実測保証ではないことを明記する必要がある。
- `real` — 現在の R1 文言は自立した判定基準として不足する: `P:49` の識別文字列は hard-code した形集合の説明であって、式から可否を再現できる規則ではない。文言案は「`B` を branch bit、`p=E[B]`、`m` を補助 draw の平均とし、事前に明記した期待値モデルで `g(p,m)=E[C]−μ` を記号導出する。`g(p,μ)=0` が全 p で成り立ち、`aμ(p−1/2), a≠0` という抑制されない項を持たない形だけを形単位で登録する。仮定と covariance 項を明記し、実測値は参照しない。物理残差は別の R3 で全 cell を判定する」である。影響: spec、選択結果、台帳の R1 をこの程度まで機械的に再現可能にする必要がある。
- `refuted` — 上の一般形に直せば R1 は論理上 `binary` だけの名指しではない: constant、平均ゼロの連続変数 `Z` を使う `C=μ+Z`、2 命令の和を常に `2μ` にする antithetic pair は満たし、平均が `μ/2` と `3μ/2` の連続分布二群を biased bit で混ぜる形は binary でなくても `μ(p−1/2)` を持って落ちる。影響: 文書にこの正例・負例を載せれば R1 の一般的射程を認証できるが、現 wave の選択履歴が事後的だった事実は消えない。
- `real` — R1 の適用は outcome-informed である: `B:39-48` は失敗値の開示後に binary を除外し、`B:70-72` と `P:252,284` も R1 が probe 後に定式化されたと認めているため、「式だけで適用できる」と「結果を見ずに規則を選んだ」は別である。影響: binary 除外を元の事前登録、または outcome-independent な操作チェック選択として認証してはならず、「probe-informed amendment、throughput 観測前固定」と台帳に記録すべきである。

## 開示、発効、probe 束縛

- `real` — §4 案は D1137 と同じ厳格さにまだ達していない: D1137 は規則を対象結果より前に固定し、後の結果を corroboration としたが、ここでは規則自体が後発である。それにもかかわらず `B:48` の「18 個の数値は追認であって選択根拠ではない」と `P:49-55` の `formula-only-not-observed-deviation` は因果履歴を弱く見せる。影響: 文書と台帳は「観測済み事実: binary 4 cell failureを見た」「事後改訂: それを契機に R1 と 2-shape grid を選んだ」「前向き固定: shape throughput 未観測の時点で v4 の全規則を固定した」の順で書く必要がある。
- `real` — 12 値の転記は、計画どおりでは由来の束縛が不足する: `J:2-5` は `/v1`、source commit、patch/formula SHA を持ち、`PR:12-19` は placeholder commit、result SHA、calls、clock を持つ一方、`P:287-315` の v4 spec 案は値と patch/formula しか明記していない。patch/formula 一致だけでは source、probe harness、compile identity、元 artifact bytes を認証しない。影響: `physical_residual.provenance` に元の `/v1`、18-cell、両 commit、result SHA、calls、clock、compile identity、抽出規則を固定し、raw `/v1` を新しい 12-cell `/v2` probe と呼ばないことが必要である。
- `refuted` — 18-cell probe が 12-cell grid を覆えないという問題はない: `J:35-305` は retained 2 形×6 μ を完全に含み、`P:304-315` の転記値も一致するため、「形名が v4 grid に属する全行を抽出」という結果非依存の写像を固定すれば、登録 12 cell の合成-loop manipulation check としては十分である。影響: 再走は論理上必須ではないが、これは formal workload 中の分布や残差を認証せず、事後的 grid 改訂も正当化しない。
- `real` — 現行 §0 の「placeholder commit→probe→値だけ転記→発効」と v4 の実履歴は同じではない: 今回は probe 後に shape 集合、schema、Holm family、run order、R1 を変更するため、`Doc:12-17` の単純な第3段ではなく amendment である。影響: 「v1 probe-informed amended v4、将来の throughput に対してのみ発効」と履歴を改稿すれば発効版と呼べるが、元の blind manipulation-check preregistration が発効したとは書けない。

## 2 水準化と A-2

- `real` — constant 対 symmetric-modulo の一 contrast だけでは B-10 の「待ち方と待ち量の直交切り分け」を一般に閉じられない: `Doc:66-68` は待ち方全般へ広すぎる。§3 文言案は「登録 grid で constant と symmetric-modulo という特定実装の一 contrast/workload を、名目 μ 一致かつ合成-loop残差1%未満の条件で検定する。有意差はこの contrast に限り、variance 全般、dose-response、binary、厳密な直交性へ一般化しない」である。影響: タイトル、認証結果、formal report の headline をこの局所主張へ狭める必要がある。
- `real` — §9 の追加予定は最低限より不足する: `P:339-340` の binary と dose-response に加え、「B-10 の一般的な直交切り分け」「formal-run 中の実要求・実待機平均の shape 間一致」「乱数計算や mixer overhead からの分離」「outcome-uninformed な独立 replication」を未取得として追加すべきである。影響: 残課題台帳が 2-shape 結果を完全な機序分離と誤認させなくなる。
- `refuted` — A-2 の数値が μ grid や判定規則を実際に動かした証拠は brief/plan 内にない: `B:50-53` は全規則据え置き、`P:282-285` も A-2 を変更根拠にしないと明記し、R1 の式にも A-2 の値は入っていない。影響: spec 変更は不要だが、最終報告は A-2 由来の期待効果や閾値を主張してはならない。
- `refuted` — A-2 を開示しつつ tuning に使わないことは不誠実ではない: 異なる source/protocol の既知の強い reject は、過去の肯定的 backoff 材料と併記して prior evidence、研究動機、解釈上の制約を明らかにする意味がある。影響: 台帳に `role=motivation-and-prior-evidence; not parameter-selection` と固定し、B-10 の定量予測へ転用しないのが妥当である。

## 代替案

- `real` — 折り返し binary は、元の B-10 主張を守る目的では親案より科学的に優れる: 独立な bit 頻度を p,q とし、二 bit が等しいとき高 arm にすれば `P(high)=1/2+2(p−1/2)(q−1/2)`、従って `E[C]=μ+2μ(p−1/2)(q−1/2)` となり一次の偏りを積へ落とせる。ただし covariance、時間相関、追加 mixer cost の検査が必要で、formula/patch SHA を変更して結果を見る前に新 placeholder を凍結し、probe を再走しなければならない。影響: 元の3水準 ladderを優先するならこの案を推奨し、D1098 に従って旧 formula の消費者を別名で凍結し、新 identity の発効は新 probe 後まで保留する。
- `refuted` — 現 binary を同じ formal grid の「記述専用 arm」にする案は親案より良くない: 4 cell が 1% gate を超えており、同じ成果物へ残せば実質的な cell exemption になるうえ、平均交絡を持つ記述値は shape 効果の補助証拠にもできない。影響: 実施するなら別 campaign・別 run order・完全に exploratory な成果物とし、認証結果、Holm family、formal report から隔離する必要がある。
- `refuted` — 合成-loop probe を本走中の測定だけに置き換える案も優れない: 実要求値や物理待機の記録には trace または計測コードが必要で、`Doc:526-531` の trace-disabled performance と trace-enabled correctness の分離により、測った binary と性能 binary の同一性を失う。影響: synthetic preflight は維持し、formal workload の分布診断は別 trace run の scope外裁定パッケージ候補にするのが妥当である。

## brief の算術と事実関係

- `refuted` — 「公平 bit なら100,000回で SE 0.158%、4.35% は約27σ」の算術自体は正しい: binary の SD は `μ/2` なので相対 SE は `1/(2√100000)=0.00158114=0.158114%`、`4.3503067/0.158114=27.51` である。影響: 算術値は報告に残せる。
- `real` — ただし 27σ を物理残差の検定値として扱うのは過大である: `J` は bit count や実際の commanded sample mean を記録せず、4.3503% には loop overhead、runtime noise、bit の非独立性が含まれる。constantとの差でも `J:315-318` の3.76745%であり、Bernoulli SEだけで標準化した統計量ではない。影響: 報告では idealized sanity check とだけ呼び、「calls を増やしても直らない」の決定的証拠にはしない。
- `real` — brief の「12 対 / 3 族」は誤りで、plan が正しい: 各 family は6 μ×3 blocks=18 paired effects、非constant形1×workload3=3 Holm familiesであり、12 は physical residual cell 数である (`Doc:306-312`, `P:319-325`)。影響: §6、decision procedure、report は「18対 / 3族」、residual table だけ「12 cell」とする。
- `real` — `B:82-84` の「probe が odd mixer の premise を反証した」は事実を言い過ぎている: odd multiplication が全64-bit domain上の全単射で、uniformな全域なら上位 bit が半々という数学は反証されていない。反証されたのは有限で非uniformな runtime start 列にその均衡を転用して物理平均一致を保証できるという運用上の推論であり、probe は bit count も持たない。影響: D1057 supersede 台帳は「bijection theorem の反証」ではなく「finite sampled sequence の半々性と独立性を保証しないため、実験設計の根拠として無効」と記録する。
- `refuted` — P2/P4 の他の派生算術は整合する: 2形×6 μ=12 residual cells、3 references+12=15 points/block、3 workloads×1 contrast=3 familiesで、受理集合変更に伴う schema v4 化も妥当である (`P:19-25,58-66`)。影響: これらの driver/report 数は維持してよい。

## 総括

`real` 所見は11件。最重要3件は、第一に binary 除外が probe-informed な事後改訂であり「追認」とは呼べないこと、第二に2水準では B-10 の一般的な直交切り分けを閉じられないこと、第三に既存 `/v1` probe から12値を移す provenance chain が計画上まだ不十分なことである。

親案はそのままでは採用不可である。目的を「将来の throughput に対する、probe-informed な2-shape amended preregistration」に限定し、R1、開示順序、probe provenance、§3、§9、18対/3族、D1057 の記録を上記どおり直せば条件付きで採用できる。元の3水準による待ち方と待ち量の切り分けを維持することが目的なら、折り返し binary を新 identity で凍結して新 probe を行う案の方が優れる。