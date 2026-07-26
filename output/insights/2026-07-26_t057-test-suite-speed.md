# [T-057] テストスイート全走が遅い原因の実測と修正 (2026-07-26)

worklog 2026-07-26 (13) の一次資料。計測環境・実測値・棄却した仮説・変異結果・先送り項目を置く。
実装は `orchestrator/tests/` のみ (本番コード 0 byte)。

## 1. 計測環境

- 計算ノード **bnode003** (Intel Xeon Platinum 8468 / 48 physical core / HT 無効)。PBS `gen_S`、
  1 node 専有要求。job = 871555 (原因調査) と 871573 (before/after)。
  単独性は job 冒頭で確認 (非 root プロセスは system daemon のみ、loadavg < 6)。
- **runbook §7 によりログインノードでは全走しない。** 診断用の単一 process / `-n 8` の小さい probe だけ
  ログインノードで実施した。
- `/usr/bin/python3` 3.10.12 + pytest 9.1.1 + pytest-xdist 3.8.0。TMPDIR は conftest 既定の `/dev/shm`。
  **計算ノードの既定 `python3` は Intel Python 3.9 で pytest が collect 不能** (871553 が 1107 error)。
- repo は Lustre (`/home`)。commit 数 = 712。

## 2. 原因

`t080_freeze_migration.verify_receipt(root=<実 repo>)` = **1 回 22.4 秒**。内訳 (親が `_git` を
計測 wrapper で包んで実測):

| git 呼び出し | 本数 | 時間 |
|---|---|---|
| `cat-file blob` | 1607 | 9.2s |
| `diff-tree --root` | 58 | 8.5s |
| `cat-file --batch-check` | 96 | 1.8s |
| `ls-tree -z` | 62 | 0.4s |
| その他 | 22 | ~0.2s |
| **合計** | **1845** | 20.1s (全体の 90%) |

`cat-file blob` 1607 本の**異なる oid は 52 個だけ** = 30.9 倍の重複。`_build_repin_report` が
commit ごとに同じ blob を取り直すため、コストは **commit 数に比例して伸びる**。

テスト側の入口は共有 helper `_run` (`test_s8b_oracle_driver.py`) が `root=ROOT` を固定で渡すこと。
姉妹 helper `_run_required_preflight` / `_run_required_fixture` は解決を patch していたが `_run` は
していなかったため、oracle driver 系の 42 node が 1〜10 回ずつこれを払っていた。

時系列の整合: `output/task-runs/*/events.jsonl` の全走実測は 2026-07-20〜21 に **9.5〜13.9 秒**
(外れ値 37.8 / 61.4 秒が各 1 回)。T-080 receipt 系テスト投入後に 239 秒 (7/25) → 1811 秒 (7/26)。
commit 数は 571 (7/20) → 712 (7/26)。

## 3. 二段目の原因 (修正の途中で実測)

process 内 memo だけにすると、**xdist の worker ごとに実解決が走る**。`-n 32` では 32 本が同時に
走り、1845 × 32 ≈ 59,000 本の git 起動が 48 core を奪い合って **1 回 22 秒が 129 秒**へ膨らんだ
(AFTER1 の duration で 11 本が各 129 秒)。各 worker の最初の memo テストがこれを吸うため、
そこが makespan になっていた。→ session 限定 cache (flock) で 1 セッション 1 回へ落とした。

## 4. before / after (同一ノード・同一順序・同一ジョブ内)

| run | 条件 | wall | 結果 |
|---|---|---|---|
| BEFORE1 | 修正前 `-n 32 --dist loadgroup` (cold) | **413 秒** | 1 failed / 3057 passed / 19 skipped |
| AFTER1 | process 内 memo のみ | **200 秒** | 0 failed / 3061 passed / 19 skipped |
| BEFORE2 | 修正前 (warm 再走) | **586 秒** | 1 failed / 3057 passed / 19 skipped |
| AFTER2 | + session 共有 cache (最終形) | **132 秒** | **0 failed** / 3062 passed / 19 skipped |

