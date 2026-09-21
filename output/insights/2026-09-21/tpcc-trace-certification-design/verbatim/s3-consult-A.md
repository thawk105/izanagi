**判定：草案は修正が必要です。最大の must-fix は、不在の選言を「cycle を作らない側」へ絞って certified にする規則です。これは実際の観測版に基づく DSG の cycle を隠せます。**

静的検査のみです。build・binary・pytest は実行していません。

以下、`B`＝親 `brief.md`、`P`＝`stage2/plan.md`、`CC`＝`external/ccbench`、`TP`＝`CC/include/tpcc`、`V`＝`orchestrator/verifier`。B/P は指定 job ディレクトリ、その他は指定 worktree 内のパスです。`real` は主張・問題が静的根拠で成立、`refuted` は記載どおりには成立しない、を意味します。

## 1. 不在の選言解消は、実際の DSG の認定として不健全

- **重大度：must-fix**
- **判定：親 P4 の解法・草案の推奨とも refuted**
- **根拠：** `B:19`、`P:199`、`P:211`、`P:215`、`P:323`。観測版から辺を作る既存契約は `V/dsg.py:645`。
- **成果物影響：** 実際には G2 がある履歴が certified となり、非直列化可能な候補が選択される。
- **修正案：** cycle の有無を観測版の決定根拠にしない。不在を直接の証拠で確定できなければ indeterminate とする。

反例は次です。k は初期不存在、y は初期存在とします。

1. S が k を含む範囲を走査し、空を返す。この時点では k は **unborn**。
2. I が k を INSERT、y を更新して commit。
3. D が k を DELETE して commit。
4. S が I の y を読んで commit。

実際の辺は、

```text
S → I   predicate rw（unborn を観測）
I → S   point wr（y）
I → D   ww（k）
```

であり、`S→I→S` が G2 です。

ところが草案は、既存の `I→S` を見て unborn 側を排除し、dead 側の `D→S` を採用します。結果は `I→D→S` と `I→S` の非巡回グラフです。**曖昧な選言が一つも残らなくても偽認定になります。** 件数、producer、frame、witness はすべて正常にできます。

