# 段 1 brief — [T-2265] cohort 2 の図のための観測長 6 秒 perf 測定

wave slug: `t2265-cohort2-perf6`

## 研究前進

T-2265 cohort 2 の反実仮想 ITT は主判定が確定している (`recommended_direction_superior`、
効果 +4.900%、95% CI [+3.316%, +6.509%]、worklog entry 1393)。**止まっているのは図だけ**である。

`tools/plotting/plot_dynamic_backoff.py` は cohort 2 の図に対し performance 成果物 6〜7 本を
要求し、その `extime_s` が 6 でなければ受理しない
(`plot_dynamic_backoff.py:683` の `"expected_extime_s": 6 if terminal_contract else 3`、
`terminal_contract = schema == COHORT2_DIAGNOSTIC_SCHEMA`)。
現存する performance 7 本 (`978014`〜`978020`) は `extime_s = 3`・schema v2 なので条件を満たさない。

**完了判定:** `plot_dynamic_backoff.py` が cohort 2 診断 1 本 + 新規 performance 6〜7 本を受理し、
3 図 (thread-axis / contrasts / diagnostic) の png+pdf と `provenance.json` を生成すること。

## scope

1. `extime 6`・schema v3・7 腕 x 3 workload x 8 スレッド = 168 点の performance 成果物を
   **7 本** 測る (7 job = 7 block、Pegasus へ同時投入)。
2. cohort 2 診断 1 本と合わせて図 3 枚 + provenance を login node で生成する。
3. insight + worklog を書く。

**scope 外:** `plot_dynamic_backoff.py` / `t2187_adaptive_const_probe.{py,pbs}` / それらの test の
改修、policy 腕どうしの性能比較 (別 wave T-2417 の領分)、直列性認証、
仮想リスク向けの gate・検査・台帳・一般化の追加。

## 確定済みユーザー裁定 (覆さない)

- 性能測定は trace-disabled build (`BACKOFF_TRACE=0`) で行う。
- 条件を割って複数ノードへ同時投入する。
- 図は `tools/plotting/FIGURE_CONVENTIONS.md` に従い、計測機の外 (login node) で描く。
- 絶対規律 2 を緩めない。本題の測定と作図だけを行う。

## 起動時検査で確定した事実 (親が実物で確認済み)

- **重複 wave あり。** `dev-wave-t2417-policy-arm-perf` の worktree が
  `tools/pegasus/probes/t2187_adaptive_const_probe.py` と `.pbs` を **未解決 merge 競合 (UU)** の
  まま保持し、`tools/plotting/plot_dynamic_backoff.py` と同 test も変更済みで保持している。
  **本 wave はこの 4 file を編集しない。**
- T-2417 が既に測った performance 18 本 (`.../perf/t2417-policy/t2417a02/policy-perf-rep*.json`) は
  cohort 1 の policy 腕 (`cw-as-dyn-p0/p1/p2`)、`extime_s = 3`、`repo_head deb1f0643`。別物である。
- `t2187_adaptive_const_probe.py` と `.pbs` の bytes は commit `8bdf173cc` と現行 main で同一
  (それぞれ sha256 先頭 `8d5c0cb06ea2b183` / `cc0ee88c6951fa2c`)。
- 既存の extime 3 の図一式は
  `output/insights/2026-09-05_dynamic-backoff-mechanism/figures/dynbackoff-*.{png,pdf}` と
  同 `dynbackoff.provenance.json` にある。生成 argv はその provenance の `reproduction.argv`。

## 不変条件 (plot_dynamic_backoff.py が exact に検査する。実物で確認済み)

1. **全入力 (performance 6〜7 本 + 診断 1 本) の identity が完全一致すること**
   (`load_inputs` の `identities` 比較)。一致が要る field と、cohort 2 診断
   `.../trace/t2265-cohort2/stage1-rep0-0_985851.nqsv.json` が持つ実値:
   - `repo_head = 8bdf173cc81e5371db7b7bcddb8bdcbb5aeff235`
   - `prereg_sha256 = cc8975112b6d5ec9ce1ea683928077805e53721adc5acd31b9a13c6c93b3ee68`
   - `ccbench_commit = 511c953` / `ccbench_head = 511c9538e4e8efa54b45cda62e72389ed3b706ec`
   - `driver_sha256 = 8d5c0cb06ea2b183e31cb7254b4d3059b209b25f0e66c9ed6ce52fbf8629fa64`
   - `pbs_sha256 = cc0ee88c6951fa2c837c47c27af8cd56d3734a42c3286e206356f97228658e85`
   - `repo_status_clean = true`
   - `patch_sha256 = 9b2153e0547e167888ba2616750951365c4a075a80f9a95be6000e60b6f8f54b`
   - `dynamic_patch_sha256 = f3fe6b7e67931775bcef0a7831dda8c6cb53dfc7fc52a74f4508360e1fedf824`
   - `counterfactual_patch_sha256 = 4c04caa89244d74aa542a204bed0befae45b13616113cc5d734570c3aae7d2ff`
   - `patch_stack_sha256 = 14ac8f00798d1b317854643e133c0b58543106e9c693f5c556f8b13edb591082`
     (patch stack は A+B+C)
   - `records = 1000000`、`extime_s = 6`、`clocks_per_us = 2100`
   → したがって **投入は `8bdf173cc` の detached checkout からしか成立しない**
     (`repo_head` は `.pbs` が `git -C "$PBS_O_WORKDIR" rev-parse HEAD` で採る)。
