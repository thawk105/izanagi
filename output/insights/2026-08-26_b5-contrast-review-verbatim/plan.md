## 追記の全文草案

```markdown
---

## 2026-08-26 追記 — B-5「LLM の因果的必要性」3 アーム同一予算対照の条件付き事前登録

**本追記の性格と効力:** 本追記は、旧 headline、ベースライン 3/4、または backoff hole の休眠を
解除する発火装置ではない。D52 が定めた復活条件が将来成立した場合に限り、何をどの予算・反復・
判定規則で走らせるかを先に拘束する**条件付き事前登録**である。2026-08-26 現在、適格軸は存在せず、
ランダム変異アームの実行入口も存在しないため、本追記だけを根拠に実走してはならない。

本追記は D44 決定 1 の作法に従う制約方向のみの追記であり、観測結果を見てアーム、予算、標本数、
停止条件、変異分布、検定族または成功条件を緩める変更を認めない。発火時に許されるのは、下記の
「発火記録」が要求する軸固有フィールドを埋めることだけである。

### 1. 対象と主張範囲

検証する estimand は、同一の編集面、workload、certification 経路および探索評価予算の下で、
LLM 合成がランダム変異または人間命名の機械 sweep より高い性能の certified variant へ到達する
能力である。主比較は次の 3 アームとする。

1. **LLM:** 固定した model・prompt・射影入力から逐次候補を生成し、直前までの構造化された正しさ・
   性能結果を次の提案入力にする。
2. **random:** §4 の凍結分布から、性能結果に依存せず候補を生成する。
3. **sweep-matched:** §5 の人間命名・事前凍結 grid を、LLM と同じ評価予算まで機械走査する。

これは**軸内探索における必要性**の検定であり、軸発見そのもの、LLM token 費用、wall-clock 効率、
または他の編集面への一般化を直接示さない。軸の起源が LLM 提案である場合はその事実を provenance
へ記録し、「軸発見を含む非 LLM 対照」とは呼ばない。

### 2. 因子、セルおよび反復

性能 workload は、既存の 3 類型を固定して用いる。

- write-heavy: rr5
- balanced: rr50
- read-heavy: rr95
- 共通動作点: RECORDS=1M、THREADS=48、EXTIME=3s、REPS=5
- 1 性能観測値: trace-disabled build による 1 session の reps median

主因子は arm 3 水準 × workload 3 水準であり、**主セルは 9 セル**である。各セルを
**N=12 独立探索系列**で反復する。系列は fresh process・fresh LLM context・独立 seed とし、
系列間で候補、会話履歴または結果を引き継がない。12 系列は時間分離した 3 campaign block × 4
系列に固定し、各 workload×系列番号内で 3 アームの実行順を、事前 commit した seed による均衡
ランダム化で決める。

主実験は計 108 系列、最大 1,080 certification 評価 slot である。共通 stock、floor campaign、
最終 correctness 検証および sweep-ceiling は校正・検証構成であり、第四の主アームとして扱わない。

### 3. 同一予算と全アーム共通の停止条件

主予算単位は**certification 評価 slot 数**とする。1 slot は Tier0
(コンパイル + スモーク) を通過した候補 1 件を certification pipeline へ投入する機会であり、
verifier が anomaly を返して reject された場合も 1 slot を消費する。成功した候補だけを数えて
anomaly を無制限に捨てる運用は禁止する。

各 arm×workload×系列について次を固定する。

- certification 評価予算 **B=10 slot**
- Tier0 前の原提案上限 **A=30 件**。Tier0 不通過は B を消費しないが A を消費する
- 検索系列の administrative wall-clock 上限 **3,600 秒**
- 性能値、順位、有意性または floor 超えを理由とする早期停止は禁止
- 一度 floor 超え候補へ到達しても、B=10 を完走する
- 機械故障 retry は非ゼロ終了、signal、build infrastructure error、runner exception の閉じた
  列挙に限り、同一操作につき 2 回までとする。候補内容または性能値を理由とする retry は禁止する

A=30 または 3,600 秒へ到達しても B=10 を満たせなかった系列は incomplete とする。固定した
12 系列のいずれかが incomplete になった workload は、欠けた系列の差し替えを行わず、
当該 workload の B-5 判定を**判定不能**とする。これを LLM 勝利へ数えてはならない。

bench 実時間は主予算にせず、arm×workload×系列ごとの `total_bench_s` と、検索・floor・検証の
内訳を副次指標として必ず報告する。したがって本設計の「同一予算」は同一の探索評価機会を意味し、
同一の金銭費用、生成時間または総 wall time を意味しない。

### 4. ランダム変異生成器と生成分布

発火記録では、正式 arm の出力を見る前に、pinned source から次の machine-readable な
**typed mutation contract** を凍結する。

- stock fragment の canonical AST
- 順序付き mutable-site 一覧
- 各 site の型、構文上許される非 stock replacement production の完全な有限一覧
- canonical serializer
- source path、line、blob hash、contract hash
- correctness whitelist と、production 一覧の導出手順

production は pinned source と correctness contract から導出し、正式 3 アームの性能値または
LLM 候補を見て追加・削除してはならない。mutable site が 2 個未満、または各 site の非 stock
production を機械固定できない軸は、本対照の発火軸にできない。

候補ごとの変異数を `Kmax=min(4, mutable-site 数)` とし、

`P(K=k) = 2^-k / Σ(j=1..Kmax) 2^-j`

で `K` を引く。K 個の相異なる site を一様・非復元抽出し、各 site では許された非 stock
production を一様抽出する。候補間の抽出は復元抽出とし、重複候補を事後に捨てない。Tier0 を
通過した重複候補は通常どおり B を消費する。

乱数列は、次の識別子を連結した SHA-256 counter stream から rejection sampling で生成し、
剰余による偏りを入れない。

`"b5-random-v1" || activation_commit || workload || series_id || proposal_index`

seed schedule と実装 hash は発火記録に含める。この分布を Tier0 通過率または性能結果を見て
再調整してはならない。

random アームは、原提案数、Tier0 通過数・通過率、Wilson 95% 区間、K 別通過率、重複数、
certification anomaly 数を系列別・workload 別・全体で必ず報告する。A=30 内に B=10 を
満たせない場合は random の敗北ではなく、§3 に従い当該 workload を判定不能とする。

### 5. 機械 sweep の軸命名と sweep-matched / sweep-ceiling

軸命名は正式 LLM アームの出力を見る前に人間が行い、発火記録へ次を凍結する。

- axis ID と一文の意味定義
- 編集面の path、line、blob hash
- 座標名、各座標の意味、level 一覧、Cartesian grid の生成規則
- canonical candidate 表現と grid hash
- 命名者、日時、参照した source・docs・insight・偵察成果物の全一覧
- 各情報源の path、line または record ID、commit/blob hash
- 見た情報と見なかった情報、および軸が LLM 提案に由来するか
- trigger 偵察の完全な既知結果台帳

「見たが命名には使わなかった」資料も省略してはならない。情報源台帳の欠落、formal arm
開始後の座標名・level・grid 変更、または formal LLM 候補を見た後の命名は、当該 B-5 比較を
無効とする。

grid の走査順は各 candidate の canonical 表現について

`SHA256("b5-sweep-v1" || activation_commit || canonical_candidate)`

を計算し、その昇順、hash tie は canonical 表現の byte 順とする。人間による順序変更を認めない。
sweep-matched はこの順に Tier0 候補を走査し、§3 の B=10、A=30、3,600 秒を適用する。

**sweep-ceiling** は同じ凍結 grid の全 unique candidate を同じ順序で最後まで評価する別構成とする。
grid が B 以下なら sweep-matched と sweep-ceiling は同一である。sweep-ceiling は経験的・局所的な
天井の副次記述に限り、同一予算の主比較、Holm 族または B-5 成立判定へ入れない。
sweep-ceiling の結果で sweep-matched の grid、順序または判定を変更してはならない。

### 6. 共通の評価経路と正しさ信号

各 B slot は次の順で処理する。

1. Tier0: コンパイル + スモーク
2. trace-enabled の別 build・別 run による correctness verification
3. anomaly ゼロの候補だけを trace-disabled build で性能計測
4. 結果を構造化し、次 slot の入力状態へ追記

3 アームの性能値はすべて trace-disabled build から取得する。trace-enabled run の timing を
性能値へ混ぜない。verifier が 1 件でも anomaly を返した候補は即 reject とし、性能計測せず、
その slot の score を -100% とする。判定規則または threshold を LLM に有利な方向へ変更しない。

次の一手へ渡す正しさ信号は最低限

`{slot, source_hash, tier0_status, verifier_status, anomaly_class, accepted}`

の固定 schema とする。LLM はこの構造化履歴を受け取る。random と sweep にも同じ state を渡すが、
それぞれの seed schedule / grid schedule は値に応じて分岐してはならない。生 trace、未構造化の
verifier 自然文または filesystem path を次の提案入力にしない。

各系列は、certified 候補の trace-disabled gain
`100 × (candidate_throughput / paired_stock_throughput - 1)` の最大値を系列 score とする。
全候補が reject の場合は系列 score=-100% とする。同値は canonical source hash の昇順で決める。

系列 endpoint となった候補は、別の trace-enabled build/run で **N_verify=8** 独立反復を行う。
1 件でも anomaly が出た場合は endpoint を失格、系列 score=-100% とし、次点候補への差し替えを
行わない。

### 7. floor、検定単位および判定規則

検定単位は slot や within-run reps ではなく、path-dependent な**独立探索系列**とする。

endpoint 固定後、各系列 endpoint と paired stock について、正式検定標本とは別に trace-disabled
**N_floor=8 独立 session**の floor campaign を行う。同じ source が複数系列で endpoint になっても
系列間で floor 標本を共有しない。

workload `w`、baseline `b` ごとに、

`floor_cmp(b,w) = max(3.0%, LLM 12 endpoint、baseline 12 endpoint、対応 stock の between-session CV)`

とする。欠測、非有限値、hash 不一致または floor campaign 未完走は当該比較を判定不能にする。

系列番号ごとの paired difference を

`D_r(b,w) = score_LLM(r,w) - score_b(r,w)`

とする。LLM 優越の検定は、12 個の paired difference の符号を全列挙する片側 exact permutation
test とし、統計量は平均 paired difference、tail tie は包含する。効果量として median difference、
確率優越 `A=P(LLM>baseline)+0.5P(tie)`、各 arm の中央値・CV・Tier0 通過率・anomaly 率を併記する。

一次仮説は 3 workload × 2 baseline の **6 比較**であり、Holm 法、family-wise α=0.05 で補正する。
slot 内候補 10 件は探索過程であり、独立検定として数えない。sweep-ceiling と random-vs-sweep の
比較は記述統計に限り、同族へ追加しない。

workload ごとの「LLM の因果的必要性」は、LLM-vs-random と LLM-vs-sweep-matched の両方が次の
連言を満たした場合に限り成立とする。

1. median paired difference が `floor_cmp(b,w)` を超える
2. 3 campaign block の各々で paired difference の中央値が正
3. exact permutation test が Holm 補正後に有意
4. endpoint correctness verification が全件完了し、比較入力に anomaly 未処理がない

一方、`|median paired difference| <= floor_cmp(b,w)` なら、既存失敗条件 (c) の
「同等に再現」を成立とする。baseline が LLM を `floor_cmp` 超で上回る場合は、LLM 固有価値なしの
より強い negative とする。LLM 差が floor 超でも、block 再現または補正後有意性を満たさない場合は
判定不能とし、優越性検定の非有意を同等性の証拠へ読み替えない。

1 workload だけ連言を満たした場合は、その workload に限定した主張だけを許す。「試験した
3 workload 全体で LLM が必要」と述べるには 6 比較すべての成立を要する。勝った workload だけを
選択報告せず、全 9 セル、全 incomplete、全 anomaly、全 floor と sweep-ceiling を報告する。

N=12 は exact sign permutation の最小片側 p が 1/4096 となり Holm 初段 0.05/6 を下回るための
p 値解像度を持つが、未知の効果量に対する 80% power を保証するものではない。完走後の効果量を
理由に N を追加してはならない。

### 8. 休眠解除の操作的条件

次の全条件が揃うまで、ベースライン 3/4 と旧 headline は休眠のままとする。

1. **軸適格性:** 単一スカラー探索へ還元できず、code-fragment の構文選択を含み、完全列挙器を
   持たない軸が pinned commit 上に実体化している。機械 grid は全 admissible code space の有限な
   部分射影であることを明記する。
2. **偵察観測:** 正式 3 アームとは別の preliminary 偵察で、fresh target-specific floor を超える
   certified 候補が、時間分離した 2 campaign block の双方で同方向に再現している。性能は
   trace-disabled、correctness は別 run で anomaly ゼロでなければならない。
3. **実行可能性:** random generator、sweep driver、共通 certification consumer、予算台帳、
   schedule 照合および report consumer が実在し、3 アームで同じ B/A/停止条件を強制できる。
4. **日付付き発火記録:** formal データ取得前に、axis ID、source pin、typed mutation contract、
   random seed schedule、sweep grid/order、命名情報源台帳、LLM model/prompt/context hash、
   floor protocol、実行 schedule を commit する。本追記の B、A、N、検定族または判定規則は
   変更しない。
5. **人間承認:** 上記発火記録と、「その軸が D52 の非列挙 code-fragment 軸に該当する」という判断を
   ユーザーが承認する。

偵察は軸選定に用いた結果既知情報なので、formal 3 アームを純粋な confirmatory study と呼ばず、
「結果既知の trigger を受けた事前登録付き比較」と限定する。発火記録が不足したまま取得した結果は
exploratory として隔離し、B-5 の証拠に数えない。

2026-08-26 時点では条件 1〜5 は成立していない。したがって、本追記は休眠を解除しない。
```

