# Izanagi 本体論文：限界節草稿 (2026-09-21 版)

本稿は 2026-09-21 の執筆依頼 (B-8 の 3 値判定 `pass` の反映) に基づく日本語草稿である。2026-09-20 の前稿
(`output/insights/2026-09-20/paper-intro-ja/limitations.md`、worklog entry 1757) を置き換え、前稿は 1 byte も変えずに残す。前稿は
[序論草稿](../../2026-09-20/paper-intro-ja/intro.md) と [貢献節草稿](../../2026-09-20/paper-intro-ja/contributions.md) と同時に起草され、
主張の強さを揃えてある (2 稿は 2026-09-20 版のまま)。この節が扱うのは**論文全体の
適用範囲と、未実証のまま残る主張**である。個々の実験の留保 (各 attempt の限定、成果物に無い情報、
欠測の内訳、図の用法) は [結果・考察草稿 (2026-09-21b 版)](../paper-results-ja-b/results-discussion.md) と
各結果稿の側に残し、ここでは繰り返さない。前稿の採用時点は local main `482f19b88` (2026-09-20 17:56 JST の commit)
で、本稿の採用時点は local main `d99c556df` (2026-09-21 13:35 JST、worklog entry 1795 までの fold を含む) である。
前稿の本文を継承し、B-8 の検証の結果 (§2 の末段、§7、出所 8) と、前稿の採用時点より後に着地して前稿の記述を偽にした状態語
— A-1 の独立再現 attempt-0002 の完走 (§1、出所 3)、凍結 v2 g1 の起動検査が拒否される段階の変化 (§5、出所 20) — を現在地へ揃えた。
あわせて、前稿の執筆時点で既に偽だった 1 か所 (§3 の「『非列挙』の定義の置き直しは未裁定」。2026-09-02 に裁定済みで、論文ストーリー
2026-09-20b 版が同じ誤りを自分の前版の訂正 1 としている) を直した (出所 11)。B-8 の記述は B-8 の単独稿
(`docs/paper-story/results/2026-09-21-b8-final-candidate-longrun-verify.md`) §3.3 / §4 と `docs/paper-story/README.md` の stale 注記 3 に
揃えた。証拠ごとの現在地の一覧は本稿の本文には置かず、同じディレクトリの [README](README.md) に別表として置く。既存の凍結稿・
図は書き換えていない。本文中の資料番号は末尾の出所を指す。

性能と正しさは節を分けてある。1 文に畳むと、同じ workload・同じ protocol で正しさも性能も確認済みだと
読まれるためである。

## 1. 測定契約の限界

本論文が報告する静的 backoff の利得 (write-heavy +38.3%、balanced +11.3%、read-heavy −6.6%) は、旧
`linux-baremetal` 環境の trace 無効 build の sweep における**記述的な結果**であり、現在の測定契約
(比べる構成を同じ campaign の中で対にして測る) より前に取られた。分母は同一 sweep 内の無 backoff 対照で
あって stock の適応 backoff ではなく、有意差判定も区間推定も持たない。この測定が旧契約の下で行われた
という事実は、後から何を測っても変わらない。[1]

現行 Pegasus 環境で採用静的 backoff を測った正式な走行は 3 つあり、いずれも同じ campaign の中で
stock と対にして測った。write-heavy と balanced の連言で `observed-positive` (median 比 +63.5485% /
+14.4213%)、read-heavy で `reject` (−5.7841%)、balanced の別の事前登録による対で `accepted`
(+11.2254%)。これらは事前登録した判定式の出力であって研究の成功宣告でも失敗宣告でもなく、信頼区間も
有意差判定も持たない。3 つは独立した protocol であり 1 つの横断実験ではない。符号が旧環境の 3 値と
3 workload とも一致したことは記述的な照合であって再現判定ではなく、旧値と新値を pool しない —
環境も CCBench の版も測定契約も推定対象も違う。「現行環境の正式な同一 campaign 対はゼロ」という
逆向きの過小主張も誤りである。[2]

現行契約が定める配置と推定対象 (均衡 5-rep ブロック交互、対差平均、検出力から導いた n = 30 と登録済み
区間推定) による測定では、非認証の attempt が 2 本完走した — 1 本目と、1 attempt に限って認可され
認可記録を照合する投入経路で投入された独立再現の 2 本目である。どちらも登録済み解析による記述的な観測値
(3 workload とも「区間が床の外」、対差平均の符号は + / + / −) を得た (2 本目では write-heavy と read-heavy で
標本標準偏差が計画値を超えたが、分類は変わらない)。ただし、これらをこの測定契約の正式な結果や
要件充足とは扱わない — その lane は昇格を禁じられている。2 本は同一配置の反復で分類と符号が一致した観察で
あり、プールした推定量も再現の判定も作らない。formal な lane での充足はユーザー手番で判定されて
いない。[3]

