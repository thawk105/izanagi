## 実コード裏取り

| 事実 | 実コード根拠 | 判定 |
|---|---|---|
| stock の backoff 点 | `external/ccbench/cc/silo/transaction.cc:27-53`。`abort()` は insert 後処理と GC、3 コンテナの clear 後、`BACK_OFF` 時に `Backoff::backoff()` を無条件実行する | gate は abort 判定後の待機有無だけを変更する |
| hole の物理面 | `patches/silo-backoff-trigger-gating-variant.patch:79-111`。マーカー内は現状 `izanagi_gate_pass = true;`、実際の `if` と backoff 呼出しはマーカー外 | hole と呼出し骨格は保持可能 |
| 現行契約 | `patches/silo-backoff-trigger-gating-variant.patch:86-102`、`orchestrator/campaign/axis_trigger_gating.py:27-49,85-96` | enum と定数のみ。今回改訂対象 |
| clear 済み集合 | `transaction.cc:38-40` | `size()==0` / `empty()==true` は恒真。ただし `capacity()`、`data()`、`bucket_count()` までゼロとは限らないため、「どの読取も情報を持たない」は誤り。型全体の禁止は正しい |
| `max_wset_` | 宣言 `include/transaction.hh:57-58`、初期化 `:72-73`、begin reset `transaction.cc:55-59`、更新 `:145-192` | 成功済み write-set 要素から得た最大 Tidword。lock conflict/absent abort では途中までの値 |
| `max_rset_` | 宣言 `include/transaction.hh:57-58`、reset `transaction.cc:55-59`、更新 `:449-475` | 検証を通過済み read-set 要素の最大 Tidword。失敗要素自身は反映前 |
| `Tidword` | `include/tuple.hh:12-30` | `uint64_t obj_` と bitfield の union。今回の許可面は初期化が追える `.obj_` のみに絞る |
| `mrctid_` | 宣言 `include/transaction.hh:57`、直前 commit TID の読取・更新 `transaction.cc:570-582` | worker の成功履歴そのもの。`result_` の代理になり得る |
| GC 履歴 | `transaction.cc:15-24,36`、蓄積 `:668-687` | `gc_records()` 後も epoch 条件を満たさない record は残る。親の生存側列挙から漏れている |
| WAL 履歴 | 宣言 `include/transaction.hh:41-42,55`、更新 `transaction.cc:495-520`、base は `WAL=0` `axis_trigger_gating.py:61-64` | 一般には履歴を持つが、この軸の動作点では不感または初期化証明不足 |
| epoch/backoff | 初期化 `include/transaction.hh:68-75`、更新入口 `transaction.cc:717-721` | 時間・適応制御・実行進捗の代理 |
| status | enum `include/transaction.hh:24-29`、begin `transaction.cc:55-59`、abort 設定 `:160-188,453-483,733-740` | transaction.cc 内の既知 abort 経路では実質 `aborted`。要因情報を持たず恒真化しやすい |
| その他の生存メンバ | `include/transaction.hh:37-62` | `pro_set_` 以外にも `quit_`、`callback_`、3 boolean などが clear されない。親の M3 は非網羅 |
| 検疫の保証範囲 | `diff_quarantine.py:14-23,285-307,464-523` | marker 外編集と一部 byte 注入は拒否するが、C++ の意味、allowlist、UB は保証しない |
| identity | `source_digest.py:81-96,2051-2086,2195-2250` | `transaction.cc` は既に digest/編集面に含まれ、identity と trace diff は fails-closed。対象ファイル拡張は不要 |
| 既存部分空間 | `axis_trigger_gating.py:73-83` | 5 gateable reasons の 32 点。新契約の部分空間としてそのまま残せる |

親の実測に対する訂正は二点ある。

