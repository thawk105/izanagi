# TPC-C を trace verifier で直列化可能性まで認定するための設計と工数見積り — 段 1 (NewOrder / Payment) は表識別子・v3 frame・trace build 限定の commit 計数で閉じ、段 2 (全 5 取引) は範囲読みを述語読みとして扱うが「見えなかった key が挿入前か削除後か」を直接の証拠で決める仕組みが要る。認定対象は silo (現 pin で X/P あり) と mocc (X/P 計装の着地後)、si は検出専用 (dev-wave precheck、実装差分ゼロ、2026-09-21)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
台帳 ID 未起票 (依頼文が「本題の調査だけ」と明記、主題 slug)。dev-wave precheck: 段 2 plan (Codex read-only) 1 本、段 3 敵対相談 (Codex read-only) 2 本、段 4 で「コードは実装しない」と裁定、docs は親、段 6 read-only review 1 本 + 焦点再レビュー。
branch `dev-wave-tpcc-trace-design`、起点 local main `36fb14a3d` (開始 gate rc 0、2026-09-21 21:4x JST)、CCBench submodule `e9e477ca`。job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-tpcc-trace-design` (prompt・待ち手・log)。
段 1〜6 の全文は `verbatim/` (`s1-brief.md` / `s2-plan.md` / `s3-consult-A.md` / `s3-consult-B.md` / `s4-ruling.md` / `s6-review.md` / `s6-focus.md`)。本文は段 4 裁定で訂正した後の設計 (v2) で、草案 (`s2-plan.md`) と食い違う箇所は本文が正しい。

**性質の断り:** すべて静的調査 (ソースを読む・grep) による設計と試算である。build・binary 実行・pytest・性能測定はしていない (§10)。以下の新形式・改修・試験・工数は提案であり、実装済み・実証済みを意味しない。

## 1. 依頼と結論

依頼 (VLDB 方針の裁定控え `rulings-inbox/2026-09-21-vldb-direction-verdicts.md` 項 2 で TPC-C を必須にしたことを受けて): CCBench の TPC-C を izanagi の trace verifier で直列化可能性まで認定できるようにする設計と工数見積り。返すもの = (1) 段 1 (NewOrder / Payment) の trace 形式と verifier の意味、(2) 段 2 (全 5 取引) の範囲読みと phantom 依存、(3) silo・si・mocc ごとの改修点、(4) 検出力を確かめる正例・負例、(5) 工数と trace 容量。段 1 / 段 2 の分割は、控えでは「TPC-C 必須というユーザー意向に対する親の改訂推奨 (明示確認は未取得)」であり、確定裁定ではない (段 3 所見 A10 で訂正)。

結論:

1. **段 1 は既存の枠組みの延長で閉じる。** 必要なのは、R/W 行の表識別子 (3 CC の read / write set 要素が既に `storage_` を持つ)、TPC-C 専用の v3 frame、trace build だけ commit 後の停止判定より先に counter を足す修正、pipeline の allowlist の拡張。表識別子は「あると良い」ではなく必須: NewOrder 表と Order 表は同じ `(w_id, 0, d_id, o_id)` の 8 byte を key に使い、NewOrder 取引が両方へ挿入する (§3.2)。
2. **段 2 は新しい意味論が要る。** 範囲読み (`tx.scan`) を Adya の述語読みとして扱い、scan ごとの範囲・件数上限・物理候補を trace に出す。難所は「範囲内で返らなかった key を、読み手は挿入前として見たのか削除後として見たのか」で、現行の trace からは決まらない。**依存グラフに cycle ができない側を選ぶ規則は、実在する G2 を隠して偽認定する** (段 3 レンズ A の反例、§4.4)。観測版は直接の証拠 (scan が触れた物理候補ごとの観測記録を主に、silo / mocc では走査区間を挟む trace build 限定の通し番号) で決め、決まらなければ indeterminate にする。ただし選言が生じるのは挿入と削除の両方を受ける NewOrder 表だけで、Masstree の走査保証が証明されるまで Delivery を含む走は indeterminate に倒れうる (§4.4)。
3. **認定まで届く CC は現状 silo だけ。** verifier の certified は X/P の証拠面 (lock 被覆 X 行と permutation P 行の emitter) を要求し (`orchestrator/verifier/model.py:77-82`, `:450-465`)、emitter は silo にしか無い。mocc は稼働中の [T-2844] wave が X/P 計装を CCBench の候補 commit として作成中で、その pin 前進の後に対象になる。si は X/P に当たる証拠契約が無く、さらに **現行 si の trace (v1 形式) は YCSB でも parser が拒否する** (`orchestrator/verifier/parse.py:323-326`) ので、今はどの workload でも検証できない。TPC-C では si を「非直列化の検出専用」にするのが推奨。
4. **工数は必須 11 実装単位 (Codex author 1 本の担当範囲) + si 任意 1、暫定 6 wave 程度。** 実装 wave の実績 (impl 7 本平均 169.6 分、118.5〜214.8 分) で約 12〜21 時間の wave 所要に、CCBench 候補 commit の push (人間手番) 待ちが加わる。17 単位 / 5 wave という草案の数字は確定見積りではない (§7)。
5. **trace 容量は 100 万 commit あたり段 1 約 1.37 GB、全 5 取引約 3.15 GB (試算)。** 検索した記録からは換算に使える TPC-C の throughput 実測が見つからなかったので、秒あたりは出せない。最初の計算投入は「小さい 1 走で throughput と trace 量を測る」にし、同じタスクの build・検査・再試行を含む合計 node 時間が 2 node 時間以上なら投入前に確認を取る (未満なら確認不要、§7.4)。

## 2. 一次資料で確かめた現状 (依頼の前提の照合)

| 依頼の前提 | 照合結果 | 根拠 |
|---|---|---|
| verifier は YCSB の点読み・点書きの G2 だけを扱う | **正しい。** 版は key ごとの (epoch, tid) 辞書順、key は hex 文字列だけで束ね、ww / wr / rw 辺を張る。op (`U`/`I`/`D`) は辺の構築に使わない | `orchestrator/verifier/dsg.py:344-370`, `:645-679`、`model.py:315-352` |
| `orchestrator/pipeline.py` が ycsb_ 以外を検証前に拒否 | **path が違う。** 実体は `orchestrator/campaign/pipeline.py:434-437` (`ycsb_` で始まらない binary を `_TraceWitnessUnsupportedWorkload` で拒否) | 同左、D295 |
| silo の R/W 行は key だけで表識別子を持たない | **正しい (silo・si・mocc の 3 つとも)。** ただし read / write set の要素は `storage_` を持つ | `external/ccbench/include/trace.hh:17-24`, `:84-97`、`include/op_element.hh:17-19` |
| TPC-C の abort は app 層で起きる | **正しい。** 取引関数が false を返すと `tx.status_ = aborted` を代入し (tpcc.hh:57-87)、`tx.abort()` と abort 計数へ進む (:89-97)。abort した取引は writePhase に届かず trace に出ない | `include/tpcc.hh:44-115`、D48 |
| NewOrder / Payment は点操作と insert だけ | **ほぼ正しい。** ただし Payment と OrderStatus の姓検索は CC を通らず `CustomerSecondary` 索引を直接読む。索引の書き手は初期ロードだけで、実行中は不変 (§3.6) | `include/tpcc/tpcc_tx_payment.hh:114-115`, `tpcc_tx_orderstatus.hh:93`、`tpcc_initializer.hh:365`, `:380` |
| Delivery / OrderStatus / StockLevel は `tx.scan` を使う | **正しい。** 5 箇所 (§4.6)。件数上限 1 の scan が 2 つある | `tpcc_tx_delivery.hh:45`, `:135`、`tpcc_tx_orderstatus.hh:30`, `:72`、`tpcc_tx_stocklevel.hh:50` |
| trace を出せるのは silo・si・mocc | **出力はするが、検証できるのは silo と mocc だけ。** si は v1 形式で parser が拒否 | `cc/si/transaction.cc:539-555`、`parse.py:323-326` |

既定の取引比率は NewOrder 45%・Payment 43%・OrderStatus / Delivery / StockLevel 各 4%、既定倉庫数は 1 (`include/tpcc/tpcc_common.hh:6-13`)。

## 3. 段 1: NewOrder / Payment の trace 形式と verifier の意味

### 3.1 v3 frame (TPC-C 専用)

```text
C <txid> <thid> <epoch> <tid> <nR> <nW> <nS> <nQ> <tx_type>
R <txid> <table> <key_hex> <ver_epoch> <ver_tid>
W <txid> <table> <key_hex> <U|I|D> <epoch> <tid>
S ... / Q ...   (段 2、§4.1)
E <txid>
```

- C 行の token 数で v2 (7) と v3 (10) を区別する。**v1 (5) の拒否は維持する** (草案の「v1 / v2 の入力受理を維持」は現行の受理集合を広げるので不採用、段 3 所見 B2)。YCSB の v2 の判定・出力 bytes は変えない。1 run の中で schema を固定し、v2 と v3 の混在は拒否する。
- `table` は `Storage` 列挙の整数 (TPC-C は Warehouse=0 … Stock=10、`tpcc_tables.hh:16-28`)。key の hex に混ぜず別 field にする。
- `tx_type` は NewOrder=1 … StockLevel=5 (`tpcc_query.hh:19` 付近の列挙)。`tpcc.hh` の `tx.begin()` の後に trace build 専用の状態へ置き、commit frame で出す。anomaly を「どの取引種別のどの表の key で壊れたか」まで返すため (規律 3)。
- 新しい helper・状態はすべて `#if TRACE` の中に置く (規律 1、D14)。旧 helper (`emit_commit` 等) は YCSB 用に残す。
- X 行 (lock 被覆違反) も TPC-C では表を持たせる。

