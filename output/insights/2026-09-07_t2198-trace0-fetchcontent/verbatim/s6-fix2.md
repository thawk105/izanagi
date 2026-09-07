## 足した負例

- `length-five-with-one-duplicate`: 5 要素・set サイズ 4 で loader の長さ検査だけを狙う。[test_paper_story_a2_certification.py:1839](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2198-fix2/orchestrator/tests/test_paper_story_a2_certification.py:1839)
- `test_trace0_rejects_empty_dependency_prefix_value`: dependency prefix の非空検査を狙う。[test_paper_story_a2_certification.py:4923](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2198-fix2/orchestrator/tests/test_paper_story_a2_certification.py:4923)
- `test_trace0_rejects_wrong_fetchcontent_prefix_with_valid_value`: prefix 一致検査だけを狙い、位置 slice 後の値は正規絶対 path のままにした。[test_paper_story_a2_certification.py:4940](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2198-fix2/orchestrator/tests/test_paper_story_a2_certification.py:4940)

## 単一理由性の実測

- m02: `not token[len(prefix):]` だけを一時除去。
  - `::test_trace0_rejects_empty_dependency_prefix_value`
  - FAILED、rc=1、`DID NOT RAISE CertificationError`
- m01: `token.startswith(prefix)` だけを一時除去。
  - `::test_trace0_rejects_wrong_fetchcontent_prefix_with_valid_value`
  - FAILED、rc=1、`DID NOT RAISE CertificationError`
- m08: `len(fetchcontent_path_argument_prefixes) != 4` だけを一時除去。
  - `::test_policy_loader_rejects_each_malformed_fetchcontent_prefix_list[length-five-with-one-duplicate]`
  - FAILED、rc=1、`DID NOT RAISE CertificationError`

除去しても赤にならなかった負例はありません。各条件は実測直後に復元しました。

## 実走結果

追加 3 node の通常状態:

- `::test_policy_loader_rejects_each_malformed_fetchcontent_prefix_list[length-five-with-one-duplicate]` — PASSED
- `::test_trace0_rejects_empty_dependency_prefix_value` — PASSED
- `::test_trace0_rejects_wrong_fetchcontent_prefix_with_valid_value` — PASSED
- 合計: 3 passed、rc=0

最終全自走 harness:

- `PYTHONPATH=. python3 orchestrator/tests/test_paper_story_a2_certification.py`
- 161 passed、rc=0
- `git diff --check` — rc=0

## production 差分がゼロであることの確認

最終 `git diff --name-only` の対象 file 一覧:

- `orchestrator/tests/test_paper_story_a2_certification.py`

除外確認結果は `NON_TEST_DIFF=none`。production コードへの一時変更はすべて復元済みです。

## 未了・停止した項目

なし。

## 総括

3 つの SURVIVED 変異をそれぞれ単独で殺す負例を追加しました。
通常実装では全ケースが拒否され、狙った条件だけを除去すると各対応 node が赤になります。
既存負例・期待値・golden・policy・production・docs は変更していません。
最終 harness は 161 passed、差分は指定されたテストファイル 1 本だけです。