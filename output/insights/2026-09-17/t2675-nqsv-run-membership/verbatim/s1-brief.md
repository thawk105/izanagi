# 段 1 brief — [T-2675] NQSV が request を RUN に留める判定方式の分離実験

基準 commit `38353207f` (local main、fresh worktree `worktree-dev-wave-t2675-nqsv-run-membership`)。
一次資料 = `output/insights/2026-09-16/t2622-compute-job-exit-hang/README.md` (D2048、F853 supersede)。

## 研究前進 (土台)
計算ノード job が pytest 完了後に終わらない事象 (F853) は orphan hold で dispatch 全体を止め、campaign の
床値・受入全走を止める。T-2622 は「同じ所属の子孫が存命する間、job の会計終了が遅れる」まで確定したが、
全記録 `sid == pgid` で判定方式 (session / process group / 追跡集合) を分離できず、D2048 が本実験を次 wave へ
渡した。完了判定 = 6 条件の `E − J` (NQSV `Ended Request Time` − trace `job-run-returned`) が事前登録の判定表の
1 行に落ち、T-2676 (終了遅延の対策) の向きが 1 行で書けること。最小差分 = 実装差分ゼロ (probe は commit しない)。

## scope
- 入: T-2622 probe (job dir、Codex author 作、commit なし) を所属変更条件つきに拡張した probe を Codex `role=author` が
  `tools/probe_t2675_run_membership.py` として書き、`--selftest` を login で実走し、計算ノードへ generic dispatch で
  6 条件を**直列・detached** で投入する。生データ・逐語・判定は insight `output/insights/2026-09-17/t2675-nqsv-run-membership/`。
- 出: 回収処理・防壁の実装 (T-2676)、subreaper (F973)、`qdel`、F853 当時の機序の断定、受入全走 (pytest/xdist) 構造への外挿、
  NQSV の内部実装の特定 (追跡集合の「どうやって」)。`_group_member_count` の Z 除外 ([T-2620]、裁定待ち) と T-2677 は触れない。

## 確定済みユーザー裁定
- 実装差分ゼロ (probe は job dir へ保全、repo へ commit しない)。subreaper は採らない (F973)。qdel はしない。
- 規律 2 を緩めない。本題の分離実験だけ。着手直前の local main から fresh worktree (済: 38353207f)。
- D2048: 帰属は「存命する子孫」で止め、判定方式は未確定として明示 → 本 wave がそれを分離する。

## 不変条件
- 子の寿命は monotonic deadline (t0+75 秒) と `alarm` (寿命+45 秒) で有界。無期限 FIFO / pipe 待ち・walltime kill 依存の終了を含めない。
- 同一 worktree からの dispatch は 1 本ずつ (pending-qsub hold)。各条件の終端 (receipt・会計・`orphan-holds/` 0 件) を見てから次へ。
- 異常時は追加投入を止め、終端を待つ (`qdel` 不使用)。判定表は結果を見る前に固定する (規律 3)。
- 実装面の commit 差分 0 → 変異 matrix 免除 (`DW-S04`)、受入全走は免除しない。

## 親の provisional 裁定 (攻撃対象)
- (P1) 6 条件で分離できる: D `no-child` (統制)、K `keep` (陽性対照 = T-2622 C 相当、fd 保持・所属不変・75 秒)、
  S0 `setsid-now` (fork 直後に `os.setsid()`)、S30 `setsid-30` (t0+30 で `setsid`)、G0 `setpgid-now` (fork 直後に `os.setpgid(0,0)`)、
  G30 `setpgid-30` (t0+30 で `setpgid`)。予測: 現 session 基準 → S0≈0 / S30≈25 / G0≈70 / G30≈70、現 pgid 基準 → 0/25/0/25、
  fork 時に記録される追跡集合 (kernel tag 等) → 全 70、周期走査で記録される集合 → S0≈0 / S30≈70 / G0≈70 / G30≈70。
- (P2) 判定域: `E − J` ≤ 5 → 「待たない」、20〜30 → 「所属変更まで待つ」、65〜75 → 「子の終了まで待つ」、他は判別保留 (同条件を 1 回だけ再走)。
- (P3) NQSV が待たない条件では子は job 外の孤児として ≤75 秒生き自滅する。有界なので許容。子の死亡時刻は 5 秒周期の heartbeat 記録で evidence 側から独立に上限づける (NQSV が job 終端で kill したかを区別する)。
- (P4) walltime `00:03:00`、`--queue-wait-timeout 1800`、`--overall-grace 2100` (QUE 9 本の混雑を見て T-2622 の 600/900 から延長。期限順序 queue-wait < walltime+grace は維持)、`--accounting-grace 120`、`--poll-interval 2`。
- (P5) 環境変数で NQSV が追跡する説は T-2622 で既に弱い (generic の clean env に PBS_* が無いのに待った) が、probe は env 名 (値なし) と `/proc/self/cgroup` を start で 1 回記録して確認する。
- (P6) 各条件 1 走で足りる (信号 ≥20 秒 vs 会計丸め ≤1 秒)。全条件が同一ノードに乗る保証は無く、ノード差は主張しない。

## 成果物の形
insight README (結論・判定表・生データ表・言えないこと)、`evidence/probe-<条件>.jsonl`、`verbatim/` (brief・plan・lens・裁定・review)、
probe は job dir に SHA-256/bytes で同定。worklog / decisions (D2048 の追補: 判定方式の確定 or 未確定の範囲) は spool fragment。
failures は新規事故が無ければ触れない。

## 分割方針
段 2 plan 1 本 (read-only)、段 3 レンズ 2 本 (a: 機序帰属と判定表の妥当性 / b: 実験設計と安全・dispatch 期限)、段 5 author 1 本 (probe)、
段 6 レビュー 2 本 (a: データ照合 / b: 因果と記録)。受入・実測 = 計算ノード (gen_S、generic dispatch、この worktree から)、selftest = login。

## 変更面 (実アンカー)
| path | 扱い |
|---|---|
| `tools/probe_t2675_run_membership.py` | 新規・untracked・commit しない (Codex author) |
| `output/insights/2026-09-17/t2675-nqsv-run-membership/**` | 新規 (親、docs-only 相当のデータ・逐語) |
| `docs/spool/*.md` | fragment (worklog 1、decisions 1) |
| `tools/pegasus/dispatch_compute.py` | **触らない** (M12 の構造は `52e8fe7cf` から不変であることを実測) |