参考: 別ジョブ (871555) の修正前 cold = 327 秒。**修正前は 327〜586 秒とばらつく** (充填の競合)。
worklog 記録のログインノード 1811 秒に対しては約 14 倍の短縮。

duration 合計 (work) は 4654 / 7328 秒 (修正前) → 1660 秒 (最終形)。

**修正後の makespan 下限は 81 秒** = `test_v3_cli_subprocess_returns_rc_3_on_protocol_violation`
(子プロセスが自前で実解決 2 回。session cache は子へ届かない)。次に唯一の実解決 (負荷下で約 50 秒)。

## 5. 並列度の実測 (「並列度を上げる」方向は効かない)

- 修正前に real-repo group を除外して `-n 48 --dist load` にすると **427 秒** で、group を含む
  `-n 32` の 327 秒より遅い (job 871555 run D)。
- 効いたのは仕事を消すこと (重複解決の除去) であって worker を増やすことではない。
- `tools/run_tests.py` の `_NPROC_CAP=32` は変更していない。

## 6. 速度だけでなく信頼性の問題だった — 修正前に 3 種の flake を実測

修正前の全走 3 回で、**毎回 1 件ずつ別のテストが落ちた**。いずれも subprocess 系で、
59,000 本の冗長な git 起動による飢餓と整合する。修正後 (AFTER1 / AFTER2) は 0 failed。

1. `test_pegasus_tools.py::test_submit_dry_run_does_not_resolve_cluster_commands` —
   `copytree` が並列 worker の bytecode 一時ファイル (`__pycache__/*.pyc.<tmp>`) を拾い、
   rename で消えた後に読んで `shutil.Error`。**本 wave で修正** (`__pycache__` を除外、3 箇所)。
2. `test_dev_waves_integration.py::test_fake_manifest_run_id_is_bound_to_path_namespace` —
   期待 `NONZERO_EXIT` に対し `TIMEOUT` を観測 (負荷で子が締切に間に合わない)。**未修正 → [T-117]**。
3. `test_dev_waves_worker.py::test_stdout_stderr_combined_cap_minus_exact_plus_one_boundaries` —
   子が stdout/stderr 0 byte しか出せず log 上限判定が外れる。**未修正 → [T-117]**。

## 7. 棄却した仮説

- **ログインノード `/dev/shm` の残留 temp dir 40,280 個** (`izanagi_s4loop*` 10192、
  `izanagi_s8at*` 8882、`s8b-selector-*` 5626 等 = production の `tempfile.mkdtemp` 後始末漏れを
  テストが大量に踏んだもの) → mkdtemp の実測は crowded 5.8µs vs 清浄 dir 5.5µs で**速度原因ではない**。
  衛生問題としては残る → [T-118]。
- **TMPDIR が Lustre に落ちて fsync barrier を踏む経路** → 本 run では conftest が `/dev/shm` を
  選んでおり非該当。
- **real-repo loadgroup の直列化が主因** → 直列実測 201 秒で makespan 327 秒の一部でしかなく、
  その 201 秒自体も同じ receipt 解決が中身だった。

## 8. 実装 (テストのみ・本番 0 byte)

commit: f2379ee → f5f5a82 → 086550b → bb1bd55 (branch `worktree-dev-wave-t057-test-speed`)。

- `orchestrator/tests/real_repo_receipt_memo.py` (新規、テストではなく支援モジュール):
  import 時点の本番 `_resolve_t080_receipt` を捕まえて memo する (MigrationError → 構造化 refusal の
  翻訳まで本番のまま通る)。canned 値は作らない。ROOT 以外は assert で拒否。
  xdist では run ID + HEAD で key 付けした session cache (flock、tmp → `os.replace`、6 時間で掃除) を
  使い、読めない/型違いは実解決へ倒す。
