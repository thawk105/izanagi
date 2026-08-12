## 総括

指定された補助関数の欠陥 8 件を修正しました。production の拒否実装は正しく、変更していません。編集対象は次の 2 ファイルだけです。

- [test_t139_approval_payload.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-fix1/orchestrator/tests/test_t139_approval_payload.py:74)
- [test_t139_preregistration_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-fix1/orchestrator/tests/test_t139_preregistration_binding.py:338)

A 群は `_mutate_once` を D282 の対象 fence 内へ限定し、その中で exact 1 件を検査して置換するよう修正しました。見出し・fence 自体の負例は、文書全体で一意性を検査する別 helper に分離しています。

B 群は最初の YAML fence ではなく、`operations:` を含む YAML fence を exact 1 件で特定し、切り出しと書き戻しで同じ境界を使うよう修正しました。

### 各負例が現在も拒否する対象

- `test_approved_blob_role_count_not_six_is_rejected` — `approved_blobs` が exact 6 role でない payload。
- `test_triplet_sha256_must_be_64_lowercase_hex` — SHA-256 が64文字の lowercase hex でない三つ組。
- `test_triplet_commit_must_be_40_lowercase_hex` — commit が40文字の lowercase hex でない三つ組。
- `test_duplicate_approved_blob_role_is_rejected` — 承認 blob role の重複。
- `test_unknown_approved_blob_role_is_rejected` — 承認集合にない未知 role。
- `test_s7_erratum_rejects_one_operation` — S7 erratum の operation 数が1件。
- `test_s7_erratum_rejects_three_operations` — S7 erratum の operation 数が3件。
- `test_s7_erratum_rejects_swapped_locators` — operation 間で locator を交換し、対象行と digest の束縛が崩れた文書。

### 実走結果

`tools/run_tests.py` は targeted、3-file 全走とも dispatch 基盤の `qstat -Q` preflight で `rc=16` でした。契約に従って素の pytest を実行しています。

- 上記8 nodeid: `8 passed in 0.73s`
- 次の3ファイル全範囲: `78 passed in 3.06s`
  - `test_t139_approval_payload.py`
  - `test_t139_preregistration_binding.py`
  - `test_t139_blobref_digest_binding.py`
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- `git diff --check`: OK

実走範囲に残る赤はありません。リポジトリ全体の suite は未実走です。

### 波及可能性

- `_mutate_once` の caller は同じ approval payload テスト内だけです。payload 内負例は D282 fence に限定され、見出し・fence 構造負例は文書全体用 helper に移りました。
- S7 YAML helper の caller は指定された3負例だけです。対象 operations fence が欠落・重複した場合は assert で停止します。
- 共有 fixture `fixed_decisions_bytes`、承認済み erratum、production caller は未変更です。
- production、`docs/`、`output/` は変更していません。`git add`、commit も実行していません。