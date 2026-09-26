# T-2797 v2 verifier 並列測定

写し元との差分: workload に `bal` (`ycsb_rratio=50`) を追加し、一時 dir の接頭辞を `t2797-v2-vprobe-` に変更した。

計算ノード上で 1 job につき 1 genome・1 workload を測る使い捨て script。`--out-dir` は空の絶対パス、`--scratch-root` は計算ノードの `/scr` 配下を指定する。

```sh
python3 scratch/t2797-v2-vprobe/probe_verify_parallel.py \
  --genome stock --workload bal --reps 5 --concurrency 5 \
  --repo-root /absolute/path/to/izanagi \
  --third-party-cache /absolute/path/to/cache \
  --scratch-root /scr --out-dir /absolute/path/to/empty-output \
  --verifier-timeout-s 600
```

`--genome B0-L-W0` と `--workload wh` / `rh` も指定可能。`bal` は balanced の較正動作点に合わせて `ycsb_rratio=50` を使う。`B0-L-W0` は `BACK_OFF=0`、`NO_WAIT_LOCKING_IN_VALIDATION=1`、`NO_WAIT_OF_TICTOC=0`、`WAL=0` の cmake flags で重い trace の代理にする。`fixed8` は define だけでは候補を実現しないので削除した。`--concurrency` の既定値は `--reps` (既定 5)。生成される `probe.json` は段階ごとに更新される。`build` は trace 有効 build、`traces` は各 trace の wall と commits、`serial` / `parallel` は各検査の wall・verdict・certified・txns・edges・total_cycles・maxrss、全体の `wall_s`、2 秒間隔の node memory 標本と最大使用量を含む。`serial_load_decay` / `parallel_load_decay` は終了直後から 90 秒までの 1 秒間隔の 1 分 load average と、4.0 に達した最初の秒数、20 秒時点の値を含む。`consistent` は両検査の 5 field の全件一致、`consistency_details` は本ごとの比較結果。`rc` は測定完了 0、実行中の timeout / 例外 1、preflight 失敗 2 で、verdict を解釈しない。

両検査には同一 trace を使う。trace と build は scratch に置かれ、終了時に消える。load average と node memory は node 全体の値なので他プロセスの影響を含む。1 分 load average は遅れて下がる指標であり、この probe は `settle` を呼ばず、その閾値の適否を判定しない。`probe.json` は逐次保存するが、process 強制終了時は最後の保存以降の結果を失う可能性がある。

`--order production` は build 後、trace を `--reps` 本続けて取得し、直ちに `--concurrency` 本の同時検査を実行する。検査終了を 0 秒として 240 秒まで load を採る。`production` 節の `job_start` は開始時刻・1 分 load・`os.cpu_count()`、`build_interval` / `trace_interval` / `verification_interval` は同じ monotonic clock と UTC による開始・終了、`load_samples` は trace 開始前から検査と減衰の終了までの 1 秒間隔の `/proc/loadavg` 標本、`load_errors` は採取エラー、`load_interval_s` は標本間隔を示す。`production` 自身の `runs` / `concurrency` / `wall_s` / `node_memory` などは従来の `parallel` と同じ検査結果で、各 `runs` の verdict・certified と判定方法は変わらない。`load_decay` は `started_at` / `finished_at`、`duration_s`、`interval_s`、`samples`、`first_at_or_below_4_s` (240 秒以内に達しなければ null)、`load1_at_60_s` / `load1_at_90_s` / `load1_at_120_s` / `load1_at_180_s` を含む。各標本には時刻・monotonic 時刻・1 分 load が入り、減衰標本には検査終了からの実経過秒数も入る。production ではトップレベルの `serial` / `parallel` / それぞれの decay と `consistent` / `consistency_details` は作らない。`--order` を省略した場合は従来の順序と出力を維持する。
