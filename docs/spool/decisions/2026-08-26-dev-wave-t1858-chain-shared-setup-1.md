---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t1858-chain-shared-setup
seq: 1
---

## {{D:shared-head-eval-not-tautological}}. snapshot 比較の右辺は fixture の HEAD 評価と共有してよい

**決定:** `test_current_repository_snapshot_exactly_matches_head` は、比較の右辺として
module fixture が path 発見のために実行した実 HEAD 評価の結果をそのまま使う。
比較の左辺 (一時 repository での独立評価) は現行どおり再導出する。
共有によって失われる「走行中に実 HEAD が動いた」場合の検出は、fixture が記録した OID と
assert 直前の HEAD OID を突き合わせる純関数の gate で補う。

**理由:**

- D747 が禁じたのは「両側を共有値にすること」による恒真化である。左辺は別 repository・別 commit で
  独立に再導出されるため、片側だけの共有は恒真化しない。段 3 の 2 レンズが独立に同じ判定を出した。
- 2 回目の評価だけが殺す production 実装の変異は書けない。評価器は commit を呼出し冒頭で一度解決し、
  raw / AST / binding / graph の cache をすべて呼出しローカルに作る。時刻・乱数・並行読取の
  非決定源も無い。
- 変異 matrix で裏取りした。evidence ref を記録しない変異の kill 集合は、共有前 (main) と共有後で
  **完全に一致**し、共有後も同 test が殺している。
- 代償は焦点鎖で 15.29 秒であり、鎖の 3 分の 1 に当たる。

**限界:** 受理集合は前後で同一ではない。**新実装の拒否集合の方が広い。** 旧実装が比較したのは
評価結果の tuple だけなので、HEAD が動いても結果が同じなら通っていた。新 gate は結果が同じ
OID 変化も拒否する。安定した checkout ではこの差は発火しない。

**却下した選択肢:**

- 据え置き (段 2 のプラン) — 依頼の「2 鎖に同じ手を当てる」を満たさず、失う検出力を具体的な
  変異として示せなかった。
- 静的な `evidence_paths` 宣言で path 発見評価を代替する — 実 evidence refs は reachability が
  動的に読んだ import dependency も含むため、静的集合では snapshot の tree が縮んで
  reason code を変える。
- gate を置かずに共有だけする — 失う検出力を補わないまま受理集合を広げることになる。

## {{D:head-bound-ops-need-one-resolved-oid}}. 実 HEAD を読む補助検査は解決済み OID へ束縛する

**決定:** テストの補助検査が実 repository の HEAD を複数の操作 (述語評価・`ls-tree`・`archive`・
記録用の `rev-parse`) で読むときは、`HEAD` という symbolic な名前を各操作へ渡さず、
一度解決した OID を全操作へ明示的に渡す。

**理由:**

- 各操作が独立に `HEAD` を再解決すると、記録した OID・評価結果・snapshot が別 commit 由来に
  なりうる。この不整合は OID 比較の gate では検出できず、逆に一貫した走行を誤って拒否しうる。
- `rev-parse` を評価の後ろへ動かすだけでは原子的にならない。束縛の単位は「解決した値を渡すこと」
  であって「読む順番」ではない。
- 段 6 の敵対レビューが実装差分からこの欠陥を検出した。静的レビューでしか出ない型であり、
  安定した checkout ではテストが緑のまま通り抜ける。

**却下した選択肢:**

- `rev-parse` を評価直後へ移す — 上記のとおり原子的でない。
- gate を諦める — 共有によって失う検出力を補えなくなる。
