---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-30
wave: dev-wave-acceptance-pyc-warm
seq: 2
---

## {{D:login-collection-prestart-not-landed}}. 受入 shard mode で login collection を preflight 前に前倒しする実装は、同時刻対照 2 対が待ち行列の長さで事前登録の適格条件を満たさず判定不能なので main へ入れない。shard に login collection を待たせる案と、計算ノードに pyc を書かせる案も採らない

**決定:**

1. md_7 (初回受入でも shard 開始前に bytecode cache をそろえる) として、`tools/run_tests.py` の shard 経路で submodule marker が有効なときだけ、未 stage 削除検査・RuleOps などの preflight より前に login collection を subprocess として起動し、`acceptance_shards.run_parallel` の `collect_login` をその回収にする実装を作ったが、**main へは入れない**。実装は branch `worktree-dev-wave-acceptance-pyc-warm` (tip f4920ddb3、Codex author) に残す。
2. 判定は段 4 で事前登録した land 条件どおり: 適格な対 (6 shard すべての待ち行列が 60 秒以内) が 2 つ必要なところ 0 だった。対 1 は K の 1 shard が 78 秒、対 2 は 6 shard 中 4 shard が 128〜484 秒。
3. 観測 (判定外): 対 1 で shard pre 中央値が K 93.0 秒 → H 69.0 秒 (24.0 秒短縮)、対 2 は待ち行列が長く両腕とも温の峰 (69.2 / 69.6 秒)。害検査 (preflight 区間が延びない、login universe と observed universe の一致 28,663 件、終了後の作業木 clean) は両対で成立。
4. 依頼の択一のうち、shard が login collection の完了を待つ案は採らない。計算ノードの job は投入の約 9 秒後に始まり、冷の login collection は投入意図から 85〜108 秒かかるので、待ちが得を上回る。計算ノード worker に pyc を書かせる案は D918 のとおり採らない (初回受入では 48 worker が同時に冷で collection するので効かない)。

**理由:**

- 事前登録の条件は結果を見る前に固定しており、対 1 だけの改善で land すると規律 3 の後付けになる。land 調整役の GO の条件も「事前登録の判定を後から変えない」だった。
- land すれば `tools/run_tests.py` の blob が変わり、走行中の全 wave が受入をやり直す (D987)。得られるのは、初回受入で待ち行列が短いときだけの shard あたり約 24 秒 (n = 1 対の観測) である。
- md_2 の区間分解 (投入意図起点) は `run_tests.py` 起動から投入意図までの 56〜102 秒を含んでおらず、その大半は login の git 検査 (`git ls-files --deleted` 34〜89 秒) だった。前倒しはこの区間に collection を重ねる形で、対 1・対 2 とも H の collection は shard の開始前後に完了した (投入意図の 33 秒後 / 9 秒後)。

**却下した選択肢:**

- 対 1 の改善だけで land する — 事前登録に反する。
- 適格条件 (60 秒) を緩めて取り直す — 結果を見た後の条件変更になる。再訪するなら、対の数と判定の規則 (例: 3 対以上、適格な対の多数決) を先に登録した新しい対照を別 wave で行い、D987 の再受入費用と比べて決める。
- 前倒し子を自前の signal handler と新 process group で管理する — 段 6 レビューが起動直後と後始末中の窓・reap 済み pid への signal・終了形式の変化を示した。branch の実装は従来の `subprocess.run` と同じ意味論に戻してある。