論文採用値には、計算機を別に起動し直して取り直した証拠が無い。Pegasus で取った結果はこの充足に
ならず (別の起動と別の環境が同時に変わる)、2 度の投入はいずれも測定前に止まった。[4]

同一候補 (fixed 5 µs) を 3 workload で同時期に測り、各 workload の同 campaign 内 stock 対照との対差を
走行間ばらつきの下限と比べた descriptive な走行では、read-heavy だけが下限を超える退行 (−11.3787%、
下限 0.2228%) で、write-heavy (+67.8968%) と balanced (+12.6717%) は退行なしだった。「全 workload の
退行込み報告」という報告要件はこの走行と図によって、**単一 attempt・descriptive・非認証・反復間の
安定性は未判定**という限定付きで満たしたと裁定された。「退行なし」は優越の判定ではなく、反復
attempt・certified への昇格・有意差判定は含まない。利得側だけを引用することはしない — 旧 3 値の
read-heavy −6.6%、正式 protocol の `reject`、fixed 5 µs の read-heavy の退行のいずれも落とさない。[5]

## 2. 正しさの保証範囲

判定器が担保するのは、YCSB の point read / write に限った、**観測できた trace 上の**直列化可能性で
ある。述語・phantom・公平性・starvation・観測されなかった実行は対象外である。「正しさゲートを一度も
緩めなかった」は工程上の事実であって証明ではない。certified は実際に build された bytes についての
判定であり、要求した構成が build されたことを含意しない — それを言えるようにしたのは正しさの緑では
なく、source を identity に束縛する仕組みの側である。判定器の書き込み隔離は道具の権限による隔離では
なく、専用書き込みツールの除去・prompt 規律・入力側の性能数値隔離の組み合わせである。trace を
有効にすると commit 数が約 44% 減るため、検証走行が踏む競合の強さは性能測定時の約 56% 相当と
解釈されている。[6]

採用静的 backoff は、性能を測った workload そのもので certified である (write-heavy / balanced の
4 cell と read-heavy の 2 cell、いずれも trace 有効の別走行)。これは性能の認証ではなく、限定が 5 つ
残る — (i) 保証範囲は上のとおり point-key trace に限る、(ii) 正しさ側の実行引数は独立に記録されて
おらず workload の束縛は campaign の設定による、(iii) artifact hash 単独では compile-out の証明に
ならない、(iv) 測定条件の関門について残るのは admission の記録と ID まで、(v) source identity の一致は
実翻訳単位全体の意味の一致を保証しない (前処理指令の効果が identity に乗らない範囲は修正で狭まったが
限界は残り、既存の判定は修正前の identity 層の下のものとして残る)。この certification は旧環境の 3 値へは
遡らない — 旧 3 値の正しさは今も「backoff は正しさに影響しない」という機序論証による外挿である。[7]

採用候補 2 genome (fixed 5 / fixed 10 µs) の各候補について、本走 24 件 (trace 有効 build の独立 8 反復 ×
3 workload) と校正で完走した 6 件を合わせた判定集合 30 件では anomaly は 0 件だった。校正 10 秒の
未完走 2 件 / 候補は verdict を持たず、この集合に含まれない。これは操作的な事実であって確率主張では
なく (「信頼度 1−εⁿ」とは書かない)、性能値を含まず、既存の certification と性能判定を昇格も降格もし
ない。「種を変えた長時間実行による最終候補の検証」(B-8) という別の要件の充足でもない — 検証相は対象
(最終候補ではなく採用静的 backoff) と長さ (extime 3 s) が要件と違う。[8]