verifier 側の変更点 (草案 §1.1 の表を採用):

| 変更先 | 変更 |
|---|---|
| `model.py:315` `Read` / `:321` `Write` / `:328` `Txn` | 識別子を `(table, key_hex)` に。Txn に schema と tx_type を持たせる |
| `parse.py:296` `_parse_file` とその C/R/W 分岐 | v3 の分岐、表・取引種別・宣言件数・終端の厳格検査。未知 tag・表番号の欠落は拒否 (indeterminate) |
| `parse.py` の compact 経路 (`_ParsedFileColumns`・`_txn_from_columns`・`_parse_file_to_columns`) | token interning を `(table, key)` 単位に。**object 経路だけ直して compact 経路を残さない** |
| `dsg.py:344` `_build`、`:388` `_build_compact_packed`、`:492` `_build_compact_tuple`、`:645`・`:671` の辺構築 | producer・key ごとの版列・辺照合を表込みに |
| `dsg.py:774` `_reasons`、`model.py:353` `EdgeReason` | 表・取引種別を復元して anomaly に載せる |

`orchestrator/verifier/report.py` は凍結証拠が現行 bytes を要求する (D295 の却下理由) ので編集しない。TPC-C の構造化出力は旧出力を保つ条件分岐か別の出力点に置く (独立 reporter は必須ではない、所見 B6)。

### 3.2 表識別子が無いと実際に衝突する key

通常の生成域 (ID の overflow 前) で、表なしの key bytes が一致する組 (草案 §1.2、親が 2 組を実コードで確認):

| 衝突する表の組 | 条件 | 根拠 |
|---|---|---|
| **NewOrder / Order** | 同じ `(w, d, o_id)`。NewOrder 取引が両方へ挿入し、Delivery が片方を削除・片方を更新する | `tpcc_tables.hh:257-262`, `:284-289` (親が確認) |
| **Warehouse / Item** | `W_ID = I_ID` (例: 両方 1) | `:44-47`, `:356-359` (親が確認) |
| District / Item | `I_ID = 256 × D_W_ID + D_ID` (例: District(1,1) と Item(257)) | `:69`, `:356` |
| Warehouse / District | `W_ID = 256 × D_W_ID + D_ID`。257 倉庫以上で実在 | `:44`, `:69` |
| Customer / Order、Customer / NewOrder | 同じ `(w, d, c_id = o_id)` | `:118`, `:257`, `:284` |
| 初期 History / Warehouse・District・Item | 初期 History の counter が一致する場合 (実行中の History は別 bit で衝突しない) | `:221`、`tpcc_initializer.hh:403`, `:463` |

表なしでは別の行の版が 1 本の版列に混ざる。silo の tid は key を跨いで一意ではないので「version dup」の integrity 違反 (indeterminate) になることが多いが、辺の取り違えは偽警報にも偽認定にもなりうる。表識別子で閉じる。

### 3.3 insert・genesis・存在の意味

- 初期ロード済みの key は genesis `(1,0)` から存在する。初期に無く最初の committed write が INSERT の key は、INSERT より前が「挿入前 (unborn)」。genesis の値を持つとは解釈しない。
- DELETE は不存在の版を作る。R 行がこの版を「存在する値」として読むのは不整合 (indeterminate)。
- W 行の op=`I` (INSERT) と、独立 tag の `I` 行 (write intent 違反) は別物 (`parse.py:393-394`)。
- abort した取引の挿入は committed の版列に入らない。abort した挿入の版を読んだ R は既存の orphan read として indeterminate になる。

### 3.4 si の読みは native set から出せない

si の update / delete は read set から当該要素を消す (update `cc/si/transaction.cc:239-247`、delete `:361-365`、親が確認)。Payment の Warehouse / District / Customer の read→update では、現行の commit 時 emitter から R 行が消え、rw 辺が落ちる。逆に `read_internal()` は deleted 版も read set に登録する (`:153-164`) ので、成功した読みをすべて live の R にするのも誤り。si を使うなら、読みを「live / deleted / 不可視 / 自己版」に区別して trace build 専用の履歴へ値で保存する (所見 A5)。silo / mocc の update は read set を消さない。

### 3.5 commit 計数 (witness) と allowlist

D295 の不一致は、`tpcc.hh` が commit 成功の後で `quit_` を見て counter 加算の前に return することが原因 (`tpcc.hh:102-111`)。最小修正:

```cpp
#if !TRACE
    if (loadAcquire(tx.quit_)) return;
#endif
    tx.result_->local_commit_counts_++;
    tx.result_->local_commit_counts_per_tx_[get_tx_type(query.type)]++;
```

- trace build は成功 commit を必ず 1 回数え、性能 build (TRACE=0) の計数の意味は今のまま。witness は C 行数との**完全一致を保ち、許容幅を作らない** (± スレッド数を許すと、末尾取引や file 丸ごとの欠落と区別できなくなる)。
- app 層 abort と commit 失敗は加算に届かない。abort した取引は C 行を出さない。したがって app 層 abort は verifier 側で数える必要がなく、abort 計数 (`local_abort_counts_per_tx_`) は診断値に留まる。
- 検出限界は D295 と同じ: trace と counter の同時欠落、個数を保つ置換、C を残した R/W の欠落 (frame の領分) は捕えない。
- `orchestrator/campaign/pipeline.py:434` の allowlist は、v3・表識別・この計数修正が揃った tpcc binary に限って広げる。段 1 の走行は既存 flag で OrderStatus / Delivery / StockLevel を 0% にでき (閾値が 0 になる、`tpcc_query.hh:57-64`)、そのとき比率は **NewOrder 57% : Payment 43%** になる (45 : 43 の正規化は整数 % の flag では表せない、所見 B7)。
- certified には既存の X/P 証拠面の要件も要る (§5.3)。

