# [T-2797] 依頼の逐語 (dev-wave 引数、2026-09-20)

以下は `/dev-wave` の引数をそのまま写したもの (改行は原文の折返し位置)。

```
[T-2797] (P2、D2172 項 4 段階裁定 (A)、共有 3 部品は entry 1746 / D2183 で main に着地済み) B-5 生成器対照の (α) 残部品の段階実装 →
  (β) launcher 設計と上限付き試走を 1 wave で、内部を段階化して進める。着手直前の local main から fresh worktree。起動時に稼働中の
  `dev-wave-t2795-k2-pair` の merge-base 差分を再照合し、`orchestrator/campaign/p3_s4_loop.py`・`tools/pegasus/p3_s4_loop_pegasus.sh`
  に差分が出ていればその着地を待つ (19:06 時点は 0 file)。(α) = `docs/b5-generator-contrast-preregistration.md` §10 の「実装が要る」残部品
  (系列開始 stock の planner 前配置、session 契約の flag 束縛と品質欠測の分類、B/A 台帳と収束停止の不適用、重複の fresh 評価、random
  生成器、sweep の hash 順 B 点、解析 consumer、較正・verify の job body 配線) を Codex author (D95) で段階実装、各単位に正例・負例の変異。(β)
  = D2172 項 4 の上限を逐語で守る: 1 workload (verifier 所要が最短、read-heavy を避ける)・3 arm × 1 系列・B = 10 評価 + 系列開始 stock 1 +
  endpoint 再計測 5 = 16 session / arm・block stock 5・合計 60 論理 session 以下・retry は §3
  どおり・結果は主標本に入れず既知結果台帳へ、verifier wall (3 秒 × 5 rep + verifier) を実測して残す。本走は未認可のまま — (γ) 2 の残部・4
  (費用上限)・6 (対象 commit) は試走後の裁定パッケージで再提示し、発効 commit は作らない。K0 arm・本走・「LLM が必要と実証した」の記述は scope
  外、規律 2 を緩めない。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
```

再照合の実測 (19:10 JST): `dev-wave-t2795-k2-pair` の HEAD は local main `6a3e15809` そのもの (merge-base 差分 0 commit)、
対象 2 file の未 commit 差分 0 file。待たずに着手した。
