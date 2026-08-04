---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-05
wave: dev-wave-t472-canonical-predicate-consumers
seq: 2
---

## {{D:consumer-local-canonical-membership}}. 凍結 literal を materialize する consumer は共有 helper の閉包に依存せず、自分が返す値を正準集合へ照合する

**決定:** 凍結成果物から取り出した literal (現時点では trigger 軸の `gate_predicate`) を
materialize 経路へ渡す consumer は、共有 materialize helper (`p3_s4_loop.quarantine`) の
内部分岐が同じ検査を持つかにかかわらず、**consumer-local に正準集合 membership を検査する**。
検査対象は入力側の凍結値ではなく、**その consumer が実際に返して materialize される値**とする。

冗長 gate であることは許容し、変異検査では実効 semantic kill と診断感度 pin を分けて記録する。
consumer-local 層だけを消しても共有層が同じ入力を拒否する場合、その変異は kill に合算しない (D中の
`DW-M03` 契約と整合)。

**理由:**

- 共有 helper 側の membership は `marker_id` の一致という**内部分岐**で発火する。
  consumer が渡す marker、helper 側の分岐条件のどちらが変わっても閉包は静かに外れる。
  閉包が偶発的である状態を、consumer 自身の防御層で解く。
- 検査対象を返り値側にするのは、`==` を偽装する非文字列が「凍結値との完全一致」を通過しても
  返り値が非正準になりうるためである。凍結値側だけを見る gate は consumer 境界の証明にならない。
- 追加した gate は現行の凍結値では発火しない。**これは恒真ではなく regression sentinel** であり、
  将来の refreeze drift・直接 caller・共有層の退行に対して発火する。
  記録では「初回閉包」と名乗らず sentinel と呼ぶ。

**却下した選択肢:**

- **共有 helper の閉包だけに依存する (現状維持)** — 閉包が helper の内部分岐に束縛されたままで、
  consumer 側の marker 結線が退行しても検出できない。
- **consumer 側の検査を凍結値 (入力) に対して行う** — 完全一致検査を通過した非文字列が
  返り値として materialize される経路を塞げない。
- **凍結値の読み取り直後 (完全一致検査より前) に置く** — 既存の不一致テストが期待する
  拒否理由を別理由で先取りし、既存テストの意味を変える。
- **共有 helper 側の membership を consumer へ移して一本化する** — 共有層は
  consumer 以外の materialize 経路も守っており、移設は受理集合を広げる。
