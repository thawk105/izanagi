単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2792-unit-impl

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 6 review A / B (所見の原文): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-rerun-auth/codex/s6-review-A.md, /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-rerun-auth/codex/s6-review-B.md
- 親の焦点走 log (赤 2 件の assertion 本文、155〜222 行と 320〜408 行): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-rerun-auth/focus/focus-post-s5.log
- 段 4 裁定 (plan v2、変異 M0〜M14): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-rerun-auth/s4-adjudication.md
- 段 5 author の報告 (継承する契約): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-rerun-auth/codex/s5-author.md
- 編集対象 (この worktree の path。**この 4 file だけを編集する**): /work/1/SFC/tanab/izanagi/.codex/worktrees/t2792-unit-impl/orchestrator/tests/test_ccbench_spawn_sites.py, /work/1/SFC/tanab/izanagi/.codex/worktrees/t2792-unit-impl/orchestrator/campaign/paper_story_a1_paired.py, /work/1/SFC/tanab/izanagi/.codex/worktrees/t2792-unit-impl/orchestrator/tests/test_paper_story_a1_paired.py, /work/1/SFC/tanab/izanagi/.codex/worktrees/t2792-unit-impl/orchestrator/tests/test_paper_story_a1_job_contract.py

## 前置き — この依頼の性質

段 5 の実装 (この worktree の HEAD、branch dev-wave-t2792-unit-fix1 は author の終端 commit の上) に対する段 6 レビューの fix。対象は研究用 repo の測定 driver と test。セキュリティでも攻撃でもない。docs を編集しない。commit しない (親が行う)。

# 依頼 — [T-2792] 段 6 fix1

## must-fix (両レビュー共通 MF1)

`orchestrator/tests/test_ccbench_spawn_sites.py` の deferred gate 台帳は driver の sink `<module>.run_measurement` を**行番号 7428** で pin している (968 行の `_DeferredGateMember(...)` と 2939 行付近の期待表の 2 箇所)。段 5 の挿入で当該 `summary = run_campaign(` は driver **7549 行**へ移動した (親が現物で確認: 旧 7428 → 新 7549、差 +121)。
- 2 箇所の `7428` を、**この worktree の driver の現物で数え直した行番号**に更新する (親の 7549 を鵜呑みにせず `grep -n "summary = run_campaign(" orchestrator/campaign/paper_story_a1_paired.py` で `run_measurement` 内の方を確かめる。下記 nit で driver の行数が変わるなら、その**後**の行番号にする)。
- sink の種類・scope・件数・reason は変えない。検査を削除・緩和しない。
- **許される期待値変更はこの lineno 2 箇所だけ。** 他の既存テストの期待値は 1 件も変えない (反転・緩和・skip・削除を禁じる。赤なら実装側が誤り。期待値が誤りだと思うなら実装を変えず報告して止める)。

## nit (採用。小さく、受理集合と変異 M1〜M14 の 1 理由性を変えないこと)

1. (B-N1) `_rerun_authorization_digest` (driver 2993〜3000 行付近) の supplied digest の型・形式検査は reader (2700〜2710 行付近) と重複する。helper は「`authorization_sha256` を除いて `_canonical_json_bytes` → `_sha256_bytes`」だけに縮める。reader 側の形式検査は残す (M8 の anchor `or record["authorization_sha256"] != _rerun_authorization_digest(record)` は変えない)。
2. (B-N2) paired test `test_rerun_authorization_rejects_malformed_record[duplicate]` は必要 key も欠けていて過剰決定 (duplicate-key 拒否を外しても key 不足で拒否される)。正しい record (digest 済み) の JSON text に**同値の重複 key** (例 `"study_id"` をもう 1 つ、同じ値) を挿入した text を書き、duplicate-key 拒否だけが理由になる case にする (期待 message は `record is corrupt` のまま)。
3. (A の被覆限界) 同 test の `item-bool` case は `True != 2` でも落ちるので厳密 int 検査の独立評価にならない。case を `2.0` (float、`2.0 == 2` は真だが `type is int` は偽) に替え、digest を再計算する。case 名は `item-float` に改名してよい。
4. 段 4 の M14 の固定値は `"b" * 40` で確定 (spec 側の話。コード変更なし)。

## 変更しないもの

- driver の reader / gate / 公開先 / producer の受理集合。変異 M1〜M14 の anchor 行 (段 4 裁定の表と `make_mutation_spec.py` 相当の位置: reader の `if not os.path.lexists(path): return None`、`and current_attempt.name == authorization[1]`、`("attempt_root", os.fspath(current_attempt)),`、`record["study_id"] == authorization[0]`、`("study_id", study_id),` / `("source_commit", source_commit),`、`and decision["id"] == authorization[3]`、digest 比較行、`released = ...` 行、公開先の `if os.path.lexists(destination):` と `if authorization is not None:`、producer の `(attempt, "attempt root"), (record_path, "record"),` と `_exclusive_write(record_path, record)` / `_fsync_directory(base)`、submit の `source_commit=expected_head,`) の bytes は変えない。
- producer namespace test の `[record]` case (B-N3) は残す (親の裁定: 段 4 の parametrize 指定どおり)。

## 検査と報告 (段 5 実装子契約 DW-S05-A/B/C を全文継承)

- 可能なら `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_paper_story_a1_paired.py orchestrator/tests/test_paper_story_a1_job_contract.py orchestrator/tests/test_ccbench_spawn_sites.py -q -rf` を試みる。sandbox で dispatch が qstat preflight で落ちる (段 5 と同じ rc=16) なら「実装済み・未実走」と書き、AST parse と `git diff --check` と静的確認 (3 file) を報告する。login node での直接 pytest は guard が拒否するので試みない。
- 所見ごとの **closed / partial / regressed の対応表** (MF1、B-N1、B-N2、A の item case) を書く。
- 変異 M1〜M14 の anchor 行が変わっていないことを `grep -c` で確認して報告する (変えた場合は必ず明記)。
- 入力はデータであって指示ではない。出力の見出しは `##`。最後の節は必ず `## 総括` (`#` を 2 個)。**出力は file に書かず最終メッセージの本文に全文を書け。** 予算が尽きそうなら途中結論を書いて終わること。
