---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-01
wave: dev-wave-t2076-t493-sort-oracle-parent-reference
seq: 1
---

## {{D:sort-oracle-relation-provenance-has-no-minimal-fix}}. D1271 の基準 snapshot は既に不在で、残る関係行列の出所は最小実装では閉じない

**決定 (裁定パッケージ・ユーザー裁定待ち):** D1271 が命じた「sort SWO oracle の基準 snapshot を
候補 comparator から不可視な親側へ移す最小実装」は、**本 wave では実装しない。**
新事実を添えてユーザー再裁定へ返す。

**着手前実測で覆った前提:**

- D1271 と D696 が exact に名指しした `trusted_snapshot` / `snapshot_corpus()` は現行実装に存在しない。
  実装側の全件検索で hit 0 件、`orchestrator/tests/test_sort_swo_oracle.py` は
  `assert "trusted_snapshot" not in source` という否定 assert を持つ。
- 撤去したのは T-1574 の実装で、corpus を read-only arena と seccomp で守る方式へ置換した。
  **その着地は D1271 の起票日より前である。** D825 はこれを「保証するもの」に入れている。
- したがって D1271 の literal な実装対象は存在しない。

**生きている穴と、それが D1271 の対象でないこと:**

- 残るのは D825 が「保証しないもの」として exact field に固定した関係行列の出所である。
  候補 comparator の lambda 本体は外形検査だけを受け、観測 fd も候補が所有するため、
  **各 corpus について comparator の真の関係と無関係な任意の SWO 行列を報告させうる。**
- 独立レンズの検証は、これを D1271 の対象 (corpus 変異検出) からの拡大と判定した。
  親も同判定を採る。

**3 案がいずれも不成立であること (本 wave の実測):**

- 比較ごとの内容 witness を観測 fd へ出す案 — 候補が同じ fd の所有者である限り出所を作れない。
- broker が trap で引数と戻り値を採取する案 — trap も trusted callsite も候補と同じ翻訳単位にあり、
  呼出しの出所を証明しない。隠蔽を防壁に数えない原則にも反する。
- 比較ごとに `fork()` して子で評価する案 — 候補文の引数評価が worker 親で起きるうえ、
  現行 seccomp は `clone` / `wait4` を許さず、filter は候補文より前に導入済みで積み増ししか
  できない。fork を通すには候補にも適用される filter を緩める必要がある。

**成立しうるのは受理言語を検証済み IR へ縮め trusted interpreter で評価する案だけ**であり、
これは受理集合と合成エージェントのインタフェースを変える大きな設計変更である。
「最小実装」でも「本題の実装だけ」でもないため、親は独断で採らない。

**却下した選択肢:**

- 非保証のまま運用を続ける — D1271 が既に却下しているが、前提が変わったので選択肢として残す。
- 親の判断で大きい再設計へ進む — 受理集合と合成エージェントのインタフェースを変える設計変更を
  実装 wave で既成事実にしない。

## {{D:sort-authority-lands-alone-when-bundling-premise-is-void}}. 束ね条項の前提が消えたので権威集合を単独で入れる

**決定 (親の判断。ユーザー裁定ではない):** D1271 は sort comparator の権威集合を
基準 snapshot の実装と**同じ変更単位**で行うことを求め、その理由を「別々にすると受入枠を
2 回消費する」と書いている。基準 snapshot 側に実装が無い以上、**束ねて節約できる枠が存在しない**。
よって条項は充足不能とし、権威集合を単独で実装して land する。

**理由:**

- 権威集合の実装は受理集合を**狭める**方向であり、規律 2 と整合する。可逆でもある。
- 単独 land が使う受入枠は 1 回で、これは実行可能な最小値である。
- 基準 snapshot 側は再裁定を要し、どの案を採っても大きい設計変更として独自の wave を要する。
  したがって枠が 2 回に分かれること自体は、束ねるか否かにかかわらず避けられない。

**却下した選択肢:**

- 両方を止めて何も land しない — 実装可能で承認済みの防壁を、充足不能な条項のために保留する。
- 親の判断で基準 snapshot 側も実装する — 上記 D のとおり最小実装が存在しない。

## {{D:sort-comparator-authority-mirrors-trigger-exactly}}. sort の権威集合は exact binding 一本で trigger 軸の鏡像にする

**決定:** `sort_best.comparator` の権威集合は、候補空間の 15 組から機械導出した
**name と comparator の exact binding 一本**で実装する。独立した membership 述語、
公開 mapping、stock 特例は作らない。束縛は trigger 軸と同じく**生成側と検証側の両方**へ入れる。

**理由:**

- membership は exact binding に受理判定上包含される。集合外の comparator は、その name に
  対応する正準値との一致検査でも必ず拒否される。独立の述語を置くと変異の単一理由性が壊れ、
  実効 gate がどちらか分からなくなる。
- stock は実 freeze の `stock_common` に name も comparator も持たない。対応する artifact が
  無い特例を作ると、発火しない条件付き機能になる。
- trigger 軸は生成側と検証側の両方で検査している。片側だけでは、生成時に正しくても保存済み
  文書の改竄を検出できず、逆もまた真である。

**却下した選択肢:**

- comparator literal を権威 module へ再掲する — 候補空間と二重管理になり drift する。
- 検証側だけに入れる — 生成経路が権威集合外の値を書けてしまう。
- 束縛 module 自身を凍結 source closure へ pin する — trigger 軸も束縛実装を pin していない。
  sort 側だけ足すと、この決定が消そうとした非対称を逆向きに作る。両軸を 1 つの変更単位で
  pin する課題として分離する。
