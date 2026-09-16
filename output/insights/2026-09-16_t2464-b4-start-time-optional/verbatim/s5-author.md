## 総括

**実装済み・未実走**です。指定の 2 ファイルだけを変更しました。commit・index・HEAD の操作はしていません。

- [受理側](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2464-impl/orchestrator/campaign/p3_b4_admission_record.py:667)：対象 label に限り、指定の `re.fullmatch` と owner の 3 条件を満たす場合に追加受理します。
- [テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2464-impl/orchestrator/tests/test_p3_b4_admission_record.py:483)：正例、指定の負例、label 限定の負例を追加しました。拒否の期待値はすべて `_SECTION5_ERROR` と exact 一致です。

「対象外 9 label」と「expectation 行の未記入テストは禁止」は衝突するため、**段 4 裁定の禁止を優先し、他行の未記入テストは expectation 行を除く 8 label** としました。

## 変更前の挙動

コード読解と親の probe によれば、変更前は全 10 欄へ一律に sentinel 検査を適用し、今回の正例も拒否します。既存 fixture の非 sentinel 値は受理され、説明文・制御文字の意味検証は行いません。

実文書には対象行以外にも **6 欄**の未記入があり、本変更後も受理されません。

## 検査

実行を試みた範囲は次の単一ファイルです。

```bash
PYTHONPATH=. python3 tools/run_tests.py orchestrator/tests/test_p3_b4_admission_record.py -rf -v
```

dispatch の `qstat -Q` preflight が失敗し、rc=16・`child_started=false` で終了しました。**実走した nodeid はありません。** 変異検査も未実走です。

静的確認では、構文解析と `git diff --check` が成功しました。既存テスト・fixture は追加部分を除いて bytes 一致を確認しており、**既存 test 関数の削除・改名・期待値変更はありません**。受理側も指定の走査部分以外は bytes を保持しています。

## 追加した test 関数名

変更した既存 test 関数はありません。追加は以下の 11 個です。

```text
test_section5_accepts_unrecorded_start_time_with_named_owner
test_section5_rejects_whole_unrecorded_owner_start_cell
test_section5_rejects_unrecorded_owner_with_unrecorded_start
test_section5_rejects_whitespace_owner_with_unrecorded_start
test_section5_rejects_reserved_owner_with_unrecorded_start
test_section5_rejects_other_start_sentinels
test_section5_rejects_unrecorded_start_suffix
test_section5_rejects_reordered_unrecorded_start_fields
test_section5_rejects_extra_owner_start_field
test_section5_rejects_optional_start_syntax_in_other_label
test_section5_rejects_unrecorded_other_rows_with_optional_start
```

## 所有外への波及可能性（静的確認）

- **caller**：`verify_b4_admission_record` を通じ、`p3_b4_closed_critic.py` と `p3_b4_launcher.py` の受理経路へ波及します。
- **projection closure**：closed critic と raw record producer が変更ファイルの bytes を入力に含めるため、closure hash は変わります。
- **共有 fixture**：`test_p3_b4_closed_critic.py` の補助を launcher・raw producer・3 種の S4 loop テストが共有し、raw producer の補助を material report・producer auth experiment が参照しています。
- **consumer test**：closed critic、launcher、raw record producer、material report、producer auth experiment、S4 loop 各種、proposal binding が間接影響候補です。段 4 指定の analysis prereg consumer・analysis path・prerun issuer・floor artifact issuer も後続確認対象ですが、今回は未実走です。
- **別経路**：material report → floor resolver は admission 検査を通りません。prerun issuer の publication root 読取も別経路で、本変更では変更していません。