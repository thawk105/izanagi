---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-acceptance-wall-20260907
seq: 1
title: 受入全走の wall を分解し短縮候補を実測で値付けした — 55 秒の本命は裁定待ち、t080 共有 cache は効果ゼロで撤去、land したのは冗長 test 2 件の削除だけ (コード + docs + insight、branch worktree-dev-wave-acceptance-wall-20260907、変異 3/3 KILLED)
---

## 本文

- **依頼は「受入全走が時間がかかりすぎている。不要なテストは消す、並列化・バッチ化・
  賢い論理での短縮はやる、リワードハック禁止」だった。land したのは冗長 test 2 件の削除
  (約 1 秒) だけである。短縮を主張しない。** 主成果は wall の分解と候補 3 つの値付けで、
  一次資料は `output/insights/2026-09-07_acceptance-wall-decomposition/`。
- **wall の分解を初めて数字で closed にした。** 直近 3 日 約 77 走の中央値で
  `wall = 最忙 worker のテスト実行時間 + 残差`。shard-0 が 75 走中 70 走で最遅
  (306.6 = 191.6 + 102.0)、shard-1 / shard-2 の残差は 59.0 / 58.6 秒。
  全体 wall 中央値 324.3 秒、300 秒超過 45/75 走。分解の契約は
  {{D:acceptance-wall-decomposition}}。
- **本命 (shard あたり約 55 秒) は D711 に塞がれており、ユーザー裁定へ返す。**
  48 プロセス同時 collection は全 file 87.57 秒に対し自 shard 絞り込み 27.44 秒。
  D711 の費用前提 (当時 12.86 秒) は約 4.6 倍に失効している。技術的障壁とされた
  `ModuleNotFoundError` は原因を特定した — 2 つの test file が他 module の import 副作用で
  `sys.path` に載る `orchestrator/` へ暗黙依存しているだけで、直せる。
  **残る論点は gate 2 (全 shard の universe 一致) を弱めてよいかの一点。**
  {{D:d711-cost-premise-expired}}。
- **t080 base の worker 跨ぎ共有は実装して A/B で効果ゼロを実測し、撤去した。**
  同一 command で wall 99.80 → 98.92 秒、所要総和 909.6 → 932.6 秒。実装は正しく動いており
  (fail-closed 2 分岐を repo 外 probe で確認)、**消費者が同時に miss すると構築が lock 待ちへ
  置き換わるだけ**という構造的理由だった。段 3 のレンズ B が事前に予告し、親は覆せなかった。
  465 行の patch は insight の `verbatim/unit-a-dropped.patch` に保全した。
  {{D:shared-fixture-cache-no-gain-on-simultaneous-miss}}。
- **collection hook の重複評価除去も撤去した。** 効果は約 0.4 秒 (wall の 0.1%) で、
  段 6 レビューが (a) 形式的な受理集合の拡大、(b) 恒真な bytes 一致検査、
  (c) 本番集約経路を通らない回帰検査を指摘した。
  {{D:no-accept-set-widening-for-sub-percent-gain}}。
- **「不要なテストを消す」は受入の所要にほぼ効かない。** 14,179 個の test function を
  AST body で走査して完全一致の対は 11 組、うち 10 組は 0.01 秒未満、1 組は別 wave の
  着地後に独立オラクルの対になるため残した。実際に削除できたのは 2 node で約 1 秒である。
- **親自身の誤りを 4 件訂正した。** (a) D1020 の引き金を shard ごとに当てたのは誤りで、
  走全体では `C = 161.6 > W/(48K) = 129.1` により成立していない。(b) 反実仮想の利得は
  中央値 11.6 秒で走間ばらつき 32 秒より小さく、D1019 はそのまま有効。(c) 中央値 324.3 秒は
  複数 tip の混合で前後比較に使えない。(d) 「削除候補ゼロ」は AST 走査の 120 文字閾値による
  取りこぼしだった。(a)(c) は段 3 のレンズ B、(d) は段 2 の子が指摘した。
- **段 2 の子が親の閉包漏れを 2 件見つけた。** t080 base の 60〜77 秒と 11 worker 分散は
  2026-09-04 の別 wave が既に実測しており、親の「発見」は再発見だった。
- **段 5 の実装子 1 本が model call 上限 100 で打ち切られた。** 編集は worktree に残っていたので
  規律どおり保全し、上限 320 の継続子へ「前の子の差分を自分で監査して完成させろ」と
  指示して投げ直した。継続子は A1 の束縛不足を自分で見つけて補強した。
- 段 6 の敵対レビュー 2 本はいずれも `blocker` 0、`should-fix` 2。
  変異は削除の positive control として「残す側が削除した側と同じ検出力を持つか」を
  production 変異で示し、**3/3 KILLED・期待 node 完全一致・MISMATCH 0・SURVIVED 0** だった。

## 次の一手差分

### 新規

- {{T:acceptance-collection-scoping-ruling}} **P1・ユーザー裁定待ち**: 受入の collection を
  自 shard の file へ絞ってよいか (D711 の再検討)。賞金は shard あたり約 55 秒で、
  費用前提の失効と技術的障壁の原因特定は済んでいる。**残る論点は gate 2
  (全 shard の `observed_universe` 一致) の弱体化を許すかの一点。**
  選択肢: (a) 現状維持、(b) 依存 2 file を直したうえで絞り込みを採り、gate 2 の代替として
  「各 shard が collect した node 集合が割付と exact 一致すること」を新設する、
  (c) 絞り込みは採らず gate を保ったまま collection 自体を速くする別案を探す。
  親の推奨は (b) の検討だが、正しさ防壁の変更なので親は実装しない。
- {{T:t080-base-prewarm}} **P2・新規**: t080 base を collection 中に組む (prewarm)。
  固定費 59 秒の窓に構築 70 秒を重ねれば test 段から消える。同時 miss の lock 待ち問題は
  test 開始前に完了することで回避する。撤去済み patch を出発点にできる。
- {{T:selftest-syspath-independence}} **P3・新規**: `test_s8b_approved.py` と
  `test_profiler_directive.py` が他 test module の `sys.path` 副作用へ暗黙依存しているのを
  直す。file 選択走の偽赤の原因であり、collection 絞り込みの前提でもある。