### 3.6 Payment / OrderStatus の姓検索

`get_customer_key_by_last_name` は CC を通らず `CustomerSecondary` を直接読む (`tpcc_tx_payment.hh:106-126`)。この索引は初期ロードで作られ (`tpcc_initializer.hh:362-380`)、ロード worker の join 後は読まれるだけで、実行中の書き手は無い。したがって索引の読みは依存辺を生まず、trace の追加は要らない。選んだ Customer 行は通常の CC 読み (`:165`) を通る。**この根拠は現行 5 取引に限る** (CustomerSecondary を実行中に更新する改修や合成が入れば無効)。

## 4. 段 2: 全 5 取引 — 範囲読みを述語読みとして扱い phantom 依存を検出する

### 4.1 scan ごとの観測 (S 行・Q 行)

```text
S <txid> <scan_id> <table> <lo_hex> <lo_excl> <hi_hex> <hi_excl> <limit> <physical_count> <returned_count> <last_physical_key> <stop>
Q <txid> <scan_id> <table> <key_hex> <state> <ver_epoch> <ver_tid>
```

- Q は Masstree が返した**物理候補ごと**に 1 行。`state` は有限集合: 返却した live 版 / tombstone を観測 (版つき) / 不可視 / 自己版 / 既読の再利用。
- commit 時の read set からは再構成できない。同じ取引の点読み・別の scan・既読や自己 write の再利用が混ざるため (silo `cc/silo/transaction.cc:304-317`、si `:429-448`、mocc `:388-402`)。
- scan は read phase で起きるので、S / Q は scan 中に trace build 専用の buffer へ**値で**コピーし (key・版・状態。`string_view` や tuple / version / body のポインタは持ち越さない)、成功 commit の frame の中でだけ出す。abort と次の begin で消す。型・container・include・記録呼出し・clear はすべて `#if TRACE` の中 (所見 B1)。mocc の RLL は retry に使うので trace buffer と一緒に消さない。
- 物理末尾は scan buffer の順序から採る。silo / mocc は既読要素を先に result に入れ新規読みを後に足すので、`result.back()` は物理末尾を表さない (所見 B1)。

### 4.2 件数上限の認定契約

Masstree の wrapper は可視性を見ずに物理候補の件数で止まり、CC がその後で不存在・不可視を除く (`include/masstree_wrapper.hh:287-288`、si `:448-451`、silo `:317`)。

- 上限に達しなかった scan の観測範囲は指定範囲全体。
- 上限に達した scan の観測範囲は [下限, 最後の物理候補]。最後の返却 key ではない。
- **物理候補が上限を埋め、返却件数が上限未満の scan は indeterminate** (未 commit の候補で上限が埋まり、後ろの live 行を見ていない。「先頭の可視行を 1 件取った」とは言えない)。これは G2 の検出ではなく認定範囲の拒否で、理由を分けて返す。
- 上限に達して live の a を返した scan では、a より後ろへの INSERT をこの scan の依存にしない (全範囲扱いは偽警報)。

### 4.3 初期キー集合

W 行だけから範囲内の key を列挙すると、初期ロード済みで実行中に一度も書かれない行を scan が取りこぼしても verifier に見えない。scan 対象の 3 表 (NewOrder・OrderSecondary・OrderLine) について、**trace build だけ、ロード完了後に実際の木を走査した初期キー一覧**を別 file に出し、ロード側で数えた件数と照合する (NewOrder は district あたり 900 行、OrderSecondary は 3,000 行、OrderLine は各 order の `O_OL_CNT + 1` 行の和)。

- 決定的な再生成では代替できない: ロードは thread-local の自己 seed 乱数・customer の permutation・乱数の OrderLine 件数を使う (所見 A2)。
- 検出限界: 一覧と scan が同じ key を同時に落とす common-mode の欠落 (同じ process 由来) は捕えない。D296 が R/W 件数について明記した限界と同型。

### 4.4 不在の観測版 — 草案の解き方は不健全、直接の証拠で決める

範囲内で返らなかった key について、読み手 S がどの版を選んだか (Adya の Vset(P) のうちその key の版) で張る辺が変わる。不在を表す版は「挿入前 (unborn)」と「削除後 (dead)」の 2 種類ある。

| key の履歴 (trace 全体) | 返らなかったとき S が選びうる不在の版 | 張る辺 |
|---|---|---|
| 挿入のみ (挿入者 I) | 挿入前だけ | S → I (predicate rw) |
| 初期存在 + 削除 (D) | 削除後だけ | D → S (predicate wr) |
| 挿入 + 削除 (I, D) | 挿入前 **または** 削除後 | 直接の証拠があれば片方。無ければ indeterminate |
| 初期存在で削除なし | 不在の版が無い | 履歴不整合 (indeterminate) |

- 上の 2 行は、選びうる不在の版が 1 つしか無いので、「返らなかった」という結果そのものが観測版を一意に決める。壊れた scan が live の key を落とした場合も、S の結果と両立する版はそれしか無く、Adya の定義どおりの辺になる。その辺で cycle ができれば非直列化として拒否され、できなければ「S をその挿入の前 (削除の後) に置く直列順」が実在する。**これは直列化可能性の認定で、実時間の順序 (strict serializability) は検査しない** (現行 verifier と同じ)。段 6 review 所見 M2 は「この 2 行にも直接の証拠が要る」としたが、この理由で採らない (§11)。
- 選言になるのは 3 行目だけ。CCBench の TPC-C で挿入と削除の両方を受けるのは NewOrder 表だけで (NewOrder が挿入、Delivery が削除 `tpcc_tx_delivery.hh:69`)、それを scan するのは Delivery だけ (§4.6)。OrderLine・OrderSecondary の行集合は挿入でしか変わらない (OrderLine と Order は Delivery が UPDATE するが、行集合は変えない)。

**草案の解き方 (既存辺の到達可能性で片方に決め、決まらなければ indeterminate) は採らない。** 段 3 レンズ A の反例: k は初期不存在、y は初期存在とする。(1) S が k を含む範囲を空で読む (このとき k は挿入前)、(2) I が k を挿入し y を更新して commit、(3) D が k を削除して commit、(4) S が I の y を読んで commit。実際の依存は S → I (predicate rw) と I → S (y の wr) で G2 だが、草案の規則は既存の I → S を見て「挿入前」を排除し D → S を選ぶので、グラフは非巡回になり certified になる。**曖昧な選言が 1 つも残らなくても偽認定になる。** Adya の Vset(P) はシステムが実際に選んだ版の集合であり、「非巡回になる版集合が存在する」ことへ置き換えると、実際の DSG の認定ではなくなる。

採用する規則 (段 4 裁定 R4 を段 6 review 所見 M1・M3・M4 で修正したもの。段 3 では攻撃されていない):

