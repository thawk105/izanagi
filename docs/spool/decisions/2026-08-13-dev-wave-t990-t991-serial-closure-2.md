---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-13
wave: dev-wave-t990-t991-serial-closure
seq: 2
---

## {{D:closure-detector-design}}. 正本リストと実資源接触の対応は、閉包条件と実行時 guard で確かめる — 静的 AST 解析は採らない

**決定:** 「正本リストに実資源接触 node が漏れていないか」を機械で確かめる検査は、次の 2 本立てとする。

1. **共有 fixture 閉包の完全性** — 正本に載っている node が使う共有 fixture (function scope を除き、
   repo 由来の baseid を持つもの) の consumer は、すべて正本に載っていなければならない。
   既存の collection subprocess の report を拡張して検査し、新しい subprocess を足さない。
   **実資源 fixture の登録簿を人が書かない。正本自身が seed である。**
2. **実接触の runtime fail-closed guard** — 実共有 submodule が `patchharness.checkout()` へ
   渡されたとき、pytest 中でありながら呼び出し元 node が正本の印を持たなければ停止する。
   判定は path 文字列でなく Git repository identity (`--git-common-dir` と `(st_dev, st_ino)`)
   で行う。pytest 外では発火せず production の受理集合を変えない。

**既知 gap を明示的に受け入れる:** どの node も正本に載っていない**全く新しい共有 fixture**は、
seed が無いため (1) では発見できない。(2) が call 経路の一部を埋めるが、両者の外は残る。

**理由:**

- 静的 AST の固定点解析案 (test/campaign/tools 配下 425 file・15.677 MB を parse) は
  D335 (authority: user)「repository の成長 (履歴・commit 数・file 数・台帳やアーカイブの分量) に
  比例して実行コストが増えるテストは新設しない」に正面から該当する。D311 も新設検査のコストが
  O(履歴) なら設計をやり直すことを要求する。
- **より重い理由は、その案が現実の欠陥を実際に取り逃していたことである。** 提案時点の control は
  一方の module の alias しか撃たないため、`prepare_fn=` で callable を渡し re-export alias を
  経由する実経路を検出できなかった。伝播規則を 1 本落とすだけで系統が丸ごと消える構造だった。
- 実行時 guard は実接触そのものを見るため、module alias・keyword callable・wrapper forwarding・
  function-local import のどれを経由しても捕まる。**AST の伝播完全性という問題が原理的に消える。**
- 閉包条件は登録簿を持たないので drift しない。コストは collected item 数に比例し、
  repository の成長には比例しない。

**却下した選択肢:**

- **AST 固定点解析** — 上記のとおり成長比例かつ取りこぼしが実証された。
- **実資源 fixture の手書き登録簿** — 新 fixture の追加・rename で drift する。
  登録簿を守る検査を足しても、未登録の構文体系の不存在は証明できない。
- **全 node の実行時トレース** (`open` / `subprocess` の観測) — skip を含む接触集合を得るには
  全 node の setup/call を走らせる必要があり、受入全走のコストを大きく増やす。
  同一 run で観測を混ぜる形は観測者効果の分離 (絶対規律 1) にも触れる。

## {{D:internal-stamp-not-public-channel}}. pytest item への内部印は公開チャネルへ載せない

**決定:** wave が pytest の collection hook で item へ付ける内部用の印は、`item.user_properties`
のような公開チャネルへ載せず、非公開属性へ置く。`user_properties` は pytest 標準の報告チャネルで
JUnit XML へ流れ、既存の契約テストが完全一致を要求しうる。

**理由:**

- 実測。当 wave が `item.user_properties` へ内部印を 1 個足したところ、別 wave が land した
  growth-test hold の契約テストが `dict(item.user_properties)` の完全一致を要求しており、
  受入全走で赤になった。対象 node は保留対象と実 repo 直列の**両方**に属していた。
- 公開チャネルは「誰でも足してよい」ようでいて、完全一致を要求する consumer が付くと
  実質的に排他になる。内部印は非公開属性にすれば、この結合が最初から生じない。

**却下した選択肢:**

- **契約テスト側の期待値を増やす** — 既存テストの期待値を変えない規律に反し、
  かつ「公開チャネルへ内部印を載せる」設計自体は残るので同型の衝突が再発する。
- **`item.stash` を使う** — pytest の型付き stash は適切な選択肢だが、`StashKey` を
  conftest と注入 plugin の双方から同一 object として見せる必要がある。
  非公開属性で足りる範囲では属性を既定とする。
