# [T-2854] 単位 11 — C1'・C2・C3 を pin C の上へ 1 系列に並べた別名の CCBench local branch を作り、計算ノード 1 走で silo・mocc の結合確認 (v3 の構造・witness・内容、YCSB v2 の certified、TRACE=0 の前処理と逆アセンブルの一致、変異 4 件) を全段合格させた。D297 の検査器は header 差分でこの候補を拒否するので、受理方式の 4 択を作りユーザーへ諮る

authority: none
default_effect: no-state-change

- 日付: 2026-09-26
- wave: `dev-wave-t2854-unit11-combined` (branch `worktree-dev-wave-t2854-unit11-combined`)。着手時 local main `74e6d2f237d3cf6501731fc9fa06a7ce22d4e07e` (開始 gate rc=0、14:03:30 JST、job dir `startup-gate.log`)
- 依頼の逐語 = `verbatim/request.md`。入力 = worklog archive entry 1852 の [T-2854] carry、設計 `output/insights/2026-09-21/tpcc-trace-certification-design/README.md` §5.3・§7.1・§8、単位 1・2 の insight `output/insights/2026-09-22/t2854-tpcc-ccbench-v3/README.md` §8、単位 3 の insight `output/insights/2026-09-23/t2854-mocc-v3-emitter/README.md` §6
- 既裁定: D14、D16、D297、D780、D2207、D2212 項 4、D2225、D2227 項 1、D2230、D2235 項 1。D2237 (第 34 回) 以後、T-2854 の新しい裁定は無い (裁定 inbox を 14:0x と 14:2x JST に確認)
- job dir (親の script・生 log・codex receipt・bundle・probe・計算の証拠・生 trace の圧縮): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/`

## 0. 結論

1. **候補 branch:** CCBench の新しい local branch `izanagi-tpcc-v3-silo-mocc` = C `68106660` (現 pin) → C1' `6aa7a58fccff9efa218067d1b7ce83026a75357d` → C3 `53f6b09757331ac7200f3f6bb5d526a676480fe3` → **C2' `40a7f4acb174ca43cb590f40d13847216a1564bc`** (C2 `a6f2c741` を `cherry-pick -x` で載せたもの)。C1' と C3 は OID のまま使い、新しい commit は C2' の 1 つだけ。既存の `izanagi-tpcc-v3-trace` (公開済み)・`izanagi-tpcc-v3-mocc`・`izanagi-mocc-xp-instrumentation` は動かしていない。push・gitlink・承認定数・pin はそのまま。
2. **計算ノードの結合確認 1 走 (request 29455.nqsv、bnode084、Elapse 243 秒) は C0〜C6 の全段合格** (`all_pass` true)。TPC-C は silo・mocc とも `structure+witness+content pass`、YCSB は silo・mocc とも v2 のまま現行 verifier で serializable / certified、TRACE=0 は 21 entry の完全展開・include 活性と 4 binary の正規化逆アセンブルが C と一致、TRACE=1 は 21 entry の構文検査に合格。
3. **変異 4 件はすべて登録どおり KILLED:** H-set (共有 header の取引種別 setter を消す) は silo・mocc の両方が先頭理由 schema、H-line (`tpcc.hh` の `#line 56` を消す) は TPC-C の 9 entry だけ完全展開が不一致、S-table (silo の表 6 → 5) は content-table だけ、M-type (mocc の種別 1 ↔ 2) は content-txtype だけ (§4)。
4. **D297 の合格は名乗らない。TPC-C の certified も名乗らない。** 現行の D297 検査器は C → C2' を `include/tpcc.hh` の header 差分で拒否する (rc=1、§5.1)。本 wave は C2' を pin に入れず、検査器も変えていない。
5. **受理方式は 4 択にしてユーザーへ諮る (§5)。** 推奨は「D297 の header 受理規則の設計審査」(択 1)。どの択も、C2' を pin に入れるには既裁定の変更 (D297 の受理規則の改訂か、C2' 限定の例外の新裁定) か、別候補での作り直しを要する。push と pin 前進の承認は人間の手番のまま。
6. 計算投入は 1 本 (Elapse 243 秒、約 0.07 node 時間)。受入 1 回 (約 0.25 node 時間) を加えても D2212 項 4 の線 (2 node 時間) の下。

