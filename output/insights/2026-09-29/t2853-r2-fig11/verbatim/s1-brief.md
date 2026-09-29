# 段 1 brief — [T-2853] R2 fig11 単位 (2026-09-29 JST、親)

- 研究前進: 論文の fig11 (A-6 read-heavy 正式 certification、fixed 2 µs 対 stock、元 attempt `a6-20260908b`、outer `reject`、ComSys では表) の再現パッケージ R2。
  同じ protocol (`paper_story_a6_certification.v2.json`、protocol SHA-256 `21427e71…`) を**現行 repo の certification driver・現行 policy (5 node)・現行 CCBench pin `6810666`** で 1 回測り直した別 attempt の値と図を insight に残す。
  完了判定: attempt が完走 (または未完走・indeterminate をそのまま記述) し、collect した R2 の certification を元 attempt と並べた表と、fig11 と同じ生成器 `tools/plotting/plot_a2_certification.py` の R2 図 (描けなければ拒否理由) が insight にある。
- 確定済み裁定・前段: 投入単位は図 1 本 = 1 タスク (repro-rest §3.3)。先例 fig8b (別 attempt・非合成・地位は投入前に commit・同じ生成器・検査は外さない)。D2212 項 4 (1 タスクの job 合計 2 node 時間以上ならユーザー確認)、D2219 項 1 (受入 ≈ 0.25 を同じ線で数える)。
  D1870 (値を見た後に attempt へ昇格しない — 地位は結果前に固定)。結果稿 §3.2 (T-2430: 元の系列の反復 attempt は行わない) — R2 は再現パッケージの試行であって結果稿の反復 attempt ではない、と §0 で結果前に明記する。
- 不変条件: 規律 1 (正しさは job 内 trace 有効 build の別走、性能は trace 無効)・規律 2 (anomaly は即 reject、検査を緩めて描かない)。元 attempt の tracked 成果物 `output/insights/2026-09-08_t2411-paper-story-a6-certification/`・結果稿・既存 fig11 は bytes 不変。repo の実装面 (driver・生成器・policy) は変えない。
- 成果物: `output/insights/2026-09-29/t2853-r2-fig11/README.md` (+ verbatim/、図 PNG と provenance の写し)。worklog / phase の記録は spool fragment。repo 外: 出力親 `/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig11-20260929/` (collect-root・figure・wrapper)、attempt root は policy 固定 base の下の新 leaf。
- (P1) 投入 checkout: 着手時 main `035fc11fa` の detached worktree を `/work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/submit-tree` に作り (submodule 再帰初期化、CCBench = `6810666`)、そこから `bash tools/pegasus/submit_paper_story_a2_certification.sh --policy orchestrator/campaign/paper_story_a6_certification.v2.json --attempt-id a6-r2-20260929a …`。fig6 wave (A-2 policy、job 名 `paper-a2-cert`、base `dev-wave-paper-story-a2-cert-20260824`) とは checkout・job 名・出力 base がすべて別。
- (P2) 依存元: `--ccbench-root <submit-tree>/external/ccbench`、`--dependency-prefix-source /work/1/SFC/tanab/izanagi-a2-deps` (B-7 と同じ)、`--third-party-source-root` は永続 cache `/work/1/SFC/tanab/izanagi-thirdparty-cache` から `tools/pegasus/fetch_third_party.py hydrate` した repo 外の新 staging の `.source_root`。
- (P3) node 時間: 1 workload (rr95) = 1 job × 5 node。同じ A-6 protocol・5 node 形の実績 `a6-20260909b` (request 986046、Elapse 1,057 s、build cache 不使用) で 5 × 1,057 = 5,285 s = **1.47 node 時間** ((a) Elapse)。受入 1 回 ≈ 0.25 を足して約 1.72 < 2 → ユーザー確認不要と判定 (親の provisional 裁定・攻撃対象)。
- (P4) trace 保全口 (D2233): submitter の `qsub -v` は環境変数を固定列挙し `IZANAGI_TRACE_ARCHIVE_ROOT` を渡す口が無い → 使わない (driver 変更は scope 外)。
- (P5) collect: submit-tree の module で `collect --repo-root <出力親>/collect-root` (repo 外の空 dir)。materialize は `<repo_root>/<tracked_destination>` へ書くので元 attempt の tracked leaf に触れない。
- (P6) 図: repo 外の使い捨て wrapper (Codex author) が生成器の `main(argv, expected_hashes=…)` を R2 の certification / raw-manifest の実 sha256 で呼び、caption の役割語だけを差し替える。測定値の受理条件・レイアウト検査は差し替えない。原 metadata で描いた図の artist_series が既存 fig11 provenance と一致することを陽性対照にする。対照表は同じ生成器の `load_measurements` で元 attempt と R2 を読んで書く。
- (P7) 現行 pin `6810666` でこの driver を実機に通した記録は 0 件。起動時検査 (condition gate・patch 適用・source evidence) が測定前に落ちる可能性があり、login で事前に確かめられる範囲を段 2 で棚卸しする。
- 分割方針: 軽量版。計算ノード job を投げて数値を書く診断 wave なので段 2 plan 1 本・段 3 相談 1 本 (2 レンズを 1 本で)・段 5 author 1 本 (wrapper)・段 6 review 1〜2 本。
- 受入・実測環境: 測定は Pegasus gen_S (policy 固定 5 node、walltime 12h)。受入は `tools/dev_wave_wait.py acceptance` (所在は worklog)。
