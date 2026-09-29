# 段 4 裁定 = plan v2 — gen-opt-gate-liveness (md_5、2026-09-29 JST)

確定 2026-09-29 14:51 JST (file の mtime)。裁定 inbox の再走査: wave 開始後に T-2883・T-2885 に関わる新しい裁定なし (docs/decisions.md 末尾の D は 2026-09-29 の他 wave 分)。

## 相談所見の裁定 (consult-a.md、8 件すべて real・採用・scope 内)

- F1 (must-fix) 採用: 照合器は Q の書き key・S の (txid,key)・trace の W 行を全件対応させ、欠け・重複・余分・書式不正を indeterminate にする (下の「照合器」1 に反映)。
- F2 (must-fix) 採用: RMW の刻印は `val_` の memcpy の後、`update` に渡す前に新しい器の `id_` へ入れる。Q に積む「書いた刻印」は器が完成した直後の値。S は writePhase の `memcpy` の入力 (`(*itr).body_.get_val_ptr()`) の先頭 8 byte から採る (「計装」に反映)。
- F3 (must-fix) 採用: B1 の発火計数 committed を「commit した取引で、その取引の中で最初の操作が R か M の key のうち、commit 時点で `read_set_` に無いものが 1 つ以上ある」取引の数に定義し直す (commit 成功の直前に read_set_ を実際に調べる)。B1 は偶数 key のすべての読み (両集合に無いとき) を省くので、同じ key の後続の読みで R が生じることは無い設計だが、計数は設計に頼らず実物を調べる。committed = 0 の run は (b) に数えず判定不能。D1 (b1) の違反取引数との一致は診断。
- F4 (should) 採用: 発生条件を種類別に commit 済み取引の件数で出し、D2b の各種別は対応条件が 0 なら not-exercised。W→R だけの取引は stock でも正常 (自分の書きを返す) ことを README に書く。
- F5 (should) 採用: 判定器の `--ccbench-root` は job で build した patch 適用済みの checkout。当てた file の sha256 を result.json と README に残す。
- F6 (should) 採用: 照合器の自走 test に手製の正例・欠落例・不一致例 (Q 欠け、Q 余分、S 欠け、S 余分、S と W の key 不一致、刻印の値域外、D1 b1・b2・a、D2b i・ii、abort 試行の混入が無い正例) を置き、親が login で実走してから実走結果を読む。
- F7 (should) 採用: 上流 CI 相当は pin 単独と pin + 修正の両方で同じ全体 build と全体 format 検査を行い、終了値と違反の差分を併記する (既に下の設計にある)。
- F8 (should) 採用: 一次資料に「`A` → `Q` の改名、`S` の書式と対応規則」を明記し、U1・U2 の起票文に「設計資料 §3.2 の `A` 行の名前を訂正してから実装」を必須条件として書く。
- 相談の確認点の取り込み: `KEY_SORT` 既定 0 (1 なら順序の基準が変わる → 本 wave は 0 のまま、README に前提として書く)。修正案は `scan` の読み集合優先を変えない → 「全 API の意味が揃った」とは書かない (限界)。

## 共通

- pin = external/ccbench 68106660686232781bca3be792a750d3e19d7a8a (repo HEAD 035fc11fa の gitlink)。
- 名前: 設計資料の「`A` 行」は判定器で abort 要因の集計 (tag `A`) に使用中なので使わない。手順列の記録は tag `Q`、据えた値の刻印は tag `S` とし、判定器が読まない別 file `gate_<thid>.log` (同じ `IZANAGI_TRACE_DIR`) に書く。実装子は `Q`・`S` が判定器 (`orchestrator/verifier/`) と CCBench の trace 出力 (`include/trace.hh`・`cc/*/transaction.cc` の `#if TRACE`) で未使用であることを grep で確かめて報告する。
- 刻印: 64 bit。書き手 = `((uint64_t)(thid + 1) << 48) | seq` (`seq` は thread ごとの通し番号、書きの操作ごとに 1 増やす。abort した試行でも増やしてよい = 同じ値を再利用しない)。初期 load = `YCSB::id_` の既存値 (key id、2^48 未満) をそのまま使う。刻印は `YCSB::id_` (値の先頭 8 byte) に置き、`val_` と VAL_SIZE は変えない。

## 計装 (instr-silo-gate-witness.patch、pin に当てる、すべて `#if TRACE` の内側)

