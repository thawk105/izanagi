---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2515-rr5-accepted-calibration
seq: 1
title: [T-2515] write-heavy (rr5) の accepted 認定較正を取得し、t48 / pegasus の 3 workload セルを揃えた (docs 1 file + output 成果物のみ、branch worktree-dev-wave-t2515-rr5-accepted-calibration、実装面の差分 0 なので変異 matrix は DW-S04 により免除)
---

## 本文

- **依頼の前提 2 つのうち 1 つが一次資料と食い違い、作業を行わなかった。** 依頼は branch
  `worktree-dev-wave-t2515-calib-rr95-rr5` (tip `559bcbc29`) の未着地 6 commit の回収を求めたが、
  内容で照合すると回収は完了済みだった — `35a740cd4` が 5 commit の必要差分を合成し、
  2026-09-15 の `worktree-dev-wave-t2515-record-recovery` が残り 17 file を byte 一致で回収し、
  `559bcbc29` の conftest 部分は T-2579 が実装していた。さらに `3dbf7ea1d` の条件関門 argv 修正は
  D1936 項 6 が `run_condition_gate` ごと撤去したため対象が消滅していた。`git cherry` が 6 件とも
  `+` を返すのは patch-id 判定だからで、着地判定には使えない。
- **段 2 プランの「実装面が必要」という結論を、親が実走で反証して不採用にした。** プランと段 3
  レンズ B はいずれも `test_probe_output_v1_corpus_is_exact_and_replays_all_physical_copies` が
  新しい attempt の追加で赤になると静的読解で判定したが、この node は
  `orchestrator/tests/growth_test_holds.py:300` に登録済みで、実走すると skip される
  (`{"collected_hold_functions":1,"opted_in":false}`、1 skipped)。両子とも pytest 未実走だと
  自ら明記していた。
- **ただし「hold で skip される」は「整合性を確認した」ではない。** 段 3 レンズ A の指摘を採用し、
  投入前から 6 件あったコーパス乖離と本 wave の増分 1 件、および hold の `collateral_note` が
  同時に止める検査 (固定件数 48・成功/失敗集合の非交差・JSON pair の完全分割) を insight へ記録した。
  hold の解除条件は explicit-user-command-only なので触っていない。
- **段 3 レンズ A の 4 所見と レンズ B の 7 所見を real として採用した。** とくに、却下試行の
  CV=0.013535 は N=1,000,000 の値であって新しい選択点 N=2,000,000 の品質を裏づけないという指摘
  (レンズ A [1]) を受け、insight では「旧系列への規則適用 (予測)」と「今回の測定」を別表に分けた。
- **親が投入前に旧系列へ現行選択規則を当てる probe を repo 外で走らせ、生死確認とした。** probe は
  N=2,000,000 / `cache_floor_warning=False` を返し、本走の実測も同じ N=2,000,000 を選んだ。
  ただし probe が示せるのは「旧系列なら選択警告が解消する」までである。
- **先行 3 本と同一の実行物ではなかった。** `certify_calibration.sh` の SHA-256 は
  `08bbc498…` から `3fc75c03…` へ変わっていた (`f5ba28378`)。差分は予約式のコメントと receipt の
  文面だけで `frozen_required_s` と timeout は不変。先行所要 184/177/238 秒は参考値に留めた。
- wave 中に main が 2 commit 進み、第 19 回の裁定 39 項が着地した。段 4 の再走査で内容を確認し、
  項 11 (同条件の較正記録が複数あるときの選別規則) は本件 (rr5 は 1 件目) に当たらないと判定した。
- エージェント工数: codex 子 3 本 (段 2 plan 1 / 段 3 consult 2、いずれも read-only、
  `reasoning=medium`)。実装子・レビュー子は実装面が無いため立てていない。
- 計算ノード job は 1 本 (request `478.nqsv`、bnode013、会計 Elapse 185 秒)。却下時の自動再投入は
  行わない方針で走らせ、却下は起きなかった。

## 次の一手差分

### 完了

- [T-2515] write-heavy (rr5) の accepted 認定較正を
  `output/env/pegasus/calibration/registered/calibration-2b7ba072b88023ae.json` として取得した。
  silo / t48 / pegasus、records 2,000,000、採用点 LLC miss 1.567%、within-run CV 0.97%、
  `quality.status=accepted`、`cache_floor_warning=false`。rr95 と合わせて 3 workload セルが揃った。
  cache floor 0.50% は動かしていない。2026-09-14 の却下記録は却下のまま残した。
  非 silo の rr5 は T-2224 の残件として本 wave の scope 外。
  remaining: none
  base: ee66260992b1cfdacdfed9b5a193c347782afec249f420f3ebb0b036bb778175
