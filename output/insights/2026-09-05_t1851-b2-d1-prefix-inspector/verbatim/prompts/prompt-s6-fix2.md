単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s4-adjudication.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/prompt-s6-fix1.md` — fix1 の契約 (**全文継承する**: 所有 path、production 変更禁止、テスト弱体化禁止)
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s6-fix1.md` — fix1 の完了報告
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/focus-2-failure.txt` — 親が統合 tree で実走した焦点走 2 の**赤 1 件の全文** (pytest の失敗本文)
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s4-adjudication.md` — 親の段 4 裁定

作業 repository は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-b2-d1-fix1` (branch `fix-dev-wave-t1851-b2-d1-1`、fix1 の状態のまま) である。

## 所有 path (これ以外は 1 byte も変更しない)

- `orchestrator/tests/test_s8b_floor_stats.py`

必要なら `orchestrator/tests/test_s8b_attempt_registry.py` の helper も所有に含めてよいが、既存 node の期待値は変えない。production 4 file、`test_s8b_holdout_admission.py`、docs、他 file は所有外。commit しない。

## 依頼 — 焦点走 2 の赤 1 件を閉じる

親の実走 (統合 tree、消費側 20 file、計算ノード): **1 failed / 2,266 passed / 8 skipped**。赤は fix1 が F1 で新設した
`orchestrator/tests/test_s8b_floor_stats.py::test_live_v5_real_registry_rejects_reported_other_generation` だけである。他の 2,266 node (fix1 の他の新設 node を含む) は緑。

失敗本文 (`focus-2-failure.txt`) の要点: 世代 B を作る `admission_cases._consumed_marker_capability_case(tmp_path / "b")` の中で、admission の予約
(`reserve_cell_holdout_admission` 相当) が同じ shared root に既存の claim file を見つけ
`HoldoutAdmissionError: measurement generation claim identity was unexpectedly reused` (`s8b_holdout_admission.py:1219` の `FileExistsError` から) で止まっている。
原因は fixture の作り方にある: `_consumed_marker_capability_case` → `_issued_cell` は campaign identity (campaign_run_id / run_relpath / manifest 等) を固定値で持つため、
protocol を `seed-b` に変えても measurement generation claim digest が世代 A と同じになり、同じ root では 2 つ目の予約が拒否される。**production の欠陥ではない。**

### 修正の方針 (優先順)

1. **(推奨) 世代 B に固有の campaign identity を与える。** `_issued_cell` / `_consumed_marker_capability_case` が identity を引数で受けられるなら
   (`test_s8b_holdout_admission.py` の helper の signature を現物で確かめよ) それを使う。受けられないなら、test 側で B の予約に必要な最小手順
   (fixed documents の書込み → admission 予約 → ticket 消費 → marker) を helper を組み合わせて別 identity で実行する。同じ shared root に **A と B の両方の有効な v2 世代**が
   実在し、`shared_admission_root(repo_a) == shared_admission_root(linked)` の assert を維持すること (裁定 A-2 の形)。
2. **(代替、1 が現実的でない場合のみ)** 世代 B だけを root に置き、外部引数 A の registry を不在にする形へ落とす。正しい実装は `unverifiable` /
   `attempt-registry-root-unavailable` または `attempt-registry-read-unavailable` で拒否し、M14 変異だけが B を replay して受理する。この形を採る場合は docstring に
   「A 不在の弱い形。A/B 両方有効の形は helper の identity 固定により本 wave では組めなかった」と明記し、完了報告に理由を書け。

どちらの場合も、同じ test 内 (または隣接 node) に **A/A の受理正例** (外部引数と artifact / proof が同じ世代を指し `[]` を返す) を保つ。inspector は monkeypatch しない。

### 禁止

- 既存 node の期待値を変えない。反転・緩和・skip・削除を禁じる。
- production code を変えない。所有外 file を変えない。
- fixture へ現行 hash を差し込んで通す形にしない。

## 検査・報告

- 実走できる範囲で `python3 -m pytest orchestrator/tests/test_s8b_floor_stats.py -q -k "real_registry or live_v5 or live_v4"` を走らせ、緑には nodeid を併記する。
  実走不能なら「実装済み・未実走」と書く (親が統合 tree で再走する)。
- 完了報告に、採った方針 (1 か 2)、変更 file と行数、A/B 両方が同じ root に実在することを示す assert の有無、を書け。
- 出力へ結合文字 U+0300〜U+036F を使わない。予算が尽きそうなら途中結論を書いて終われ。
- 出力の最後に `## 総括` 節を置き、5 行以内で書け。
