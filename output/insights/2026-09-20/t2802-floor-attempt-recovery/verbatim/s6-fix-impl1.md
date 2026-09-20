## 総括

**実装済み・未実走です。** 編集は [test_s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2802-unit-impl/orchestrator/tests/test_s8b_holdout_admission.py) のみ。production・docs の変更、git 操作、commit は行っていません。

case 数は **99 → 97（重複削減）→ 110（13 case 追加）**。今回の差分は +204／−3 行、author 分との追加行数の合計上限は618行で、+900行以内です。

以下の nodeid はすべて `orchestrator/tests/test_s8b_holdout_admission.py::` 接頭辞です。

| 変更 nodeid | case 数 |
|---|---:|
| `test_cut6_multiclaim_consumption_sequence` | 1 → 1 |
| `test_cut6_claim_error_precedes_main_read` | 9 → 7 |
| `test_cut6_claim_projection_entry_rejected[{extra-key,missing-key,identity}-{before-hit,after-hit}]` | +6 |
| `test_cut6_claim_attempt_ids_rejected[{type,element-type,duplicate}]` | +3 |
| `test_cut6_main_matching_row_count_rejected[{zero,two}]` | +2 |
| `test_cut6_legacy_projection_once_per_claim_per_call[{claim,main}]` | +2 |

波括弧は parameter の列挙です。N4 の残存 ID は `none-v1`、`none-v2`、`none-generation`、`entry-v2`、`entry-generation`、`seams-v2`、`seams-generation`。ASCII・改行なしです。

N1 の期待辞書は13 key を literal で明示し、production の文書 constructor を使わなくしました。

| field | 出所 |
|---|---|
| `schema_version` | literal `"s8b-holdout-measurement-generation-attempt-consumption/v1"` |
| `event` | literal `"consume"` |
| `observation_role` | literal `"floor_campaign"` |
| `cell_effect_digest` | 発行済み claim 文書の読取 |
| `measurement_generation_digest` | reservation の公開 field |
| `measurement_generation_claim_digest` | admission token の公開 field |
| `attempt_id` | fixture の cell ID と schedule の seq |
| `campaign_run_id` | reservation に渡す `"run-a"` |
| `manifest_sha256` | fixture が書いた manifest bytes の SHA-256 |
| `run_relpath` | protocol の `env_tag` と reservation の run ID |
| `cell_id` | protocol／freeze から列挙した cell |
| `freeze_holdout_key` | 同 cell |
| `configuration_id` | 同 cell |

追加負例の message は production の固定 literal と照合済みです。`after-hit` は、正常な別 claim の memo hit を通過した後、不正 claim の初回導出で拒否する構成です。呼出し途中のファイル改変は行いません。legacy は2 claim × 各2 attempt で、読取回数・次回の再読・claim/main 改竄拒否を検査します。

静的検査では構文、N1 の key 集合・constructor 非依存、変更範囲を確認しました。変更前 SHA との復元照合により、N1・N4 の parameter 列挙・追加4 test 以外が保持されていることも確認しました。

| 所見 | 状態 | 対応 |
|---|---|---|
| A-M4 / B-MF1 | partial | N1 の期待辞書を独立化。実走待ち |
| A-S1 | partial | v1 の重複2 case を縮約。実走待ち |
| A-S2 | partial | 指定境界の代表13 case を追加。実走待ち |

指定コマンドは実行要求しましたが、**pytest 未起動、実走 nodeid なし、passed 0／failed 0**です。緑・closed とは報告しません。

PreToolUse の `guard_bash` が、Pegasus ログインノードでの pytest 直接起動を拒否しました。指定された扱いに従い、dispatch せず「実装済み・未実走」で引き渡します。