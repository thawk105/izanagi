---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t673-d-guard-measurement
seq: 2
---

## 新規

### {{F:preregistered-nodes-need-runner-scope}}. 事前登録の期待 node を別 runner 範囲から流用し、変異 26 件を判定不能にした [手順漏れ]

- 事象: [T-673] 残余 (3) の計測 wave で、先行 wave の *focal 4 node* 実行から写した
  `expected_nodes` を、runner にはテストファイル全体 (77 node) を渡す arm へそのまま登録した。
  範囲が違うので該当 arm は全件 `MISMATCH` になり、F 系 3 arm 26 entry が判定不能になった。
  同 wave の別誤り ({{F:guard-preempts-later-diagnostics}}) と合わせて第 1 巡 77 entry のうち
  47 entry を再走した。実害は再走コストだけで、誤った結論は 1 件も出ていない
  (harness が fail-closed で止めたため)。
- 根本原因: 変異 spec には runner 対象範囲を書く field が無く、期待 node 集合 (spec) と
  runner argv (実行スクリプト) が別の場所にある。両者が対であることを機械検査する経路が無い。
  先行 wave は focal 用と full-file 用の spec を分けて回避していたが、その理由はどの台帳にも
  reference にも記録されておらず、暗黙知だった。
- 恒久対応: 発火段 (段 4 の事前登録) に対応する `DW-M01` は L1 層で **予算残 0 bytes** のため
  reference へ統合できない ([T-627]・[T-673] 先行 wave に続き 3 波連続)。裁定 §56 (7)
  「T-700 (b) 規範下で L2 か台帳」に従い、本エントリと memory
  `mutation-expected-nodes-need-runner-scope` を恒久対応とする。
  機械側の防壁は既存の `MISMATCH` fail-closed (harness が status を kill と読み替えず停止する) で、
  本件でも実際にここで止まった。
- 再発検知: arm ごとに `summary.matching == summary.registered` かつ `MISMATCH == 0` を要求する
  (`check-ledgers.py` 相当の照合)。範囲違いは必ず全件 MISMATCH として現れる。

### {{F:guard-preempts-later-diagnostics}}. 新設 guard が後段の診断を先取りする経路を事前登録で数え落とした [恒真ゲート]

- 事象: 同 wave で、走査完全性 guard を loop 直後に置いた変種に対する期待 node を
  「不正行の位置が `pos ≥ N` のときだけ診断が変わる」という規則で導いた。実際には
  **前段 (量化点 G) の guard が発火すると後段 (量化点 P) の loop 自体が 1 度も走らない**ため、
  P 側の意味的診断は位置によらず全部走査診断へ置き換わる。8 entry が `MISMATCH` になった。
- 根本原因: 新設 gate の変異設計で「その gate が何を検出するか」だけを数え、
  **その gate が fail-closed したことで到達しなくなる後段の検査**を数えなかった。
  gate は通過時には何もしないが、発火時には後段の観測点を丸ごと消す。
- 恒久対応: 発火段 (段 4) の `DW-M01` は L1 予算残 0 のため統合できない。本エントリと memory
  `new-gate-mutations-count-preempted-checks` を恒久対応とする。既存の機械防壁は
  `MISMATCH` の fail-closed で、本件でも規則をコードから導き直して再走する契機になった
  (kill への読み替えはしていない)。
- 再発検知: 同上。期待と観測の食い違いは `MISMATCH` として必ず露出する。

### {{F:fold-dryrun-before-acceptance}}. fold の dry-run を受入の前に通さず、stale な carry で land が止まり受入 1 回分を空費した [手順漏れ]

- 事象: [T-673] 残余 (3) の wave で、worklog fragment の `### carry` に `[T-737]` を書いたまま
  受入全走 (524 秒) を通して land したところ、`tools/dev_wave_land.py` が rc=26
  `candidate fold planning failed: SpoolValidationError: active でない操作対象: [T-737]` で停止した。
  [T-737] は本 wave の走行中に別 session が land して active でなくなっていた。
  fragment を直すと tip が動くため、**受入全走をもう 1 回やり直す**ことになった。
- 根本原因: fragment の妥当性 (carry 対象が active か、placeholder が解決するか) は
  `tools/spool_fold.py --dry-run` で land 前に検査できるが、受入全走はこれを検査しない。
  一方 land は tested tip と HEAD の一致を要求するので、**受入の後に fragment を直せない**。
  この 2 つの制約の交点に、順序の落とし穴がある。
- 恒久対応: 記録 commit の直後・受入投入の前に `python3 tools/spool_fold.py --dry-run` を通す。
  memory `fold-dryrun-before-acceptance` を恒久対応とする (発火段 段 7 の `DW-S07` は L1 層で
  予算残 0 bytes のため reference へ統合できない)。
- 再発検知: dry-run の `status` が `planned` 以外なら受入を投入しない。stale carry は
  `SpoolValidationError` として必ず露出する。