B-8 そのものは、合成した軸 (abort 要因別の gate) の最終候補 (案 A = 系側 gate 構成) を対象とする別の事前登録で
検証された。事前登録は発効し、その規則の下で、独立 8 反復 × 3 workload の本走 24 件 (規則が校正から機械的に決めた
extime 10 s の trace 有効 build) と校正で完走した 6 件を合わせた判定集合 30 枠のすべてで anomaly は 0 件、runner の
3 値判定は `pass` だった。これも上と同じ保証範囲の中の操作的事実であり、`pass` は規則の機械適用の出力であって
研究の成功宣告ではない (「証明」「信頼度」とは書かない)。「種を変えた」は独立 process の自己シードという操作的定義で、
seed 値は記録しておらず、乱数列の独立性は検証していない。「長時間」は extime 10 s という操作的定義で、長さ・反復数の
検出力は主張しない。性能値を含まず、identity は現行の素材コーパスの版と patch に束縛され、合成軸の性能判定 (§3 の
B-1 の不成立) を変えない。検証相とは対象が違うので比較しない。1 回の cohort の結果であり、別の日・別の計算ノード
集合での再現は取っていない。[8]

mocc については同じ強さの検出力の実証が無い。stock mocc の G2 signal は trace の witness を切った
producer でだけ再現し、witness を入れた条件では 0 件だったが、片側 Fisher は非有意で、原因が実装の
性質か trace hook の側かは分かれていない。0 件は不在の証明ではなく、非有意は同等性の証明ではない。
追加実験は費用対効果を理由に見送られ、上流向けには観測事実と限界の報告までとする。[9]

## 3. 合成能力についての限界

**既知軸最良を超えるという主張 (B-1) は測って不成立だった。** 合成した軸は既知軸の一部 (書込ロック順の
並べ替え) には 3 workload とも勝ったが、コンパイル時フラグ最適化と静的 backoff 最良値には負け、9 対の
家族連言 (family p = 1.0) を満たさなかった。これは新しい否定的発見ではなく、結果既知の追試として
登録した複合主張の失敗報告である。合成軸の on/off 効果は登録追試として成立したが headline の救済に
ならず、適格率次元の発見再現性は未実証のままである。現行環境の走行 (正式 3 走行、非認証 lane、同一
候補の同時期測定) はいずれも採用静的 backoff と無 backoff の比較であって、合成軸と既知軸最良の比較では
ない。B-1 は新しい軸か既知軸を組み合わせた構成でしか埋まらず、新しい軸の側には次の壁がある。[10]

**「非列挙のコード片軸」は現行の編集面では実体化できない。** C++ の観測はすべて有限幅なので、入力空間が
有限ならそこから boolean を返す述語の集合も有限になる (有限幅の壁)。述語空間を広げようとして編集面から
見える量を増やすと、候補は禁止された代理指標 (大域の進捗時計、run 自身の fitness 信号、ワーカー識別、
トランザクション種別による公平性の犠牲) になる (代理の壁)。空間の広さと reward hack の遮断が正面から
衝突する。この衝突に対し、「非列挙」は固定予算の下で操作的に列挙し尽くせないことへ定義し直された
(2026-09-02 の裁定)。ただし裁定済みであることは、壁が解けたことでも軸が復活したことでもない — その定義の下で
実体化を再試行した走行は無く、コード片軸は休眠のままで、二重の壁 (有限幅・代理) の実測結果は変わらない。[11]

**ワークロード特化の合成ができたとは書けない (B-2)。** workload descriptor を条件にした生成の因果証拠
(on / off、必要なら入替えの対照) が無い。selector 実験・dry-run・既知 workload の pilot・非認証の登録経路で
走らせた対照は、この証拠に数えないと設計文書自身が宣言している。[12]

**LLM でなければ到達できないとも書けない (B-5)。** この形の必要性は対照を取っても言えないと裁定されて
おり、主張は固定予算・固定編集面の下での条件付き優越へ狭まっている。その対照 (合成ループ / ランダム
変異 / 機械 sweep を同一評価数で比べる) の事前登録は作られ、部品の段階実装と上限付きの試走が認可されたが、
本走は未認可で、対照は未取得である。[13]

**出力を「新しい CC」とは書かない。** 出力契約は certified な選択結果であり、証拠が支持しなければ stock
または「差なし」を返す。合成ループは、pin 前進前の CCBench `511c9538` の下で certified の終端判定へ
4 度到達したが、評価したのは固定 backoff の初期値 (20 / 25 / 10 µs) であって新しい CC 構造ではなく、3 走は非同時刻で
改善・退行の根拠にならない。批評役の診断が次の生成の型付き入力へ届いたことと「効いた」ことは別で
あり、同じ job 内の stock 対照は本稿の時点では取れていない。[14]

## 4. 探索の否定的結果の射程と、機序説明の帯域

