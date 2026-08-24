---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-24
wave: dev-wave-t1574-t1529-sort-swo-oracle
seq: 1
---

## {{D:sort-swo-strong-isolation-before-reactivation}}. sort SWO corpus mutation 防壁は candidate の protocol・memory capability を分離するまで再有効化しない

**決定 (ユーザー裁定):** sort SWO oracle の corpus mutation 防壁は、candidate comparator が
protocol write fd を一度も所有せず、実 `WriteElement<Tuple>` の snapshot 対象 bytes への書込みを
強制的に拒否または trusted 側で観測できる process / memory capability 境界を設計・実証するまで
再有効化せず、正しさ防壁として数えない。本 wave ではコードを変更しない。

D696 の pre-sort snapshot 専用 pipe + 親側 pre/post 比較という方向は、同一 process / 同一 TU では
candidate が基準 snapshot を上書きできるだけでなく post frame 自体を偽造できるため不十分だった。
candidate を別 translation unit へ移して trusted symbolを通常の name/linkage から隠す案も、同一
process が post pipe fd capabilityを共有するため採用しない。

この決定は、既存 oracle の有限 corpus 上のSWO公理検査や他のfindingを合格へ倒すものではない。
対象は corpus mutation 防壁の信用と、修理済みの明示的正例・負例を得る前の再有効化だけである。
Masstree test environmentのbuild残骸依存と合法candidateのA2は未修理のまま残し、強い隔離と同じ
閉包で再設計する。

**理由:**
- 一度process外へ出たpre bytesはcandidateが取り消せないが、同じprocessがpost fdを所有すれば
  mutation前snapshotと合法relationを偽post frameとして新たに書ける。
- 別TUは `trusted_snapshot` やwriter helperへの通常の名前解決を遮断するが、process capabilityを
  遮断しない。識別子隠蔽を防壁として数えるとD696が退けた隠蔽依存を別の形で繰り返す。
- 規律2は、修理を急ぐ圧力を理由に既知bypassを残したoracleを再有効化することを許さない。

**却下した選択肢:**
- D696 の同一TU literal実装 — candidate側baseline再代入は閉じてもpost frame偽造が残る。
- 別TUだけを追加する — name/linkage分離は成立するがfd capabilityが残る。
- 既知残余として受容し再有効化する — 規律2最優先というユーザー指示に反する。
- 本 wave でprocess/memory隔離まで即実装する — 非同値な大幅scope拡大で、設計と実証が未完である。
