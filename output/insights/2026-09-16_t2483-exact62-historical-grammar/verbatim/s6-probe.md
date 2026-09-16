## 作成ファイル

[t2483_real_corpus_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2483-impl/t2483_real_corpus_probe.py) のみ作成しました。

`--repo-root` は必須です。対象は `--rr5`・`--rr50`・`--rr95`・`--exact24` で上書きできます。`--out` は campaign 配下を拒否し、新規ファイルだけに出力します。

## JSON schema

| キー | 意味 |
|---|---|
| `schema_version`, `repo_root` | 形式識別子、使用リポジトリ |
| `imports` | API の import 結果と実ファイルパス |
| `campaigns` | 実 3 本の独立した結果 |
| `negative_control` | exact-24 の独立した結果 |
| `completed` | 全測定ループの完了 |
| `required_checks_passed` | C を除く必達条件・対照・拒否・不変性の総合判定 |
| `errors`, `output` | 全体エラー、任意ファイル出力の結果 |

各主体には次を記録します。

- `subject`, `campaign_dir`, `expected_path_count`：対象情報。
- `hashes_before`, `hashes_after`：lock・WAL の SHA-256。
- `A_decode`：返却型、記録 path 列、件数、期待 tuple との一致。
- `B_epoch`：返却型、state、epoch、両 scope、conformance、scope 一致。
- `C_admission`：返却型と read purpose。実 3 本のみ。
- `certified_rejection`：拒否、想定例外型、予期しない成功。実 3 本のみ。
- `bytes_unchanged`：ファイル別一致と総合判定。

各段の `status` は `ok/error/blocked`、判定は `passed`。例外の `exception.chain` に型名・module・文字列を外側から全 `__cause__` 分記録し、循環は `cause_cycle_to` で示します。

## 成功条件と行番号

| 段 | 成功条件 | 行 |
|---|---|---|
| 前後 hash | 読み取りと SHA-256 計算が例外なく完了 | 43–51、68–78 |
| 必達 A | decode 成功、期待 tuple と一致、tuple 型、62 件 | 81–92 |
| 必達 B | exact `HistoricalCampaignVerifierEpoch` 型、`state == "E1"` | 103–110 |
| 測定 C | API 成功、exact `HistoricalCampaignView` 型、歴史 purpose | 113–119 |
| exact-24 対照 | A を24件の既存 tuple で判定し、B も成功 | 85–92、177、189–190 |
| certified 拒否 | gate が `ArtifactAdmissionError` 系を送出。別例外は失敗として記録 | 122–135 |
| bytes 不変 | 両ファイルで前後 hash が取得でき、一致 | 138–144 |

## 総括

指定の script 1 本の作成を完了しました。script・pytest は実行していません。  
他ファイルの変更、実 corpus の複製、Git 操作は行っていません。  
実測結果は未確認です。C の後段 gate 拒否は記録対象であり、必達条件には含めません。  
stdout 自体が書き込み不能な場合、JSON の stdout 出力は保証できず、stderr へ退避します。