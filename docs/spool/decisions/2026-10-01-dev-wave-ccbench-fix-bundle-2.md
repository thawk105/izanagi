---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-10-01
wave: dev-wave-ccbench-fix-bundle
seq: 2
---

## {{D:d297-cicada-value-contexts}}. D297 検査器の Cicada 対応は CONTEXT_MACROS への登録でなく、検査器の中で Cicada の値 macro 4 個の 16 組合せを列挙して比べる形にし、束ねた tip の条件 (2) は合成 A→B′ の D297 pass で示す

**決定 1:** `tools/check_trace0_preprocess_identity.py` は `cc/cicada/` 配下の `.cc` について、old/new 各 commit の Cicada の CMake 供給値を `Genome("cicada", {})` と `_head_defines` で取り、両側の供給集合の一致と INLINE_VERSION_OPT・INLINE_VERSION_PROMOTION・SINGLE_EXEC・WORKER1_INSERT_DELAY_RPHASE の値が 0/1 であることを確かめてから、4 値の直積 16 組合せ × 既存 overlay 2 = 32 文脈で正規化前処理出力と include 活性を比べる。期待件数は path ごとに列挙元から導出し、実比較数と食い違えば拒否する。未登録の macro は従来どおり停止する。`orchestrator/campaign/source_digest.py` の CONTEXT_MACROS と digest の bytes は変えない。

**決定 2:** CCBench の修正を束ねた tip について、D2322 項 4 の条件 (2) (F → tip の TRACE=0 差分が修正の hunk だけ) は、合成 A (親 F、tree = F に各修正 tip の F からの diff を `git apply` で独立に当てたもの) → B′ (親 A、tree = 束ねた tip の tree) の D297 pass (GCC 11・12) と、F と各修正 tip から作った修正 hunk の manifest で示す。修正 hunk そのものを D297 が認証したとは書かない (両側に同じ修正が入るため)。

**理由:**
- D2322 項 4 は「cicada の文脈 macro を検査器の既知一覧 (CONTEXT_MACROS) へ登録する」と書くが、CONTEXT_MACROS は TU 内 `#define` で注入される macro の素/define 2 文脈用で、2 個以上は結合枝を覆えないので停止する設計であり、ここへ足すと digest の bytes (src token・凍結の閉包) が変わる。Cicada の 4 macro は CMake が `-D` で値を与える macro なので、値の組合せを検査器の中で列挙するのが同じ目的 (未知マクロ停止の解消、緩和しない) を最小の波及で満たす。
- 名前を既知集合に足すだけでは、その macro で条件づけられた枝が比べられないまま通る (緩和)。組合せを実際に列挙し、既定値と反対の値でだけ生きる枝の差を拒否する負例と、列挙を縮める・名前だけ既知にする・期待件数を実数から導出する変異が殺されること (`output/insights/2026-09-30/ccbench-fix-bundle/README.md` §6、変異 7/7) で拡張であることを示した。
- 合成 A→B′ は Silo の先例 (D2322 が条件 (2) として認めた「pin + 修正 → 新 tip」の D297 (b)) と同形で、merge の解決と非修正の差分 (正しさ関門の記録) が TRACE=0 に何も足していないことを機械判定できる。F → 束ねた tip の直接比較は修正を含むので構造上不合格になり、条件 (2) を示さない。

**却下した選択肢:**
- source_digest.py の CONTEXT_MACROS へ 4 macro を足す — digest の bytes と凍結の閉包が変わり、単一文脈列の設計の再設計が要る。
- 4 macro を既知集合に名前だけ足す — 緩和。
- 条件 (2) を F → 束ねた tip の D297 の不合格箇所の目視で示す — 検査器は最初の不一致で止まり、差分が修正の箇所に閉じることを示せない。人の目だけの受け入れは D2322 項 4 が却下。
