---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-04
wave: dev-wave-t2227-noinline-meaning
seq: 1
title: [T-2227] BACKOFF_NOINLINE の意味の節を枝選択 witness で確立し、未確立のまま paper へ通る形を狭めた (コード + テスト + insight、branch worktree-dev-wave-t2227-noinline-meaning、変異 10/10 KILLED + 等価 1 SURVIVED)
---

## 本文

- ユーザー裁定 D1569 を実装した。`BACKOFF_NOINLINE` を枝選択 witness の登録簿へ header 所有
  (`include/backoff.hh`) で登録し、宣言は registry factory からだけ出す。旧宣言型と CLI は
  `BACKOFF_FIXED` 固定のまま。配線は D1492 に従い A-2 (paper)、s1_direct_comparison、t1683 cost probe
  の 3 面。配線しない driver と理由は insight の表。
- **段 1 の実測で、引数の前提 2 点が現物と違った。** (a) 指令は所有 TU でなく header にあり、現行の
  shadow tree (祖先 symlink) では計装が見えない。深い鏡像 (全 dir 実体・file symlink) へ拡張した。
  (b) A-2 の要求値は既定と同じ 0 で、現行 factory (要求 1・既定 0) では登録しても未確立一覧が縮まない。
  要求 0 では値 1 を対照値として観測する形を {{D:inert-request-contrast-value-branch-witness}} として
  記録した (D1490 は AI 決定であり、D1569 を満たす実装が他に無い。ユーザーが覆す revert 点は factory の
  条件 1 行)。
- **既受理成果物への影響は repo `output/` 内で空集合** (実 admission record 0 件、A-2 の実走 2 回は
  driver_rc=2)。repo 外の保存先は未走査で、主張はその範囲に限る。
- 段 3 の敵対相談が実在の副作用を 1 件出した: 登録簿へ足すと供給の節 `shared_branch_build` が
  cache route の同 macro (要求 1) を `compile-command-unavailable` で落とす。共有 build root を
  CMAKE_CXX_FLAGS route に限定して閉じ、要求 1 の供給正例を登録した。同相談は D1492 に raw 除外が
  無いことも指摘し、brief の raw/promotion 境界を撤回して t1683 probe を配線先へ戻した。plan の
  「依存 file で計装 header の実読を要求する検査」は本題外の新防壁として削った
  (読まれなければ両観測 (0,0) で既存の非識別判定が red にする)。
- **段 4 で配線先に s1 を足した際、s1 について path の pin 閉包 (DW-O09) を引き直さなかった。**
  consumer 焦点走 39 file で 3 赤: s1 の file 全体 sha256 を焼き込む reviewed spec の独立 golden
  (`test_s8b_oracle_manifest.py`) と `run_role` の build sink 行番号 pin (`test_ccbench_spawn_sites.py`)。
  いずれも同一性 pin の追随で、先例 2e62753a7 と同じく literal 側で閉じた (fix 子 1 本)。
  key 名でも値の字面でも見つからない型で、配線先を追加した時点で閉包を引き直すべきだった。
- 実 patch 木 dogfood (計算ノード、二段 include・Masstree・実 `-I`): 要求 0/0 で requested (0,1)・
  default (1,1) の green、要求 1/0 で意味・供給とも green、admission true。
- 実装しなかった所見: 宣言 object の発行元 capability (D1491 を object 同一性で実装する案) と
  依存 file 実読検査。いずれも受理集合を変えない新防壁で scope 外。
- 工数: codex 子 = plan 1、consult 2、author 1、review 2、fix 1、focus 1。計算ノード dispatch =
  単独走 4、focus 1、dogfood 1、再走 1、変異 probe 1 + 本走 1 (各 12 走)、受入 1。

## 次の一手差分

### 完了

- [T-2227] `BACKOFF_NOINLINE` の意味の節を枝選択 witness (header 所有・対照値観測) で確立し、A-2 / s1 /
  t1683 へ配線した。既受理成果物への影響は repo 内で空集合。A-2 の admission 全体は D1523 取り込み後の
  fresh run で初めて成果物に現れる。
  remaining: none
  base: 98a3efe283c0cb6cc64b41c61b5230a7ae24ce261ddb605fc78abea79910c722
