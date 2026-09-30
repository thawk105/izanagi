---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-30
wave: dev-wave-acceptance-shard0-load
seq: 2
---

## {{D:t080-base-prewarm-not-landed}}. 受入 controller が collection 中に T-080 共有 base を先に組む実装は、同時刻対照 2 対が割れて事前登録の land 条件を満たさないので main へ入れない。floor の snapshot 比較器の置換と active-v2 の emitter 共有も採らない

**決定:**

1. md_6 (受入 shard-0 の最忙 worker の仕事を減らす) の候補のうち、controller が `pytest_configure_node` の早期 prewarm 分岐から、worker の collection と並行に T-080 共有 base の default key と active-v2 key を既存の `_T080SharedBases` 規約のまま先に組む形 (D1708 が次の一手として名指しした形) を実装したが、**main へは入れない**。実装は branch `worktree-dev-wave-acceptance-shard0-load` (tip c9af2b562、実装だけの系列は `as0-u1` の 7d20b2c1f) に残す。
2. 判定は段 4 で事前登録した land 条件どおり: 対 1 (collection 約 90〜120 秒) は shard-0 の test 段 T0 が 130.5 秒 (32%) 縮んだが、対 2 (collection 約 68 秒) は 10.7 秒伸びた。L1 (2 対とも ΔT0 > 0) と L4 (2 対とも W0 が悪化しない) が偽。
3. floor official 群の `_real_output_snapshot()` 前後比較を「cacheable は (index blob, path)、それ以外は sha256」の比較器へ替える案は採らない。racy clean と mode 変更の組合せで、現行なら赤の入力を緑にする例と逆の例を段 3 相談が構成し、受理集合が同値にならない (D1709)。
4. active-v2 系の emitter memo 迂回の共有は採らない。実測で 1 本 約 8 秒 × 約 6 本と小さく、key の拡張が既存の key 要素数の golden を動かす。

**理由:**

- 生死確認 (計算ノード) で、T-080 群の 1 本 85〜117 秒の大半は共有 base の構築 (1 回 約 100〜150 秒) の flock 待ちと分けた。先行構築は写しの完成を待ってから始まり構築に約 100 秒かかるので、collection が短い温の木では test 開始に間に合わず、対 2 では T-080 群の所要合計も縮まなかった (2,102 → 2,195 秒)。効果は collection が長い走に限られると読むのが 2 対と整合する (n=1 ずつで確定ではない)。
- 事前登録の条件は結果を見る前に固定しており、片方の対だけの改善で land すると規律 3 の後付けになる。
- 対照の途中で、prewarm が写しを consumer 用の 180 秒上限で待ち、consumer の無い shard を終了処理で赤にする実在欠陥が出た。branch 上で直したが ({{F:prewarm-copied-consumer-timeout}})、land 可否の判定はその修正後の 2 対で行った。

**却下した選択肢:**

- 対 1 の改善だけで land する — 事前登録の L1・L4 に反する。
- collection の長さを条件に land 条件を書き換えて取り直す — 結果を見た後の条件変更になる。条件付きの効果を狙うなら、写しを待たずに構築を始める等の改良と、collection の長さを事前登録した新しい対照を別 wave で行う。
- floor 比較器の置換を「同値」として入れる — 反例が構成されている。受理集合を変えない代案 (11 本を 2 本ずつ xdist group にして process 内 cache を共有) は未評価。
