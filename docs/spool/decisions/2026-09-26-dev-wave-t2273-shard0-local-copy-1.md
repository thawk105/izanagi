---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-26
wave: dev-wave-t2273-shard0-local-copy
seq: 1
---

## {{D:t080-visible-output-lazy-local-copy-not-landed}}. t080 共有 base の可視 output を session 局所の写しから複製する実装は、事前登録の land 条件を満たさなかったので land しない

**決定:**

1. `orchestrator/tests/test_s8b_oracle_driver.py` の共有 base builder の複製元を、xdist session ごとに最初の builder が作る計算ノード局所の写し (`_T080SharedBases.copy_visible_output`) に替える実装 (branch `worktree-t2273-shard0-local-copy`、実装 commit `eb65d322f`) を **local main へ入れない**。branch は残す。
2. 判定は段 4 で事前登録し段 6 で erratum を足した条件どおりに行った。隣接 3 対 (A = main `620a6bb13`、B = A + 実装、順序 A,B / B,A / A,B) の shard-0 W_0 の対差は +19.111 / +19.679 / −4.341 秒、対率中央値 5.2 %。「3 対すべて短縮」と「対率中央値 ≥ 10 %」の両方を外した。
3. 事前登録は「性能改善としての land」だけを定めていた。改善なしの中立な整理として land するかは新しい判断なので、ここでは決めず、次の一手の候補と並べてユーザー裁定へ置く。

**理由:**

- 事前登録を結果を見た後に緩めない (規律 3 の後付け禁止と同じ向き)。
- 第 4 回診断の −123.9 秒は写しを計測前に用意した対照の値で、本実装の形 (最初の builder が Lustre から 1 回作り、他は待つ) の期待値ではないと段 4 で明記していた。診断が示した「複製は待ち支配」と段 3 の反例 (同時 5 本でも copy 30〜35 秒) を合わせると、同時 8 本を直列 1 本 + 待ちに替えても、その 1 本の Lustre 複製が依存 builder に残ることと整合する (実受入に計器が無く、写し生成 1 回の所要は測っていない)。
- 正しさの側 (全件性の検査 2 か所、複製関数本体、受理集合) は不変で、変異 M1〜M5 は全件 KILLED だったので、land しない理由は効果だけである。

**却下した選択肢:**

- 対率 5 % の方向を根拠に land する — D357 の 1 走比較では 3 対とも「変化なし」で、事前登録の閾値を外れている。
- 失敗走 (infra 3 走) を捨てて有効対だけで結論する — 失敗走は分類記録と条件別件数 (A 2、B 1) を insight に残した。どれも本実装の経路外 (queue 待ち超過、collection 時の早期 memo 待ち超過) である。
- 写しの生成時期を collection 中へ前倒しする実装をこの wave で足す — 依頼の scope 外で、効果の見込みを先に測る必要がある。
