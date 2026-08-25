---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t822-evidence-gaps
seq: 1
title: [T-822] 正式受入が 6 report の計測対象の同一性を要求するようにした (コード + テスト、branch worktree-dev-wave-t822-evidence-gaps、変異 matrix = baseline PASSED・6/6 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **親の段 1 前提は誤っており、段 3 が救った。** 親は段 0 の実測から「D863 の 3 件は
  2026-08-17〜18 に実装済みで既に閉じている」と brief に書いた。根拠は
  `assert_campaign_layer3_chain` が acceptance から呼ばれていること、
  `acceptance-arm-execution` が arm を再導出していること、`measurement_head` の
  6 件一致検査があること、判定器で C02 / C09 / C10 が合格終端に達していることだった。
  段 3 レンズ A がすべて原典で反証し、親が逐語で裏取りした。
  **誤りは「呼び出しが存在すること」を「保証が発火すること」と同一視した点である。**
  段 3 を省いていれば、閉じていない条件を閉じたと台帳へ書き、正式系列の起動条件を
  誤って解除していた。詳細は {{F:call-site-mistaken-for-guarantee}}。
- 反証の中身。層 3 鎖の呼び出しは必須経路ではなく、`do_build=False` は関数を呼ばずに進み、
  campaignless failure cell は呼んでも `continue` で鎖検証へ到達しない。
  既存テスト `test_s8c_acceptance_failure_cell_pins_layer3_chain_absent_reason` が
  この迂回を含む束の受領証発行を逐語で固定していた。
  さらに契約 C09 の「no-build を certify しない」保証は**恒真**である —
  受領証は `certifying is not False` の無条件拒否により構造上つねに非 certifying で、
  何も certify できない以上その保証は自動的に成り立つ。
- **段 2 プランの芯を不採用にした。** 段 2 は世代数の独立再導出先として
  `loop_state.json` の `iteration` を選んだが、原典自身が「checkpoint は WAL でなく
  loop 状態の投影 — 正本は WAL」「iteration 整合・campaign/run origin は検査しない」と
  明記している。同じ走行側が書いた値どうしの照合を独立再導出として記録すると
  恒真な保証になるため実装しなかった ({{D:same-producer-projection-is-not-independent}})。
- 代わりに D863 第 3 条件を実質的に閉じた。従来の受入は 6 report が同じ
  `measurement_head` を持つことだけを要求し、**何を計測したかを一切照合していなかった**
  (`trial_registry.py` に `ccbench` と `env_tag` の出現は 0 件)。
  6 セルが別々の CCBench source を別々の環境で計測した束も受理された
  ({{D:acceptance-must-check-what-was-measured}})。
- 変異 matrix の運用で harness の起動条件に 5 回はじかれた。argv への `-rf` 必須、
  spec は試験対象 checkout の外、spec の key は `schema` + `timeout_seconds`、
  作業ツリーが固定 HEAD と一致 (= 実装 commit が先)、untracked file ゼロ。
  いずれも起動前には気づけず、都度 1 往復を要した ({{F:mutation-harness-preflight-serial-rejects}})。
- 最終巡は M02 で `PARSE_ERROR` 停止した。rc=1 だが計算ノードの stdout から failed node を
  確実に抽出できなかったもので、**変異でなく捕捉側の失敗**である (同じ M02 は probe 巡で
  node 1 件の KILLED だった)。`--resume` で続きから再開して完走した。
- M06 (過剰拒否を検出する正例) は probe 巡で MISMATCH になった。発火自体はしていたが
  赤 node が 6 本で、親が登録した期待集合が 1 本の部分集合だった。DW-M08 の
  probe → 再登録手順に従い実測 node で登録し直した。
- 子の工数: codex 8 本 (plan 1・consult 2・author 1・review 2・fix 2)。
  全て `launcher_rc=0`。model は全段 `gpt-5.6-sol`、reasoning は `xhigh`。
- 段 6 レビューは本体 gate・受領証不変性・禁止編集面のいずれにも must-fix を認めなかった。
  must-fix 2 件は「層 3 レポート 0 件の負例が無く恒真化回帰を検出できない」と
  「拒否時のエラーが trial / 値 / path を示さず診断不能」で、どちらも fix で閉じた。
- 稼働中の別 wave (t1176-t1230) が `autonomous_trial_completeness.py` を編集中だったため、
  同 file を 0 byte のまま保つ設計に寄せた。段 6 レビュー両本が差分で確認している。

## 次の一手差分

### 更新

- [T-822] **P2・裁定済み (2026-08-25 /rulings 全件、推奨どおり) → 一部実装済み**: 択 (a) 採用 —
  8c 正式受入の証拠欠落 3 件を閉じてから正式系列へ入る。
  **第 3 条件 (レポート間で計測対象の一致) は閉じた** — 受入が層 3 レポートを再読して
  `meta.ccbench_commit` と `env_tags` の 6 件一致と母数下限を要求する。
  第 1 条件 (層 3 鎖の必須経路化) は迂回を hard failure にするかが設計択一のため
  {{D:formal-acceptance-incomplete-bundle-choice}} でユーザー裁定待ち。
  第 2 条件 (宣言 arm から実 CCBench source への因果束縛) は producer / completeness 側の
  変更を要し、稼働中の別 wave が同 file を編集中のため未着手。
  base: 97e012010815c69d9681df8875908d2872e6456f42b29dbb0b1a796daf422a48
- [T-1211] **P2・実装方針が確定**: 受入の世代数検査が report と journal の自己整合からしか
  値を得ていない件。campaign tree 内の `loop_state.json` は同じ走行側が書く投影であり
  原典自身が「正本は WAL」と明記しているため、独立再導出の錨にならないことを実測で確定した。
  本タスク自身の記述どおり**外部 immutable anchor が要る**。open のまま残す。
  base: 412cccd09f58717d2ffa691c9bd8fe36deae87efdb0f742692d249c963fa3e4c
- [T-1135] **P2・起動条件が明確化**: 正式系列の投入タスク。判定器の実測で、
  実際の残 blocker は D863 の 3 件ではなく C03 (`manifest-registry-proof-undefined`)、
  C05 (`schedule-schema-absent`、`output/s8c-preregistration/schedule.v1.json` が不在)、
  C08 (`prereg-binding-proof-undefined`)、および T-468 (承認権限の不在。受領証は
  構造上つねに非 certifying) であることが分かった。
  base: 52e5fc89b856d2c8ca07076c20c588a4ccdb2114dc745bd948b81528c94a96e2

### 新規

- {{T:formal-acceptance-standalone-verifier-rederivation}} **P2・新規**: 追跡済み受領証を読む
  standalone verifier が、報告・manifest・層 3 参照・checkpoint を再読しないため、
  発行時の保証が受領証の耐久保証にならない。任意の leaf digest を持つ受領証でも
  `verify_acceptance_receipt` が成功する。段 6 レビュー B 所見 3 が原典付きで指摘した。
- {{T:formal-acceptance-arm-to-source-causal-binding}} **P2・新規**: 宣言 arm から
  実際に build・bench された CCBench source への因果束縛が無い。proposal bytes は hash
  されるだけで WAL source・trigger binding・variant と比較されず、走行側が整合した
  payload / proposal 一式を残しつつ別の有効 source を build した WAL を作れる。
  D863 第 2 条件の実体。producer / completeness 側の変更が要る。