- `include/trace.hh`: `gate_stream(thid)` (thread_local ofstream、`gate_<thid>.log`)、thread_local の「直前に commit した txid」の置き場、`Q`・`S` の書き出し helper。
- `cc/silo/transaction.cc` `TxExecutor::writePhase`: (1) `izanagi_txid` を thread_local の置き場へ残す。(2) `OpType::UPDATE` の各要素で、`memcpy` で据える直前に `(*itr).body_.get_val_ptr()` の先頭 8 byte を読み `S <txid> <key_hex> <stamp>` を書く。INSERT・DELETE は YCSB で使わないので書かない (出たら照合器が判定不能にする)。
- `include/ycsb.hh` `YcsbWorkload::run`: 試行ごと (`RETRY:` の後) に手順の記録を空にし、各操作で (op, key_hex, 観測した刻印 or `-`, 書いた刻印 or `-`) を積む。READ は `body->get_value().cast_to<YCSB>().id_` を観測。WRITE は新しい器の `id_` に刻印を書く。RMW は旧値の `id_` を観測し、`val_` の memcpy の後・`update` に渡す前に新しい器の `id_` に刻印を書く (F2)。積む「書いた刻印」は器が完成した直後の値。abort した操作 (status が aborted) は積まない。`tx.commit()` が true を返した直後、counter 加算の前に `Q <txid> <thid> <n> <op>:<key_hex>:<obs>:<wr> ...` を 1 行書く (op は R・W・M)。
- TRACE=0 では何も残らない (枝除去で pin と bytes 一致)。

## B1 (broken-silo-b1-unregistered-first-read.patch、計装の上、無条件)

- `TxExecutor::read` で読み集合・書き込み集合の両方に無い key のうち、key id が偶数のものについて、`read_internal` と同じ一貫読み (lock の解けた TID を 2 度読んで一致を確かめる) で値を取り、`read_set_` に登録せず thread_local の副 buffer (取引の開始で空にする) に置いてその body を返す。`max_rset_` は更新しない。
- 発火の計数 (F3): reached = 省いた読みの回数、committed = commit が成功する直前に、その試行で省いた key のうち `read_set_` に実際に無いもの (searchReadSet で確かめる) が 1 つ以上ある取引の数。省いた key は試行ごとに thread_local で持ち、試行の開始 (begin) で空にする。process 終了時に stderr へ `GATE_B1_FIRED reached=<n> committed=<n>` を 1 行。計数は relaxed atomic の加算だけ。

## 修正案 (fix-silo-intra-txn-values.patch、pin 単独にも計装の上にも当たる、無条件)

- `TxExecutor::read`: 書き込み集合を先に探し、無ければ読み集合、無ければ tuple を読む。
- `TxExecutor::update`: 同じ key が書き込み集合にあれば、その要素の `body_` を新しい body で置き換えて戻る (op は変えない)。
- それ以外は変えない。clang-format 14 (repo の `external/ccbench/.clang-format`) で整形済みの形にする。

## 照合器 (gate_check.py)

入力: trace dir (trace_*.log と gate_*.log)。repo の `orchestrator.verifier.parse.parse_trace_dir` で C…E 枠を読み (判定器と同じ解釈)、gate file は自前で読む。出力: JSON 1 つ。

1. **入力の到達可能性 (先に検査、欠ければ全体を indeterminate):** gate file が trace file と同じ thread の組で存在、全行の書式が正しい、Q の txid が C…E 枠と 1 対 1 (欠け・重複・余分なし)、Q と枠の thid が一致、thread 内の順序が一致、S は UPDATE の W 行と (txid, key) で 1 対 1、parse の issues が空。刻印の値域: 観測した刻印がすべて「初期 (2^48 未満)」か「書き手の形 (上位 16 bit = 1..thread 数)」であること。
2. **D1:** 取引ごとに (a) Q の書き (W・M) の key 集合 = W 行の key 集合、(b1) 「その key への最初の操作が R か M」の key 集合 ⊆ R 行の key 集合、(b2) R 行の key 集合 ⊆ Q の読み (R・M) の key 集合。違反を条項別に件数と見本 (先頭 20 件の txid) で出す。
3. **D2b:** 取引ごとに Q を順に辿り、key ごとの「自分の最後の書きの刻印」を持つ。(i) 自分が先に書いた key の読み (R・M の観測) の刻印がその時点の最後の書きと一致すること、(ii) 取引の終わりに key ごとの最後の書きの刻印 = その key の S の刻印。種別ごとに件数と見本。
4. **発生条件の計数:** 取引数、読みだけの取引数、同じ key が 2 回以上現れる取引数、次の型が現れた取引数と出現数: R→R、W→R、R→W→R (M→R を含む)、W→W、M→M、書き → 書き全般。
5. 判定: 各述語について `pass` (到達可能 かつ 違反 0)、`violation` (違反 ≥ 1)、`indeterminate` (到達可能性の欠け)。D2b の (i)・(ii) はそれぞれ、対応する発生条件の件数が 0 なら `not-exercised` を併記。

