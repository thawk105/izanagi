# dev-wave の機械時間 — 実測、律速の同定、次 wave の材料 (2026-07-30)

read-only の測定。**実装は伴わない。** 本番 repo は変更していない (git メンテナンス系の測定はすべて clone 上)。
次 wave の裁定材料として残す。

## 0. 計測環境

すべて Pegasus 計算ノードの PBS ジョブ内で実行した。単独性は各ジョブ内で確認している
(他ユーザーの %CPU>1 プロセスなし)。

| job | node | 内容 |
|---|---|---|
| 874102 | bnode111 | 全走 3 走 + durations + targeted 4 本 + provenance 帰属 + 軽量検査 |
| 874131 | bnode111 | clone 上の `git gc` 効果 + 並列度掃引 (16/48/64/96) |
| 874209 | bnode021 | 全走の gc 有無 A/B + collection 順 A/B |
| 874241 | bnode021 | 全走の `/home` 対 `/scr` (ノード内蔵 NVMe) A/B + 最長 node 単体 |
| 874258 | bnode090 | gc の分解 (commit-graph のみ / repack のみ) |

commit 範囲は測定中に他セッションの作業で 542 → 553 件へ動いた。arm 間比較は同一 job 内でのみ行う。
ログインノードでの初期測定 (08:10〜09:28) は §6 の運用所見としてだけ使い、値の正本にはしない。

## 1. 1 回あたりの wall

| 行為 | wall | 補足 |
|---|---|---|
| 受入全走 `run_tests.py` | 207 秒 (206.6 / 208.0 / 209.0) | 3891 passed / 19 skipped、CPU 1111 秒 |
| `check_ai_provenance.py` | 128 秒 (542 件) / 149 秒 (553 件) | 100% が git subprocess。呼び出し 2963 回 |
| targeted `test_s8b_oracle_driver.py` | 117 秒 | 82 passed |
| targeted `test_dev_waves_integration.py` | 23 秒 | 80 passed |
| targeted `test_check_ai_provenance.py` | 3.1 秒 | 116 passed |
| targeted `test_campaign.py` | 2.5 秒 | 168 passed |
| `ruleops.py check` | 0.95 秒 | 受入形の全走ごとに preflight で毎回走る |
| `check_docs.py` | 0.45 秒 | |
| `check_wave_startup.py` | 0.19 秒 | |
| `check_codex_agents.py` | 0.10 秒 | |
| hooks (`guard_bash` / `guard_read` / `guard_write`) | 0.020 / 0.019 / 0.020 秒 | python 起動 0.014 秒が支配 |
| pytest の収集のみ | 1.4 秒 | |
| C++ ビルド | 0 秒 | ログインノード・計算ノードとも `g++-13` 不在で実ビルド群は skip |

## 2. wave 1 本あたりの回数 (親 transcript 6 本の Bash 呼び出しを機械集計)

| 行為 | 回数 |
|---|---|
| 受入全走 | 2〜7 |
| `check_ai_provenance.py` | 2〜7 |
| `check_docs.py` | 5〜23 |
| `git commit` | 2〜8 |
| `codex exec` (親起動分) | 3〜8 |
| ツール呼び出し合計 (= hook 発火数) | 252〜303 |

親が直列に待つ機械時間は **全走 7〜24 分 + provenance 4〜15 分**。
`check_docs` / `ruleops` / `check_wave_startup` / hooks は合計 30 秒未満で、最適化の対象価値がない。

変異 matrix は harness (job tmp) が `python -m pytest <対象> -q -rf` を**直列・xdist なし**で
1 変異ごとに回す。対象ファイル次第で 1 本 2.5〜117 秒。T-180 は 13 走 (初回 10 + 再照準 3)。

## 3. 律速の同定

### 3.1 `check_ai_provenance` = git 呼び出しの山

| 呼び出し | 回数 | 合計 | 割合 |
|---|---|---|---|
| `log --full-history --no-renames -S` (commit ごとの pickaxe) | 542 | 92.0 秒 | 72.2% |
| `merge-base --is-ancestor` | 558 | 17.9 秒 | 14.1% |
| `show -s --format=%s` / `%B` | 1084 | 11.5 秒 | 9.0% |
| その他 | 779 | 5.9 秒 | 4.7% |

commit ごとに ancestry 全体を走査する構造のため、commit 数に対して二乗で伸びる。

### 3.2 全走 = `real-repo` xdist group の直列鎖 145.2 秒