1. 生存メンバ列挙から `gc_records_`、WAL 系、`quit_`、`callback_`、`reconnoitering_`、`is_ronly_`、`is_batch_` が漏れている。
2. `clear()` が保証するのは論理要素数ゼロであり、コンテナの全観測が恒真ゼロになるわけではない。capacity、bucket、storage address は履歴や個体識別情報を残し得る。したがって D48 のコンテナ名単位の禁止は維持すべきである。

## 軸定義シート草案

| §2 欄 | 草案 |
|---|---|
| 軸名 | `silo-backoff-trigger-gating`。既存 marker と identity を維持する。根拠: `axis_trigger_gating.py:22-25` |
| 変異型 | **非列挙のコード片軸**。出力は値ではなく、単一の boolean 述語代入。現行 wire-only 定数空間は偵察用部分空間へ降格する。根拠: hole `patch:79-110`、コード片軸要件 `axis-onboarding.md:223-245` |
| SOURCE_REL | `cc/silo/transaction.cc`。既に `EVOLVE_BLOCK_SOURCES` と file allowlist 内。根拠: `axis_trigger_gating.py:23-25`、`source_digest.py:73-96` |
| マーカー ID | `silo-backoff-trigger-gating`。据え置き。根拠: `axis_trigger_gating.py:23,27-50` |
| hole の位置と骨格 | `TxExecutor::abort()` の `#if BACK_OFF` 内、3 コンテナ clear 後。coder 面は `izanagi_gate_pass = <bool-expression>;` の右辺だけとし、変数宣言、sentinel、`if`、`Backoff::backoff()`、stock 枝は骨格専権。根拠: `transaction.cc:27-52`、`patch:75-111` |
| 構文契約 | 既存の `izanagi_abort_reason_`、`IzanagiAbortReason::*`、コンパイル時 unsigned 定数に加え、**`max_rset_.obj_` と `max_wset_.obj_` の rvalue 読取だけを許可**する。`kUnset` は全メンバ値について必ず true とする。外側は単一代入。許可演算子は unsigned の全域演算、比較、boolean 結合、括弧に限定する。除算、剰余、shift、cast、アドレス取得、pointer/reference traversal、添字、関数・member function 呼出し、代入以外の副作用、lambda、例外、volatile/atomic access、非決定 builtin、未列挙 identifier は既定禁止。`this` 経由の別綴りも禁止。根拠: 候補の初期化・更新 `transaction.cc:55-59,145-192,449-475`、型 `tuple.hh:12-30`、現行閉領域 `patch:86-100` |
| stock の動作 | `BACK_OFF=1` なら abort 要因や member 値によらず一度 `Backoff::backoff(FLAGS_clocks_per_us)` を呼ぶ。根拠: `transaction.cc:42-52` |
| フラグ名 | `CCBENCH_BACKOFF_TRIGGER_GATING`、TU macro は `BACKOFF_TRIGGER_GATING`。0=stock、1=variant。`_BASE` は `BACK_OFF=1`。根拠: `patch:5-28`、`axis_trigger_gating.py:58-64` |
| 壊しうる不変条件 | 契約どおりなら abort 決定や共有 DB 更新には触れず、serializability の新規変更はない。一方、契約違反を通すと C++ UB、sentinel fallback 破壊、入力隔離破壊が起こり得る。契約内でも abort storm、live-lock、特定 transaction/record 世代への偏り、適応 backoff との帰属混同が可能。根拠: backoff が clear 後 `transaction.cc:38-52`、最大 Tidword の由来 `:145-192,449-475` |
| verifier の死角 | abort hole は trace event を出さず、trace は commit/writePhase と P/X 検査が中心なので、predicate 入力、gate 判定、部分 starvation、member 起因の偏り、UB による最適化を直接見ない。根拠: `transaction.cc:27-53,584-634,694-699`。pre-build admission は verifier と別の必須一次防壁 |
| reward hack 仮説 | `mrctid_`、epoch、backoff、GC/WAL 履歴による fitness/progress 適応、pointer/address による thread identity 復元、transaction class flag や `pro_set_` による fairness 犠牲、`max_*` の低位 bit を用いた疑似 thread/record partition、定数縮退、sentinel 条件付き縮退。直接・代理を問わず禁止面は identifier 単位で拒否する |
| positive control 設計 | CC の serializability 用新 assert は不要。ただし admission-language の正しさは新規不変条件。禁止 identifier、pointer/cast、ゼロ除算、範囲外 shift、副作用、`kUnset=false` をそれぞれ独立に入れた mutation-red が build 前に構造化 reject されることを証明する。既存の要因記録 misattribution positive control は維持する。根拠: `axis-onboarding.md:146-158,323-334`、既存設計 `existing-sheet-2026-07-10.md:158-169` |
| 偵察の列挙空間 | 拡張後の全 coder 空間は有限候補集合を契約から導けないため完全 sweep 不可。**列挙可能な部分空間は現行 5-bit wire 空間**、すなわち `GATEABLE_REASONS` の部分集合 32 点。根拠: `axis_trigger_gating.py:73-83`。これは拡張空間の安全な下位集合であり、全空間との一致は主張しない |
| 感度を持つ workload | balanced、write-heavy、read-heavy の三類型を据え置く。新規 reconnaissance 数値や勝ち実装は入力にしない。根拠: `existing-sheet-2026-07-10.md:193-198`、firewall `axis_trigger_gating.py:11-16` |
| 計測動作点 | p2_2 の t48、1M records、skew 0.9 を据え置く。拡張全空間の floor を意味せず、5-bit 部分空間の既存生存確認にのみ使う。read-heavy floor の扱いは従来条件を維持。根拠: `existing-sheet-2026-07-10.md:200-203` |

