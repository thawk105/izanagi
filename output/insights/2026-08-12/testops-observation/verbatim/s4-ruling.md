# 段 4 裁定 — dev-wave-testops-observation

両レンズとも **NO-GO**。親は以下のとおり裁定する。

## 0. 親 brief の訂正 (実測による)

段 3 の A10 / B5 が brief の一般化を突いた。実測して訂正する。

- 誤: 「実 run ディレクトリ 11」→ **正: task run は 10 件ちょうど**。11 個目の entry は
  `output/task-runs/pilot-final.json` (最終 report 名 + SHA-256 を封じた凍結マーカー)。
- 誤: 「台帳が空」→ **正: 台帳には 10 走行・69 event が残っている。ゼロなのは凍結後の新規記録**。
  全 event の最終 timestamp は `2026-07-21T20:33:39.243Z` (内容から実測)。以後 21 日間、
  新規 event はゼロ。
- **記録が止まっている機序を実測で確定した。** `tools/task_runs/ledger.py:544-557` は
  (i) final marker 存在、(ii) `published >= max_task_runs` (10/10 到達)、
  (iii) `now >= pilot_started + max_days` (14 日、2026-08-03 に超過) の**三重**で `start_run` を拒否する。
  したがって「凍結後の記録率 = 0」は観測不能な母集団の推定ではなく、writer が構造的に拒否する事実である。
- ただし A10 の指摘の一部は認める。「`IZANAGI_TASK_RUN_ID` なしの `run_tests.py` invocation 総数」
  という分母は測っていない。本 wave はこの分母を主張の根拠に使わない。
- A11 も認める。brief の「記録失敗が child rc を置換しない」は無条件に書いたが、D66 (3) は
  `KeyboardInterrupt` / `SystemExit` の再送出を要求する。正しくは「通常の `Exception` は飲む、
  operator signal は再送出する」。

## 1. 所見の裁定

### refuted

- **A1 (blocker) — sidecar の I/O 例外が pytest の rc を壊す: refuted。**
  `orchestrator/tests/conftest.py:270-307` が `pytest_collection_finish` /
  `pytest_xdist_node_collection_finished` / `pytest_sessionfinish` の 3 hook すべてを
  `try: ... except Exception: pass` で包む。`_create_sidecar` の `OSError` / `PermissionError` /
  `ENOSPC` は hook の外へ出ない。`Exception` は `KeyboardInterrupt` / `SystemExit` を含まないため
  D66 (3) の再送出契約とも整合する。
  子が conftest を見られなかったのは、親が読む範囲の名指しに conftest を含めなかったためである
  (段 8 の改善候補)。

### real かつ scope 内 (plan v2 で閉じるべきもの)

| # | 要旨 | 帰結 |
|---|---|---|
| A2 | 4 gate の凍結を関数本体の無差分で担保できない。依存定数表・caller・`PYTEST_ADDOPTS` が射程外 | truth-table characterization test が必須 |
| A3 | 外部 base が証拠 namespace / symlink 経由でそこを指せる。lock・generation・`pilot.json` は `start_run` より前に作られるので ledger 側拒否では遅い | 禁止 namespace 検査を series manager 自身へ |
| A5 | series 全体を読む fail-closed reader が無い。破損世代を無言で飛ばして健全な 1 世代だけ report できる | series 単位の validate 入口が必須 |
| A6 | direct pytest 子へ所有 marker が渡らず、入れ子起動で run が増殖する | 全 child env へ marker |
| A7 | series lock に timeout / nonblocking 契約が無く、競合で pytest 自体が始まらない | fail-open が破れる |
| A8 | `start_run(repo_root=...)` は base commit の間接的な caller 指定になり D66 (4) の自己申告遮断を破る | 別 repo の HEAD を注入できる |
| A9 | synthetic task の objective に repo file path を保存する設計。privacy 検査が argv/selector/node ID に限定 | sentinel 検査へ拡張 |
| B1 | cap 判定が未完了 run を数えず、並行 wave で 10 件を超える | 世代境界が崩れる |
| B2 | 世代 mkdir と `init_pilot` の間で落ちると以後永久に記録不能 | recovery が必要 |
| B3 | dispatch / bounded scope は sidecar を持たず counts・digest が欠測 | 経路間比較が成立しない |
| B4 | bounded scope の OOM / timeout は記録経路に入らない | 資源で落ちた走行ほど台帳から消える |
| M1 | fail-open が完全に無言で、記録停止を誰も知れない | v1 と同じ沈黙を再生産する |
| M2 | manual CLI が series lock を迂回して同じ世代へ書ける | 台帳状態が食い違う |
| M3 | `trigger` は環境変数の手番が残ったまま。ID だけ自動化しても cohort 分けができない | 無手番化が半分 |
| M4 | 既定 root の filesystem 契約 (flock / O_APPEND / fsync の成立) を確認していない | 破損の実現性 |

