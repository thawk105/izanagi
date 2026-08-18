---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-18
wave: dev-wave-t1363-c06-budget-consumer
seq: 2
---

## {{D:staged-evaluator-registry}}. 8c 条件評価器の段階登録は production dispatch へ載せない

**決定:** 契約 `machine_checkable` が false のままの条件について評価器を先行実装するとき、
その評価器は module 定数 `_STAGED_EVALUATORS` へ置き、`PredicateRegistry.evaluate_all` の
dispatch からは参照しない。テストは `_MACHINE_EVALUATORS` を monkeypatch し、tmp 契約で当該条件の
`machine_checkable` を true にして end-to-end で通す。昇格は契約 1 bit、registry 1 行、
`DECIDER_VERSION` bump、その版を持つ次世代 record の 4 点を**同一変更単位**で動かすときだけ行う。

**理由:**
- 契約 JSON の `machine_checkable` と `_MACHINE_EVALUATORS` は双射で機械 pin されており、
  片方だけ動かすと既存テストが赤になる。評価器の先行実装は、この pin を壊さずに行う必要がある。
- production dispatch が staged map を参照すると、**契約 blob を 1 bit 変えるだけ**で当該条件の
  受理・拒否理由が `DECIDER_VERSION` と凍結 record の管理外で変わりうる。
  現行の「評価器の無い条件を machine_checkable にしたら実行時エラーで倒れる」は fail-closed であり、
  こちらを維持する方が安全である。
- 段階登録は門を回り込む口ではない。門 (`machine_checkable` false) は閉じたままで、
  評価器は門の内側に置かれるのを待つ部品として実装・試験されるだけである。

**却下した選択肢:**
- `_MACHINE_DISPATCH = {**_MACHINE_EVALUATORS, **_STAGED_EVALUATORS}` を dispatch が参照する形 —
  上記のとおり契約 blob 単独で受理集合が広がる経路を作る。
- 評価器を定義するだけでテストから直接 probe を組み立てる形 — end-to-end の dispatch 経路を
  1 度も通らないため、昇格時に初めて発覚する欠陥を残す。
- 契約と registry を同時に反転して即座に機械検査対象へ載せる形 — 凍結世代の発行を伴うため、
  同じ評価器面を触る並行 wave と世代が衝突する。世代の衝突は merge では解けない。
