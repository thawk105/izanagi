単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 6 裁定 (fix1 の仕様の正本。所見ごとの採否と対応、変異登録の更新): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/s6-adjudication.md
- 段 4 裁定 (plan v2 の元の仕様): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/s4-adjudication.md
- 親 brief: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/s1-brief.md
- レビュー A 逐語 (過剰・削除): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/codex/s6-review-A.md
- レビュー B 逐語 (逐語照合・正しさ境界・拒否条件表・変異の単一理由性): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/codex/s6-review-B.md
- 段 5 author の報告 (現行実装の説明): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/codex/s5-author.md
- 作図規約の正本: /work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/tools/plotting/FIGURE_CONVENTIONS.md
- caption_source の稿 (表示文字列の出所): /work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md
- 編集対象の現物 3 file: /work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/tools/plotting/plot_k2_loop_flow.py、/work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/tools/plotting/k2_loop_flow_2026-09-20.json、/work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/orchestrator/tests/test_plot_k2_loop_flow.py

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

研究用 repo の論文用説明図 (matplotlib の模式図) の生成器・入力 JSON・単体 test に対する、敵対レビュー 2 本の所見の fix である。セキュリティでも攻撃でもない。生成器は凍結済みの稿から人が JSON へ写した「3 巡のデータフロー」を描くだけで、判定・値・認証を再計算しない。**性能値は図のどこにも出さない。**

# 依頼 — fix1: 段 6 裁定の「採用」項目を全部実装する

## 所有 path (これ以外は編集禁止)

1. `tools/plotting/plot_k2_loop_flow.py`
2. `tools/plotting/k2_loop_flow_2026-09-20.json`
3. `orchestrator/tests/test_plot_k2_loop_flow.py` (**同 wave の新 test file で、編集対象**)
4. `probe-k2fig12/` (新規 dir、untracked のまま。実データで生成した scratch 図の置き場)

## 禁止 (各項を個別に守ること)

- `git add` / `git commit` / `git stash` / `git checkout` / `git switch` / `git reset` を一度も実行しない。commit は親が行う。
- docs を編集しない: `docs/` 配下の全 file (稿、`docs/paper-story/figures/README.md`、`docs/handoff/` への file 作成を含む)、`tools/plotting/README.md`、`tools/plotting/FIGURE_CONVENTIONS.md`。
- `docs/paper-story/figures/` へ file を作らない。`output/` 配下へ書かない。`.claude/` 配下を編集しない。
- 所有外の既存 file (他の生成器、tracked の既存 test、`conftest.py`、`orchestrator/tests/README.md`) を編集しない。
- `tools/run_tests.py` と `python -m pytest` は sandbox では走らない。使わない。
- **tracked の既存テストの期待値を変えない。** 自分の test file 内でも、反転・緩和・skip・xfail・削除で緑にしない。赤なら実装側が誤りとする。期待値が誤りなら実装を変えず報告して止める。
- 代役 (test double) の signature / 入力は直してよいが、production を代役に合わせて緩めない。
- 生成器へ判定・値の計算経路 (稿の数値の再計算、性能の比較、因果の主張) を足さない。

## 作業 — 段 6 裁定「所見の裁定」表の「採用」行を、その「fix1 での対応」列のとおり全部実装する

要点 (正本は裁定 file):