- 観測版は**直接の証拠**で決める。DSG の cycle の有無で選ばない。
  - **Q の観測記録 (最優先):** scan が物理候補として触れた key は、Q に「その場で選んだ版、または返さなかった理由 (未 commit で不可視・deleted 版・abort 版)」を値で残す。時刻からの推定より優先する。tombstone は、committed の削除者と対応する版を実際に観測した場合だけ削除後の証拠にする。abort 版を不在の版の producer にしない。
  - **si:** snapshot 時刻 (`txid_` = 全 thread の `lastcstamp` の最大 + 1、`cc/si/transaction.cc:25-73`) と最終の `cstamp` は可視性の必要条件として使うが、**単独では観測版を決めない** (所見 M1)。`read_internal()` は読取り時の status と cstamp の両方で版を選ぶので (`:153-158`、cstamp = snapshot は committed / deleted として観測した場合に限り可視側)、読取り時に inflight だった挿入が後で cstamp = snapshot で commit すると、最終履歴の時刻比較では「見えるはず」でも実際は不可視だった経路がある。物理候補に触れた key は Q で決め、木から除去済みで候補に現れなかった key は、物理的な除去との前後関係を別に証明できなければ indeterminate。
  - **silo / mocc:** 単一版の OCC なので CC に snapshot 時刻は無い。trace build 限定の全体通し番号を、木への挿入の**直前**、木からの除去の**直後**、scan の走査 (Masstree の scan 呼出し) の**開始**と**終了**で採る。「除去の直後 < 走査の開始」なら、その key は走査中ずっと木に無かった → 削除後。「挿入の直前 > 走査の終了」なら走査中に木に無かった → 挿入前。重なれば決めない。**境界は node 検証ではなく走査区間** (観測は走査中に起きる。初版は「node 検証の終了」を境にしていたため、下の反例が重なりで indeterminate になり §6.2 の期待「赤」と矛盾した = 所見 M3)。
- 決まらない key を含む scan は indeterminate にし、件数と理由を返す。
- **通し番号の契約 (所見 M4、§7.1 単位 6 の完了条件):** (a) 採番器・保存状態・呼出し・include はすべて `#if TRACE` の中 (規律 1)。(b) 順序は seq_cst の fetch_add とし、木の操作との happens-before を明示する。既存の `next_txid()` は grouping 用の relaxed 採番なので物理順の証拠に流用しない (`include/trace.hh:41-46`)。(c) record 形式と、取引・key・scan への対応 (挿入・除去の番号は W 行、走査区間は S 行)。(d) 木の操作の成功・失敗 (WARN_ALREADY_EXISTS)・abort 時の除去を区別し、abort した取引の番号は証拠にしない。(e) 採番の呼出しは合成 variant が変えられない位置 (EVOLVE-BLOCK の外、auditor と diff 検疫の保護下) に置く (規律 6)。除去の直後の番号は「木に無い」ことの証拠であって、既にポインタを持つ読み手が tombstone を見たことの証拠ではない (それは Q の領分)。
- 草案が物理連番を退けた理由 (採番と木の変更は原子的でない / scan は区間 / si は物理的に在っても snapshot より新しい版を見ない) には、前後を挟む採り方・重なりの indeterminate 化・si は Q を主にする、で答える。
- **未検証の前提:** Masstree の scan が「走査開始前に挿入を終え、走査終了後まで除去されない key を必ず通る」こと。wrapper は `table_.scan()` を呼ぶだけで (`include/masstree_wrapper.hh:194-208`)、split / retry を含む保証は固定 pin の Masstree (`cmake/ThirdParty.cmake:35-45`、tag `b3c5d054`) の実装に依存し、本 wave でも段 6 でも証明していない。**証明が閉じるまで、選言の key を通し番号だけで認定しない** (§8 の 6)。代案は Masstree の node 版 (scan callback が既に集めている、silo `:733`) を証拠にする方式で、split の扱いがさらに重い。

### 4.5 張る辺 (まとめ)

| 観測 | 追加する依存 |
|---|---|
| 範囲内の live 版 v を返した | producer(v) → S の wr、v の直後版の書き手へ S → 書き手の rw (既存の点読みと同じ) |
| 挿入前を観測 (不在の版が 1 つで一意、または直接の証拠) | S → 最初の挿入者 (predicate rw) |
| 削除後を観測 (同上) | 削除者 → S (predicate wr)。再挿入があれば S → 次の挿入者 |
| 初期存在の key が返らず、説明する削除も無い | 履歴不整合 (indeterminate) |
| 観測範囲の外 | 辺なし |
| 自取引の変更 | 自己観測。外部取引への自己ループは作らない |

### 4.6 5 つの scan と範囲に入る key の書き手

| scan | 範囲・上限 | 範囲内の書き手 | 行集合の変化 |
|---|---|---|---|
| Delivery `tpcc_tx_delivery.hh:45` | NewOrder、`[(w,d,1), (w,d+1,1))`、昇順 limit 1 | NewOrder の INSERT (`tpcc_tx_neworder.hh:143`)、Delivery の DELETE (`tpcc_tx_delivery.hh:69`) | **挿入 + 削除** |
| Delivery `:135` | OrderLine、`[(w,d,o,1), (w,d,o+1,1))`、上限なし | NewOrder の INSERT (`:279`)、Delivery の UPDATE (`:150`) | 挿入のみ |
| OrderStatus `tpcc_tx_orderstatus.hh:30` | OrderSecondary、`[(w,d,c,1), (w,d,c+1,1))`、昇順 limit 1 | NewOrder の INSERT (`tpcc_tx_neworder.hh:114`) | 挿入のみ |
| OrderStatus `:72` | OrderLine、Delivery と同じ形 | 同上 | 挿入のみ |
| StockLevel `tpcc_tx_stocklevel.hh:50` | OrderLine、`[(w,d,next−20,1), (w,d,next,1))`、上限なし | 同上 | 挿入のみ |

- OrderLine の番号は初期ロードが `1 .. O_OL_CNT+1` (`tpcc_initializer.hh:279`)、実行中の NewOrder が `0 .. n−1` (`tpcc_tx_neworder.hh:314`、親が確認)。範囲 `[(o,1), (o+1,1))` は自 order の line 0 を含まず、次 order の line 0 を含みうる。実コードの範囲のまま扱う (TPC-C 仕様との差は §9)。
- OrderStatus は「最新の order」を求める仕様だが、実装は昇順木の limit 1 で最古を読む。全 customer が初期 order を持ち削除されないので、通常ロードでは OrderSecondary の phantom 辺は作れない (所見 A8)。

### 4.7 計算量と辺の数

- 表ごとに初期キーと committed の write key を整列し、scan ごとに二分探索: scan 1 回 `O(log K + k)`、k は観測範囲内の distinct key 数 (返却件数ではない)。
- **Delivery の NewOrder scan は、観測範囲に同じ district の配送済み (削除済み) key をすべて含む** (下限が `o_id = 1`)。1 倉庫で各 Delivery が 10 district を順に配送する条件では、削除後の観測が生む依存理由の候補は約 `10 × N_D (N_D − 1) / 2`、現行 verifier と同じく取引対で重複除去した辺は約 `N_D (N_D − 1) / 2` (N_D は Delivery の commit 数、隣接は宛先の集合で重複除去 `orchestrator/verifier/dsg.py:641-643`)。N_D = 12,000 なら約 7.2 億候補・約 7,200 万辺 (段 6 所見 M5 で訂正。初版は候補数を辺数と書いていた)。比較できる実績は現行 verifier で 5.95 億辺・896 秒 (read-heavy 6 秒の trace、`output/insights/2026-09-20/verifier-capacity/README.md:47`) だが、新しい述語の列挙時間には直接換算しない。候補の列挙が Delivery 数の二乗で増えることは残る。
- 辺の間引きが健全な条件 (所見 M5): **削除する各辺 u → v を、削除後も残る直接証拠つきの有向路 u → … → v が代替し、その路の辺を相互依存で同時に削除しないこと。** 「連続する Delivery は直前の削除を観測するから鎖がある」と仮定せず、実際に張った辺で確かめる。delete_record の NOT_FOUND 無視 (§9) で鎖が切れる場合は間引かない。間引けなければ述語処理が検査時間を支配しうる。

