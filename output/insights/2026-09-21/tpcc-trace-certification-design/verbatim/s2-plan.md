## (P1)〜(P8) の判定

本稿は静的調査に基づく設計草案である。build・binary 実行・pytest は行っていない。以下の新形式・改修・試験・工数は提案であり、実装済み・実証済みを意味しない。

パスを短くするため、`CC/` は `external/ccbench/`、`TP/` は `external/ccbench/include/tpcc/`、`V/` は `orchestrator/verifier/` を表す。行番号は投入先 worktree の現行ファイルに対するもの。

| 前提 | 判定と根拠 |
|---|---|
| P1 | **修正。** `(storage_, key)` は支持。ただし SI は update/delete 時に既読要素を消すため、残存 set に表番号を足すだけでは不十分。読みの trace 専用保存が要る。`CC/include/op_element.hh:19`、`CC/cc/si/transaction.cc:239`・`:360`。 |
| P2 | **支持。** 成功 commit 後の counter 加算を確実に行う。最小案は TRACE build だけ `quit_` の早期 return を抑えること。`CC/include/tpcc.hh:102`・`:110`。 |
| P3 | **支持、射程限定。** 現行五取引では CustomerSecondary は不変。直接索引参照そのものの依存辺は不要だが、選んだ Customer の CC 読みは必要。`TP/tpcc_tx_payment.hh:114`・`:165`、`TP/tpcc_initializer.hh:365`・`:380`・`:402`。 |
| P4 | **修正。** S 行だけでなく scan ごとの観測キー・版との対応、物理上限による打切り、初期キー集合が必要。不在の選言は到達可能性で一意化できる場合だけ採用し、残りは indeterminate。`CC/include/masstree_wrapper.hh:287`、`CC/cc/si/transaction.cc:448`。 |
| P5 | **修正。** node validation は三者に存在する。しかし挿入 tuple の公開後・write set 登録前の abort と、abort 時の即時解放があり、「制御改修不要」は支持できない。`CC/cc/silo/transaction.cc:88`・`:97`・`:109`・`:27`、SI `:319`・`:328`・`:340`・`:578`、MOCC `:504`・`:513`・`:525`・`:1059`。 |
| P6 | **修正。** MOCC watermark を TPC-C に使わない点は支持。INSERT/DELETE では明示的に abort する。SI の**現行** v1 は事実だが、新 TPC-C 形式まで v1 に据え置く理由はない。YCSB v1 を保存し、TPC-C は三者共通の新 frame にする。`CC/cc/mocc/transaction.cc:78`・`:1173`、SI `:539`。 |
| P7 | **修正。** 点読み NOT_FOUND で取引を abort する整理は支持。ただし「Delivery の scan の R が必ず残る」は SI では反証される。delete が read set から消すため、履歴保存が必要。`TP/tpcc_tx_delivery.hh:69`、`CC/cc/si/transaction.cc:360`。 |
| P8 | **支持、補足。** hook の三ファイル境界と pin 前進は正しい。編集面内の trace 本採用も D16 上は枝への収容対象。寿命修正は trace 計装と分けた本体バグ修正になる。`hooks/guard_write.py:44`、`orchestrator/campaign/s8b_approved.py:67`、`docs/decisions.md:67618`。 |

## 1. 段 1：NewOrder / Payment の trace 形式と verifier の意味

### 1.1 表識別子・形式・旧形式との共存

三者の要素が継承する `OpElement` に `storage_` があり、整数化には既存の `get_storage()` を使える。表番号は Warehouse=0〜Stock=10。キーの hex 自体へ表番号を混ぜず、別 field とする。根拠：`CC/include/op_element.hh:17`、`CC/include/workload.hh:5`、`TP/tpcc_tables.hh:16`。

**提案：TPC-C 専用 v3 frame。**

```text
C <txid> <thid> <epoch> <tid> <nR> <nW> <nS> <nQ> <tx_type>
R <txid> <table> <key_hex> <ver_epoch> <ver_tid>
W <txid> <table> <key_hex> <U|I|D> <epoch> <tid>
... S/Q は段2 ...
E <txid>
```

- C の token 数で旧 v1=5、旧 v2=7、新 v3=10 を区別する。TPC-C 呼出しでは v3 を必須とし、表なし R/W を旧形式へ読み替えない。
- `tx_type` は既存の NewOrder=1〜StockLevel=5。`tpcc.hh` の `begin()` 後に TRACE 専用状態へ設定し、commit frame に渡す。
- 新 helper は `#if TRACE` 内に追加し、旧 `emit_commit/read/write` は YCSB 用に維持する。TPC-C かどうかは workload 層が設定する TRACE 専用 context で識別でき、CC の通常制御へ workload 判定を持ち込む必要はない。
- nR/nW/nS/nQ、txid 相関、E、既知 tag・表番号・取引番号を厳格に検査する。未知 tag や欠落を無視しない。
- X/I 等の違反行も TPC-C では表を持たせる。R/W だけ表付きにしても、構造化診断が曖昧なまま残る。

根拠：現行 frame は `CC/cc/silo/transaction.cc:594`、MOCC `:1134`、SI `:539`。旧 helper は `CC/include/trace.hh:78`、取引番号は `TP/tpcc_query.hh:19`、dispatch は `CC/include/tpcc.hh:55`。未知 tag の拒否は `V/parse.py:455`。

