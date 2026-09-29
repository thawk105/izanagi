単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6

必読事項の射影:
- /work/1/SFC/tanab/tmp/t2853-r2-fig6-20260929/s1-brief.md (段 1 brief。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/output/insights/2026-09-29/t2853-r2-fig6/README.md の §0 (R2 attempt の地位。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/output/insights/2026-09-29/t2853-r2-fig6/verbatim/s4-ruling.md (段 4 裁定。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig6-author/tools/plotting/plot_a2_certification.py (生成器。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig6-author/docs/paper-story/figures/fig6_a2_certification_observed_positive.provenance.json (既存 fig6 の provenance。読めなければ即停止)

あなたは izanagi の dev-wave 段 5 の実装子 (Codex `role=author`) である。作業木は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig6-author` (以下 WT)。

## 目的

原 fig6 と同じ生成器 `WT/tools/plotting/plot_a2_certification.py` を **1 byte も変えずに**呼び出し、A-2 の R2 attempt (現行 policy・5 node で測り直した別 attempt) の図と、原 attempt と R2 の対照表を作る**使い捨ての wrapper** を 1 本書く。repo には入れない。

## 書いてよい場所 (これ以外は編集しない)

- `WT/scratch/t2853_r2_fig6_plot.py` (wrapper 本体) と `WT/scratch/out/` (出力)。`scratch/` は untracked のまま置く。commit しない。docs を編集しない。tracked file を 1 つも変えない (終了時に `git -C WT status --porcelain --untracked-files=no` が空であること)。

## wrapper の仕様

- 実行: `python3.10 WT/scratch/t2853_r2_fig6_plot.py --generator <生成器の絶対 path> <subcommand> ...`。wrapper は `--generator` の file を importlib で読み込み (module 名は任意)、その関数だけを呼ぶ。生成器の sha256 を実行時に計算して標準出力と provenance 外の記録 (後述) に出し、`--expected-generator-sha256` が与えられたら不一致で rc=2・出力なしで止まる。
- 生成器の入力束縛は、生成器が既に持つ差し替え口 `main(argv, expected_hashes=...)` / `load_measurements(..., expected_hashes=...)` だけで行う。`expected_hashes` は `{"certification": <sha256>, "raw_manifest": <sha256>}` で、**値は wrapper が入力 file から実行時に計算した sha256** にする (定数を焼き込まない)。生成器の検査関数・定数 (CANONICAL_SHA256・受理条件・layout 検査・caption 組み立て) を差し替えない・monkeypatch しない。
- subcommand `draw`: `--measurement-root <attempt root 絶対 path> --certification <path> --raw-manifest <path> --out-prefix <path>`。out-prefix の basename は `fig6_` で始まること (生成器の規約)。生成器の `main` に `--measurement-root`・`--certification`・`--raw-manifest`・out-prefix を渡し、`expected_hashes` を与えて描く。rc は生成器の rc をそのまま返す。描けたら、出力 provenance に対して生成器の `validate_external_sources(provenance, measurement_root)` と `validate_repo_closure(provenance, <生成器の repo root>)` を呼び、失敗は rc=2。caption は生成器の既定のまま (変えない)。
- subcommand `table`: 2 つの attempt (`--original-*` と `--r2-*` にそれぞれ measurement-root・certification・raw-manifest) を生成器の `load_measurements` (全検査つき、expected_hashes は同様に実行時計算) で読み、markdown の対照表を `--out <path>.md` に書く。どちらかの読み込みが検査で拒否されたら、表は書かず拒否理由を stderr に出して rc=3。表の中身:
  - attempt 表: attempt ID・outer status・current_pin・izanagi source commit・protocol_sha256 の先頭 12 桁・workload ごとの request ID / host / 記録時刻・toolchain の要約・正しさ (certified cell 数 / 全 cell 数、legacy 反復・performance 反復)。
  - cell 表: workload・cell ID・role・genome・median tps・mean tps・t 分布 95% CI 半幅 (df 4、生成器の `_T975[4]` と同じ定数でよい)・CV・abort rate を、原 attempt と R2 で横に並べる (値は `load_measurements` の返り値から取る。wrapper で再計算しない。CI 半幅だけは返り値に無ければ返り値の標本から計算し、その旨を表の注に書く)。
  - 効果表: workload ごとの median 比の効果 (certification の `effects` と `effect_crosschecks.computed`) を 2 attempt 並べる。
  - 表の注に「2 attempt の値は別々に読んだもので合成していない。数値の近さを再現精度として評価しない」を 1 文で入れる。
- subcommand `control` (陽性対照): 原 attempt `t2364-20260907b` を `draw` と同じ経路 (expected_hashes を実行時計算) で描き、その provenance の `artist_series` が既存 fig6 provenance (`WT/docs/paper-story/figures/fig6_a2_certification_observed_positive.provenance.json`) の `artist_series` と完全一致するかを比べ、一致なら rc=0 と `control: artist_series match`、不一致なら rc=1。これは wrapper が値を変えないことの確認である。

## 実走して確かめること (実走した command と rc を報告に書く)

入力 (読み取りのみ、書き換え禁止):
- 原 attempt: measurement root `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907b`、certification `WT/output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json`、raw manifest 同 dir の `raw-manifest.json`。
- R2 attempt の結果はまだ無い (計測中)。**R2 の代わりに原 attempt を `--r2-*` に渡して** `table` が 2 列とも受理して書けることを確かめる。

1. `control` → rc=0・`control: artist_series match`。
2. `draw` を原 attempt で out-prefix `WT/scratch/out/fig6_control_draw` として実走 → rc=0、PNG・PDF・provenance が出て、両 validate が通る。
3. `table` (原 attempt を両側に) → rc=0。
4. 負例: (a) 存在しない measurement root で `draw` → rc≠0・図なし。(b) `--expected-generator-sha256` に誤った値 → rc=2・図なし。(c) certification を 1 byte 変えた一時 copy (`WT/scratch/tmp/` に作る) を渡した `draw` は、wrapper が計算した sha256 で束縛するので hash 検査では通ってしまう — その場合でも生成器の他の検査 (manifest との identity 照合など) で拒否されるかを実測して報告する (拒否されなくても wrapper を曲げない。事実だけ書く)。

## 守ること

- 生成器・既存 test・docs を変更しない。検査を緩めて描かない。生成器が拒否した入力を描けるように wrapper を曲げない。
- 期待値へ揮発値を焼き込まない。緑には実走した command・rc を併記する。実走できなかったものは「実装済み・未実走」と書く。
- 所有外 caller・共有 fixture・consumer test への波及は無い見込みだが、あれば静的に列挙する。
- 現行の受理・拒否挙動 (生成器の拒否条件) を変えない。
- 出力は NFC。python は `python3.10`。network は使わない。
- 予算が尽きそうなら、途中結論を下の形式どおり書いて終われ。

## 報告の形式

最終メッセージに、(1) 作った file の path と sha256、(2) 生成器の sha256、(3) 実走した command・rc・要点 (1〜4)、(4) 負例 4(c) の実測結果、(5) 未実走の項目、を書き、最後に `## 総括` 節を置いて 3 行以内でまとめる。
