## (P1)〜(P5) の正誤

| 仮説 | 静的照合の結果 |
|---|---|
| **P1：読み取り再検査が新版を飛ばす** | **成立し得る。原因としては未確定。** 読み取り専用 tx は `rts_` で版を選び、`later_ver_` を保存する（[transaction.cc](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/ccbench-G/cc/cicada/transaction.cc:92)）。promotion は `update()` の後に `is_ronly_=false` とする（[transaction.hh](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/ccbench-G/cc/cicada/include/transaction.hh:201)）。再検査は保存済み `later_ver_` から始まる（`transaction.cc:543–550`）。その後に挿入された、`rts_` より新しく `wts_` より古い確定版を飛ばせる。ただし、既存の巡回との因果関係は未測定。 |
| **P2：TPC-C の `bad_alloc` の三候補** | **いずれも未確定。** (a) promotion 後の本来の `update()` が `searchWriteSet` で素通りする経路は実在する（`transaction.cc:205`）。(b) INSERT abort の UAF も実在する。(c) `TupleBody` の複写は値を再確保する（[tuple_body.hh](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/ccbench-G/include/tuple_body.hh:32)、[heap_object.hh](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/ccbench-G/include/heap_object.hh:122)）。例外送出点が無い現状では順位を付けない。 |
| **P3：INSERT tuple の解放を clean 後へ移す** | **方向は正しいが、そのままでは不完全。** `writeSetClean()` は末尾で `write_set_` を消す（`transaction.hh:367`）。削除対象を先に退避し、索引から除去 → clean → tuple を解放する必要がある。 |
| **P4：G と gc 修理 tip の merge** | **妥当。** G の変更は promotion 周辺・`read_internal()`・`commit()`、gc 修理は `scan()`・`gc_records()`。同じ `transaction.cc` だが差分の行は離れており、提示された差分には同一行の競合が無い。実 merge の無衝突はまだ主張しない。 |
| **P5：D297 は拒否を記録し、非 Cicada 文脈は F の結果を引く** | **限定付きで妥当。** 新 tip の D297 *pass* にはならない。Cicada 固有 macro で検査器が fails-closed する既知の拒否を記録し、F→新 tip の非 Cicada path 差分が 0 なら、T-2854 の選定文脈についてのみ C→F の結果を引き継ぐ**推論**と明記する。pin 前進時の新 tip 判定は別件のまま残す。 |

## 単位 D — 帰属の診断

**土台の G＋gc 修理で、修理前に行う。** 前 wave の起動器・1 秒 cell を複製し、固定 SHA・`compile_commands.json` の macro・実行 argv・stderr・判定器 JSON を同じ job に残す。診断計器は repo 外の使い捨て patch とし、性能値には使わない。

1. **YCSB K・R、4 thread、各 1 秒、対照と診断版を交互に各 2 回。** `read_internal()` の選択時に `is_ronly_`、`rts_`、`wts_`、読んだ版と `later_ver_` の wts を保持し、`inlineVersionPromotion()` の試行・`update()` の成功／early abort・`is_ronly_` の転換を計数する。`validation()` の再検査直前には「現行の `later_ver_` 起点」と「診断専用の latest 起点」を**判定を変えず**双方走査し、結果が違う件数、飛ばした確定版の wts、当該 tx の commit 件数を出す。`transaction.cc:543–569` の実際の合否は維持する。trace の C 行へ tx の wts を対応させ、判定器 witness の `rw` 辺の key・版・tx と突き合わせる。latest 起点で違いがなく巡回が残れば P1 を退ける。
2. **競合候補を分ける観測。** 読み取り専用からの転換が必要かは、その転換だけを止める使い捨て版で比較する。`rts_` 読みと `wts_` 書きの混在は各読取の timestamp と commit wts を照合する。early abort が `Status::OK` を返す経路（`transaction.cc:253–261,291–297`）は status・write set・commit を数える。本来の `update()` の素通りは同じ `(storage,key)` の promotion 書込みと後続 `update()` を数える。版の回収・再利用は複写元 pointer／wts と `gcAfterThisVersion()`・`newVersionGeneration()` の解放／再利用事象を照合する。各候補について**巡回を含む commit tx に事象があるか**を判定する。
3. **TPC-C M・R2、4 thread、各 1 秒。** まず TRACE=0 の Debug または ASan 版で最初の例外／メモリ報告を採る。`gdb catch throw` なら送出点と呼出し鎖を採り、`TupleBody` のコピー／`HeapObject::allocate()`、INSERT abort、後続 `update()` のどれかを特定する。続けて「promotion 無効」「読み取り専用 promotion だけ無効」「UAF だけ使い捨て回避」「後続 `update()` の素通りだけ回避」を、一度に一要因ずつ土台と交互に走らせる。TPC-C は読み取り専用指定を立てないため、読み取り専用 promotion の停止で TPC-C も直るとは予測しない。例外が消えた組だけを根拠にせず、最初の backtrace と発火計数を合わせて帰属する。最小の入口は M・R2 各 1 走、再現が不安定な条件だけ各 2 走へ増やす。

