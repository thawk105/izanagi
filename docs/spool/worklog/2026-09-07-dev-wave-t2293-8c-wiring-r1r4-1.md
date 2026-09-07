---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2293-8c-wiring-r1r4
seq: 1
title: [T-2293] 8c 結線の契約側 (R1・R3・R4 の identity/consumer 面) を実装した — R2 と受入要件 12・18 は producer 層に依存するため裁定パッケージへ返す (コード + テスト + docs、branch worktree-dev-wave-t2293-8c-wiring-r1r4、変異 9/9 KILLED + 等価 1)
---

## 本文

- 依頼は D1667〜D1670 (R1〜R4) の結線。**本 wave が閉じたのは「8c の物理束縛契約」だけである。**
  「8c 結線完了」「発行 3 条件を満たした」「P6 が発火する」「本番で物理実行を保証する」とは名乗らない。
  **発行 3 条件は 0/3、本番 authority は 0 件のまま変わらない。**
- 段 3 の敵対レンズ 2 本が独立に「作り直し」と判定し、根本原因も一致した。R2 と受入要件 12・18 は
  親 brief 自身が scope 外と宣言した層 (ledger producer FSM、物理 evidence writer、
  witness normalizer、材料レポート renderer = 設計文書 §9 の未存在層) を必要とする。
  発火する producer を持たない gate を足すのは、ユーザーが明示した
  「仮想リスク向けの gate・検査の追加は scope 外」に反するので実装しなかった。
- 段 2 プランと段 3 の両レンズが「受入要件 14 は `result-evidence` に 3 本目の ref が要り、
  R1〜R4 の裁定範囲外だから実装不能」と結論したが、親はこれを **refuted** と裁定した。
  錠前の場所は identity から計算で決まるので、参照を足さずに受け手が計算して読める。
  詳細は {{D:origin-lock-path-computed-not-declared}}。
- 親が段 4 で出した「読み取り側で必要十分条件を強制せよ」という要求は**実装不能**だった。
  段 6 で訂正し、実在する層へ移した。{{D:origin-lifecycle-loader-cannot-enforce-the-iff}} と
  {{F:loader-used-a-proxy-for-a-bit-it-could-not-see}}。
- 本 wave は退行を 1 件入れ、同じ wave 内で直した。順序是正で lifecycle start が観測開始より
  前へ移り、観測後の失敗が終端を書けなくなった。
  {{D:origin-failure-terminal-without-projection}} と
  {{F:ordering-fix-orphaned-the-failure-terminal}}。
- 受理集合の変化は 3 件で、D1721 に従いいずれも**制御された拡張**として記録する。
  「緩めていない」とは書かない。(1) lifecycle start が 1 択から 2 択へ、
  (2) `execution-provenance` に v2 世代を追加し起点 consumer の受理を v2 だけへ縮小、
  (3) 起点の失敗終端が projection 無しで通る。originless の受理集合と bytes は不変。
- **v1 の歴史 decoder は作らなかった。** D1669 の「実在成果物を確認できたときだけ」の条件を
  実測で確かめたところ、`execution-provenance/v1` の実在成果物は repo の tracked corpus に 0 件で、
  production の書き手も存在せず、あるのは test fixture だけだった。条件不成立。
- 受入要件 16 (FC05a) と 17 の native WAL decoder は既に実装済みだった。
  **設計文書 §D の「現 formal consumer は fixture 形を要求する」は古い。**
  本 wave が足したのは 17 のうち shape family の混在拒否だけである。
- 変異は段 2 プランの 18 候補から、他層が先に同じ入力を拒否する 4 件を D1723 に従って外して
  10 件を登録した。初回は DW-M08 に従い probe として走らせ (期待 node の完全集合が未確定)、
  実測した集合で再登録して本走した。
  **本走は baseline PASSED、9/9 KILLED、SURVIVED 0 / MISMATCH 0。**
  probe で SURVIVED した 1 件は等価変異と確定した — producer が
  `campaign_output_root` へ `run_root` そのものを 1 箇所で代入しているため 2 式は同値で、
  どのテストも区別できない。段 6 の fix が root の分裂を構造的に閉じた結果であり、
  検査の欠落ではない。ただし**この性質はテストではなく単一代入によって保たれている**。
  mu3 は観測 node が 52 件に及び、単一理由性の証拠としては弱い (DW-M03 に従い明記)。
- 工数: codex 子 13 本 (plan 1、consult 2、author 3、review 2、fix 5)。
  段 5 の初回投入は 3 本とも 32 秒で停止した。**原因は親の手順漏れ**で、段 4 裁定を
  子から読める場所へ複製していなかった。子は「必読の正本が読めない」と申告して即停止しており、
  指示どおりの正しい動作である。job-id を変えて再投入した。
- 焦点走 1 回目は計算ノードの `queue-wait-timeout` で rc=16 になった。子は 1 度も起動していないので
  変更に帰属しない。D612 の上書き (queue 3600 / grace 600) で再投入して緑。
- 変異 harness の契約違反で 6 回止められた。いずれも harness が fail-closed で検出したもので、
  黙って進んだものはない。詳細は insight。特に「期待した赤テストが収集集合に存在しない」検査は、
  存在しないテストを期待集合にしたまま kill を主張するのを防いだ
  ({{F:expected-red-nodes-were-not-in-the-collection}})。

## 次の一手差分

### 更新

- [T-2293] **P1・実装中 (契約側は着地) → producer 層の設計 wave 待ち**:
  R1 (lifecycle start の起点専用 optional key)、R3 (execution-provenance/v2)、
  R4 の identity/consumer 面 (受入要件 9・10・11・13・14・15・17) は着地した。
  **R2 (起点専用 completion) と受入要件 12 (sealed executor)・18 (origin report) は未実装。**
  これらは設計文書 §9 が「未存在」と書いた producer 層 — ledger producer FSM、
  物理 evidence writer、witness normalizer、材料レポート renderer — に依存する。
  次はこの 4 層の設計 wave を 1 本立て、その後の実装 wave で R2 と要件 12・18 を閉じる。
  作らない限り、要件 12・18 と R2 は実装しても発火する producer を持たない。
  現状は発行 3 条件 0/3、本番 authority 0 件なので、作らなくても
  certified 選択・材料レポート・試行台帳の現在値は 1 つも変わらない。
  base: 62bba5ea81fee6d6c9cd4d279a5928538f4781771fe7f945370959a71d41a1a3
