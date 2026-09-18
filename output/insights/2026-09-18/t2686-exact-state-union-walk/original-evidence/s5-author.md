## 現行の受理・拒否挙動

`landed` は exact tree state または正式な fold receipt による正証拠で判定し、候補上限の1件先で照合できた正証拠も維持します。`not-landed` は closed-world の負証拠が成立した場合だけ返し、未証明・timeout・解析不能などは `indeterminate` に倒します。

## 変更面

以下、C は `tools/check_branch_landed.py`、T は `orchestrator/tests/test_check_branch_landed.py` です。

- **C:770、803**：strict NUL parser、遅延 supplier、tip memo、union／per-path fallback、有界走査と再走査、失敗 memo を実装。
- **C:913、1506、1864、2160**：supplier を照合・proof・assess に接続し、例外経路も含む timing を追加。
- **T:395、455、494、1090付近**：既存の注入面と signature を更新。既存 assertion の変更はゼロ。
- **T:2097以降**：旧 command との直接比較22ケース、parser、有界走査、fallback、走査本数、実 timeout、再走査 deadline、payload 比較を追加。

判定関数4つは AST が変更前と一致し、exact-state の候補照合部分は byte 単位で一致しています。

## 実走結果

**実装済み・未実走です。pytest の緑・赤はともに0件です。**

`pegasus02` の実行規律に従い、直接 pytest ではなく、次を runner 経由で試行しました。両方とも `qstat -Q preflight rc=1`、runner **rc=16／child_started=false** で終了しました。

```bash
PYTHONDONTWRITEBYTECODE=1 IZANAGI_TASK_RUN_AUTO_RECORD=0 \
python3 tools/run_tests.py orchestrator/tests/test_check_branch_landed.py \
-q -p no:cacheprovider -n 0
```

```bash
PYTHONDONTWRITEBYTECODE=1 IZANAGI_TASK_RUN_AUTO_RECORD=0 \
python3 tools/run_tests.py \
orchestrator/tests/test_check_branch_landed.py \
orchestrator/tests/test_check_branch_rescue.py \
orchestrator/tests/test_acceptance_schedule_order.py \
orchestrator/tests/test_update_acceptance_duration_ledger.py \
-q -p no:cacheprovider -n 0
```

対象は各ファイル全体です。consumer には次の node を含みます。

- `test_p02_real_checker_landed_and_loose_deadline_is_rc0`
- `test_p03_real_checker_not_landed_is_still_rc0`
- `test_real_checker_unlanded_spool_details`

障害は実行基盤に帰属し、テスト成否は未確認です。構文解析と `git diff --check` は成功しました。

## 波及の静的列挙

- `_find_exact_state`／`_proof_unit` の所有外ファイルからの直接呼出しはありません。
- `tools/check_branch_rescue.py` は CLI を子プロセスとして利用します。
- 既存 helper を再利用し、共有 fixture・`conftest.py` は変更していません。
- duration ledger と制約テストを検索しました。対象ファイルの node 数を直接 pin するテストは見つからず、関連する上記2つの制約ファイルを実走対象へ含めました。
- 最終差分は指定2ファイルのみ。runner が生成した一時成果物は除去済みです。

## 変異位置

すべて C 内です。引用は置換対象の逐語部分です。**変異実走は未実施**です。

| ID | 位置 | 置換前の逐語／適用箇所 |
|---|---|---|
| m01 | C:868 | `"--no-renames"` |
| m02 | C:868 | `"--ignore-submodules=none"` |
| m03 | C:846 | `name == p or name.startswith(p + b"/")` |
| m04 | C:847 | `_derive` の `return result`。各列を sort して返す変異を適用可能 |
| m05 | C:846 | `[:self.limit + 1]` |
| m06 | C:868 | `"--diff-merges=separate"` |
| m07 | C:867 | union command 内の `"--full-history"` |
| m08 | C:867 | `"-c", "log.showRoot=true",` |
| m09 | C:877 | `if len(entries) == bound and any(len(rows) < self.limit + 1 for rows in derived.values()):` |
| m10 | C:794、874、877 | `names = entries.setdefault(header.decode("ascii"), {})` と distinct 後の `len(entries)`。entry 数は parser で失われるため、単一置換位置には定まらず、段6で変異方法の確定が必要 |
| m11 | C:857 | `follow.stdout.strip() == b"true"` |
| m12 | C:858 | `sum(len(p.encode("utf-8")) + 1 for p in paths) > HISTORY_CANDIDATE_ARGV_BYTES_LIMIT` |
| m13 | C:791 | `name = first[1:]` |
| m14 | C:851 | `if not _entry_matches(required, self.tip_entry(path))` |
| m15 | C:893 | `if self._union_failure is not None:` に続く `raise self._union_failure`。この分岐を再走査へ置換 |
| m16 | C:771 | `"""Parse NUL-framed commit entries without decoding tree names."""` |
| m17 | C:857 | m11・m12から成る fallback 条件全体を `if True:` へ置換し、旧 per-path 供給を強制 |

m12 の検査名は指定どおり `argv_limit_zero`／`argv_limit_boundary` です。

## 未実装・未実走・懸念

- 指定実装とテスト追加は完了しましたが、動的検証は未完了です。
- 焦点走、consumer、制約テスト、変異 matrix、親の受入実験・全走は未確認です。
- m10 の具体的変異は親の段6で確定が必要です。
- 正常完走時の同一性と timeout 時の class 維持を区別し、時間の非退行は主張していません。

## 総括

指定2ファイルを変更し、既存の期待値と判定処理を維持しました。
静的検査は成功、pytest は基盤障害により未起動です。
状態は **実装済み・未実走** であり、closed ではありません。
docs 編集・git add・commit は行っていません。
