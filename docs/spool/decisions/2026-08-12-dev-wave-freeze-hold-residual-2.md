---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-freeze-hold-residual
seq: 2
---

## {{D:hold-inventory-declares-its-own-incompleteness}}. 保留の統合一覧は完全性を名乗らず、登録済み層の snapshot と自己申告する

**決定:** 恒久保留を横断して読む統合 inventory (`tools/hold_inventory.py`) は、
**未知の保留層を自動発見しない**ことを機械可読に自己申告する。
`completeness` field を `"registered-layers-only"` に固定し、見出し・docstring・human 出力にも
同じ制限を書く。契約テストは「完全性を主張する文言が出力に無い」ことを**禁止語の羅列ではなく
構造**で検査する — human は独立な期待 line sequence との exact 比較、JSON は top-level と
全 nested object の key 集合の exact 固定とし、source から導けない値はメタテスト側の
canonical literal で固定する。

また、保留状態は次の 3 つを分けて出す。

- `configured_status` — 台帳がどう定義しているか
- `effective_status` — 今この環境・この runner で実際に保留されるか
- `bypass_surface` — 保留を迂回しうる経路 (未解決のものは未解決と明示する)

**理由:**
- 敵対レビュー 2 本が独立に「source を import して source と比べる契約では、
  新しい保留層が増えた壊れ方は原理的に捕まらない」と示した。捕まえられない保証を
  名乗ると、利用者は不完全な一覧を完全版として参照する。
- 一方のレビューは**禁止語に当たらない完全性主張文を実際に書いて素通りを実証**した。
  blacklist は保証手段にならない。構造で縛るしかない。
- 恒久保留の解除がユーザーの明示命令のみである以上、「今なにが止まっているか」の一覧は
  ユーザーの判断入力そのものである。**嘘をつくくらいなら範囲を狭く名乗る方が正直で、
  範囲を広げるときも機械的に検査できる。**
- `effective_status` を無条件に `held` と出すと嘘になる経路が実在する
  (素の runner、`--noconftest`、suite 下を指す `--confcutdir`、test 関数の直接呼び出し、
  `PYTEST_ADDOPTS` transport)。前提を書かずに status だけ出してはならない。

**却下した選択肢:**
- 全 hold provider に登録を強制する canonical provider registry を新設する — 未登録機構を
  拒否できる唯一の形だが、production 側の機構すべてに登録義務を課す横断変更になる。
  保留一覧という読み取り専用の目的に対して過大で、本 wave の scope を超える。
- 禁止語 blacklist だけで過剰保証を防ぐ — 回避文言が実際に書けることを実証済み。
- 完全性を名乗って運用で担保する — 保証の主体が機械でなくなる。