この allowlist は「メンバ名」ではなく「許可された観測式」を列挙する。例えば `max_rset_` を丸ごと許可せず、`max_rset_.obj_` だけを許す。これにより bitfield union、pointer、member method への横展開を既定拒否できる。

## allowlist 判定表

| メンバ、宣言型 | hole 時点の意味 | clear/reset | UB、恒真化、非決定性 | 最終判定 |
|---|---|---|---|---|
| `read_set_`: `std::vector<ReadElement<Tuple>>` `transaction.hh:35` | current transaction の read 集合だったもの | `abort()` で clear `transaction.cc:38` | size/empty は恒真。capacity/data は履歴・address を残す。要素参照は UB | **禁止** |
| `write_set_`: `std::vector<WriteElement<Tuple>>` `transaction.hh:36` | current transaction の write 集合だったもの | clear `transaction.cc:39` | read_set と同じ。破棄済み要素の参照は UB | **禁止** |
| `node_map_`: `std::unordered_map<void*,uint64_t>` `transaction.hh:39` | scan/node version 集合だったもの | clear `transaction.cc:40` | size は恒真だが bucket_count、hash storage は履歴を残す | **禁止** |
| `pro_set_`: `std::vector<Procedure>` `transaction.hh:37` | projected source だけでは生成・意味を確認不能 | `abort()` では clear なし | `.size()` 自体は安全だが transaction class/fairness proxy。要素型の安全面は未確認 | **禁止** |
| `gc_records_`: `std::deque<Tuple*>` `transaction.hh:38` | 未回収 delete record の履歴 | hole 前に GC、条件不成立要素は残る `transaction.cc:15-24,36` | size は安全だが進捗・reclamation backlog proxy。pointer dereference は lifetime リスク | **禁止** |
| `log_set_`: `std::vector<LogRecord>` `transaction.hh:41` | WAL 履歴 | `wal()` 内だけで更新・clear `transaction.cc:495-520`。base は WAL=0 | base では実質不感。WAL 有効時は成功履歴 proxy | **禁止** |
| `latest_log_header_`: `LogHeader` `transaction.hh:42` | WAL 集計 | constructor の明示 init はコメントアウト `transaction.hh:71` | 型定義が射影外で初期化証明なし。不定値読取の可能性を排除不能 | **禁止** |
| `status_`: `TransactionStatus` `transaction.hh:44` | tx 状態 | begin で inflight、失敗点で aborted | projected 内 abort 経路では aborted に縮退。begin 前 lifecycle は射影内で証明不能 | **禁止** |
| `thid_`: `size_t` `transaction.hh:45` | worker ID | constructor 固定 `:68-70` | 初期化済みだが安定した fairness partition | **明示禁止を維持** |
| `result_`: `Result*` `transaction.hh:49` | run の各種集計への入口 | constructor 固定、各処理でカウンタ更新 `transaction.cc:71-80` ほか | fitness 信号、pointer identity、共有状態競合の入口 | **明示禁止を維持** |
| `epoch_timer_start/stop`: `uint64_t` `transaction.hh:50` | leader epoch/timing 状態 | constructor `:74-75`、外部関数へ参照渡し `transaction.cc:717-718` | `rdtsc()` 起源で非決定。進捗・時間予算 proxy | **禁止** |
| `backoff_`: `Backoff` `transaction.hh:51` | leader の適応 backoff 状態 | constructor `:68-70`、`CCBenchResults` と更新 `transaction.cc:719-721` | 内部型が射影外。fitness 信号の代理になり得る | **禁止** |
| `quit_`: `const bool&` `transaction.hh:52` | thread termination control | constructor で外部参照を保持 | 実行終了時刻への適応。writer の同期方式が射影外で data race を排除不能 | **禁止** |
| `callback_`: `TxScanCallback` `transaction.hh:53` | executor への callback state | `this` で初期化 `:69-70` | pointer identity/reentry 面。内部型が射影外 | **禁止** |
| `logfile_`: `File` `transaction.hh:55` | WAL I/O state | 明示初期化なし、write 使用 `transaction.cc:508-516` | 型の初期化、I/O状態、同期が射影外 | **禁止** |
| `mrctid_`: `Tidword` `transaction.hh:57` | worker が直前に選んだ commit TID `transaction.cc:570-582` | abort/reset なし。型 default は obj=0 `tuple.hh:24` | 安全に読めても local commit progress、`result_` counter の強い代理 | **禁止** |
| `max_rset_.obj_`: `Tidword` `transaction.hh:58` | 検証済み read の最大 version `transaction.cc:449-475` | constructor と begin で 0 | `.obj_` は初期化済み。全体/bitfield/参照は許可しない。DB進捗との相関は残る | **allowlist 採用** |
| `max_wset_.obj_`: `Tidword` `transaction.hh:58` | lock 済み write の最大 version `transaction.cc:145-192` | constructor と begin で 0 | `.obj_` は初期化済み。lock conflict では部分値または0 | **allowlist 採用** |
| `reconnoitering_`: `bool` `transaction.hh:60` | reconnoitering mode | false 初期化、begin/end 変更 `transaction.cc:724-730` | 実験相・warmup 相への条件付け、fairness/measurement hack | **禁止** |
| `is_ronly_`, `is_batch_`: `bool` `transaction.hh:61-62` | 名称上は tx class だが projected source に設定箇所なし | false 初期化、abort reset なし | 現構成では恒真 false の可能性。将来は transaction class fairness proxy | **禁止** |

