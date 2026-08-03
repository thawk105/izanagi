# [T-361] / [T-362] 実測結果 — Lustre cross-node flock と NQSV walltime signal

実測日: 2026-08-04 (JST)。機体: Pegasus (筑波大 CCS)、queue `gen_S`、project `SFC`。
driver commit: `d1c28e2` 系列 (本ディレクトリの `driver/`)。
**判定基準は実測前に `verdict-preregistration` として固定した** (本 wave の手順書は `README.md`)。

---

## 1. [T-362] NQSV は walltime 超過時に **SIGKILL を直接送る** — `finally` は走らない

**これは危険側の結果であり、D130 決定 (3) 条件 3 は既定構成では充足しない。**

### 一次証拠 (スケジューラ自身の宣言)

request `882048.nqsv` の stderr 先頭行:

```text
%NQSV(INFO): Batch job received signal SIGKILL. (Exceeded per-req elapse time limit)
```

**これは推論ではなく NQSV 自身の出力である。** signal 種別を「観測されなかったこと」から
推定したのではない。

### 会計 (同 stderr の NQSV 会計 block)

```text
Request ID:             882048.nqsv
Number of Jobs:         1
Started Request Time:   Tue Aug  4 00:50:36 2026
Ended Request Time:     Tue Aug  4 00:53:36 2026
Resources Information:
  Elapse:               184S
  Remaining Elapse:     0S
```

`Remaining Elapse: 0S` は経過時間制限による終了を示す (自発終了した [T-361] の request では
`Remaining Elapse: 287S` だった)。

### 3 層の観測

| 層 | signal 受信記録 | heartbeat | 備考 |
|---|---|---|---|
| job script (bash) | **なし** | 1 件 | trap は仕掛けたが発火せず |
| Python 親 (`_install_signal_handlers` 同型) | **なし** | 181 件 / 178.9 秒で途絶 | `after_signal` は最後まで未設定 |
| 孫 (`start_new_session=True`) | **なし** | 178 件 / 親の 0.565 秒前に途絶 | pytest 子に相当 |

**`canary.txt` の最終値は `MUTATED`。** Python 親の `finally` は canary を `ORIGINAL` へ復元する
実装だが、**復元は行われなかった**。

### 自己検査 (probe が壊れていないことの確認)

- `parent_started` → `grandchild_spawned` → `canary_mutated_persisted` →
  `grandchild_alive_immediately_before_ready` → `ready_after_login_readback_ack` まで到達。
  **login 側 observer による canary の読み返しと ack まで成立してから測定に入っている**
  (LB-08 の ready 条件)。
- 3 層すべてが起動し heartbeat を書いていた = 「届かなかった」と「起動していなかった」を区別できる。

### 構成の射程 (重要)

本結果は **`--accept-sigterm` を指定せず、`elapstim_req` の警告値も省略した既定構成**についてのもので
ある。これは `tools/pegasus/dispatch_compute.py` の `_job_script` が現に使っている構成と同じである。

**未実測:** `--accept-sigterm=yes` + `elapstim_req="max,warn"` (warn < max) +
`--warning-signal=elapstim:SIGTERM` の **mitigation leg** と、SIGUSR1 による
**split-warning leg** は投入されなかった (理由は §3)。したがって
**「捕捉可能な構成が存在するか」は未解決**である。

### [T-360] への意味

- **既定構成のまま変異 harness を計算ノードの 1 ジョブへ束ねると、walltime 超過時に
  `mutation_harness` の `finally` 復元は原理的に走らない。** 変異が当たったままの tree が残る
  (F32 の再発型)。
- `_stop_process` は pytest 子へ SIGTERM 後 5 秒 + SIGKILL 後 5 秒を待ってから
  `_restore_targets` に到達する (`tools/mutation_harness.py:1098-1113`, `:1132-1174`, `:1251-1332`)。
  **grace が 0 である以上、この 10 秒超の cleanup 列は最初の 1 歩も実行されない。**
- したがって [T-360] は次のいずれかを備えないと着手できない。
  (a) mitigation 構成が実際に捕捉可能な signal と十分な grace を与えることの実測、
  (b) walltime 内に必ず終わる設計、
  (c) 外部から残留変異を検出・復元する経路。
  **本 wave はどれも実装せず、裁定パッケージとして返す。**

---

## 2. [T-361] cross-node flock は `/work`・`/home` とも **排他された** (silent fail-open は観測されず)