## 起動器 (launch_gate_liveness.py)

先例 /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/launch_mutation_run.py と /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-si-v2/launch_si_run.py の形に合わせる。

- 引数: `--job {stock,b1,fix}`、`--patch-dir`、`--checker` (gate_check.py の絶対 path)、`--third-party-cache`、`--out-dir` (空であること)、`--repo-root` (計測木)。login node なら拒否。
- preflight: 先例と同じ (python ≥ 3.10、cmake ≥ 3.21、policy の toolchain、numactl と /usr/bin/time、単独性、空き容量、`assert_pinned_clean`)。
- build: job ごとに patch 列 (stock = [計装]、b1 = [計装, B1]、fix = [計装, 修正]) を pin に `git apply` (fuzz なし) で当て、`s2_verify_calibration._broken_build_and_verify` と同じ configure (STOCK_G.cmake_defines + `-DCCBENCH_TRACE=1`、Release、sanitizer OFF、policy の compiler) で `ycsb_silo.exe` を build する。macro (`-D<name>=1`) は付けないので条件 gate は通らない (無条件 patch の別 build)。当てた後の file の sha256 と binary の sha256 を記録。build 後は patch を外して submodule を clean に戻す (先例の `applied()` の形)。
- run: workload W-rmw (`thread_num=4 ycsb_tuple_num=200 ycsb_zipf_skew=0.9 ycsb_rratio=50 ycsb_rmw=true ycsb_max_ope=5`) と W-blind (同じで `ycsb_rmw=false`) を各 1 回、`extime=1`、`clocks_per_us` は `s2_verify_calibration.CLK`、argv 形は `_run_once` と同じ (numactl interleave)。`IZANAGI_TRACE_DIR` は run ごとの新しい dir。stdout・stderr を全文保存。
- 判定: 完走した run ごとに (1) 既存の判定器 (`_verifier_run` と同じ argv、commit 件数の証人つき、`--ccbench-root` は patch を当てた状態の checkout) の JSON、(2) 照合器の JSON。
- 生出力: trace dir (trace_*.log と gate_*.log) を run ごとに tar.gz にして sha256 を記録。
- fix job だけ追加: 上流 CI 相当の build を 2 回 — pin 単独と pin + 修正 — それぞれ新しい checkout で `cmake -S <src> -B <build> -DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF` → `cmake --build <build> -j <nproc>` (compiler は policy のもの、依存物の供給は他の build と同じ)。rc・所要秒・log の末尾 200 行を記録。
- 出力: `<out-dir>/result.json` (job・host・時刻・pin・patch と binary の sha256・各 run の commits/aborts・判定器の verdict と要約・照合器の JSON・B1 の発火行・CI build の結果)、`meta.json`。例外は記録して非 0 終了。

## format 検査 (fmt_check.py、login)

- repo の external/ccbench (pin で clean) から `git ls-files -- cc include common` の `.cc/.hh/.cpp` を job 一時 dir へ写し (pin tree)、同じものに修正案 patch を `git apply` した tree を作る。
- 各 tree で `/usr/bin/clang-format-14 --dry-run --Werror` を file ごとに走らせ、違反のある file と違反件数 (警告行の数) を数える。
- 出力: pin と pin + 修正の file 別違反件数、修正で変わる file の違反の増減、修正で変えた行の範囲に掛かる違反の件数。CI の format 段が pin + 修正で通るか (全 file 違反 0 か) も書く。

## 事前登録 (結果を見る前)

- (a) stock: 両 workload で照合器の到達可能性が成り立ち、D1 = pass。成り立たなければ smoke とみなして止め、何が欠けたかを構造化する。D1 = violation なら述語を緩めず、条項・見本を設計へ戻す (§7)。
- (b) B1: 両 workload で B1 の committed ≥ 1 かつ D1 = violation (条項 b1)。D1 (b1) の違反取引数と B1 の committed の一致は診断として記録 (ずれれば所見)。committed = 0 の run は (b) に数えない。
- (c) stock の D2b: 違反件数を種別ごとに記録する。予想は「両 workload で ≥ 1」(§3.5)。調査の計数で certified に使わない。
- (d) 修正: 両 workload で到達可能性が成り立ち、D2b = pass (該当する発生条件 ≥ 1 のとき)、D1 = pass、既存の判定器の verdict が serializable (certified) で commit 件数の証人と一致。
- 既存の判定器の verdict は stock・修正で serializable を期待 (診断)。B1 の既存判定器の verdict は記録だけ (盲点かどうかの資料)。
- 再走: build 失敗・run の異常終了・queue 待ちの打ち切りは 1 回だけ再投入してよい。到達可能性の欠けは patch・照合器を直してから再投入 (2 node 時間の上限内)。
