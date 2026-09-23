# [T-2854] TPC-C 段 1 の単位 3 — mocc の trace v3 emitter を、候補 C の上に C1 の helper を載せた CCBench の local branch に C3 として置き、計算ノード 1 走で構造・witness・内容、YCSB v2 の certified、TRACE=0 の前処理と逆アセンブルの一致、変異 6 件を確かめた

authority: none
default_effect: no-state-change

- 日付: 2026-09-23
- wave: `dev-wave-t2854-mocc-v3-emitter` (branch `worktree-dev-wave-t2854-mocc-v3-emitter`)。着手時 local main `cadaf3805e75bb0d02744955469ef588aabcd5c6` (開始 gate rc=0、08:36 JST)
- 依頼の逐語 = `verbatim/request.md`。入力 = 設計 `output/insights/2026-09-21/tpcc-trace-certification-design/README.md` §3.1・§3.5・§5.2・§7.1、単位 1・2 の insight `output/insights/2026-09-22/t2854-tpcc-ccbench-v3/README.md` (D2225)、T-2844 の insight `output/insights/2026-09-21/t2844-mocc-xp-hook-branch/README.md` (候補 C)
- 既裁定: D14、D16、D2207、D2224、D2225、D297、F546。裁定 inbox 第 32 回 (2026-09-23 08:29 JST) の項 1 (T-2858: pin を C 単独で承認、TPC-C の commit は完成時に別途承認) と項 7 (`izanagi-tpcc-v3-trace` は今は push しない)。本 wave の設計判断は decisions の fragment (`{{D:tpcc-v3-producer-mocc}}` として land 時に採番)
- job dir (親の script・生 log・codex receipt・bundle・probe・生 trace の圧縮): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-mocc-v3-emitter/`

## 0. 結論

1. **候補 commit:** CCBench の新しい local branch `izanagi-tpcc-v3-mocc` に、候補 C `68106660` → C1' `6aa7a58fccff9efa218067d1b7ce83026a75357d` (C1 `56b5cb70` を `cherry-pick -x` で載せたもの、header 2 file) → C3 `53f6b09757331ac7200f3f6bb5d526a676480fe3` (`cc/mocc/transaction.cc` だけ) の 2 commit を置いた。`izanagi-mocc-xp-instrumentation` (= C) は動かしていない。push・gitlink・承認定数・pin はそのまま。
2. **計算ノードの確認 1 走 (request 19053.nqsv、Elapse 206 秒) は C0〜C6 の全段合格。** TPC-C (NewOrder / Payment、2 thread、1 秒) の mocc の trace は v3 の構造検査・witness (C 行 35,572 = stdout の `commit_counts_` 35,572)・内容照合に合格、YCSB の mocc の trace は v2 のまま現行 verifier が serializable / certified (286,026 取引)。TRACE=0 は変更 header を読む 12 source / 21 compile entry の完全展開と include 活性が C と一致し、tpcc_mocc / ycsb_mocc の正規化逆アセンブルも一致。TRACE=1 は同じ 21 entry が `-Werror` 付きの構文検査に合格。
3. **変異 (事前登録の 6 件) は全件期待どおり:** 診断変種 D1 は PASS、M2 (旧計数順序) は C 1,881 > commit 数 1,879 の witness だけで KILLED、M1m (mocc が context を読まない)・M3m (表 6 → 5)・M4m (種別 1 ↔ 2)・M5m (`#line 1187` 削除) も登録した理由で KILLED (§4)。
4. **TPC-C の trace は certified ではない。** 結果名は `structure+witness+content pass`。現行 verifier は v3 の run に存在履歴未検査の印を立てて認定しない (D2224)。
5. **D297 の合格は名乗らない** (D2225 決定 6 と同じ理由: header の差分を含む)。
6. 計算投入は 1 本、Elapse 206 秒 (約 0.06 node 時間、待ち行列 18 分は含まない)。

## 1. 依頼の完了条件と状態

