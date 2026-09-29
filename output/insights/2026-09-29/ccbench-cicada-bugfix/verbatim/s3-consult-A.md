## 所見 — promotion の意味

- **must-fix｜重複した read が TPC-C の結果を変える。** `read_internal()` は既に read 集合へ追加し、promotion は同じ要素を再追加する（`cc/cicada/transaction.cc:126`、`cc/cicada/include/transaction.hh:207-210`）。`scan()` は追加された要素をすべて結果へ移すため（`transaction.cc:445-457`）、1 行を要求した OrderStatus の scan が 2 行を返し、`include/tpcc/tpcc_tx_orderstatus.hh:30-37` の `ERR` に達し得る。**反例の筋:** promotion を有効にした TPC-C OrderStatus、4 worker、対象の OrderSecondary 版が非 inline で promotion 条件を満たす走行。G の完走結果が異常終了に変わる。**直し方:** `inlineVersionPromotion()` の二度目の `read_set_.emplace_back` を行わない。既存の要素は `update()` が見つけ、読み取り専用からの移行にも残る。

- **should｜abort 後の再試行で読み取り専用の指定が戻らない。** YCSB は `is_ronly_` を `RETRY` より前で一度だけ設定する（`include/ycsb.hh:106-113`）。promotion が false に変えた後（`transaction.hh:208-209`）、`update()` の early abort または validation 失敗で再試行すると、次の試行は wts で読む（`transaction.cc:93-97`）。直列化可能性の反例とは言えないが、G の R workload の実行内容と検証記録の「読み取り専用」の意味が変わる。**直し方:** 各 `begin()` の前に procedure の `ronly_` から設定し直す。

- **should｜early abort は `Status` だけでは分からない。** `update()` は `status_=aborted` にしても `Status::OK` を返す（`transaction.cc:253-261,276-297`）。YCSB は各操作後に、TPC-C は tx ループ末尾に状態を調べて abort する（`include/ycsb.hh:149-155`、`include/tpcc.hh:100-107`）。従って、この二つのループでは aborted tx が commit される穴は確認できない。ただし TPC-C の helper は `read()` の戻り値だけで値を使う箇所がある（例 `include/tpcc/tpcc_tx_stocklevel.hh:15-19`）。G で promotion 後の early abort が起きると、abort 確定前に後続処理を続け得る。**直し方:** `read()` が promotion 後の aborted 状態を呼び出し元へ返し、helper が値を使う前に止まるようにする。

- **判定｜既存 read の検証と値の対応には、示された経路上で穴は見つからない。** `read_internal()` は rts で選んだ版を記録し（`transaction.cc:93-126`）、write tx に変わった場合は validation が各記録版を wts で見える版と照合する（`transaction.cc:536-569`）。途中に別の committed 版が入れば不一致で abort する。promotion の値はその記録版の `TupleBody` のコピーである（`transaction.hh:203-207`）。`inline_ver_` の `unused` 読みは予約ではないが、実際の取得は `getInlineVersionRight()` の CAS が裁定し、負ければ通常の版を作る（`transaction.hh:217-245`、`cc/cicada/include/tuple.hh:54-71`）。この読みだけから競合による二重取得は導けない。

## 所見 — 既定 build の不変と A2・A3 の直し方

- **should｜P1 の結論は条件付きで正しいが、`ERR` の根拠が誤っている。** 置換を既定で無効な `#if INLINE_VERSION_OPT`、`#if WORKER1_INSERT_DELAY_RPHASE` 内に限り、物理行数と directive を維持すれば、既定 context の TRACE=0 preprocess 出力は一致する見込みが強い（`cmake/Options.cmake:14-19,49-54`）。ただし、この F の `ERR`→`NNN` は `__LINE__` を展開しない（`include/debug.hh:54-65`）。「`ERR` の `__LINE__` が一致する」は確認項目として成立しない。**放置時:** G の D297 記録が、実際には測っていない性質を保証した表現になる。**直し方:** 既定 context の正規化 preprocess 一致と、物理行番号の維持を別々に記録する。