LLM 誘導探索が自明な空間で貪欲探索を超えず、欺瞞的な構造で有害だったという結果は、3 workload のうち
2 つについてのものである。read-heavy は到達判定が情報を持たない構成であり、一般化には使えない。主指標は
tie を半加算する確率優越へ再校正済みで、旧指標の読みは否定的結果を実態より強く見せる方向だった。誘導と
random の比較は未到達試行の扱いに依存するため、単体では headline にしない。この結果は有限フラグ空間に
ついてのものであり、LLM によるコード生成一般が無益だとは推論できない。[15]

backoff の機序について閉じているのは 0〜10 µs の帯だけである。この帯では abort が約 4 割減り (0.815 →
0.494、「半減」とは書かない)、有用 IPC はほぼ一定で、total IPC の低下は純粋な spin 希釈だった。25〜100 µs
の過抑制域では有用 IPC 自体が下がり、stock の適応 backoff が駐車する約 560 µs 点は外挿である。abort 率の
単一冪則や代数減衰を確定主張として書かず、spin 割合の単発値 (87.3%) を代表値として引用しない。「約
560 µs への駐車」と格子刻みによる到達不能性は、CCBench 既定の 3 定数についての事実であって適応 backoff
という機構一般の性質ではない。既定 adaptive と調整済み adaptive の差は別の論文の主題であり、本論文は
数値と図を共有しない。[16]

右 tail (1000〜9999 µs) について言えるのは、事前登録の固定表現「この事前登録の述語では、表現可能域で
ある 9999 マイクロ秒までに飽和を観測しなかった」までである。同じ格子では、1250 から 9999 µs への増加に
伴い、throughput は 3 workload とも半分以下へ低下した (過抑制の費用)。9999 µs は符号化の上限であって
物理的な限界ではなく、右側は測れない。主結果の cohort 1 を保持し、独立再現の第 2 cohort は併記する
だけで合成せず、統合判定・プール推定・cohort をまたぐ有意水準を作らない。「飽和しない」「再現されたので
飽和しない」「機序を説明した」「この項目を閉じた」とは書かない — 機序は同定していない。待ち方の比較
(`constant` 対 `symmetric-modulo`) は 3 族とも Holm で `different` だったが、判定が及ぶのはその 1 つの
対比だけである。[17]

## 5. 機構の成立と、測りたい量が測れたことの区別

本論文が報告する機構 — 軸提案のループ内化、iteration 間をセッションを跨がずに運ぶ駆動、双射検査を
持つ材料レポート、機序仮説層 — は**いずれも運用上の証拠であって科学的主張の証拠ではない**。4 つは
成立しているが、一続きの「提案 → 無人の build / bench → 材料レポート」として実走した事実は無い。[18]

- 軸提案のループ内化は観測が n = 1 で、人間の承認 gate を挟む経路である。合成ループの 3 巡でも一般化しない。
- **無人で研究ループが回るとは書けない (B-3)。** 駆動は bounded MVP であり、軸は 1 つに固定され軸提案役を
  呼ばない。live pilot は実機で検証を越え性能測定まで到達した (到達点を過小にも書かない) が、正式系列は
  未発効である。止めている最上流は権限の不在である — 受領証の外部署名主体の実効層はいずれも計算環境の
  管理権限を要し、ユーザーがそれを持たないため当面設置しない。受領証の署名鍵はユーザーが配置したが、
  置き場所の所有者は AI の実行主体と同一である。閉じられない理由が権限の不在であることまで書く。
- 材料レポートの双射検査は生成時の検査であり、対象とした campaign 群についてだけ成立を確認できる。値の
  改変に対する深い一致検査は本体側で「実施しない」と裁定済みである。機序仮説層が出した材料は
  非 certifying の二次的な view であり、機序の証拠ではない。

**構造化された正しさシグナルの還流が次の合成を改善する、とは書けない (B-4)。** 実走しているのは「赤 →
構造化 → 批評役が形状別に方向を返す」までで、還流の改善効果は未実証である。その ablation は推定対象を
詳細 anomaly の増分効果へ狭め、記述統計へ限定したうえで、適格な赤 precursor が 0 件で実施不可のままで
ある。床値側の測定は準備と進行の段階であり、それは ablation でも床値の採用でもない。[19]

