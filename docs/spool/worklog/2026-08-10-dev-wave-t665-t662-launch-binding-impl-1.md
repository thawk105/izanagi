---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t665-t662-launch-binding-impl
seq: 1
title: dev-wave の起動値を docs 権威へ機械束縛した ([T-665] + [T-662]) — 変異だけが「中核主張が未証明」を暴いた (コード + docs、受入 8237 passed / 20 skipped / 477.80 秒 / rc=0、変異 2 走で KILLED 相当 8・冗長分岐 1、branch worktree-dev-wave-t665-t662-launch-binding-impl)
---

## 本文

- **ユーザー指示による起動。** 「[T-184] は land 済みで待ち条件は外れている。R1〜R5 の承認どおり、
  dev-wave が起動する codex の `-m` 実引数と段 6 の effort を機械束縛せよ」。
  **D266 は本文で「本決定は下流タスクの待ち解除語として使ってはならない」「下流が待っているのは
  canonical stage matrix と起動前 policy であり、本決定はそれを発行していない」と明記している。**
  親はこれを AI による自己解除の禁止と読み、ユーザーの明示指示を人間権限による解除として採った。
  この判断自体を記録に残す。設計は {{D:launch-value-docs-binder}}。
- **段 3 の敵対 2 レンズはいずれも NO-GO** (レンズ A = sol / must-fix 12、レンズ B = luna /
  must-fix 7)。所見は**全部 real で refuted はゼロ**だった。親は承認済み裁定を不採用にはせず、
  実装できる範囲へ scope を縮小し、残りを新事実付きでユーザー再裁定へ返した。
- **親自身の実測を 2 件撤回した。** (i) 段 1 で「launcher は `turn_context.payload` だけを見る」と
  書いたが、実装は `payload.get("model", event.get("model"))` で top-level へ fallback していた。
  不変条件は**未充足**だった。(ii) `_writer_truth` は `attempts[-1]` だけで job を accepted に
  しており、先行 attempt が invalid でも retry が通れば rc=0 になっていた。両方とも本 wave で閉じた。
- **land する起動経路を wave 内で実際に使った (dogfood)。** 段 6 のレビュー 2 本を
  `tools/dev_wave_codex.py` 経由で起動し、receipt v3 に `requested_model=gpt-5.6-sol` /
  `requested_effort=high` / `effort_authority=docs` と authority snapshot
  (commit `3cd457a4` と `DW-O01` / `DW-S06-A` / `DW-S06-C` の節 digest) が記録された。
  **これが本 wave の中核証拠である。**
- **その dogfood が、静的レビュー 4 本が出せなかった欠陥を 1 件出した。**
  契約どおりに起動すると rc=2 で必ず死ぬ状態だった ({{F:documented-route-not-executable}})。
  **親が最初に書いた `DW-O01` の文面自体が実行不能で、それは両レンズが独立に指摘した。**
- **変異が、本 wave で最も重要な発見をもたらした。** 対象テスト 623 全緑・敵対レビュー 4 本
  通過の状態で、段 6 effort の派生を別値へ置換する変異が**生存した**。期待値を派生関数自身から
  取る循環のせいで、[T-665] の中核主張が証明されていなかった
  ({{F:derived-oracle-circular-test}}、{{D:derived-value-test-needs-independent-oracle}})。
  docs を独立に読む cross-check 3 本を足し、訂正再走で KILLED になった。production は変えていない。
- **変異 2 走の判定は KILLED 相当 8 / 冗長分岐 1** (baseline は両走とも PASSED)。
  M03 は U+2028/U+2029 拒否分岐で、単層でも二層でも生存した。親が機序を実測したところ
  **Python の `splitlines()` が U+2028/U+2029 で行を分割する**ため偽装行は上流で拒否されており、
  性質は守られているが当該分岐が独立に効くことは示せない。`DW-M03` に従い kill として数えず
  冗長分岐と記録した。診断文字列の一致だけで kill を作ることはしていない。
  M01 / M06 の MISMATCH は親の登録漏れで、期待 node はすべて赤くなっている。
  M06 の 1 node は 1 走目赤・2 走目緑のフレークで変異へ帰属しない。