| 変更先 | 具体的な変更 |
|---|---|
| `V/model.py:315` `Read`、`:321` `Write` | TPC-C の識別を `(table, key_hex)` にする。旧入力は専用 legacy namespace とし、Warehouse=0 と同一視しない。 |
| `V/model.py:328` `Txn` | schema、tx_type、scan 観測を保持。`write_keys()`（`:337`）も表込み。 |
| `V/parse.py:296` `_parse_file` | C/R/W の v3 分岐、取引型・表・全件数・終端検査。既存 C/R/W 分岐は `:320`・`:366`・`:372`。 |
| `V/parse.py:182` `_ParsedFileColumns`、`:520` `_txn_from_columns`、`:547` `_parse_file_to_columns` | compact 経路にも表を保存する。token interning は `(table,key)` 単位にし、復元時にも失わない。 |
| `V/dsg.py:344` `_build`、`:388` `_build_compact_packed`、`:492` `_build_compact_tuple` | producer、per-key versions、token→key_id を表込みに変更。object 経路だけ直して compact 経路を残してはいけない。 |
| `V/dsg.py:198` `_edge_candidates_for_task`、`:645` `_add_read_edges`、`:671` `_add_ww_edges` | ww/wr/rw の照合単位を表込みにする。 |
| `V/dsg.py:774` `_reasons`、`V/model.py:353` `EdgeReason` | 表・取引型・後述の scan_id を復元できるようにする。 |

既存 JSON の bytes を守るため、`V/report.py:17`・`:96` の YCSB 出力は維持する。TPC-C の構造化出力は専用 reporter に置き、`table / key / tx_type / scan_id / edge_type / versions` を出す案を推奨する。report.py の凍結制約は、必読 `decisions-excerpt.md:98` にも明記されている。

### 1.2 表なしキーの衝突を全部列挙する

通常の生成域、ID の overflow 前、History の bitfield がコードコメントどおりの配置であることを前提とする。**同じレイアウトだけでなく、異なるレイアウトが同じ bytes を生成する組も含める。**

| 衝突する表の組 | 条件・例 | 根拠 |
|---|---|---|
| Warehouse / Item | `W_ID=I_ID`。例：双方 1 | `TP/tpcc_tables.hh:44`・`:356` |
| District / Item | `I_ID=256×D_W_ID+D_ID`。例：District(1,1) と Item(257) | 同 `:69`・`:356` |
| Warehouse / District | `W_ID=256×D_W_ID+D_ID`。例：Warehouse(257) と District(1,1)。257 warehouse 以上なら実在しうる | 同 `:44`・`:69` |
| Customer / Order | 同じ `(w,d,c_id=o_id)` | 同 `:118`・`:284` |
| Customer / NewOrder | 同じ `(w,d,c_id=no_o_id)`。初期ロードの NewOrder は Order と同じ o_id を持つ | 同 `:118`・`:257`、`TP/tpcc_initializer.hh:283` |
| NewOrder / Order | 同じ `(w,d,o_id)`。NewOrder が両方へ挿入する | `TP/tpcc_tables.hh:257`・`:284`、`TP/tpcc_tx_neworder.hh:308` |
| 初期 History / Warehouse | History の `id=0, at_work=0, counter=W_ID` | `TP/tpcc_tables.hh:221`、`TP/tpcc_initializer.hh:403`・`:463` |
| 初期 History / District | 同 History の `counter=256×w+d`。例 counter=257 | 同上、`TP/tpcc_tables.hh:69` |
| 初期 History / Item | 同 History の `counter=I_ID`。例 counter=1 | 同上、`TP/tpcc_tables.hh:356` |

初期 History は warehouse ごとに 30,000 行、先頭 warehouse の counter は 0〜29,999。したがって最後の三組は生成域内で実在する。ただし通常の実行 trace は初期 History を読まず、Payment の新 History は `at_work=1` なので、初期 History の衝突がそのまま今回の R/W に現れるわけではない。根拠：`TP/tpcc_common.hh:24`、`TP/tpcc_initializer.hh:403`・`:463`、`CC/include/tpcc.hh:39`。

この生成域では、Stock は先頭二 byte が 0、その次に非零 warehouse、Customer/NewOrder/Order は先頭に非零 warehouse、OrderLine は byte 2 に非零 district を置くため、上表以外の固定長キー同士は区別できる。OrderSecondary は16 byte。CustomerSecondary は姓名から作る可変長キーで、他表の生成キーとは一致しない。根拠：`TP/tpcc_tables.hh:118`・`:158`・`:297`・`:331`・`:390`。任意の整数入力や counter wrap まで含む衝突全称命題には拡張しない。

### 1.3 INSERT・genesis・abort

**W の op=`I` と、独立 tag `I` は別物である。** 前者は INSERT、新版は commit 版。後者は既存 write-intent 違反行なので転用しない。根拠：`V/model.py:321`、`V/parse.py:394`。

提案する存在状態は次のとおり。

- 初期ロード済みキー：genesis `(1,0)` に存在する。
- 初期ロードになく最初の committed write が INSERT：INSERT より前は **unborn**。genesis の値を持つとは解釈しない。
- DELETE：不存在版を作る。通常の R がこの版を「存在する値」として読むのは不整合。
- UPDATE：存在する版を更新する。存在履歴の矛盾は indeterminate。
- abort した INSERT：committed version chain に入れない。

現行 DSG は op を使わず write を版列へ並べるため、存在意味を追加する必要がある。根拠：`V/dsg.py:344`・`:357`・`:645`。TPC-C の初期版は Silo `CC/cc/silo/include/tuple.hh:40`、SI `CC/cc/si/include/tuple.hh:21`。

**重要：abort 後の tuple 寿命は、計装追加だけでは閉じない。**

| CC | 静的に読める経路 | 設計上の扱い |
|---|---|---|
| Silo | INSERT は lock=1/absent=1 の tuple を木へ公開。他取引の read はポインタ取得後、lock が下がるまで tuple を再読する。一方 abort は木から除去して即 delete。 | reader がポインタを持った後に abort が解放する interleaving をソース上排除できない。退役・遅延回収と待機解除が必要。 |
| SI | read/scan は tuple の `latest_` を読み、未 commit 版を prev へ辿る。abort は公開済み tuple を即 delete。 | tuple の寿命保護が必要。tuple delete 後の `ver_->status_` 更新も所有関係込みで扱う。 |
| MOCC | read は tuple の温度・rwlock・tidword・payload を参照。abort は即 delete。 | absent 判定に到達する前にも参照がある。冷温両経路と CLL/RLL の参照を含めて退役条件を設計する。 |

