---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t1748-receipt-leaf-binding
seq: 1
title: [T-1748] 追跡済み受領証の cross-binding leaf を現物から再導出して照合するようにした — 射程は current v5 に限る (コード + テスト + docs、branch worktree-dev-wave-t1748-receipt-leaf-binding、変異 matrix = baseline PASSED・KILLED 8・SURVIVED 0・MISMATCH 0・期待 node 完全一致 8/8)
---

## 本文

- **依頼本文の出典が誤っていた。** 引数は「段 6 レビュー B 所見 3 が原典付きで指摘した」と書くが、
  worklog 959 の段 6 レビュー B の所見 3 は「完全 build 束の母数 6」で別件である。実体は同 wave の
  **段 3 レンズ B** (`output/insights/2026-08-25_t822-evidence-gaps/verbatim/s3-lensB.md`) と
  段 3 レンズ A の記述だった。主張内容そのものは原典に逐語で存在したので対象は変えていない。
- **親の段 1 前提が誤っており、親自身の実測で反証した。** brief は (P1-b) として
  「build mode では campaign 現物に到達できないので完全な再導出は不可能」と書いたが、
  `verify_s8c_cross_binding` の 4 引数はすべて追跡済み受領証から復元できる
  (`run_root` = attempt journal の解決済み path の親、`output_root` = その親の親で、
  発行側が両者の一致を強制済み)。段 2 と段 3 レンズ B が独立に同じ結論へ達し 3 者一致した。
  これにより成果物を増やす案 (leaf の preimage を sidecar として永続化する) は不要になった。
- **段 3 レンズ A の唯一の must-fix は射程不一致で、実装を広げずに閉じた。** 修正は current v5 に
  だけ効き legacy v3/v4 は aggregate のみのままである。legacy は唯一の production consumer
  `layer3_report.build_accepted_report` が `require_current_verified_receipt` を通し同関数が v5 以外を
  無条件拒否するため下流 capability へ到達せず、当時の campaign 現物を要求すると過剰拒否になる。
  実装を広げるのではなく、docstring と本記録で射程を明記する形で閉じた。
  **「`verify_acceptance_receipt` 全体で任意 leaf が通らなくなった」とは書けない。**
- **段 6 レビュー B が正例の恒真性を正しく切り分けた。** `_upgrade_to_current` が作る no-build 正例は
  production と同じ計算を同じ引数で 2 回やっているだけで、それ単体では引数導出の正しさを証明しない。
  意味を持たせているのは materialized build 側の正例で、発行経路と検証経路が別々に引数を導く。
  変異 M7 / M8 がその正例だけを殺すことが、穴が埋まっている実測である。
- 段 3・段 6 の敵対レビューは合計 4 本で must-fix は段 3 レンズ A の 1 件のみ。段 6 は 2 本とも 0 件。
- 手落ち 3 件を {{F:mutation-probe-file-scoping}}、{{F:mutation-timeout-vs-queue-override}} に記録した。
  M5 の初回登録が過剰決定だった件は `DW-M03` に従い M5b へ差し替えて単一理由に絞り直した。
- 計算ノードが終始混雑しており、実装子は pytest を 1 件も走らせられなかった (`rc=16`)。
  テストの実測はすべて親が行った。login node の負荷は一時 21 まで上がり、変異 probe の
  1 走が 26 分かかった (CPU 時間は 35 秒で、ハングではなく順番待ち)。
- 子の工数: codex 6 本 (plan 1・consult 2・author 1・review 2)。全て `launcher_rc=0`。
  model は全段 `gpt-5.6-sol`、reasoning は plan / consult が `xhigh`、author / review は docs 権威導出。

## 次の一手差分

### 完了

- [T-1748] current v5 の cross-binding leaf を現物から再導出して照合するようにした。
  射程は current v5 に限り、legacy v3/v4 は aggregate のみのままとする (下流 capability へ
  到達しないため)。負の対照は leaf 1 本を差し替え aggregate も辻褄を合わせた受領証を拒否する。
  remaining: none
  base: f8e757525af3c8be756627e440370ecba7e0bb4c3db24ef9c8e10a62f48beec3
