---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t1946-registry-proof-chain
seq: 1
title: [T-1946] 試行台帳の proof chain 束縛を設計しきり、書き手が未配線のため実装せず凍結した (docs のみ、branch worktree-dev-wave-t1946-registry-proof-chain、実装面差分ゼロにつき変異 matrix は DW-S04 の免除)
---

## 本文

D1194 (旧 D1112) の択 (b) を実装する依頼で着手した。設計は完成したが、
D1114 の両条件が成立したため実装せず凍結し、裁定パッケージとして返す。
経緯は {{D:registry-binding-blocked-by-missing-writer}}、identity の形は
{{D:registry-proof-identity-is-prefix-not-tail}}。

**着手後に判明した順序抵触。** 依頼は D1112 を一次資料に指していたが、主題で引き直すと
後継の D1194 (ユーザー裁定) があり、さらに D1114 (順序) と D1193・D1279 (予算の留保) が
掛かっていた。T-1946 という ID で検索するだけではこの 3 件を全部取りこぼす。
裁定の照合は ID ではなく主題で行う必要がある。

**3 者独立で一致した実測。** 台帳の書き手を production から呼ぶ箇所は 0 件である。
親・レンズ A・レンズ B が別々に AST と動的解決まで調べて同じ結論に達した。
レンズ B は追加で、現在の production CLI が pilot だけであり official は既存検査が
既に拒否することも測った。したがって検査側だけを入れると、止まるのは
唯一稼働している pilot campaign である。

**独立レビューが親の実測 3 件を訂正した。** いずれも採用した。
(1) 遮断 meta-test が検出するのは exact token だけなので「admission に台帳参照を足すと
確実に赤」は過剰一般化だった。core と profile の read-only 経路は該当しない。
(2) schema を拒否する consumer 述語は 3 件であって 7 件ではない。
親が数えた残り 2 件は必要な変更面ではあるが述語ではない。
(3) 「行が無い台帳と genesis だけの台帳を chain head で区別できない可能性」は誤りで、
genesis は chained row になり非 zero の hash を持つ。

**レンズ B が単独で見つけた設計欠陥。** plan の初版は成果物へ記録した台帳 identity を
現在の末尾と完全一致で比較する形だった。台帳は append されるので、正当な次の試行 1 件で
既に certified だった成果物が参照不能になる。先頭 N 行の証明へ改めた
({{D:registry-proof-identity-is-prefix-not-tail}})。設計段階の敵対レビューが
実装前に捕らえた型である。

**レンズ A が単独で見つけた層の漏れ。** 公式選択表を発行する最終層は、
批准済み成果物を path と hash で照合するだけで live verifier を通らない。親も独立に確認した。
ただしこの層は certification の消費側であり、消費時点で台帳の生存を再確認することは
D1194 が求めた前向き束縛より強い性質なので、択一として返す。

**工数。** 子 3 本 (plan 1、consult 2)、いずれも rc=0 で成果物検査も緑。
実装子は起動していない。逐語は `output/insights/2026-09-01_t1946-registry-proof-chain/`。

## 次の一手差分

### 更新

- [T-1946] **P1・裁定済み (D1194) だが、裁定時の順序制約 D1114 で実装が塞がれた → ユーザー裁定待ち**:
  設計は完成し凍結した。実装単位 (配線と束縛を同時に land するか、配線を先行させるか)、
  D1193 が留保した予算の置き場所、成果物へ pin する identity の形、
  公式表発行層を射程に入れるかの 4 択を返す。詳細と親の推奨は
  {{D:registry-binding-blocked-by-missing-writer}} と
  `output/insights/2026-09-01_t1946-registry-proof-chain/s4-adjudication.md`。
  base: bee87a701503a939f8e32d85794e98fae703c29e5df30446502f2d76c23148f5

### 新規

- {{T:floor-registry-writer-wiring}} **P1・ユーザー裁定待ち**: 床値 campaign を試行台帳の
  書き手へ配線する。D1193 が留保し D1279 が「設計案が出た時点で諮る」と確認した
  予算の置き場所の裁定が前提になる。設計案は
  `output/insights/2026-09-01_t1946-registry-proof-chain/s4-adjudication.md` の択一 2 にある。
- {{T:floor-final-table-registry-liveness}} **P2・ユーザー裁定待ち**: 公式選択表を発行する
  最終層は批准済み成果物を path と hash で照合するだけで、台帳の生存を再確認しない。
  消費時点でも再確認するかを裁定する。親の推奨は「しない」(certification 自体は批准経路で
  起きており、消費時点の再確認は D1194 の要求より強い)。
