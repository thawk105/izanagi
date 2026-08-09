---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t677-relay-reach
seq: 3
title: [T-677] 失敗診断が dispatch の末尾 64 KiB 中継を越えて届くことを機械検査した (コード + docs、受入 7629 passed / 20 skipped、変異 7/7 KILLED、branch worktree-dev-wave-t677-relay-reach)
---

## 本文

- **依頼 = [T-677] の実装。** 現状の「例外 message 内での末尾への要約再掲」を、診断が確実に
  人間へ届く形の機械検査に置き換えるか補強する。方式は {{D:failure-digest-producer-side}} で
  producer 側の終端ダイジェストに確定し、dispatcher は無編集とした。編集面は
  `orchestrator/tests/conftest.py` と新規 `orchestrator/tests/test_pytest_failure_digest.py` の 2 本。
- **前提は既存 artifact から実測した (repo 無改変)。** 緑の全走は child stdout 8,808 bytes で
  全量が中継に収まる。110 failed の全走では 523,987 bytes のうち 458,452 bytes (87.5%) が欠落し、
  `=== FAILURES ===` の見出しごと消えていた。他に 213,154 / 190,958 / 180,952 / 100,125 /
  95,214 bytes の切り詰め実績。**T-677 の前提は仮説ではなく再現済み**である。
- **親 brief の主張を 3 件撤回した。** (1)「tracked test file 150 件はすべて `orchestrator/tests`
  配下」は誤りで、`output/insights/` 配下と `tools/task_runs/` に反例がある (canonical
  acceptance の収集集合に限れば成立)。(2) 上記の 110 failed ログに
  `test_codex_worker_launch` は含まれないため、**「launcher 固有の診断消失」は推論であって実測ではない**
  (generic な切り詰めの再現は実測)。(3)「失敗ごとに診断本体を残す」という不変条件は 49 KiB 予算と
  両立しないため、「代表 failure の本体 + 全件の正確な省略会計 + 完全ログへの耐久参照」へ弱めた。
- **反証した所見が 1 件。** 「`| ` 接頭辞と frame で実中継 bytes が膨らみ到達が壊れる」は、
  `_utf8_tail` の切り詰めが `_prefix_relay_lines` の**前**に効くため到達保証には影響しない。
  表示 bytes の会計だけを E2E に併記させた。
- **最重要の所見は consumer 取り残しだった** ({{D:diagnostic-line-prefix-not-pipe}})。当初案の
  `| ` 行頭 prefix は変異 harness の `_strip_relay_prefix` に剥がされ、診断本文中の
  `FAILED path::name` が偽の失敗 node として変異台帳へ混入する。F65 と同型。
- **段 6 は fix 3 巡 (上限) を要した。** 1 巡目は敵対レビュー 2 本の must-fix 14 件、
  2 巡目は親の組み合わせ実走で出た in-tree 一時ファイル欠陥 ({{F:in-tree-temp-test-tree}})、
  3 巡目は焦点再レビューの残 4 件 (repo 外書込み保証、恒真な sha256 検査、予算探索の
  O(n^2 log n)、repo root 不在 probe が実は root 上で走っていた件)。
- **子の単一ファイル実走は親の組み合わせ実走を代替しなかった。** 子は 14 passed / 26 passed を
  報告していたが、guard を含む組み合わせで初めて赤が出た。恒久対応は
  {{F:in-tree-temp-test-tree}} に記録した。
- **受入 lease の飽和で全走を 2 回落とした。** 30 秒間隔で 60 分・120 分の 2 窓とも取得できず
  (4 wave が ~23 分ずつ連続保持)。**間隔を 10 秒へ詰めて 3 回目で取得**し完走した。
  memory の「30 秒間隔」は 2 wave 競合の実測に基づく値であり、4 wave 飽和時には足りない。
- **peer 通知 3 本を受けた** (provenance の `/model` 裁定、既知 23 件の調停、land への
  full-history 監査追加の予告)。いずれも取り込み契機としてのみ使い、検査の省略には使っていない。
  本 wave の commit は `model=claude-opus-5` を使った — 露出 slug の `claude-opus-5[1m]` は
  規約の文字集合に反し、`claude-opus-5-1m` は自作 slug になるため。本セッションは `/model` を
  実行していないので `model=unknown` 条項には当たらない。
- **full-history provenance 監査の rc=1 は既知 23 件由来**であり、本 wave の新規違反はゼロ
  (`--message-file` preflight rc=0、`--range` 監査 17 件・違反なし)。既知分は専任 wave が担当中で
  本 wave は手当していない。
- 工数: codex 子 8 本 (plan 1、敵対 2、実装 1、レビュー 2、fix 3 のうち再レビュー 1 を含む)。
  親の実走は targeted 4 回、変異 3 走 (Arm A / A2 / B)、受入 1 完走。

## 次の一手差分

### 完了

- [T-677] 失敗診断の中継到達を機械検査で固定した。producer 側の終端ダイジェストと、
  自動 discovery を通す E2E・consumer 検査・中継結合検査を新設した。
  remaining: none
  base: 820c1f31cae222d1970e2ccf1d2f61267f78e5a67cef730af465749dc65005da

### 新規

- {{T:digest-xdist-crash-coverage}} **P2・新規**: xdist worker の internal error と
  pre-item crash では `failed`/`error` report が生成されず、終端ダイジェストが空になる。
  `pytest_internalerror` と `pytest_testnodedown` を別診断項目として取り込むか、
  既存 xdist summary を正本と定めるかを裁定する。
- {{T:digest-infra-kill-evidence}} **P2・新規**: SIGKILL・OOM kill・PBS walltime 打ち切り・
  pytest 起動前の rc=16 は pytest hook の到達範囲外で、診断が一切残らない。job wrapper 側の
  durable checkpoint / partial-log path を作るかを裁定する。本 wave の保証は
  「pytest セッションが完走した場合」に限定して記録済み。
- {{T:relay-best-effort-durability}} **P3・新規**: dispatch の中継は best-effort で
  BrokenPipe と relay error を握る。真の「確実に届く」を要求するなら dispatcher 側の
  耐久経路が要る。receipt の `scheduler_logs.stdout.path` を人間向け fallback として
  手順・検査へ明示するかを含めて裁定する。
- {{T:digest-stash-session-binding}} **P3・新規**: 終端ダイジェストの failure stash が
  module global であり、同一 process の入れ子 `pytest.main()` で外側 session の report が失われる。
  session / plugin instance 束縛の collector へ移すかを裁定する。canonical acceptance に
  この経路が実在するかは未確認で、現行仕様は回帰テストで固定済み。
