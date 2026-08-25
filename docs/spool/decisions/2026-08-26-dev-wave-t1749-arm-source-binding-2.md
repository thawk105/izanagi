---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t1749-arm-source-binding
seq: 2
---

## {{D:proof-kind-names-the-actual-reach}}. 証明の種別は届いた範囲そのもので命名する

**決定:** 受領証へ「独立に再導出した」と記録してよいのは、consumer が権威 bytes から計算し直した
値だけとする (D920)。加えて、**再導出が届いた範囲を種別名そのものに書く**。宣言 arm と実 source の
関連付けは、materialize された文字列が実体に在ることまでしか示せないので
`consumer-rederived-textual-materialization` と名付け、`consumer-rederived` とは書かない。
走行側が書いた値どうしの照合は `producer-self-consistency`、producer の実行時契約に依存する辺は
`producer-execution-contract` として別 field に分ける。

**理由:**
- 受入の時点に checkout も compiler も無いため、宣言した述語が**実行される**ことは consumer 単独で
  閉じない。閉じない部分を閉じたと書けば、下流がその「完了状態」を参照して構築し、
  恒真な保証が伝播する。これは規律 2 が禁じる型である。
- 種別を 1 語にまとめると、届いた範囲の違いが名前から消える。名前が実態より強いと、
  後続は名前だけを見て判断する。

**却下した選択肢:**
- 単一の `consumer-rederived` で通す — 実行到達性まで再導出したと読め、実態より強い。
- 関連付け自体を実装しない — 宣言と実体が別物の束を受理し続けることになり、閉じるべき欠落が残る。

## {{D:acceptance-gates-stay-outside-the-enforcement-closure}}. 受入 gate の実装は強制ソース閉包を避ける

**決定:** 正式受入の gate を足す実装は、campaign lock が固定する強制ソース閉包の exact 25 path を
編集しない。閉包の外にある受入照合器・受領証・producer 側 driver・指紋計算 module で閉じる。
閉包内 file の改訂が本当に必要になった場合は、既存 campaign を無効化する影響を明示して
ユーザー裁定へ返す。

**理由:**
- 閉包 file の blob map は campaign artifact へ記録され、読み取り時に現在の map と照合される。
  1 byte でも変えると既存 campaign はすべて `E1-stale` として certified 受入から外れる。
- 受入 gate の追加は、既存の計測資産を捨てることと引き換えにする必要がない。
  同じ保証が閉包の外で作れるなら、そちらが常に安い。

**却下した選択肢:**
- 閉包内の producer へ書き込み経路を足す — 設計としては素直だが、既存 campaign の再計測か
  明示的な epoch migration を同時に要求する。今回の目的に対して代償が釣り合わない。