- **should｜A3 の識別子修正は妥当だが、積には overflow がある。** `transaction.hh:10,18` から `backoff.hh:12`／`util.hh:250-253` へ辿れるので `sleepTics` は見える。`unlikely` は既に使われており、`include/compiler.hh:3-4` の macro が入口 TU から供給される。flag と `FLAGS_clocks_per_us` はともに `uint64`（`common.hh:38-40,61-62,75,90`）で、その積は符号なし 64 bit で折り返す。**放置時:** 大きな runtime 引数では G の W5 が指定より短く待ち、待機実測の記録が誤る。**直し方:** A3 の三識別子を置換し、積を計算する前に除算による上限検査を入れる。追加行が必要なら D2293 の方式で後続の論理行番号を戻し、P1 の「行数不変」自体を目的化しない。`thid_ == 1` は worker 1 を指す。runner は worker を 0 から生成し（`common/runner.hh:281-286`）、Cicada の leader は 0（`transaction.cc:960`）。

- **should｜A2 は計上行そのものを無効にする。** `read_internal()` に `start` はなく（`transaction.cc:79-137`）、`read()` は既に計上する（`transaction.cc:144-147,185-189`）。**放置時:** G の `ADD_ANALYSIS=1` 代表 genome は compile 不能のまま。**直し方:** 131 行を行数不変の空文またはコメントに置換する。`read()` の計上は残す。

## 所見 — 検証の射程

- **should｜`#error` を外した使い捨て計装は、この経路の観測として成立する。** promotion が成功すれば `update()` は `write_set_` に RMW を追加し（`transaction.cc:210-218,285-288`）、`traceCommit()` の W 行に出る（`instr-cicada-trace.patch` の `traceCommit` hunk）。promotion で `is_ronly_` が false なら `writePhase()` で記録され、true のままなら read-only commit 側で記録される（`transaction.cc:910-913,934-947` と patch の二つの `traceCommit()` hunk）。**放置時:** `#error` を外した理由を説明しない G の検証記録では、promotion 書き込みを観測した根拠が欠ける。**直し方:** 使い捨て変種、TRACE=1、W 行と commit 件数の対応を記録する。TRACE=0 の G 本体へ計装を入れる必要はなく、判定器も変えない。

- **should｜重複 R は integrity 0 でも残る。** patch は `read_set_.size()` を C 行に書き、各要素を R 行にするため、重複しても件数は一致する。判定器の `framing_violations` は宣言件数と実件数を比べ（`orchestrator/verifier/parse.py:289-303`）、`version_dups` は異なる tx による同一 write 版を数える（`orchestrator/verifier/dsg.py:466-475`）。同一 tx の同じ R を直接拒否する項目ではない。**放置時:** G の小走行が integrity 0 でも P4 の「重複は無害」を支持した記録にならず、上記 scan の障害を見逃す。**直し方:** 重複挿入を修正し、trace の R 行数もその結果として一件にする。

- **判定｜小走行の合格は、観測した履歴に限る。** 巡回 0・integrity 0 はその trace の DSG を支持するが、全スケジュールの直列化可能性、値そのものの一致、TPC-C promotion の scan 経路は証明しない。特に P5 の promotion cell は YCSB のみで、上記の TPC-C 反例を通らない。**直し方:** G の記録では「指定 cell の観測結果」と書き、promotion 有効の TPC-C OrderStatus を正しさ小走行に含める。判定器の条件は維持する。

## (P1)〜(P7) への意見

| 項目 | 意見 |
|---|---|
| P1 | 条件付きで妥当。`ERR`／`__LINE__` の説明と、全 patch の無 offset 適用を行数だけから断定する部分は修正が必要。 |
| P2 | `write`→`update` は API 修正として妥当。validation の静的根拠はあるが、scan 重複と再試行時の状態が未解決。 |
| P3 | runtime flag、`sleepTics`、worker 1 の選択は妥当。乗算 overflow を扱う必要がある。 |
| P4 | A2 修正に賛成。A1′「二度検証するだけで無害」は誤りで、G に含めて直す必要がある。 |
| P5 | trace の観測方法は妥当。promotion TPC-C の scan を含まないまま一般化しない。 |
| P6 | build、待機、CI、D297 はそれぞれ指定した結果だけを主張する。F との対照や throughput の低下は W5 の待機を支えるが、正しさの証明にはならない。 |
| P7 | 提示資料だけでは node 時間の見積りを検証できない。正しさ所見による追加対象の費用を親が計上すべき。 |

## 総括

G に入れる前の主要修正は **promotion の重複 read 集合追加の除去**です。これは trace の見栄えだけでなく TPC-C の `scan(limit=1)` の返却値を変えます。続いて read-only 再試行の状態復元と A3 の乗算上限を扱い、検証結果は実際に走らせた cell の観測として記録してください。これは指定資料の静的判定であり、build・テストは実行していません。