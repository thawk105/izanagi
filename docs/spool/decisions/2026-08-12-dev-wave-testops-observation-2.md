---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-testops-observation
seq: 2
---

## {{D:testops-observation-frozen-pilot}}. task-run 台帳の凍結は契約であり、再開・記録先・被覆範囲はユーザー裁定へ返す

**決定:** 「テスト運用観測層 (TestOps) を導入する」という依頼に対し、本 wave では実装しない。
D66 の task-run 台帳 v1 が同じ役割をすでに担っており、その停止は破損でも放置でもなく pilot 契約の
発効だからである。再開の可否と形、記録先、被覆範囲の 3 点を裁定パッケージとしてユーザーへ返す。

**理由:**

- **停止機序は三重の構造的拒否である。** `tools/task_runs/ledger.py:544-557` が final marker 存在、
  `published >= max_task_runs`、`now >= pilot_started + max_days` のそれぞれで `start_run` を拒否する。
  実測時点で 3 条件すべてが成立していた。したがって「記録率ゼロ」は観測不能な母集団の推定ではない。
- **再開は D66 が明示的に予約した事項である。** D66 (6) は常設化を「pilot 実証前の常設化は盛りすぎ —
  実証後にユーザー提案」として却下し、`output/task-runs/README.md` の pilot 契約は「最終 report
  生成後に凍結。次 pilot の root 世代命名はその時に裁定」と定める。scope を選ぶ設問への回答を、
  別の設問 (無期限 rollover の可否) への承認として流用しない。
- **記録先の択一は threat model の変更を含む。** D66 (5) は append-only を crash-consistency 契約へ
  格下げし、改竄検出は tracked file の git 履歴という外部 anchor に委ねた。repo 外へ移すと
  schema 妥当な事後書換えが validate も git も通る。一方 repo 内 tracked に留めると、走行ごとに
  untracked が生じ、並行する全 wave の clean-tree gate と land の untracked 拒否を毎走行で壊す。
  どちらも代償の性質が異なり、親が単独で決める範囲を超える。
- **規模が D205 / D220 の判断に触れる。** 敵対相談 2 本が独立に返した blocker 9 件 (並行 start での
  cap race、世代作成の crash recovery、dispatch / bounded scope での counts 欠測、OOM・timeout の
  未記録、series 単位の fail-closed reader 不在、外部 base が証拠 namespace を指せる、
  base commit の間接的な caller 指定、無言 fail-open、4 gate の凍結範囲) を安全に閉じると、
  段 2 プランの 142 行見積りは成立しない。D220 が同種の拡張を 645〜816 行として不採用にしている。

**却下した選択肢:**

- **凍結済み世代を捕捉して自動 rollover する** (段 2 プランの骨子) — 有界 pilot を無期限の常時計装へ
  黙って変える。cap と最終レビューが無意味になり、上記の予約を迂回する。
- **既定の記録先を `XDG_STATE_HOME` → `HOME/.local/state` の順で解決する** — 実機では
  `XDG_STATE_HOME` が未設定であり home 配下に解決される。作業ファイルを home へ置かないという
  ユーザー是正と `docs/pegasus-runbook.md` §6 に反する。repo 外に置くなら、コードへマシン固有 path を
  焼かずに済む形として `git rev-parse --git-common-dir` から導く repo 兄弟が候補になる
  (前例 = third-party cache と dev-wave-jobs)。ただし採否は記録先の裁定に従属する。
- **分析側 (実行時間の回帰検出・flaky 検出) を先に実装する** — 台帳へ新規記録が入らない以上、
  発火する既存 artifact path を書けない。順序として成立しない。
- **per-test 粒度を持たせて flaky 検出と遅いテスト順位を作る** — `tools/task_runs/pytest_stats.py` は
  node ID を保存せず digest だけを残す。git 履歴へ入った記録は事実上削除できないため privacy を
  schema で機械強制した D66 (1) の設計であり、緩めるなら独立の裁定を要する。