1. **A-M1 (must):** role cell の `discipline6` を typed object `{"form": ..., "instruction_like_detected": ...}` にし、form は role 固定を要求、marker の形は bool で変わり、drawn_items の text に `data boundary: none detected` / `data boundary: detected` を固定 template で含める。反転 test と form 不一致の負例。
2. **B-M1 (must):** 列見出しを typed (`number`、`kind`、`date_proposal`、`date_evaluation`) から `Round <n>` / `After round <n> (not a round)` + `proposal <date> (per round records) · evaluation <date> (job log)` (未評価列は `evaluation: none`) で組む。JSON の column `label` は削除 (typed から導く)。caption に固定文 7 を足す。
3. **B-M2 (must):** not-a-round 固有制約の独立負例 4 つ (kind だけ違反 / round 列で critic だけ null / round 列で date_evaluation だけ null / 巡 3 以外で has_diagnosis true)。各 1 理由で、拒否文言まで照合。
4. **B-M3 (must):** `collision` fixture を「登録済み Text の座標移動 (文字列不変)」に変え、T6 が publisher の layout 検査だけを理由に赤になるようにする。T6 は overlap / escape / arrow-crossing の 3 種で parametrize。T5 から `tmp_path` の空検査を外す。
5. **A-S1 / A-S2:** caption の固定文 7 と 8 を逐語で足す (裁定 file の文言)。role sublabel の `structural blockade` を `no tool access (structural blockade of tool use)` に。
6. **A-S3 / P1(b) / B-nit2:** coder cell は instance + `synthesizes one backoff literal` (値なし)。proposal cell は instance + `backoff literal <v>` + known / not known + evaluated / not + sublabel。`value` の語を使わない。sublabel の `outside the known set` 重複を除く。
7. **A-S4 / B-S3:** provenance `arrows` は描いた artist (layout) から組み (id / kind / from / to / visible)、保存前に JSON の arrows と完全一致を要求。caption の回数語は JSON の kind 別件数から生成 (once / twice / three times、4 以上は拒否)。test は JSON から独立に期待を組み、artist 可視と件数を照合。
8. **B-S2:** 凡例の固定文に coder の field 名 `data_boundary_report.instruction_like_content_detected` と、typed bool から組んだ `false in all recorded rounds` (全 cell が false のとき。1 つでも true なら `detected in at least one recorded round`) を書く。
9. **B 表の負例不足:** `test_t3_invalid_json_without_drawing` に各 1 例 (schema 固定、ISO 日付、reference_ids 形式・重複・未使用、roles 順序・definition_path、lanes 順序、columns 順序、certified flags、job 重複、instance 重複、arrow id 重複、non-absent の to null、`evaluated=true` で evaluation null)。
10. **A-nit1 / A 削除候補:** neutral marker 分岐を削除。lanes の planner / coder / critic は `id` と `source_anchor` だけにし表示は roles から導く (重複入力と一致検査を削除)。
11. **親の目視 (裁定 file の下 8 行):** `check_display_text` の token 照合で両端の `()[].:` を剥ぐ (JSON は `(R0)` / `(T-2795)` に)、absent で `to` が null の矢印は右への短い水平 stub + `×`、R6 marker を markersize 7 で cell 右上へ、副題 `Source: frozen results note <basename> (SHA-256 in provenance); figure created <date>`、round-1 evaluation の sublabel を `legacy verify condition` だけに、parent lane の sublabel 文言、lane の高さを内容に合わせて縮める (layout check が緑の範囲で)。
12. **変異登録の更新** (裁定 file 末尾、10 群 12 変異 + M11 群 2 変異): 各変異を殺す test の nodeid が裁定表のとおり存在するようにする。M7 の kill 理由が「検査なしで公開される」の単一理由になること (B-M3)。

段 4 裁定の plan v2 のうち、段 6 裁定が変えていない事項 (schema の他の部分、anchor、role 束縛、layout check、provenance の他の key、CLI、no-clobber、caption の固定文 1〜6 の逐語) は維持する。

## 検査 (sandbox で走るものだけ。実走した nodeid と件数を報告する)

1. `PYTHONPATH=. python3 orchestrator/tests/test_plot_k2_loop_flow.py` (self-run harness)。着地 test 以外が全部 passed であること。所要秒を報告 (目安 20 秒以内)。
2. 実データの実走: `python3 tools/plotting/plot_k2_loop_flow.py probe-k2fig12/fig12_k2_manual_loop_dataflow` が rc=0 で 3 成果物を出す (既存の probe 出力があれば先に消す)。provenance の `caption_source.sha256` = `1b0f6f568f17af4967362cb864a14c18ef9220f826e257c113da0065bb512758`、`arrows` の件数 (measurement-reflux 2 / diagnosis-reflux 1 / absent 3)、drawn_items の全文字列を報告に列挙する。
3. `PYTHONPATH=. python3 orchestrator/tests/test_plain_runner_coverage.py`、`python3 tools/check_subprocess_bytecode_guard.py --repo /work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit`、`orchestrator/tests/test_pytest_collection_config.py` の該当 test。
4. `git diff --stat` 相当は禁止 command を含むので行わず、変更 file の一覧を自分で書く。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない。出力は file に書かず、最終メッセージの本文に全文を書け — 親の launcher が保存する)

## 所見ごとの対応表
裁定表の各行 (A-M1、B-M1、B-M2、B-M3、A-S1、A-S2、A-S3、A-S4/B-S3、B-S1、B-S2、B 表の負例不足、A-nit1、A 削除候補、親の目視 8 項) について closed / partial / regressed と、対応した file:関数 (test は nodeid)。
## 実走した検査
nodeid と passed / failed / skipped 件数、所要秒。実データ実走の rc、arrows 件数、drawn_items の全文字列。
## 受理・拒否の含意
今回の変更で受理集合がどう変わったか (各 1 文)、通る正例 1 つ。
## 変異登録への対応
M1〜M11 の各変異について位置 (関数) と kill する nodeid、単一理由にならない変異があれば指摘。
## 所有外への波及
無ければ「無し」と根拠。
## 総括
実装済み / 未実走 / 期待赤 / 親への依頼 を 5 行以内。
