# [T-2854] 段 1 brief — TPC-C 段 1 の CCBench 側 (単位 1・2)

wave: dev-wave-t2854-tpcc-ccbench-v3 / branch worktree-dev-wave-t2854-tpcc-ccbench-v3 / 起点 local main eef04f5a7 (開始 gate rc=0、2026-09-22 19:50:04 JST) / CCBench pin e9e477ca1b55348ab4530de0b1cf663ce4555290

## 研究前進
VLDB 方針 (D2212 項 2、D2219 項 2 で段 1 → 段 2 の分割を確定) の TPC-C 段 1 (NewOrder / Payment の直列化可能性の認定) の producer 側。今は silo の TPC-C trace に表識別子も取引種別も無く、trace build の commit 計数が C 行数と食い違う (設計 §3.5、D295) ため、単位 4 (verifier) にも単位 5 (pipeline の allowlist) にも実入力が無い。完了判定 = e9e477ca の子の候補 commit (local branch) 上で、計算ノード 1 走により (a) tpcc_silo TRACE=1 (57:43) の trace が v3 frame の構造検査を通り、全 thread の C 行数 = stdout の commit_counts_、(b) ycsb_silo TRACE=1 の trace を現行 verifier (v2) が certified にし C 行数 = commit_counts_、(c) TRACE=0 で pin と候補の tpcc_silo / ycsb_silo が nm・strings の trace 記号 0 と正規化逆アセンブル一致、かつ変更 header の consumer TU の TRACE=0 正規化前処理出力が一致。

## scope
- 内: 設計 §7.1 単位 1 (include/trace.hh の v3 helper、include/tpcc.hh の取引種別 context と trace build 限定の計数修正) と単位 2 (cc/silo/transaction.cc の v3 emitter)。Codex author (D95) が書き、親が CCBench の local branch に commit・bundle 保全・主 checkout の submodule 保管庫へ fetch。計算ノードの確認 1 走と記録。
- 外: mocc (単位 3)・verifier / pipeline (単位 4・5)・pin 前進と gitlink / 承認定数 (単位 11)・push (D16、人間)・si・段 2 (S/Q)・gate / 検査 / 台帳の repo への追加。

## 確定済み裁定 (逐語は job dir verbatim/)
D16 (trace-hook は izanagi-trace 系統、push は人間)、D14 (`#if TRACE`)、D95 (実装面は Codex author)、D295 (witness は完全一致、許容幅なし)、D297 (pin 前進時の TRACE=0 同一性、header 差分は拒否)、D2207 (D297 検査器を緩めず計装側を include 行不変に直す)、D2212 項 2・4 (2 node 時間以上は確認)、D2219 項 2・7 (§9 所見は実装 wave で実行再現を試みる)、設計 §3.1 / §3.5 / §8。F546 (CCBench 編集は使い捨て clone、親が適用)。

## 不変条件
1. 規律 1: 追加する trace コードはすべて `#if TRACE` 内。TRACE=0 の前処理出力・include 活性・`__LINE__` 展開 (ERR が使う: tpcc.hh:88、silo transaction.cc:106 / :690) を pin と一致させる (先例 mocc 候補 68106660 の `#line` 復元)。
2. 規律 2: witness の許容幅を作らない。計数修正は TRACE=0 の挙動を変えない (`#if !TRACE` で quit 判定を残す)。
3. YCSB の v2 出力の形 (C 7 token + R/W/X/P/E) を変えない。si・mocc・他 protocol の source を変えない。gitlink は e9e477ca のまま。
4. v3 frame は並走の単位 4 と相互連絡で一致させた形: C 10 token (tx_type = TxType 1..5、0 は出さない)、R/W/X に table (Storage 0..10)、I 行・A 行は出さない、P / E は v2 と同形、段 1 は nS = nQ = 0。

