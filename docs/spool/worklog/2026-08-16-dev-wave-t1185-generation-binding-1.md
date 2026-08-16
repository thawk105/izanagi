---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1185-generation-binding
seq: 1
title: 8c 正式系列の exact G=2 を manifest 宣言と受入・起動の突き合わせで機械強制する (コード + docs、branch worktree-dev-wave-t1185-generation-binding)
---

## 本文

- 8c 正式系列の事前登録は「各 cell を正確に `G=2` で起動する」を起動形の責務として既に規範化して
  いたが、それを機械で確かめる経路が無かった。承認上限 `MAX_APPROVED_GENERATIONS = 2` は
  **上限しか強制せず**、予算 validator は 1 以上を受理し、CLI 既定値は 1 である。したがって
  budget=1 の 6 cell が manifest 登録・launch binding・完全性検査・受入 gate をすべて通過できた。
  [T-324] の裁定 (budget=1 の結果を workload 特化合成の証拠に数えない) が機械側で一切
  強制されていなかった。本 wave はその裁定を機械へ落とす。設計判断は {{D:generation-binding}}。
- **段 2 プランの中心案を段 4 で不採用にした。** プランは正式受入で partial report を拒否し、
  `report.cells` をちょうど 1 個へ狭め、`stop_reason` を `fixed-generation-budget` だけに閉じ、
  `test_p6_partial_terminal_outcomes_are_reported_not_dropped` の期待を反転する案だった。
  段 3 レンズ A と親の独立所見が一致して、これは [T-325] が塞いだ file-drawer を受入側で
  開け直す設計だと判定した。一方で受入 receipt の `certifying` は literal `False` 固定なので、
  「exact 2 でなければ non-certifying にする」だけの案は受理集合を 1 bit も変えず恒真になる
  ([T-1132] / F341 と同じ型)。両立解として **budget (宣言・起動意図) と actual (実際に起きたこと)
  の間に線を引く**裁定を採った。詳細は {{D:generation-binding}}。
- **親 brief の成果物影響に誤りがあり、段 3 の両レンズが独立に訂正した。** brief は
  「G=1 でも受入 receipt の `certifying` が真になりうる」と書いていたが、
  `trial_registry.py` の admission は `certifying is not False` を拒否し、receipt emitter は
  literal `False` を出し、`layer3_report.py` は certified-selection consumer が未配線の
  fail-closed entrypoint だと明記している。実際に起きるのは「G=1 が non-certifying な正式
  receipt の accepted trial 行へ入る」までである。本 wave の値は「今 certified が汚染される」
  ではなく「将来 certifying を結線するときの前提を、証拠がまだ無いうちに閉じる」であり、
  この格で記録する。
- 段 3 レンズ B は影響半径を理由に「schema bump も binding 伝播も不要」と判定し、
  親はこれを採って plan v2 を最小構成にした。プランの 132 base nodeid 見積もりは
  レンズ B が独立に数え直して一致したが、採った最小構成では実際の変更は
  6 ファイル (+388/-61) に収まった。`TrialBinding` / launch admission / lifecycle /
  受入 receipt への伝播、run/report の v3/v4 tagged union、`s8c_acceptance_receipt.py` の
  変更はいずれも見送った。
- 段 6 の敵対レビュー 2 本は **blocker 0 件**。レンズ B の must-fix 1 件を real と裁定して
  fix 子を投じた — originless 互換 golden の投影が第 2 世代を**比較前に**削除しており、
  key 構造は assert していたが値は未検査で、origin binding の有無で G2 の値が食い違う回帰が
  golden でも `_assert_same_structure` でも赤にならなかった。fix はテスト 2 ファイルへの
  純増 118 行・削除 0 で、production は無変更。レンズ A の nit (起動側 gate の順序が
  `build_run_context` に対して未固定) も同じ子で閉じた。
- **変異 M2 は段 4 で登録を取り下げた。** `type(generations) is int` を `isinstance` へ緩める
  変異は、`bool` が `True == 2` で偽になるため後段の `== 2` に先取りされ、単一理由にできない
  (DW-M01 / F28)。**M4 も取り下げた** — 「先頭 1 件だけ検査する」変異を単一理由の置換として
  書けず過剰決定になるため。全件走査の検出力は M3 の負例が**末尾**の cell に不一致を置くことで
  担保されることを実コードで確認した。
