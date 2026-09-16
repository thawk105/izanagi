---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2655-prov-incremental
seq: 1
title: [T-2655] 差分 provenance 監査は前日に着地済みで、残っていたのは stale carry だけだった (docs、branch worktree-dev-wave-t2655-prov-incremental、実装差分ゼロ・変異 matrix 免除)
---

## 本文

- ユーザー依頼は「全史 provenance 監査を差分監査にする。台帳は [T-2655] (P1・新規)。D908 が課す
  条件 — 取り込み差分だけを対象とする独立監査を先に設計し、被覆が現行と等価であることを示す — を
  満たす形にする。着手前に段 1 で本項が未着手であることを再確認すること。実装面は Codex author。
  本題の差分監査だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **依頼の前提は覆った。本題は 2026-09-15 に着地済みである。** 一次資料は commit
  `33c608726c39c4adab8b5fb6538083f3b559922c` (2026-09-15 21:41 JST)、裁定 D2045、
  worklog entry (1529)。entry (1529) のユーザー依頼文は本 wave の依頼文とほぼ同文であり、
  D908 の条件・fail-open の禁止・D387 型の限界の明記まで一致する。親は段 4 で
  **「実装しない」と裁定**し、段 5・6 を飛ばして `4→7→8→9` とした。
- **依頼が挙げた 3 つの確認は、どれも正しく、どれも不在証明になっていなかった。**
  (1) `git log main --grep=T-2655` = 0 件 — 着地 commit の題は英文で task ID を含まない。
  (2) branch `worktree-dev-wave-prov-incremental-audit` の `main..branch` = 0 — land 後に
  main へ ff-only された結果であって、未着手の印ではない。
  (3) 中身の無い worktree 残骸 — 撤去されなかった land 済み wave の残骸である。
  **着地判定の一次は commit 題でも branch の ahead 数でもなく、成果物そのものの実在**であった。
  本 wave は `tools/check_ai_provenance.py` の `_receipt_bindings` / `_receipt_prefix` /
  `_publish_audit_receipt` を読んで初めて済を確定した。
- **親が段 1 の生死実験で測った値が、前提を覆す前に誤った方向へ働いた。** 全史監査を素で 1 走
  させたところ 10465 件 / 671.594 秒 (rc=0) を要し、親はこれを「差分化の取り分は大きい」と読んだ。
  実際にはこれは**受領証不在の cold 走**であり、既存機構が効いていない状態の値だった。同一 HEAD で
  2 走目を測ると 118.041 秒 (rc=0、出力同一) で、warm 経路が現に発火していた。
  **1 走だけの計測は、機構の有無ではなく cache の状態を測りうる。**
- **warm 118 秒は entry (1529) が記録した warm 値 (1.105〜4.754 秒) と 2 桁違う。** 本走は
  bounded local scope (予算 1 GiB) の login node で、他 session の同種監査と競合していた。
  差は履歴長に比例して残る項 (選択集合の列挙・祖先 bitset・append-only 検査・属性 fingerprint) に
  乗ると見られるが、本 wave は切り分けていない。これは [T-2656] の担当範囲であり、
  **本 wave の scope 外**として実測値だけを残す。
- **stale carry は F35 の既知 6 形態のうち 2026-08-18 型の再発である。** entry (1529) は本題を
  実装・記録しながら、次の一手差分で自 task ID を `完了` 節へ明示しなかった。`docs/spool/README.md`
  の暗黙 carry が `- [T-2655] (N)` を (1528) から (1543) まで無傷で送り続けた。carry stub は本文を
  持たないため、描画された worklog を読む限り陳腐化は見えない。恒久対応 1 (`DW-S01` の
  brief 前照合) は本 wave でも投入前の防壁として働き、**実装子を 1 本も走らせずに止まった**。
- 工数: codex 子 1 本 (段 2 plan) を起動したが、前提が覆った時点で親が停止させた。段 3・5・6 は
  起動していない。実装面の差分はゼロなので変異 matrix は免除 (D237 / D301 の連言が成立)。
  受入全走は免除せず実走した。

## 次の一手差分

### 完了

- [T-2655] 差分 provenance 監査は commit `33c608726` と D2045 (いずれも 2026-09-15〜16) で
  既に着地しており、本 wave は済を一次資料で確定して carry を閉じた。残る per-commit /
  履歴長比例コストは [T-2656] が持つ。
  remaining: none
  base: 58beb22f565c3e53b80f17b6e15494e05136178764866e85d1e5b61bb534d5b4
