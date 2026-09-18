# 段 4 裁定 — [T-2489] A-2 nodes=5 実走 probe

裁定 inbox の再走査: D1910 以後の decisions に A-2 nodes / bench.lock の新裁定は無い (grep 済み)。
段 3 相談 (`s3-consult.md`、gpt-6-astra / medium、lane luna) の所見 11 件を裁定する。

| # | 所見 | 判定 | 採否 | 反映 |
|---|---|---|---|---|
| 1 | 投入 command に `--ccbench-root` / `--dependency-prefix-source` / `--third-party-source-root` が必須 | real | 採用 | `run-submit.sh` に絶対 path 入りで確定 (A-6 の `run-submit.sh` と同形) |
| 2 | 2 request は逐次投入で片側だけ受理される経路がある。同 attempt の無条件再投入は不可 (create-only) | real | 採用 | 片側失敗時は `jobs/<w>/scheduler/request-id` と qsub 診断を記録し、原因を見てから**新 attempt-id** で投げ直す。同時開始は保証されない事実も記録 |
| 3 | 識別子の筋は通る。enforcement closure に policy JSON は入らない。submit-tree は完走まで固定 | real (nit) | 採用 | submit-tree を `git worktree lock` し、完走まで checkout / commit / 撤去しない |
| 4 | cluster 越し直列化は「強く整合する推測」であり立証ではない (WAL に acquire/release 無し) | real | 採用 | insight では「強く整合する推測」と書く。補強: login node の `/home` は lustre `rw,flock` mount (`/proc/mounts` 実測)。計算ノード側の mount option は未確認と明記 |
| 5 | fan-out でも head は兄弟待ちの全期間 lock を保持し、2 head の pass が直列化する。兄弟の lock は task 単位 | real | 採用 | 所要モデルを「pass 単位の直列化」に直す |
| 6 | durable cache / receipts の直接衝突無し。host alias は文字列比較のまま | real (nit) | 採用 | 限界として記録 |
| 7 | A-2 trace の bytes / verifier memory と `/scr`・head tmp の空きは未確認 | real | 採用 | 「未確認の実機リスク」と明記。head 側は nodes=1 の 3 attempt と同じ既定 tmp で完走済み (事実)、兄弟側は本走で初めて分かる |
| 8 | 不変条件 2 の分類が粗い。ssh に総 timeout 無し。費用上限は walltime 6h × 10 node = 60 node-hours | real | 採用 | 不変条件 2 を「遠隔結果の欠落・MAC 不一致は `verify-remote-unavailable`、正当な worker 失敗は各 reason を保持、pass に読み替えない」に改める。hang 対策: qstat sampler で監視し、WAL が 90 分無進行なら親が自分の request を qdel し indeterminate として記録 |
| 9 | 出力同値性は「科学的条件の同値性」と「成果物の同一性」を分ける。24 検査・16 遠隔 result。MAC は head 実行時の受理証拠 | real | 採用 | 解析計画 §同値性に採用 (下記) |
| 10 | WAL だけでは並列化分と lock 待ち分を厳密分離できない。rr50 「bench 34 s」は rr5 bench 17 s を含む。24 分見積りは誤り (12〜15 分) | real | 採用 | 静的見積りを訂正: nodes=5 + 共有 lock ≈ 2 cell × (build/legacy 75 + rr5 pass ≈140 + rr50 pass ≈190 + bench 17+17) ≈ 880 s ≈ 15 分 (同時開始・rep 時間維持・overhead 小の仮定)。並列化分と lock 待ち分は「pass 長の短縮」と「他方の待ちの短縮」として因果的に連動し、独立の speedup として足さない |
| 11 | queue 費用は Σ nodes_i × Elapse_i。request ごとの submit/start/end・待ち・node 一覧・終了状態・CPU time を残す。elapsed 短縮と node 秒削減は別 | real | 採用 | 解析計画 §費用に採用 |

**総括: 条件付き go を満たしたので投入する。** 本 wave で判定できるのは nodes=5 の 1 attempt の実測だけ。
node-local lock の効果は静的見積りに留め、恒久採用は裁定しない (D1910 項 2 の実測手番のみ)。

## plan v2 (投入と解析)

1. `run-submit.sh`: `submit_paper_story_a2_certification.sh --policy orchestrator/campaign/paper_story_a2_certification.v2.json --attempt-id t2489-20260918a --ccbench-root <tree>/external/ccbench --dependency-prefix-source /work/1/SFC/tanab/izanagi-a2-deps --third-party-source-root <tree>/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src` (tree = submit-tree、HEAD 3f61c3408)。
2. `qstat -f` sampler (30 秒間隔、両 request) を detach。待ち手は request 消滅 (両方) を 1 条件にする。
3. 完走後 `finish-group` で completion receipt を書く (collect はしない)。
4. 解析 (親、script は job dir): (a) WAL 時刻差 (両 workload・両 cell)、(b) NQSV 会計 (Created/Started/Ended/Elapse、node 一覧)、(c) fan-out `task.json`/`result.json` 16 件の rep・verdict・MAC 受理、(d) 検査 24 件の verdict/certified/anomalies、(e) 費用 Σ nodes×Elapse、queue 待ち、attempt span、(f) 現行 t2364-20260907b との比較表、(g) lock 直列化の時刻整合の再検査 (5 ノード走でも rr5/rr50 の pass が交互になるか)。
5. insight `output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md` + worklog fragment。裁定パッケージ: (i) A-2 nodes=5 の採否、(ii) job body で `IZANAGI_BENCH_LOCK` を node-local にするか (静的見積りのみ)、(iii) 遠隔実行の総 timeout。

## 同値性の判定 (所見 9 反映)

- 科学的条件: workload flags (`run_cmd` の argv)・reps・records・threads・extime・genome・src_token・
  protocol_sha256・CCBench pin・toolchain が現行 attempt と一致。
- 成果物の同一性ではなく対応: 4 cell × (legacy 1 + performance 5) = 24 検査すべて
  `serializable` / `certified` / anomaly 0、遠隔 16 件の `result.json` が head の MAC 照合を通って
  WAL に取り込まれた (head 実行時の受理証拠)。commits / aborts / tps は観測量として並記し一致条件にしない。
- 一致対象にしないもの: policy bytes sha256、source_commit、task sha256、MAC、campaign identity。