- **docs 予算が設計を 2 度動かした。** [T-313] の三層構造 land 後も L1 = 10,625/10,625、
  L1.5 = 9,566/9,566 でどちらも残 0 だった。`DW-O01` の改訂を 2 度実測し直し、
  最終的に 833 → 821 bytes (L1.5 = 9,554 / 9,566、余白 12) に収めて発火する契約文を通した。
  段 2 プランが提案した `DW-S06-A/C` への追記と `DW-O17` への 293 bytes は、裁定で撤回した。
- **段 6 の fix は 3 巡回した。** 1 巡目で 4 赤 → 2 赤、2 巡目で 0 赤、3 巡目は変異が暴いた
  検出力の穴を塞ぐテスト追加。2 巡目を一枚岩にしたのは、残る 2 所見が 1 巡目の所有分割
  (launcher / dispatcher) を跨いだためである。
- **実装子は 5 本とも pytest を 1 件も走らせられなかった** (sandbox が予約台帳と socket を作れず
  runner が rc=16 で停止)。緑の判定はすべて親が計算ノードで実測した。
- 受入は 1 走。lease を `acquired` した直後に local main を merge commit で取り込んでから投入した
  (待機中に main が 71 commit 進んでいた)。**request `901025.nqsv`、tip `01436512`、
  8237 passed / 20 skipped / 477.80 秒 / rc=0**。記録 commit はこの tip より後になる。
- 逐語・裁定・変異台帳の正本は `output/insights/2026-08-10_t665-t662-launch-binding-impl/`。

## 次の一手差分

### 更新

- [T-665] **P2・段 6 effort の束縛は land 済み → 残余はユーザー再裁定待ち**: 段 6 の
  review / focus は `DW-S06-A` / `DW-S06-C` から effort を導出して起動前に束縛し、全 attempt の
  全 `turn_context` が一致しなければ受理しない。実運用の dogfood で receipt に記録済み。
  **R2(a) の段 7 集合等価 gate は実装していない** — 新事実 2 件を添えて返す。
  (i) bootstrap: 本 wave 自身の段 2/3 は raw 起動で receipt を持たず、v3-only gate を自己適用できない。
  (ii) 完全性: 必要 job slot の inventory は未発行の canonical stage matrix に依存し、
  `len(E)>0` だけでは工程別 0 件が恒真になる。
  base: e8540c0f115dc38ce88e83ff830ea7ff86fdf94f2e85ad36f25514671eb9aef9
- [T-662] **P2・model の束縛は land 済み → 残余は [T-665] と同じ**: `-m` 実引数は全段で
  `DW-O01` の権威行から導出し、caller は指定できない (`--model` は削除、既定値も除去)。
  未申告の raw `codex exec` は R2(a) の既知限界として引き続き観測できない。
  base: 6ae49356e7e0b147f141f72994deff5242af07e30fe77adef86ca467e7996023

### 新規

- {{T:launch-binding-set-equality}} **P2・ユーザー裁定待ち**: 起動値束縛の段 7 集合等価 gate と
  期待 job 台帳の freeze。返す理由は bootstrap と完全性の 2 件 ([T-665] の項)。
  未申告 raw の閉包 (実行面で拒否する hook 配線) も同じ束で判断する。
- {{T:dispatcher-sandbox-normative}} **P3・ユーザー裁定待ち**: `DW-S06-A` / `DW-S06-C` に
  sandbox 値が無いため、dispatcher は `--sandbox` を caller 必須にしている。
  規範化するなら別裁定と所有の明示が要る。段別 resource 上限と retry policy も同じ空白にある。
- {{T:u2028-branch-redundancy}} **P3・調査**: 規範行抽出の U+2028/U+2029 拒否分岐が
  単層・二層のどちらの変異でも生存した。性質は上流 (`splitlines` の行分割) が守っている。
  当該分岐を残すか外すか、独立に効かせるかを決める。
