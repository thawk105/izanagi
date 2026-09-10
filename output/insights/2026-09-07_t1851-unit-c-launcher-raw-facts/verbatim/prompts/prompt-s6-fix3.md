単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s4-adjudication.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s4-adjudication.md` — 親の段 4 裁定 (4 節 plan v2 — C1a、変異 M1〜M12)。本 fix の契約
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/prompt-s5-launcher.md` と `prompt-s6-fix2.md` — 実装子 / fix2 の契約 (所有 path、禁止事項、DW-S05-C の検査・報告)。**本 fix は同じ権限境界・禁止事項を全文継承する**
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/artifacts/t1851-unit-c/s6-rereview.md` — 統合後の焦点再レビュー (NO-GO)。親の裁定は下の「依頼」に書く
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s5-s6-fix2-integrated-snapshot.patch` — 現在の統合差分 (実装子 + fix1 + fix2)。本 worktree にはこれが適用済み

作業 repository は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-c-fix3` (branch `fix-dev-wave-t1851-unit-c-3`、base `04f06d032` + 統合 patch 適用済み、未 commit) である。コードはすべてこの worktree の中で読み書きする。

## 所有 path (これ以外は 1 byte も変更しない)

- `orchestrator/campaign/s8b_floor_attempt_launcher.py`
- `orchestrator/tests/test_s8b_floor_attempt_launcher.py`

`test_official_perf_closure.py` の guard は `_checked_reservation_policy` 内の 2 つの `if` 条件式の ast.unparse 逐語に束縛されている。**その 2 つの式は変えるな**。adapter / core / profile / campaign / calibrator、他の test file、docs は所有外。

## 依頼 — 再レビュー所見の fix (4 件) と親の裁定

各所見に対し、完了報告へ **closed / partial / regressed の対応表**を書け。

1. **A-1 (親裁定: real、must-fix) 検査済み kwargs の nested 別名。** `_checked_measurement_keyword_arguments` (launcher :475-493 付近) が作る copy は浅い `dict` であり、`workload` / `extra_env` (Mapping)、`numactl` (sequence) は元 object と同じ値 object を共有する。copy 作成時に、値が `Mapping` なら独立した `dict`、`list` / `tuple` なら `tuple` に固定する (1 段でよい。sealed capability や callable などそれ以外の object は identity のまま保持し、深い copy をしない)。既存の A-1 node (`test_capture_uses_checked_kwargs_snapshot_after_source_mapping_mutates`) を拡張するか別 node を足し、pre-probe の中で元 Mapping の nested container (`extra_env` の中身と `numactl` の要素) を書き換えても fake capture が受け取る値が検査時の値のままであることを検査する。`_capture` が `measurement.keyword_arguments` を再読していないことは維持。
2. **A-3 (親裁定: real、must-fix) callable 負例の単一理由性。** protocol / receipt の callable 負例を、`_contains_callable` を外すと後続の canonical 化・receipt 検査を**通ってしまう**入力にする: `__call__` を持つ `dict` subclass に valid な内容 (protocol は binding の digest と一致する内容、receipt は valid な receipt 全体で measurement の `use_perf` を導出値へ合わせる) を持たせ、拒否 message が callable gate のものであることを固定する。marker は現状 (非 None gate) のまま。
3. **R-1 (親裁定: real、must-fix) fix2 で緩んだ値検査を戻す。** `repetition_evidence` の snapshot 検査 (test :817-825 付近) を、fake が private sink へ書いた 3 record 全体 (実体同形 6 key の値まで) と exact tuple で比較する形へ戻す。`rep_index` 列と key 集合だけの検査は緩和である。B-2 の要点 (private sink 由来であり public `rep_observations` を読んでいない) は維持する。
4. **R-2 (親裁定: nit、予算内なら) A-2 node の固定強化。** `test_open_failure_cannot_be_reported_as_observed` の observed 申告で `observation_sha256` / `primary_value` を non-null の valid 値にし、拒否後に registry の terminal / observation が呼ばれないことに加え、出力 (seal) が未封印であることを recorder で検査する。

**M12 について (親裁定: 本 wave では変更しない)。** 再レビューは「失敗理由なしの `terminal-failure` は実 core では無効」と指摘した。open 失敗の失敗理由は terminal 証拠の契約 v2 (`failure{stage}`) が定めるもので、C1a は v1 terminal API のまま置く裁定である。M12 node は fake registry で snapshot が空 tuple であることだけを固定しており、この形を変えない。

## 規模上限

production +10〜40 / −10、test +40〜140 / −30。超えそうなら止めて報告する。

## 検査・報告 (DW-S05-C を継承)

- `PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_attempt_launcher.py` (自走 harness) を実走し、緑には実走 nodeid・範囲を併記する。pytest wrapper が sandbox で動かないなら理由を書く。
- 既存テストの期待値を変えない (反転・緩和・skip・削除は禁止。R-1 は「緩和を元に戻す」向きだけ)。赤なら実装側が誤りとして報告する。
- fixture へ現行 hash を差し込むなど、テストを甘くして緑にしない。揮発 payload を焼き込まない。
- 完了報告に所有外への波及 (`test_official_perf_closure.py` の guard 逐語、`test_ccbench_spawn_sites.py:212`) を静的列挙する。
- commit しない。docs を編集しない。

## 制約

- 出力へ結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力の最後に `## 総括` 節を置き、所見 4 件の closed / partial / regressed、変更行数、新設・変更 node 数、実走結果を 10 行以内で書け。