- 適用は **opt-in**。`_run` (既定 on) と実 repo 直接呼び出し 5 箇所 + driftguards 2 箇所。
- **opt-out が必須だった 2 関数 (3 item)**: `test_run_block_resolves_receipt_once_...` (2 param) と
  `test_run_block_rejects_receipt_epoch_drift_before_campaign_start_g4`。解決回数・世代差そのものが
  検査対象で、memo はその機序を消す。**probe で実装前に実測して判明した** (global memo で 3 item が赤)。
- **二重 import の罠**: テストは `campaign.s8b_oracle_driver` を import するため、
  `orchestrator.campaign.s8b_oracle_driver` を patch すると memo が 1 度も発火しない静かな空振りに
  なる (最初の probe が実際に踏んだ)。

## 9. 変異事前登録と実測 (親)

新設 gate = positive control 4 本 (`test_s8b_binding_driftguards.py`、実 repo を歩かず 0.22 秒)。
harness = `$CLAUDE_JOB_DIR/tmp/t057/mutate.py` (アンカー一意性 assert・注入実在確認・
元テキストとの内容一致で復元検査)。

| # | 変異 | 結果 | 帰属 |
|---|---|---|---|
| S1 | memo が戻り object を `copy.deepcopy` して返す | **KILLED** (identity control 2 本) | 新 control |
| S2 | patch 先を `orchestrator.campaign.s8b_oracle_driver` (テストが使わない側) にする | **KILLED** | 新 control |
| S3 | ROOT guard の assert を無効化する | **KILLED** (負例 control。guard 無しでは tmp root でも実解決 22.9 秒を走らせて値を返す) | 新 control |
| S4 | memo を opt-in から無条件適用へ変える | **KILLED** (既存 3 item) | **非帰属 control** |

S1〜S3 の変異対象は本 wave で新設したモジュールであり、変更前 HEAD 側のテスト集合は構造的に
検出不能 (走らせていない)。S4 は probe による実測。

## 10. 先送り・裁定へ返す項目

- **[T-116] 本番 `_build_repin_report` の blob 再取得 30.9 倍** → 裁定パッケージ。
  production 非改変の wrapper で実測すると `verify_receipt` は **21.9 秒 → 13.1 秒 (1.7 倍)**、
  結果は byte 同一 (state / refusals / validation_head / observation)。`cat-file blob` の実発行は
  1607 → 52 本。残りは `diff-tree --root` 58 本 (8.5 秒) 等。テスト側 memo とは独立に効き、
  CLI 子プロセス経路 (makespan 下限の 81 秒) にも効く唯一の手。
  worklog 2026-07-26 (12) の条件 (本番に触る改善は裁定へ返す) に従い本 wave では実装していない。
- **[T-117] 残 tail と負荷依存 flake 2 件**: CLI 子プロセス系 (81 秒 / 30 秒)、
  `_t080_stub_free_e2e_repo` 系 7 本 (各 20〜27 秒。17 秒が subprocess 待ち、fork 779 本)、
  §6 の flake 2 と 3。
- **[T-118] `/dev/shm` の残留 temp dir 40,280 個**: production の `mkdtemp` 後始末漏れ (衛生)。

## 11. ワークフローの逸脱 (正直な記録)

本作業は `/dev-wave` として開始したが、段 3 (敵対相談 2 本) の途中でユーザーが中断を指示し、
軽量ワークフロー (実測 → 実装 → 検証 → commit) へ切り替えた。したがって
**独立コンテキストの敵対レビューは入っていない**。代替として親が行ったのは、
probe による前提の実証 (§8 の opt-out 必須性と二重 import)、変異 4 件の実測 (§9)、
同一ノードでの before/after 反復計測 (§4) である。段 2 の codex プラン (23KB) は
実装前に読んで call site 列挙に使った (逐語は job tmp、要点は本文へ吸収)。