根拠：Silo `CC/cc/silo/include/tuple.hh:50`、`CC/cc/silo/transaction.cc:226`・`:250`・`:27`。SI `CC/cc/si/transaction.cc:147`・`:433`・`:578`、tuple は `CC/cc/si/include/tuple.hh:9`。MOCC `CC/cc/mocc/transaction.cc:276`・`:320`・`:356`・`:1059`。

これは **実行で UAF を再現したという主張ではなく、静的に構成できる危険な経路**である。Masstree の `get_value()` は生ポインタを返し、scan も生ポインタを buffer に積むので、木の内部保護だけを tuple の寿命保証と数えられない。`CC/include/masstree_wrapper.hh:182`・`:294`。

さらに三者とも、木への INSERT 成功後、node version 不一致で return する箇所が write set 登録より前にある。abort が write set だけを掃除するため、この分岐では公開 tuple が掃除対象から漏れる。登録順序または明示的 rollback を直す必要がある。根拠：Silo `:88`〜`:109`、SI `:319`〜`:340`、MOCC `:504`〜`:525`。

これらの本体修正は **TRACE の外で両 build に適用するバグ修正**とし、trace 専用の動作差で隠さない。既存 GC にそのまま push すれば安全とも断定しない。Silo の回収は tuple の epoch を見る一方、未 commit INSERT の epoch は committed DELETE と同じ意味を持たないためである。`CC/cc/silo/transaction.cc:15`、`CC/cc/silo/include/tuple.hh:50`。

### 1.4 SI の読み保存は段 1 から必要

SI の Payment は Warehouse/District/Customer を read→update するが、update は read set の該当要素を消す。したがって現行 commit emitter からは、この三つの R が消える。根拠：`TP/tpcc_tx_payment.hh:25`・`:62`・`:165`、`CC/cc/si/transaction.cc:239`・`:541`。

提案は、TPC-C の成功した外部版読みを、その時点で **表・キー・版の値として** TRACE 専用履歴へ保存すること。版ポインタを保存し続けない。update/delete による native set の変更から独立させ、abort/begin で消し、commit 時に出力する。自分の INSERT/UPDATE を読む操作は外部 producer の R に偽装しない。YCSB の現行 emitter は変更しない。

### 1.5 app abort・commit counter・allowlist

最小改修は、`CC/include/tpcc.hh:110` のみを次のようにする案である。

```cpp
#if !TRACE
    if (loadAcquire(tx.quit_)) return;
#endif
    tx.result_->local_commit_counts_++;
    tx.result_->local_commit_counts_per_tx_[get_tx_type(query.type)]++;
```

これにより TRACE=0 の計数意味は現行のまま、TRACE=1 は成功 commit ごとに一回加算する。trace 外 counter を C 行数から計算しない。app abort は `tpcc.hh:92`、commit 失敗は `:102` で abort に入り、加算へ到達しない。

無条件に counter を前へ移す案も正当な本体修正になりうるが、性能側の終了境界で数える commit が変わる。今回の trace 導入とは分ける方が小さい。規律1の根拠は `CC/include/trace.hh:5`、D14 は必読 `decisions-excerpt.md:3`。

`orchestrator/campaign/pipeline.py:434` の allowlist は、次が揃った **対応済み TPC-C binary** に限って広げる。

1. v3・表識別・必要な操作履歴が揃う。
2. 段1では NewOrder/Payment のみが生成される設定である。
3. C 件数と stdout counter が完全一致し、batch counter は既存どおり非対応。
4. 段2では述語観測が完全で、未解決不在がない。
5. 現行の X/P proof-surface 要件も満たす。

最後の条件は既存要件であり新 gate ではない。現在の `Integrity.clean()` は X/P evidence を要求するため、**cycle がないだけでは certified にならない**。`V/model.py:77`・`:450`。SI 向けの対応する証拠面が未成立なら、allowlist を広げても「SI certified」を約束できない。

witness の ±thread 数等の許容は作らない。終了境界の既知差と、末尾取引・ファイル丸ごとの欠落が区別できなくなるためである。D295 の根拠：必読 `decisions-excerpt.md:74`・`:85`。比較実装は `V/model.py:450`。

### 1.6 Payment の姓検索

`CustomerSecondary` の vector は初期ロードで作成・整列され、ロード worker は終了前に join される。実行時は vector から選んだ Customer key を通常の CC read に渡す。したがって現行五取引に限れば、索引直接参照について新たな R/S は不要である。根拠：`TP/tpcc_initializer.hh:362`・`:402`・`:496`、`TP/tpcc_tx_payment.hh:114`・`:125`・`:259`。

この根拠は「一般の二次索引読みは trace 不要」という規則ではない。CustomerSecondary の実行時更新を追加する改修には適用できない。

## 2. 段 2：全五取引の述語読みと phantom

### 2.1 S 行と scan ごとの観測

**提案：**

```text
S <txid> <scan_id> <table> <lo_hex> <lo_excl> <hi_hex> <hi_excl>
  <limit> <direction> <physical_count> <returned_count> <last_physical_key> <stop>
Q <txid> <scan_id> <table> <key_hex> <state> <ver_epoch> <ver_tid>
```

実際は各々一行。空の端点・版なしには定義済み sentinel を用い、`stop` は範囲終端／件数上限、`state` は返却 live／観測 tombstone／可視版なし／自取引版等の有限集合とする。Q は scan の物理候補ごとに保存し、S の件数と対応を検査する。

Q が必要なのは、同じ取引の別の point read や scan と R set が混ざり、scan に返った集合を commit 時の R set だけから復元できないためである。自分の write や既読要素の再利用もある。根拠：Silo `CC/cc/silo/transaction.cc:304`、SI `:429`、MOCC `:388`。

S/Q は scan 中に thread-local buffer へコピーし、成功 commit の frame 内にだけ出す。abort で消す。出力時まで tuple/body の参照を保持しない。