Adya の `Vset(P)` はシステムがその操作で選んだ版集合であり、dead/unborn も含みます。predicate wr はその集合に含まれる版の producer によって決まります。「非巡回になる版集合が存在する」ことへの置換は、実際の DSG の認定と同じではありません。[Adya 博士論文 §3.1.3–3.1.4](https://publications.csail.mit.edu/lcs/pubs/pdf/MIT-LCS-TR-786.pdf)

草案の「直接観測された辺として報告しない」という注記だけでは、`certified` の受理集合の変更を防げません。

## 2. 初期状態は必要だが、G 行だけでは完全性の根拠が不足

- **重大度：must-fix**
- **判定：初期状態の必要性は real／「G 一覧が必須」は refuted**
- **根拠：** `P:173`、`P:177`、`P:179`、`TP/tpcc_initializer.hh:259`、`:279`、`:284`、`:408`、`CC/include/random.hh:20`、`TP/tpcc_util.hh:22`。
- **成果物影響：** G の欠落と scan の取りこぼしが重なると、初期 live key が検査対象から消え、不完全な述語読みを受理する。
- **修正案：** 初期集合を取得する方法と、その完全性・当該 run との対応を別々に定義する。

W だけでは、一度も更新されない初期 OrderLine の取りこぼしを検出できません。この指摘は正しいです。一方、必要なのは**正確な初期集合**であって G という形式ではありません。

決定的再生成も原理的には可能ですが、現行は thread-local RNG と自己シード、customer permutation、ランダムな OrderLine 件数を使います。現状の warehouse 数だけからの再生成では足りません。

G 案にも次の穴が残ります。

```text
初期 live k を scan が取りこぼす
G からも k が欠落する
k の W は一度もない
⇒ verifier は k を列挙しない
```

G の件数と終端を同じ出力元から作るだけでは、同時欠落・同数置換を検出できません。D296 が R/W 件数について明記する限界と同型です。

最小案は、成功した初期挿入に対応する記録と、ロード完了後の実際の対象木との照合を設計することです。代替は、再現可能な初期化入力を保存して再生成すること。署名台帳などを新設する必要はありませんが、**何を信頼し、どの欠落を検出するか**は明記が必要です。

## 3. 物理 LIMIT の prefix は観測範囲であって、可視行 LIMIT の完全性証明ではない

- **重大度：must-fix**
- **判定：親 P4 の返却末尾案は refuted／草案の物理候補末尾案は条件付き real**
- **根拠：** `B:18`、`B:20`、`P:162`、`P:167`、`CC/include/masstree_wrapper.hh:287`、`CC/cc/si/transaction.cc:448`、`TP/tpcc_tx_delivery.hh:45`。
- **成果物影響：** 解釈次第で、後方キーへの偽 rw を作って正常実行を落とすか、可視行の欠落を隠して受理する。
- **修正案：** 認定する scan の契約を一つに固定する。

wrapper は可視性を調べず候補数で停止し、SI はその後で null/deleted を除外します。したがって、

```text
a：未 commit 候補
b：初期 live
limit=1
physical_count=1, returned_count=0
```

は成立しうる構造です。「全域が空」ではありません。

ただし、`[lo,a]` の観測だけを認定しても「先頭の可視行を一件取得した」ことにはなりません。草案の `P:167` の indeterminate 方針を、任意の解釈ではなく認定条件として確定すべきです。

正常な serializable 実行でも、この物理仕様に当たれば indeterminate になりえます。これは G2 の検出ではなく、認定対象と API 仕様の不一致による拒否です。

逆に live a を一件返した正常な scan では、a より後の b への INSERT をこの scan の rw にしてはいけません。全範囲扱いは偽警報になります。

## 4. abort INSERT の危険は実在するが、二つの経路を分ける必要がある

- **重大度：must-fix**
- **判定：親 P5 は refuted／草案の寿命・rollback 指摘は real**
- **根拠：** Silo `CC/cc/silo/transaction.cc:27`、`:88`、`:97`、`:109`、`:250`。SI `CC/cc/si/transaction.cc:319`、`:328`、`:340`、`:433`、`:578`。MOCC `CC/cc/mocc/transaction.cc:504`、`:513`、`:525`、`:1059`。
- **成果物影響：** dangling pointer、待機停止、未 commit tuple の残存により、trace が表す版と実際の読みが対応しない可能性が残る。
- **修正案：** 公開後 rollback と参照寿命を別の本体修正として設計し、TRACE の有無で安全性を変えない。

静的に成立する経路は二つです。

1. **公開後・write set 登録前の abort**
   三 CC とも node version 不一致による return が登録より前にあります。abort は write set を掃除するため、公開した tuple が残ります。

2. **登録済み INSERT の abort 即時解放**
   別取引が木や scan buffer からポインタを取得した後、挿入者が除去・delete できます。Silo はそのポインタ上の lock を繰り返し読みます。遅延回収だけでなく、待機解除条件も必要です。

ただし、「残存 tuple が必ず dirty read として commit する」とまでは立証できません。通常経路では Silo は lock/absent、SI は版 status、MOCC の冷経路は absent で阻止します。**UAF の静的危険と、具体的な偽 certified の再現を同一視してはいけません。**

追加の注意点として、MOCC の熱い経路は `transaction.cc:356` で payload を読み、冷経路の `:341` にある absent 判定を通りません。validation の `:1008` 以降も epoch/tid と lock を調べます。寿命修正だけでなく、この経路で不存在 tuple を読めない条件も設計対象です。

なお SI の `Tuple` に Version を削除する destructor は見当たらず、`abort():586` を単純に「同一スレッド内で解放済み Version へ書く」と断定する根拠はありません。tuple を他スレッドが参照する危険とは区別すべきです。

これらは本 wave の実装済み成果ではなく、**本体修正・新 pin の裁定パッケージ候補**です。

## 5. SI の読み保存は必要。ただし tombstone を live R にしてはいけない

- **重大度：must-fix**
- **判定：親 P1/P7 の「追加不要」は refuted／草案の履歴保存は real**
- **根拠：** `P:104`、`P:108`、`CC/cc/si/transaction.cc:239`、`:365`、`:164`、`:448`、`:541`。
- **成果物影響：** 読み消去では rw が落ちて偽認定、tombstone の誤った R 化では正常な scan が存在履歴不整合で拒否される。
- **修正案：** 外部 live 読み、deleted 観測、不可視、自己版を計装時点で区別する。

SI の update/delete は既読要素を消します。Payment の read→update、Delivery の scan→delete/update の読みを commit 時の native set だけから出す設計は不足です。

一方、`read_internal()` は deleted 版も read set に登録して返し、scan がその後に除外します。したがって、`read_internal()` の成功をすべて live R にコピーする実装も誤りです。deleted は Q の不存在観測として扱う必要があります。

Silo/MOCC の scan は既読・自 write の再利用時に新しい R を追加しません。草案の Q はこの対応を保存する方向として妥当です。ただし実際に返した分岐を記録し、単に「同じキーが write set にあるから自己版」と推定してはいけません。既読検索が write set 検索より先だからです。

自己 INSERT→scan の一般 API 意味まで保証するなら操作順も必要です。しかし現行五取引のためだけに一般的な操作ログを導入するのは過剰です。現行 workload の到達経路と一般 API fixture の射程を分けることを推奨します。

## 6. SI の X/P は「後で足す」だけでは既存契約を満たせない

- **重大度：must-fix**
- **判定：未成立という草案の留保は real／三 CC の認定経路が設計済みという解釈は refuted**
- **根拠：** `P:132`、`P:134`、`P:362`、`V/model.py:77`、`:450`、`CC/cc/si/transaction.cc:170`、`:471`。
- **成果物影響：** SI の正常な非巡回 trace も certified にならない。形式だけの emitter を置けば、逆に証拠のない認定を許す。
- **修正案：** SI の証拠面を独立した未決項として、対応する安全条件と破壊変異まで具体化する。

SI は Silo の write lock 保持や write-set sort と同じ仕組みではありません。既存 X/P の意味をそのまま充足する方法が、草案にはありません。

`model.py` の認定条件を protocol 特例で外すことや、検査しない X/P emitter を追加して source assessment だけ通すことは、既存契約を保った対応ではありません。SI の install-version 所有・公開条件と、操作集合保存の検査をどの契約に対応させるかを裁定へ返す必要があります。

SI が実際に G2 を作った場合の拒否は正しい挙動です。X/P 不足による indeterminate とは理由を分けて報告すべきです。

## 7. witness 修正は妥当。ただし試験は終了境界だけでは不足

- **重大度：should**
- **判定：親 P2・草案の TRACE 限定案は real**
- **根拠：** `B:16`、`P:112`、`P:136`、`P:297`、`CC/include/tpcc.hh:92`、`:102`、`:110`、`V/model.py:450`。
- **成果物影響：** 正しい終了時 commit が拒否されなくなる一方、欠落試験を省くと D295 の防護を実証したとは報告できない。
- **修正案：** 完全一致を維持し、末尾 C frame・最大 txid・thread file 全体の欠落を別々に試験する。

提案された `#if !TRACE` による quit return の抑制では、TRACE build の成功 commit が一回だけ counter に到達します。app abort と commit 失敗は加算されません。C 行から counter を算出せず、許容幅もないため、D295 の個数による欠落検出は維持できます。

ただし検出限界も維持されます。

- trace と counter の同時欠落
- 個数を保存する置換
- C を残した R/W 欠落――これは frame や操作履歴の領分

無条件に counter を移す案も本体修正としてはありえますが、perf build が終了境界で数える commit を変えます。TRACE 限定案は TRACE=0 の挙動を維持します。両案を同じ性能計測意味として扱ってはいけません。

## 8. 正例・負例の帰属に未完成部分がある

- **重大度：must-fix**
- **根拠：** `P:290`、`:291`、`:292`、`:304`、`:320`、`:323`、`:325`、`:332`。
- **成果物影響：** 別の integrity 検査で赤になるだけの例や、変異後も赤の例を検出力の証拠として数えてしまう。
- **修正案：** 各 fixture の全操作・版順・初期状態を固定し、狙った機構を外したときの辺差分を明記する。

| 草案の例 | 静的判定 |
|---|---|
| 表欠落による偽警報 `P:290` | **real、版順の指定が必要。** B の Warehouse 更新版が A の Item 更新版より前なら、表なしでは `B→A ww` と `A→B rw` ができる。表ありでは `A→B rw` のみ。草案記載の辺方向は修正が必要。 |
| 表欠落による見逃し `P:291` | **帰属不成立。** 記載された操作には逆辺がなく、cycle が未完成。同版 producer 衝突は version duplicate による拒否にもなる。 |
| 二表 W の上書き変異 `P:292` | **帰属不成立。** 消した W を読む R が残れば orphan。具体的に何が残り、何が消えるか未指定。 |
| 手書き G2 `P:304` | 表ありでは `0→1 rw` と `1→0 rw`。ただし表を消しても genesis 読みから両方向 rw が残り、cycle は消えない。**G2 control として real、表識別の検出力としては帰属不成立。** |
| broken read validation | `A→B ww`、`B→A rw` で real。正常 Silo/MOCC では片方 abort が必要。 |
| INSERT phantom `P:320` | `S→I predicate rw` と `I→S point rw`。predicate 辺だけを外せば非巡回になるので real。 |
| DELETE phantom `P:322` | 基本例は `D→S` の二種類の辺だけで非巡回。赤例の逆依存は未指定。 |
| 不在一意化 `P:323` | **refuted。** 指摘1の反例そのものを緑にする可能性がある。 |
| limit 偽依存防止 `P:325` | 後方 b の除外は real。ただし偽 cycle を示すには、b の挿入者から scan への逆依存も指定する必要がある。 |
| genesis 誤用・初期行欠落・物理 LIMIT | integrity/認定範囲の試験として real。cycle control と数えない。 |
| 正常対照 | graph green と certified は別。X/P、frame、witness を満たす形を併記する必要がある。 |

表識別の偽 green control は、例えば次のように完成できます。

```text
A：Warehouse(k) genesis を読む、Item(k) を書く
B：Item(k) genesis を読む、Warehouse(k) を書く
```

これは草案同様 G2 ですが、表消去だけでは cycle が残ります。したがってこれを表識別の control に流用せず、**表ありの参照グラフとの辺集合比較**と、重複・欠落の integrity 試験を別に置く方が正確です。

### 実 TPC-C schedule と API 合成例

草案の OrderStatus→NewOrder→Payment 案は、通常ロードでは「成立しない場合が多い」より強く制約されます。全 customer に初期 OrderSecondary があり、削除されず、昇順 limit=1 は初期最小 order を選びます。通常の新規 order はその後ろです。

根拠は `TP/tpcc_initializer.hh:407`、`TP/tpcc_tx_orderstatus.hh:28`、`TP/tpcc_tables.hh:297`。overflow 等を除く通常域では、この OrderSecondary phantom 辺は作れません。

一方、全五取引を許す workload 内での G2 候補は、実際の取引で次のように構成できます。

```text
NewOrder N → Delivery D   rw(Customer)
Delivery D → StockLevel L wr(OrderLine)
StockLevel L → NewOrder N rw(District)
```

到達可能な前状態として、Delivery の次対象 order が当該 district の直近20件に入るまで古い NewOrder を処理しておきます。N はその order の customer を選びます。

1. N が Customer の旧版を読み、一旦停止。
2. D が対象 OrderLine と Customer を更新して commit。
3. L が更新済み OrderLine と、N 更新前の District を読み commit。
4. N が District を更新して commit。

根拠は `tpcc_tx_neworder.hh:36`、`:60`、`:71`、`tpcc_tx_delivery.hh:150`、`:187`、`tpcc_tx_stocklevel.hh:42`、`:50`。これは**静的 schedule 案であり、再現済みではありません**。SI では read/write 競合だけで排除されるとは限らず、Silo/MOCC では N の古い Customer 読みの検証が焦点になります。predicate 固有の control とも区別できます。

## 9. 親 brief と草案推奨の判定一覧

| 親前提 | 判定 | 理由 |
|---|---|---|
| P1 | **refuted（一部 real）** | 表付きキーは必要。既存 set に表を足すだけでは SI の消えた読みを回復できない。 |
| P2 | **real** | quit return が加算前。完全一致を維持して直せる。 |
| P3 | **real、現行五取引限定** | CustomerSecondary はロード時に構築・整列し、join 後は参照のみ。OrderStatus も同じ姓検索を使い、選択後の Customer は CC read を通る。 |
| P4 | **refuted** | 観測対応、LIMIT、不在の選言に不足。OrderLine/Order は Delivery が UPDATE する。「INSERT/DELETE 両方を受けるのは NewOrder」は real。 |
| P5 | **refuted** | 三 CC に node validation があることは real。それだけで完全な phantom 防止や制御改修不要は導けない。 |
| P6 | **一部 real／一部 refuted** | MOCC watermark 不使用は real。SI 現行 v1 は事実だが、新 TPC-C まで v1 を維持すべきという根拠にはならない。 |
| P7 | **refuted（一部 real）** | 点読み失敗の app abort は支持。Delivery の読みが必ず既存 trace に残るという部分は SI で成立しない。 |
| P8 | **real、承認と能力を区別** | hook の三ファイルと D16 の行き先は一致。ただし hook 設定の存在を Codex 上の防護実証には数えない。 |

P3 の根拠は `tpcc_initializer.hh:365`、`:380`、`:402`、`:496`、`tpcc_tx_payment.hh:115`、`:165`、`tpcc_tx_orderstatus.hh:93`、`:106` です。

| 草案末尾の推奨 | 判定 |
|---|---|
| v3、表付きキー、SI 読み保存、TRACE commit 計数 | **real**。指摘5の状態区別が必要。 |
| YCSB 互換、TPC-C の表なし入力拒否 | **real**。run 全体で workload/schema を固定し、legacy namespace への分離だけで混在を許さない。 |
| INSERT rollback・寿命の本体修正 | **real**。別裁定・別実装項目。 |
| S＋Q＋初期集合 | **real**。G 形式の必須性と完全性保証は未成立。 |
| 到達可能性で不在選言を解く | **refuted**。偽認定反例あり。 |
| 物理 LIMIT の可視行欠落を認定しない | **real**。認定契約として確定すること。 |
| MOCC watermark 不使用、SI G2 拒否 | **real**。 |
| 17単位・5 wave、容量試算 | **refuted（確定見積りとして）**。選言解法と SI 証拠面が未成立。仮定付き予算値としてのみ残せる。 |
| X/P と pin 波及を残す | **real**。SI 対応完了とは書けない。 |

## 10. scope と裁定の表現

- **重大度：should**
- **根拠：** `B:7`、裁定控え「項2」、`P:270`、`P:276`、`P:362`。
- **成果物影響：** 親の改訂提案や未実装の本体修正が、採用済み裁定・完成済み認定経路として台帳に載る。
- **修正案：** 「TPC-C 必須」と「NewOrder/Payment→全五取引の段階案」の権威を分ける。

裁定控え自身は二段階案を「改訂推奨。ユーザーの明示確認はまだ取れていない」と記しています。B の「確定裁定」はこの部分について強すぎます。今回の設計対象として進めることと、ユーザーの逐語裁定として記録することは別です。

効く層である CCBench emitter、verifier、pipeline allowlist、witness は草案にすべて登場しています。不要な台帳新設も見当たりません。ただし以下は完成済みと扱わず、裁定パッケージ候補です。

- abort INSERT の本体安全性修正
- 可視行 LIMIT への API 動作変更
- SI の X/P に対応する証拠契約
- 新 pin の採用・公開
- 実際の DSG から別の直列化可能性定義へ認定意味を変更する案

## 総括

must-fix は次の六点です。

1. **cycle 回避を根拠に不在版を選ぶ規則を撤回する。**
2. **初期集合の完全性と当該 run との対応を定義する。**
3. **物理 LIMIT と可視行 LIMIT の認定契約を固定する。**
4. **公開 INSERT の rollback・参照寿命・MOCC の absent 経路を別々に閉じる。**
5. **SI の読み保存を live／deleted／不可視／自己版で区別する。**
6. **SI の証拠面と、各 control の辺構成・帰属を完成させる。**

推奨は、段1の v3・表付きキー・読み保存・完全一致 witness を採り、段2は S/Q と正確な初期状態を追加することです。**不在版を実際の証拠で確定できない履歴は indeterminate のまま残す**のが、既存の認定契約を緩めない解き方です。