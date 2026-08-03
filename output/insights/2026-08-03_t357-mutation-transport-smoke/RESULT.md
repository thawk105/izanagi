# 生死確認 (transport smoke) の結果

anchor = `ea6ca433eb83d666ec64f3629cc35c769a2b5c19` (2026-08-03 時点の main)
spec = `driver/spec.json`、sha256 `1d13164c2830896656bdc3b12261756996decef018c9fd83dd4f7f495de2d70e`
変異 = `tools/spool_fold.py` の 3 guard (filename 不一致 / symbol 重複 / malformed placeholder 残留)
test command = canonical 全走 `tools/run_tests.py -rf -p no:cacheprovider` (**pytest 引数列は同一。
ただし argv[0] の綴りは leg1 `/usr/bin/python3.10` / leg2 `/bin/python3.10` で異なる。下記参照**)
実行場所 = 使い捨て worktree (wave worktree と main は変異させていない)

## 結論: GO

`compare_verdicts.py` (段 6 で 3 度厳格化した最終版、gate 84 件) の判定 = **GO** (rc=0)。
比較は **ledger の全 leaf field を再帰的に**行い、除外した field は理由つきで全列挙している。

| | leg 1 = 現行 (1 変異 = 1 qsub) | leg 2 = 束ね (1 ジョブ内 local) |
|---|---|---|
| collection | PASSED / 正規化後 5281 key | PASSED / 正規化後 5281 key (**件数・内容・重複度・順序が一致**) |
| collection の生 nodeid 列 | 5282 件 | 5282 件 (**順序まで一致**) |
| baseline | PASSED rc=0 failed=[] | PASSED rc=0 failed=[] |
| G01 | KILLED / `test_n01_...` / match=True | 同一 |
| G03 | KILLED / `test_n03_...` / match=True | 同一 |
| G04 | KILLED / `test_n04_...` / match=True | 同一 |
| `test_command[1:]` | 一致 | 一致 |
| `pytest_distribution_sha256` | `57e75bdc...` | 同一 |
| `entrypoint_sha256` (`run_tests.py`) | `ffd0ef92...` | 同一 |
| `repo_tree` | `454802197c4f...` | 同一 |
| `tool_sha256` | `25e76736...` | 同一 |
| 終了後の worktree | clean、HEAD=anchor、diff なし | clean、HEAD=anchor、diff なし |

