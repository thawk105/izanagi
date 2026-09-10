# TestOps (テスト運用観測層) の導入要求 — 実測と裁定パッケージ (2026-08-12)

authority: none
default_effect: no-state-change

wave = `dev-wave-testops-observation` / branch `worktree-dev-wave-testops-observation`
base = main `5b8cccac` / **実装差分ゼロ** (段 4 で「実装しない」と裁定し、`4→7→8→9`)

## 何をしたか

ユーザー依頼「TestOps をこのリポジトリに導入してください」を受け、語がリポジトリ内で未定義だった
ため段 1 前に scope を諮り、**「自前のテスト運用観測層」**の選択を得た。そのうえで既存被覆を
性質で検索したところ、**同じものが既に実装されており、かつ契約どおり凍結されている**ことが判明した。

## 実測で確定した事実

1. **テスト運用観測層は既に存在する。** D66 の task-run 台帳 v1。実装は `tools/task_runs/`
   (ledger 987 / aggregate 930 / schema 620 / pytest_stats 182 行) と `tools/task_run.py` /
   `task_run_check.py` / `task_run_report.py`。テスト走行ごとに suite_id / suite_kind / duration_s /
   collected / passed / failed / skipped / exit_status / trigger / collected_node_digest を追記する
   (`tools/task_runs/ledger.py:851`)。
2. **記録は 21 日間ゼロである。** 台帳には task run 10 件・event 69 件が残り、全 event の最終
   timestamp は `2026-07-21T20:33:39.243Z` (内容から実測)。11 個目の entry は run ではなく
   `pilot-final.json` (最終 report 名と SHA-256 を封じた凍結マーカー)。
3. **止まっている機序は三重の構造的拒否である。** `tools/task_runs/ledger.py:544-557` が
   (i) final marker 存在、(ii) `published >= max_task_runs` (10/10 到達)、
   (iii) `now >= pilot_started + max_days` (14 日、2026-08-03 に超過) のそれぞれで `start_run` を拒否する。
   よって「凍結後の記録率 = 0」は推定ではなく writer の仕様である。
4. **これは事故ではなく契約である。** D66 と `output/task-runs/README.md` の pilot 契約は
   「最終 report 生成後に凍結 (新規 start 拒否)。**次 pilot の root 世代命名はその時に裁定**」と定め、
   D66 (6) は常設化を「pilot 実証前の常設化は盛りすぎ — 実証後にユーザー提案」として却下している。
5. **per-test 粒度は設計上わざと持たない。** `tools/task_runs/pytest_stats.py:1-6,48-52` は node ID を
   保存せず 12 hex digest だけを残す。git 履歴へ入った記録は事実上削除できないためであり (D66 (1))、
   flaky 検出・遅いテスト順位は v1 の設計外である。

## 敵対相談の結果 — 両レンズ独立で NO-GO

段 2 の codex プラン (repo 外の世代 root へ ID 不要の合成 task-run を自動記録し、cap 到達済み世代を
自動 rollover する案、production 差分 142 行見積り) に対し、異なるレンズ 2 本を並列で当てた。

- **レンズ A (正しさ境界):** blocker 5・must-fix 6・裁定候補 1。
- **レンズ B (実効性と全層被覆):** blocker 5・must-fix 5・裁定候補 4。実行経路の被覆表を作らせ、
  素の `python3 -m pytest`・mutation harness の local mode・別 clone が原理的に未被覆であることを
  明示させた。

親が独立に裁定した結果、blocker 10 件のうち **1 件を refuted**、9 件を real とした。

- **refuted (レンズ A blocker 1):** 「sidecar の I/O 例外が pytest の rc を壊す」。
  `orchestrator/tests/conftest.py:270-307` が 3 hook すべてを `try: ... except Exception: pass` で
  包んでおり、`OSError` / `PermissionError` / `ENOSPC` は hook の外へ出ない。`Exception` は
  `KeyboardInterrupt` / `SystemExit` を含まないため D66 (3) の再送出契約とも整合する。
  子がこれを見られなかったのは、親が読む範囲の名指しに conftest を含めなかったためである。

親自身の実測でも 1 件見つかった。プランの既定記録先 `${XDG_STATE_HOME:-$HOME/.local/state}` は、
`XDG_STATE_HOME` 未設定 (実測) のため `/home/SFC/tanab/.local/state/...` に解決され、
「作業ファイルは `/work` 配下、home に置かない」というユーザー是正と runbook §6 に反する。

## なぜ実装しなかったか

親が単独で解けない理由が 3 つある。

1. **観測の再開そのものが D66 の予約事項である** (上記 4)。承認済み裁定を親が不採用にせず、
   新事実付きでユーザー再裁定へ戻す (`DW-S04`)。本 wave 冒頭のユーザー選択は scope の選択であって、
   無期限 rollover の承認ではない。
2. **記録先の択一が threat model を変える。** D66 (5) は hash chain を作らない代わりに tracked file の
   git 履歴を改竄検出の外部 anchor とした。repo 外へ移すと schema 妥当な事後書換えが validate も
   git も通る。repo 内に留めれば、走行ごとの untracked が並行する全 wave の clean-tree gate と
   land の untracked 拒否を壊す。
3. **規模が裁定を要する。** blocker 9 件を安全に閉じると、プランの 142 行見積りは成立しない。
   D220 が「過大」として不採用にした 645〜816 行の水準へ近づき、D205 のプロトタイプ基準に触れる。

## 逐語

- `verbatim/s1-brief.md` — 親 brief (訂正前の原文。訂正は `verbatim/s4-ruling.md` §0)
- `verbatim/s2-plan.md` — 段 2 codex プラン
- `verbatim/s3-lens-a.md` — 段 3 敵対相談 レンズ A (正しさ境界)
- `verbatim/s3-lens-b.md` — 段 3 敵対相談 レンズ B (実効性・全層被覆)
- `verbatim/s4-ruling.md` — 段 4 親裁定と、ユーザーへ返す裁定パッケージ Q1〜Q3

## ユーザー裁定待ち

`verbatim/s4-ruling.md` §3 の Q1 (再開の可否と形)、Q2 (記録先と改竄検出 anchor)、
Q3 (被覆する実行経路の定義) の 3 点。親の推奨はいずれも (a)。