### real だが scope 外 — ユーザー裁定へ返す

- **A4 (blocker) — 自動 rollover が D66 の pilot 停止とユーザー裁定を迂回する。**
  D66 と `output/task-runs/README.md` の pilot 契約は「最終 report 生成後に凍結 (新規 start 拒否)。
  **次 pilot の root 世代命名はその時に裁定**」と定め、D66 (6) は常設化を
  「pilot 実証前の常設化は盛りすぎ — 実証後にユーザー提案」として却下している。
  段 2 プランは凍結状態を捕捉して**無条件に次世代を作る**設計であり、この予約を迂回する。
  本 wave 冒頭のユーザー選択 (「(A) 自前のテスト運用観測層」) は scope の選択であって、
  **無期限 rollover の承認ではない** (別問の選択肢集合に対する裁定を流用しない)。
- **A12 — repo 外化は D66 が依存した外部 anchor (git 履歴) を失う。**
  D66 (5) は hash chain を作らない代わりに tracked file の git 履歴を改竄検出の外部 anchor とした。
  repo 外へ移すと schema 妥当な事後書換えが validate も git も通る。これは clean-tree 回避の
  利便性の話ではなく **threat model の変更**であり、親が単独で決めてよい範囲を超える。
- **M5 — 規模。** 10 件の blocker を閉じると、プランの 142 行見積り (および brief の 150 行目標) は
  成立しない。lock の timeout、crash recovery、series validate、経路別 payload、禁止 namespace 検査、
  診断出口を実装すると D220 が「過大」として不採用にした 645〜816 行の水準へ近づく。
  D205 のプロトタイプ基準に照らし、**規模そのものをユーザー裁定へ返す。**
- **R1 — 素の `python3 -m pytest` と mutation harness の local mode は原理的に未被覆。**
- **R2 — 現行 field だけでは実行時間の回帰を信頼して検出できない** (`suite_id` が並列度を区別せず、
  direct / dispatch / scope で duration の意味が違う)。本 wave では分析を実装しないので実害はないが、
  「比較可能になった」と成果に書いてはならない。
- **R3 — cross-clone 共有は実現しない** (namespace が git common-dir digest で分かれる)。
- **R4 — 自動世代に retention と発見手段が無い。**
- **PF-1 (親の実測) — プランの既定 base は home を汚す。**
  `XDG_STATE_HOME` 未設定 (実測)、`HOME=/home/SFC/tanab` なので既定は
  `/home/SFC/tanab/.local/state/izanagi/task-runs/` に解決される。2026-08-03 / 08-04 のユーザー是正
  (作業ファイルは `/work/SFC/tanab` 配下、home に置かない) と runbook §6 に反する。
  コードへマシン固有 path を焼くのも禁止のため、両立形は
  `git rev-parse --git-common-dir` の realpath から導く **repo の兄弟** (本機では
  `/work/1/SFC/tanab/izanagi-task-runs/`)。前例が 2 つある — third-party cache
  (`/work/1/SFC/tanab/izanagi-thirdparty-cache`、2026-08-06 に home 配下から移した) と
  `/work/1/SFC/tanab/dev-wave-jobs/`。これは Q2 の付帯として裁定へ返す。

