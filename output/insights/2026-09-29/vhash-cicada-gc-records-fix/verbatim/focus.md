## 対応表

| 対象 | 判定 | 根拠 |
|---|---|---|
| review-a 所見 1：identity 判定 | **closed（静的）** | 修正後の CUSTOM は compile command と命令列の両方を要求する（`stage6/launch_gcfix_run.py:1193-1196`）。既存 L0-TPCC と同じ条件（同:1162-1164）。L0 本体には前処理・シンボルの追加条件がある（同:1137-1145）。実行時の再確認は未実施。 |
| review-b 所見 1：M2 の分類 | **closed** | 起動器は引き続き記録専用（`stage6/launch_gcfix_run.py:630-633`）だが、親の原本では t4 が 10/10、t8 が 3/10 の既知 ERR。親が **KILLED** と分類済み（`v1-result-summary.md:13-14`、`s4-ruling-addendum-1.md:7,30`）。 |
| review-b 所見 2：V1 の run 数 | **closed** | 原本 `runs/v1/result-CUSTOM.json` は計 66 run。要約の内訳 20＋20＋3＋20＋3 と一致する（`v1-result-summary.md:8-15`）。追補裁定も 66 と訂正した（`s4-ruling-addendum-1.md:31`）。 |
| 新事実 S：scan の空 key | **partial** | scan-key patch は最新版の body からの取得を `Tuple::body_` に変更する（`stage6/fix-cicada-gc-records-scan-key.patch:7-13`）。通常設定の load・insert では正しい key を保持するが、`INLINE_VERSION_OPT=1` の新規 insert 経路には下記の例外がある。V3 trace の実測も未了。 |
| 新事実 U：abort の use-after-free | **partial** | 原因は INSERT tuple を消した後の `writeSetClean()` にある（`transaction.cc:745-754`、`include/transaction.hh:343-361`）。使い捨て patch はその要素を読み飛ばす（`stage6/asan-abort-uaf-workaround.patch:4-10`）。scope 外として記録済み（`s4-ruling-addendum-1.md:20-23`）だが、回避後の ASan 実測は未了。 |

ここでの `transaction.cc` と `include/transaction.hh` は [Cicada のソース](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/external/ccbench/cc/cicada/transaction.cc) とその `include/` を指す。

## 新しい所見

- **should-fix — `INLINE_VERSION_OPT=1` まで「全 insert で key が正しい」とは言えない。** `new Tuple()` の inline 版は既定で `pending`（`include/version.hh:34-37`）なので、`newVersionGeneration()` の `unused` 要求が通らず（`include/tuple.hh:56-65`、`include/transaction.hh:217-245`）、heap 版が作られる。一方、insert 用 `Tuple::init()` は inline 版の空 body を `Tuple::body_` に複写する（`include/tuple.hh:95-107`）。成果物への影響：この構成では scan-key patch が**有効な最新版 key を空 key に退行**させうる。V3 の既定設定 `INLINE_VERSION_OPT=0` とは分けて主張する必要がある。

- **nit — V3a の見積りが 10 run 多い。** `s4-ruling-addendum-1.md:39-43,51` の「48 run」に対し、`spec-v3a.json:4-26` は 10＋20＋3＋2＋3＝**38 run**。成果物への影響：実施数の記録にずれが残る。

- **nit — V2 の空 key 件数の範囲が狭い。** `v2-result-summary.md:7` の「1 file あたり 88〜114 行」に対し、原本 trace の F 3 run・12 file は **82〜114 行/file**。成果物への影響：新事実 S の量の記述だけがずれる。

## 検算

通常の load は元 body から key を複写し（`include/tuple.hh:74-92`）、`INLINE_VERSION_OPT=0` の insert も body 付き新規版から複写する（`transaction.cc:313-315`、`include/tuple.hh:95-107`）。再利用版も `set()` で body ごと入れ替える（`include/transaction.hh:229-244`、`include/version.hh:85-91`）。確認した TPCC の load・insert・update 呼出しでは、索引 key と body key に同じ値を渡す（例：`include/tpcc/tpcc_initializer.hh:32-36`、`include/tpcc/tpcc_tx_neworder.hh:143-144,215-216`）。ただし `update()` 自体は二つの key の一致を検証しない（`transaction.cc:196-205,285-288`）。したがって「空 key の場合だけ変わる」は**確認した workload と通常設定に限る**。`Tuple::body_` は版からの独立した複写なので版の更新・再利用では変わらない（`include/tuple.hh:84-106`、`include/tuple_body.hh:32-55`）。tuple 自体の delete と scan の競合は既存の最新版参照にもある問題で、この patch はその寿命を改善・保証しない（`transaction.cc:423-432,849-855`）。

ASan 回避は abort 後の後始末だけに作用し、validation と commit の判断経路には触れない（`transaction.cc:463-609,687-720,745-754`）。INSERT は validation の版 install を飛ばすため（同:481-483）、読み飛ばす `new_ver_` は abort 時に再利用リストへ戻らず、使い捨て ASan 走行では漏れる。一方、`gc_records()` の分岐は残るので、その寿命検査を直接は妨げない。ASan 合格の可否は実測待ち。

V3 spec の build、patch、期待値、run の指定は追補裁定の表と一致する（`spec-v3a.json:2-27`、`spec-v3b.json:2-22`、`s4-ruling-addendum-1.md:35-49`）。V3b の計数 patch は gc 修理後、scan-key patch 前に適用されるが、修正箇所は独立している（`spec-v3b.json:3-6`、`stage5/count-gcfix-skips.patch:4-25`）。

原本 `runs/v1/result-CUSTOM.json` は **66 run**：無修理 20/20 ERR、修理 20/20 rc=0、pin C 3/3 rc=0、M2 は計 13/20 ERR、ASan は 3/3 rc=1。`runs/v2/result-CUSTOM.json` は **12 run**：修理 F の 3/3 は本体 rc=0 だが検証器 rc=2、D は 1,578／1,510／1,636 件、読み飛ばしは 261／246／315 回、D の thread は各 run で 4。M・R2 の修理版と stock 版は各 4/4 で所定の判定を満たす。SKIPRC は本体 rc=0、検証器 rc=2。V2 identity 原本の 3 TU は compile command・命令列とも一致する。これらは既存 V1/V2 の値であり、修正後 V3 の結果ではない。

## 総括

通常設定での scan-key 修理と起動器修正は、静的には裁定に沿う。**全構成での key 正当性には `INLINE_VERSION_OPT=1` の例外が残る。** V3 の trace・ASan・identity の合否は、このレビューでは確定できない。