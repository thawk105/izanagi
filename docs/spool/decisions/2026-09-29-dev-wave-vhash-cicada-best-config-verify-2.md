---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: dev-wave-vhash-cicada-best-config-verify
seq: 2
---

## {{D:cicada-best-config-verify}}. VHash 論文の比較相手 Cicada の観測最良設定は、実走した範囲で判定器の巡回なし (上限 indeterminate) として主比較の相手に使い、inline slot の記録の忠実性は repo 外の診断 patch の 3 点比較で確かめる

**決定:**
1. md_11 の観測最良設定 (rr5・rr50・rr95 用 BACK_OFF=0・INLINE_VERSION_OPT=1・INLINE_VERSION_PROMOTION=0・REUSE_VERSION=1・WRITE_LATEST_ONLY=0、100 操作型用 BACK_OFF=0・OPT=0・PROM=0・REUSE=0・WLO=0) を、md_3 の trace (`patches/instr-cicada-trace.patch`、D2279) で判定器に掛けた。YCSB (skew 0.9) の 30 条件 (tuple 200 の thread 4・48 と tuple 1M の thread 48、走行 1 秒) の 32 run で、stock の最良設定と既定は巡回 0・integrity の数値項目 0・C 行 = commit 数だった。論文の「正しさ未検証」の注記は「この範囲で巡回なし (上限 indeterminate、certified ではない)」に置き換えてよい。md_11 の主比較条件 (走行 3 秒以上) そのものは検査していないことを併記する。
2. INLINE_VERSION_OPT=1 の inline slot は再利用されるので、版を選んだ瞬間・read set への登録・commit の 3 時点の wts を比べる診断を、trace の行を変えない repo 外の使い捨て patch として全ての検査 build に重ねる。3 点の食い違いと、基準時刻より新しい版の登録が 0 でない run は、巡回 0 でも検査通過と数えない (診断異常)。今回は全 run で 0。
3. 検出力は、同じ設定に既存の壊し `broken-cicada-skip-read-recheck.patch` を重ねた正例で設定ごとに示す (BEST の rr50 thread 4・48、BEST100 の 100 操作型 thread 4 で検出・帰属)。既定に近い設定での正例 (md_3) を最良設定の検出力の代わりにしない。
4. `patches/instr-cicada-trace.patch` の bytes は変えない (D2294。記録されない読み書きの経路は見つからなかった)。起動器と診断 patch は repo 外 (Codex author) に置き、`patches/` に足さない。

**理由:**
- 正しさ未検証の相手を主比較に使うことは絶対規律 2 に反する。md_11 の最良設定は既定より 2〜4.5 倍速く、弱い既定を相手にすると baseline が弱くなる (D2291)。
- md_3 の記録は登録時の wts を使い、`READ_WTS_MISMATCH` は登録時と commit 時しか比べないので、版を選んでから登録するまでに inline slot が再利用される窓を見逃す (段 2 plan・段 3 相談 A)。wts は書き手ごとに一意で再利用は wts を上書きするので、選んだ瞬間と commit の瞬間の一致は、その間に版 object が別の版へ再利用されなかったことを示す。
- 診断を `patches/` に置くと patch を全件走査する test と、instr patch の上に試作を重ねている並走 wave に波及する。repo 外なら判定に必要な観測だけを足せる。
- 実測 (一次資料 `output/insights/2026-09-29/vhash-cicada-best-config-verify/README.md`): stock 32 run 合格、inline slot の版は読みの 5.2〜59.4%・書きの 4.7〜36.9%、診断 3 値と `READ_WTS_MISMATCH` は全 35 run で 0、正例 3 本は non-serializable で (辺, 事象) の帰属が成立。計算は合計 1,165 s。

**却下した選択肢:**
- inline slot の件数だけを数える — 経路に到達した証拠にはなるが、記録された版が選んだ版と同じことを示さない (段 3 相談 A1・B3)。
- instr patch に選択時の wts を足して bytes を変える — 並走 wave の重ね patch と D2294 に波及し、判定に要る観測は repo 外の診断で足りる。
- md_11 の主比較条件 (1M・48 thread・3 秒) を全条件の必須 cell にする — trace build では trace 量と判定器所要が予測できなかったので、実測単価から投入可否を決める段階制にした (段 2 plan §4)。実走した J2 (1M・48 thread・1 秒) は判定器 1 run 最長 41.6 秒だった。
- TRACE=0 の命令列の同一性を最良設定の CMake 値で取り直す — 本検査は性能値を出さず instr patch の bytes も変えないので、判定の必要条件ではない (段 3 相談 B6)。