| 完了条件 (段 4 裁定 `verbatim/s4-ruling.md` §3、C0 の記述は段 6 裁定 `verbatim/s6-ruling.md` で訂正) | 状態 |
|---|---|
| 候補 C の上に新しい local branch を切り C1 の helper を載せる | **済** — C1' (§2)。header 2 file の blob は C1 と同一 (`verbatim/mk-c1p.log`) |
| mocc の v3 emitter を Codex author で書き commit | **済** — C3 (§2) |
| C0 source と toolchain の束縛 | **済** — C と C3 を bundle から取り出し 404 / 404 file の集合と blob が tree と一致 (除外は gitlink `third_party/shirakami` だけ)。C1' は祖先 (親 = C、C3 の親 = C1') と raw diff (C..C1' = header 2 file、C1'..C3 = mocc 1 file) で照合。compiler は policy の digest と一致した `x86_64-linux-gnu-g++-11` |
| C1 TRACE=0 前処理 (21 entry) | **済** — 21 / 21 が完全展開・include 活性とも C と一致。負例 (`#include "trace.hh"` を `#if TRACE` の外へ出した版) は TPC-C consumer 9 / 9 で include 活性が不一致 (完全展開も 9 件とも不一致) |
| C2 TRACE=1 構文検査 (21 entry、実 flag) | **済** — 21 / 21 rc=0 |
| C3 TRACE=0 binary | **済** — §3 |
| C4 TPC-C の v3 構造・witness・内容 | **済** — §3 |
| C5 YCSB の v2 と現行 verifier の certified | **済** — §3 |
| C6 D1 と変異 M1m〜M5m | **済** — §4 |
| C7 構造検査器の自己試験 (親が login で実走) | **済** — 197 / 197 (`evidence/parent-selftest-summary.txt`) |
| C8 superproject の受入全走 | 本 insight の記録 commit の後に走る。結果は land の受領証と worklog の後続記録が持つ |
| push・gitlink / 承認定数・pin 前進 (単位 11) | 行っていない (依頼どおり scope 外) |

## 2. 候補 commit (CCBench の local branch `izanagi-tpcc-v3-mocc`)

| 項目 | C1' | C3 |
|---|---|---|
| OID | `6aa7a58fccff9efa218067d1b7ce83026a75357d` | `53f6b09757331ac7200f3f6bb5d526a676480fe3` |
| 親 | `68106660686232781bca3be792a750d3e19d7a8a` (候補 C) | C1' |
| tree | `d5be6f74b6142a9b03501a40a921654e8723458e` | `a0ffd57c2971a762fd6c9ae9c5afb9b499a4b79e` |
| 変更 | `include/trace.hh` +49、`include/tpcc.hh` +12 (C1 と同じ) | `cc/mocc/transaction.cc` +61 / −10 |
| 変更後の blob | trace.hh `1ff95bcec49e49d02669321b09414ab114c20df2`、tpcc.hh `24e7d13288cf7df1e86a87aac0bd44ab9112eb9c` | transaction.cc `30bea5c21911182cde7c1f428f3185c7124fb47f` |