**床値についての区別。** 8b holdout の official 経路の床値 campaign は完走し、floor 案 (rr20 = 35,817.945、
rr80 = 46,065.78 tps) を出したが、両 holdout とも配線下限 0.03 × stock 中央値で決まった — 「この 1 走行では
実測 noise 項が配線下限を下回り、床値案は stock 中央値の 3% となった」と書き、「noise が 3% だった」「判定
下限を較正した」とは書かない。この案は世代 g1 の床として採用され、本稿の時点で発効した。ただしその批准は
記録済みの委任裁定の下で AI が作った record によるものであり、「科学的に十分な床」の主張は含まない。
発効時に oracle 走行の起動検査を拒否させていた既存の不整合 2 件は後に整合されたが、起動検査は素材コーパスの
版の前進後、binary admission policy の不一致で拒否されたままで、descriptor を条件にした合成の oracle 実走
(B-2) には至っていない。一方で「床値がまったく取れていない」も誤りである — 旧環境の走行間ばらつき、旧
主実験の floor campaign、新 protocol の pilot 値、現行 Pegasus の走行間ばらつきの下限 (cold-boot と温度
ドリフトを含まない、rr5 0.9536% / rr50 0.7250% / rr95 0.2228%) は取得済みであり、これらと floor 案と
B-4 の床値は別の量で、1 語の「床値」で書かない。「凍結床値を超えた」という語り口は使わない。[20]

hooks を「実装済みの機械防壁」とは書かない。語れるのは否定的結果込みの防壁設計事例と最小の第二防壁
までであり、repo 内の挙動検査は gate と検査を同じ主体が変更できる限り意図的な弱体化への完全な防壁では
ない。宣言した arm と実際に build・bench された source の関連付けについて確かめられているのは文字列
としての materialization までで、実行到達性・実 compiler 入力・汚染 cache・後段の再検証は閉じていない。
同じ走行主体が書いた複数の投影が一致したことを独立な裏取りとしては扱わない。[21]

## 6. スコープと優先権

探索・合成が実際に回ったのは Silo 1 protocol の backoff / sort / trigger-gating の 3 軸だけである。合成
対象を Silo に限定する方針は解除され、素材コーパス CCBench の採用版も 2026-09-20 に mocc の trace hook を
含む候補へ進んだが、実働範囲は変わっていない — その前進は較正の再取得・mocc の certified 系列・性能
比較のいずれも含まず、既存の系列は前進前の固定した checkout で続ける。mocc について取れているのは
pilot と較正、証明面の計装 (採用版とは別の patch として)、探索面へ入れる前の 2 段階の準備検証までで、
いずれも公式認証でも性能比較でもない。狙う増分主張は「指定した二つの CC 実装で合成・評価手順を実証
した」に限り、「mocc は第 2 の成功例」「クロスプロトコルへ広げた」「10 プロトコルから選ぶ」とは書かない。
TicToc は較正と床値基準線の登録まで、Cicada は測定 0 件、snapshot isolation は証明面を持たない。[22]

素材コーパス側で見つけた欠陥は副産物であって合成能力の証拠ではない。上流へマージ済みのもの (2 件) と、
還元判断が人間手番のもの、観測事実の報告案までのものを一括して「還元した」とは書かない。それらを
見つけたロック規律スタディ自体は手設計で証明の連鎖の外にあり、新規性の主張としても置かない。[23]

**優先権は主張しない。** 言えるのは「本調査では、LLM が、トランザクションの並行性制御を対象として、
アクション空間自体をコードで拡張する既存例を発見していない」の 1 文までであり、系譜の中で何本目かを
数える書き方も採らない。関連研究の調査は 2 軸とも費用対効果を理由に限定付きで止めており、停止は完了では
なく、制限が恒久化したのでもない。差別化の核は 3 点で書き、「説明可能性が核である」という短縮形は
使わない。[24]

## 7. 未実証のまま残る主張

本論文は、既知軸最良の超越 (B-1)、ワークロード情報を条件とする生成の因果効果 (B-2)、無人系列の完走
(B-3)、正しさシグナルの還流による改善 (B-4)、生成器の条件付き優越 (B-5)、機序の同定 (B-9 / B-10)、
クロスプロトコルの選定 (C-1)、体系的な先行研究調査 (C-4) を
実証していない。現行契約下の対測定 (A-1) は記述的な観測までで正式な充足は未判定であり、論文採用値の
別 boot での取り直し (A-5) は未取得である。実装や準備の進展は、これらの証拠の取得を意味しない。
種を変えた長時間実行による最終候補の検証 (B-8) は、発効した事前登録の下で 3 値判定 `pass` を得たので
この一覧に含めない (§2) — それは最終候補の正しさ側の検証であり、上の主張のどれも埋めない。
各実験の配置・欠測・成果物の束縛範囲は、対応する結果稿に示す。証拠ごとの現在地の一覧は執筆者向けの
作業表として [README](README.md) に置き、本文には含めない。[25]