**件数上限の意味：**

- 上限未到達で範囲終端まで走査した場合、実効範囲は指定範囲。
- 上限到達時、観測できた prefix は下限〜最後の**物理候補キー**まで。最後の返却 live key ではない。
- `returned_count < limit` でも全域走査と解釈しない。
- API を「可視行の LIMIT」として認定するなら、未 commit 候補で上限が埋まって後続 live 行を見なかった履歴は、そのまま完全な述語読みとして認定できない。まず indeterminate とする。可視行数を満たすまで走査を続ける本体修正は別途必要。

Masstree は可視性判定前に buffer の件数で止まり、CC が後で不存在版を除く。`CC/include/masstree_wrapper.hh:287`、`CC/cc/si/transaction.cc:448`、Silo `:317`。

なお「最後に触れたキー」は、上限チェックで拒否した次候補と、buffer に採用した最後の候補を区別する。後者を実効 prefix の終端として記録する。`CC/include/masstree_wrapper.hh:288`。

### 2.2 初期キー集合を省けない

W 行だけから範囲内の候補キーを作ると、初期ロード済みで実行中一度も更新されず、壊れた scan が取りこぼしたキーが検査対象に現れない。

段2では、scan 対象の **NewOrder・OrderSecondary・OrderLine の初期キー一覧**を、TRACE build のロード時に保存する案を推奨する。値全体は不要。件数・終端付きの別初期化ファイルとし、取引 C counter へ混ぜない。

必要性の具体例は、OrderSecondary の初期 permutation と OrderLine のランダム件数であり、単純な定数範囲だけでは実キー集合を再構成できない。`TP/tpcc_initializer.hh:259`・`:269`・`:279`・`:407`・`:413`。初期 NewOrder の条件も `o_id>2100` ではなくコード上は `c_id>2100` である。`:283`。

### 2.3 張る辺

既存の値読みの定義は維持する。`V/model.py:343`、`V/dsg.py:645`・`:671`。

| 観測 | 追加する依存 |
|---|---|
| 範囲内 live 版 v を返した | producer(v) → reader の wr。v の直後版 writer へ reader → writer の rw。値更新も対象。 |
| 範囲内で「挿入前の不存在」を観測した | reader → first INSERT の predicate rw。 |
| 範囲内で DELETE 版による不存在を観測した | DELETE producer → reader の predicate wr。再挿入があれば reader → next INSERT の predicate rw。 |
| 存在するはずの初期キーが返らず、対応する DELETE もない | 履歴不整合。単なる「辺なし」にしない。 |
| predicate 外へのキー | その scan からは辺を張らない。 |
| 自取引の変更 | 操作順と自己観測として処理し、外部取引への自己ループを作らない。 |

ここで predicate wr/rw は、述語結果の membership を決めた版／次に変える版への依存である。キー範囲内だからといって、読んだ版より後の**全 writer**へ無差別に辺を張る必要はない。直後版への辺と ww chain を使う。既存にも直後版＋推移性の試験がある。`orchestrator/tests/test_verifier.py:257`。

### 2.4 不在の曖昧さ：比較と推奨

INSERT producer を I、DELETE producer を D、scan 取引を S とする。初期不存在キーについて、見えない理由が未確定なら、

```text
S → I    または    D → S
```

という選言になる。I→D の存在履歴と既存の点依存を先に作る。

| 案 | 評価 |
|---|---|
| **(i) 到達可能性で一意化、未決は indeterminate** | **推奨。** 例えば I→…→S が既にあれば unborn 側は直列順と両立せず、dead 側だけが残る。S→…→D があれば逆。片方を選ぶ根拠がなければ選ばない。複数選言の相互依存も勝手に一括決定しない。 |
| (ii) TRACE 専用の物理通し番号 | 番号採番と木の変更は原子的ではなく、scan は区間操作。開始／終了の番号が重なる履歴は決まらない。さらに SI は物理的に存在しても snapshot より新しい版を見ない。単なる連番では解決しない。 |
| (iii) 存在版/tombstone を残し、不在観測版を直接記録 | 観測を明確にできるが、現行は木から DELETE するため、墓石管理・snapshot 可視性・GC まで変更が広がる。段2の最初の実装には過大。 |

(i) の採用は、観測版が確定したと偽ることではない。**完全な直列化が存在すると仮定したとき、両立しうる選択肢を必要条件で絞る**。残った選言があれば certified にしない。両側が矛盾する場合は選言そのものを含む非直列化の証拠を返すか、初版では indeterminate に留める。仮定で作った一辺を「直接観測された辺」として報告しない。

物理順だけで不十分な根拠：SI の `read_internal()` は `txid_ < cstamp` を飛ばす（`CC/cc/si/transaction.cc:153`）。DELETE は物理除去（`:513`）。scan の候補取得と版読みは分かれている（`:424`・`:448`）。

### 2.5 五つの scan と writer

| scan | 実コードの範囲・上限 | 実行時 writer | 分類 |
|---|---|---|---|
| Delivery `TP/tpcc_tx_delivery.hh:45` | NewOrder、`[(w,d,1),(w,d+1,1))`、昇順 limit=1 | NewOrder の INSERT（`tpcc_tx_neworder.hh:143`）、Delivery の DELETE（`tpcc_tx_delivery.hh:69`） | **挿入＋削除** |
| Delivery `:135` | OrderLine、`[(w,d,o,1),(w,d,o+1,1))`、無制限 | NewOrder の INSERT（`:279`）、Delivery の UPDATE（`tpcc_tx_delivery.hh:150`） | **挿入＋更新** |
| OrderStatus `TP/tpcc_tx_orderstatus.hh:30` | OrderSecondary、`[(w,d,c,1),(w,d,c+1,1))`、昇順 limit=1 | NewOrder の INSERT（`tpcc_tx_neworder.hh:114`） | **挿入のみ** |
| OrderStatus `:72` | OrderLine、Delivery と同じ形、無制限 | NewOrder INSERT、Delivery UPDATE | **挿入＋更新** |
| StockLevel `TP/tpcc_tx_stocklevel.hh:50` | OrderLine、`[(w,d,next−20,1),(w,d,next,1))`、無制限 | NewOrder INSERT、Delivery UPDATE | **挿入＋更新** |