## 5. CC ごとの改修点

### 5.1 実装の差 (草案 §3 の表を採用)

| 面 | silo | si | mocc |
|---|---|---|---|
| scan | 物理候補 → read set、既読・自 write の再利用 (`:291-340`) | snapshot 版の選択、deleted / null を除外 (`:417-460`) | silo に類似 (`:375-418`)。冷経路の absent 読みは abort (`:341-364`) するが、高温・RLL 経路は lock 取得後に同じ absent 判定を通らない (`:280-309`) |
| insert | absent かつ lock 済みの tuple を木へ先に公開 (`:70-115`) | inflight の初版を公開 (`:301-345`) | absent tuple を公開 (`:486-530`) |
| delete | writePhase で木から除去、epoch GC (`:668`) | tombstone 版を install、commit で木から除去 (`:348`, `:513`) | lock・検証を経て除去 (`:533`, `:1180`) |
| abort | 挿入 tuple を木から外して即 delete (`:27-35`) | 挿入 tuple を即 delete、版を aborted に (`:578`) | 挿入 tuple を即 delete、CLL / RLL 処理 (`:1059`) |
| phantom 防止 | node_map_ の版比較 (`:477-481`)、callback (`:733`) | 比較 (`:485`)、callback (`:685`) | 比較 (`:1042`)、callback (`:1286`) |
| 現行 trace | v2 frame (C 7 token + E) | **v1 (parser が拒否)** | v2 frame |
| X/P 証拠面 | あり (X の emitter 3 箇所・P の emitter 1 箇所 `:432`) | なし | なし ([T-2844] が作成中) |

(行番号は各 `external/ccbench/cc/<cc>/transaction.cc`。)

**node_map_ があることは、完全な述語読みの証明ではない** (親 P5 を訂正): 公開済みの未 commit tuple が commit で live になるとき、木の構造版が必ず変わるとは限らない。CC の可視性処理と node 検証を合わせて trace で検査する (§4)。

### 5.2 CC ごとの改修

| CC | 段 1 | 段 2 | 認定 |
|---|---|---|---|
| silo | R/W に表、v3 C 行 (編集面内) | S/Q の buffer と emitter、通し番号、abort 即時解放の本体修正 | **対象** (X/P 既存) |
| mocc | 同上 (編集面内)。G2 watermark (値の先頭 8 byte に txid を刻む、`cc/mocc/transaction.cc:23-120`) は TPC-C の行を壊し INSERT / DELETE で明示 abort する (`:1173-1182`) ので TPC-C では使わない | silo と同じ + CLL / RLL を含む寿命条件。高温・RLL 経路が absent 判定を通らないので、返した状態と版を Q に正しく記録し、deleted 版の live 返却を拒否する正例・負例を足す (段 3 所見 A4 / 段 6 所見 S6。この経路で偽認定が成立すると実証したわけではない) | [T-2844] の X/P 計装と pin 前進の後に対象 |
| si | v3 frame、読み履歴 (状態区別)、snapshot 時刻 (編集面外) | S/Q (deleted 観測の区別) | **検出専用** (非直列化の判定は有効、serializable は indeterminate のまま) |

si は snapshot isolation で anti-dependency を検査しない (`cc/si/transaction.cc:614`) ので、TPC-C で G2 が出れば verifier が拒否するのが正しい挙動。ただし「この 5 取引で G2 を再現できる」ことは未実証。

### 5.3 編集面と pin 前進

| 改修 | hook の編集面 (`hooks/guard_write.py:44-45` = `include/backoff.hh`・silo / mocc の `transaction.cc`) | 行き先 |
|---|---|---|
| silo / mocc の `transaction.cc` の計装 | 内 | 本採用は D16 の `izanagi-trace` 枝 |
| si の `transaction.cc`、`include/trace.hh`、`include/tpcc.hh`、`tpcc_initializer.hh`、scan wrapper、transaction header | 外 | `izanagi-trace` 枝 (Codex author が CCBench 側で commit) |
| abort 即時解放の本体修正 | ファイルによる | trace 計装と分けた本体修正。性能 build の挙動も変わる (§8 の 2) |
| 壊した CC (phantom の正例) | — | `patches/` の out-of-tree patch (D16 の第 3 類) |
| verifier・pipeline | CCBench の外 | superproject |

pin 前進は 1 回必要 (候補 commit の材料 → 人間の push → gitlink・`CCBENCH_FULL_SHA` (`orchestrator/campaign/s8b_approved.py:67`)・`CURRENT_PIN` の同時更新、先例 D2150 / D2184)。稼働中の [T-2844] (mocc X/P の候補 commit、`dev-wave-jobs/dev-wave-t2844-mocc-xp-hook-branch/`) の上に積み、pin 前進を分けない。旧 8b / 8c 系列の再開・再凍結は裁定控え項 5 により見積りから外す (所見 B5)。

## 6. 検出力を確かめる正例・負例

いずれも試験案と期待結果で、実行結果ではない。「cycle を作る辺」まで書く。**狙った機構を外したときに結果が変わるか (帰属)** を各例に付ける (所見 A8)。

### 6.1 段 1

| 例 | 内容 | 期待 | 帰属 |
|---|---|---|---|
| 表識別 (辺集合比較) | A: Warehouse(k) の genesis を読み Item(k) を更新。B: Warehouse(k) を更新 (B の版が A の版より前) | 表あり = A → B の rw だけ。表を落とす変異 = B → A の ww と A → B の rw が加わる | cycle ではなく**表ありの参照グラフとの辺集合の一致**で判定する (表を消しても cycle が残る例は表識別の control にしない) |
| lost update (TPC-C 上の壊した silo) | 既存 `patches/broken-silo-norw-validation.patch` を TPC-C で。2 取引が District の同じ版を読み順に更新 | A → B の ww、B → A の rw で non-serializable | 読み検証を戻すと片方が abort して消える |
| 手書き G2 (v3) | 草案 §4.1 の 8 行 (表 0 と表 9 の同じ key) | 0 → 1 と 1 → 0 の rw で non-serializable | **v3 parser と cycle 検出の control**。表識別の検出力には数えない (genesis 読みから両向き rw が残るため) |
| genesis の誤用 | 初期不存在の key へ A が INSERT、B がその key の `(1,0)` を live として読む | 存在履歴の不整合で indeterminate | integrity の試験 (cycle の control ではない) |
| si の読み消去 | 読み履歴 buffer を無効にする変異 | read → update の R が消え、その R が作る rw を含む既知 cycle が消える | si を検出に使う場合だけ |
| witness | (a) commit 成功直後に quit を立てる、(b) 末尾の C frame を落とす、(c) 最大 txid の取引を落とす、(d) thread の trace file を丸ごと落とす | (a) 一致、(b)〜(d) 件数不一致で indeterminate。旧順序へ戻す変異は (a) で拒否 | D295 の防護の再実証 |
| 正常対照 | 同じ fixture を直列に実行 | graph green。**certified には X/P・frame・witness の充足も要る**ことを併記 | — |

