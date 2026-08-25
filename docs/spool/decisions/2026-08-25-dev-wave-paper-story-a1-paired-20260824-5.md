---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-paper-story-a1-paired-20260824
seq: 5
---

## {{D:family-admission-by-contract-registry}}. 族の形状要求は除外条件でなく契約記録へ集約し、期待値は test-owned literal に置く

**決定:** 自動編入する族 (`orchestrator/tests/test_p3_exploration_namespace.py` の
exploration campaign root producer) に、別形状の driver が現れたとき、次の順で扱う。

1. **族から外す条件を足さない。** 編入は AST の発見だけで決め、除外述語・`skip`・
   名前による分岐を作らない。閉包検査を緩める方向は採らない。
2. **形状要求を既定値のない契約記録へ集約する。** driver ごとに CLI authority mode
   (`coder-opt-in` / `no-coder-cli`)、coder entrypoint site、期待 generator、
   opt-in 無し / build spy / routing の 3 種 argv factory、AST 呼出し数、実行時呼出し数、
   期待 campaign ID の独立導出を、すべて必須 field として登録する。
3. **登録漏れは二重に落とす。** 直接 index の `KeyError` と、発見集合と登録集合の
   完全一致 assertion の両方。lookup を helper へ切り出す場合は、欠落 map を渡して
   `KeyError` を要求する検査を同時に置き、hard fail 自体の恒真化を塞ぐ。
4. **期待値は test 側が所有する literal にする。** 観測した実行時 context・
   sink が受けた config・driver の自己申告から期待値を作らない。
   production の生成器を期待値導出に使う場合は、同一性を決める literal
   (slug、tag、workload 順) を test 側で別に pin し、生成器の共通変異が
   期待側と実際側を同時に動かす経路を塞ぐ。
5. **順序を持つ成果は順序で比較する。** 複数の campaign root を作る driver では
   観測 ID を呼出し順の tuple で比較し、集合比較は補助へ降格する。
   集合比較だけでは、同じ workload を複数回実行した縮退と順序反転を通す。

**理由:**
- 編入条件と形状要求が別々に決まっていると、新形状の driver は「族に入るが契約を
  満たせない」状態へ構造的に落ちる。契約記録は両者を 1 箇所で突き合わせる。
- 期待値を production から導くと、生成器を壊す変更で oracle も同時に壊れ、
  検査が生き残ったまま検出力だけが消える。実測では、期待 campaign ID を
  production の config 生成器から作る案は、生成器の識別子を変える変異を
  当該 node では検出できなかった。
- 「明示 opt-in 無しに coder 由来 build へ進まない」という族の不変条件は、
  coder 由来 build を一切許さない driver に対しては自明に成立して何も検出しない。
  その driver には向きを変え、「coder 権限の入口が存在しない」ことと
  「build 文脈が coder 権限を持たない」ことを直接検査する。

**却下した選択肢:**
- **driver 側を族の形状へ合わせる** — 必須 option へ既定値を与えれば
  「証拠束縛を指定しない計測」が構造的に可能になる。正しさゲートを緩める方向であり採らない。
- **族から当該 driver を外す条件を足す** — 閉包検査を緩め、以後の driver が同じ穴から漏れる。
- **観測値を期待値にして検査を通す** — driver が何を作っても一致する恒真な検査になる。
- **`manual` を CLI authority mode の語として使う** — 既存の manual build 分類と
  同じ語で別の軸を指し、識別子が二義化する (D75)。
