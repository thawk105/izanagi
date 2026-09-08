---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-09
wave: dev-wave-t2418-static-backoff-explore
seq: 3
---

## 再発

### F902

- **再発: 2026-09-09** — **新規 test file を足していない wave でも同じ赤が出る。** 既存
  `orchestrator/tests/test_backoff_extended_sweep.py` へ 8 node 足しただけで、被覆は
  19935 / 22155 = 89.979689% となり閾値を割った。8 node を除いた反実仮想は
  19935 / 22147 = 90.012191% で、main 側の余裕は 1 node 未満のままだった。
  是正で二次の罠も再現した — 台帳を正本 producer で更新して commit した直後に、
  **別 wave が同一の add-only 更新 (2081 node、`2fd1679dd`) を main へ着地させ**、受入の
  merge guard が `stage=owned-path-overlap` で走行前に停止した。自分の更新を残したまま
  main を取り込むと 3-way merge が 56 か所衝突する (`git merge-file` で実測)。
  **本 wave は自分の台帳 commit を取り下げて抜けた** — main 側の台帳は 22123 node へ更新済みで
  被覆は約 99.9%、自分の 8 node が未登録でも閾値を大きく上回るため、登録は次に台帳を触る wave へ
  委ねられる。合成 merge より安く、閾値も一切下げない。この抜け方が使えるのは
  **main 側の被覆に余裕がある場合だけ**で、余裕が 1 node 未満のときは F902 の恒久対応どおり
  producer による合成が要る。判定は受入 1 回目の被覆分数を反実仮想と突き合わせて行う。
