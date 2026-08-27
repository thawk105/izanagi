---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-28
wave: dev-wave-t2018-condition-meaning-gate-codex-resume
seq: 2
---

## {{D:condition-meaning-independent-arms}}. define 条件の供給と意味は独立した証拠として評価する

**決定:** patch供給defineの関門は、source-owner CMake cache-to-TU route/valueを評価する
supply armと、適用後decoderを実compilerでpointwise評価するmeaning armを、別public function、
別evidence、別reason code、別負例として持つ。単一pass bitへ潰さない。

初版はBACKOFF_FIXEDだけに閉じる。meaningのproof kindはcaptured applied-source decoderを
standalone TUで評価したfinite pointwise witnessとし、actual target TU、dynamic reachability、
exact post-configure build inputを名乗らない。driver integrationはnoneで、driverへの義務接続は
D1198の別残件とする。

**理由:**
- F707は供給されない型、F718は供給・適用・供給検査を通って値の意味だけ違う型である。
  一方の緑は他方の緑を含意しない。
- 文字列存在、binary hash差、格子単射性だけでは、一様shift、別単位、contextごとの結果入替を通す。
- 独立期待bitsとのpointwise比較なら、BACKOFF_FIXED=1000が0へ復号される現物を実compilerで拒否できる。
- driver接続0の段でgateと呼べるのは明示呼出し内だけであり、現行driverが保護済みとは書けない。

**却下した選択肢:**
- supply名集合だけを検査する — wrong RHS/valueとF718を見逃す。
- expected/observedを集合比較する — context入替を通す。
- fixture JSONを任意path/macro/result kindのproduction契約にする — 実在consumer 0の入力面を増やす。
- BACKOFF_FIXED以外7 macroを同じscalar decoderとして一般化する — selector/enum/diagnosticが混在する。
- 格子を0..999へ狭めるだけで族を閉じたとする — 現fixed量軸は閉じてもdefine-decode族は閉じない。