## 1. 依頼の完了条件と状態

| 完了条件 (段 4 裁定 `verbatim/s4-ruling.md` §2・§3、H-line の consumer 選択は段 6 裁定 `verbatim/s6-ruling.md` §3 で明確化) | 状態 |
|---|---|
| C1'・C2・C3 を C の上へ 1 系列に並べた別名の local branch | **済** — §2 |
| 公開 branch `izanagi-tpcc-v3-trace` を残し、同名への force push をしない | **済** — 触れていない (GitHub の ls-remote で同名の新 branch が無いことも確認) |
| C0 source と commit 構成の束縛 | **済** — bundle から C と C2' を取り出し、C → C1' → C3 → C2' の親と各区間の raw diff、取り出した file 集合と blob を tree と照合 |
| C1 TRACE=0 前処理 (21 entry) | **済** — 21 / 21 が完全展開・include 活性とも C と一致。負例 (`#include "trace.hh"` を `#if TRACE` の外へ) は TPC-C 9 / 9 で include 活性が不一致 (完全展開も 9 件とも不一致) |
| C2 TRACE=1 構文検査 (21 entry、実 flag) | **済** — 21 / 21 rc=0 |
| C3 TRACE=0 binary (4 本) | **済** — §3 |
| C4 TPC-C の v3 構造・witness・内容 (silo・mocc) | **済** — §3 |
| C5 YCSB の v2 と現行 verifier の certified (silo・mocc) | **済** — §3 |
| C6 変異 (事前登録 4 件) | **済** — §4 |
| C7 構造検査器の自己試験 (親が login で実走) | **済** — 最終 185 / 185 (job dir `evidence/parent-selftest-2.txt`) |
| D297 の header 差分の受理方式案と諮問 | **済 (諮問)** — §5。既裁定の変更を要するので本 wave では決めない |
| C8 superproject の受入全走 | 本 insight の記録 commit の後に走る。結果は land の受領証と worklog の後続記録が持つ (本 insight には書けない) |
| push・pin 前進 (gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN`) | 行っていない (人間の手番、依頼どおり) |

## 2. 候補 branch (CCBench の local branch `izanagi-tpcc-v3-silo-mocc`)

| commit | OID | 親 | 変更 (前の commit から) |
|---|---|---|---|
| C (現 pin) | `68106660686232781bca3be792a750d3e19d7a8a` | e9e477ca | `cc/mocc/transaction.cc` (mocc の X/P 計装、T-2844) |
| C1' | `6aa7a58fccff9efa218067d1b7ce83026a75357d` | C | `include/trace.hh`・`include/tpcc.hh` (単位 3 で C1 を載せ替え済み) |
| C3 | `53f6b09757331ac7200f3f6bb5d526a676480fe3` | C1' | `cc/mocc/transaction.cc` (mocc の v3 emitter) |
| **C2'** | `40a7f4acb174ca43cb590f40d13847216a1564bc` (tree `92c9c3d620711250a4c1e448b893f190704b0ac6`) | C3 | `cc/silo/transaction.cc` (silo の v3 emitter、C2 の `cherry-pick -x`) |

- C..C2' は 4 file の M だけ (mode 100644 不変)。各 blob は由来の commit と一致: trace.hh `1ff95bce`・tpcc.hh `24e7d132` (C1')、mocc `30bea5c2` (C3)、silo `4434447d` (C2)。C3 の silo の blob は C1 の silo と同じ `054a7e5f` で、C2 はそのまま当たる (`verbatim/mk-c2p.log`)。
- **作り方:** 親が wave 木の submodule に job dir 配下の一時 worktree を C3 で切り、branch を作って C2 を `cherry-pick -x` (message は C2 のまま、出所行つき。trailer は C2 の Codex `role=author` / `role=reviewer` と Claude `role=manager`)。superproject の `external/ccbench` の HEAD と作業ツリーは C のまま (porcelain 0)。
- 自己完結 bundle = job dir `C.bundle` (3,200,920 byte、sha256 `99882fa76fbbdda0479c79254eca8d22db436c6beee4f4addffec25cfec78479`、complete history、`git bundle verify` 済み)。land 後に主 checkout の submodule の git dir へ非 force で取り込む (前例 T-2844・単位 1〜3)。
- `verbatim/mk-c2p.log` は git の進捗表示 (CR 区切りの 1 行、CR 73 個) を最終表示だけへ畳んだ可逆最小正規化版。原文は job dir `mk-c2p.log` (6,511 byte、sha256 `85dc940b37bdf4faf708104a6e9bd070551e7f7ca8249eb3a0628c1df520a4e3`)。

## 3. 結合確認 (計算 1 走)

実行: `python3 tools/pegasus/dispatch_compute.py --task generic --walltime 01:00:00 -- /usr/bin/python3 <job dir>/probe/run_probe.py …` を wave 木 (clean、HEAD `74e6d2f23`) から (job dir `run-compute.sh`、4 OID を裁定済みの値と照合してから投入)。request 29455.nqsv、gen_S 1 node (bnode084)、14:45:37〜14:49:36 JST、Elapse 243 秒、child rc=0。段ごとの値 = `verbatim/compute-1-summary.txt`、本体 = job dir `evidence/compute-1/compute.json` (sha256 `e18c8503c2c00fcf8c00202c9ac02a887fb009b176251603b44c898d708871a0`)。

**結合確認の命題:** C2' の単一 source tree から作る各 protocol の binary (`tpcc_silo`・`ycsb_silo`・`tpcc_mocc`・`ycsb_mocc`) が、共有 header (trace.hh・tpcc.hh) と各 emitter を正しく使うこと。silo と mocc が 1 つの binary に入る構成は無い (CMake の target は protocol ごと)。

| 走 | 条件 | 結果 |
|---|---|---|
| TPC-C B0 silo (C2'、TRACE=1) | 前例と同じ flag (`-thread_num=2 -extime=1 -tpcc_num_wh=1 -tpcc_perc_payment=43 -tpcc_perc_order_status=0 -tpcc_perc_delivery=0 -tpcc_perc_stock_level=0 -clocks_per_us=2100`) | `structure+witness+content pass`。C 36,106 = E 36,106 = `commit_counts_` 36,106、`batch_commit_counts_` 0、rc 0。R 493,700・W 529,986・X 0・P 0。種別 1 (NewOrder) 19,497・2 (Payment) 16,609 |
| TPC-C B0 mocc (C2'、TRACE=1) | 同じ flag | `structure+witness+content pass`。C 34,859 = E 34,859 = `commit_counts_` 34,859、batch 0、rc 0。R 484,347・W 519,376・X 0・P 0。種別 1 19,082・2 15,777 |
| YCSB B0 silo (C2'、TRACE=1) | 前例と同じ flag (`-thread_num=2 -extime=1 -ycsb_tuple_num=200 -ycsb_rratio=50 -ycsb_rmw=true -ycsb_max_ope=5 -ycsb_zipf_skew=0 -clocks_per_us=2100`) | C 行はすべて v2 の 7 token。C 296,366 = `commit_counts_`。現行 verifier (`orchestrator/verify.py … --protocol silo --ccbench-root <C2' の source> --json`) は certified_serializable 1、verdict serializable (reads 1,466,964、writes 737,854、keys 200、edges 2,163,004、integrity clean) |
| YCSB B0 mocc (C2'、TRACE=1) | 同じ flag | C 行はすべて v2。C 289,143 = `commit_counts_`。`--protocol mocc` で certified_serializable 1、verdict serializable (reads 1,431,497、writes 719,446、keys 200、edges 2,111,471、integrity clean) |
| TRACE=0 binary (C と C2') | 等長の source / build path、比較用の追加 flag なし | 4 本とも nm の `izanagi` 0 件、strings の `izanagi_trace` / `IZANAGI_` 0 件、正規化逆アセンブルの digest 一致。byte 数は C と C2' で同じ (tpcc_silo 756,016・ycsb_silo 701,720・tpcc_mocc 748,992・ycsb_mocc 698,672)。binary 本体の sha256 は異なる。`.text` の bytes 一致は測っておらず主張しない |

- 21 entry = 変更 header を読む 12 source (9 protocol の `tpcc_<p>.cc` と silo・si・mocc の `transaction.cc`) × target。C と C2' の両木で、CMake の宣言から作った期待集合と compile database が一致した。
- 内容照合の定義は前例と同じ (W の署名と宣言種別の一致 `content-txtype`、表構成 `content-table`)。
- **trace 量 (実測):** TPC-C silo 36,619,792 byte / 36,106 取引、mocc 35,856,381 byte / 34,859 取引 (約 1,014 byte / 取引と約 1,029 byte / 取引。前例の単独確認は silo 約 1,024・mocc 約 1,020)。
- **生 trace の保持:** B0 の 4 走を zstd で job dir `evidence/traces-1/` に保持 (8 file 計 39,437,099 byte ≈ 38 MiB、sha256 = job dir `evidence/kept-traces-sha256.txt`)。repo には入れない。
- throughput は trace build の値なので性能の主張に使わない。比較は選んだ構成 (Release・stock の protocol option・GCC 11.4) に限る。

## 4. 変異 (C6、事前登録 = 段 4 裁定 §3)

harness は単位 3 の probe の独自 harness (出現 1 回の assert・逐次・pristine 復元の sha256 照合・1 件ずつ flush、build / 走行の失敗は ERROR で kill に数えない) を 2 protocol 向けに改めたもの (Codex author B、段 6 fix 1 巡)。spec = job dir `spec/mutation-spec.json` (anchor は C2' の実 bytes で出現 1 回を親が照合、`verbatim/check_anchors.log`)。結果 = job dir `evidence/compute-1/mutation-results.json` (sha256 `a4a11621dd6e23de5f524c1e924dd9658d64dfd57aabfab50b9ebf226780c890`)。

| ID | 変異 (C2' の上) | 期待 (KILLED の条件) | 結果 |
|---|---|---|---|
| H-set | `include/tpcc.hh` の `izanagi_trace::set_tpcc_tx_type(get_tx_type(query.type));` を消す。`tpcc_silo` と `tpcc_mocc` を再 build し各 B0 | silo・mocc の**両方**が先頭理由 schema (構造破損に伴う派生理由の併発は許す) | **KILLED** (両方とも理由 = schema・frame・witness・content-txtype・content-table、先頭 schema) |
| H-line | `include/tpcc.hh` の `#line 56` を消す (build しない) | `tpcc_<p>.cc` の 9 entry の完全展開が全件不一致、他 12 entry は両 mode とも一致、include 活性は 21 / 21 一致 | **KILLED** |
| S-table | silo の v3 W で表 6 を表 5 に写す。`tpcc_silo` だけ再 build | 理由集合 = content-table だけ | **KILLED** |
| M-type | mocc の v3 C で種別 1 と 2 を入れ替える。`tpcc_mocc` だけ再 build | 理由集合 = content-txtype だけ | **KILLED** |

- H-set は結合に固有の変異 (共有 header の 1 箇所が 2 protocol の v3 切替を同時に担う)。H-line は規律 1 の証拠層 (C1) が結合 tree の共有 header の論理行ずれを検出すること。S-table・M-type は protocol 側の代表例で、影響しない側の再 build・再走行はしない (段 3 相談 B: 別 target なので結合の証拠にならない)。
- 単位 1〜3 で済んだ変異 (計数順序の D1 / M2、各 protocol の `#line`) は再演しなかった (段 3 相談 B、段 4 裁定)。
- superproject の実装面差分はゼロなので pytest の変異 matrix は免除 (DW-S04)。

## 5. D297 の検査器が拒否する header 差分の受理方式案 — ユーザーへの諮問

### 5.1 事実

- 現行の D297 検査器 (`tools/check_trace0_preprocess_identity.py`) を C → C2' に走らせると rc=1 で、理由は「header の変更は consumer TU での解析が必要であり、この checker の保証範囲外なので fail-closed で拒否する: 'include/tpcc.hh'」(`tools/check_trace0_preprocess_identity.py:194-199`、`verbatim/d297-C-to-C2p.stderr.txt`)。前処理の比較に入る前の差分検査で止まる。これは C2' が**検査器の受理集合の外**にあることを示すだけで、TRACE=0 の同一性が偽であることは示さない。
- 検査器は変更された file を**その file 単体で**前処理して比べる (include を marker に置き換え、`-nostdinc`)。比べる文脈は 16 = silo の有効 genome 8 × 文脈 macro `GLOBAL_VALUE_DEFINE` の有無 2 (`orchestrator/campaign/genome.py:106-116`、`orchestrator/campaign/source_digest.py:344-351`)。これは実際の TPC-C build の 16 構成ではない。`tpcc_silo.cc`・`tpcc_mocc.cc` は冒頭で自ら `GLOBAL_VALUE_DEFINE` を定義する。
- D297 が header を拒否する理由のうち「`-E -P` は `#define` を残さない」は、現行の `_cpp_normalize` が `-dD` を使うので部分的に解消している。残る本質は「header 単体の前処理は、consumer TU の中で先行する定義・include 順の下でどう展開されるかを代表しない」ことである (段 3 相談 A の所見 2)。
- C2' の header 差分の中身: `include/trace.hh` の追加はすべて既存の `#if TRACE` 領域の内側 (v3 helper と取引種別の thread-local)。`include/tpcc.hh` は `#if TRACE` の include と setter、`#if !TRACE` で囲んだ commit 後の quit 判定、行番号を戻す `#line` 4 本。
- 段 1 の v3 と witness は header を変える形で決まっている (D2225 決定 2・3: 取引種別は `tpcc.hh` が `tx.begin()` 直後に置き、計数修正も `tpcc.hh` の quit 判定)。

### 5.2 択 (いずれも「pin C を維持したまま、次に何を検討するか」の問い)

依頼どおり、検査器の拡張と代替証拠での受理は AI の判断で採らない。

| 択 | 中身 | 変更を要する既裁定 | 不足する保証 / 失うもの | 費用 |
|---|---|---|---|---|
| 1 (推奨) | **D297 の header 受理規則の設計審査。** 変更 header を読む consumer TU を列挙し、TU ごとに実際の protocol と compile define を対応づけ、TRACE=0 の完全展開 (`-dD`) と include 活性を複数 compiler で比べる規則を検査器に足す設計を、まず審査する。審査の承認と実装の委任は別の裁定にする | D297 (header 一律拒否 → 条件つき受理)。D2207 は mocc の `<set>` include を許さない判断として射程を説明し変えない。D2225 決定 6 (C2' は現行検査器の D297 合格を名乗らない) は過去の名乗りとして維持。D780 項 2 (実 compile command・全 TU を結ぶ別防壁は単独設計しない) は維持し、この比較を trace 完全除去の防壁と呼ばない | consumer TU の母集合 (直接 include から引くか、全 `.cc` の前処理から引くか) の閉包証明がまだ無い。急ぐと新しい偽緑を作る | 設計審査 1 wave + 実装・変異 1 wave 以上 (未設計なので上限ではない) |
| 2 | **C2' に限る代替証拠での受理。** 本 wave の証拠 (§3・§4) に、必要なら pin 前進 wave で 16 文脈 × GCC 2 版へ広げた consumer TU 比較を足して受理し、D297 の合格とは呼ばない | D297 に C2' 限定の例外を認める新裁定 | silo の他 genome と `GLOBAL_VALUE_DEFINE` 無の文脈、第 2 compiler、repo の独立した検査器としての試験と変異、列挙した 21 entry の外の TU (本 wave の証拠のままの場合)。段 2 でも同じ例外が要る | 裁定だけ (+ 広げる場合は計算 1 job) |
| 3 | **header を変えない別候補。** 取引 loop (dispatch・abort/retry・commit 後の計数) を各 `tpcc_<protocol>.cc` の `#if TRACE` 側へ複製し、取引種別と計数を .cc 側で扱う | D297 は現行のまま通る可能性がある (未実証、段 2 plan 3.2)。D2225 決定 2・3・5 と D2230 の系列の再裁定が要る | 検証済みの C1'・C2'・C3 と単位 1〜3・本 wave の証拠を捨てる。TRACE=1 と TRACE=0 で workload の経路が分かれ、trace が性能 build と同じ経路を観測しているかの確認が新たに要る。取引 loop の二重管理 | C++ 実装・レビュー・計算のやり直し (1 wave 以上) |
| 4 | **当面は何もしない。** C2' は branch 上の証拠として保持し、TPC-C 段 1 の campaign での認定は保留する | なし | 研究前進 (TPC-C 段 1 の silo・mocc の campaign 認定) が止まる | なし |

### 5.3 推奨の理由とやらない理由

- **推奨は択 1 の設計審査。** 段 2 (設計 §5.3・§7.1 の単位 6・7) も `include/tpcc.hh`・`include/tpcc/tpcc_initializer.hh` などの header を変えるので、択 2 の C2' 限りの例外は段 2 で同じ諮問を繰り返す。header を変える pin 前進が今後も続くなら、例外を重ねるより受理の規則を 1 度設計する方が D297 の保証名と実態を離さない。
- **択 1 をやらない理由の最も強い形:** pin 前進の最後の防壁の受理集合を、ちょうど候補が赤になった時点で広げる形になる。consumer TU の母集合の閉包を急げば新しい偽緑を作る。
- **択 2 が最短であること:** 規律 1 の趣旨 (性能 build からの trace 除去) に照らすと、C2' の header 差分は `#if TRACE` / `#if !TRACE` と `#line` だけで、本 wave の 21 entry の完全展開と 4 binary の逆アセンブルは一致した。研究を急ぐなら択 2 (16 文脈 × GCC 2 版へ広げた比較つき) が最短で、失う保証は上の表のとおり限られる。ただし段 2 で再び例外が要る。
- **択 3 を推さない理由:** 検証済みの成果を捨て、取引 loop の二重管理という新しい負担を作る。header を変えずに済むことの利点は、検査器の規則を変えずに済むことだけである。
- 段 2 plan の最初の推奨は「択 1 を別 wave で設計・実装・敵対確認し、それまで pin C」だった。段 3 相談 A が「実装まで束ねた推奨は強すぎる、1〜2 wave は根拠ある上限でない、header 無変更案には D2225・D2230 の再裁定が要る」と攻撃し、成立したので上の形に改めた (`verbatim/s3-consult-A.md`、段 4 裁定 §1)。

### 5.4 人間の手番

- **push (任意の時点で可):** 候補 branch は別名なので、公開しても `izanagi-tpcc-v3-trace` とは衝突しない (force 不要)。主 checkout の submodule から `git push origin izanagi-tpcc-v3-silo-mocc` (branch は本 wave の land 後に主 checkout の submodule の git dir へ取り込む)。
- **pin 前進の承認:** §5.2 の択の裁定の後。承認後の pin 前進 (gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` の同時更新、先例 D2150 / D2184) は AI の wave。

## 6. 経過

- **段 1:** brief (`verbatim/s1-brief.md`、provisional (P1)〜(P7))。前提の実測 = branch の作成と照合、D297 検査器の実走、GitHub の ls-remote。
- **段 2・3:** 受理方式が設計択一で正しさ防壁に触るので残した。plan 1 本 (`verbatim/s2-plan.md`) → 敵対相談 2 本 (A = 正しさ境界・受理方式 `verbatim/s3-consult-A.md`、B = 実効性と過剰・削除 `verbatim/s3-consult-B.md`)。A は 16 文脈の説明・`-dD` の扱い・header 無変更案の既裁定・推奨の束ね方を、B は変異の再演と「影響しない側の PASS」の kill 条件を攻撃し、いずれも採用 (段 4 裁定 §1)。
- **段 4:** `verbatim/s4-ruling.md`。変異を 4 件に絞り (結合固有の H-set と規律 1 層の H-line、protocol 側の代表 2 件)、受理方式を 4 択に。
- **段 5:** Codex author B (probe、254 秒) が単位 3 の probe を 2 protocol 向けに改めた。自己確認の `py_compile` が作った `__pycache__` を消そうとして拒否され、指示どおり報告の途中で停止した (改修自体は入っていた)。親が probe を job dir へ退避し、差分を作り、自己試験 (184 / 184) と anchor 照合を行ってレビューへ渡した。
- **段 6:** 敵対レビュー 2 本 (A = 正しさ境界 NO-GO: 4 OID を裁定済みの値に固定していない、B = 過剰・削除 GO: C4 の結果名・診断計数の名残・説明文)。**親の検算で H-line の判定の誤りを見つけた:** TPC-C consumer を target 名 (`tpcc_` で始まる) で選んでいたが、実際の 21 entry では該当が 12 件 (`transaction.cc` の tpcc target 3 件を含む) で、正しく検出しても必ず「理由違い」になる形だった。selftest の合成 row が実構成を写していなかったため、レビュー 2 本とも見逃した。段 6 裁定 (`verbatim/s6-ruling.md`) で fix 1 巡 (Codex、216 秒: source で選ぶ・selftest を前例の実測 21 組にする・旧 filter が拒否される陰性 case・結果名・名残の削除)、親は投入 script に OID 照合を足した。焦点再レビュー (`verbatim/s6-review-F-1.md`) は全所見 closed、GO。
- **段 7:** 記録の read-only レビュー 1 本 (`verbatim/s6-review-R-1.md`、NO-GO) が Codex 実績の合計の誤り (初稿の 112 call・1,483 秒は受領証の別 field を拾っていた)、worklog の [T-2854] 更新本文での旧事実の脱落、F109 再発の恒久対応の言い過ぎ、trace 量の単位を指摘し、全件を直した。焦点再レビュー (`verbatim/s6-review-G-1.md`) は数値と F109 の記述を closed とし、worklog の 2 箇所 (C 単独の pin 前進の既承認の脱落、択 4 を含めて「既裁定の変更を要する」と書いた矛盾) を残したので、親が直して一次資料 (main の gitlink、本 insight §5.2) と照合した。
- Codex 子は計 10 本 (plan 1・consult 2・author 1・review 2・fix 1・focus 1・記録レビュー 1・記録の焦点再レビュー 1)。受領証の `actuals` の合計は model call 143、wall 1,842.6 秒 (段 7 の 2 本を除く 8 本では 116 call・1,546.1 秒)。全子 gpt-6-sol / medium。

## 7. 主張しないこと

- TPC-C の直列化可能性の認定。本 wave は TPC-C の trace を verifier に通していない (依頼の確認項目は構造・witness・内容で、結果名は `structure+witness+content pass`)。campaign の pin の tpcc binary は C2' が pin に入るまで v2 を出す。
- D297 の合格、`.text` の bytes 一致、全 compiler・全 macro 構成での TRACE=0 同一性。比較は選んだ構成 (Release・stock・GCC 11.4) の 21 entry と 4 binary に限る。
- 他 7 protocol の TPC-C binary の比較 (前処理の 21 entry には含まれるが、binary は silo・mocc の 4 本だけ)。
- v3 の X 行の実出力 (正常走では X = 0)。
- throughput (trace build の値)。

## 8. 再現資料

- job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/`: `C.bundle`・`C2p.oid`、`mk-c2p.sh`・`mk-bundle.sh` (親の branch 作成と bundle)、`probe/` (run_probe.py・v3check.py・selftest.py・mutation-spec.template.json、Codex author B が単位 3 の probe を改めたもの。sha256 = `evidence/probe-sha256-v2.txt`)、`verbatim/origin-probe/` (起点)、`probe-snapshot-pre-fix1/`、`spec/mutation-spec.json`、`check_anchors.py`・`summarize.py`、`run-compute.sh`、`evidence/compute-1/` (compute.json 本体と 1.6 GB の log)、`evidence/traces-1/`、`d297-C-to-C2p.*`、`review/` (起点からの差分)。
- repo には probe の `.py` と差分の `.patch` を入れていない (実装面の判定のため)。