したがって、今回確定する CC-native allowlist は `max_rset_.obj_` と `max_wset_.obj_` の二観測だけである。これらも `TxExecutor` が単一 worker 所有であるという lifecycle 前提が C 段で実コード確認できなければ自動的に禁止へ倒す。

## 非列挙性の論証と列挙可能部分空間

新契約は有限候補リストではなく、再帰的な boolean expression 文法を与える。契約には AST 深さ、式 byte 数、部分式数、定数個数の上限がない。したがって、許可 token が有限でも、契約から完全な有限 candidate set は導けない。`DiffQuarantine` 自体も意味 admission を保証しないと明記している (`diff_quarantine.py:14-23`)。

さらに member allowlist だけでは C++ の安全性は導けない。例えばゼロ除算、範囲外 shift、signed overflow、pointer/cast を別 gate で閉じない限り、許可された値を読む式でも UB を作れる。このため、

- 全 coder 空間について有限完全列挙する
- その全点の安全性を構成的に保証する

という §3-D の組は成立しない。C 段では候補ごとの型付き admission を作れても、全空間の有限 sweep にはならない。

一方、列挙可能な部分空間は明確である。`axis_trigger_gating.py:77-83` の現行 5-bit wire 空間、すなわち5 abort 要因の部分集合 32 点である。enum membership だけなので全点の UB 不在を構成的に示せる。これは新空間の下位集合であり、偵察で確認できるのはこの下界だけである。

