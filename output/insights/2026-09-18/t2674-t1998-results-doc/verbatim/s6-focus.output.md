## 対応表

対象稿・README は commit `e31030990` と差分なし。静的検査のみ実施した。`partial` は未対応部分または編集上の部分採用を示す。

| レンズ | 番号 | 重さ | 判定 | 根拠 |
|---|---:|---|---|---|
| A | 1 | must-fix | closed | §2.5・§4(j) は `b1a3d45d61ac7a62f589c514683e5ba999b50609`、2026-09-14 08:30:25 JST に訂正済み。main first-parent 列に存在し、是正 commit の祖先判定は同 commit で rc=0、第1親 `e0b1c336…` で rc=1。land 時刻との区別も明記。 |
| A | 2 | must-fix | closed | §2.5・§5.4 は終了時刻と Elapse の出所を stderr に訂正。現物は `22:39:23`、`712S`。投入時刻は group_id と qstat に限定し、receipt に時刻 field がないことも明記。 |
| A | 3 | must-fix | closed | §5.4 は canonical `genome`・`src_token` を `build_start.payload`、source digest 等をその下の `build_admission.source` に分離。WAL の現物と一致。 |
| A | 4 | must-fix | closed | §1.3 の `ycsb_rmw`、`ycsb_rratio`、`ycsb_zipf_skew` は復号した lock と一致。値も文字列 `"0"`、`"50"`、`"0.9"`。 |
| A | 5 | must-fix | closed | §2.2 は `perf_counter_statuses = ["not_required"]` に訂正。result は配列、WAL の `counter_status` は文字列という区別も正しい。 |
| A | 6 | must-fix | closed | §1.2 の引用は事前登録 §4 冒頭と一致。§5.4 も判定規則を「記号を置き換えた要約・転記」と明記。 |
| A | 7 | must-fix | closed | §2.3 の「23 key」は result のトップレベルを数え直して一致。`correctness` key はない。 |
| A | 8 | should-fix | closed | §2.1 は一致対象を identity fields に限定。共有する7 field が一致し、追加の `common.repository_commit` と欠ける `schema_version` も正しく説明。 |
| A | 9 | should-fix | closed | §2.3・限定7に D1993 理由節を追加。射影原文に A-2 の4 cell・A-6 の2 cell が「legacy 1 回 + performance 5 回」を通った記述がある。 |
| B | 1 | must-fix | closed | 限定5は温度ドリフトの影響を「分離・評価していない」に変更。WAL が示す baseline、target の順次測定と整合。 |
| B | 2 | should-fix | closed | §1.4・§4(a) は source identity の一致と patch／tracked diff 対応の未照合を区別。両 arm は同じ2パス・`29aef2bc…`、source digest はそれぞれ `2d691b45…`／`678b7203…`。 |
| B | 3 | should-fix | closed | §2.3 の追加経路を確認。`loop.py` は `evaluate` に `correctness` を渡さず、lock に `verify` key はない。既定値と実行時 argv の記録を区別する限定もある。 |
| B | 4 | should-fix | partial | §2.4 の8点表は残るが、登録外2点の比較文・行2の hash 余談は削除済み。所見が認めた表存置時の注意書きも追加され、推定量は登録2点に限定。残存は編集判断であり、阻害事項ではない。 |
| B | 5 | should-fix | partial | §4 の分類、README の「欠落10件」削除、§4(b) の保存先限定は対応済み。ただし **§2.1 に「その判定 JSON は保全されていない」が残る**。§4(b) と同じ「参照した保存先では確認できない」に統一すべき。 |
| B | 6 | nit | partial | README は短縮され、全点掲載宣言などを削除。ただし冒頭・§5.5・README に「横断稿から引き継がない」という作成経緯が残り、重複解消は部分的。事実誤認ではない。 |

## 検算