- **作り方:** C1' は親が wave 木の submodule に job dir 配下の一時 worktree を C で切り、branch を作って C1 を `cherry-pick -x` した (message は C1 のまま、出所行つき)。C3 は Codex author A が使い捨て clone (C1' を checkout、gitignore 下、F546) の mocc 1 file を編集し、親が最終 file を一時 worktree に置いて blob と差分 path 数を照合してから `commit -F` した (`verbatim/mk-c3.log`)。superproject の `external/ccbench` の HEAD と作業ツリーは pin `e9e477ca` のまま (porcelain 0)。
- C3 の commit message の逐語 = `verbatim/msg-C3.txt`。trailer は Codex `role=author` (author A)、Codex `role=reviewer` (段 6 レビュー 2 本、gpt-6-astra / medium)、Claude `role=manager`。
- 自己完結 bundle = job dir `C.bundle` (3,199,059 byte、sha256 `306a68a6777847d03e8f597f4d8acd613bde2c04d4f43d0aaac8ddf38c0adbb7`、complete history、`git bundle verify` 済み)。
- 差分の逐語は本 insight に写さない (`.patch` は実装面と判定されるため)。`git show 53f6b097` か bundle から読む。author A の報告 (`verbatim/s5-author-A.md`) には差分の全文がある。
- **実装の要点:** writePhase の既存 `#if TRACE` 内で取引種別の context を 1 回読み、非 0 なら C / R / W と X 4 箇所 (not-locked-at-entry、UPDATE と DELETE の lock-lost-before-write、lock-lost-before-publish) を v3 helper で出し、0 なら既存の v2 の式と既存の `izanagi_trace::emit_lock_violation(` 呼出しを使う。表は `get_storage(<elem>.storage_)`、E の直後に context を 0 へ戻す。P 行・validation・lock・G2 watermark (環境変数で有効化) は不変。既存の `#line` 7 本は値を保ち、E の後に `#line 1206` を 1 本足した。親の独立検算で、TRACE=0 で有効な行の (論理行番号, 本文) は C1' と完全一致 (`evidence/parent-trace0-lines-mocc.txt`)。v2 の X 呼出しは 4 本のまま、v3 の X が 4 本、P の stream は 1 本のまま。

## 3. TPC-C と YCSB の走行、TRACE=0 binary (C3〜C5)

実行: `python3 tools/pegasus/dispatch_compute.py --task generic --walltime 01:00:00 -- /usr/bin/python3 <job dir>/probe/run_probe.py …` を wave worktree (clean、HEAD `cadaf3805`) から。request 19053.nqsv、gen_S 1 node、09:24:23〜09:27:44 JST、Elapse 206 秒、child rc=0 (`evidence/compute-1-dispatch.log`)。段ごとの要約 = `evidence/compute-1-summary.txt`。

| 走 | 条件 | 結果 |
|---|---|---|
| TPC-C B0 (C3、TRACE=1、`tpcc_mocc`) | 前 wave と同じ flag (`-thread_num=2 -extime=1 -tpcc_num_wh=1 -tpcc_perc_payment=43 -tpcc_perc_order_status=0 -tpcc_perc_delivery=0 -tpcc_perc_stock_level=0 -clocks_per_us=2100`) | `structure+witness+content pass`。C 35,572 = E 35,572 = `commit_counts_` 35,572、`batch_commit_counts_` 0、rc 0。R 489,500・W 525,263・X 0・P 0。取引種別は 1 (NewOrder) 19,263・2 (Payment) 16,309 |
| YCSB B0 (C3、TRACE=1、`ycsb_mocc`) | `-thread_num=2 -extime=1 -ycsb_tuple_num=200 -ycsb_rratio=50 -ycsb_rmw=true -ycsb_max_ope=5 -ycsb_zipf_skew=0 -clocks_per_us=2100` | C 行はすべて v2 の 7 token。C 286,026 = `commit_counts_`。現行 verifier (`orchestrator/verify.py … --protocol mocc --ccbench-root <C3 の source> --json`) は rc 0、certified_serializable 1、verdict serializable (reads 1,415,914、writes 711,034、keys 200、edges 2,088,838、integrity clean) |
| TRACE=0 binary (C と C3) | 等長の source / build path、比較用の追加 flag なし | `tpcc_mocc.exe` (748,992 byte) と `ycsb_mocc.exe` (698,672 byte) の両方で nm の `izanagi` 0 件、strings の `izanagi_trace` / `IZANAGI_` 0 件、正規化逆アセンブルの digest 一致 (`evidence/compute-1/binary-digests.json`)。binary 本体の sha256 は C と C3 で異なる。`.text` の bytes 一致は測っておらず主張しない |