D1012 の「両 arm を同じ有限契約へ閉じると完全列挙器が構成できる」という識別問題 (`D1012-verbatim.md:25-30`) は、全軸をこの部分空間と同一視しないことで回避する。D1067 により主張も「LLM 必要性」ではなく、固定予算・固定面で事前登録した非 LLM 生成器に対する条件付き優越へ限定済み (`D1067-verbatim.md:3-11`) である。

## reward hack と UB の洗い出し

**直接禁止の復活経路**

- `result_` 代理:
  - `mrctid_` は worker の直前 commit TIDであり、local commit count/progress に近い。
  - `backoff_` は `CCBenchResults` とともに更新されるため、fitness 由来状態の入口になり得る。
  - epoch timers、GC/WAL の残量は時間、成功数、負荷進捗の代理になる。
  - 以上は全禁止する。

- `thid_` 代理:
  - `result_`、callback、container storage の address を整数化すれば安定した worker partition を作れる。
  - `mrctid_` の low bits や epoch/tid 配置も worker と相関し得る。
  - address取得、cast、pointer操作、`mrctid_` は禁止する。
  - 許可した `max_*` にも producer/thread や record 世代との相関は残るため、低位 bit partition を reward-hack review の必須項目にする。

**その他の経路**

- `max_rset_` と `max_wset_` のゼロ/大小関係で read/write transaction class を近似し、特定クラスだけ待たせる。
- abort reason と version 条件を組み合わせ、多数派 record 世代だけ素通しして aggregate throughput を上げる。
- 常 true、常 false、または実 workload で常値になる predicate に縮退する。
- `kUnset` のときだけ member 条件を評価し、非 YCSB abort の stock fallback を破る。
- backoff 発火率を変えて adaptive `backoff_` の吸着点を動かし、gate 単独効果に見せる。

**UB 問診**

- `max_rset_.obj_`、`max_wset_.obj_` は constructor と begin で明示的に0化され、その後も `Tidword` のコピーで更新されるため、`.obj_` の rvalue 読取自体に不定値はない (`transaction.hh:72-73`、`transaction.cc:55-59,191,474`)。
- bitfield の `.tid`、`.epoch`、`.lock` 等は union active-member と実装依存 layout の問題を増やすため許可しない (`tuple.hh:12-24`)。
- clear 済み container の要素参照は無効。size は安全でも恒真、capacity/address は履歴または個体識別になるため型ごと禁止する。
- `status_` は begin 前の初期化を constructor から確認できず、abort 呼出し規約も射影外なので禁止する。
- `latest_log_header_`、`File`、`Backoff`、`TxScanCallback`、`Procedure` の内部契約は射影資料だけでは確認不能。既定禁止する。
- 許可値であっても、除算・剰余・shift・cast・pointer・副作用を許すと UB または非決定性が再導入されるため operator allowlist も必要である。

## positive control 方針

判定は二層である。

- **CC意味論:** 契約どおりの predicate は abort 処理と集合 clear 後に backoff 呼出しの有無だけを決めるため、新しい serializability 不変条件は導入しない。
- **admission意味論:** 「許可観測だけを使い、total、決定的、副作用なし、`kUnset` は必ず stock fallback」という新しい正しさ不変条件を導入する。

