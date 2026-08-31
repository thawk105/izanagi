---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t2076-t493-sort-oracle-parent-reference
seq: 3
title: [T-493] sort comparator の閉じた権威集合を入れ、T-2076 は前提が覆ったので再裁定へ返す (コード + docs、branch worktree-dev-wave-t2076-t493-sort-oracle-parent-reference)
---

## 本文

- 依頼は T-2076 (D1271) と T-493 を 1 変更単位で実装することだった。着手前実測で D1271 の前提が
  覆り、T-2076 は実装せず裁定パッケージへ返した。T-493 だけを実装して land した。判断の理由は
  {{D:sort-oracle-relation-provenance-has-no-minimal-fix}} と
  {{D:sort-authority-lands-alone-when-bundling-premise-is-void}}。
  実装の設計は {{D:sort-comparator-authority-mirrors-trigger-exactly}}。
- **束ね条項を充足不能と判断したのは親であり、ユーザー裁定ではない。** 取り消したい場合は
  実装 commit を revert できる。
- 親の provisional 案 2 件はどちらも子に反証された。観測 fd へ内容 witness を足す案 (段 1) は、
  候補が同じ fd の所有者なので出所を作れない。比較ごとに `fork()` する案 (段 2 後に親が着想) は、
  候補文の引数評価が worker 親で起きること、および現行 seccomp が `clone` / `wait4` を許さず
  filter を積み増ししかできないことで潰れた。段 2 が推した broker trap 案も、trap と
  trusted callsite が候補と同じ翻訳単位にあるため呼出しの出所を証明しないと段 3 が判定した。
- **逆に、子の反証のうち 1 件は親が実測で退けた。** レンズ B は「候補が `active_order` を
  書き換えると broker の解釈がずれる」と述べたが、`active_order` から得た添字は読まれない配列の
  索引にしか使われず、comparator の入力も観測の出力順も position 索引である。親の (P1-b) が real。
- 親 brief の記述 2 件が stale だった。oracle test の受入全走からの恒久除外は現行では成立せず
  (除外表は空)、凍結 bytes 検査は hold 中で実効関門ではない。どちらもレンズ B が指摘し、
  親が再測して採用した。
- 着手前から存在する drift を 1 件見つけた。凍結文書が記録する generator の sha256 と現行実装が
  食い違い、`verify_document` は本 wave と無関係に赤になる。本 wave が壊したものではない。
- レンズ A の must-fix 1 件は real で、親が repo 外 probe で再現した。既存 node の一 byte 改竄先が
  `sort_best.name` だったため、新しい権威検査が機械再構成照合より先に発火していた。改竄先を
  `what` 値へ移して意図と期待メッセージを保ち、name 改竄が権威層で止まる挙動は専用 node で
  別に固定した。レンズ B の must-fix (束縛 module を凍結 source closure へ pin する) は
  trigger 軸も同じ性質を持つため、本 wave の回帰ではないと裁定し backlog へ送った。
- 変異事前登録は段 4 で凍結した後、実装後の実テスト構成に合わせて erratum で訂正した。
  MUT-1 の期待 node は 2 件から 7 件の完全集合へ、MUT-3 (常に拒否させる正例) は過剰決定のため
  単独変異の証拠から外し、承認外の過剰拒否は 2 つの正例テストが担う形へ改めた。
- 子の工数: plan 1 本、相談 3 本 (うち 1 本は内容フィルタで成果物ゼロ、書き直して再投入)、
  実装 1 本、レビュー 2 本、fix 1 本。すべて `gpt-5.6-sol` / `reasoning=xhigh`。
- 実測: 焦点走は fix 後に 38 passed / 9 skipped で rc=0。consumer 4 file は 202 passed /
  23 skipped で rc=0。glob 走査のメタ test は 3 passed。変異 matrix は 3 変異すべて KILLED、
  `matches_expectation=true`、baseline PASSED。全史 provenance 監査は 7159 件・新規違反なし。
- 変異の共有木検査は主 checkout の churn で最初 rc=125 になった。独立 clone を `--source-repo`
  へ渡して構造的に断ち、plan-only rc=0 を確認してから detached で本走した。

## 次の一手差分

### 完了

- [T-493] `sort_best.comparator` に候補空間 15 組から機械導出した閉じた権威集合を入れた。
  exact binding 一本で、生成側 2 経路と `_validate_schema` の検証側に束縛を置いた。
  凍結済み 3 entry は bytes を変えずに通る。
  remaining: none
  base: 711a3650a85e25366ae6c3024e52905835415895e1a7f80416631243a6cef314

### 更新

- [T-2076] **P1・ユーザー再裁定待ち**: D1271 が名指しした基準 snapshot は T-1574 が先に
  read-only arena へ移しており、literal な実装対象が存在しない。残る関係行列の出所は
  D1271 の対象外であり、検討した 3 案はいずれも不成立だった。成立しうるのは受理言語を
  検証済み IR へ縮め trusted interpreter で評価する案だけで、最小実装ではない。
  択一は (a) 別 wave の設計として起票、(b) 非保証のまま運用、(c) 別案。
  詳細は {{D:sort-oracle-relation-provenance-has-no-minimal-fix}}。
  base: 547f77cdb4134c03b065a404e4a2636918169b631fcb6757bb7813b9f5cd2aea

### 新規

- {{T:freeze-source-pin-for-binding-modules}} **P3・新規 (段 6 レンズ B の所見を裁定して分離)**:
  凍結文書の source closure が、trigger 軸の束縛実装も sort 軸の権威集合も pin していない。
  受理集合を決める候補空間と正準述語は pin 済みだが、導出ロジックは pin されていないため、
  後続 commit が束縛 module だけを変えても凍結参照が変わらない。**両軸を 1 つの変更単位で**
  pin する。片側だけ足すと非対称を逆向きに作る。