### 6.2 段 2

| 例 | 内容 | 期待 | 帰属 |
|---|---|---|---|
| INSERT phantom (合成) | S が OrderSecondary の範囲を空で読み x を更新。I が範囲内へ挿入し x の genesis を読む | S → I (predicate rw) と I → S (x の rw) で G2 | predicate 辺だけを外すと非巡回になる |
| 実 CC の phantom | scan 後に他取引が範囲内へ挿入する schedule で、silo の node 検証 (`:477-481`) を無効にする patch。逆向きの点依存も作る | 上の 2 辺で赤 | 検証を外すだけでは異常 schedule の証拠にならないので、逆向き依存の成立も確かめる |
| DELETE phantom の対 | D が初期 key k を削除、S は範囲で k の不在を観測し D が読んだ x を更新。逆向きの依存を足した版と足さない版 | 足した版だけ赤 | 基本形 (D → S の 2 辺) だけでは非巡回 |
| **偽認定の反例 (§4.4)** | 挿入前の空読み → 挿入・更新 → 削除 → 読み手が更新を読む。通し番号の順は「S の走査開始 < 走査終了 < I の挿入直前 < D の除去直後 < S の commit」 | 走査区間を境にする規則: 「挿入の直前 > 走査の終了」で挿入前が決まり、S → I (predicate rw) と I → S (y の wr) で G2 の赤。合成 fixture では挿入前の観測を直接与えて同じ辺を確かめる | 到達可能性で決める変異が**緑にしてしまう**ことを検出。node 検証の終了を境にする変異は重なりで indeterminate になる (段 6 所見 M3)。実 CC で同じ schedule を作るには silo の node 検証を外す必要があり、その control とは分けて数える |
| 決まらない不在 | 通し番号の区間が重なる | indeterminate | 恣意的に片側を選ぶ変異を検出 |
| LIMIT の偽依存防止 | limit 1 で live a を返し、後ろの b へ別取引が挿入。b の挿入者から S への逆依存も置く | b からの predicate 辺なし (緑) | 全範囲扱いの変異が偽 cycle を作る |
| 物理上限で可視行欠落 | 先頭の物理候補が未 commit、後ろに初期 live、返却 0・物理 1・limit 1 | indeterminate | 返却件数だけで完走と判定する変異を検出 |
| 初期キーの取りこぼし | 初期一覧にある OrderLine を scan が落とす | 説明する削除がなければ拒否 | W 行だけで候補を作る変異を検出 |

実取引で G2 を作りうる静的な schedule (所見 A8、未再現): NewOrder N が Customer の旧版を読んで止まる → Delivery D が対象 OrderLine と同じ Customer を更新して commit → StockLevel L が更新済み OrderLine と N 更新前の District を読んで commit → N が District を更新して commit。辺は N → D (Customer の rw)、D → L (OrderLine の wr)、L → N (District の rw)。前提として Delivery の次対象 order が当該 district の直近 20 件に入るまで古い注文を配送しておく。silo / mocc では N の古い Customer 読みの検証が焦点。

## 7. 工数・trace 容量・計算投入の見積り

### 7.1 実装単位 (Codex author 1 本の担当範囲)

| # | 段 | 単位 | 置き場 |
|---:|---|---|---|
| 1 | 1 | `trace.hh` の v3 helper (表・取引種別・C 10 token)、`tpcc.hh` の取引種別 context と trace build 限定の計数修正 | CCBench (編集面外) |
| 2 | 1 | silo の v3 emitter | CCBench (編集面内) |
| 3 | 1 | mocc の v3 emitter ([T-2844] の後) | CCBench (編集面内) |
| 4 | 1 | verifier の v3 parse と `(table, key)` (object / compact の両経路)、anomaly の表・取引種別 | superproject |
| 5 | 1 | pipeline の allowlist (tpcc + v3 + 57:43 の flag)、witness 試験、段 1 の正例・負例 | superproject + patches |
| 6 | 2 | S/Q の buffer と emitter (silo / mocc)、scan wrapper の物理候補、通し番号。完了条件に §4.4 の通し番号の契約 (a)〜(e) と、固定 pin の Masstree の走査保証 (split / retry) の一次資料での確認を含める | CCBench (内外) |
| 7 | 2 | 初期キー一覧 (ロード後の実木の走査 + 件数照合) | CCBench (編集面外) |
| 8 | 2 | verifier の範囲 index・述語辺 (§4.4 の規則)・LIMIT 契約・辺の間引き・indeterminate の理由 | superproject |
| 9 | 2 | 段 2 の正例・負例 (合成 fixture + node 検証を外した patch) | superproject + patches |
| 10 | 2 | abort 即時解放の本体修正 (silo / mocc、§8 の 2 が採られた場合) | CCBench 本体 |
| 11 | 共通 | pin 前進 (候補の材料、人間の push 後の gitlink・承認定数・`CURRENT_PIN` の同時更新) | superproject |
| (12) | 任意 | si の v3 frame・読み履歴・S/Q・snapshot 時刻 (検出専用) | CCBench (編集面外) |

草案の 17 単位から外したもの: 木への挿入後・write set 登録前の return の修正 3 単位 (TPC-C では到達しない、§9)、寿命修正を段 1 より前に置く順序、独立の TPC-C reporter、旧系列の再凍結 (所見 B3・B5・B6)。削れないもの: 初期キー集合、scan と観測の対応、計数修正、構造化 anomaly。

### 7.2 wave 数と所要 (暫定工程表)

段 1 = 2 wave (CCBench 側 1 + verifier / pipeline 側 1)、段 2 = 3 wave (観測と初期キー 1、verifier と control 1、寿命修正 1)、pin 前進 1 wave (人間の push 待ちを含む)、計 **6 wave 程度**。段 1 を内部の受入の節目として先に閉じ、pin は全体で 1 回にする構成が安い (所見 B6)。

実績の比較 (記録): trace 形式 v2 (D296 / T816) は C++ 差分 +14/−1 の 1 wave の後、parser と pin 移行に別 wave を要し fix 2 巡 (`output/insights/2026-08-12/t816-step4-impl/README.md`)。witness (D295 / T756) は 1 wave で fix 2 巡・焦点走 4 回・変異 3 走。実装 wave の所要は impl 7 本平均 169.6 分 (118.5〜214.8 分、同じ夜の 12 本の標本、`output/insights/2026-09-21/dev-wave-wall-decomp/README.md:37`, `:54`)。6 wave なら**約 12〜21 時間**の wave 所要 (並走で短縮可) に、人間の push 待ちが加わる。§4.4 の規則と §4.7 の辺の間引きが実装 wave で覆れば、段 2 は増える。

### 7.3 trace 容量 (試算)

1 行の byte 数は形式から計算 (ASCII、区切り 1 byte、LF 1 byte)。txid ≤ 7 桁・thid ≤ 2 桁・epoch ≤ 3 桁・tid ≤ 8 桁・表 ≤ 2 桁と置いた**予算用の幅**で、実測平均でも無条件の上限でもない。8 byte key で R ≤ 43 B、W ≤ 45 B、Q 約 48 B、S 約 86 B。