**ただし本結果は `PENDING_EXECUTION_HOST_VALIDATION` であり、`dangerous` は `null` のままである。**
安全と読み替えてはならない。

### 観測

request `882038.nqsv` (`#PBS -b 2`、既定 topology `distrib`)。

| 項目 | 実測値 |
|---|---|
| 実行ホスト対 | `bnode001` / `bnode005` (**別ノード**) |
| `PBS_JOBID` | `0:882038.nqsv` / `1:882038.nqsv` (job 番号 prefix つき) |
| cross-node 試行の結果 | `/work` **6/6 `BLOCKED`**、`/home` **6/6 `BLOCKED`** |
| trial 数 | 3 |
| 計算ノード側 mount (`/work`, `/home`) | `lustre`、`flock` あり、**`localflock` なし**、両ノードで signature 一致 |

### 自己検査 (すべて通過)

- `backing_object_proof_valid: true` — holder が lock file へ書いた nonce を contender が
  **開いた fd 経由**で読み、同一 backing object を争っていることを実証
- `controls_valid_on_both_bnodes: true` — 同一ノード内の排他 (陽性対照) と未保持時の取得成功
  (陰性対照) を**両 bnode で**確認
- `effective_mounts_valid_on_both_bnodes: true` — `/proc/self/mountinfo` から最深 mount を解決
- `long_hold_one_fd_from_recon_through_all_trials: true` — filesystem ごとに 1 fd を全 trial 通して保持

### なぜ確定していないか

controller が実行時欠陥で落ちた回の attempt であり、`qstat -J -f` の Execution Host と
marker の一対一照合が完了していない。**probe は照合前に安全を宣言しない設計になっており、
`dangerous` を `false` ではなく `null` に保った。** 後から安全側へ倒していない。

### 射程限界

- **この結果は `bnode001`/`bnode005` の対、当日の kernel と mount に限る。**
  `mount.lustre(8)` は distributed coherence を「`flock` option を使う client 同士」に限定しており、
  異なる option の client が混在しうる。gen_S 全体へ一般化してはならない。
- **数時間保持は再現していない。** long-hold は同一 job 内の全 trial を通す範囲にとどまる。
- **本結果は Lustre `flock` primitive についてのものであり、D131 共通前提 1 (shared / legacy lock の
  移行と二重走行の窓) を閉じない。** 移行期に旧 process が node-local `/tmp`、新 process が
  Lustre lock を取る窓は、flock がどれだけ正しく効いても残る。

---

## 3. 実施できなかったこと (正直な記録)

- **T-362 の split-warning leg と mitigation leg は投入されなかった。**
  controller は t362-default の attempt を `admissible: false` と判定して恒久停止した。
  理由は `racctjob` / `racctreq` が当該 request のレコードを返さなかったこと
  (`matching_request_record_count: 0`) である。会計の反映遅延と考えられるが未確認。
- **設計上の気づき:** admissibility の連言に「cleanup 順序の確認」が入っているため、
  **SIGKILL で cleanup が走らないという危険な結末そのものが `admissible: false` を生む。**
  「probe が正しく危険を捉えた」ことと「安全な attempt だった」ことを同じ連言で表しており、
  危険側の観測は構造的に authoritative になれない。これは本 wave の裁定 (S6-FS-01) の副作用である。
  次 wave はこの 2 つを別 field に分けるべきである。
- したがって `session-summary.json` の `authoritative_attempts` は空であり、
  `all_legs_have_authoritative_attempt: false` である。**本 RESULT は staged raw から
  再構成した観測であり、controller が authoritative と認めた集合ではない。**

## 4. 資源の実測

| 項目 | 値 |
|---|---|
| 投入 request | 3 本 (`882038` = T-361、`882048` = T-362 default、うち 1 本は controller crash 前) |
| requested node-min 累計 | 13 (上限 40) |
| `rbudgetcheck` 減少 | **0.29 point** (313.97 → 313.68) |
| node-minute → point 換算率 | **未確定** (推測しない) |

## 5. 証拠の所在

- `evidence/20260803T154703Z-0de9e25c32cba9eb/` — controller が staging し追跡確認したもの
- `driver/` — probe と controller の実体 (commit 済み)
- job の stdout/stderr は `.stdout.raw` / `.stderr.raw` へ改名して保存した
  (`.gitignore:11` が `*.o` を無視するため。元名は manifest にある)
