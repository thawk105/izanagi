---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-23
wave: dev-wave-t2854-mocc-v3-emitter
seq: 1
---

## {{D:tpcc-v3-producer-mocc}}. TPC-C 段 1 の mocc の trace v3 producer は、候補 C の上に C1 を載せ直した別 branch に D2225 と同じ切替で置き、規律 1 の比較基点は C にする

**決定:**
1. **置き場:** CCBench の新しい local branch `izanagi-tpcc-v3-mocc` = 候補 C `68106660` → C1' `6aa7a58f` (C1 `56b5cb70` の `cherry-pick -x`、header 2 file の blob は C1 と同一) → C3 `53f6b097` (`cc/mocc/transaction.cc` だけ)。`izanagi-mocc-xp-instrumentation` (= C) と `izanagi-tpcc-v3-trace` (C1・C2) は動かさない。push・gitlink・承認定数は動かさない (D16)。
2. **切替:** D2225 決定 2 と同じ。mocc の writePhase が取引種別の context を 1 回読み、非 0 なら C / R / W と X 4 箇所 (not-locked-at-entry、UPDATE と DELETE の lock-lost-before-write、lock-lost-before-publish) を v3 helper で出し、0 なら既存の v2 の式と既存の `izanagi_trace::emit_lock_violation` 呼出しを使う。E の直後に context を 0 へ戻す。P 行・G2 watermark (環境変数で有効化) は変えない。
3. **規律 1 の証拠:** 比較基点は C (新 branch の親)。D2225 決定 6 と同じ種類の証拠 (変更 header を読む 12 source / 21 entry の TRACE=0 完全展開・include 活性の一致、同じ 21 entry の TRACE=1 構文検査、tpcc_mocc / ycsb_mocc の TRACE=0 binary 比較) を C と C3 で取り、D297 の合格とは呼ばない。

**理由:**
- 設計 §5.3 は pin 前進を T-2844 の候補 C の上に積んで 1 回にする構成を採る。C1 は C と path が重ならないので、C の上へそのまま載せ直せる (blob 同一を照合)。
- silo の C2 を同じ branch に含めないのは、依頼が C1 の helper と mocc の emitter に限るため。単位 11 で C1'・C2・C3 を 1 系列に並べるときも path は重ならない。
- 比較基点を pin にすると、C の X/P 計装 (T-2844 で D297 を通した差分) まで本 wave の差分に混ざり、本 wave の変更の除去を示す比較にならない。

**却下した選択肢:**
- `izanagi-tpcc-v3-trace` (C1・C2) の上に mocc の emitter を積む — C の X/P 計装を含まず、mocc の証拠面 (YCSB の certified に要る X/P) が無い系列になる。
- `izanagi-mocc-xp-instrumentation` を進めて C の上へ直接積む — 稼働中の T-2858 が C をこの branch で材料として固定している。
- v3 の X だけを別の関数 (header 内の振り分け) にまとめる — verifier の証拠面検出が関数名で探すため (D2225 の却下理由と同じ)。