| 取引 (条件) | R / W / S / Q 行 | 約 B / commit | 出所 |
|---|---|---:|---|
| NewOrder (品目 n = 10、重複なし) | 23 / 24 / 0 / 0 | 2,133 | コードから数えた + 形式試算 (`tpcc_tx_neworder.hh:295-340`) |
| Payment | 3 / 4 / 0 / 0 | 355 | 同 (`tpcc_tx_payment.hh:242-269`) |
| Delivery (10 district、L = 110) | 140 / 140 / 20 / 120 | 19,853 | 同 (`tpcc_tx_delivery.hh:199-222`)。初期ロード中心の例 |
| OrderStatus (L = 11) | 14 / 0 / 2 / 12 | 1,478 | 同 |
| StockLevel (L = u = 220) | 441 / 0 / 1 / 220 | 29,659 | 同 |
| **段 1 (57 : 43)** | 31.8 行 / commit | **1,368** | 既存 flag の閾値 + 試算 |
| **全 5 取引 (45 : 43 : 4 : 4 : 4)** | 70.6 行 / commit | **3,152** | 既定比率 + 試算 |
| 初期キー一覧 (1 倉庫) | NewOrder 9,000・OrderSecondary 30,000・OrderLine 平均 330,000 行 | 約 8.6 MB (commit 数に依らない) | 試算 |

100 万 commit あたり段 1 約 1.37 GB、全 5 取引約 3.15 GB。品目数は 5〜15 の一様 (`tpcc_query.hh:98`)、Item の重複を禁じる処理は無効なので、NewOrder を常に 23 / 24 行とは言えない。生成比率と commit 比率は同じでない (NewOrder は 1% の意図的な無効品目で abort し、abort ごとに query を作り直す `tpcc_query.hh:122`、`tpcc.hh:48`)。既定 1 倉庫・48 スレッドでは Payment の Warehouse 更新と 10 District に競合が集中し、abort 率と取引別の commit 比率が変わる。L = 110 / 11 / 220 は初期状態中心の例で、長い走行の平均ではない (所見 B8)。

### 7.4 verifier の時間と計算投入

| 記録 / 試算 | 時間 | 出所 |
|---|---:|---|
| YCSB write-heavy 8,323,838 取引 | 297 秒 (35.7 秒 / 百万取引) | 記録、`output/insights/2026-09-20/verifier-capacity/README.md:40` |
| YCSB balanced 14,748,197 取引 | 478 秒 (32.4 秒 / 百万) | 記録、同 `:41` |
| YCSB read-heavy 16,819,316 取引 | 433 秒 (25.7 秒 / 百万) | 記録、同 `:46` |
| 段 1 (57 : 43) | 約 77〜106 秒 / 百万 commit | 試算 (操作数 29.8 を YCSB の約 10 操作へ比例) |
| 全 5 取引 | 約 170〜240 秒 / 百万 commit **+ 述語処理** | 試算。§4.7 の辺の数次第で支配項が変わる |

「48 スレッド 3 秒の read-heavy YCSB で検査 1 回 23 分」は旧い混合区間の値で、現行 verifier の単価には使わない (現行は 433 秒)。

**検索した記録 (worklog・insights・decisions の Markdown) からは、この換算に使える 3 CC の TPC-C throughput の実測は見つからなかった** (所見 B9)。3 秒走の総生成率を仮に 10 万 / 秒と置くと 30 万 commit・trace 約 0.95 GB・検査の比例項 51〜72 秒 (0.014〜0.020 node 時間)、100 万 / 秒と置くと 300 万 commit・約 9.5 GB・510〜720 秒 (0.14〜0.20 node 時間)。いずれも仮定で、build・ロード・trace の書き出し・述語処理・再試行を含まず、§4.4 で足す通し番号などの保存費用も入っていない。同規模 10 走なら比例項だけで上側が 2 node 時間に届く。**最初の計算投入は、少ないスレッド・短い走行の 1 走で throughput と trace 量と検査時間を測るものにし、同じタスクの build・検査・変異・再試行を含む合計 node 時間を見積もって、2 node 時間以上なら投入前に確認を取る (未満なら確認不要、裁定控え項 4)。** build は login では hook が拒否する (§10) ので計算ノードで行う。

## 8. 実装へ進む前に決めたこと — 親の決定と、やらない理由の最も強い形

本 wave は設計と見積りを返して終える。次の 1〜4 と 6 は段 3 の 2 レンズ (6 は段 6 review) の攻撃を経た親の決定で、実装 wave はこれを前提に起票してよい。覆す新事実が出たら、その実装 wave の段 4 で裁定し直す。5 だけはユーザーの確認ライン (裁定控え項 4) に従う。

1. **si は検出専用にする。** 最も強い反論: si は 3 CC のうち唯一の多版 CC で、論文で「多版の CC も認定できる」と言えなくなる。それでも採る理由: 現行の certified は X/P の証拠面を要求し、si にはそれに当たる安全条件が無い。形式だけの emitter を置けば証拠の偽装になる (所見 A6)。si 固有の証拠契約 (install-version の所有・公開条件と操作集合の保存) は別の設計課題として残す。
2. **abort 即時解放の本体修正を段 2 の前提に採る (段 1 の前提にはしない)。** 最も強い反論: 性能 build の挙動が変わり、baseline と既存の計測との比較が崩れる。既定 mix で踏む頻度は低い。それでも採る理由: 静的に到達しうる解放済み tuple の参照を抱えたまま完走した trace を検査しても、実行基盤の正当性は補えない (所見 B4)。旧計測は旧 pin の事実として残り、無効にはならない (規律 7)。旧 pin → 新 pin に TRACE=0 の同一性は要求しない (所見 B5)。段 1 では挿入先の表を他取引が読まないので前提にしない。
3. **pin 前進は [T-2844] の候補 commit の上で 1 回にする。** 最も強い反論: [T-2844] の進み具合に依存し、段 1 の完成が遅れる。それでも採る理由: 段 1 の silo 部分は現 pin の上で内部の受入まで進められ、pin 前進を 2 回にすると候補の公開・承認・整合の手続きが 2 回かかる (所見 B5・B6)。段 1 を急いで使う必要が出た場合だけ 2 回に分ける (+1 wave)。
4. **段 1 (57 : 43) → 段 2 (全 5 取引) の分割を使う。** 最も強い反論: 段 2 の設計 (§4.4) が未検証のまま段 1 を作ると、v3 frame を段 2 で作り直す恐れがある。それでも採る理由: v3 の C 行は S / Q の件数 field (nS, nQ) を最初から持つ (§3.1)。段 1 は述語・初期キー・寿命修正を待たずに、表付きの点依存と計数を検査できる (所見 B6)。
5. **最初の計算投入 (ユーザー確認ライン):** 小さい 1 走で throughput・trace 量・検査時間を測る。同じタスクの build・検査・変異・再試行を含む合計 node 時間を見積もり、2 node 時間以上なら投入前にユーザーの確認を取る。未満なら確認は要らない (§7.4 の仮定では 1 走の検査比例項は 0.014〜0.20 node 時間だが、throughput の実測が無いので投入前に見積もり直す)。
6. **§4.4 の証拠は、Q の観測記録を主にし、silo / mocc は走査区間を挟む通し番号、si は Q と時刻を必要条件として使う。** 最も強い反論: 通し番号の全体同期は trace build の interleaving を変え、検証した実行が性能 build の実行と違う分布になる。Masstree の走査保証も未証明。それでも採る理由: trace build は既に txid の全体採番を持ち、規律 1 は性能 build から計装を除くことで守る。走査保証は単位 6 の完了条件にし、証明できなければ Masstree の node 版を証拠にする方式か、「選言の key を含む scan は indeterminate」へ倒す (この場合 Delivery を含む走は認定できず、段 2 で認定できるのは Delivery を 0% にした 4 取引の mix までになる)。

