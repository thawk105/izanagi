FOCUS-01 / FOCUS-02 を実装しました。編集は指定された 2 ファイルのみで、docs・fixture・固定 SHA・status 算出・commit には触れていません。

- [_read_design](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-rulings/orchestrator/tests/calibration_freeze_authority_contract.py:272): comment 除去と未閉鎖専用分岐を削除。`<!--` または `-->` があれば `design document must not contain HTML comments` で拒否。
- [負例 node](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-rulings/orchestrator/tests/test_calibration_freeze_authority_contract.py:664): canonical Markdown 行を comment 内へ移し、可視側を非 Markdown の `<tr>` drift 行へ変更。comment 素通し実装なら受理され、本修正では拒否される構成です。

### 受理・拒否の変化

| 類型 | 1巡目 fix | 修正後 | 差 |
|---|---|---|---|
| code fence 内 opener と外側 closer が可視 drift を挟む | 受理し得る | comment 存在で拒否 | 受理集合を縮小 |
| otherwise-valid 文書の balanced comment | 除去後に受理 | 拒否 | 受理集合を縮小 |
| opener のない `-->` | 受理し得る | 拒否 | 受理集合を縮小 |
| 未閉鎖 `<!--` | 専用理由で拒否 | 指定理由で拒否 | 診断理由のみ変更 |
| comment 内 canonical 行＋可視の非 Markdown drift（今回の負例） | 抽出行不足で拒否 | comment 存在で拒否 | 1巡目比では診断差。ただし comment 素通し実装では受理されるため、負例として受理集合差を検出 |
| HTML marker のない文書 | 従来どおり | 従来どおり | 変化なし |

### 既存 4 抽出器への影響

`_extract_design_row_ids`、`_extract_ruling_ids`、`_extract_design_selection_enums`、`_fixture_assignment_gate_id_from_design` はすべて `_read_design` を通るため、comment を含む文書を抽出前に同一理由で拒否します。comment のない文書には原文がそのまま渡るため、4 抽出結果は不変です。現行設計正本の `<!--` / `-->` は各 0 件でした。

検査結果:

- AST parse: 2 ファイル成功
- `git diff --check`: 成功
- pytest: `tools/run_tests.py` で対象ファイルを起動したものの、Pegasus の `qstat -Q` preflight が失敗し rc=16。pytest 本体は未実走です。

## 総括

HTML comment の除去を廃止し、marker の存在を fail-closed で拒否しました。  
負例を comment 素通し実装なら受理される構成へ修正しました。  
既存 4 抽出器は comment-free 入力で不変です。  
静的検査は成功、pytest は dispatch 障害により未実走です。