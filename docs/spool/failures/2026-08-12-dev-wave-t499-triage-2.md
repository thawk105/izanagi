---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t499-triage
seq: 2
---

## 新規

### {{F:fold-two-fragments-same-task}}. 同一 fold で 2 つの fragment が同じ T を操作すると後着が赤になる — 契約文書に書かれていない [手順漏れ]

- 事象: 兄弟 wave の未 land fragment を cherry-pick で相乗りさせる wave で、その fragment が
  `更新` している項を自 wave が `見送り` へ落とそうとした。fold は fragment を `(wave, seq)` 順に
  適用して active 集合を逐次更新するため、先に当たった側が項を active から外し、
  後着の操作が `transition-target: active でない操作対象` で停止する。適用順は **wave slug の
  辞書順**で決まるので、どちらが先かは wave の命名という無関係な事情に依存する。
- 根本原因: `docs/spool/README.md` と `docs/spool/worklog/README.md` は 1 fragment 内の文法と
  fold の producer 契約だけを書いており、**複数 fragment の合成規則** (同じ T を 2 度操作できない、
  順序は wave slug 順) を書いていない。本件は親が `tools/spool_fold.py` の
  `_render_next_actions` を読んで初めて気付いた。書式検査 (`tools/check_docs.py`) は
  1 fragment ずつ見るため赤にならず、`--dry-run` まで進んで初めて出る。
- 恒久対応: memory `sibling-fragment-carry-by-cherry-pick` へ「相乗りさせた fragment が操作する
  T と自 wave の操作対象が交差してはならない。交差したら相乗り側の該当 block を外す」を追記する。
  併せて、相乗りを含む wave では land 前に `python3 tools/spool_fold.py --dry-run` を必ず走らせる
  (memory `fold-dryrun-before-acceptance` の既存義務が本件も覆う)。
- 再発検知: `--dry-run` の rc。交差があれば `transition-target` で非 0 になる。
  本 wave では 13 項の `更新` block を外したうえで rc=0 を実測した。