## 挿入位置

[docs/phase3-main-experiment.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-llm-necessity-contrast/docs/phase3-main-experiment.md:386) の現行末尾、すなわち line 386 の後ろへ追加する。空行と区切り線を入れた場合、新見出しは概ね line 390 になる。

ここが適切なのは、既存の時系列追記を改変せず、2026-07-16 の最終判定までを保存したうえで、2026-08-26 時点の条件付き規約を追加できるためである。特に D52 の休眠宣言（現行 lines 159–173）を上書きせず、末尾から明示的に参照できる。

## 設計論証

予算単位には「評価回数」を採用した。ただし「成功して certified になった候補だけ」を数えると、Tier0 不合格や verifier anomaly を無料で何件でも捨てられる。そこで単位を「Tier0 通過後に certification へ投入した slot」と厳密化し、anomaly も B を消費させた。Tier0 前にも A=30 の共通上限を置き、random の不成立を案山子として LLM 勝利へ数えず、比較全体を判定不能へ倒す。

この同一予算が意味するのは、同じ数の高価な評価機会を与えたときの探索誘導能力である。LLM API 時間、token 費用、候補生成時間まで同一にはしない。したがって「LLM の方が安い・速い」は導けず、bench 実時間も副次報告に留める。

B=10 は D39 の iteration budget を継承する。N=12 は P2-5 の系列数を継承し、6 仮説の Holm 初段 `0.05/6` に対して exact sign permutation の最小 p=`1/4096` が十分小さい。一方、効果量不明なので power 80% は主張せず、観測後の N 追加も禁止した。

