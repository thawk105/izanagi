# 段 1 brief — dev-wave-t692-r3-xdist-walltime

- wave slug: `dev-wave-t692-r3-xdist-walltime` / branch `worktree-dev-wave-t692-r3-xdist-walltime`
- base: main `4be7a362` (2026-08-09)
- 依頼 (逐語): 「[T-692] R3 が別起票とした受入全走の pytest-xdist 対応を進めてください
  (T 番号は worklog の採番に従ってください)。walltime 逼迫 (30→40 分化後も試験数は増加中)
  への恒久策として、並列化の可否・分離が必要なテスト群・所要短縮の実測を伴う実装または
  択一パッケージを返してください。producer / pilot / 本走の受入がすべてこの suite に乗ります。」

## 0. brief 前に実測した前提 (DW-S01)

- **suite は既に xdist 前提で走っている。** `tools/run_tests.py` は `--dist loadgroup` を既定付与し、
  計算ノードでは `site_policy.default_test_jobs` が cap 無しで affinity 全数 = **48 worker**。
  したがって依頼文の「並列化の可否」は *導入の可否* ではなく **現行分配の改善余地**である。
  この訂正を段 2 以降の前提に置く。
- **受入 1 走の実測 (直近 land tip `03374f20`)**: 7685 passed / 20 skipped / **1379.26 秒**、
  PBS Elapse 1392 秒。上限は `dispatch_compute.DEFAULT_WALLTIME = "00:40:00"` = **2400 秒**で、
  `run_tests.py` は `--walltime` を渡さないため**呼び出し側から上げられない**。残余 1008 秒。
- **過去の並列度実測 (runbook、2026-07-30 / request 874129 / bnode114、48 core)**:
  当時の全走は `-n 48` = 205 秒、`-n 32` = 207 秒で**差はほぼ無い**。
  `-n 16` 以下との対照は未取得。「並列度を上げるほど速い」は実測されていない。
- **本 wave の baseline 計測を投入済み** (job dir `measure1.*`、`--junitxml` 付きの全走)。
  per-test duration から (i) 直列総和、(ii) xdist group ごとの直列総和、(iii) critical path
  下界を出す。**受入形ではない** (`--junitxml` を足すと acceptance shape 判定が False になるため、
  受入判定には使わない。受入は段 6 で別に走らせる)。

## 1. scope

- **入れる**: 受入全走の wall を縮める、xdist の分配 (group / 分割 / 並列度) 側の恒久対応。
  R3 原案 (案 F = 実 repo 読取テストの同一 group 寄せ) の採否判断を含む。
- **入れる**: [T-438] — `test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight`
  の `xdist_group(name="real_repo")` が canonical `real-repo` と**別 group**になっている未了 P2。
  R3 が塞ごうとした「実 repo 競合」の実体そのものなので、重複起票せず本 wave で扱う。
- **入れない (所有が別 wave)**: 個別テストの中身を速くする短縮
  (`dev-wave-suite-floor-recheck` が `_any_history_touches_path` を所有)。
  `s8c_preregistration` の git 時間予算 R1/R2 (`dev-wave-t553-git-budget` が所有)。
- **入れない**: production の受理集合を変える変更。walltime 上限の引き上げ**単独**での解決。

## 2. 確定済みユーザー裁定

- [T-692] R3 = **(a) 起票する**。原案は「s8c candidate / ruleops / その他の実 repo 読み取り
  テストを同一 xdist group へ入れ、既知の同時 git 競合を除く」であり、**目的はフレーク除去**である。
- 本 wave の依頼は **walltime 短縮**を主目的に置く。**この 2 つは向きが逆になりうる** —
  同一 group への寄せは直列化なので critical path を伸ばす。両立点を探すのが本 wave の設計課題。

## 3. 不変条件 (緩めない)

- D63 の競合閉包を緩めない: 実 repo working tree / 共有 ccbench submodule の writer と reader は
  単一 runner invocation 内で相互排他であり続ける。**速さのために排他を外さない** (規律 2)。
- 二個目の `xdist_group` を同一 node へ付けない (group 名結合で排他が壊れる、D63)。
- `REAL_REPO_SERIAL_NODES` と独立 golden (`test_real_repo_serialization.py`) の二重管理契約を保つ。
- 受理集合を変えない。速くなるだけで pass/fail が変わる変更を採らない。

## 4. 成果物影響 (DW-G05)

- 実装しない場合: 受入 1 走が 1379/2400 秒で、試験数の増加が続けば **walltime 超過で全走が
  rc≠0 になる**。そのとき producer / pilot / 本走の受入判定は「赤」ではなく「取得不能」になり、
  certified 選択・材料レポート・試行台帳の**更新経路そのものが止まる**。
- 排他を緩めて速くした場合: 実 repo 競合による偽の赤 / 偽の緑が混入し、受入結果が
  proof chain の根拠として使えなくなる。

## 5. 親の provisional 裁定 (攻撃対象)

- **(P1)** 本 wave の第一目的は wall 短縮、第二目的が競合除去である。両立不能なら
  競合除去を優先し、短縮は別案へ回す。
- **(P2)** 並列度 (`_NPROC_CAP` / `default_test_jobs`) は触らない。計算ノードでは既に affinity 全数で、
  2026-07-30 実測は 32→48 でほぼ改善なしだった。
- **(P3)** `DEFAULT_WALLTIME` の引き上げは根治ではないため単独では採らない。ただし
  「上げられない」ことが構造的欠陥なら、**短縮策と別建てで**指摘だけ返す。
- **(P4)** wall の律速は `real-repo` group の直列和である、と親は予想する。**未実測** —
  `measure1` の junit が出るまで設計を確定しない。外れたら段 4 で brief を書き換える。
- **(P5)** 分割するなら「reader 専用群を別 group へ出す」方向になる。ただし xdist に
  reader/writer 意味論は無いため、**分割の安全性は排他契約の再証明を要する**。

## 6. 並列分割方針 (子の所有)

- 段 2 プラン起草 1 本 (read-only)。入力に `measure1` の集計を渡す。
- 段 3 敵対相談 2 本: レンズ A = 「排他が壊れる / 偽の緑が出る」正しさ攻撃、
  レンズ B = 「短縮の見積もりが誤り / 測定が交絡」測定攻撃。
- 段 5 実装 1 本 (codex author)。段 6 レビュー 2 本 + fix。
- 計測解析スクリプトも実装面なので codex author が書く (親は書かない)。

## 7. 条件 dispatch の評価 (段 1 時点)

- `DW-O08` 成立 → submodule init 実行済み (rc=0)。
- `DW-O09` / `DW-O10`: **不成立と判断**。本 wave の変更面は test の分配 (marker / conftest /
  runner 引数) であり、凍結成果物の bytes を書く producer に触れない。
  ただし段 2 で `run_tests.py` 側へ手が伸びる案が出たら再評価する。
- `DW-O13` 成立の見込み (収集監査 gate を増やす可能性) → 段 2 前に読む。
- `DW-O20` 成立 → 実行済み (`check_wave_startup.py` rc=0、handoff は repo 外)。
