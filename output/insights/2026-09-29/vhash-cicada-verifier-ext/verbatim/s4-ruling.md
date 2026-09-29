# 段 4 裁定 — [md_17] Cicada の正しさ検査を insert / delete と TPC-C へ広げる (2026-09-29 15:0x JST)

入力: s1-brief.md、plan.md (段 2)、consult-a.md (A1〜A7)、consult-b.md (B1〜B5)。裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) を段 4 直前に再走査: 最新は 2026-09-28 full39、wave 開始後の更新なし、Cicada / md_17 / T-2874 の語 0 件。local main は起点 `035fc11fa` から不動。
ユーザーへの差し戻しは行わない (記憶「needs input は出さず codex と決める」)。割れた論点は相談 2 本を材料に親が決め、根拠をここと fragment に残す。

## R0. 親の追加実測 (段 3 後、段 4 前)

- stock の insert の abort (`cc/cicada/transaction.cc` の `abort()`) は、INSERT の write set 要素について `remove_value` の後に `delete we.rcdptr_` で tuple を解放し、その後の `writeSetClean()` (`cc/cicada/include/transaction.hh:343-365`) が同じ要素の `rcdptr_->continuing_commit_` に書く (解放後の書き込み)。INSERT の新版は `finish_version_install_` が立たないので、`REUSE_VERSION=1` では状態 `unused` にして再利用 pool へ戻す。pending のまま待っていた読み手 (`read_internal` の待ちループ) は、`unused` が committed / deleted / pending / aborted のどれでもないので抜けられない形である (未実測の静的読み)。
- → 「未確定の insert 版を読ませる」型の壊し (G1a を狙う) は、inserter が abort すると解放後使用・無限待ちに当たりうる。判定器より先に異常終了する壊しは正例に使えない。
- 判定器の `orphan_reads` は件数だけで、行の詳細は出さない (`orchestrator/verifier/dsg.py:210-302,728-768`、`model.py:475`)。
- YCSB に insert / delete は無い。BOMB (`external/ccbench/include/bomb.hh`) には insert / delete がある (相談 A5)。

## R1. 所見の裁定

| ID | 裁定 | 採否と内容 |
|---|---|---|
| A1 / B2 / B3 read 検査を取引種別で絞った変異は insert / delete の検出力を示さない | real | 採用。plan §6 の候補 1・2 は insert / delete の正例に数えない。R4 で、insert の意味そのものを壊す正例 1 本 (β) を新設し、巡回の検出経路は既存の壊し patch を TPC-C に重ねて確かめる (α)。 |
| A2 / B4 中途失敗 insert の残骸と stock の停止条件 | real | 採用。R5 の生死確認に停止条件を固定する (stock で integrity・存在履歴・C 数・READ_WTS_MISMATCH のどれかが非 0、異常終了、walltime 到達のいずれかで本走と正例を止め、原因を記録する)。R0 の abort の潜在欠陥は stock Cicada の事実として一次資料に書く (直さない。CCBench の変更は所有外で、上流 CI・pin の手続きが要る — D2277)。 |
| A3 不在読み・scan の範囲は巡回グラフに入らない | real | 採用。一次資料・README・fragment の主張を「TPC-C 走行で**記録された点読みと書き**から、巡回と integrity・存在履歴の違反を検出する」に限定する。phantom (空の scan・範囲への insert) は未対応、設計メモのみ (P6)。 |
| A4 / B1 campaign の受理経路につながらない | real | 採用。成果は repo 外起動器による診断走行。「評価計画の TPC-C が門の対象になった」とは書かず、「門の前提 (trace と検出) の一部を実測した、campaign 接続・Cicada の証拠面・phantom は未対応」と書く。campaign 接続は insight の「後続に要るもの」に記録 (起票しない)。 |
| A5 BOMB にも insert / delete | real | 採用。brief の親実測を訂正する。本 wave の検査は YCSB (md_3) と TPC-C。BOMB / SBOMB は TRACE=0 の命令列比較だけの対象と明記する。 |
| A6 TPC-C は read-only 早期 return を使わない | real | 採用。TPC-C の C 行数は通常の commit 経路で照合する。read-only 経路は YCSB 用と記す。 |
| A7 READ_WTS_MISMATCH を負例の条件に | real | 採用。stock の合格条件に `CICADA_TRACE_READ_WTS_MISMATCH n=0` を加える。非 0 なら R2 の停止条件。 |
| B5 TRACE=0 の二系列 | real | 採用 (plan §7 どおり)。 |
| plan §1〜§5・§7〜§10 | 採用 | 重ね patch・C1' 基点・v3 切替・判定器不変・fixture 追加なし・二系列の TRACE=0・phantom 設計メモ。 |