random は sweep grid の一様抽出にしなかった。D46 が指摘したとおり、それでは機械列挙の劣化版にしかならない。typed AST の複数 site 変異とし、構文的に妥当な分布、seed、変異数分布を事前固定した。Tier0 通過率を独立の必須報告にすることで、生成器の質も隠さない。

sweep-matched は B=10 の同一予算対抗馬であり、sweep-ceiling は凍結 grid 全走の副次的経験天井である。hash 順を採用したのは、人間が「matched に入る 10 点」だけを既知結果に合わせて並べ替える自由度を除くためである。

9 セル、12 系列、検定単位=系列としたのは、slot が逐次履歴に依存して独立でないためである。workload ごとに LLM が random と sweep の双方へ勝つことを連言条件とし、片方だけに勝った結果を「非 LLM では到達不能」と過大解釈できないようにした。

発火条件は D52 の「非列挙 code-fragment 軸の実体化 + floor 超地形」を、2 block 再現、実行入口の実在、日付付き binding、ユーザー承認まで具体化した。現時点の文書追記だけでは発火しない。

## 親の provisional 裁定への応答

- **(P1) 条件付き賛成。** 評価回数は探索誘導の因果比較に最も直接的で、latency と分離できる。ただし「certified 成功だけを 1 単位」とすると reject の無料廃棄が可能になるため、「Tier0 通過後の certification 評価 slot。anomaly も消費」と修正すべきである。Tier0 前にも A=30 を置く。bench 実時間は副次併記でよい。

