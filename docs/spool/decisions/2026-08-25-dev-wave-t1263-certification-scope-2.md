---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1263-certification-scope
seq: 2
---

## {{D:material-report-certification-scope}}. 材料レポートは自分の認証水準を機械可読に宣言し、載る packet の snapshot evidence だけを 1 箇所で検査する

**決定:** A/B 実験装置 (`tools/codex_reasoning_ab.py`) の材料レポートについて次を採る。

1. `verify` / `aggregate` の返値へ `certification_scope` を足し、certified なのは
   `valid` だけであること、adjudication の中間 artifact (packet、packet-state、
   verdict log、verdict freeze、revealed map) は未認証であることを機械可読に宣言する。
   宣言は**公開 API の全 return path**が付ける。集計 helper の返値には付けない。
2. 材料レポートに載る packet の由来 run が snapshot evidence の再走に成功していることを、
   packet と run の join 点 1 箇所でだけ検査する。中間層へ再検証を足さない。
3. 宣言の閉世界主張は、join 点が実際に読む manifest descriptor key を AST で導出して
   突き合わせる検査と**対で**置く。宣言だけを置くことを認めない。
4. run ごとの pre/post evidence 一致を全 run で検査する。同一 oracle identity を共有する
   2 本目以降でも省略しない。

**理由:**
- 論文素材になるのは材料レポートである。全中間層へ再検証を要求すると費用対効果が悪く、
  1 箇所へ置けば裁定が求める性質は満たせる。
- 宣言を private helper へ付けると、helper を直呼びして空の理由集合を渡すだけで
  「宣言付きの合格レポート」を構成できてしまう。認証の主体は公開経路に限る。
- 宣言と実装の食い違いは、この装置がいちばん避けたい事故である。実測でも、最初の実装は
  未認証 artifact の列挙が閉じていないまま `closed_world: true` と主張していた。
  literal 比較だけの検査ではこの型を捕まえられないので、実装から導出した集合と
  突き合わせる形にする。
- 「certified」は既存の用語集では variant が正しさゲートを通った状態を指す。
  レポートの boolean と混同させないため、宣言の主体を field 名で明示する。
- 保証の強さを名前に盛らない。実装が保証するのは凍結 pre/post evidence と replay 時現物の
  再走成功までであって、run 実行時点の歴史的 snapshot の再構成ではない。

**却下した選択肢:**
- 全中間層への再検証追加 — 裁定本文が費用対効果を理由に明示的に却下している。
- join 点でなく replay 側へ検査を置く — その時点ではどの run が材料 packet に載ったかを
  まだ知らないため、裁定の「材料レポートに載る packet だけ」より広い条件になる。
- 集計 helper へ宣言を付ける — 上記のとおり宣言付き合格レポートの構成経路を残す。
- 宣言を literal 一致テストだけで守る — 実装が新しい中間 artifact を読み始めても気付けない。

**この決定が保証しないこと:**
- 中間 CLI (packet 生成、verdict 追記、verdict 凍結、mapping 開示、単独採点) を
  公開経路を通さず直接消費する利用者は保護されない。宣言はそれを未認証と告知するだけである。
- 材料 packet の由来検査は、公開 manifest の受理集合を狭めない。外れる入力は既存の
  snapshot 理由でも必ず拒否されるためである。この検査は、将来 replay 側の再検証や
  evidence の伝達が外れたときに赤くする構造的な固定である。受理集合を実際に狭めるのは
  run ごとの pre/post 検査の方であり、両者を同じ欄に記録してはならない。
- 実験後に snapshot を同じ bytes へ戻す攻撃、および descriptor 検査と後続読取の間の
  競合は本決定の射程外である。
