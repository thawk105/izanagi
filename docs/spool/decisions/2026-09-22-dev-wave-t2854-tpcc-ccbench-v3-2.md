---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-22
wave: dev-wave-t2854-tpcc-ccbench-v3
seq: 2
---

## {{D:tpcc-v3-producer-silo}}. TPC-C 段 1 の trace v3 producer (CCBench 側) は取引種別の thread-local context で silo の出力を v2 / v3 に切り替え、header を含む候補の規律 1 は consumer TU の前処理比較と binary 比較で確かめて D297 の合格とは呼ばない

**決定:**
1. **v3 frame:** `C <txid> <thid> <epoch> <tid> <nR> <nW> <nS> <nQ> <tx_type>` (10 token)、`R <txid> <table> <key_hex> <ver_epoch> <ver_tid>`、`W <txid> <table> <key_hex> <U|I|D> <epoch> <tid>`、`X <txid> <table> <key_hex> <reason>`。table は `Storage` の整数 (TPC-C は 0..10)、tx_type は `TxType` の値 (1..5、0 は出さない)、段 1 は nS = nQ = 0。P / E は v2 と同形、I 行は出さない。並走の verifier 側 wave と相互連絡で同じ形に合わせた。
2. **v2 / v3 の切替:** `include/tpcc.hh` が `tx.begin()` 直後に trace build 限定の thread-local context (外部 linkage の inline 関数内、TU 間で共有) へ取引種別を置き、silo の writePhase が取引ごとに 1 回読む。非 0 なら C / R / W と X 3 箇所を `include/trace.hh` の v3 helper で出し、0 (YCSB ほか) なら既存の v2 の式と既存の `izanagi_trace::emit_lock_violation` 呼出しをそのまま使う。E の直後に context を 0 へ戻す。1 取引に C 行はちょうど 1 本。
3. **計数:** `include/tpcc.hh` の commit 成功後の quit 判定を `#if !TRACE` で囲み、trace build は成功 commit を必ず数える (設計 §3.5)。TRACE=0 の判定と計数順序は変えない。witness の許容幅は作らない (D295)。
4. **規律 1:** 追加はすべて `#if TRACE` (計数だけ `#if !TRACE`) 内。`#line` で TRACE=0 の論理行番号 (ERR の `__LINE__`) を pin と一致させる (tpcc.hh 4 本、silo 4 本、先例は mocc の計装候補)。
5. **置き場:** CCBench の local branch `izanagi-tpcc-v3-trace` に、現 pin e9e477ca の子として C1 (include/trace.hh・include/tpcc.hh) と C2 (cc/silo/transaction.cc) の 2 commit。push は人間 (D16)。gitlink・承認定数は動かさない。
6. **規律 1 の証拠の範囲:** D297 の検査器は header の差分を保証範囲外として拒否するので、この候補は D297 の合格を名乗らない。本 wave の証拠は、変更 header を include する 12 source / 21 compile entry の TRACE=0 完全展開 (`-E -P -dD`) と include 活性 (line marker の入退場の file 列) の pin との一致、同じ 21 entry の TRACE=1 構文検査、tpcc_silo / ycsb_silo の TRACE=0 binary 比較 (nm / strings / 正規化逆アセンブル)。pin 前進 (単位 11) で header 差分をどう受理するかは本決定では決めない。

**理由:**
- silo の `transaction.cc` は ycsb_silo と tpcc_silo で同じ define のまま compile される (現行 CMake は workload 別の define を供給しない) ので、compile 時に workload を区別できない。
- 既存の v2 の `emit_lock_violation(` 呼出しを残すのは、verifier の証拠面検出 (`orchestrator/verifier/model.py` の正規表現) が関数名で探すため。v3 helper だけにすると YCSB の certified に要る証拠面が消える。
- D2207 は D297 の検査器の include 規則を緩めず計装側を直すと決めている。本 wave で検査器を拡張すると gate の変更になり依頼の scope 外なので、証拠の種類を分けて名乗りを限定する。
- 2 commit に分けると、mocc の v3 emitter (単位 3) が C1 だけを mocc の X/P 計装候補の上へ載せられる。

**却下した選択肢:**
- TRACE=1 の target にだけ workload 別 define を足す — 可能だが CMake の変更と取引種別の二重管理が増える。
- v2 の X 呼出しを v3 helper や header 内の振り分けへ置き換える — 証拠面検出が外れる。
- `include/tpcc.hh` の abort・commit 失敗の各経路でも context を 0 へ戻す — 次の取引は必ず begin 直後の setter を通り、silo は E の直後に戻すので冗長。共有 header の変更面と `#line` が増える。
- D297 の検査器に consumer TU の解析を足して本 wave で合格させる — gate の変更で scope 外 (D2207 の向きとも合わない)。
- 1 commit にまとめる — 最終 tree と確認命題は同じだが、単位 3 が header だけを再利用できない。