後者には通常の §3-C characterization は適用不能である。禁止式は build 前に止めるべきであり、実行して `total_cycles==0` かつ `violation>0` を観測する対象ではない。また UB は実行時に必ず再現するとは限らず、既存 UBSan には無関係ノイズの既知限界もある (`axis-onboarding.md:243-245`)。

従って設計方針は次のとおり。

1. admission gate の mutation-red は、禁止面ごとの独立入力が構造化 reject になる静的 negative control とする。
2. `result_`、`thid_`、clear 済み container、pointer/cast、ゼロ除算、shift、追加代入、`kUnset=false` を別検査点にする。
3. 既存の abort reason misattribution は単一スレッド characterization が適用可能なので、その positive control を維持する (`existing-sheet-2026-07-10.md:158-169`)。
4. fairness/liveness は characterization 不可能な死角として規律3へ送る。指標は per-thread/per-class gate-pass率、commit率、Giniまたはmax/min比、abort継続時間、無進捗timeout。発火閾値は未定で、事前登録前に親裁定が必要。
5. hole に帰属できる sanitizer signal、compiler warning、異常終了が一件でも出た場合は certified にせず indeterminate とする。

## 既存シートとの差分表

| §2 欄 | 差分 | 既存根拠 |
|---|---|---|
| 軸名 | 据え置き | `existing-sheet-2026-07-10.md:27` |
| 変異型 | 表記はコード片のまま。意味を現行5-bit wireから非列挙コード片へ戻す | `:29` |
| SOURCE_REL | 据え置き | `:31-42` |
| マーカー ID | 据え置き | `:44` |
| hole 位置と骨格 | 1行代入 hole と外側 gate は据え置き。コメントと admission 契約を改訂対象にする | `:46-82`、現行実装精緻化 `:18-21` |
| 構文契約 | **変更**。enum+定数から、正確な二つの member observation を追加。旧禁止は全維持し、代理面を追加禁止 | `:84-93` |
| stock 動作 | 据え置き | `:95-100` |
| フラグ名 | 据え置き | `:102-106` |
| 壊しうる不変条件 | **変更**。member 式の UB、input isolation、version/class 条件付き fairness を追加 | `:108-127` |
| verifier の死角 | **変更**。member 値、gate decision、admission失敗、UB最適化を追加 | `:129-136` |
| reward hack | **変更**。`result_` / `thid_` の代理復活、address、progress、low-bit partition を追加 | `:138-156` |
| positive control | **変更**。既存 misattribution control を維持し、静的 admission mutation-red を追加。新部分への characterization は不適用 | `:158-169` |
| 偵察の列挙空間 | **変更**。32点を全 coder 空間から列挙可能な部分空間へ位置づけ直す | `:171-191` |
| 感度 workload | 据え置き。偵察具体値は転記しない | `:193-198` |
| 計測動作点 | 据え置き。部分空間の既存動作点として限定 | `:200-203` |

## C 段必須条件リスト案