## 出所 (執筆者向け)

1. **旧 3 値と測定契約:** [P2-4 sweep の単独稿](../../../../docs/paper-story/results/2026-09-20-p24-static-backoff-sweep-linux-baremetal.md)、
   decisions の D496 (同一 campaign 内の対測定)・D20・D1163 (絶対規律 7)、[claim-evidence 2026-09-20 稿](../../../../docs/paper-story/claim-evidence/2026-09-20.md)
   の C1 と `L03` / `L22` / `L27`、同稿 §5.1。
2. **現行環境の 3 走行:** A-2 [certification.json](../../2026-09-07_t2364-paper-story-a2-certification/certification.json) (rr5 0.63548…、rr50 0.14421…、
   `a4_noise_floor_status` open)、A-6 [certification.json](../../2026-09-08_t2411-paper-story-a6-certification/certification.json) (rr95 −0.057841…)、
   [T-1998 単独稿](../../../../docs/paper-story/results/2026-09-18-t1998-balanced-stock-inline-accepted.md) (improvement_percent 11.2253753…)、D1993 項 6、D12、
   claim-evidence の C18〜C20 と `L29` / `L31` / `L33`、§2.4 の「逆向きの過小主張」。
3. **A-1:** [attempt-0001 の単独稿](../../../../docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md) と
   [公開 leaf の result.json](../../2026-09-13/paper-story-a1-balanced5-sized/result.json) (`formal` false / `promotion_prohibited` true、対差平均は
   write-heavy +1,591,948.5 / balanced +448,830.17 / read-heavy −576,749.77 tps)、D2120 項 3、D2044 項 8、D2156 (attempt-0002 の gate 拒否)、
   D2172 項 2 (1 attempt 限定の認可)、D2178 (認可記録を照合する gate 解除の実装)、
   `output/insights/2026-09-20/t2792-a1-sized-rerun-authorization/README.md` (認可の記録。同 insight 自体は投入・測定をしていない)、`L34` / `L35` / `L36`。
   2 本目の完走と値は [attempt-0002 の単独稿](../../../../docs/paper-story/results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md) (§2.7 の並記表、
   `variance_plan_breach` は write-heavy / read-heavy で true) と worklog entry 1755 (`output/insights/2026-09-20/t2792-a1-sized-attempt2/README.md`)、
   2 attempt の書き方 (同一配置の反復で分類と符号が一致した観察、L-A1S-4 の解除には触れない) は D2194 項 6。
4. **A-5:** D1100、D1525、`output/insights/2026-09-04/t2211-a5-second-boot-resubmit/README.md`。
5. **B-7:** [fixed 5 µs の 3 workload 同時期測定の稿](../../../../docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md) と
   [certification.json](../../2026-09-19_t1998-b7-fixed5-three-workload/certification.json)、D2162 (判定規則の結果前固定、充足の判定はしない)、
   **D2174 項 3 (限定付き充足、D2044 項 3 を supersede)**、`output/insights/2026-09-20/t2610-b7-limited-satisfaction/README.md`、
   [figures README](../../../../docs/paper-story/figures/README.md) の fig10 節。claim-evidence 稿の C26 / `L41` は D2174 より前の記述で、本稿は裁定後を採る。
6. **保証範囲:** [roadmap](../../../../docs/roadmap.md) §3.1、claim-evidence の `L01` / `L07` と §5.2、F707、[方法節草稿](../../2026-09-10/paper-methods-ja/methods.md) §3。
   commit 数 44% 減と競合 56% 相当は D36 決定 3 が正本と明記する
   `output/env/linux-baremetal/calibration/s2_verify_t48_skew0p9_rr50_rmw0.json` (2.79M → 1.55M) と claim-evidence の C8。56% は競合レートの直接測定値ではなく
   D36 が記録した被覆の解釈である。
7. **限定 (i)〜(v):** D1993 (4 限定)、D1257 (argv の独立記録)、D2108 と D2120 項 7 (identity 層の修正と残る限界 = 指令と include の相対位置、`push_macro` / `pop_macro`)、
   claim-evidence の C2 と `L42`。