## 割れうる前提 (親の provisional 裁定・攻撃対象)
- (P1) v2 / v3 の切替は、tpcc.hh が `tx.begin()` 直後に trace build 限定の thread-local へ取引種別を置き、silo の writePhase がそれを読んで 0 以外なら v3 を出し、出力後に 0 へ戻す。根拠: silo の transaction.cc は ycsb_silo / tpcc_silo で同じ define のまま compile されるので compile 時に workload を区別できず、workload 別 define を CMake に足すと perf build の flag も変わる。
- (P2) D297 検査器は header 差分を拒否するので、本 wave の規律 1 の証拠は D297 の pass ではなく、consumer TU (変更 header を include する全 .cc) の TRACE=0 正規化前処理比較と binary 比較で取る。D297 検査器自体は変えず (D2207)、実走して拒否される事実を記録し、単位 11 (pin 前進) の前提課題として残す。
- (P3) CCBench 側の commit は 2 本 (単位 1 = include/ の 2 file、単位 2 = cc/silo/transaction.cc)、local branch `izanagi-tpcc-v3-trace` (e9e477ca の子)。
- (P4) 内部の受入 = 上の完了判定 (a)〜(c) の計算ノード 1 走 + superproject の受入全走 (本 wave の superproject 差分は insight と spool fragment だけ)。superproject の実装面差分ゼロなので変異 matrix は DW-S04 で免除し、代わりに probe の構造検査に自己試験 (壊した trace を拒否する負例) を持たせる。
- (P5) D2219 項 7 の §9 再現: 段 1 の取引で観測しうるのは「OrderLine の番号が初期ロード (1 始まり) と実行時 (0 始まり) で食い違う」だけ。v3 trace の OrderLine 挿入 key を復号して実行時の番号の最小値を記録する (追加の計算なし)。他の所見は段 1 の取引では到達しない旨だけ記録する。
- (P7) 変更経路: include/trace.hh と include/tpcc.hh は hook の編集面 (EVOLVE_BLOCK_SOURCES) の外。D16・設計 §5.3 に従い izanagi-trace 系統への commit で入れ、superproject の作業ツリーの external/ccbench は 1 byte も書かない。Codex author は F546 の使い捨て clone を編集し、親は job dir の一時 CCBench worktree (e9e477ca) で `git apply --check` → 適用 → `commit -F` (先例 T-2844 の mk-C-commit.sh)。D41 が退けたのは合成用作業ツリーの編集面 hook を scratch copy で迂回して trace.hh を書く行為で、本経路は作業ツリーを変えない。hook・classifier が拒否したら迂回せず停止し裁定へ返す。D296 (v2 は silo 内で完結、helper を二重権威にしない) との関係: v3 の C 行は helper だけが出し、1 txn に C 行は 1 本 (v2 か v3 のどちらか) であることを実装と probe で確かめる。
- (P6) 既存 patch (patches/ 配下で cc/silo/transaction.cc・include/tpcc.hh・include/trace.hh に当たるもの) が候補にまだ当たるかを login で `git apply --check` して記録する (pin 前進時の波及の先行把握、何も直さない)。

## 成果物の形
CCBench: local branch の commit 2 本、bundle (job dir)、主 checkout の submodule 保管庫への非 force fetch。job dir: probe 一式と生 log。superproject (docs のみ): `output/insights/2026-09-22/t2854-tpcc-ccbench-v3/README.md` + verbatim、spool の worklog fragment (必要なら decisions fragment)。

## 分割
Codex author A = C++ (使い捨て clone `output/runs/t2854-ccbench-v3/ccbench` を編集面にする、F546)。Codex author B = 計算ノード probe (repo 内 scratch に書かせ親が job dir へ退避)。A と B は所有 path が素集合で並列。

## 受入・実測環境
計算ノード (Pegasus、`tools/pegasus/dispatch_compute.py --task generic`) で build と走行。login では cmake configure・前処理比較・D297 実走・patch の apply 検査・probe の自己試験だけ。受入は `tools/dev_wave_wait.py acceptance`。計算量見積り: 確認 1 走 ≈ 0.3〜0.5 node 時間 (build 3 木 + 短い走行、再投入 1 回込みで ≤ 1.0)、受入 ≈ 0.25 × 1〜2 回 → 合計 ≤ 1.5 node 時間で 2 node 時間の確認ライン未満。