| 対象 | 現物からの再計数・再計算 | 稿との照合 |
|---|---|---|
| `23 key` | result トップレベル23件、`correctness` なし | 一致 |
| `40 record`・「すべて pegasus」 | 8 variant × `build_start / build_done / verify_done / bench_done / commit` 各1件。全40件の `env_tag=pegasus` | 一致 |
| `63 blob` | `contract_loader_blob_sha256s` は63 entry。`loop.py`・`pipeline.py` は含まれ、`backoff_sweep.py` は含まれない | 一致 |
| 限定20件 | §3 の番号付き項目は1～20 | README とも一致 |
| §4 の区分 | 4.1 は5項目、4.2 は2項目、4.3 は3項目、計10項目 | 一括した「欠落10件」は README から削除済み |
| 成果物 file 数 | root 配下23 file、うち0 byte が9 file、`.failure.json` は0件 | 一致 |
| 主要 file の bytes | result 1,864、reservation 921、lock 7,951、WAL 60,166 | 一致 |
| receipt・stdout | receipt 2行（`manifest`／`submitted`）、stdout 268行 | 一致 |
| insight README 数 | §5.2 に異なる5本を列挙 | 冒頭の5本と一致 |
| 「8点とも」完走 | commit 8件、abort stage 0件 | 一致 |
| 「8点とも」共通状態 | 全8点で `high_variance=false`、`unstable=false`、`rounds=1`、X/P=`evidence-present`、I=`evidence-absent` | 一致 |
| 正しさ「両 arm とも」 | 各1件の `verify_done`、`serializable`、`certified=true`、anomalies=0。`verify_configs=["legacy"]`、verifier evidence 各1件 | 一致 |
| 両 arm の測定記録 | 各5標本、`cv_history` 各1要素。`settled` は baseline=true、target=null。stage の時刻順も記述どおり | 一致 |
| identity「全項一致」 | 事前登録の共有7 field が consumer JSON と一致。両 arm の source digest、各 commit の環境 digest も一致 | block 全体の同一性へ拡張していない |
| repository identity | result・reservation・lock・receipt の4者は `a551cdd3…`。同 commit の gitlink は `511c9538…` | 一致 |
| 事前登録 SHA | 現行 file と `a551cdd3…` の blob はともに `464e3af5…719c`。判定 JSON の2 pin も同値 | 一致 |
| 標本・median・CV | 8点の全40標本を照合。median と標本標準偏差÷平均を再計算 | 全8点で一致。CV の小数4桁表示も一致 |
| 効果量「全桁一致」 | `4330570 / 3893509 = 1.1122537536191646`、改善率 `11.225375361916456` | producer・consumer・稿で一致 |
| hash | root の23 file、receipt、stdout、stderr、採用判定 JSON の SHA-256 を再計算 | §5.1 の掲載値・空 file の省略記述と一致 |
| §2.5 の時刻 | qstat の投入22:27:23・開始22:27:36、stderr の終了22:39:23・Elapse 712S | 一致。Elapse は NQSV 記録値として転記 |
| 事前登録 §4 の引用 | 「次の値を、測定を 1 度も走らせる前に固定する。」 | 逐語一致 |
| 「登録2点だけ」 | spec の baseline／target は表の行1／行4。§2.1・§2.2 の推定量に登録外6点は入っていない | 一致 |

8点の median／CV 再計算結果は、WAL 順に次のとおり。

| 行 | median | CV（小数4桁） |
|---:|---:|---:|
| 1 | 3,893,509 | 0.0227 |
| 2 | 1,265,586 | 0.0354 |
| 3 | 4,442,208 | 0.0282 |
| 4 | 4,330,570 | 0.0128 |
| 5 | 3,910,016 | 0.0044 |
| 6 | 3,066,391 | 0.0034 |
| 7 | 2,431,951 | 0.0028 |
| 8 | 1,870,346 | 0.0035 |

量化の確認範囲には次の限界がある。

- **「投入1回・2本目なし」**：指定 receipt・成果物から確認できるのは balanced の1 job。事前登録 §7 は投入回数の規則であり、それ自体は他の投入が存在しない証明ではない。全保存先に対する不存在監査はしていない。
- **2026-09-15 の「全桁一致」**：稿は insight README に記録された事実として述べている。今回、その日の判定 JSON との独立な数値照合はしていない。

## 新規所見

**fix に起因する新規所見はなし。**

重点確認した §2.3 の経路は現物と一致する。

- `loop.py` の SHA-256 は `785dd6fe…35808` で、lock の値と一致。
- `_closed_verify_workloads` は `search_config["verify"]` が未指定なら `None` を返す。今回の lock に同 key はない。
- `evaluate` 呼出しには `correctness` の指定がなく、pipeline 側で `CorrectnessWorkload()` に落ちる。
- 同 constructor の既定値は稿の8項目と一致。`backoff_sweep.py` の呼出しにも上書きはない。
- この code の確認を実行時 argv の直接記録と扱わない限定が維持されている。

B-5 の残存断定と B-6 の重複は、既存所見の部分未対応であり、新規所見には重複計上しない。

## 総括

**closed 12件／partial 3件／regressed 0件。新規所見0件。着地は止めない。**

must-fix 8件はすべて解消し、追加経路・主要数値・件数も一致した。B-5 の断定は保存先限定へ統一することを推奨する。