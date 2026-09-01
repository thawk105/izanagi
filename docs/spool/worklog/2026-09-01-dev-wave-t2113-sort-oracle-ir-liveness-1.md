---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t2113-sort-oracle-ir-liveness
seq: 1
title: [T-2113] sort SWO oracle を検証済み IR へ縮める方向の生死確認は 4 項目すべて真 (実装面の差分ゼロ、branch worktree-dev-wave-t2113-sort-oracle-ir-liveness、負例対照 3/3 KILLED)
---

## 本文

D1355 が実装前に確かめよと定めた生死確認を行い、**4 項目すべて真**で終えた。縮小そのものは
実装していない。判断と限界は {{D:sort-oracle-ir-liveness-bounded}}、逐語と実測は
`output/insights/2026-09-01_t2113-sort-oracle-ir-liveness/`。

**段 2 と段 3 の両レンズが共有していた前提が、親の実測で覆った。** 三者とも
「実 oracle は masstree 未設定で実行不能。ground truth は 3 field だけの proxy 型に限る」と
判断し、レンズ B はそれを根拠に `PASS` 不可、レンズ A は `q2=UNAVAILABLE` を要求していた。
実際には masstree source が機体に実在し、実 TU (35103 bytes、実型 `WriteElement<Tuple>`) が
そのまま compile でき (rc=0)、実 broker・実 seccomp・実 arena が 324 byte の行列を返した。
よって proxy C++ harness は書かず、ground truth を production 実装そのものにした。
D344 が実型 harness を必須とした理由はこれで回避されている。

測定規模は IR 79 値 (3 field に対する相異なる field 辞書式比較の完全閉包) x 2 corpus x
3 order x 324 セル = 153,576 セル、compile 80 回、**不一致 0**。

**緑が恒真でないことを負例対照 3 件で確かめた。** Python evaluator だけを壊し実 TU は変えていない。
符号つき storage、逆順 pointer rank、NUL 切り詰め key の 3 件すべて KILLED。
pointer rank の逆転が各 corpus 108 セルで検出されたことは、pointer 順位の導出が
偶然の一致ではなく実際に検査されていることの証拠である。

段 3 の所見のうち real で scope 外の 4 件はユーザー裁定へ返す (insight §6)。**最重要は
D344 との衝突**である。D344 は本方向 (typed IR / AST allowlist) を明示的に却下しており、
理由は技術的不能ではなく「合成が事前 allowlist からの選択に化け、raw C++ comparator の
独立合成という D39 の実証点を別実験に変える」であって「親は決めずユーザー裁定へ返せ」と
書いてある。D1355 はこの却下理由に触れていない。生死確認が真でも、D1355 が D344 の
この部分を supersede するかは未裁定である。

親 brief の誤りを段 2 が 2 件是正した (allocator 順の行番号、exact binding 関数の行番号)。
親 brief の「pointer 順位は corpus から導出できる」も「corpus の kind/slot と現在の TU の
記述順から導出できる」へ狭められた。

`DW-G01` の 100 行予算は超過した (driver 3 ファイル 270 物理行)。C++ harness を書かない分は
縮んだが、79 値・JSON wire 12 例・全セル比較・4 状態分離を 100 行へ収めると複雑さを
行数から隠すだけになるため、検査範囲を減らさず超過を明記する方を選んだ。

稼働中の [T-1999] が `orchestrator/tests/test_sort_swo_oracle.py` を branch tip と
未 commit の作業ツリー 2 本で所有していたため、起動時の編集面重複検査 (branch 42 件 /
worktree 28 件、unreadable 0) で確認したうえで同 file に触れていない。

## 次の一手差分

### 完了

- [T-2113] 生死確認を 4 項目すべて真で終えた。実 oracle の TU・型・allocator・broker を
  ground truth に使い、79 値 x 2 corpus x 3 order の全 153,576 セルで不一致 0。
  負例対照 3 件すべて KILLED。実装面の差分は持たない。
  remaining: none
  base: f51343751286a555726a7390ebaa1e9fed19575f16db010e29b01d8ab038a90a

### 更新

- [T-2076] **P1・ユーザー裁定待ち**: 向き (受理言語を検証済み IR へ縮める) の生死確認は
  [T-2113] で真になった。技術的な障害は無い。残るのは D344 が却下理由として挙げ、
  ユーザー裁定へ返した実験同一性の論点であり、D1355 はそこに触れていない。
  設計 wave の起票前に、D1355 が D344 の当該部分を supersede するかの裁定が要る。
  base: be40840f930bc59f89ee1e907867cc87cb4b0b1e5906115c90ce3f63eaf1aa6e

### 新規

- {{T:sort-oracle-ir-design}} **P1・新規 ([T-2113] が真だったため起票)**:
  sort SWO oracle の受理言語を検証済み IR へ縮める本設計を実装する。
  **[T-2076] の裁定待ちが解けるまで着手しない。** 着手時は生死確認が licence していない
  4 点を設計事項として先に閉じる — 受理権威の役割分離 (IR parser /
  `_validate_single_sort_statement` / `coder_effect_gate` / SWO oracle / exact binding の
  どれが権威でどれが恒真化するか)、pointer 意味論の確定と contract 束縛、
  現行 accepted 集合との包含の完全証明、certified `sort_best` の 15 組 exact binding を
  79 値 admission で置き換えない分離。
