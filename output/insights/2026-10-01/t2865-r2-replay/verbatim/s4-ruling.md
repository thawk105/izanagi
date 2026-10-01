# 段 4 裁定 — dev-wave-t2865-r2-replay (親、2026-10-01 03:3x JST)

入力: 段 1 brief `s1-brief.md`、段 3 相談 `s3-consult.md` (read-only codex 1 本、2 レンズ、check_codex_output rc=0)。裁定 inbox 再走査: docs/handoff は README と 2026-08-28 の 1 件のみ (本題と無関係)。local main は 74029b18f → 19f9eb831 に進んだが差は md_23 の docs・insight だけで、pin.py・driver・job 本体・patches・CCBench は不変。

## 所見の裁定

1. refuted (「別 checkout でも衝突」) — 同意。claim は `<checkout>/output/env/pegasus/claims/` 下。insight では ID 単独で結合せず、候補・round・checkout 絶対 path・campaign dir・job を表に並べる。
2. real 低 (「2 本目は必ず ClaimError」の条件) — 採用。記述は「同じ checkout で同じ設定の先行実行が claim を取得済みなら、候補を問わず terminal 判定より前の claim 取得で拒否される」に限定する (insight・runbook とも)。
3. real 中 (stock 呼出しの環境切替) — 採用済み。wrapper `r2-pair-job.sh` は 2 回目を `env -u IZANAGI_S4_POLICY_PROPOSAL_PATH` で呼び、scratch 名は `${PBS_JOBID//:/_}` で job 本体と同じ置換を使う。claim は退避しない。
4. refuted (nonce 再使用) — 同意。残り 1 秒検査は存在確認に過ぎず完走保証でないことは insight に書く。walltime は 2,400 秒を要求する。
5. 要実測 (二重呼出しの完走) — smoke の成立条件にする: 候補・stock 両側の job 本体 rc=0 (compute-result の driver_rc)、両側の WAL の BENCH_DONE、verify_done の anomaly 0、候補の certified と stock の `certified-stock`、両側の trace 保全先に実体があること。
6. real 中 (P3 の見積り) — 採用。smoke の wrapper 全体 Elapse で 6 本を積算し、受入全走の計算を足して 2 node 時間を判定してから残り 5 本を投げる。5 ノード並行は wall を縮めるだけで node 時間は減らさない。
7. real 中 (P4 の失格単位) — 採用。anomaly は候補全体を失格とし (他 round の観測は事実として残すが再現成功には数えない)、候補・stock とも成立した round だけ比を示す。
8. refuted (pair mode 流用) — 同意。流用しない。

## (P) の確定

- P1 採用: (候補, round) ごとに新しい detached submit checkout、起点は全 6 本とも 74029b18f (wave 開始時の local main、開始 gate と同じ)。CCBench 6810666・骨格 patch SHA-256 9cb54552… は系列 C と同じ。driver・job 本体・テストは変えない (段 5・6 なし、4→7→8→9)。変異 matrix は実装面差分ゼロで免除。受入全走は記録 commit 後に行う。
- P2 修正採用: 上記 3 のとおり。順序は候補 → stock 固定 (系列 C の pair と同じ)。逐次対照であり順序効果を除いた差とは呼ばない。
- P3 修正採用: 上記 6。smoke = 候補 2・round 1 (観測として数える)。
- P4 修正採用: 上記 7。比 = 同じ wrapper job 内の候補 5 rep 中央値 ÷ stock 5 rep 中央値。abort 率は bench の leading_indicators。水準・並びは観測された一致/不一致として書き、最高水準への優位や安定した順位の証明へ広げない。
- P5 採用 (条件限定): runbook §3.1 の誤記 1 文だけを上記 2 の限定形に直す。wrapper 手順は runbook に足さない。