- 内容照合の定義は前 wave と同じ (W の署名と宣言種別の一致 `content-txtype`、NewOrder の表 5・6・7・8 への INSERT と表 5 / 表 6 の key の 1 対 1、Payment の表 4 への INSERT 1 本と表 0・1・2 への UPDATE `content-table`)。
- 実行時の OrderLine の番号は 19,263 注文すべてで最小値 0 (前 wave の silo と同じ観測)。
- **trace 量 (実測):** TPC-C 36,267,017 byte / 35,572 取引 = 約 1,020 byte / 取引 (前 wave の silo は約 1,024)。
- **生 trace の保持:** B0 の TPC-C / YCSB を zstd で job dir `evidence/traces-1/` に保持 (sha256 = `evidence/kept-traces-sha256.txt`)。repo には入れない。
- TPC-C の stdout には `insert order failed` が 311 行出た (commit 35,572、abort 2,844)。同じ条件の silo (前 wave) でも 434 行出ており、mocc 固有ではない。本 wave はこの表示の原因を調べていない。
- throughput は trace build の値なので性能の主張に使わない。
- 比較は選んだ構成 (Release・stock の protocol option・GCC 11.4) に限る。

## 4. 変異 (C6、事前登録 = 段 4 裁定 §4)

harness は前 wave の probe の独自 harness (出現 1 回の assert・逐次・pristine 復元の sha256 照合・1 件ずつ flush、build 失敗は ERROR) を mocc 向けに改めたもの (Codex author B)。spec = `verbatim/mutation-spec.json` (anchor は C3 の blob で出現 1 回を親が照合、`verbatim/check_anchors.log`)。結果 = `evidence/compute-1/mutation-results.json`。

| ID | 変異 | 条件 | 結果 |
|---|---|---|---|
| D1 | tpcc.hh の commit 成功直後に、成功 commit が 1,000 回目の thread が marker を出し quit を立てる | PASS = 全検査合格・marker ≥ 1・C 1,000 行以上の file ≥ 1 | **PASS** (marker 1、C = commit 数 = 1,886) |
| M1m | mocc の context の読みを `0U` に | 先頭理由 `schema` | **KILLED** (理由 = schema・frame・witness・content-txtype・content-table、先頭 schema) |
| M2 | D1 の上で `#if !TRACE` を `#if 1` に | 理由集合 = witness だけ・rc 0・E = C・C > commit 数・marker・1,000 行以上の file | **KILLED** (C 1,881 > commit 数 1,879、E 1,881、marker 1) |
| M3m | mocc の v3 W で表 6 を表 5 に写す | 理由集合 = content-table だけ | **KILLED** |
| M4m | mocc の v3 C で種別 1 と 2 を入れ替える | 理由集合 = content-txtype だけ | **KILLED** |
| M5m | mocc の `#line 1187` を消す (build しない) | mocc の 4 entry の完全展開が不一致・21 entry の include 活性が一致・他 17 entry は両方一致 | **KILLED** (完全展開の一致 17 / 21、include 活性の一致 21 / 21) |

- M1m は前 wave の M1 と同じく先頭理由の一致として数える。M1m は mocc 側の切替 (context を読むこと) を外す変異で、前 wave の M1 (tpcc.hh の setter を消す) とは外す層が違う。
- D1 / M2 は、mocc の上でも計数修正が commit 直後の quit 境界で C 行数と commit 数を一致させ、旧順序ではずれることを示す。
- 変異は計算 job 内の独自 harness で、repo の `tools/mutation_harness.py` ではない。superproject の実装面差分はゼロ。

## 5. 経過