**collection の収集 node 列は生 5282 件・順序まで一致した。** ledger が記録する 5281 は
`_normalize_node` が nodeid 中の `\` を `/` に潰した後の key 数であり、生の test case 数ではない
(衝突するのは `...[output//x]` と `...[output\\x]` の 2 件)。

### 残った差 (すべて分類・明示済み)

- **同一実体の別綴り 2 件**: `procedure.test_command[0]` と `runner_identity.command[0]` が
  `/usr/bin/python3.10` 対 `/bin/python3.10`。両 ledger の**解決済み `executable_path` は
  どちらも `/usr/bin/python3.10`** であり (harness 自身が `resolve(strict=True)` した値)、
  login node で `/bin -> usr/bin` の symlink も実測した。
- **経路差**: `runner_mode`、`receipt_path` / `job_stdout_path` (dispatch のみ)、`duration_s`、
  時刻を含む stdout とその派生 hash、`dispatch_entrypoint_*`、`date` / `updated_at`。
- **非等価だが verdict に効かない、名前付き観測 1 件**: `runner_identity.executable_sha256` が
  leg1 `7d51cd6b...` / leg2 `d6bca2b8...`。同じ解決 path・同じ version 3.10.12 でありながら
  bytes が異なる = **login node と計算ノードで `/usr/bin/python3.10` の実体が違う**。
  含意: **leg 1 (現行 dispatch) の `runner_identity` は login node の interpreter を記録しており、
  実際に pytest を走らせた計算ノードの interpreter ではない。** leg 2 (束ね) は実際の runner を
  記録する。**証拠の忠実さは束ね側が上である。**

## 削減量 (実測)

| | leg 1 (現行) | leg 2 (束ね) |
|---|---|---|
| ledger の `duration_s` 合計 | 1567.5 s | 992.2 s |
| 内側 pytest 所要の合計 (collection 含む) | 988.2 s | 989.7 s |
| **harness 外側との差** | **579.3 s** | **2.5 s** |
| 投入〜完了の wall | 14:49:56 → 15:16:07 = 1571 s | 15:37:29 → 15:58:18 = 1249 s |
| 内訳 (wall) | 5 回それぞれが順番待ちを払う | queue 250 s + job elapse 1004 s |

- **内側の仕事量はほぼ同じ** (988.2 s 対 989.7 s、差 0.15%)。束ねても pytest は速くならない。
  消えるのは順番待ちだけである。
- 「harness 外側との差」であって純粋な scheduler 待ちではない。dispatch 側は receipt 検証・
  qstat polling・accounting 猶予も含む。
- この 3 変異の smoke での削減は wall で **322 s (20%)**。
- **41 変異の本走への外挿**: T-243 の `2026-08-02_t243-parallel-docs-spool` ledger を全 41 record
  再集計すると、**42 execution run (41 変異 + baseline) の paired 差の合計が 9161.6 s (2.545 h)**。
  collection は `--collect-only` が `in Xs` 行を出さないため内訳を分離できず、この合計に含めていない。
  束ねならこれが 1 回分の順番待ち (今回 250 s) に縮む。→ **1 matrix あたり約 2.5 時間の削減**。
  ただしこれは**当該 matrix の観測値からの条件付き予測**であり、41 変異規模の束ね実行は未実測である。
- **削減量はキュー混雑に依存する。** 今回の leg 1 の per-run 差は 24.9 / 245.2 / 21.1 / 264.0 s と
  ばらついた (空いていれば ~21 s、前にジョブがいれば ~250 s)。T-243 台帳の一貫した ~228 s は
  混雑時の値である。

## 束ね 1 回目の失敗 (erratum、`DW-M02`)

leg 2 の 1 回目 (request 878505) は **baseline が赤**で fail-closed 停止した (rc=2)。
証拠は `leg2-attempt1-ledger-erratum.json` と `driver/submit_leg2_bundle.sh.attempt1`。

- 19 failed / 5244 passed / 19 skipped。失敗はすべて `orchestrator/tests/test_t126_pegasus_tools.py`
- 根本原因 = `TypeError: dataclass() got an unexpected keyword argument 'slots'`。
  `slots=True` は Python 3.10 以降の機能
- 外側 pytest は `/usr/bin/python3.10` (3.10.12) で走っていたが、**テストが起動する入れ子 subprocess
  だけが 3.10 未満の python を掴んでいた**
- 計算ノードの既定 PATH (attempt 2 の診断出力で実測):
  `/system/apps/ubuntu/20.04-202210/oneapi/2022.3.1/intelpython/latest/bin` が `/usr/bin` より前にある
- `dispatch_compute._job_script` は `command -v` で python3.10 を選び
  `export PATH="$(dirname "$selected"):$PATH"` を行う。使い捨て投入器はこれを写していなかった
- attempt 2 で `_job_script` の interpreter 選択・probe・PATH 先頭化を等価に写したところ緑になった

**この失敗が示したこと (恒久設計への一次証拠):** 束ね投入器は sanctioned job script の環境正規化を
逐語で写さないと、内側の suite は同じ suite ではなくなる。手書き `submit_*.sh` を新設する案より、
`dispatch_compute` の `_job_script` を再利用する案が有利に働く材料になる。

**この失敗が示していないこと:** attempt 1 は baseline で停止しており、**変異は 1 件も当たっていない**。
したがってここで確認できたのは **baseline の fail-closed と、もともと clean な tree が保たれたこと
だけ**である。「walltime kill 後の復元が働いた」証拠にはならない。

## この smoke が示していないこと

`DW-G01` の生死確認であって、移設全体の安全性の証明ではない。次はいずれも**未確認**である。

1. **cross-node flock**。`_lock_path_for` は `tempfile.gettempdir()` = node-local `/tmp` を使う。
   計算ノードへ移すと「同一 repo で同時 1 本」の保証が bnode 間で消える。`/work`・`/home` は
   Lustre を `flock` mount option 付きでマウントしているが、cross-node で効くか、
   silent fail-open しないかは測っていない。本 smoke は両 leg を**逐次**に走らせて回避した。
2. **walltime kill 後の復元**。NQSV が walltime 超過時に SIGTERM を送るか、grace があるかは未確認。
   SIGKILL なら harness の `finally` 復元は走らない (F32)。今回は walltime に到達していない
   (要求 2700 s、実 elapse 1004 s)。
3. **`--resume` の回収能力**。変異が当たったまま落ちた tree からは `_assert_clean_tracked` が
   先に止めるため resume できない。今回は発生していない。
4. **親 dispatcher の `total_deadline`**。`dispatch_compute.py:1182` は
   `submitted_at + walltime_s + overall_grace_s` で、**順番待ちを実行時間から差し引く**。
   超過時は `_best_effort_qdel` (:1381) が**走行中のジョブを qdel** する。今日の dispatch 経路にも
   ある潜在欠陥で、数時間の束ねジョブでは発火確率が上がる。本 smoke は独立した使い捨て qsub を
   使ったため、この経路を通っていない。
5. **恒久 dispatcher 経路そのもの**。`mutation` task、argv/env validator、transport 証拠、hook 層は
   1 行も実装・検証していない。
6. **collection の並列度差が安全かどうか**。`_collection_command` は dispatch のときだけ `-n 0` を
   足す (`mutation_harness.py:928-942`)。今回は収集列が一致したが、**そもそも
   `_observed_status` は mutation の stdout の rc と failed set しか見ないため、
   期待 node 以外の collection 差は構造的に verdict へ届かない**。したがって
   「`-n 0` 対 既定 48 は安全」という結論はこの smoke からは出せない。
7. **規模と偏り**。3 変異・単一 subsystem・すべて単一 node の KILLED 型である。
   複数 node 失敗、SURVIVED、TIMEOUT、`hang_risk`、resume は含まれていない。
8. **41 変異規模での連続実行**。今回のジョブ elapse は 1004 s。本走想定の約 3 時間は測っていない。

## 副作用と残留物

- 使い捨て worktree (証拠を `evidence/` へ固定した**後**に `git worktree remove` + `prune` した)
- login node と bnode の `/tmp/izanagi-mutation-<hash>.lock` (空 inode が残りうる)
- scheduler の `.o` / `.e` (`evidence/scheduler-logs/` へ固定済み)
- **wave worktree と main は 1 byte も変異していない** (両 leg の前後で実測確認)
