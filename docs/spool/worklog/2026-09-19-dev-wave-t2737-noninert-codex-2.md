---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-19
wave: dev-wave-t2737-noninert-codex
seq: 2
title: [T-2737] 中断waveを回収し、受入で出たdefine目録の赤をinclude guard除外で閉じた (コード + docs、branch dev-wave-t2737-noninert-codex)
---

## 本文

- 記録commit `fdbf21820` で中断したwaveを別セッションが回収した。実装は変えない前提で受入へ進めたが、
  受入attempt 1 (3 shard、25276 passed) が `test_ccbench_spawn_sites.py` の define 目録 3 件で赤になった。
  原因は本wave起因: 裁定済み patch c (`#pragma once` → include guard) の guard 3 個を目録関数が
  外部供給 TU define と誤認した。base/main の patch には無い (hit 0)。
- 裁定: `#pragma once` 復帰 (裁定違反)・`DEFINE_SPECS` 登録 (supply macro 化)・期待値更新/skip (弱体化) は
  採らず、Codex author の fix3 で目録関数に「新規 file の include guard 慣用句」の構造的除外を足した。
  受理集合が変わるため read-only 焦点再レビューを 1 本入れ、NO-GO (guard 形 + 本文 `#if X + 0` で
  外部供給 macro が消える逃がし道) → fix4 で除外を guard 行 1 行に限り反例を負例に追加。
  統合commit `134ea235c` → `7f24b1c32`。焦点走 180 passed / 2 skipped × 2 (計算ノード)。
- 変異 (fix4 commit を独立clone main に固定): baseline PASSED、M7/M8/M9 すべて KILLED、期待 node 完全一致 3/3。
  一次記録は `output/insights/2026-09-19/t2737-noninert-implementation/README.md` 末尾の節。
- 焦点走が `patches/` を directory glob で読む consumer test を名前検索で落とした点は F386 の再発として追記した。
- Codex 子 3 本 (fix3 11 call / fix4 7 call / focus3 6 call) はいずれも計算ノード dispatch の preflight で
  pytest を起動できず、実走は親が行った。main は base から 35 commit 前進しており、統合commit `4c9d9ecc2`
  で取り込んだ (衝突は `docs/phase3.md` 先頭項目 1 か所、両項目を保持)。
- 受入再走・land・撤去は本fragment時点で未実施。専用handoffと原ログは
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-noninert-codex/`。dev-wave改善候補はなし。

## 次の一手差分

### 完了

- [T-2737] D2148項4のhelper接続と非inert局所修正、phase1条件・計器呼出し保存の検証を完了した。受入で出たdefine目録の赤はinclude guard除外 (fix3/fix4) で閉じた。controls全体は未成立のまま、inert側の契約は変更しない。
  remaining: none
  base: 26025c5cd7c51c3e144cff72b3a2a31863e40953e922a9a17833ccb705e5c8a8
