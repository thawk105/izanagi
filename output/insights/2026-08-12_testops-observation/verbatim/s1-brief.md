# 段 1 brief — dev-wave-testops-observation

**依頼:** 「TestOps をこのリポジトリに導入してください」

**確定済みユーザー裁定 (本 wave 冒頭、2026-08-11):** 語がリポジトリ内で未定義だったため段 1 前に諮った。
選択肢 (A) 自前のテスト運用観測層 / (B) 外部 TestOps 製品 (Allure・Katalon 等) / (C) テスト選択・
影響解析 / (D) 別の具体 のうち、**ユーザーは (A) を選択**。(B)(C) は scope 外である。

## 実測した既存被覆 (機構名でなく性質で検索した結果)

- テスト走行の結果と所要時間を蓄積する経路は**既に存在する** — D66 の task-run 台帳 v1。実装は
  `tools/task_runs/` (ledger 987 / aggregate 930 / schema 620 / pytest_stats 182 行) と
  `tools/task_run.py` / `task_run_check.py` / `task_run_report.py`。
- 1 走行あたりの記録内容 (`tools/task_runs/ledger.py:851` `record_test_run`): suite_id / suite_kind /
  duration_s / collected / passed / failed / skipped / exit_status / trigger / collected_node_digest。
- **node ID は構造的に保存しない** (`tools/task_runs/pytest_stats.py:1-6,48-52`。12 hex digest のみ)。
  git 履歴へ入った記録は事実上削除できないため privacy を schema で機械強制する設計 (D66 (1)、
  `output/task-runs/README.md`)。したがって per-test の flaky 検出・遅いテスト順位は v1 の設計外。
- 発火は **opt-in**。`tools/run_tests.py:1487,1641,1865` は `IZANAGI_TASK_RUN_ID` が未設定なら
  記録経路へ入らない。root 既定は tracked な `output/task-runs` (`tools/run_tests.py:1501`)。
- **pilot は終了済み。** `output/task-runs/pilot.json` の cap = 10 run / 14 日、開始
  `2026-07-20T02:28:06Z`。実 run ディレクトリ 11、最終 report
  `output/task-runs/reports/20260720-20260722_task-efficiency.md` 発行済み。
  → **現在テスト走行は 1 件も記録されていない。**
- 同 report の実証: 自動配線された test_run は 10 run 中 8 run で有効値を持つ。一方、親セッションの
  手動 CLI に依存する stage は 10 run 中 9 run が `unclassified_rate = 1` (全部未記録)、trigger も
  44 件中 39 件が `unspecified`。**自動の面だけが機能し、手番を要する面は機能しなかった。**

## 純増検出力

現在ゼロである「テスト走行の記録」を再開し、走行列の比較を可能にする。v1 は 1 走行の観測値は
持つが走行間比較を持たない (report は cohort 内観測表のみで、閾値も推奨も意図的に持たない)。

## scope — 親の provisional 裁定であり攻撃対象

- **(P1) 順序.** 分析 (実行時間の回帰検出・flaky・遅いテスト) より先に**記録の再開**を実装する。
  台帳が空である以上、分析側は `DW-G04` の発火条件 (発火する既存 artifact path) を書けない。
- **(P2) 無手番化.** `IZANAGI_TASK_RUN_ID` の手動 start を要求せず `tools/run_tests.py` の走行を
  記録する。根拠は上記実証 (手番を要する面は実際に記録されなかった)。
- **(P3) 記録先.** 既定 root を **repo 外**にする。tracked な `output/task-runs` へ常時追記すると、
  全 wave の clean-tree gate と land の untracked 拒否 (`DW-O23`) を毎走行で壊す。
  共有性を失う代償は裁定へ返す。
- **(P4) 規模.** D205 のプロトタイプ基準と D220 の判定 (645〜816 行を過大として不採用) に合わせ、
  production 差分 150 行以内を目標とする。schema 世代の新設はしない。

## 不変条件 (緩めない)

- `tools/run_tests.py` の 4 gate (`_is_full_suite:388` / `_has_no_execution_flag:448` /
  `_has_dispatch_exempt_flag:458` / `_is_acceptance_run:505`) の判定を 1 bit も変えない。
  pytest argv へ flag を足さない (受入形が False へ倒れる既知事故がある)。
- 書く側 fail-open / 読む側 fail-closed (D66 (3))。記録失敗が child rc を置換しない。
- 台帳は `authority: development-observation-not-evidence` を保ち、proof chain・fitness・benchmark の
  証拠にしない (D66 (1))。
- node ID を保存しない。privacy の機械強制を弱めない。
- 「削れる工程」の自動推奨を作らない (D66 (5)、絶対規律 2/3)。

## 成果物の形

`tools/run_tests.py` の記録配線の変更 + `tools/task_runs/` の最小追加 + `orchestrator/tests/` の
新規テスト + docs (`output/task-runs/README.md` の世代契約、decisions fragment、worklog fragment)。

## 並列分割方針

実装は 1 単位。`tools/run_tests.py` と `tools/task_runs/` は結合が強く所有を素集合に割れない。
テスト追加も同一単位に含める。

## wave 形

正しさ防壁 (`run_tests.py` の gate 群) に触れ、かつ記録先の設計択一が割れるため、
`DW-C00` の軽量版に該当しない。段 2・3 の敵対子と段 6 の review 2 本を省かない。

## 成果物影響 (DW-G05)

これを実装しない場合、certified 選択・レポート・3 台帳の値・受理集合・参照は**変わらない**
(開発観測 namespace は証拠から構造的に切り離されている)。変わるのは開発運用の可観測性だけであり、
本 wave の must-fix はこの範囲を超えない。