## R2. 置き場と所有 (D fragment)

- `patches/instr-cicada-trace.patch` の bytes は変えない。TPC-C の v3 出力は新 patch `patches/instr-cicada-trace-tpcc.patch` を instr patch の上に重ねる。base は C1' `6aa7a58f` 以降 (pin C 単独には重ねない。起動器が base OID を記録し、pin C に重ねた TRACE=1 build をしない)。依頼の「instr-cicada-trace.patch の更新」は「instr-cicada-trace 系の更新 = 重ね patch の新設」と読み替える (1 本に統合すると pin C の TRACE=1 compile が壊れ、md_14 の YCSB 検査を止めるため)。
- pin の C2' 系への前進 (D2277 項 1、並走 wave) の後は、重ね順の厳密適用と生死確認を取り直す (md_3 の 4 patch と同じ扱い)。
- 判定器 production・テストは変えない。`patches/ledger.json` は触らない (entries 1 件固定)。

## R3. プラン v2 (段 5 の単位)

- **単位 T (Codex author、先行):**
  - `patches/instr-cicada-trace-tpcc.patch`: `traceCommit()` で `izanagi_trace::tpcc_tx_type()` を 1 回読み、非 0 なら v3 (C = `txid thid hi lo nR nW 0 0 tx_type`、R / W は表 = `storage_` の整数、`emit_*_v3` を使う)、0 なら既存 v2 の式をそのまま通す。E の直後に `izanagi_trace::clear_tpcc_tx_type()`。`tpcc_cicada.cc` の main で `initial_wts` を渡し `CICADA_TRACE_INITIAL_WTS=` と終了時報告 (ycsb と同形)。追加は `#if TRACE` 内だけ、`#else` 側に `#line`。`#if` 条件語は `TRACE` だけ、`IZANAGI_` の語を含めない。
  - repo 外起動器 `.cicada-launcher/launch_cicada_run.py` (md_3 の版を複製し拡張、親が job dir へ退避): base OID (pin C / C1')・target (ycsb / tpcc / bomb / sbomb)・schema (v2 / v3)・patch 順を build spec に持つ。TPC-C の flag (`tpcc_num_wh`・`tpcc_perc_*`・`thread_num`・`extime`・`group_commit=0`)。v3 の判定 JSON (`result_to_dict_v3`) から巡回・`integrity` 数値項目・`existence_violations` を集計。identity mode を target 引数化し、R6 の二系列を取る。
- **生死確認 (親、単位 T の統合後、1 job):** R5 の L0。
- **単位 B (Codex author、生死確認成立後):** 正例 β の patch と、起動器の帰属解析 (β は raw trace から orphan read を数え直す、α は v3 の表付き witness 照合)。

## R4. 正例 (事前登録、実装前)

完了判定 (ii) の読み替え (記録する): 依頼は「insert / delete を壊した patch を判定器が**巡回として**検出し、壊した経路に帰属できる」。TPC-C では NewOrder 行を読むのは Delivery だけで、Delivery は読んだ行を自分で削除するため、delete 経路の単一 site の壊しは他の検査 (install 時の最新版検査・validation (a)(b)) に止められ、committed な巡回を作らない (段 2 plan §6、段 3 A1 / B3、親の読み)。insert の意味を壊した履歴は、TPC-C では巡回より先に「生産者の無い版の読み (orphan read)」「存在履歴違反」として判定器に現れる。そこで (ii) を次の 2 本で満たす。判定器の門 (巡回 0 かつ integrity 数値項目 0 かつ存在履歴違反 0 でなければ失格) は変えない。

| id | patch | 壊し方 (単一 site) | 期待する検出 | 帰属規則 |
|---|---|---|---|---|
| β | `broken-cicada-insert-past-ts.patch` (新) | `insert()` で作る新版の wts を、自分の wts ではなく begin 時の読み時刻 `rts_` にする (新版生成の直後 1 か所、`cc/cicada/transaction.cc` の `insert`)。insert した行が、自分より前に直列化された読み手に見える (版の時刻と commit の時刻が食い違う insert) | orphan read > 0 (R の版に生産者の W が無い)。存在履歴違反・巡回は観測値として記録 (期待しない) | 起動器が raw trace で「R の (表, key, 版) に一致する W が無い」行を数え、その件数が判定器の `orphan_reads` と一致し、かつその R のうち 1 件以上が事象 `CICADA_BREAK_EVENT slug=insert-past-ts … table=<表> key=<hex> a_wts=<公開した版の wts>` の (表, key, a_wts の版) と一致する |
| α | 既存 `broken-cicada-skip-read-recheck.patch` (bytes 不変) を TPC-C に重ねる | validation の read set 再検査で不一致でも abort しない (md_3 と同じ) | non-serializable (巡回) | md_3 R4 の規則を v3 に拡張: witness の巡回に、事象の txn から事象の key 上で rw 辺があり、その辺の読んだ版が事象の `a_wts` の版と一致する (表は辺の reason の table を記録) |

- β の診断は既存 3 本と同形 (事象を thread ごとに溜め、その txn が commit したときだけ全件出す。終了時に `CICADA_BREAK_FIRED slug=insert-past-ts reached=… changed=… committed=…`)。事象行に `table=` を足す。`IZANAGI_` の語を含めない。無マクロの無条件 patch で、正例の build にだけ重ねる。
- β は `rts_` < 自分の wts が常に成り立つ (begin で `rts_ = MinWts - 1`、`wts_` は rdtscp 由来) ので changed = reached を期待するが、観測値をそのまま記録する。β の版は latest なので GC に回収されない。β が異常終了・hang した場合は正例不成立として記録し、判定を緩めない。
- 分類: 「期待した経路で検出」= 期待する検出が成立し帰属規則を満たし、同じ cell の stock 対照が合格 (R5 の負例条件)、かつ正例 run 自身の framing 違反 0・C 行 = commit 数。「検出したが帰属不能」「盲点」(committed > 0 で検出 0)「未発火」(changed = 0) は md_3 と同じ。
- **完了判定 (ii):** β が「期待した経路で検出」かつ α が「期待した経路で検出」。満たさなければ判定を緩めず事実を一次資料に書き、段 4 へ戻る。
- delete 経路の正例は作らない。理由 (上記) と、delete の壊しが検出されない形 (木から早く外す・除去を飛ばす → R が出ず不在として消える) が phantom と同じ盲点であることを一次資料に書く。

## R5. cell・job・停止条件 (事前登録)

共通: warehouse 1 (`tpcc_num_wh=1`)、`extime=1`、`group_commit=0`、`tpcc_interactive_ms=0`、CMake は md_3 と同じ受理構成 (`INLINE_VERSION_OPT_CICADA=0 INLINE_VERSION_PROMOTION=1 REUSE_VERSION=1 SINGLE_EXEC=0 WRITE_LATEST_ONLY=0 TRACE=1`)、base = C1' + instr + tpcc 重ね patch (正例はさらに重ねる)。

| cell | `tpcc_perc_payment / order_status / delivery / stock_level` | NewOrder | 使い道 |
|---|---|---|---|
| M (段 1 mix) | 43 / 0 / 0 / 0 | 57 | stock 負例 (insert のみ、delete なし) |
| F (全 mix) | 43 / 4 / 4 / 4 | 45 | stock 負例 (insert・delete・scan)、α |
| S (読み重視) | 43 / 4 / 4 / 20 | 29 | stock 負例、β (StockLevel が最近の OrderLine を読む) |

| job | 内容 | 期待 |
|---|---|---|
| L0 (生死確認) | stock の M・F × thread 1・4、trace 量と verifier 所要の実測、TRACE=0 の R6 二系列 | 全 run: 巡回 0、`existence_violations` 0、integrity 数値項目 0、framing 違反 0、C 行 = stdout の commit 数、`READ_WTS_MISMATCH n=0`、全 W の版 > initial_wts。identity は命令列一致・trace 語残存 0 |
| J1 (本走) | stock の S × thread 4、F × thread 4 (対照) + β の S × thread 4 + α の F × thread 4 | 対照は L0 と同じ。正例は R4 |

- 停止条件 (A2 / B4): L0 の stock でいずれかの期待が外れる、異常終了、walltime 到達のどれかなら、J1 と単位 B を止めて原因を調べ、一次資料に事実を書く。判定器・期待を緩めない。
- trace 量・verifier 所要が L0 で過大 (1 run の verifier が 10 分超) なら、thread 数を減らした cell を段 4 追補として登録してから J1 を走らせる。
- 未発火・盲点・帰属不能の正例は、事前登録の焦点 cell (S / F の thread 8) で 1 回だけ再走してよい。
- 見積り: L0 ≈ 15 分 (build 4〜5 本 + TPC-C 小走行 4 + verifier)、J1 ≈ 15 分、焦点再走 ≤ 10 分。受入・焦点走 ≈ 30 分。合計 ≈ 1.2 node 時間 < 2 (L0 実測後に更新)。

## R6. TRACE=0 (絶対規律 1)

同じ compile command (checkout root だけ置換して一致を確認) で TRACE=0 build を比べ、objdump の命令列 (md_3 の正規化) を合否の根拠、前処理出力と nm / strings を診断とする。
- (i) pin C 対 pin C + instr: tpcc・bomb・sbomb の各 target の 3 TU (`transaction.cc`・`util.cc`・workload TU)。md_3 が未比較と明記した範囲を埋める。
- (ii) pin C 対 C1' + instr + tpcc 重ね patch: tpcc target の 3 TU。C1' の `include/tpcc.hh` の `#line` を含む差分の影響も含めて「pin と一致」を直接確かめる。
- 期待: 全 TU で命令列の差分 0 byte、trace 語 (`izanagi_trace`・`CICADA_TRACE`・`tpcc_tx_type`) の残存 0。一致しなければ規律 1 違反として止める。

## R7. 変異 (DW-M01 事前登録)

- **実系の変異 = R4 の正例 2 本** (Cicada の実装への単一 site の変異。kill = 分類「期待した経路で検出」)。単一理由性: β は insert の版の時刻だけを変え、他の検査は insert を検査しない (validation の install・(b) は INSERT を飛ばす、`transaction.cc` の validation 冒頭 2 か所)。α は md_3 で単一理由性を確認済み。
- 本 wave は判定器・テストを変えないので pytest の変異 matrix は置かない (実装面は patch と repo 外起動器で、実走で検証する。md_3 R6 の先例)。
- 起動器は repo 外で、変異 matrix の対象外。

## R9. 追補 (15:5x JST、L0 の停止条件成立を受けて。R4・R5 の事前登録は書き換えず、ここで差し替える)

事実 (`l0-result-summary.md`): stock の M t1・M t4・F t1 は L0 の期待をすべて満たした。TRACE=0 の命令列比較は (i)(ii) の 12 TU とも一致。**stock の F t4 (Delivery を含む全 mix、4 thread) は benchmark 自体が `gc_records()` の `ERR` (`cc/cicada/transaction.cc:853`) で異常終了した (1 走行中 1)。** R5 の停止条件に当たるので J1 と単位 B を止めた。判定器・期待は緩めない。

1. **原因の切り分け (新 job `GC-PROBE`、事前登録):** trace の有無で異常終了が変わるかを反復で測る。(a) pin C 無 patch の TRACE=0 build で F × thread 4 を 5 回 (判定器は掛けない。rc と stderr の `ERR` 行を記録)、(b) C1' + instr + tpcc 重ね patch の TRACE=1 build で F × thread 4 を 5 回 (完走した run は L0 と同じ判定・合否を記録)。期待を置かず観測値を記録する。(a) で 1 回以上異常終了すれば「stock Cicada (pin C) の delete 経路の欠陥で、trace の有無に依らない」と書く。(a) が 5 回とも完走し (b) だけ落ちるなら、観測者効果の疑いとして記録し、trace patch の変更は別途裁定する。
2. **正例の cell を差し替える:** delete (Delivery) を含む cell は、4 thread では stock 自体が落ちるので、stock 対照の合格を要する正例に使えない。β は新 cell **R2** (`tpcc_perc_payment / order_status / delivery / stock_level` = 43 / 4 / 0 / 20、NewOrder 33、StockLevel が最近の OrderLine を読む、delete なし) × thread 4、α は **M** × thread 4 (NewOrder / Payment の競合) とする。対照は同じ cell の stock。R4 の帰属規則・分類・完了判定は変えない。
3. **J1 (差し替え後):** stock の R2 t4・M t4 (対照) + β の R2 t4 + α の M t4。焦点再走は β の R2 t8・α の M t8 と同じ cell の stock。
4. **delete 経路の範囲 (一次資料の書き方):** stock の F t1 (delete を含む、並行なし) で巡回 0・存在履歴違反 0・integrity 0 を確かめた。並行下 (F t4) は stock Cicada が落ちるので、判定器まで届く履歴を得られていない。欠陥の修理は CCBench の変更で本 wave の所有外 (D2277 項 2 の「普通に使って直す」は、修理を別 item として次の一手に起票する形で扱う)。
5. 単位 B の所有に `GC-PROBE` の起動器変更を加える (起動器は repo 外で owned_paths 外)。計算の見積りは GC-PROBE ≈ 10 分を加えて合計 < 1.5 node 時間。

## R8. 所有 (素集合)

- T: `patches/instr-cicada-trace-tpcc.patch`、`.cicada-launcher/launch_cicada_run.py` (単位 worktree 内に書かせ、親が job dir へ退避)。
- B: `patches/broken-cicada-insert-past-ts.patch`、`.cicada-launcher/launch_cicada_run.py` (T 統合後の版から)。
- 親: `patches/README.md` 節、insight、fragment、job dir の script。
- 触らない: `patches/instr-cicada-trace.patch`、既存 `patches/broken-cicada-*.patch` 3 本、md_14 / md_15 / md_16 の所有物、`orchestrator/`、`external/ccbench` の gitlink。