## 2. 中核の裁定 — 本 wave では実装しない

理由は 3 つで、いずれも親が単独で解けない。

1. **観測の再開そのものが D66 の予約事項である。** 凍結は事故ではなく契約であり、
   「最終 report 後の継続・縮小・撤去はユーザー裁定」と明記されている。承認済み裁定を親が
   不採用にせず、新事実付きでユーザー再裁定へ戻す (`DW-S04`)。
2. **記録先の択一が threat model を変える** (A12)。repo 内は全 wave の clean-tree gate を壊し、
   repo 外は改竄検出の外部 anchor を失う。どちらも代償の性質が違い、設計択一として割れている。
3. **規模が裁定を要する** (M5)。安全に閉じる実装は D205 / D220 の水準判断に触れる。

したがって `DW-S04` の「実装しない」裁定とし、遷移は **4→7→8→9**。実装差分ゼロなので変異 matrix は
免除。受入全走は免除せず、実 repo を読むテストの有無を段 7 の記録前に判定して結果を worklog へ書く。

## 3. ユーザーへ返す裁定パッケージ

### Q1. テスト運用観測を再開するか、どの形で

- **(a) 有界の次世代 pilot として再開する (親の推奨).** cap (例: 30 走行または 30 日) を持たせ、
  到達したら再び凍結して最終 report をユーザーへ返す。D66 の設計思想 (有界 pilot → 実証 → 裁定) を
  そのまま踏襲し、無期限の常時計装を作らない。rollover は自動化せず、次世代の開始は明示裁定とする。
- **(b) 無期限の常設計装にする.** D66 (6) が「盛りすぎ」として却下した形。cap と最終レビューが
  無意味になる。段 2 プランの自動 rollover はこれに相当する。
- **(c) 再開しない.** `output/task-runs/` を凍結 archive のまま残す。テスト運用の観測は行わない。

### Q2. 記録先と改竄検出の anchor

- **(a) repo 外 (repo の兄弟) + 「証拠でない」の再確認 (親の推奨).** 本機では
  `/work/1/SFC/tanab/izanagi-task-runs/`。clean-tree gate を壊さず、home も汚さない。
  失うのは git 履歴による改竄検出であり、D66 (5) が既に「append-only は crash-consistency 契約で
  あって改竄検出ではない」と主張を格下げ済みである点と整合する。台帳を証拠に使わない限り実害は無い。
- **(b) repo 内 tracked の次世代 root.** anchor を保つが、走行ごとに untracked が生じ、
  並行する全 wave の clean-tree gate と land の untracked 拒否を壊す。実運用は困難。
- **(c) repo 外 + 定期的に要約を repo へ commit して anchor を復元する.** 両取りだが実装が増え、
  M5 の規模問題を悪化させる。

### Q3. 被覆する実行経路の定義

- **(a) `tools/run_tests.py` 経由のみを被覆と定義し、未被覆を docs に明記する (親の推奨).**
  素の `python3 -m pytest`、mutation harness の local mode、別 clone は未被覆と書く。
  「全走行を記録する」と称さない。
- **(b) conftest 側で計装して全 pytest を被覆する.** 被覆は広がるが、テスト process 自体に
  観測を常設することになり、受入形・観測者効果・fail-open の射程が段違いに広がる。

## 4. 段 7 以降で残す成果物

- 段 2 プラン・段 3 レンズ 2 本の逐語を `output/insights/` へ凍結。
- 本裁定を decisions fragment へ (D66 の追補として、凍結の三重機序・再開が予約事項である事実・
  記録先の threat model 択一を記録)。
- worklog fragment に実測値 (10 run / 69 event / 最終 event timestamp / 21 日ゼロ) と、
  Q1〜Q3 を裁定待ちとして起票。
