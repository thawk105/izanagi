---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2709-blob-transfer-cost
seq: 1
title: [T-2709] t080 fixture の「必要 blob だけの移送」を計算ノードで対比較し、測定条件内で base 1 回 −1.68 秒 (15%) の改善候補と記録した (受入 wall は未測定、docs + 計測成果物、実装差分ゼロ、branch worktree-dev-wave-t2709-blob-transfer-cost)
---

## 本文

- 依頼は [T-2709] の費用実測だけ (fixture 本体は変えない、新 gate・台帳・一般化なし)。一次資料は
  `output/insights/2026-09-20/t2709-blob-transfer-cost/README.md` (設計・事前登録・全試行の生値・裁定パッケージ)、設計判断は
  {{D:t2709-blob-transfer-measured}}。専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2709-blob-transfer-cost/HANDOFF.md`。
- **起票文の前提を brief 前に覆した。** 「削減分 79〜191 秒」は login の外乱値で、D2086 の一次資料 (計算ノード直列、git 操作 11 回 9.5 秒)
  と本 wave の実測 (A の `add -A` 10.65 秒) が示すとおり、計算ノードの index 化は 11 秒である。
- 段 3 相談 1 本 (2 レンズ、codex sol) は must-fix 7 (参照 `.git` が `add -A` に拾われる / C2 の不足 blob / C1 の選定費用 / cold の語彙 /
  「普遍的下限」は `checkout-index -u` で反証 / 同値性の検査 4 種 / 判定規則の語彙と最小効果量) を出し全採用、棄却 0。
- 段 5 は Codex author 1 本 (probe 959 行、`0e675923…`、repo に入れず job dir へ保全)。親が login で selftest (20 項目緑) と
  hold-session-only を実走し、計算ノード generic dispatch 1 本 (`11899.nqsv`、bnode007、local xfs `/tmp`、Elapse 400 秒) で本走した。
  段 6 review 1 本 (2 レンズ)、fix なし。実装差分ゼロなので変異 matrix は免除。
- **実測 (同一 fixture、5 round 交互、失格 0):** A (現行 `add -A` + commit + production 形 status) 中央値 10.978 秒、
  C1 (source 側の OID 選定 0.38 + blob だけの pack 移送 6.48 + `add -A` 2.15 + commit + status) 9.296 秒、C2 (移送 + index-info +
  write-tree + commit-tree + 明示 refresh 2.09 + status) 8.919 秒。対差 C1 − A は 5 round とも負 (中央値 −1.682 秒) → 事前登録の規則で
  **改善候補**。ハッシュ走査の参照値 2.094 秒は C2 の refresh 2.09・C1 の add 2.15 と同程度。「0.61 秒」相当の index-info + write-tree +
  commit-tree は 0.26 秒で、C2 (参考費用) にはこれに refresh と移送が乗る。移送は `--window=0 --depth=0` で wall 6.48 秒 / 子の user CPU 7.7 秒
  (既定の delta 探索は 10.09 秒 / 33 秒)。
- **副産物 (scope 外):** fixture 全体を test 用に `copytree` した複製先で production 形 status を連続 2 回走らせると 2.147 / 2.14 秒
  (元 fixture では 0.06 秒。stat が外れて再走査する説明と整合、件数・実テスト内の回数・refresh 後は未測定)。`.git` の複製は loose 22k file
  0.89 秒 → pack 0.17 秒、fixture 全体の複製 2.35 → 1.61 秒。
- 棄却・限界: 受入 wall の変化と D357 / D1260 の達否は未測定 (1 job・1 node・同一 tip の base 計測、受入の対比較ではない)。cold は作れない。
  C2 は参考費用で他の自己完結経路の下限ではない。段 6 review (must-fix 3) は本文の限定文の修正で全採用、probe 再走なし。
- 採否はユーザー裁定へ返す (README §8: (a) 採用 wave / (b) 見送り。推奨 (b) — 効果量に対して検証費用が大きいため。scope 外候補 2 件:
  複製先 status の再走査、移送 + `checkout-index` で複製の置換。いずれも未測定部分あり)。
- 工数: codex 3 本 (consult 1、author 1、review 1)、review の 1 本目は launcher が `--reasoning` を review 段へ渡して rc=2 (DW-C01 の
  自分の適用漏れ、新 tag で再投入)、計算ノード job 1 本。

## 次の一手差分

### 更新

- [T-2709] **P2・ユーザー裁定待ち (採否)**: 必要 blob だけの移送 (C1) は計算ノード bnode007・local xfs・同一 tip で base 1 回 −1.68 秒
  (15%、5/5 round、事前登録で改善候補)。受入 wall の変化と D357 / D1260 の達否は未測定。
  `output/insights/2026-09-20/t2709-blob-transfer-cost/README.md` §8 の (a) 採用 wave (fixture の `add -A` 直前に選定 + 移送、
  fallback、変異 §8-3、実受入の対比較) / (b) 見送り。推奨 (b) (効果量に対し検証費用が大きい)。
  scope 外の候補 2 件 (§8-2、未測定部分あり): 複製先で production 形 status が連続 2 回とも 2.14〜2.15 秒 (実テスト内の回数・refresh 後は未測定) /
  移送 + `checkout-index -u -f` で `output/` 複製 (D2086 で 52.9 秒) を置換する経路。
  base: 165b4532ad3ea3bbfe1a71f289ed43a27f219f1b152ab9c28a3b7cbe28b5071f
