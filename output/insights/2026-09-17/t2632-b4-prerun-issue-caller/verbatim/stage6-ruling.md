# 段 6 レビュー所見の裁定 — dev-wave-t2632-b4-prerun-issue-caller

| # | 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| A1 | review A | `missing[].artifact_path` / `artifact_key` が全 12 field で `loop_state.json` / `whiteboard[i]` を指す。field の出所として参照していない artifact を指すのは記録の値の誤り (DW-G05: 不足レポートの参照値が変わる) | real / must-fix | 採用。両 key を `null` にする (候補の所在は `campaign_root` / `whiteboard_index` / `iteration` が持つ)。B の nit 2 (docstring で「12 項目は現行保存形式の既知の制限に基づく静的な不足分類」と明記) も同時採用。B の「checkpoint を観測位置として維持」は A1 と両立しないので A1 側を採る (key 名が「その field の出所 artifact」を含意するため) |
| A2 | review A | `json.loads` の `RecursionError` が `except (OSError, UnicodeError, ValueError)` から漏れ typed stop でなく未捕捉終了になる | real / must-fix | 採用。捕捉集合へ `RecursionError` を足す |
| A3 | review A | M3 / M4 (と M9) は fail-closed の kill でなく構造化出力の diagnostic sensitivity pin (DW-M08) | real / must-fix (記録) | 採用。spec には残すが insight / worklog で「診断感度 pin」として別枠記録し、fail-closed の検出力に数えない |
| A4 | review A | M10 の置換が具体化されていない | plausible / nit | 採用。M10 = `f"{attempt.attempt_id}.json"` → `"attempt.json"` (全行同一 path → 発行器 `PLANNED_RESULT_PATH_DUPLICATE`、T5 の `rc == 0` で赤、単一理由) |
| A5 | review A | `registry_ordinal` は概念のみ | real / nit | 記録のみ (行を作らないので番号は生成しない。裁定と等価) |
| A6 / A7 | review A | 候補ありで発行する経路 / stub 化 | refuted | — |
| B1 | review B | whiteboard 行に未使用の `direction` / `magnitude` / `delta_pct` を必須にする検査は要求外 (DW-G05) | real / must-fix | 採用。行検査は `isinstance(row, dict)` と `result` / `iteration` の存在だけに絞る。`test_unreadable...` の `row` case (`[null]`) はそのまま通る |
| B2 | review B | 静的な欠落理由が探索済みの不存在証明に読める | plausible / nit | 採用 (A1 と同時、docstring 1〜2 文) |
| B3 | review B | 内部関数の戻り値が裁定の表記 (`(batch, missing)`、`issue -> dict`) と違う | real / nit | 不採用 (変更しない)。件数と rc の受け渡しに閉じた差で JSON 契約は一致。DW-O12 に従い worklog には実際の形を書く |
| B4 / B5 / B6 | review B | 常に空 batch / 例外型と追加 test / 文言・英語・相対 path | refuted | — |
| B (現物予測) | review B | 現物実行の予測 JSON と rc=2、root 非作成の根拠 | — | 親が fix 後に 1 回実行して照合する |

## fix 単位 (Codex 1 本、実装 worktree、所有は同じ 2 file)

1. `orchestrator/campaign/p3_b4_prerun_caller.py`
   - `except (OSError, UnicodeError, ValueError)` → `except (OSError, UnicodeError, ValueError, RecursionError)`。
   - 行検査を `isinstance(row, dict) and {"iteration", "result"} <= row.keys()` に絞る (message は「lacks result/iteration」等に合わせる)。
   - `missing` の `artifact_path` / `artifact_key` を `None` にする。
   - `collect_scheduled_batch` の docstring に「12 項目の欠落は現行保存形式 (checkpoint 5 field、WAL genome / src_token) の既知の制限に基づく静的分類であり、個別 artifact を探索した結果ではない。`artifact_path` / `artifact_key` は参照した出所が無いので null」を足す。
2. `orchestrator/tests/test_p3_b4_prerun_caller.py`
   - T2 の `artifact_path` / `artifact_key` 期待を `None` に。
   - `test_unreadable_campaign_never_calls_issuer` に「`result` 欠落の行」と「深い入れ子 JSON (`"[" * 100000 + "]" * 100000` 相当で `RecursionError` を起こす lock)」の 2 parameter を足す (既存 6 parameter は残す)。**`direction` 等が無い行は解釈可能** (候補判定に進む) ことを 1 本足す: `{"iteration": 1, "result": "rejected"}` だけの行 → `scheduled_input_sources_missing`、`candidate_count == 1`。
   - 他の既存期待値は変えない。

## 変異 matrix v2 (spec 用、期待 node は probe で確定)

| ID | 置換 (実装 file、fix 後の行で確定) | 期待 | 分類 |
|---|---|---|---|
| M0 | `# All twelve sources are absent in the current storage format.` の comment 本文を変える | SURVIVED | 等価対照 (positive) |
| M1 | `if row["result"] == "rejected":` → `if row["result"] != "success":` | KILLED: T3 | fail-closed (negative) |
| M2 | `if missing:` 分岐を潰す (`if missing and False:`) | KILLED: T2, test_all_candidates | fail-closed (negative) |
| M3 | `_MISSING_SOURCES` から `bootstrap_member` 行を削除 | KILLED: T2, test_all_candidates (+ 新 `result`/`iteration` のみ行の test) | 診断感度 pin (negative) |
| M4 | `_MISSING_SOURCES` から `arm_digest_received` 行を削除 | 同上 | 診断感度 pin (negative) |
| M5 | campaign loop 内で候補 0 の campaign ごとに `issue(())` を呼び最初の例外で返す形 | KILLED: T1, T2 | fail-closed (negative) |
| M6 | `issuer._REPOSITORY_ROOT / "output/b4-prerun-publication"` → `Path.cwd() / "output/b4-prerun-publication"` | KILLED: T1, T3, T5 | fail-closed (negative) |
| M7 | `issue` の except 側 `}, 2` → `}, 0` | KILLED: T1, T3 | fail-closed (negative) |
| M8 | `payload, rc = issue(batch)` → `payload, rc = (issue(batch) if batch else ({"issued": None}, 0))` | KILLED: T1, T3 | fail-closed (negative) |
| M9 | `"manifest_row_count": len(publication.manifest.rows),` 行を削除 | KILLED: T5 | 診断感度 pin (negative) |
| M10 | `f"{attempt.attempt_id}.json"` → `"attempt.json"` | KILLED: T5 | fail-closed (negative、発行器の path 重複拒否) |