- **(P2) 賛成。** B=10、A=30、3,600 秒を全アーム共通にし、性能早期停止を禁止する。資源上限到達、機械故障、anomaly reject は性能に基づく停止ではないが、不完走を勝敗へ倒さず判定不能にする必要がある。

- **(P3) 条件付き賛成。** 現存軸を無理に選ばず、軸非依存の骨子にするのが D52 と整合する。ただし発火時の裁量を残さないため、typed mutation contract、grid、命名情報源、model/prompt、floor、schedule を閉じた発火記録へ束縛し、ユーザー承認前は休眠を維持すべきである。

## ユーザー再裁定へ返すべき事項

- 将来現れた具体軸が、D52 の「非列挙 code-fragment 軸」に本当に該当するか。
- その軸の preliminary floor 超観測を受け、旧 headline と対照 3/4 を実際に発火させるか。
- 発火記録に束縛された具体的な軸、編集面、命名情報源および既知結果台帳を承認するか。
- 将来の実装・実走を認可するか。現 wave の docs-only 権限には含まれない。
- B=10、N=12、A=30 が費用上受け入れられず緩和が必要になった場合の再設計。観測後に子判断で縮小してはならない。

D52 の休眠または trigger-gating の (c') 事前自認を覆す新事実は、今回の射影内にはない。

## 総括

B-5 を 3 arm × 3 workload × 12 系列、各系列 B=10 の条件付き事前登録として起草した。  
評価回数予算の抜け穴を、anomaly の slot 消費、原提案 A=30、未充足時の判定不能で閉じた。  
random の typed-AST 分布、sweep の命名 provenance、Holm 族 6 と workload 別連言判定を固定した。  
最大の弱点は、適格な非列挙軸も random 実行入口もまだ存在せず、総実走量も大きいことである。  
したがって追記は休眠を解除せず、具体軸の選定と発火は将来のユーザー再裁定に残る。