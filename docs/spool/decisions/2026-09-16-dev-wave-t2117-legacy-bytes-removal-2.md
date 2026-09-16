---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t2117-legacy-bytes-removal
seq: 2
---

## {{D:m2-golden-synthetic-restore}}. 復元不能な歴史 bytes を要求する node は、関数を消さず要求だけを外して合成入力へ戻す

**決定:** 外部保持期限で失われた材料の exact bytes 一致を要求していた
`test_m2_production_golden_requires_both_routes` について、関数を削除も改名もせず、
実 corpus 参照・availability 判定・歴史 golden の SHA-256 assert だけを撤去し、
一時 repo の合成 blob と合成 rollout で production の二経路導出を最後まで走らせる形へ戻す。
あわせて mismatch 拒否の負例を隣に新設する。

歴史 commit 定数 (`BASE_COMMIT` / `INTEGRATED_COMMIT`) は `monkeypatch` で合成 commit へ
差し替える。実 commit を使って合成中間状態への patch を構成する案は採らない。

**理由:**

- 関数を消して別名で作り直すと、変異事前登録・所要台帳・過去の変異台帳が指す node 名が
  すべて宙に浮く。撤去対象は「当時の bytes 一致」であって node の同一性ではない。
- production 差分ゼロのまま、`_compare_golden_routes` の恒真化を殺せる負例が得られる。
  D1367 が残した availability 判定と自己検査はそのまま生きる。
- 実 commit を使う案は、大きな歴史本文への依存と親 repo reader の登録判断を持ち込む。
  小さな 4 状態 (base / authored / golden / integrated) なら各段の寄与を明示でき、
  実 `_git`・別 parser 2 種・SHA 検査をすべて通せる。

**却下した選択肢:**

- 恒久 skip または historical audit への格下げ — 被覆を暗黙に消す。
- 関数を削除して新名の 2 node へ置き換える — node 名の参照が宙に浮く。
- 実データ依存の assert だけを別 test へ切り出す — D1615 が要求外の一般化として却下済み。
- `verify_source_sha` の拒否能力まで新 node で証明する — 撤去で生じた穴ではなく既存の
  被覆限界であり、本 wave の scope を超える。
