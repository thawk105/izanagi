---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t496-ruleops-inventory-diag
seq: 1
title: [T-496] ruleops inventory の exit 2 を診断可能にし、fail-closed 条件を実測で絞った (コード + docs、branch worktree-dev-wave-t496-ruleops-inventory-diag)
---

## 本文

- **診断欠落の機序は「ruleops が黙っている」ではなかった。** `tools/ruleops.py` は exit 2 の直前に
  必ず `ruleops: <reason>: <detail>` を stderr へ出している。失っていたのはテスト側で、
  `subprocess.run(..., capture_output=True, check=True)` が投げる `CalledProcessError` の
  **文字列表現は rc とコマンド列だけで stderr を含まない**。したがって修理対象は ruleops ではなく
  テストの診断経路であり、[T-496] が疑った「共有 `.git` の並行アクセス」は原因の候補にすぎない。
- **`test_ruleops.py` の子 process 起動を 1 本の診断経路へ集約した。** 非 0 rc のとき
  command・rc・stdout・stderr を assertion message へ載せる。ruleops の理由行は stderr の先頭に
  出るため先頭を必ず残して切り詰め、切り詰めた事実も message に残す。bytes と不正 UTF-8 は
  `errors="replace"` で扱う。素の `subprocess.run(..., check=True)` はこの file から 0 件になった。
- **exit 2 の理由を静的に全列挙した。** inventory 経路の git 呼び出しは `rev-parse` /
  `for-each-ref` / `ls-tree` / `cat-file --batch` / `log` で、すべて `--no-optional-locks` +
  `GIT_OPTIONAL_LOCKS=0` の読み取り専用であり index.lock を取らない。他プロセスの `git status` 由来の
  lock 競合とは独立である。並行アクセスで発火しうる理由は `git-unavailable` / `git-timeout` /
  `git-failed` / `head-moved` の 4 つに絞れ、**いずれも stderr の reason 行で一意に判別できる**。
- **`head-moved` の発火源を絞った。** 受入全走のテスト群に実 repo の HEAD を動かす git 操作は 0 件で
  (`orchestrator/tests/` を `add|commit|checkout|reset|stash|gc|repack|prune|worktree` で検索)、
  `run_tests.py` が実 repo へ打つ 3 つの git はいずれも pytest 起動前の preflight である。
  `head-moved` が出るとすれば**同じ worktree を触る外部アクター**がいた場合だけである。
- **probe で reachability を実測した** (scratch clone のみ、40.1 秒)。
  `head-moved` = 到達可能 (`HEAD moved during RuleOps query: <old> -> <new>`)、
  `git-timeout` = 到達可能 (21 秒の遅い git shim で 20.16 秒後に `git rev-parse timeout`。
  `GIT_TIMEOUT_SECONDS = 20` に対し実 repo の inventory は idle 1.03 秒)、
  並行 `git repack -a -d` / `git gc --prune=now` = **落ちなかった** (各 1 試行、rc=0 で
  2,595,597 bytes を完走)。試行 1 回なので「起きない」ではなく「1 試行では再現しない」である。
- **request 889456 の原因は特定していない。** 標本 1 件で当時の stderr は残っていない。
  本 wave が入れた診断は、次の再発を 1 回で原因層まで確定させるための罠である。
- **`tools/ruleops.py` は 1 byte も変えていない** (commit 前後で SHA-256 一致を確認)。
  fail-closed の意味論・exit code・閾値は不変、テストの受理集合も不変である。
  `GIT_TIMEOUT_SECONDS` の引き上げや retry の導入は fail-closed 閾値の変更にあたるため
  実装せず {{D:ruleops-failclosed-threshold-unchanged}} として裁定へ返す。
- **変異が実装の穴を 1 つ見つけ、fix した。** 初回 matrix で **M2 (assertion message から子の stderr を
  落とす) が SURVIVED した**。原因は pytest の assertion 書き換えで、失敗時の `AssertionError` には
  自前 message に続けて `+ where 23 = CompletedProcess(args=..., stdout=..., stderr=...).returncode`
  が付き、この repr が stdout・stderr・args を含むため、診断コードが何も載せなくても
  `"...sentinel" in message` が満たされていた (過剰決定、`DW-M03`)。`CompletedProcess` の repr は
  1 行の key=value 形式で `stderr:\n<内容>` の改行隣接を作れないため、その非対称を使って
  4 つの検査すべてを helper 自身の整形結果だけが満たせる形へ差し替えた。初回の SURVIVED は
  erratum として残す (`DW-M02`)。
- **fix を 1 回空振りさせた (自己申告)。** 上記 fix を「変異 baseline が緑判定を兼ねる」として
  実測せずに commit したところ、pytest が複数行 message の継続行を 2 space 字下げするため
  `"\nrc: 23\n"` が一致せず baseline が赤になり、harness 2 走を無駄にした。実装子は login node で
  pytest を走らせられず assert の逐語を検証できないので、**親の 1 走が唯一の検証点**である。
  3 回目の fix で字下げ幅に依存しない正規化へ替え、commit 前に実測した (91 passed、`-n 0`)。