`--dist loadgroup` は同一 group を 1 worker に固定するため、group の直列和が wall の下限になる。
値は 874102 の `--durations=0` 出力から、`conftest.py` の `REAL_REPO_SERIAL_NODES` 正本と
突き合わせて集計した (node id の `@real-repo` 接尾を外して照合する)。

| node | 時間 |
|---|---|
| `test_s8b_binding_driftguards.py::test_run_block_broken_binding_manifest_refuses_and_writes_nothing` | 72.2 秒 |
| `test_s8b_oracle_driver.py::test_cli_subprocess_returns_rc_2_on_gate_refused` | 41.0 秒 |
| 残り 40 node | 32.0 秒 |
| **合計** | **145.2 秒** |

後者の原因は特定できた。この test は `subprocess` で driver を実 repo (`--root ROOT --freeze REAL_FREEZE`)
に対して起動するため、T-057 / T-117 が入れた**プロセス内 memo (実 receipt 解決 22.4 秒、
active 世代解決 4.4 秒) が子プロセスに効かない**。

ungrouped 側の最長 node は `test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5` の 107.8 秒。
単体で走らせると 104.4 秒 wall / 98.2 秒 CPU = **CPU 律速**であり、置き場所を変えても縮まない
(`/scr` で 100.4 秒)。T-080 の base fixture は `_T080_E2E_BASE_CACHE` がプロセス内 memo のみのため、
worker ごとに 15〜22 秒かけて再構築される (2026-07-27 insight の施策 #1、未実装)。

work の分布: 上位 20 node で 64%、`test_s8b_oracle_driver.py` だけで 69.5%、
0.1 秒未満の 924 node は合計 33.5 秒。

## 4. 効くと確認できた施策

### 4.1 git のメンテナンス (コード変更なし)

本番 repo は loose object 6223 個 (108.75 MiB)、pack は 5.90 MiB、commit-graph は 2026-07-17 のまま。
loose object 数が git の自動 gc 閾値 6700 の直下にあり、自動 gc が一度も発火していない。

| 処置 | 処置コスト | provenance | `merge-base` | pickaxe | `show -s` |
|---|---|---|---|---|---|
| なし | — | 149.4 秒 | 103.8 ms | 639.2 ms | 64.1 ms |
| `commit-graph write --reachable` のみ | 0.28 秒 | 103.2 秒 | 5.6 ms | 388.1 ms | 56.7 ms |
| `repack -a -d` | 46.3 秒 | 20.4 秒 | 9.1 ms | 14.5 ms | 8.2 ms |
| `gc` (別 job、542 件時) | 44.5 秒 | 128.4 → 18.4 秒 | 4.9 ms | 9.4 ms | 5.0 ms |

出力は 3 arm すべて同一 (`553 件、違反なし`、forward-correction の対象・訂正 commit も一致)。
`commit-graph write` は object store に触れないため完全に非破壊。

### 4.2 `real-repo` group の 2 node

全走の下限 145.2 秒の 78%。subprocess 越しに実 receipt 解決をやり直している経路へ、
ディスク上の共有 memo か事前解決済み成果物を渡せば削れる見込み。

### 4.3 T-080 base fixture の worker 間共有

最長 ungrouped node 107.8 秒の主因。base を 1 回だけ作り各 node へ実体コピーを渡す案は
2026-07-27 insight の施策 #1 と同じで、当時から未実装。

### 4.4 テストをノード内蔵 NVMe で走らせる

同一 job 内 A/B: `/home` 229.8 / 222.0 秒 → `/scr` 201.7 / 191.3 秒 (−13%)。
system time は 249.9 → 78.2 秒。ただし §3.2 の下限には効かない。

### 4.5 [T-173] pickaxe のアルゴリズム置換 (登録済み)

git メンテナンスを入れると 18〜20 秒まで落ちるため緊急度は下がるが、
commit 数に対する二乗の伸びは構造として残る。

## 5. 効かないと確認できた施策

| 施策 | 実測 | 判定 |
|---|---|---|
| 並列度を上げる | `-n 16` 215.8 / `-n 32` 207 / `-n 48` 147.8 (赤 1) / `-n 64` 217.8 (赤 3、worker 落下による再割当て痕跡) / `-n 96` 197.8 (赤 42)。別 job の `/scr -n 48` は 197.5 秒で 147.8 秒を再現せず | 不採用。速度が非再現で、赤を増やす |
| 重いファイルを collection 先頭へ | 234.9 秒 (対照 237.2 / 219.3 秒) | 効果なし。xdist の割当は動的で、順序仮説は成立しない |
| `git gc` による全走短縮 | 228 → 221 秒 (走行間ばらつき 18 秒の範囲内) | 効果なし。gc が効くのは履歴監査だけ |
| TMPDIR を NVMe へ | 205.7 秒 (対照 209.0 秒) | 効果なし。conftest が既に `/dev/shm` を使う |
| hooks・軽量検査の最適化 | wave あたり合計 30 秒未満 | 対象価値なし |

## 6. 運用上の所見

- **ログインノードでの全走が無言でハングする**: xdist worker 落下後に CPU 0.7% で 10 分放置される事象を 2 回、
  `rc=247` の異常終了を 2 回観測した。計算ノードでの 12 走はいずれも安定。
  timeout を付けない限り wave の wall を静かに食う。
- **ログインノードでのみ赤が出た**: `test_s8b_oracle_driver.py` の T-080 系が全走で 2 件、単独走で 8 件落ちたが、
  同一 checkout・計算ノードでは再現しない (rc=0)。実装差分ではなく環境要因。
- **`test_dev_wave_land.py::test_merge_child_inherits_lock_fd_if_helper_is_killed`** は計算ノードの clone 上で
  4 走中 3 走で落ちた。本番 checkout では落ちていない。
- **task-run 台帳が 2026-07-21 以降空**: `IZANAGI_TASK_RUN_ID` が opt-in で dev-wave の契約に入っていないため、
  全走の duration が自動記録されていない。
- **変異 harness は直列・xdist なし**: 対象ファイルが重い場合、`tools/run_tests.py` 経由にするだけで縮む
  (例: `test_dev_waves_integration.py` は直列 57 秒相当 → 並列 23 秒)。

## 7. 次 wave の材料 (scope = 全走の下限を下げる。ユーザー裁定 2026-07-30)

以下は**材料であり brief ではない**。段 1 は自分で前提を実測し直すこと。

### 7.1 対象

1. `real-repo` group の 2 node (§3.2) — subprocess 越しでも効く共有経路を入れる
2. T-080 base fixture の worker 間共有 (§4.3)

### 7.2 不変条件 (壊してはいけないもの)

- 実 repo 接触テストの単一 runner invocation 内排他 (D63、`conftest.py` の `REAL_REPO_SERIAL_NODES`) を弱めない。
  group から node を外す設計を採るなら、その node が実 repo / 共有 submodule の writer 窓に触れないことを
  コードで示す
- 共有 memo は検査を弱める経路になりうる。解決結果が本物と一致することをテストで固定し、
  古い値・空の値で緑になる経路を残さない
- base fixture の共有は read-only とし、各 node へは独立した実体コピーを渡す
  (テストが受け取った repo を破壊的に変異させるため、共有実体を渡すと相互汚染する)
- 共有をまたぐ書き込みは単一走行 guard (`flock`) を持ち、取得失敗で fail-closed にする

### 7.3 事前登録する変異の候補 (DW-M01 の実効 gate 照準)

- 共有 memo が古い / 空の解決結果を返しても緑になるか (= 検査が効いていない変異)
- `flock` 取得失敗時に fail-open して共有 base を再構築する変異
- 各 node へ実体コピーでなく共有 base をそのまま渡す変異 (破壊的変異の相互汚染を検出できるか)

### 7.4 受入 (すべて計算ノードの PBS ジョブで測る)

- 受入全走 rc=0
- `real-repo` group の直列和を before/after で実測する (`--durations=0` 出力を
  `REAL_REPO_SERIAL_NODES` と突き合わせて集計。before = 145.2 秒)
- 最長 ungrouped node の before/after (before = 107.8 秒)
- 全走 wall の before/after (before = 207 秒、同一ノード・同一並列度で比較する)
- 変異 matrix 全 KILLED、復元後 byte 一致

## 8. git メンテナンスの手順 (ユーザー裁定 = 他セッションが静穏になってから実行)

1. 静穏の確認: `pgrep -u tanab -a claude`、`pgrep -u tanab -a codex`、`qstat` で稼働中の wave が無いこと
2. `git -C <repo> commit-graph write --reachable` (0.28 秒、object store 非破壊)
3. `git -C <repo> gc` (44 秒)
4. 検証: `python3 tools/check_ai_provenance.py` が rc=0 かつ件数が実行前と一致すること
5. 恒久化の選択肢 (裁定事項): `git maintenance` への登録 / dev-wave 段 9 での実行 / `gc.auto` の引き下げ
