---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t080-accept-speed
seq: 1
title: 受入全走の t080 e2e の内訳を計算ノードで実測し、実 repo 複製を session 1 回の proto にする実装を検証したが受入 wall −5.7% では採用せず branch に保存した (docs のみ land、branch worktree-dev-wave-t080-accept-speed、変異 matrix = baseline PASSED・負例 9/9 KILLED 期待 node 完全一致・等価 1 SURVIVED)
---

## 本文

- ユーザー依頼は「計算ノードで t080 e2e 1 本の内訳 (実 repo からの複製 / git add / 発行時の全件 scan 回数と所要 /
  本体) を測り、支配項を実装で削る。第一候補は実 repo からの複製を session 1 回にし key を計算ノード内で派生させる形
  (bytes 同一)。目標は 5 分ではなく受入全走の実時間の短縮。D2068 の『案 C は符号未確認』は本日の対比較
  (温 cache で 9.55 秒対 9.66 秒) で『効かない』と確定したので訂正を含める」。
- 一次資料は `output/insights/2026-09-16/accept-speed-t080-session-copy/README.md`。profile・pytest 出力・受領証・
  spec・probe 結果・運転 script は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t080-accept-speed/` に保全した。
- **内訳は custom probe を書かずに測った。** 標準 profiler (`python3 -m cProfile -m pytest …`) で既存 test を
  計算ノードで直列に走らせ、caller 別の集計で分けた。base 構築 118.2 秒 = lustre 複製 52.9 (45%) + 発行 subprocess
  53.3 (45%) + git 操作 9.5 (8%) + 他 2.5。5 key 一括走では複製が延べ 190 秒 (平均 38 秒) で温 cache でも同じ桁だった。
- **親の brief は 2 レンズに 12 項目訂正された。** 発行時の全件 scan は「5 回」でなく **13 回** (plan は 12 と数え、
  gate_check の 2 回目 scan を落としていた)。`temp_roots` 19.8 秒は境界検査で build ではない (no-issue の初回 build は
  g7 に含まれる)。「verify 4.85 秒のうち search 5.3 秒」は包含として成立しない。「git add -A は 8%」は git 操作 11 回の
  合計。「key 別複製 8〜45 秒」「温 cache でも安くならない」は durations の引き算で根拠不足。「差 80〜100 秒は競合」は
  分解不能。「proto は index 未作成」は誤り (submodule add が stage する)。無条件の「bytes 同一」は条件付き定義へ。
- **F971 の「build 1 回 20〜24 秒」は本日の実測 (発行込み 118 秒) と一致せず、出所も無い。** 当初「temp_roots 19.8 秒と
  整合」と読んだが、レンズ B が refuted した。docs の数値は一次資料と一致するまで根拠にしない。
- 設計判断は {{D:t080-fixture-session-proto}} (実装の形・I1 の定義・session snapshot・採用しない判断) と
  {{D:d2068-erratum-index-fast-path-no-effect}} (D2068 の訂正)。
- **実装 (commit `bdfa49950`、Codex author) は bytes 同一まで示した。** 1 回限りの probe で旧 module を base commit
  `08d56628e` から exec し、両経路の commit metadata を固定して default / distinct の 2 key を比較 — basis commit・
  basis tree・発行後 HEAD tree・receipt raw/document・working tree が全項目一致。probe (Codex `role=author`、200 行) は
  repo へ commit せず job dir に保全 (sha256 `b57a80433f128d149ca6bf208b90c09343f6b06997100a27f67d23af02806b9d`、8008 bytes)。
  1 回目は `python3 tools/<probe>.py` 起動で `sys.path[0]` が `tools/` になり conftest が `orchestrator` を import できず
  collection rc=3 で落ちた。`python3 -m tools.<probe>` で通った。
- **非競合の critical path は縮まらない。** 同一 node (bnode067) の xdist `-n 12` 焦点走で旧 136.7 秒・新 133.3 秒
  (旧 2 走・新 3 走とも同水準)。レンズ B の勝利条件 `max(R_k) > R_proto + D` のとおり 12 worker では lustre 5 本並行読みが
  飽和しない。
- **受入の同時刻ペア (別 worktree から同時投入、対照は `--wave control-…` で lease を分ける) は 4 組。** ペア 1 (両側緑)
  最遅 shard 332.0 → 296.5 秒 (−10.7%、e2e 10 node は各 −36 秒、proto 経路外の `temp_roots` 104.6 → 23.6)、ペア 2 は post 側の
  shard-0 node だけ git subprocess 30 秒 timeout ×29 (F945 型) で不成立、ペア 3 (両側が同型の F945 赤、lustre 飽和下)
  474.4 → 465.5 (−1.9%)、ペア 4 (両側緑) 326.7 → 308.1 (−5.7%)。**比較可能 3 ペアの中央値 −5.7% は D357 / D1260 の
  10% 基準の内側なので、段 4 裁定 §6 のとおり fixture 変更は land しない。** 実装は branch `impl-dev-wave-t080-accept-speed`
  に保存し、採用可否を裁定パッケージで返す。
- **同名 `--wave` の同時受入は lease の `claim-self-unverified` (main-sha-mismatch) で落ちる。** 緑で保持された lease は
  main が進むと自己 claim を通せない。計測走は各走の後に `wave_land_window.py release` し、対照は別 wave 名にした。
- 段 6 の敵対レビュー 2 本は must-fix 0 件。nit: 変異 M1 の固定 path を `output/tracked.txt` に限る (operational path は
  後段で再配置され SURVIVED になる)、構築失敗後は後続 worker が再試行する、新規は 9 node、所要台帳の未登録は配置と実行順で
  既定値が違う (1 秒 / 上位 96 番目相当)。
- **変異 matrix (container worktree、`run_tests.py -k <小型 + shared-base + 境界 + 可視集合>`、25 node):** probe 走 2 本
  (全件 SURVIVED 期待) で観測 node を集めてから本走。本走は baseline PASSED、負例 9 件 (M1〜M5、M7〜M10) すべて KILLED で
  期待 node と観測 node が完全一致、等価変異 M0 は SURVIVED。**M6 (proto marker を build 前に公開) は probe 走で hang**
  (hang_timeout 1500 秒 → orphan hold 中止、wave worktree に変異残留 → job の walltime 終端後に `git checkout --` で復元)。
  hang node は `test_t080_proto_incomplete_build_is_rebuilt[False]` (`-v` の 6 分 job で特定): 親の
  `assert not marker.exists()` が Pipe で子を止めたまま失敗し `finally` の `terminate → join` が戻らない。DW-M06 に従い
  dispatch から外した。M11 (proto 入口の境界検査削除) は `temp_roots` 経由で test 対象 checkout の実 `output/` へ書くので
  登録から外した。
- 受入 pre-3 / post-2 / post-3 / pre-6 は F945 型の非帰属赤 (setup の `git ls-files --others` 30 秒 timeout、
  `git archive` timeout、real-repo lock deadline)。同時刻に本 wave の変異走と他 session の受入が重なっていた。
  赤の走の wall は計測に使わず (ペア 3 は両側同型なので参考値)。land 用の最終受入は記録 commit の後に docs-only の tip で単独に投げる (結果は land の受領証が持つ)。
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2、全段 `gpt-6-astra` / `medium`)。計算ノード job:
  内訳実測 2、df probe 1、実 corpus probe 2、焦点走 old 2 / new 3、小型焦点 1、m6 特定 1、変異 (probe 13 + probe2 5 +
  本走 11 走)、受入は計測用に pre 7 + post 4 (最終受入は別)。

## 次の一手差分

### 新規

- {{T:t080-proto-land-ruling}} **P2・ユーザー裁定待ち**: t080 e2e fixture の session 1 回 proto 化 (commit `bdfa49950`、
  branch `impl-dev-wave-t080-accept-speed`) を land するか。受入 wall の同時刻ペア中央値 −5.7% (−10.7 / −1.9 / −5.7、退行なし)
  は D357 / D1260 の 10% 基準の内側。bytes 同一・変異 9/9 KILLED・レビュー must-fix 0・受入緑は済。採用なら
  「共有資源削減を別目的として採用」か「10% 基準の緩和」の明示裁定が要る。材料は
  `output/insights/2026-09-16/accept-speed-t080-session-copy/README.md` §5・§7-5。
- {{T:t080-second-proto-issued-unactivated}} **P3・新規**: t080 e2e の発行済み・未活性化状態を第 2 proto にして
  default / codex-trailer / extra-r-path の 3 key で draft→validate→finalize (10 scan) を共有する案の裁定。延べ約 80 秒の
  削減候補だが「production 発行を key ごとに走らせる」現行 e2e の性質を変える。同 README §7-1。
- {{T:t080-proto-incomplete-build-test-hang}} **P3・新規**: `test_t080_proto_incomplete_build_is_rebuilt[False]` は
  「marker を build 前に公開する」欠陥下で hang する (M6)。`finally` で子へ `"fail"` を送ってから `terminate`、
  `join(timeout)` + `kill` にする小さな fix (Codex author)。実装 branch と一緒に扱う。同 README §7-4。