8. **検証相と B-8:** [検証相の単独稿](../../../../docs/paper-story/results/2026-09-20-verify-phase-adopted-backoff.md) (本走 24 + 校正完走 6 = 判定集合 30 / 候補、
   校正 10 s の未完走 2 件 / 候補は verdict なし)、D2160 項 4〜5、D2172 項 8、`L40` / `L51`、D2175 (B-8 事前登録 v1、登録時は発効・試走・本走を認可しない)。
   B-8 の結果は [B-8 の単独稿](../../../../docs/paper-story/results/2026-09-21-b8-final-candidate-longrun-verify.md) (§1.1 の対象と identity、§2 の規則、
   §3.3 の判定 = 判定集合 30 枠・anomaly 0・`pass`、§4 の限定 11 件) と [結果・考察草稿 (2026-09-21b 版)](../paper-results-ja-b/results-discussion.md) §6.2。
   認可は D2186 項 1 (試走、(2) = 仕分け (2) を独立 process の自己シードへ) と D2194 項 1 (発効と本走)、実施の形は D2202、発効・校正・本走・判定の
   実施記録は worklog entry 1791 と `output/insights/2026-09-21/t2807-b8-effective/README.md` (§2 仕分け (2) の限定、§6 限定)、
   `docs/paper-story/README.md` の stale 注記 3。検証相を B-8 に数えない理由 (対象と長さ) は同 insight §2。
9. **mocc:** [G2 観測条件の単独稿](../../../../docs/paper-story/results/2026-09-20-mocc-g2-observation-conditions.md)、
   [軽量 witness 4 arm の単独稿](../../../../docs/paper-story/results/2026-09-20-mocc-witlight-four-arm.md)、D2148 項 13、D2172 項 7 (追加実験見送り)、`L44`。
10. **B-1:** [S-1 report](../../../../output/reports/s1_direct_comparison/report.json)、[最終報告](../../../../output/reports/s_prime_final_report.md)、
    [S-1a 9 対の単独稿](../../../../docs/paper-story/results/2026-09-20-s1a-nine-pair-direct-comparison.md)、claim-evidence の C4〜C6 と §4.3 B-1、`L12` / `L13`。
11. **非列挙の壁:** D1409、D48 (代理指標の禁止)、ストーリー §2 (b)。定義の置き直しは D1441 (2026-09-02、「固定予算の下で操作的に列挙し
    尽くせない」)、休眠は D52 / D2158 (「非列挙」の定義を変えない)、裁定済みでも壁と休眠は不変である点と前版の「未裁定」の訂正は
    `docs/paper-story/2026-09-21b.md` §2 第 3 幕 (b) と `docs/paper-story/2026-09-20b.md` 冒頭の訂正 1。旧 headline 復活条件へ D1441 を置く追補 1 は
    `docs/phase3-main-experiment-addendum-1.md` ([T-1871]、worklog entry 1752)。
12. **B-2:** [8b descriptor 設計](../../../../docs/phase3-8b-descriptor-design.md) の「selector 実験は証拠に数えない」、D960、D1363 (充足可能集合 `{"C10"}`)、D959。
13. **B-5:** D1067、D2158、D2172 項 4、[B-5 事前登録](../../../../docs/b5-generator-contrast-preregistration.md)、`L47`。
14. **出力契約と合成ループ:** ストーリー §1 の成果物 1、`L20`、[K2 3 巡の単独稿](../../../../docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md)、
    D2155、D2172 項 3、D2183 (同 job stock 対照の実装。worklog entry 1746 は「1 job も投入していない」と明記)、`L45`。
    その後の初投入の不成立は D2187 と worklog entry 1754、driver の修復は D2205 と worklog entry 1795 (実機の pair 再投入は未、
    `output/insights/2026-09-21/t2795-pair-repair/README.md` §0) — いずれも「同じ job 内の stock 対照は取れていない」を変えない。
15. **P2-5 の射程:** [凍結集計](../../../../output/campaigns/p2-5-summary.json)、D21 / D29、claim-evidence §5.4、[結果・考察草稿 (2026-09-21b 版)](../paper-results-ja-b/results-discussion.md) §1。
16. **機序の帯域:** D20、`output/insights/2026-06-22_p2-case-study-backoff-synthesis.md` と `docs/paper-story/notes-2026-07-10.md` の訂正 (0.815 → 0.494)、
    D1505 / D1506 (既定 3 定数)、D1724 / D1857 (機序主張の上限)、D1637 (2 本目の論文と数値を共有しない)、`L04` / `L05` / `L53`。