- **段 1・4:** brief (`verbatim/s1-brief.md`、provisional (P1)〜(P8)) → 裁定 (`verbatim/s4-ruling.md`)。段 2・3 は軽量版で省いた (silo の C2 と同じ形の移植で設計択一が割れない。敵対検証は段 6 のレビュー 2 本が担う)。裁定 inbox 第 32 回と食い違わないことを段 4 の直前に確かめた。
- **段 5:** author A (C++、270 秒) と author B (probe、461 秒) を並列。どちらも裁定からの逸脱なし。親は A の最終 file の TRACE=0 論理行を独立に照合 (MATCH) し、probe の自己試験を login で実走 (197 / 197) してから C3 を commit した。
- **段 6:** 敵対レビュー 2 本 (A = 正しさ境界と規律 1、B = 過剰・削除) はどちらも GO、must-fix 0。B の should 2 件は裁定文の訂正 (C0 の checkout 本数) と見積りの注記で、実装面の fix は無い (`verbatim/s6-ruling.md`)。fix 子・焦点再レビューは起動していない。
- Codex 子は計 4 本 (author 2・review 2)、model call 計 53、wall 合計 1,154 秒。全子 gpt-6-astra / medium。

## 6. 単位 11 (pin 前進) へ渡す材料 — 本 wave では決めていない

- 本 branch は silo の v3 emitter (C2) を含まない。単位 11 で C の上に C1・C2・C3 を 1 系列に並べるとき、C1' と C3 はそのまま使え、C2 (`cc/silo/transaction.cc` だけ) は path が重ならないので載せ替えで衝突しない見込み (内容の結合確認は単位 11 の仕事)。
- D297 の検査器は header の差分を拒否する。受理方法は単位 11 の論点のまま (裁定 inbox 第 32 回の索引外記録: 方式案は AI 手番、既裁定の変更を要する案は再裁定へ)。
- **存在履歴 (設計 §3.3) の前提の mocc 側 (静的確認のみ):** 並走の [T-2854] 残り (1) の wave (存在履歴の verifier 実装) の連絡により、同 wave の検査の契約「(表, key) は最初の committed write が I でなければ genesis (1,0) から存在」が mocc でも成り立つかを C3 の source で読んだ。TPC-C の初期ロード (`include/tpcc/tpcc_initializer.hh:36`) は `tuple->init(thid, …)` を呼び、mocc の `Tuple::init(size_t, TupleBody&&, void*)` は版を epoch 1・tid 0・absent=false に置く (`cc/mocc/include/tuple.hh:74-83`)。実行時の insert は `init(TupleBody&&)` (absent=true) を使い、`TxExecutor::insert` は write set か木に同じ key があれば `WARN_ALREADY_EXISTS` で失敗する (`cc/mocc/transaction.cc` の `insert`)。silo と同じ 2 点が静的には成り立つ。実 trace での確認 (存在履歴を実装した verifier に本 wave の B0 を通すこと) はしていない。
- T-2858 (pin を C へ進める更新 wave) が land すれば、C3 系列の比較基点 C はその時点の pin と一致する。

## 7. 主張しないこと

- TPC-C の直列化可能性の認定 (現行 verifier は v3 の run を認定しない)。
- D297 の合格、`.text` の bytes 一致、全 compiler・全 macro 構成での TRACE=0 同一性。
- v3 の X 行の実出力 (正常走では X = 0 で、v3 の X 経路は走っていない。形の正しさは静的レビューと構文検査まで)。
- mocc の高温・RLL 経路の不存在判定の扱い (段 2、設計 §5.2)。
- throughput (trace build の値)。

## 8. 再現資料

- job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-mocc-v3-emitter/`: `C.bundle`・`C1p.oid`・`C3.oid`、`probe/` (run_probe.py・v3check.py・selftest.py・mutation-spec.template.json、Codex author B が前 wave の probe を改めたもの)、`spec/mutation-spec.json`、`run-compute.sh`、`evidence/compute-1/` (compute.json 本体と 1.6 GB の log、sha256 = `evidence/compute-json-sha256.txt`)、`evidence/traces-1/`、`mk-c1p.sh`・`mk-c3.sh`・`verify_trace0_lines.py`・`check_anchors.py`・`summarize.py` (親の script)。sha256 = `evidence/probe-and-parent-scripts-sha256.txt`。
- repo には probe の `.py` と差分の `.patch` を入れていない (実装面の判定のため)。
