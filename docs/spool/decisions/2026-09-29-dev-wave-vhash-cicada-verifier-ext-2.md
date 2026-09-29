---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: dev-wave-vhash-cicada-verifier-ext
seq: 2
---

## {{D:cicada-tpcc-trace-v3-overlay}}. Cicada の TPC-C trace は既存の v3 で出し、md_3 の計装の bytes を変えない重ね patch として C1' 以降に置く。insert の正例は orphan read で検出・帰属し、巡回の経路は既存の壊しを TPC-C に重ねて確かめる

**決定:**
1. **書式:** Cicada の TPC-C 走行は、判定器が既に受理する trace v3 (D2224 / D2225、表番号・取引種別付き、nS = nQ = 0) で出す。切替は silo と同じく `include/tpcc.hh` の取引種別の thread-local 文脈を `traceCommit()` が読む形で、文脈が 0 (YCSB ほか) なら D2279 の v2 の式をそのまま通す。判定器の production とテストは変えない。
2. **置き場:** `patches/instr-cicada-trace.patch` (D2279) の bytes は変えず、TPC-C 用は `patches/instr-cicada-trace-tpcc.patch` を重ねる。適用順は CCBench C1' `6aa7a58f` (以降) → 既存計装 → 重ね patch。pin C 単独には重ねない (v3 の部品が C1' にしかない)。依頼の「instr-cicada-trace.patch の更新」はこの重ね patch の新設と読み替える。`patches/ledger.json` には登録しない (entries 1 件固定)。pin の C2' 系への前進後は、重ね順の厳密適用と生死確認を取り直す。
3. **正例と完了判定の読み替え:** 依頼は「insert / delete を壊した patch を判定器が巡回として検出し帰属できる」。insert の意味を壊した正例 `patches/broken-cicada-insert-past-ts.patch` (insert の新版に自分より古い時刻を付ける) は、事前登録では orphan read (生産者の W が無い版の読み) の検出と、raw trace からの数え直し・事象との一致で判定し、巡回の経路は既存の `broken-cicada-skip-read-recheck.patch` を TPC-C に重ねた版で確かめる。delete を壊した正例は作らない。判定器の門 (巡回・integrity 数値項目・存在履歴違反のどれかが 0 でなければ失格) は変えない。実測では insert の正例でも巡回が 1 件出て、その辺も壊した insert に帰属した。
4. **stock の欠陥の扱い:** stock Cicada (CCBench pin C) は TPC-C の全 mix (Delivery を含む) × 4 thread で `gc_records()` の `ERR` により、trace の有無に依らず毎回異常終了した。本 wave では直さず、stock 対照の合格を要する正例を delete を含まない cell に移し、原因の特定から始める修理を次の一手に起票する (D2277 項 2)。

**理由:**
- md_14 が既存計装の上に forwarding の試作を重ねて YCSB を検査しているので、既存計装の bytes と v2 出力を揺らさないことが互換の条件である。1 本に統合すると pin C で TRACE=1 の compile が壊れる。
- v3 は表を持ち、存在履歴の検査 (D2232) も v3 でだけ走る。TPC-C を v2 で出すと表だけ違う key の版が混ざる (D2224)。
- TPC-C で NewOrder 行を読むのは Delivery だけで、Delivery は読んだ行を自分で削除する。delete 経路の単一 site の壊しは他の検査 (install 時の最新版検査、validation の再検査と (b)) に止められ、committed な巡回を作らない (段 2 plan・段 3 相談 2 本・親の読みが一致)。insert の意味の壊しは TPC-C では巡回より先に orphan read として判定器に現れる。
- 取引種別で絞って read 検査を壊す案は、insert / delete の検出力ではなく read 検査の検出力を示すだけなので正例に数えない (段 3 相談 A / B の must-fix)。
- 実測 (一次資料 `output/insights/2026-09-29/vhash-cicada-verifier-ext/README.md`): stock の TPC-C 5 走行で巡回 0・integrity 0・存在履歴違反 0・C 行 = commit 数、insert の正例は orphan read 1,144,962 件の全件と巡回 1 件が壊した insert に帰属、既存の壊しの TPC-C 版は巡回 2,135 件・代表 witness 20 件中 20 件が表まで照合して帰属、TRACE=0 は 12 TU で命令列が pin C と一致。

**却下した選択肢:**
- 既存計装 1 本に v3 を統合する — pin C の TRACE=1 compile と md_14 の YCSB 検査を壊す。
- Cicada の中で v3 の出力と取引種別を自前で持つ — 共有 header と意味を二重管理し、trace build の commit 計数も別途直す必要がある。
- TPC-C を v2 のまま key に表を混ぜて出す — 書式の変更に当たり、存在履歴の検査も走らない。
- insert / delete を含む取引に限って read 検査を壊す正例 — insert / delete の検出力を示さない。
- stock の `gc_records()` の欠陥を本 wave で直す — CCBench の変更で所有外、上流 CI と pin の手続きが要る。
