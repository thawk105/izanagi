# 2026-08-04 [T-361] / [T-362] cluster probe — 証拠の地図

D130 決定 (3) の条件 2 ([T-361] cross-node flock) と条件 3 ([T-362] walltime signal) を
Pegasus 実機で測った wave の一次資料。**結論は `RESULT.md`。** 本書はどの証拠がどの主張を支えるかの
対応表である。

## 主張と証拠の対応

| 主張 | 支える証拠 |
|---|---|
| NQSV は walltime 超過で **SIGKILL を直送**する | `evidence/.../attempts/t362-default/.../scheduler/*.stderr.raw` の 1 行目 (`%NQSV(INFO): Batch job received signal SIGKILL.`) |
| その終了が経過時間制限によるものである | 同 `.stderr.raw` の NQSV 会計 block (`Elapse: 184S` / `Remaining Elapse: 0S`) |
| 3 層いずれにも signal が届かなかった | `events-job-script.jsonl` / `events-parent.jsonl` / `events-grandchild.jsonl` に signal 受信記録がゼロ |
| 3 層とも起動していた (届かなかったのであって未起動ではない) | 同 events の `parent_started` / `grandchild_spawned` / `grandchild_alive_immediately_before_ready` と `heartbeats-*.jsonl` (親 181 件 / 孫 178 件) |
| `finally` が走らなかった | `canary.txt` の最終値が `MUTATED` (`finally` は `ORIGINAL` へ戻す実装) |
| 測定開始が login 側の確認を経ている | `canary_readback_ack.json` と `ready.json` (observer 読み返し → ack → ready) |
| cross-node flock が排他した | `probe-runs/t361-flock/.../flock-result.json` の `raw_attempt_outcomes` (`/work`・`/home` とも 6/6 `BLOCKED`) |
| 2 ノードが別ホストだった | 同 `exact_host_pair` = `bnode001` / `bnode005`、`pbs_jobids_raw` = `0:882038.nqsv` / `1:882038.nqsv` |
| 計算ノード側 mount が `flock` で `localflock` でない | 同 `filesystem_results.*.mount_entries_from_both_jobs` の `/proc/self/mountinfo` 生値 |
| 安全と宣言していない | 同 `result_state` = `PENDING_EXECUTION_HOST_VALIDATION`、`dangerous` = `null` |
| 費用 | `evidence/.../controller/session-summary.json` の `wave_budget_delta` (0.29 point) |

## 構成

```text
driver/      probe と login 側 controller の実体 (commit 済み)
evidence/    controller が staging し git 追跡を確認した証拠
RESULT.md    実測結果と判定 (正本)
README.md    本書
```

`driver/README.md` が controller の使い方と判定表、残存物の扱いを持つ。

## 再現

```bash
PYTHONDONTWRITEBYTECODE=1 python3 driver/run_probes.py run
```

controller だけが `qsub` を行う。PBS script を直接投入してはならない。
中断した session が残っている場合は先に `driver/run_probes.py resolve` を通す。

## 読むときの注意

- **job の stdout / stderr は `.stdout.raw` / `.stderr.raw` へ改名して保存している。**
  `.gitignore` が `*.o` を無視するため、元の名前のままでは commit されず失われる。元名は manifest にある。
- `RESULT.md` §3 に**実施できなかったこと**を書いた。T-362 の mitigation leg と split-warning leg は
  未投入であり、「捕捉可能な構成が存在するか」は未解決である。
- 本 wave の判定基準は**実測前に固定**した。無効な試行の `dangerous` は `false` ではなく `null` で
  あり、安全の不在を安全と読み替えていない。