- **変異事前登録を段 6 で 2 度訂正した。** (1) M3 の期待 node を `...preflight` と登録したが、
  xdist の loadgroup 下では失敗 node が `...preflight@real_repo` と記録されて MISMATCH になり、
  逆に `@real_repo` 付きで登録すると harness の collection 検査が「実在しない」と拒否する。
  **`tools/mutation_harness.py` はどちらの表記でも xdist group 付き node を事前登録できない**
  (F33 の同型)。runner へ `-n 0` を渡して xdist を外し、素の表記へ揃えて回避した。
  (2) `DW-M08` の新旧両走は、変更前 HEAD の clone ではなく**両層変異 M4** で構成した
  (production 変異 + 当該呼び出しだけを変更前の `check=True` 形へ戻す)。同じ worktree・同じ runner で
  差分が test 側の呼び出し形だけになるため、clone 方式より統制が効く。
- **変異実測**: baseline PASSED、**M1 / M2 / M3 / M4 = いずれも KILLED** (期待 node と一致、
  `mutation-ledger-v2.json`)。検出力の差は M3 と M4 の比較で示した — 同じ production 変異に対し
  **M3 (新経路) の失敗出力は `ruleops: git-failed: MUTANTREASONSENTINEL` を含み、
  M4 (変更前の呼び出し形) は含まず `subprocess.CalledProcessError: ... returned non-zero exit status 2`
  だけを残す**。両者とも赤になる = 受理集合は同じで、**残る理由だけが違う**。
  M2 は診断文字列を pin する変異なので、`DW-M08` に従い kill でなく
  **diagnostic sensitivity pin** として別枠に数える。
- **手順違反 1 件 (自己申告)**: S2 probe をログインノードで走らせたが、runbook §7.0 の手順で測った
  cgroup charged memory のピークは 567 MiB、certified peak = 567 + 128 = **695 MiB** で
  規範値 512 MiB を超えていた。事後的には計算ノード行きである。ただし §7.0 は**分類のための
  初回計測をどこで走らせるかを定めていない** — 値は一度走らせないと測れないため、
  新規スクリプトの 1 走目は必ずログインノードに落ちる。恒久対応は
  {{F:first-run-classification-site-undefined}}。
- **受入全走**: request 890142 = `6237 passed / 19 skipped / 0 failed` (816.53s、`-n 32`)、
  local main 11 commit を追加取り込み後の request 890171 =
  `6296 passed / 19 skipped / 0 failed` (657.71s、`-n 32`)。いずれも waiver なし。[T-496] が報告した
  `test_real_checkout_independent_maximum_package_and_runner_preflight@real_repo` の赤は
  この全走では再現しなかった。**再現しなかったことは修理の証拠にはならない** — 元の赤も
  単独走行では再現しなかったためである。本 wave が主張できるのは
  「次に再発したとき理由が残る」ことだけである。
- 子の工数: 段 5 実装が約 12 分、段 6 fix が 3 巡で約 3 分 / 4 分 / 3 分 (いずれも codex
  `gpt-5.6-sol`、effort=high、workspace-write)。実装子・fix 子はいずれも pytest を実走できず
  (login node)、**正しく「実装済み・未実走」と申告した**。テスト実測はすべて親が行った。
- 軽量版で走った (`DW-C00`)。設計択一が割れず (repo 既存 idiom
  `assert r.returncode == 0, r.stderr` が 20 箇所以上で確立)、正しさ防壁に触れず、
  受理集合が変わらないため段 2・3 と段 6 の review 子を省いた。所見ゼロを緑と数えず、
  変異 4 本で裏取りした (`DW-M02`)。

## 次の一手差分

### 完了

- [T-496] 子 process の失敗理由をテストの診断へ出し、inventory の fail-closed 条件を実測で絞った。
  診断は M1/M2 が pin し、検出力の純増は M3 と M4 の比較で示した。
  remaining: none
  base: 6a56d8df54c0bd3a7ca6cacb1e498b233b960e7c09cee61081079a1638e86b2c

### 新規

- {{T:ruleops-git-timeout-threshold}} **P3・新規**: `tools/ruleops.py` の
  `GIT_TIMEOUT_SECONDS = 20` は、実 repo の inventory 実測 1.03 秒に対し 20 倍の余裕しかない。
  高並列受入全走の負荷下で到達しうる (probe で reachability を実測済み) 一方、
  引き上げは fail-closed 閾値の変更であり本 wave の scope 外とした。閾値を上げるか、
  retry を入れるか、現状維持かを裁定する。判断材料は {{D:ruleops-failclosed-threshold-unchanged}}。
- {{T:first-run-classification-site}} **P3・新規**: runbook §7.0 は実行場所を cgroup charged
  memory のピークで決めるが、その値は一度走らせないと得られず、**未計測の新規スクリプトの
  1 走目を必ずログインノードに落とす**。`dispatch_compute` の `TASKS` も `tests` /
  `provenance` の 2 つに閉じており、任意 command を計算ノードへ送る経路が無い。
  §7.0 へ初回走行の規定を足すか、汎用 dispatch task を足すかを裁定する。詳細は
  {{F:first-run-classification-site-undefined}}。
- {{T:mutation-harness-xdist-group-nodes}} **P3・新規**: `tools/mutation_harness.py` は
  xdist の loadgroup marker が付く test node を事前登録できない。collection 検査は素の nodeid を
  要求し、失敗 node 抽出は `@<group>` 付きを返すため、どちらの表記でも matrix が通らない。
  本 wave は runner へ `-n 0` を渡して回避したが、並列でしか出ない挙動を変異で測りたい wave では
  回避できない。突き合わせ前の正規化を harness 側へ入れる (F33 の機械化)。
