単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-impl

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-freeze-v2-g1-candidate/s5-author-prompt.md` — 段 5 実装子契約 (権限・所有・禁止・検査・報告形式)。**全文を継承する**
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-freeze-v2-g1-candidate/artifacts/dev-wave-t2724-freeze-v2-g1-candidate/s6-review-a.md` — レビュー A
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-freeze-v2-g1-candidate/artifacts/dev-wave-t2724-freeze-v2-g1-candidate/s6-review-b.md` — レビュー B
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-impl/orchestrator/campaign/s8b_holdout_freeze.py` — 編集対象 (`_validate_floor_inputs` 1375〜1500)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-impl/orchestrator/tests/test_s8b_holdout_freeze.py` — 編集対象 (新規 3 test 1838〜1905、既存 helper `_rewrite_floor_artifacts_for_uncommitted_protocol_seed` 1726 付近)

repo root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-impl`。所有 path は段 5 と同じ 3 file。**既存テストの期待値を変更しない** (反転・緩和・skip・削除を禁じる。赤なら実装側が誤り。期待値が誤りなら実装を変えず報告して止める)。docs 編集・commit をしない。

## 親の裁定 (所見ごと)

| 所見 | 判定 | fix |
|---|---|---|
| RB-1 (must-fix) `protocol["master_seed"] += 1` は str に int 加算で TypeError | real | **F-1:** 既存 helper (T:1726 付近) と同じく文字列に接尾辞を足す形へ。改変前後で bytes が異なることも assert する |
| RA-2 (nit) / RB-4 例外文言の `reason.startswith(...)` 書換えは campaign 側文字列に結合 | real | **F-2:** 書換え分岐を削除し、`FloorCampaignError` は `FreezeError(f"floor protocol を index authority で解決できない: {exc}")` に包むだけにする。新規の版付き worktree 改変負例 (T:1895 付近) の match は `"floor protocol を index authority で解決できない"` にする。既存 anchor 負例 (T:1810〜1836) は producer 側の `protocol_raw != head_protocol_raw` 検査に到達する (resolver は anchor の worktree bytes を HEAD と比較しない) ので match を変えない |
| RB-3 (should) 「固定 protocol hash と不一致」は解決後の意味と合わない | real | **F-3:** HF:1488 の文言を `"floor result.protocol_sha256 が解決した protocol hash と不一致"` に改め、新規負例 (T:1879) の match も同じ語へ。旧文言を match する他 test は無い (親が grep で確認済み) |
| RA-1 (should) `protocol_raw != record.raw_bytes` は HEAD blob 比較と同一 bytes を比べる冗長検査 | real | **F-4:** 追加した `if protocol_raw != record.raw_bytes: raise …` を削除する (record.raw_bytes は同じ commit の HEAD blob なので恒真)。`record.commit_oid != head` の検査は残す |
| RB-2 (should) closure の除外 assert は除外前 hit の実在を示さない | real (記録) | fix 不要。親が記録に「独立の検出力に数えない」と書く |
| RA-3 / RB-4 / RB-5 変異 M3・M5 | real (登録側) | fix 不要。親が M3 を診断差、M5 を登録外に再分類する |

## 検査

- 段 5 契約と同じ焦点走を試みる。dispatch 障害なら「実装済み・未実走」と書く (親が実走する)。
- `python3 -c "import ast; ast.parse(open('orchestrator/campaign/s8b_holdout_freeze.py').read())"` 相当の parse 確認、`git diff --check`。
- `FLOOR_PROTOCOL_REL = "…"` 代入 1 件、`_run_git*` 各 1 件、必須 3 呼出しが保たれていることを再確認する。

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け。** 見出しはすべて `##`、最後の節は必ず `## 総括`。

節の順:

## 所見ごとの対応表 (closed / partial / regressed)
## 変更点 (file:line)
## 実走した検査と結果
## 総括