17. **右 tail と待ち方 grid:** [cohort 1 の単独稿](../../../../docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md) (1250 → 9999 µs で throughput は
    write-heavy 905,601.2 → 401,697.6、balanced 659,017.0 → 317,246.2、read-heavy 1,545,212.0 → 618,689.8 tps の 5 反復平均)、
    [cohort 2 の単独稿](../../../../docs/paper-story/results/2026-09-19-b10-static-tail-cohort2.md)、D2157、D2173 (再現欄付き後継図 fig8b)、
    [待ち方 grid の単独稿](../../../../docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md)、D1678、`L37` / `L38` / `L39`。
18. **4 機構:** claim-evidence の C9〜C11 と §5.5、D47 (8a)、D106 (8c bounded MVP)、D2143 (仮説層)。
19. **B-3 / B-4:** D1829 (権限の不在)、D906、D2016 (記述統計)、D824 (推定対象)、D1986 項 4 (赤 precursor 0 件)、D2138 / D2145 / D2146 (床値 3 spec)、
    `output/insights/2026-09-19/t2288-floor-pair-w1/README.md` (第 1 窓の完走、集約前)、`L09` / `L16` / `L46`。
20. **床値と g1:** `output/insights/2026-09-16/t2698-official-floor-resubmit/README.md` (floor 案)、D2120 項 2 (採用、「科学的に十分な床」は主張しない)、
    **D2180 (承認 A と active pointer X は AI が作る。D2120 項 2 (b) と D2174 項 4 を supersede)**、`output/insights/2026-09-20/t2724-ax-delegated/README.md`
    (発効後も gate-check は `allowed: false`、原因 2 件)、worklog の [T-2810] 起票文、走行間ばらつきの下限 3 workload は
    `output/env/pegasus/calibration/between_run_noise_t48_skew0p9_{rr5,rr50,rr95}_rmw0.json` の `between_run.cv`
    (0.009536… / 0.007250… / 0.002228…、D1639)、`L14` / `L15` / `L17` / `L43`。
    claim-evidence 稿と論文ストーリー版の「未発効・人間手番」は D2180 より前の記述で、本稿は裁定後を採る。
    不整合 2 件の整合は D2196 と worklog entry 1776 (`output/insights/2026-09-20/t2810-g1-launch-validation/README.md`)、live の起動検査が
    段階 4 の binary admission policy の不一致で拒否されることは entry 1776 / 1787 (`output/insights/2026-09-21/t2824-g1-candidate-removal/README.md` §3) /
    1790 (`output/insights/2026-09-21/t2812-old-series-realignment/README.md`)、live の起動を通す方式の設計択一は D2201。
21. **hooks・materialization:** D30、D387、D1718、D955、D920、`L08` / `L26`。
22. **スコープ:** D2114、D1360、D2083 (X/P 証明面計装は採用版の祖先ではない)、`output/insights/2026-09-20/t2304-pin-advance/README.md` と同 wave の
    spool fragment (ccbench pin を 511c9538 から e9e477ca へ前進 = mocc の trace v2 hook と TRACE 専用 lineage witness を含む 4 commit、
    D2150 項 1 の実施、較正・certified 系列・性能比較は含まず、旧系列は前進前の固定 checkout で継続)、`output/insights/2026-09-17/t2756-pin-evidence/README.md`
    (候補 4 commit の内訳)、D2134 / D2147 / D2159 (機械実証の 2 段階)、D2127 (TicToc 床値基準線)、D1936 項 39 (Cicada)、`L10` / `L19`。
23. **副産物の還元状態:** claim-evidence の C15a〜C15c と §5.7、`L28`。
24. **優先権:** D1598、related-work README と claim-survey 裁定 3 本、D1760 / D1931 / D2095 / D2120 項 14 / D2150 項 4、`L06`。
25. **未実証の主張:** claim-evidence 稿 §2.4 (書けない主張) と §4 (A / B / C 群の現在地) を土台に、前稿は D2172〜D2183 と 2026-09-20 の着地
    (fig8b / fig10 / g1 発効 / B-7 限定付き充足 / pin 前進) で一覧を更新した。本稿は採用時点 `d99c556df` までの着地 (A-1 attempt-0002 の完走、
    K2 pair の初投入の不成立と driver の修復、B-5 の試走の完走と本走の段階認可、g1 の launch validator の整合、B-8 の発効と `pass`) で
    更新した一覧を [README](README.md) の別表に置く。件数を準備完了度と読まない規律は同稿 G1。