既存の raw trace は索引と先頭だけを利用する。前 wave の「K 4、R 327 巡回」「TPC-C は TRACE=0 でも異常終了」「重複 read 登録を戻しても巡回」は再現の事前情報であり、原因の証拠にはしない。

## 単位 F — 修理の分岐

原論文 §3.1 は読み取り専用 tx が `rts` の固定 snapshot を読み、read set を検証しない規則である。§3.3 は可視の非 inline 版を同じ値で RMW に格上げする規則、§3.4 は書込み tx が自分の timestamp で読取版を再検査する規則である。修理はこの三つを同時に満たすものに限る。

- **P1 が witness に帰属した場合の最小案:** `transaction.hh:201–213` で `is_ronly_` の tx は promotion を試みず、`rts_` snapshot のまま commit させる。`read_internal()` の読取登録と `commit()` の読み取り専用経路は維持する。読み取り専用 workload では inline 化機会が減るため性能は低下方向を見込むが、競合書込みと abort は減り得る。予想だけで性能値は書かない。
- **読み取り専用 tx の promotion を残す必要があり、P1 が真の場合:** `transaction.cc:543–550` の再検査を、転換前に `rts_` で読んだ要素に限って latest から開始し、`wts_` 時点の可視版と `ver_` を比較する。`later_ver_` の早道を使わない。さらに転換までの全読取を同じ `wts_` の再検査へ含める。検査増で遅くなる方向。原論文の RMW を保てるが、前案より変更と証明範囲が広いので、診断で必要性が出た場合に限る。
- **後続 `update()` の素通りが実害の原因なら:** `transaction.cc:205` で既存 write 要素が promotion 由来のとき、`new_ver_->body_` を後続の本来の body で置き換える。INSERT 等の別種の既存 write は従来どおり扱い、promotion 由来を識別できる最小の状態に絞る。書込み集合の版は一つに保ち、read／write validation を省かない。コピー・分岐分の負担は増えるが、失われた書込みを復元する。
- **early abort または版寿命が帰属した場合:** `Status::OK` を返すだけを独立の巡回修理と決めつけない。`status_=aborted` の tx が commit している証拠ならその経路を修理し、そうでなければ別の戻り値整理に拡げない。複写元の UAF が ASan／backtrace で確認された場合は、`transaction.hh:207` のコピー前に版の寿命を保証する修理を選ぶ。単に例外を捕まえる案、read 再検査や判定器を省く案は採らない。

各案の受入前に、既定 genome の Cicada TU の**前処理出力**を土台と比較する。promotion guard 内だけの修理なら既定では一致する見込み。一方、UAF 修理は既定の `abort()`／`writeSetClean()` 本文を変えるため、既定 genome の前処理出力が不変とは言えない。変更箇所と意味を明示する。計装 2 本は hunk の実文脈を確認済みで、trace patch は `transaction.hh` の promotion 関数**直前**、`newVersionGeneration()` 直後、`transaction.cc` の `writePhase()` と `commit()` に挿入する。TPC-C patch は計装が作る `traceCommit()` 本文に重ねる。修理で関数宣言・その前後の文脈を動かさなければ fuzz なしで当たる見込みだが、tip に対する `git apply --check` の結果を記録する。promotion の TRACE=1 は既存 patch の `#error` が残るため、正しさの小走行だけ repo 外の診断変種を使う。

**UAF は P3 の順序案を採る。** `transaction.cc:745–754` で INSERT の tuple pointer を退避し、索引から除去し、`writeSetClean()` の後に退避した tuple を解放する。`writeSetClean()` の INSERT を単純に `continue` する案は UAF を避けるが、`continuing_commit_` と install 済み `new_ver_` の後始末も飛ばすため採らない。`INLINE_VERSION_OPT=1` なら `new_ver_` が tuple 内の inline 版であり、clean 前の delete は直接 UAF、clean 後の delete は有効。`OPT=0` なら `new_ver_` は別確保で、tuple の解放だけではその版を解放しない。`REUSE_VERSION=0/1` の双方で、現行の INSERT 要素は `finish_version_install_=true` として clean 時に aborted にされるだけなので、この別版の既存の未回収状態は**順序変更だけでは直らない**。`REUSE_VERSION=1` でも INSERT 版を直ちに reuse pool へ移さない。別の読者がその版を参照し得る寿命の設計なしに再利用すると新しい UAF を作る。四組合せで「tuple の UAF が消える」「非 inline INSERT 版の既存の未回収は残る」を分けて記録する。

## 土台

G `eb93423b` と gc 修理 tip `81fc4a84` は共通の F `25898d00` の子である。新しい local branch に両者を merge し、その merge tip を修理前の対照とする。G だけを土台にすると、削除を含む TPC-C の gc 既知欠陥が確認を妨げる。gc 修理だけを土台にすると promotion の build 修理を取り込み直す必要がある。merge なら既存 SHA と人間の push／まとめ方の選択肢を保持できる。