- 変異 matrix は **KILLED 4/4、MISMATCH 0、SURVIVED 0、TIMEOUT 0**
  (`mutation-ledger-v2.json`、spec sha256 `ce01af17748c1687702d4fc530e6fa3ff8031bb119b61eee56a508ea541345d5`、
  repo_head `03172bd39afce5d42a945df2078a8c045598918a`)。過剰拒否の正例は期待 node の完全集合を
  手計算できなかったため初回を probe とし、実測 94 node を再登録して再走した (DW-M08)。
  probe 台帳は `mutation-ledger-probe-erratum.json` として保全した。
- 実測は login node の bounded local が 2 回とも rc=16 で止まった
  (`bounded scope の memory.max / memory.oom.group を走行中に attest できない` =
  dispatcher infrastructure failure でテスト結果ではない)。以後は
  `tools/run_tests.py --force-dispatch` で計算ノードへ投入した。
- 焦点走の実測 (すべて計算ノード): 実装直後 149 passed → fix 後 316 passed (4 ファイル) →
  [T-1184] land 後の統合 merge 後 694 passed (6 ファイル、T-1184 が触った
  `test_s8c_preregistration_core` / `_predicates` を含む)。
- **[T-1184] wave との並行を実測で追跡した。** 本 wave の起動時 (13:53) には T-1184 の
  worktree も process も無く「重複なし」と判定したが、その後に立ち上がり 16:11 に land した。
  ファイル重複はゼロで、T-1184 が規範本文・証拠契約・第 3 世代の凍結記録を、
  T-1185 が同じ規範を機械側へ落とす側を持つ分担になった。本 wave は
  `docs/phase3-8c-preregistration.md` を 1 行も触っていない。
- 段 3 レンズ B が既存欠陥を 1 件見つけ、親が独立に確認した。受入 receipt の emitter は
  条件付きで `origin_terminal_projection` を trial 行へ足すが、parser の `_TRIAL_KEYS` は
  単一の exact key set でそれを拒否する。**origin 付き正式 report は、受入が書いた receipt を
  自分の parser が読めない。** 本 wave とは独立の既存欠陥なので
  {{T:receipt-origin-projection-key-mismatch}} として起票する。

## 次の一手差分

### 完了

- [T-1185] 8c 正式系列の exact G=2 を機械強制した。manifest / registration schema を v2 へ上げて
  trial 行へ `generations` を足し値を整数 2 に閉じ、受入は 6 report 全件で宣言値と
  `generation_budget_per_workload` の一致を要求し、registered 起動は runtime の generations が
  manifest 宣言値と一致しなければ campaign identity 導出と run root 作成より前に拒否する。
  partial の受理、exploratory の受理集合、CLI 既定値 1、承認上限 2 はいずれも不変。
  remaining: none
  base: b45af3b7175643966e74eb752c9924cc6678da68dc38974cd415b8209cbbf772

### 新規

- {{T:receipt-origin-projection-key-mismatch}} **P2・新規**: 受入 receipt の emitter が
  条件付きで足す `origin_terminal_projection` を、parser の単一 exact key set が拒否する。
  origin 付き正式 report では受入が書いた receipt を自分の parser が読めない。
  emitter 側を tagged exact-key alternatives にするか、parser 側へ分岐を足すかを決める。
  [T-1185] 段 3 レンズ B が発見し親が独立確認した既存欠陥で、[T-1185] とは独立。
- {{T:acceptance-generation-independent-rederivation}} **P2・新規**: 受入の世代数検査は
  report と journal の自己整合からしか値を得ておらず、campaign WAL / Layer 3 chain を
  独立に再検査していない。証拠契約 `s8c_preregistration_evidence_contract.v1.json` は
  formal acceptance からの Layer 3 chain 再検査を要求している。閉じるには C09 / C10 と
  外部 immutable anchor が要るため [T-1185] では scope 外とした。
- {{T:trial-binding-generation-seal}} **P3・新規・ユーザー裁定待ち**: 世代数を
  `TrialBinding` の封印 capability として持たせるか。[T-1185] は起動時検査が manifest を
  再読して等価性を得るため不要と裁定したが、封印値として持つ方が強いという議論は成立する。
  **択 (a) 現状維持 (manifest 再読)、択 (b) `TrialBinding` へ伝播。親の推奨は (a)** —
  (b) は launch admission の exact key 契約と originless golden の bytes を変えるため、
  等価な保証に対して影響半径が大きい。
- {{T:s8c-runbook-generation-cap-stale}} **P3・新規**: 8c runbook は
  `MAX_APPROVED_GENERATIONS = 1`・「`--max-generations` は 2 以上にできない」と記すが、
  D410 (2026-08-15) が上限を 2 へ上げ、コードも 2 である。運用者が読む living doc が
  実装と逆を指している。所有を [T-1184] 側とするか独立タスクとするかを決めて直す。