Order は scan 対象ではないが、NewOrder が INSERT、Delivery が UPDATE する。したがって P4 の「OrderLine・Order は挿入のみ」は、**membership の変更だけを指すならよいが、行の writer 全体としては誤り**。根拠：`TP/tpcc_tx_delivery.hh:106`・`:150`。

また OrderStatus のコメントは最新 order を求めるが、実装は昇順木の limit=1。最新を読むと仮定して依存を作ってはいけない。`TP/tpcc_tx_orderstatus.hh:9`・`:28`、`CC/include/masstree_wrapper.hh:208`。

### 2.6 計算量

提案は表ごとに初期キーと committed write キーを整列し、各 scan を二分探索する。

- 初期構築：K 個のキーに対して概ね `O(K log K)`、版列は既存構築へ統合。
- scan 1 回：`O(log K + k + Σ log v_k)`。k は**実効範囲内にある初期キー＋実行中生成キーの distinct 数**であり、返却件数だけではない。
- 不在選言一件の単純な到達可能性探索：最悪 `O(T+E)`。未解決数 a に対して最悪 `O(a(T+E))` が追加される。
- NewOrder の limit=1 でも、先頭 live key より前の deleted keys を大量に含みうる。常に一件処理とは見積もらない。
- OrderLine は通常、一 order 当たり十数件、StockLevel は二十 order 分。ただし物理候補・初期番号範囲の差をそのまま計数する。

既存版の二分探索は `V/dsg.py:645`、隣接構築は `:641`。範囲検索・到達可能性は新実装であり、上記は**設計上の計算量**である。

## 3. CC ごとの改修点

| 面 | Silo | SI | MOCC |
|---|---|---|---|
| scan | 生 tuple 候補→read set、既読・自 write 再利用。`:291` | snapshot 版選択、deleted/null を除外。`:417` | Silo 類似だが read の absent で abort。`:375`・`:341` |
| insert | absent/locked tuple を先に公開。`:70` | inflight 初版を公開。`:301` | absent tuple を公開。`:486` |
| delete | writePhase で除去、epoch GC。`:668` | tombstone version を install、commit で木から除去。`:348`・`:513` | lock/validation を経て除去、GC。`:533`・`:1180` |
| abort | INSERT 即時 delete。`:27` | INSERT 即時 delete、版を aborted にする。`:578` | INSERT 即時 delete、CLL/RLL 処理。`:1059` |
| phantom validation | `node_map_` 比較 `:477`、callback `:733` | 比較 `:485`、callback `:685` | 比較 `:1042`、callback `:1286` |
| 現行 trace | v2 `:594`、E `:698` | v1 `:539`、E なし | v2 `:1134`、E `:1204` |
| TPC-C 固有の主改修 | 表付き出力、S/Q、寿命修正 | 左記＋消された read の保存、deleted 観測の区別、新 frame | 表付き出力、S/Q、寿命修正、watermark 非使用 |

表中の `:行` は各 `CC/cc/<cc>/transaction.cc`。

**node_map_ の存在は、完全な述語読みの証明ではない。** 公開済み未 commit tuple が commit して live になるとき、必ず木の構造版が変わるとは限らない。CC の可視性処理と node validation を合わせて検査する必要がある。Silo の INSERT commit は tidword の store（`:663`）、SI は version status の store（`:517`）である。

**MOCC watermark は使用不可。** 先頭8 byte の上書きは Warehouse/Customer 等の ID を壊すほか、INSERT/DELETE は明示 abort になる。`CC/cc/mocc/transaction.cc:78`・`:1165`・`:1173`。TPC-C は native 版の DSG と既存の proof-surface 要件を用い、YCSB watermark の検出力を TPC-C へ転用したと主張しない。

**SI で G2 が出ても、検査失敗を補正しない。** native SI は anti-dependency 検査をしない（`CC/cc/si/transaction.cc:614`）。したがって TPC-C の全実行が直列化可能という保証はない。ただし「この五取引の特定設定で G2 を再現できる」ことは本調査では未実証。TPC-C の競合構造で実際に成立する schedule は焦点走で確かめる。合成 write-skew は決定的な検出試験に使う。

### 編集面と pin 前進

| 改修 | hook の三ファイル内か | 行き先 |
|---|---|---|
| Silo/MOCC transaction.cc の計装 | 内 | 本採用 trace-hook は `izanagi-trace` |
| SI transaction.cc | 外 | `izanagi-trace` |
| trace.hh、tpcc.hh、初期キー出力 | 外 | TRACE 計装は `izanagi-trace` |
| scan callback/wrapper、transaction header の TRACE fields | 外 | 必要分だけ `izanagi-trace` |
| abort 寿命・公開後 rollback の本体修正 | ファイルにより内外 | TRACE 外の本体修正として分離し、trace 枝へ取り込む |
| broken phantom 等の control | repo の patches | out-of-tree patch を維持 |
| verifier、pipeline、TPC-C reporter | CCBench 三ファイル制限の対象外 | superproject |

根拠：`hooks/guard_write.py:44`、必読 `decisions-excerpt.md:25`・`:54`。

