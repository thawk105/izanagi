---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2198-trace0-fetchcontent
seq: 3
---

## 新規

### {{F:hidden-negative-behind-adjacent-check}}. 新設した検査 3 本が隣接する別の検査に隠れ、テストに固定されていなかった [テスト代表性] [恒真ゲート]

- 事象: A-2 / A-6 の trace0 文法拡張で新設した検査のうち 3 本が、変異走行の probe 巡で
  **どのテストにも殺されなかった** (SURVIVED)。段 6 の敵対レビュー 2 本は静的検査でこれを
  1 件も指摘できなかった。負例テスト自体は存在していたのに、いずれも別の検査に先に拒否されて
  対象の検査へ届いていなかった。
- 根本原因: 負例が「その検査だけを撃つ」形になっていなかった。3 件とも隣接する検査が同じ入力を
  先に拒否する。(1) path token の非空検査 — 値が空の FetchContent token は直後の正規絶対 path 判定が
  拒否するため隠れる。判定を持たないのは dependency prefix (先頭 1 本) だけで、その空値の負例が
  無かった。(2) path token の prefix 一致検査 — 期待値が受け取った token をそのまま写す構造のため、
  最終の全一致比較でも捕まらない。統制 define の抽出器も対象外の接頭辞しか見ない。「位置は正しいが
  prefix が違い、値は正規絶対 path」という負例が無かった。(3) policy の要素数検査 — 既存の負例が
  3 要素だったため要素の重複を見る一意性検査にも掛かって隠れる。長さ検査だけを撃つには
  「5 要素でうち 1 つが重複」(集合サイズは 4) が要る。
- 恒久対応: `docs/dev-wave/mutation.md` の `DW-M01` (単一理由性) と `DW-M02` (所見ゼロの裏取り) の
  fails-closed 適用。**新設検査には、その検査の項だけを一時的に落として当該負例が赤になることを
  実測してから登録する。** 本 wave では 3 件すべてでこの実測を行い、復元後に production 差分ゼロを
  確認した (`output/insights/2026-09-07_t2198-trace0-fetchcontent/verbatim/s6-fix2.md`)。
- 再発検知: 変異走行の SURVIVED。静的レビューでは検出できないことが本件で実証された
  (敵対レビュー 2 本がいずれも見落とした)。`DW-M02` の「変異が生存したらまず他層の mask と
  等価変異を疑う」が発火点である。

## supersede 追記

- F808 **supersede: 2026-09-07** — 根本原因節の「`run_campaign` は FetchContent の source dir を受け取る引数を持たない」は現行 main では偽である。`orchestrator/campaign/loop.py` の `run_campaign` は 5 引数すべてを持ち `pipeline.evaluate` 経由で `buildcache` へ素通ししており、T-2356 の commit `466528512` で着地している。残っていたのは認証経路の呼び手が 5 引数を渡していないことと、閉じた trace0 argv 文法が FetchContent token を拒否することの 2 点で、いずれも D1693 と {{D:certification-third-party-input-is-hydrate-layout}} の実装で解消した。
