---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t1815-cli-entrypoint
seq: 3
title: [T-1815] 8c 事前登録 CLI の二重実体化と相対 import を直し、実プロセス検査を足した (コード + テスト + docs、branch worktree-dev-wave-t1815-cli-entrypoint、変異 4/4 KILLED)
---

## 本文

F631 が記録した CLI 欠陥を閉じた。設計判断は {{D:cli-transport-repair-is-not-decider-semantics}} と
{{D:real-process-cli-check-uses-synthetic-repo}}、実施記録と逐語は
`output/insights/2026-09-07_t1815-cli-entrypoint/`。

- **`-m` 形式も壊れていた。F631 の記述より欠陥は広い。** F631 は「package として import して
  `main()` を呼ぶと本当の内訳が出る」と書いており、これ自体は正しい。しかし `-m` は `runpy` が
  対象コードを `__main__` の namespace で実行するため、判定器では同じ二重実体化が起きる。
  F631 が独立入口として名指しした gate report の `-m` が動くのは、gate report が `__main__` で
  core を通常の canonical import するからであって、`-m` 形式そのものが安全だからではない。
- **親の追補が測っていない否定を含んでいた ({{F:unmeasured-negation-in-parent-addendum}})。**
  実 repo の全評価が 39〜119 秒という実測は正しかったが、そこから「安く同じ欠陥を踏む方法は無い」を
  導いて子へ渡した。段 3 のレンズ sol が反例を出し、親が実測して確認した。合成 repo なら
  1 走 0.2〜0.3 秒である。**当初案 (最悪 950 秒) を採っていれば、新設検査 1 本で suite の
  5 分上限を超えていた。**
- **レンズ sol の blocker (「`DECIDER_VERSION` を bump せよ」) は親が一次資料で反証した。**
  凍結範囲を変えない世代更新は `spurious-revision` で機械拒否されるため、bump は発行不能である。
  bump を選ぶことは、CLI の起動経路を直すために保護対象文書の改訂を強制することになる。
- **`s8c_gate_report.py` は修正前から `campaign-direct-bootstrap` 規則に違反していた。**
  例外台帳に該当項目は 1 件も無い。赤になっていなかったのは、その test file 全体が growth hold 下で
  既定の走行に入らないためである。本 wave の修正はこの潜在違反も閉じる。**hold は解放していない。**
- **段 6 の 2 レンズが must-fix を 4 件出し、うち 1 件は検出力の問題だった。** 継承 `PYTHONPATH` が
  あると `sys.path.insert` を消しても `orchestrator` が解決でき、事前登録した変異 M4 が生存する。
  閉じた環境へ直し、fix 子が一時変異で `[gate-path]` だけが赤になることを実証した。
  もう 1 件は `--commit` 採用検査が恒真だった点で、合成 repo に第 2 commit を足して閉じた。
- **所要台帳の最初の投入で、本 wave と無関係な未登録 node が 202 件あることが判明した。**
  repo 全体の焦点走 JUnit を渡したため子が 206 件を追加してしまい、**子は要件外と判断して
  変更を破棄し、報告して止まった。** 親が新規 test file 単独走の JUnit を取り直し、4 件だけを
  登録した。202 件は他 wave 由来の既存の未登録分であり、本 wave では触らない。
- **変異は KILLED でなく diagnostic sensitivity pin として記録した** (`DW-M08`)。4 件とも
  受理集合を変えず (`effective` はどの経路でも false)、変えるのは診断出力だけだからである。
  baseline PASSED、M1〜M4 すべて期待 node と観測 node が完全一致した。
  **M3 と M4 には既定走では発火しない第 2 の検出層 (hold 下の bootstrap 逐語検査) がある**ので、
  単一層性は「既定 hold 下で」という条件付きである。
- **機構を強制する構造 pin は作らなかった。** 新設テストは答えを pin するので、alias を足さずに
  結果正規化の型検査を緩める実装でも通ってしまう。ユーザーが「仮想リスク向けの gate・検査の追加は
  scope 外」と明示したため実装せず、裁定パッケージ候補として残す。規律 2 は
  「結果正規化を不変とする」不変条件、段 6 敵対レビュー、変異 matrix で守った。

## 次の一手差分

### 完了

- [T-1815] 判定器と gate report の CLI 起動経路を直し、実プロセスで 4 起動形を library 判定と
  突き合わせる回帰検査を新設した。受理集合は不変で、`effective` はどの経路でも false のままである。
  remaining: none
  base: 1cae0cedd9815d79007b00af0f5f444c7b185c7dbad47354171fa45ad20d6202

### 新規

- {{T:s8c-cli-alias-mechanism-pin}} **P2・新規**: 実プロセス CLI 検査は答えを pin するだけなので、
  canonical alias を足さずに結果正規化の型検査を緩める実装でも通る。機構そのものを強制する
  構造 pin を足すかを裁定する。足すなら、遅れて設定される alias でも通らない形にする必要がある。
- {{T:s8c-evaluator-exception-provenance}} **P2・新規**: 評価器呼び出しを囲む広い例外捕捉が
  例外理由を捨てるため、fail-closed に倒れた理由が消える (F631 が「なぜ通らなかったかが消える」と
  書いた部分)。fail-closed の status を保ったまま構造化した内部 reason を残す設計を検討する。
- {{T:s8c-gate-report-lock-closure}} **P3・新規**: gate report を campaign lock の enforcement
  source closure へ入れるかを裁定する。入れると 62 path 集合と digest が変わるので単独の変更単位にする。
- {{T:campaign-bootstrap-invariant-hold-release}} **P3・新規**: `campaign-direct-bootstrap` 規則を
  持つ meta-test の growth hold を解放するかを裁定する。本 wave で潜在違反 1 件が解消したので、
  解放時の赤の量が変わっている可能性がある。
- {{T:duration-ledger-unregistered-nodes}} **P3・新規**: 受入所要台帳に未登録の node が 202 件ある。
  どの wave 由来かを特定し、実測 JUnit から一括登録するか、未登録を許容する条件を決める。
