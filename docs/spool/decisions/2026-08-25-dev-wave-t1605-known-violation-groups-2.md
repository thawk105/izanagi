---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1605-known-violation-groups
seq: 2
---

## {{D:known-violation-frozen-baseline}}. known-violation の 2 群は凍結 baseline 集合で判定し、ancestry は test 層の裏取りに置く

**決定:** D742 の「不可逆な歴史群」と「新規に増えている群」は、D742 批准 commit
`5265fc6782fa5807aa742a198fa16d58006d17fb` 時点の台帳 53 複合キーを凍結 baseline とし、
その集合に属するか否かで判定する。判定は純粋な集合演算とし、checker の実行時経路へ
git 呼出しを足さない。「baseline の全 commit が批准 commit の祖先である」ことは
test 層で real repo に対して独立に裏取りし、凍結集合 (データ) と ancestry (意味) の
双方向一致に権威を置く。

群の値は rc の入力にしない。受理集合は変えない。群ごとの件数と母集合・除外条件は
history 経路で常に stdout へ出し、監査範囲に依存させない。既存の総数表示は意味ごと維持する。

上限は「歴史群のキー集合が凍結 baseline と完全一致すること」に置き、
positive control は production から独立した 53 キーの literal oracle をテスト側に持たせて
完全一致を要求する形とする。新規群 0 は運用目標として公開するが rc=1 にはしない。

**理由:**
- ancestry は commit の年代を判定するだけで**歴史群の集合を固定しない**。批准 commit より
  古い commit へ entry を足せば歴史群が 54 件へ増えても、件数下限・包含・分割の整合はすべて通る。
  D742 が求める「固定」が成立しない。
- ancestry を実行時経路へ置くと、batch 判定の前提が崩れる repo (境界 commit が解決できない
  一時 repo、shallow clone、prune 済み repo) で git 失敗が起き、**従来 rc=0 / rc=1 だった入力が
  rc=2 へ変わる**。報告だけの変更のはずが受理集合の変更になる。
- 新規群 0 を rc=1 にすると、D662 決定 4/5 が定めた「known-violation 登録で land する」経路が
  閉じる。受入の preclaim も land も引数なしの全史監査を stage failure として扱うため、
  新規 entry を登録した wave が自分の登録のせいで land 不能になる。
- 群の母集合を監査範囲に依存させると、範囲を空にするだけで指標を報告から完全に消せる。
  台帳全体を母集合にすればこの経路が塞がる。
- 指標を新規群 0 に改める効果は、遡及訂正枠 (`PR-C01`) の一回性を解除せず、
  監査文法も緩めずに得られる。

**却下した選択肢:**
- 群を `KnownViolationSpec` の宣言 field にする — 新しく作った違反を歴史群と自称して
  指標から消す経路を作る。
- 凍結 baseline を台帳から実行時導出する — 「歴史群 == 台帳全体」が恒真になり凍結が死ぬ。
- 承認済み新規 entry の集合を checker へ置く — 既存の逐語 mirror が同じ検出力を持つ
  二重化であり、D662 が新規登録への事前承認を明示的に却下している。
- 群の値を rc へ入れる — 受理集合の変更であり、land 経路を塞ぐ。
