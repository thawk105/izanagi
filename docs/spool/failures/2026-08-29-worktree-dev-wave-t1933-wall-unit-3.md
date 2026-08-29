---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-29
wave: worktree-dev-wave-t1933-wall-unit
seq: 3
---

## 新規

### {{F:bound-direction-unchecked}}. 導出していない境界の向きを、結論を否定する含意として使った [捏造/幻覚] [計測汚染]

- 事象: 受入 wall の律速同定で、親が境界の向きを 2 箇所で取り違えた。
  1. `wall − max_occ` を「全 worker がテストを走らせていない時間の**下限**」と brief と
     measurements へ書いた。実際は**上界**である。`tools/acceptance_shards.py` の
     `worker_occupancy` は phase の duration を node ごとに加算するだけで、全 worker の phase
     区間の和集合は必ず max_occ 以上になる。`orchestrator/tests/conftest.py` の real-repo lock 待ちが
     `yield` の外側にあることも見ていなかった。
  2. 反実仮想の LPT 詰め直しについて「LPT は最適 makespan の近似なので、実 scheduler の
     makespan はこれ以上になる。したがって LPT でも縮まないなら実 scheduler でも縮まない」と書いた。
     LPT makespan は実行可能解であって下界ではなく、xdist の動的補充 scheduler との大小関係は
     定まらない。段 3 の 2 レンズが独立に同じ反例を構成した。
  どちらも「単一処理は wall を決めていない」という結論の**主根拠**として使っていた。
  結論自体は `makespan >= 最長 unit の所要` という定理へ置き換えて維持できたが、
  置き換えるまでの根拠は誤りだった。
- 根本原因: 不等号の向きを一度も導出せず、直観の言い換えで進めた。1 は
  「差分だから下限だろう」、2 は「近似アルゴリズムだから下界だろう」という語感である。
  どちらも 2 行の導出で判定できた。数値の母集合を確かめる規律 (F473) は数値には効いたが、
  **数値ではなく関係の向き**には発火していない。
- 恒久対応: memory `bound-direction-must-be-derived-not-assumed`
  (上界・下界・単調性・含意の向きを結論の根拠に使うときは、値を出す前にその向きを 2 行で導出して
  併記する。導出できないなら向きに依存しない量へ言い換える)。
  本件では `wall − max_occ` を上界と明示し、反実仮想を
  `makespan >= 最長 unit` という向きの要らない定理へ置き換えた。
- 再発検知: 敵対レビューのレンズに「親が使った不等号・含意それぞれについて、
  向きの導出が本文にあるかを確かめ、無ければ反例を構成する」を含める。
  本 wave では段 3 の両レンズが実際にこの検査で 2 件とも検出した。

## 再発

### F473

- **再発: 2026-08-29** — 受入 wall の律速同定で、親が `collections.Counter` の
  `most_common(8)` 出力をそのまま「最 busy worker の item 数分布」として引用した。
  484 走のうち 209 走しか写っておらず、実際の分布は中央値 72 の二峰性で、
  「2〜5 node」が成り立つのは K=3 の直近 117 走に限られていた。段 3 レンズが
  「合計は 209 で 275 走が未記載」と指摘し、全件列挙で確認して訂正した。
  同じ走で universe 件数を `login-collection.log` の行数 18,954 と取り違え
  (実際は `observed_universe` の 18,895)、collection 回数から login collection 1 回を落として
  144 回と書いた。いずれも母集合と除外を 1 行で言わずに数値を出した F473 の型である。
  F473 の恒久対応 (memory `tool-filtered-view-is-not-the-total`) を変更しない。
