---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-02
wave: dev-wave-t2067-oracle-manifest-selection
seq: 2
---

## {{D:historical-reverify-skips-selection}}. historical reverify は選択 identity を実行しない

**決定:** `reverify_published_freeze` を呼ぶ consumer を「床値選択規則が強制済み」と扱わない。
選択 identity の再強制が要る load-only consumer の母集合は、`load_ratified_freeze` だけを
呼ぶ入口に限らず、`reverify_published_freeze` を経由する入口も含めて数え直す。

**理由:**

- `_launch_validate` の選択 identity 検査は `result_type is LaunchValidatedFreeze` の条件下に
  ある。`reverify_published_freeze` は `result_type=ReverifiedFreeze` を渡すため、
  historical reverify では選択検査が実行されない。
- 既存 test がこの挙動を固定している。earlier result を足したまま reverify が成功することを
  明示的に assert する node が landed 済みで在る。D1312 が定めた「loader と historical へ
  current policy を持ち込まない」境界の帰結であり、欠陥ではなく設計である。
- したがって「reverify を通るから被覆済み」という推論は成り立たない。本 wave の親 brief は
  この推論で 3 consumer を scope 外にしており、段 3 の 2 レンズが独立に反証し、親が
  一次資料で追認して撤回した。

**却下した選択肢:**

- `reverify_published_freeze` 自体へ選択検査を足す — historical reverify が recorded semantics を
  選ぶ前に current policy で落ちる。D1312 が却下済みの形と同じになる。
- 被覆済みという当初の整理を保ったまま進む — 事実に反する母集合の上で残余を数えることになる。

## {{D:selection-gate-test-following-keeps-g1}}. 選択 gate を足す consumer test は g1 のまま記録 stub で追随させる

**決定:** 静的 loader だけを通る consumer へ D1370 の狭い API を足すとき、その consumer の
既存 test が合成 g1 fixture を使っているなら、**fixture の generation_number を 2 へ移さない。**
合成 g1 のまま残し、選択 assert だけを「呼出しを記録して何もしない stub」へ差し替えて、
各 test に呼出し回数と引数を検査させる。機構そのものの証明は、実 loader と実 callee を通す
genuine g1 の正例と負例に担わせる。

**理由:**

- 合成 fixture は v1 文書へ floor と budget を足しただけで、実 loader が要求する v2 exact schema、
  本文の世代番号、世代連鎖、approval pairing を通らない。dataclass の generation_number だけを
  2 にすると、実 loader では決して成立しない受理集合を test 上に作る。
- manifest 構築は generation_number から freeze の記録 path 文字列を組み立てて成果物へ焼き込む。
  g2 化は成果物の参照文字列そのものを変える。
- 既存 test を g2 へ移すと、g1 が gate 通過後に manifest を最後まで構築して再検証される
  成功被覆が消える。狭い API は非 g1 では何も観測せずに返るため、g2 fixture では
  引数の取り違えを検出する変異が殺せない。
- 記録 stub は緑を作るための細工ではなく、gate が呼ばれた事実と引数を固定する検査点である。
  実測では、gate 削除・引数の取り違え・root の取り違え・gate の位置移動のいずれもこの
  呼出し記録が検出した。

**却下した選択肢:**

- 既存 test の fixture を g2 にする — 上記のとおり実在しない受理集合を作り、被覆を失う。
- loader と選択 assert の両方を stub する — 機構を一度も通らない緑になる。
- production へ test 時だけ検査を飛ばす分岐を入れる — 正しさゲートの弱体化であり D1371 が
  名指しで却下している。
