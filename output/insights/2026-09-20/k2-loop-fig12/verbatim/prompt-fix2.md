単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 6 裁定 2 巡目 (fix2 の仕様の正本): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/s6-adjudication-2.md
- 焦点再レビュー逐語 (所見の根拠): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/codex/s6-focus.md
- 段 6 裁定 1 巡目 (fix1 の仕様、維持する事項): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/s6-adjudication.md
- fix1 の報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/codex/s6-fix1.md
- caption_source の稿 (§0.1 の還流の定義、§1.5 の run-card 既知集合、§2.2 / §2.3 の経路): /work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md
- 編集対象の現物 3 file: /work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/tools/plotting/plot_k2_loop_flow.py、/work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/tools/plotting/k2_loop_flow_2026-09-20.json、/work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/orchestrator/tests/test_plot_k2_loop_flow.py

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

研究用 repo の論文用説明図 (matplotlib の模式図) の生成器・入力 JSON・単体 test に対する、焦点再レビュー所見の小さな fix (2 巡目) である。セキュリティでも攻撃でもない。生成器は凍結済みの稿から人が JSON へ写した「3 巡のデータフロー」を描くだけで、判定・値・認証を再計算しない。性能値は図のどこにも出さない。

# 依頼 — fix2: 段 6 裁定 2 巡目の「採用」6 項目を実装する

## 所有 path (これ以外は編集禁止)

1. `tools/plotting/plot_k2_loop_flow.py`
2. `tools/plotting/k2_loop_flow_2026-09-20.json`
3. `orchestrator/tests/test_plot_k2_loop_flow.py` (同 wave の新 test file で、編集対象)
4. `probe-k2fig12/` (untracked の scratch)

## 禁止 (各項を個別に守ること)

- `git add` / `git commit` / `git stash` / `git checkout` / `git switch` / `git reset` を一度も実行しない。commit は親が行う。
- docs を編集しない (`docs/` 配下の全 file、`tools/plotting/README.md`、`tools/plotting/FIGURE_CONVENTIONS.md`、`docs/handoff/` への file 作成を含む)。`docs/paper-story/figures/` へ file を作らない。`output/` と `.claude/` 配下へ書かない。
- 所有外の既存 file を編集しない。`tools/run_tests.py` と `python -m pytest` は使わない。
- tracked の既存テストの期待値を変えない。自分の test file 内でも、反転・緩和・skip・xfail・削除で緑にしない。
- 生成器へ判定・値の計算経路を足さない。
- 変異登録の anchor 文字列 (裁定 2 巡目「fix2 の所有と契約」に列挙) を保つ。変えるなら報告に旧→新を書く。

## 作業 (正本は裁定 2 巡目の表)

1. **F-M1:** caption の還流の文を裁定の固定文に差し替え (回数語の可変生成 `_arrow_count_words` を廃止)。生成器に定数 `EXPECTED_ARROWS` (id / kind / from / to の 7 組: m1 measurement-reflux round-1.evaluation→round-2.parent、m2a measurement-reflux round-2.evaluation→after-round-2.parent、m2b measurement-reflux round-2.evaluation→round-3.parent、d1 diagnosis-reflux round-2.critic→round-3.parent、a1 absent round-1.critic→round-2.parent、a2 absent round-2.critic→after-round-2.parent、a3 absent round-3.critic→null) を置き、`load_flow` で JSON の arrows と完全一致を要求 (不一致は拒否)。test は稿から手で確定した独立の 7 組の表を持ち、JSON と provenance `arrows` の両方と照合する (負例: 1 本の to を変える → 拒否)。
2. **F-M2:** caption の規律 6 の文を typed bool に束縛 (全 false / 1 つでも true で文が変わる)。凡例の coder 集約は coder の 4 出力だけから (`false in all four coder outputs` / `true in at least one coder output`)、全 role 集約は別の句 (`no role reported detection` / `at least one role reported detection`)。反転 test を planner 単独 true でも caption と凡例が変わる形に広げる。
3. **F-S1:** role cell の固定 template を `instruction-like content: none detected (self-report)` / `instruction-like content: detected (self-report)` に。
4. **F-S2:** proposal cell の `known` / `not known` を `in the run-card known set` / `outside the run-card known set` に。lane-proposal の sublabel の `known-value re-proposals` を `run-card known-value re-proposals` に。
5. **F-S3 / F-S4:** 1 で閉じる (test 側の独立表と `EXPECTED_ARROWS`)。
6. caption の固定文 1〜8 (裁定 1 巡目・fix1 の逐語) は維持し、test の逐語検査も維持する。

## 検査 (sandbox で走るものだけ)

1. `PYTHONPATH=. python3 orchestrator/tests/test_plot_k2_loop_flow.py` (self-run harness)。着地 test 以外が全部 passed、所要秒を報告。
2. 実データ実走: 既存の `probe-k2fig12/` の 3 file を消してから `python3 tools/plotting/plot_k2_loop_flow.py probe-k2fig12/fig12_k2_manual_loop_dataflow` が rc=0。provenance の `caption` 全文と drawn_items のうち変わった行を報告に写す。
3. `PYTHONPATH=. python3 orchestrator/tests/test_plain_runner_coverage.py`、`python3 tools/check_subprocess_bytecode_guard.py --repo /work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit`。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない。出力は file に書かず、最終メッセージの本文に全文を書け)

## 所見ごとの対応表
F-M1 / F-M2 / F-S1 / F-S2 / F-S3 / F-S4 の closed / partial / regressed と file:関数 (test は nodeid)。
## 実走した検査
nodeid と passed / failed / skipped 件数、所要秒。実データ実走の rc、caption 全文、変わった drawn_items 行。
## 変異 anchor の維持
裁定に列挙した anchor 文字列が現物に残るか (残らないものは旧→新)。
## 所有外への波及
無ければ「無し」と根拠。
## 総括
実装済み / 未実走 / 期待赤 / 親への依頼 を 5 行以内。
