---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2304-pin-advance
seq: 1
title: [T-2304] ccbench pin を 511c9538 から候補 e9e477ca へ前進した — 3 点同一 commit・生成物形の再実測・policy epoch の test 追随、D2150 前提の射程を限定 (コード + docs、branch worktree-dev-wave-t2304-pin-advance)
---

## 本文

- **前提実測 (13:17 JST):** GitHub `thawk105/ccbench` だけを取得元とする single-branch fresh clone で候補 `e9e477ca1b55348ab4530de0b1cf663ce4555290` を取得、`511c9538` は祖先 (間 4 commit)、差分は `cc/mocc/transaction.cc` の 141 行追加のみ。D2150 項 1 (ii) の人間 push は成立していた。
- **実装 (Codex author 1 本 + fix 3 本):** gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` を同一 commit で更新 (`827682b60`)。⑦ は 2 層 — 現行 pin の literal 7 行 (群 A) と、**admission policy の epoch 移動** (`build_admission` の preimage に `repo_stock_pin=CURRENT_PIN` → policy sha `949ddcc2…` → `db6bc9ea…`) に伴う golden の追随 (`ad966d12f`、`225eba818`。旧 epoch は歴史 golden として保持、T-816 と同型)。旧 pin を control・凍結・比較 base・歴史 fixture とする 43 行と `p3_s4_loop.py` の独立 full OID は据え置き。t2187 probe の `PIN_FULL` は同 probe が `CURRENT_PIN` 一致を自ら要求するため追随。
- **④ 再実測:** 計算ノード bnode019 (CMake 3.25.0、configure TRACE=0/1 + `ycsb_mocc.exe` build、26 秒) と login (3.25.0 / 3.22.1、configure) で production の 2 check 関数が実 build dir に対して OK。T-1997 と同形。
- **焦点走 (計算ノード、61 file):** set1 6541 passed / 104 failed / 75 errors → fix 後 set2 1 failed → set3 **6720 passed / 31 skipped / 0 failed**。
- **敵対レビュー 2 本 (must-fix A 4 件・B 1 件、すべて real・採用):** 分類誤り 3 行 (実 checkout 照合・現行 builder golden)、policy sha / campaign ID の追随漏れ、④ は 3.25.0 限定の主張に留めること (その後 3.22.1 も実測して解消)、**policy sha の波及が D2150 の「独立 full OID と旧凍結の保持で影響なし」前提を覆す** (下記)。
- **新事実と裁定 ({{D:pin-advance-policy-epoch}}):** 旧 policy の binary / lock は新 main から live 消費できず (`s8b_binary_admission`・`LaunchValidatedFreeze`・floor resume・`ident` の旧 lock 拒否)、`resolve_current_floor_protocol()` は新 gitlink で fail-closed (候補 2 件・head exact 0)。相談 2 本 (設計・決定 / 最強の反論、`--lane luna`) が独立に同じ結論 = **O2**: 候補の正しさは否定されず稼働中 attempt (固定 submit-tree) は止まらないので承認範囲を維持して続行し、land は並行 wave [T-2724] (凍結 v2 g1 の A/X) の land 完了 tip が local main に含まれてから。「裁定へ返す」は採らない。D2150 の逐語は書き換えず、射程を限定する事実を新 D として追記。
- 旧系列 (K2 の巡・A-1 sized v3・凍結 g1 chain・B-4 床値の旧 binary) は pin 前進前の superproject と対応 submodule・旧契約の固定 checkout から走る。新 main への移行は系列ごとに ② ③ ⑤ と source / admission の整合が要り、旧 binary の再 admission だけでは足りない ({{T:pin-epoch-series-migration}})。
- 素材: 材料 §4.1 ①④⑦ の実体、pin 前進で動く identity の層 (campaign ID・cache key・builder bytes・receipt) と動かない層 (較正 record・凍結 protocol・比較 policy・歴史 golden) の区別は `output/insights/2026-09-20/t2304-pin-advance/README.md` §1〜§4。
- **変異 matrix (独立 clone、main = 225eba818):** MUT-1 (`CCBENCH_FULL_SHA` 退行) KILLED 13 node、MUT-2 (`CURRENT_PIN` 退行) KILLED 21 node、MUT-3 (等価 comment) SURVIVED、baseline PASSED。事前登録の killer は部分列挙だったので初回を probe と明記して観測 node で final を再登録 (DW-M08)。
- 工数: codex 子 8 本 (author 1・review 2・consult 2・fix 3)。計算ノード job: generic 1・焦点走 3・変異 2 (probe2 + final)・受入。受入・land の結果は job dir の receipt (insight §6 に手順)。

## 次の一手差分

### 完了

- [T-2304] gitlink・CCBENCH_FULL_SHA・CURRENT_PIN を同一 commit で候補 e9e477ca へ前進し、④ の再実測と ⑦ の追随 (policy epoch 込み) を完了、land 済み。
  remaining: none
  base: 407ce828ad9743b506c15ca5849b3a5fe98e655737b978fa18ebe461959076a7

### 新規

- {{T:pin-epoch-series-migration}} **P2・新規 (D2150 項 1 の ②③⑤ の実体化条件)**: 新 pin の main から K2 の巡・A-1 sized・凍結 v2 g1 の launch・B-4 床値の binary 再利用を再開・再投入する前に、系列ごとに ② 新登録と identity、③ driver の pin (`p3_s4_loop.py` の D1936 独立 full OID 等)、⑤ successor floor protocol (AI reseal)、source / admission (policy epoch `db6bc9ea…`) の整合を揃える。それまで旧系列は pin 前進前の superproject commit と対応 submodule の固定 checkout (submit-tree) から走る。旧 binary の再 admission だけでは旧 lock の継続も source pin の不一致も解消しない ({{D:pin-advance-policy-epoch}}、insight `output/insights/2026-09-20/t2304-pin-advance/README.md` §4)。
