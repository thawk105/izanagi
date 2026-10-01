単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01

必読事項の射影:
- /work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01/s1-brief.md (親の段 1 brief。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig2c-author/output/insights/2026-10-01/t2853-r2-fig2c/README.md の §0 (R2 attempt の地位。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig2c-author/tools/plotting/plot_b10_extended_backoff.py (fig2c の生成器。全文。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig2c-author/tools/plotting/plot_backoff.py (生成器の依存。必要な関数だけ。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig2c-author/docs/paper-story/figures/fig2c_b10_extended_backoff.provenance.json (原図の provenance。読めなければ即停止)
- /work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928/tools/t2853_r2_fig8b_plot.py (前例: 別の図 fig8b で同じ目的に作った repo 外 wrapper。設計の手本。読めなければ即停止)

## 目的

fig2c (B-10 拡張格子の記述図) の R2 attempt (原 attempt と同じ driver・同じ source commit で測り直した別の 1 group × 3 job) を、
原図と同じ生成器 `tools/plotting/plot_b10_extended_backoff.py` (bytes を変えない) で描き、原 attempt と並べた表を作る、
**repo 外で使う使い捨て wrapper** を 1 本書く。repo には入れない (親が実行後に repo 外へ移す)。

## 所有と権限

- 書いてよいのは `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig2c-author/scratch/` の下だけ。wrapper 本体は `scratch/t2853_r2_fig2c_plot.py`、試走の出力は `scratch/out/` の下。
- tracked file (生成器・依存・docs・tests を含む) は 1 byte も変えない。commit しない。docs を編集しない。
- 測定データの root (下記) は読むだけ。書かない。`docs/paper-story/figures/` に書かない (生成器の `REAL_OUTPUT_PATHS` へ出力させない)。
- 委任 (spawn_agent 等) をしない。

## 入力の所在 (読むだけ)

- 原 attempt: measurement root `/work/1/SFC/tanab/b10-backoff-grid-runs5`、group `b10-backoff-grid-20260826T234647Z-783837` (生成器の定数そのもの)。
- R2 attempt: measurement root `/work/1/SFC/tanab/b10-backoff-grid-t2853-r2-fig2c-20261001`、group `b10-backoff-grid-20261001T012637Z-3721300`、
  job 40679 (write-heavy) / 40680 (balanced) / 40681 (read-heavy)。**いま計算ノードで走行中で、あなたの作業中にはまだ完成していない。**
  R2 の実データでの実走は親が行う。あなたは原 attempt のデータを R2 に見立てて全経路を実走して確かめる (下の「確かめること」)。
  R2 の job dir の形は原 attempt と同じ (`<root>/<group>.submit.jsonl`、`<root>/<group>-<workload>/{completion.json,reservation.json,campaigns/<campaign_id>/...}`)。
  R2 の job 番号・host・campaign id・入力 sha256 は**実行時に receipt・reservation・completion・campaign lock から読み取り**、wrapper に焼き込まない。
  campaign id は条件の hash なので原 attempt と同じ値になりうるが、決め打ちせず読む。

## 作るもの (サブコマンド)

1. `control` — 原 attempt を、wrapper の経路 (生成器を import し、差し替えなしで `load_measurements` → `make_figure` → 出力 → `build_provenance` → `validate_provenance_semantics` / `validate_external_sources` / `validate_repo_closure` 相当の生成器の既存検査) で描き、
   出来た provenance の `artist_series` と `data` が、原図の provenance (`docs/paper-story/figures/fig2c_b10_extended_backoff.provenance.json`) と完全一致するかを比べる。
   一致しなければ差分 (系列・点・値) を出力して非 0 で終わる。依存 `plot_backoff.py` は原図の時点 (`bdb3c223…`) から現行 (`aa168498…`) へ変わっているので、この陽性対照がその影響の有無を判定する。
2. `r2` — R2 group を描く。生成器の**原 attempt 固有の定数だけ**を、実行時に R2 の receipt 等から読んだ値で差し替える:
   `GROUP_ID`・`SUBMIT_PATH`・`SUBMISSION_NONCE`・`WORKLOAD_SPECS` の job_id / host (campaign_id / identity_sha256 は R2 の lock から読んで一致を確かめる)・`CANONICAL_SHA256` (R2 の各 file から計算)・
   `REAL_OUTPUT_PATHS` (出力先は `--out-prefix`)、caption と図中文言の**役割語だけ** (原 attempt を名指す語を「R2 attempt (re-measurement of the original fig2c group, separate from and not pooled with it)」の趣旨へ。置換対象が想定回数だけ現れることを assert し、外れたら止める)。
   `REPOSITORY_COMMIT` (`78c7a2c1…`)・`CCBENCH_COMMIT` (`511c9538…`)・`JOB_SCRIPT_SHA256` (`9579690d…`) は R2 も同じはずなので**差し替えず**、R2 の記録と食い違えば生成器の検査で止まるのに任せる。
   **差し替えないもの:** 測定値の受理条件 (DAT と WAL の照合、F718 の 1000 µs 除外、条件の固定値、CV 等の既存検査)、レイアウト検査 (`_validate_text_bboxes` を含む)、provenance の意味検査。どれかが R2 の値で拒否したら、
   検査を外さず、拒否理由をそのまま出して非 0 で終わる (図は出さない)。
3. `table` — 原 attempt と R2 を、生成器の `load_measurements` (全検査つき。R2 側は `r2` と同じ差し替え) で読み、markdown の対照表を書く:
   workload ごとに backoff µs (29 点、1000 は「F718 除外」と明記) × {原 attempt, R2} の throughput 平均 ± t 分布 95% CI 半幅 (M tps) と abort rate 平均。
   加えて group ごとの正しさの集計を WAL の `verify_done` 行から数える (variant 数、`certified: true` の数、`anomalies` の合計、`verdict` の値の内訳) — 生成器が読まない参照 2 variant (backoff なし・既定 adaptive) も含めて 31 variant 全部。
   値は group ごとに別々に計算し、合成しない (プール・差の検定・再現精度の評価をしない)。
- 共通: `--generator <path>` を必須にし、その sha256 が `04db851a4a6bb502852fecdd53d9b64f56c0b7b7c3fb94e0526de651cc14216a` でなければ描かずに rc=2。
  provenance には再現コマンド (実際の wrapper 呼び出し argv) と wrapper 自身の sha256 を残す。図の出力は PNG と PDF と provenance JSON。
- 前例 wrapper の構造 (生成器 module を読み込んで定数を差し替える方式、置換回数の assert、sha256 照合) を手本にしてよいが、fig2c の生成器の実際の関数・定数に合わせること。

## 確かめること (実走して報告)

- `control`: rc と `artist_series` / `data` の一致・不一致。
- `r2` を原 attempt の root・group に向けて実走 (R2 の見立て): rc、出力 3 file、caption と図中文言が R2 の役割語になること、`artist_series` が control と完全一致すること。
- `table` を「原 attempt vs 原 attempt を R2 に見立てたもの」で実走: rc、表の一部、正しさの集計 (3 workload × 31 variant)。
- 負例: sha256 の違う生成器を渡すと rc=2・図なし。存在しない root/group を渡すと非 0・図なし。DAT を 1 行だけ変えた写し (scratch/ の下に原 root の該当 job dir の写しを作ってよい。原 root は変えない) で `r2` が受理検査で止まり図が出ないこと。
- 生成器・依存の sha256 が実走の前後で変わっていないこと、`git status --porcelain` が scratch/ 以外に差分を持たないこと。
- 実行に使う python は `python3.10` (前例と同じ)。matplotlib 等が無ければその事実を報告して止まる。

## 報告

報告の最後に `## 総括` 節を置き、作ったもの (path と sha256)、各サブコマンドの CLI、実走の argv と rc と結果、負例の結果、
差し替えた定数・差し替えなかった検査の一覧、未実走のもの (あれば「未実走」と明記)、気づいた懸念を書く。
テストを甘くして緑にしない。受理条件を変える必要があると判断したら、変えずに理由を書いて止まる。
予算が切迫したら途中結論を上の形式で書き終えること。