## 9. 付随して見つけた CCBench の問題 (構造化。還元判断: ユーザー確認待ち)

いずれも静的に読める経路で、実行による再現はしていない。

| 発見 | 該当コード | 再現条件 (静的) | TPC-C 認定への影響 |
|---|---|---|---|
| 挿入 tuple を木へ公開した後、node 版の不一致で write set 登録より前に return する。abort は write set しか掃除しないので、absent かつ lock 済みの tuple が木に残る (以後その key を読む取引は lock 待ちから抜けない) | silo `cc/silo/transaction.cc:88-109`、si `:319-340`、mocc `:504-525` | 同じ取引で scan の後に同じ node へ挿入する | **現行 5 取引では到達しない** (scan する取引は挿入せず、挿入する取引は scan しない)。合成が取引の操作を変える場合は再評価 |
| abort が挿入 tuple を木から外して即 delete する。別取引が木や scan buffer から取ったポインタを使い続けうる (silo は lock が下りるまで同じ tuple を読み続ける) | silo `:27-35`, `:250-255`、si `:578-586`、mocc `:1059-1077` | NewOrder が挿入後に無効品目で abort する間に、隣 order の line 0 を含む OrderLine 範囲を scan する | 段 2 の実行基盤の前提 (§8 の 2)。si の Tuple は Version を delete しないので「解放済み Version への書込み」とまでは言えない |
| si の update / delete が read set の要素を消す | si `:239-247`, `:352-362` | read → update / delete | si の trace から R が落ちる (§3.4) |
| si の trace は v1 形式で、現行 parser が拒否する | si `:539-555`、`parse.py:323-326` | si の任意の trace | si は現状どの workload でも検証できない |
| OrderLine の番号が初期ロード (1 .. O_OL_CNT+1) と実行時 (0 .. n−1) で食い違い、scan 範囲は隣の order の line 0 を含む | `tpcc_initializer.hh:279`、`tpcc_tx_neworder.hh:314`、`tpcc_tx_delivery.hh:133-134` | 常時 | 認定は実コードの操作履歴に対して行う (TPC-C 仕様準拠の証明ではない)。直すと workload が変わるので trace 計装と分ける |
| OrderStatus は最新の order を求める仕様だが、昇順木の limit 1 で最古を読む | `tpcc_tx_orderstatus.hh:9`, `:28-31` | 常時 | 同上 |
| Delivery の delete_record は NOT_FOUND を無視して取引を続ける | `tpcc_tx_delivery.hh:66-70` | 同じ new-order を 2 つの Delivery が扱う | 同じ key を scan で読んだ R が rw 辺を張るので、追加の trace は要らない。§4.7 の削除者の鎖が切れうる |

## 10. 限界

- **静的調査のみ。** build・binary 実行・pytest・性能測定はしていない。login での小規模 build は、`cmake -S` (TRACE=1、依存 prefix `/work/1/SFC/tanab/izanagi-a2-deps`、system の gcc 11.4) が rc 0 で tpcc の 3 target を生成対象に含めたところまで。`cmake --build` は hook (`guard_bash`) が「Pegasus ログインノードでは重い処理を実行できない」として拒否し、依頼の制約 (計算ノードへ投げない) に従って build 確認は行っていない。本番の toolchain (gcc-13) とも違う。
- §4.4 の証拠規則 (段 4 で親が採用) は段 3 で攻撃されていない。攻撃したのは段 6 の review と焦点再レビューだけ (§11)。
- 工数・容量・時間はすべて試算で、値ごとに出所を付けた。TPC-C の throughput 実測が無いので秒あたりの値は出していない。
- 衝突の列挙 (§3.2) は通常の生成域に限り、任意の整数入力や counter の wrap は含めない。
- 実取引の G2 schedule (§6.2) は静的な案で、再現していない。

## 11. 段 6 review

read-only review 1 本 (2 レンズ: 一次資料との照合と R4 の健全性、`verbatim/s6-review.md`) の判定は **NO-GO** (must-fix 5、should 2、nit 1)。数値の再計算 (57:43、31.80 / 70.56 行、1,368 / 3,152 B、初期キー 8,598,000 B、秒 / 百万、node 時間、6 wave = 11.85〜21.48 時間) はすべて本文と一致した。量化 (「挿入 + 削除は NewOrder だけ」「scan する取引は挿入しない」「CustomerSecondary はロード後不変」「si の v1 は parser が拒否」) も支持された。

| 所見 | 親の判定 | 対応 |
|---|---|---|
| M1 si の snapshot 時刻と最終 cstamp だけでは読取り時の不可視を再構成できない | real | §4.4: si は Q を主にし、時刻は必要条件だけ。除去済みで候補に現れない key は前後関係を別に証明できなければ indeterminate |
| M2 「挿入のみ」「初期存在 + 削除」の不在にも直接の証拠が要る | **refuted** | 不在の版が 1 つしか無い key では結果が観測版を一意に決め、Adya の定義どおりの辺になる (壊れた scan の取りこぼしも、その辺で cycle ができれば拒否され、できなければ直列順が実在する)。認定するのは直列化可能性で、実時間の順序は検査しない。§4.4 の表と §4.5 の書き方の矛盾 (「証拠あり」) は直した |
| M3 反例は「node 検証の終了」を境にした通し番号では重なって indeterminate になり、本文の「赤」と矛盾 | real | 境界を走査区間 (Masstree の scan 呼出しの前後) に直した。観測は走査中に起きるので、この境界で反例は S → I と I → S の G2 になる (§4.4、§6.2) |
| M4 通し番号の保存形式・対応・順序・保護位置が未定義。Masstree の split を含む走査保証は未証明 | real | §4.4 に契約 (a)〜(e) を書き、§7.1 単位 6 の完了条件にした。証明が閉じるまで選言の key を通し番号だけで認定しない |
| M5 約 7 億は依存理由の候補数で、取引対で重複除去した辺は約 7,200 万。実績は 5.95 億辺・896 秒もある | real | §4.7 を訂正し、間引きが健全な条件を 1 行で書いた |
| S6 mocc の高温・RLL 経路は absent 判定を通らない (段 3 A の所見を本文が落としていた) | real | §5.1・§5.2 に書き、正例・負例を足した |
| S7 計算確認を 2 node 時間の線と無関係に全投入へ掛けていた | real | §1・§7.4・§8 の 5 を「合計 2 node 時間以上なら確認、未満は不要」に直した |
| N8 引用 (si の delete、snapshot、mocc の abort、P の emitter 数) と限定表現 | real | 直した |

焦点再レビュー 1 本 (`verbatim/s6-focus.md`) の判定は **GO**。前回 8 所見はすべて closed。M2 は、不在の版が 1 つの key について「取りこぼしを別の点依存で拘束する履歴」を 2 通り (挿入のみ / 初期存在 + 削除) 作って攻撃したが、どちらも cycle として検出され、非直列化なのに非巡回になる反例は作れなかった (攻撃不成立、refuted のまま閉鎖)。派生値 (7.1994 億候補・7,199.4 万辺、5.95 億辺・896 秒、si の snapshot = 最大 + 1、relaxed 採番、silo の X 3 箇所・P 1 箇所) は再計算・照合で一致し、訂正による回帰は無かった。**GO は訂正後の設計文書に対する判定で、Masstree の走査保証・通し番号の実装契約・実 CC での control の実証は後続の実装の完了条件として残る。**
