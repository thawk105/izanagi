# 段 4 裁定 — prune-orchestrator-batch2 (md_4)

基準: local main 4f412c67bcd7ff9cca1e78ce9bd1dd7a15d46037。入力: s1-brief.md、s2-plan-codex.md (Codex gpt-6-sol / medium、read-only、check_codex_output rc=0)。
段 4 直前の裁定 inbox 再走査: 開始後の新着は 2026-09-30-rulings-full40-verdicts.md (第 40 回) だけで、本件の候補・台帳に触れる項なし。

## 所見の裁定

| 所見 | 裁定 |
|---|---|
| S2: 候補は「12 module」ではなく 9 群 (submission_gate/ の 11 file + campaign 8 module = 19 file) | **real、採用**。親 brief の件数の誤り。記録では「9 群・19 file」と書く |
| S2: P1 支持、ただし t139 承認 manifest が直接 pin するのは fixture index (orchestrator/tests/fixtures/t338_submission_gate/conformance/index-v2.json @ 6d431a60a) で、11 実装 file ではない | **real、採用**。submission_gate の保持根拠は D574・D597・D749 (有効な決定が実装として名指し) と、T-139 が持ち越しに active で残ること (D2257 項 7、取り下げても D は取り消さない)。manifest は fixture 側の拘束として別に書く |
| S2: P2〜P6 支持 (根拠 file:line 付き) | **real、採用** |
| S2: backoff_sweep_report の検査は専用 test でなく共有の test_backoff_consumers.py にある | **real、採用**。「専用 test」の対が存在しない候補として記録 |
| S2: s8b_oracle_exploration の test (test_s8b_oracle_artifacts.py) は official loader も検査する共有 test | **real、採用**。D2179 の専用性不成立を追加の根拠に書く |
| S2: hash (sha256・blob) の hit は歴史的言及・再利用記録・到達性台帳だけで、新しい live pin ではない | 親の独立 hash 検索 (candidate-hash-hits.txt) の結果と突き合わせて記録 |

## 裁定

- **削除 0 (実装しない)**。9 群のどれも D1989 (現役の拘束的 consumer が無い) と D2179 (3 連言 + 専用 test の専用性) を同時には満たさない。未確認の条件は 1 つも無く、全群が確認済みの拘束で残る。
- 状態遷移は 4→7→8→9 (段 5・6 の実装・fix なし)。
- 段 3 は省略: 段 2 の段階で実装面の変更ゼロが確定し、受理集合も変わらないので DW-C00 の独立敵対検証子必須の条件 (受理集合が変わる・正しさ防壁に触る・設計択一が割れる) が不成立。段 2 には「残しすぎ」「消しすぎ」の両方向の検査を課した。
- 一次資料から事実を再抽出する docs-only なので、DW-C00 に従い段 7 の記録に対して独立 read-only レビュー 1 本を commit 前に置く。
- 変異 matrix: 実装面 (D95 決定 2) の差分ゼロで免除 (DW-S04)。
- 受入: 変更は output/insights/2026-09-30/prune-orchestrator-batch2/** と docs/spool/worklog/ の fragment 追加だけにし、D2316 の縮小受入 (`tools/dev_wave_wait.py acceptance --scoped`) で受ける。分類が不適格なら受入全走へ切り替える。
- 所有面の追随 (test_ccbench_spawn_sites.py:297、orchestrator/tests/README.md:181 の allowlist、nodeid 台帳、docs/README.md の地図) は削除 0 のため変更なし。
- commit 題: md_4 の指定どおり `prune(orchestrator): ...` とし、題に「削除 0・判定記録のみ」と明記する (後で `git log --grep='^prune'` で残した理由も引けるように)。
- decisions fragment は作らない (新しい設計判断はなく、D1989・D2179 の適用結果)。worklog fragment 1 本。
