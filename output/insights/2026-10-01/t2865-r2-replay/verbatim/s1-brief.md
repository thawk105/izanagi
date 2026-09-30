# 段 1 brief — dev-wave-t2865-r2-replay (親、2026-10-01 03:2x JST)

- 研究前進: [T-2865] 系列 C の certified 候補 3 本 (iteration 2・3・4、proposal = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-series-c/llm/prop-{2,3,4}.json`、repo 逐語 `output/insights/2026-09-29/t2865-silo-policy-series-c/verbatim/llm/prop-{2,3,4}.json` と sha256 一致) の同じ job の stock 比 2.17・1.86・2.64 は各 1 観測。R2 (runbook §3.1、LLM なし) で候補ごとに 2 回、同じノード・同じ job の stock と並べて比と abort 率を取り、比の水準と候補間の並びが再現するかを判定する。完了 = 6 観測 (または区切った数) の表・正しさ分類・元の値との対照を insight に書く。
- scope: 再測定だけ。repo のコード・テスト・job 本体は変えない (4→7→8→9)。仮想リスク向け gate・検査・台帳・一般化は足さない。stock 比の再現は最高水準に対する優位の証明とは別に書く。
- 確定済みユーザー裁定: 依頼文 (入口 runbook §3.1、`IZANAGI_S4_POLICY_MODE=replay`、`evaluation_purpose=r2`、LLM なし、loop 予算不使用、候補ごと 2 回目標、同ノード同 round に stock、識別子は R2 に閉じた最小の対応、共有 driver 編集が稼働 wave と衝突するなら各候補の初回 R2 で区切る、trace 保全 §3.2 と正しさ gate は実走と同じ、anomaly は即失格、smoke 後に積算し 2 node 時間以上なら land 調整役に諮る、成果は insight と spool fragment、規律 2 不変)。D2270 項 4 (R2 入口) と同却下欄 (「R2 の run id と replay-pair mode は同じ候補を同じ checkout で繰り返す必要が出たときに足す」)。
- 実測した前提 (実コード):
  - replay は候補を 1 評価するだけで stock 対照を持たない (`orchestrator/campaign/p3_s4_loop_policy.py:1067-1071`)。job 本体は 1 job で driver を 1 回呼ぶ (`tools/pegasus/p3_s4_loop_pegasus.sh:798-813`)。
  - R2 の campaign identity は候補を含まない (`default_cfg` :164-191、`ident.canonical_preimage`)。claim は `<checkout>/output/env/pegasus/claims/<identity>.claim` に O_EXCL で一度きり (loop.py:373-409、campaign_claim.py)、terminal skip より前に取る (loop.py:698 → :778)。よって同じ checkout の 2 本目の R2 は候補を問わず ClaimError。bootstrap stock も checkout ごとに 1 回。runbook §3.1 の「同じ候補を同じ checkout で 2 回 R2 すると terminal skip」は実コードと食い違う。
  - job 本体は scratch `/scr/$USER/p3-s4-loop-pegasus/<PBS_JOBID>` の新しさ (:390-395)、evidence root 内の compute-result・allocation-qstat・reservation・prebuild receipt の新しさを検査する。予約検査の要求残時間は 1 秒 (loop.py:216,384)。nonce 再使用の台帳は無い (reservation.py)。
  - 並行: `worktree-dev-wave-t2867-contrast-run` (未着地) が driver `run_stock_control` と `test_p3_s4_loop_policy.py` を編集中。pin-f (未着地) が CCBench pin を 6810666 → 25898d0 に進める予定。local main 74029b18f の pin は 6810666 (= 系列 C)。
- (P1) 親の provisional 裁定・攻撃対象: driver に R2 識別子を足さず、(候補, round) ごとに新しい detached submit checkout (起点 = local main 74029b18f、AI worktree 容器外、job dir 下) を 1 本作り、その checkout の r2 と bootstrap を 1 回ずつ使う。checkout の絶対 path が R2 に閉じた識別子。6 本。
- (P2) 同じノード・同じ job の stock: repo 外の親専用 wrapper job script (PBS header は job 本体と同じ -A SFC -q gen_S -b 1、elapstim 2400 秒) が同じ allocation で job 本体を 2 回 `bash` で呼ぶ: 1 回目 replay (候補)、2 回目 stock (`--stock-baseline`、bootstrap campaign)。呼出しごとに evidence root と trace 保全先を分け、間で 1 回目の scratch dir を別名へ退避する (job 本体の全検査はそのまま走る)。順序は系列 C の pair と同じ 候補 → stock。
- (P3) 計算: 1 job ≈ R2 491〜807 秒 + stock 300 秒 + 前処理 2 回分 ≈ 900〜1,100 秒。6 job ≈ 1.5〜1.8 node 時間 (< 2)。smoke = 候補 2 の round 1 を 1 本、成立を確かめてから残り 5 本を 5 ノードへ並行投入。smoke 実測で積算し直し 2 node 時間以上なら land 調整役に諮る。
- (P4) 成立判定: 候補 = 計測 dir の WAL の BENCH_DONE・verify_done の anomaly 0・stdout の certified、stock = stdout `certified-stock`。anomaly の候補は即失格 (その round の比は取らない)。比 = 候補 5 rep 中央値 ÷ 同 job の stock 5 rep 中央値。abort 率は bench の leading_indicators。
- (P5) runbook §3.1 の誤記 1 文を実コードに合わせて直す (docs-only)。wrapper 手順は runbook へ足さず insight に置く。
- 成果物: insight `output/insights/2026-10-01/t2865-r2-replay/README.md` (+ verbatim)、worklog fragment、runbook 1 文の是正。decisions は新設判断が無ければ書かない。
- 受入: 記録 commit 後に受入全走 (コード差分ゼロ、変異 matrix 免除)。実測環境 = Pegasus gen_S (runbook `docs/pegasus-runbook.md`)。
- 並列分割: 実装子なし。段 3 は read-only codex 1 本 (2 レンズ)。