1. **段階B出口を満たす。** 本草案を3レンズが全員 adopt または adopt-with-conditions とし、改訂契約と以下の条件を D 番号で凍結できたこと (`axis-onboarding.md:24-30,115-125`)。
2. **allowlist を observation 単位で凍結する。** 許可集合が `max_rset_.obj_`、`max_wset_.obj_` の二つだけで、未列挙 identifier と `this` 経由の迂回が既定拒否になること。
3. **単一 owner 前提を実コードで証明する。** TxExecutor と両 Tidword に hole と並行する writer がないことを callsite/lifecycle から確認する。証明できなければ二候補とも禁止へ倒すこと。
4. **型付き pre-build admission を設計する。** identifier、member chain、operator、literal型、単一代入、`kUnset` fallback を build 前に機械検査し、欠落、未知構文、parse不能をすべて例外停止できること。`DiffQuarantine` 単独を意味保証として数えない。
5. **proxy 禁止を機械契約へ反映する。** `thid_`、`result_` に加え、`mrctid_`、epoch、backoff、container、pointer/address、transaction class flag を禁止リストへ追加し、各々の negative test が赤になること。
6. **hole の単一代入性を実証する。** marker 内で変更可能なのが predicate 代入一個だけで、変数宣言、gate 呼出し、sentinel reset、reason store、stock 枝が frame として不変であること。現行 generic quarantine の複数行許容を別の gate で閉じること。
7. **stock inert と identity を再実証する。** flag 0 が pinned stock と同一 `src_token="stock"`、flag 1 の実変更が別 digest、TRACE diff-of-diffs が一致すること (`source_digest.py:2051-2086,2108-2117,2195-2235`)。
8. **骨格中立性を再確認する。** enum store、begin sentinel reset、gate scaffold が abort 分岐、commit path、共有DB更新を変えないこと。理由記録7点の全数性も維持する。
9. **positive control を分離して通す。** 既存 misattribution characterization は `total_cycles==0` かつ `violation>0` で indeterminate、追加 admission mutation-red は build 前 reject とし、二種類を混同しないこと。
10. **UB 問診を executable gate にする。** 除算、剰余、shift、cast、pointer/reference traversal、関数呼出し、副作用、未対応 token が受理されないこと。compile成功を安全性証明に代用しないこと。
11. **残存 fairness/liveness を規律3へ登録する。** per-thread/per-class gate率、commit率、Giniまたはmax/min、無進捗時間の指標、発火条件、indeterminate条件を事前に凍結すること。
12. **列挙可能部分空間を維持する。** `GATEABLE_REASONS` 5-bit、退化点、stock 対照が改訂後も有効で、全非列挙空間の代表性は主張しないこと (`axis_trigger_gating.py:73-83`)。
13. **偵察 firewall を維持する。** 下流 coder/planner に渡すのは軸が生きているという二値だけで、具体候補、順位、利得値を渡さないこと (`axis_trigger_gating.py:11-16`)。
14. **正本同期の変更集合を事前列挙する。** skeleton comment、frozen block bytes、syntax contract、forbidden registry、軸定数が同一契約を表し、不一致が fails-closed になること。§7.1 の共通資材は変更対象に含めない。
15. **C出口の実測責任を明示する。** 関連テスト、identity、negative controls、positive control の実走は親が行い、未実走を緑と記録しないこと。

## 未定・親裁定を要する点

- `Procedure`、`Backoff`、`LogHeader`、`File`、`TxScanCallback` の定義は今回の必読射影に含まれない。従って関連メンバは禁止で確定した。将来許可候補に戻すなら型定義と全 writer を射影した別レビューが必要。
- TxExecutor の単一 worker 所有は patch コメントには記載されるが、実 callsite は今回の射影外である。二つの allowlist 観測の data-race 不在はC入口で裏取りが必要。
- fairness/liveness 観測の数値閾値は未定。今回の静的資料から事前登録値を導けないためである。
- 「非列挙」を構文候補集合で判定するか、有限幅入力上の意味論的同値類で判定するかの権威的定義は射影資料にない。本草案は §3-D の運用上必要な「契約から有限 candidate set を生成できるか」で判定した。親のD番号凍結時に明記すべきである。
- read-heavy floor の具体的再較正要否は既存条件を維持したが、新規実測は本段の scope 外である。

## 総括

条件付き採用案は、既存 hole と stock 骨格を保ち、CC-native allowlist を `max_rset_.obj_` と `max_wset_.obj_` の二観測だけに拡張するものである。`mrctid_`、backoff、epoch、GC/WAL、pointer、transaction class は `result_` または `thid_` の代理になり得るため禁止する。

全コード片空間は有限 sweep 不能だが、現行 5-bit wire 空間を列挙可能で構成的に安全な部分空間として保持できる。正しさゲートを緩めずに採用するには、C 段前に typed admission、proxy 禁止、UB negative control、single-owner 証明を必須条件として凍結する必要がある。

ファイル変更とテスト実走は行っていない。結論は指定資料に対する静的検査のみであり、テスト緑は主張しない。