2. `cell_order` は rep index による巡回順 `CELLS[i:] + CELLS[:i]`。
   `CELLS = (none, stock, tuned, tuned-u10240, cw, cw-as, cw-as-dyn)`。
3. `rep_index` は 0..6 で重複なし。`pbs_jobid` は本数分すべて相異なること。
4. `cells` は `CELLS x WORKLOADS x THREADS` の部分集合。
   `WORKLOADS = (write-heavy, balanced, read-heavy)`、`THREADS = (6,12,18,24,30,36,42,48)`。
5. 絶対規律 1: trace-disabled build で測る。診断 symbol・文字列が 0 個であることは probe 自身が
   検査して JSON に記録する。
6. 絶対規律 2: 性能値は未認証である。variant 採用の根拠にしない。図と insight に明記する。
7. 絶対規律 7: 既存の extime 3 の 7 本と、それに基づく凍結済みの判定は変えない・無効にしない。
   本 wave は置き換えでも再測定でもなく、別の観測長の companion 集合である。

## (P1) 親の provisional 裁定 — 攻撃対象

extime 6 の 7 腕 performance 格子は、既存のどの事前登録にも覆われていない。

- `docs/dynamic-backoff-preregistration.md` §3「測定条件」は `extime | 3 秒、1 job あたり 1 rep`、
  driver は `結果 schema v2` で凍結している。
- `docs/backoff-counterfactual-cohort2-preregistration.md` §10「本書が覆わない次の一手」は
  「**policy 腕の trace 無効な性能測定。**…本書は覆わない」と明記している。

**provisional 裁定:** 値を 1 つも見る前に、この companion 測定の条件・本数・順序・
主張してよい範囲を書いた短い登録文書を**新規 file** として main へ commit し、その後に投入する。
既存 2 文書の bytes は 1 byte も変えない (変えると `prereg_sha256` が動き、上記 identity 検査が
落ちて図が生成できなくなる)。図の H1–H7 は「凍結された extime 3 の判定を置き換えない記述」と
明記する。

## (P2) 親の provisional 裁定 — 攻撃対象

図に使う cohort 2 診断成果物は 12 本ある
(`.../trace/t2265-cohort2/stage1-rep0-0_9858{51..62}.nqsv.json`)。plot は 1 本しか取らない。
**図を 1 枚も見る前に、job ID 昇順の先頭 `985851` を選ぶ**と決める。

## 成果物の形

- companion 登録 doc 1 本 (docs-only、投入前に commit) — (P1) が通れば
- performance JSON 7 本 — `/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf/` (repo 外)
- 図 3 枚 x (png, pdf) + `*.provenance.json` —
  `output/insights/2026-09-09_t2265-cohort2-figures/`
- insight README 1 本、worklog 1 件

## 実装面と並列分割

- 実装面は **qsub launcher `.sh` 1 本だけ**。段 5 の Codex `role=author` が書く。親は直接編集しない。
  repo 内に書かせ、親が実行前に job dir へ退避して実行する。
- `plot_dynamic_backoff.py` / probe / test は編集しない。
- 段 5 は 1 unit。測定待ちの間に親が docs を進める。

## 測定の見積もり (実測値から)

extime 3 での実測 wall は 714〜731 秒/job (168 点、build 7 本込み、`wall_seconds` field)。
extime 6 では 168 点 x +3 秒 = +504 秒 → **約 1220 秒 ≒ 20 分/job**。
`.pbs` 既定の `elapstim_req` は `00:40:00` で約 2 倍の余裕がある。
build cache の取り合いは起きない (driver が `$TMPDIR` へ node ローカルの木を建てる。
`output/insights/2026-09-08_t2265-cohort2/README.md` §4 の実測)。

## 投入元 tree

`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-perf6/submit-tree`
(`8bdf173cc` の detached worktree。親が作成中)。
既存の `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/submit-tree` も同じ SHA で
tracked-clean だが、別 session (T-2265 認証 wave、312 job) が使っている可能性があるため使わない。