衝突の静的見込みは低い。G の `transaction.hh:207,210`、`transaction.cc:131,924–925` と、gc 側の `transaction.cc:432,853` は離れている。計装 patch の `commit()`／`writePhase()` 周辺と gc patch の二箇所も離れる。gc 修理 patch 2 本は merge tip に既に含まれるので**再適用しない**。既存 Cicada 系 patch は、計装 2 本と壊し patch のうち実際に使うものを merge tip に fuzz なしで照合し、当たらないものは旧 preimage 向けと記録して必要な診断用複製だけ適応する。gitlink と pin は動かさない。

## 確認・正例・CI・D297

修理前 merge tip と修理後 tip を**同じ job で交互**に実行する。8 genome は `INLINE_VERSION_OPT=1 ∧ INLINE_VERSION_PROMOTION=1` と残りの軸の正準値を `build_genomes.py` から取り、両 tip で build・macro 束縛を確認する。正しさは各 tip の代表 promotion genome で YCSB K・W・R・P、TPC-C M・R2 を各 4 thread・1 秒で判定する。修理後は全 cell で巡回 0、integrity の数値項目 0、存在履歴違反 0、C 行＝commit 数、`READ_WTS_MISMATCH` 0、判定器 rc∈{0,3} を要求する。巡回 0 の上限は *indeterminate*。TPC-C M・R2 は修理前後を各 3 回交互に走らせ、修理前の `bad_alloc` 再現と修理後の全回完走を対にする。ASan は Debug・`ENABLE_SANITIZER=ON`・`ASAN_OPTIONS=detect_leaks=0` の M ×4 thread を修理前後各 2 回以上とし、修理前の INSERT abort UAF 報告と修理後の `ERROR: AddressSanitizer` 0 件を対にする。修理前の期待失敗を job 全体の失敗として捨てない。

**正例は原因確定後に一本作る。** P1 が真なら `broken-cicada-promotion-stale-recheck.patch` として、修理後の読み取り専用 promotion 抑止、または転換読取の latest 起点再検査の**該当修理だけ**を壊す。preimage は「修理後 tip → `instr-cicada-trace.patch` → 診断用の promotion 対応 → 壊し」で、壊しは無条件 patch とする。`CICADA_BREAK_EVENT slug=promotion-stale-recheck tx_wts= key= a_wts= b_wts=` は**壊した条件を通って commit した tx だけ**、終了時は先例どおり `CICADA_BREAK_FIRED reached= changed= committed=` を出す。判定器の巡回 witness の tx・key・版を event と照合し、巡回の辺に壊した経路が入ること、他の integrity 数値項目が 0 で**巡回という単一理由で赤**になることを確かめる。P1 が反証されたら、確定した promotion の一箇所を壊す同形の patch に切り替え、原因未確定のまま P1 の壊しを正例と呼ばない。

CI は前 wave の `check_format_ci.sh` と `run_ci_build.sh` の実行本文を流用できる。前者は追跡対象約 213 file に clang-format 14 `--dry-run --Werror`、後者は CI image で Release・sanitizer OFF の全 protocol build を行う。ただし両 script の **F の直子／変更 path／G SHA という入力固定検査は merge tip・新 tip 用に直す**。CI の既定 build だけでは promotion の非既定分岐を検査しないので、上の 8 genome build と対にする。D297 は P5 の限定に従い、拒否 rc と F→新 tip の path 差分を記録する。検査器や受理条件は緩めない。

## 所有・並列・見積り

依存順は **D の帰属 → 親の原因裁定 → F の修理 → 対照確認・正例**。D の所有は repo 外 job 本体と使い捨て計器である。F は CCBench の `cc/cicada/transaction.cc`・`cc/cicada/include/transaction.hh` に限る。正例担当は repo 内の `patches/broken-cicada-promotion-*.patch` と `patches/README.md` の節を所有し、job 本体は repo 内 scratch に起草して親が job dir へ移す。F の原因裁定後は修理実装と正例・確認 script の準備を並行できるが、正例の最終 hunk と受入走行は修理 tip に依存する。指定された forwarding 系、version-lifetime patch、gitlink、`pin.py`、model tool には触れない。

既往の所要を上限寄りに使う見積りは、D の診断 build・小走行・判定 **8 条件 × 45 秒＝360 秒**、8 genome の前後 build **16 × 12 秒＝192 秒**、6 cell の前後判定 **12 × 35 秒＝420 秒**、TPC-C 追加反復 **8 × 20 秒＝160 秒**、ASan **4 × 75 秒＝300 秒**、壊し・CI **250 秒**、予備 **600 秒**で計 **2,282 秒、約 0.64 node 時間**。これは前 wave の実測 690 秒、gc wave 1,024 秒を踏まえた投入前見積りであり、未実測。複数 node に分けても node 時間を合算し、2 node 時間に達する見込みになれば投入前に再見積りする。

## 総括

静的に確認できた欠陥は、`rts_` で読んだ要素を `wts_` で再検査するときの起点不整合、promotion 後の `update()` 素通り、INSERT abort の UAF である。既存の巡回と `bad_alloc` をどれに帰属させるかは未測定である。先に D の witness・backtrace・一要因対照で原因を決め、その結果に必要な最小修理だけを merge 土台へ載せる。今回の指定に従い、ファイル編集・build・テストは行っていない。