pin 前進は一作業項目として数える。候補 OID の材料を揃え、人間による公開後に取得可能性を確認し、gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` を同時更新する。過去の e9e477ca 承認を新候補へ流用しない。`docs/decisions.md:67618`。

D2184 のとおり pin 前進は admission policy や既存 lock に波及する。旧 YCSB **判定・出力**を保存できても、旧 campaign の新 main 上での再開まで不変とは言えない。新 TPC-C 系列に必要な整合を行い、旧成果物は旧 checkout とともに保存する。`docs/decisions.md:69182`。

## 4. 検出力を確かめる正例・負例

以下は**試験案と期待結果**であり、実行結果ではない。

既存 control は read validation を意図的に無効化する patch と、手書き trace の G2・lost update・混合辺 cycle である。根拠：`patches/broken-silo-norw-validation.patch:5`、`orchestrator/tests/test_verifier.py:201`・`:227`・`:246`。この型を拡張する。

### 4.1 段 1

| 例 | schedule／壊し方 | 期待する辺・結果 |
|---|---|---|
| 表欠落による偽警報 | A は Warehouse(k) の genesis を読み Item(k) を更新、B は Warehouse(k) を更新 | 正しくは A→B の rw のみ。表を落とすと A 自身の Item 書込みを同一キー版列へ混ぜ、A→B の ww と B→A の rw を作りうる。 |
| 表欠落による見逃し | A が Warehouse(k) の v を書く。B がその v と Item(j) genesis を読み Warehouse(k) を更新。A は Item(j) genesis も読む。C が Item(k) に同じ v を書く | 本来 A→B の wr、A→B 等の関係を含む fixture を、別キーへの逆辺で cycle にする。表を落とすと `(k,v)` producer 重複や取り違えが起きる。**安全な parser は偽 green でなく indeterminate に落とすことも確認する。** |
| 決定的な表欠落見逃し | A の同一 raw key に対する二表の W を、表なしで一要素へ上書きする変異 | 失われた表の producer からの wr と、その表の successor への rw が消える。fixture では残す側・消す側を入れ替え、cycle の消失を検出する。 |
| broken read validation | 二取引が District の同じ版を読み、順に更新して両方 commit | A→B の ww、B→A の rw。既存 lost-update 型の G2。 |
| 正しい直列 schedule | A が INSERT、B がその版を read/update | A→B の wr/ww のみ。graph は green。 |
| genesis の誤用 | 初期不存在キーへ A が INSERT、B がそのキーの `(1,0)` を live として読む | 存在履歴不整合で indeterminate。cycle 検出例とは数えない。 |
| SI の読み消去 | 読み保存 buffer を無効化し、read→update の R を消す | R が作る rw を含む既知 cycle fixture が消える変異を検出。 |
| 終了境界 | commit 成功直後に quit を立てる | C=counter。旧順序へ戻す変異は件数不一致で拒否。cycle 例ではない。 |

表欠落だけで「必ず偽 green」と決めつけない。現行には version duplicate/orphan の拒否があるため、**辺を間違えることと、最終 certified が誤って真になることを分けて期待値を置く**。`V/dsg.py:357`、`V/model.py:459`。

手書きの最小 G2 は次でよい。ヘッダの tx_type は例示値であり、業務全体を再現する fixture ではない。

```text
C 0 0 1 1 1 1 0 0 1
R 0 0 0000000000000001 1 0
W 0 9 0000000000000001 U 1 1
E 0
C 1 1 1 2 1 1 0 0 2
R 1 9 0000000000000001 1 0
W 1 0 0000000000000001 U 1 2
E 1
```

表0の R により `0→1 rw`、表9の R により `1→0 rw`。両表のキーが等しくても二辺を正しく保持する。synthetic 初期状態では両キーを genesis に置く。

### 4.2 段 2

| 例 | schedule／壊し方 | 期待する辺・結果 |
|---|---|---|
| INSERT phantom の決定的 fixture | S が OrderSecondary の範囲を空と読み x を更新。I が範囲内へ INSERT し、x の genesis を読む | S→I の predicate rw と I→S の point rw。G2。 |
| 実 CC の phantom control | scan 後に他取引が範囲内へ INSERT。`node_map_` の commit 検証を無効化し、逆向きの point 依存も作る | 上記二辺で赤。単に validation を外すだけでは異常 schedule が成立した証拠にならない。 |
| DELETE phantom | D が初期キー k を DELETE。S は範囲で k 不在を観測し、D が読んだ x を更新 | D→S の predicate wr と D→S の point rw だけなら非巡回。逆向きの別依存を加えた版を赤、加えない版を緑にする。 |
| 不在が一意化できる例 | I→…→S が点依存で既知、k は I により挿入・D により削除、S には見えない | dead 側 D→S を採用。逆向き到達関係がある版で矛盾を検出。 |
| 不在が決まらない例 | I/D と S の間に決定材料がない | indeterminate。恣意的に片側を選ぶ変異を検出。 |
| limit の偽依存防止 | live key a を limit=1 で返し、後方 b へ別取引が INSERT | b からの predicate 辺はない。全指定範囲へ広げる verifier 変異が偽 cycle を作ることを検出。 |
| 物理上限で可視行欠落 | 最初の物理候補が未 commit、後ろに初期 live key、返却0・物理1・limit1 | 全域空と解釈せず indeterminate。返却件数だけで完走判定する変異を検出。 |
| 初期キーの取りこぼし | initial manifest にある OrderLine を scan が落とす | 不存在を説明する DELETE がなければ拒否。W-only 候補索引の変異を検出。 |
| 正常対照 | 同じ fixture を完全に直列実行し、scan が正しい集合を返す | producer→reader と reader→後続 writer の前向き辺のみ。graph green。 |

limit を無視して多く読む変更は、それだけで直列化不能にはならない。S/Q と件数仕様の不一致を検出する試験と、真の cycle を作る試験を区別する。上限実装の根拠は `CC/include/masstree_wrapper.hh:287`。

実 TPC-C の焦点例としては、OrderStatus と NewOrder を使い、Customer の更新を行う Payment を第三取引に置く案がある。

```text
OrderStatus S --predicate rw--> NewOrder N
NewOrder N   --rw(Customer)--> Payment P
Payment P    --wr(Customer)--> OrderStatus S
```

ただし現行 OrderStatus は最小 order を limit=1 で読むため、**通常の末尾 INSERT は実効 prefix 外になり、この cycle は成立しない場合が多い**。範囲内 INSERT となる初期状態・キーを持つ CC API fixture でまず確定させる。通常 mix だけで出ると約束しない。根拠：`TP/tpcc_tx_orderstatus.hh:28`、`TP/tpcc_tx_neworder.hh:36`・`:114`、`TP/tpcc_tx_payment.hh:188`。

## 5. 工数と trace 容量の見積り

### 5.1 実装単位と dev-wave 数

以下は**推測による工数**。一単位は Codex author 一本が差分・関連 fixture を所有する範囲。

| 実装単位 | 数 |
|---|---:|
| 公開 INSERT の rollback・退役・回収条件修正：CC ごと | 3 |
| 共通 v3 helper、取引型 context、counter 境界 | 1 |
| 段1 emitter：Silo/MOCC、SI 読み保存 | 2 |
| 表付き model/parser/compact DSG、TPC-C 構造化出力 | 2 |
| 段1 pipeline・mix 設定・既存 X/P 要件との統合 | 1 |
| 段2 S/Q producer：三 CC と wrapper 境界 | 3 |
| 初期キー出力と完全性の読取り | 1 |
| predicate DSG、存在履歴、選言処理 | 2 |
| 段2 control・pipeline 統合 | 1 |
| 新 pin 候補の材料、公開後の三点更新・identity 整合 | 1 |
| **合計** | **17 単位** |

根拠となる変更面は §1〜3 のアンカー。SI の X/P 証拠面が現行契約で表現できず独立設計を要する場合、**追加1〜2単位**を見込む。これは現行 gate の存在（`V/model.py:77`）からの推測であり、承認済み変更ではない。

推奨分割は **5 dev-wave**。

1. INSERT 寿命・rollback の本体修正。
2. 段1の形式・emitter・verifier。
3. 段1の統合・検出力・必要な証拠面。
4. 段2の観測・predicate verifier・control。
5. 全体受入と pin 前進。

段1を先に公開・pin して使うなら pin 手続きを二回に分け、**18単位・6 wave 程度**。review/fix の往復や人間の公開待ちは author 数へ含めていない。2 node 時間以上の実験投入は別途見積り確認が必要である。必読裁定控えの項4。

### 5.2 操作数

`n`=NewOrder の品目数、`u_i`=distinct Item 数、`u_s`=distinct Stock 数、`g`=Delivery の対象 district 数、`L`=OrderLine の返却数、`u`=StockLevel が読む distinct Stock 数。

| 取引 | R | W | S | Q の平常時件数 | 出所 |
|---|---:|---:|---:|---:|---|
| NewOrder | `3+u_i+u_s ≤ 3+2n` | `4+u_s+n ≤ 4+2n` | 0 | 0 | コード：`TP/tpcc_tx_neworder.hh:295`・`:308`・`:314` |
| Payment | 3 | 4 | 0 | 0 | コード：`TP/tpcc_tx_payment.hh:242`・`:259`・`:263` |
| Delivery | `3g+L` | `3g+L` | `10+g` | `g+L` | コード：`TP/tpcc_tx_delivery.hh:199`・`:207`・`:215` |
| OrderStatus | `3+L` | 0 | 2 | `1+L` | コード：`TP/tpcc_tx_orderstatus.hh:106`・`:113`・`:118`・`:130` |
| StockLevel | `1+L+u` | 0 | 1 | `L` | コード：`TP/tpcc_tx_stocklevel.hh:42`・`:50`・`:67` |

R/W は重複キーを集約した履歴を前提とする。SI は提案した読み保存後の数であり、現行 emitter の数ではない。Q は物理候補を数えるため、不可視候補があれば表の平常時件数より増える。

`n` は5〜15、平均10。Item の重複を禁止するコードは無効化されているので、NewOrder を常に R=23/W=24 と断定できない。`TP/tpcc_query.hh:98`・`:101`。

**初期 OrderLine は平均11行。** loader は `ol_num=1` から `O_OL_CNT+1` **以下**まで生成する。一方実行中 NewOrder は `0`〜`n−1`。scan は `ol_num=1` を下限にしているので、生成元によって返却件数が異なり、隣接 order の line 0 が上限未満へ入る場合もある。`TP/tpcc_initializer.hh:259`・`:279`、`TP/tpcc_tx_neworder.hh:314`、`TP/tpcc_tx_delivery.hh:133`。

これは容量にも認定対象の意味にも関わる。今回の認定は**実コードの操作履歴の直列化可能性**であり、TPC-C 仕様準拠を同時に証明するものではない。

### 5.3 一行の byte 数

ASCII、空白一つ、LF 一つ。`d(x)` は十進桁数、k は key の hex 長。

```text
R = 7 + d(txid) + d(table) + k + d(epoch) + d(tid)
W = 9 + d(txid) + d(table) + k + d(epoch) + d(tid)
E = 3 + d(txid)
```

v3 C は tag・区切り・LF が11 byte、残り九 field の桁数を加える。旧形式が十進数と hex を出す根拠は `CC/include/trace.hh:67`・`:84`。

以下の予算用計算では `txid≤7桁、thid≤2桁、epoch≤3桁、tid≤8桁、table≤2桁` を置く。**実際の平均桁数ではなく、指定桁幅内の容量見積り**である。genesis の R はこれより短い。

| 行 | 8-byte key | 16-byte key | 出所 |
|---|---:|---:|---|
| R | ≤43 B | ≤59 B | 提案形式から計算 |
| W | ≤45 B | ≤61 B | 同上 |
| S | 約86 B | 約134 B | 提案形式、scan_id 2桁・件数3桁・三つのキー field を仮定 |
| Q | 約48 B | 約64 B | 提案形式、state 1文字・scan_id 2桁 |
| C+E | 約46〜53 B | 同左 | 取引別 R/W/S/Q 件数の桁数から計算 |

### 5.4 一 commit 当たり・百万 commit 当たり

例示条件は、NewOrder の重複なしで n=10、Delivery は全10 district を処理し L=110、OrderStatus L=11、StockLevel L=220/u=220、不可視物理候補なし。**平均行数に上記の予算用行幅を掛けた試算**であり、実測容量でも全履歴の上限でもない。

| 取引 | R/W/S/Q | B/commit | 出所 |
|---|---|---:|---|
| NewOrder | 23 / 24 / 0 / 0 | 約2,133 | コードの操作数＋形式から試算。OrderSecondary の W 一行分に16 B追加 |
| Payment | 3 / 4 / 0 / 0 | 約355 | 同上 |
| Delivery | 140 / 140 / 20 / 120 | 約19,853 | 初期ロード中心の例から試算 |
| OrderStatus | 14 / 0 / 2 / 12 | 約1,478 | 同上。OrderSecondary の長い R/S/Q を加算 |
| StockLevel | 441 / 0 / 1 / 220 | 約29,659 | 同上。Stock 重複を無視した予算値 |

既定の生成比率は **NewOrder 45%、Payment 43%、残り各4%**。`TP/tpcc_common.hh:7`、`TP/tpcc_query.hh:57`。

| 対象 | 平均容量の試算 | 百万 commit | 出所 |
|---|---:|---:|---|
| 段1、45:43 を正規化 | 約1,264 B/commit | 約1.26 GB | 上表の加重平均 |
| 段2、45:43:4:4:4 | 約3,152 B/commit | 約3.15 GB | 上表の加重平均 |
| 段2初期キー一覧 | 約8.6 MB/warehouse | commit 数によらない加算 | NewOrder 9,000、OrderSecondary 30,000、OrderLine 平均330,000キーを G 行として試算 |

初期 G 行を `G <table> <key>` とすれば、二桁表番号を予算化して8-byte key は22 B、16-byte key は38 B。件数・終端の小さな overhead は別。初期件数の根拠は `TP/tpcc_common.hh:24`、`TP/tpcc_initializer.hh:279`・`:283`・`:407`。

生成比率と committed 比率は同じとは限らない。NewOrder は1%の意図的 NOT_FOUND を生成し、abort ごとに query を再生成する。上表は要求された既定比率での試算であり、実 run は取引別 commit counter で再加重する。`TP/tpcc_query.hh:122`、`CC/include/tpcc.hh:48`・`:99`・`:112`。

### 5.5 throughput と verifier 時間

今回参照した repo 内記録からは、**この三 CC の TPC-C 容量換算に採用できる throughput 実測は見つからなかった**。したがって秒間容量は出さず、百万 commit 単位にする。

親の記憶した値は一部訂正が必要である。

| 記録 | 値・意味 | 出所 |
|---|---|---|
| 旧 read-heavy 記録 | 16.83M〜17.19M commit、1346.9〜1465.6秒。ただし benchmark・trace I/O・検査等の混合区間 | `output/insights/2026-09-02_b10-trace-truncation/README.md:181`・`:207` |
| 現行 packed verifier の read-heavy 3秒 trace | 16,819,316取引、291,168,798辺、検査433秒 | `output/insights/2026-09-20/verifier-capacity/README.md:46` |
| 同 balanced 10秒 trace | 14,748,197取引、215,144,539辺、478秒 | 同 `:41` |
| 同 write-heavy 10秒 trace | 8,323,838取引、84,993,314辺、297秒 | 同 `:40` |

したがって「verifier 一回23分」を現行の単価として使わない。

既存 YCSB の上表を単純に百万取引へ正規化すると約26〜36秒。ただし TPC-C は操作数・キー数・述語処理が違う。YCSB が約10 R/W 行/取引である記録（同 README `:17`・`:18`）から、操作数だけ比例させると次の**粗い試算**になる。

| 対象 | 百万 commit の時間表現 | 出所・限界 |
|---|---|---|
| 段1 | 約90〜100秒級 | 平均約27.45 R/W 行/commit と balanced/write-heavy の単価から試算。大量の新規キー生成の差は未較正 |
| 段2 | 点処理等だけで約170〜240秒級 **＋述語キー列挙・到達可能性** | 平均約53.56 R/W、14.08 Q、0.92 S/commit の例から試算 |
| 段2の認定全体 | 現時点では信頼できる秒数上限なし | `Σk` と不在選言数 a が支配しうる。§2.6 の最悪計算量を参照 |

段2の到達可能性を含む所要は、小さな保全 trace を用いた後続計測が必要である。上記の試算を、そのまま計算予算承認の確定値には使わない。

## 総括

- 段1は、TPC-C 専用 v3 frame、表付きキー、SI の読み保存、TRACE 側の完全 commit 計数を推奨する。
- YCSB の v1/v2 入力・既存出力を保存し、TPC-C の表なし入力を黙認しない。
- INSERT の公開後 rollback 漏れと abort 即時解放は、trace 計装と分けて本体修正する。
- 段2は S＋scan 別 Q＋三つの scan 対象表の初期キー集合を使う。
- 不在の選言は既存依存で一意化できる場合だけ解き、残りは indeterminate とする。
- 物理上限で可視行を取りこぼした scan を、完全な述語読みとして認定しない。
- MOCC watermark は TPC-C に使わず、SI の G2 は正しく拒否する。
- 工数は概ね17 author単位・5 wave、容量例は段1約1.26 GB、段2約3.15 GB／百万 commit。
- 現行 X/P 要件と pin 前進の波及は残る。cycle 不在だけを certified と呼ばない。

**親が段3で攻撃させるべき未決点：** ① 三 CC の公開 tuple の安全な退役条件、特に Silo の lock 待機と MOCC の CLL/RLL、② 選言を到達可能性で絞る処理の健全性と計算量、③ 物理 LIMIT と可視行 LIMIT の認定射程、④ SI の X/P 証拠面を既存契約を緩めず成立させる方法、⑤ 初期／実行時 OrderLine の番号差を維持した容量・範囲計算、⑥ 全五取引が実際に作れる G2 schedule と API 合成例の区別。