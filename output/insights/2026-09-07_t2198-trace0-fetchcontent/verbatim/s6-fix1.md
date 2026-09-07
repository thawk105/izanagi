## 所見対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| FIX-1 | closed | [paper_story_a2_certification.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2198-fix1/orchestrator/campaign/paper_story_a2_certification.py:2177)、[test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2198-fix1/orchestrator/tests/test_paper_story_a2_certification.py:4961) |
| FIX-2 | closed | [submitter](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2198-fix1/tools/pegasus/submit_paper_story_a2_certification.sh:192)、[test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2198-fix1/orchestrator/tests/test_paper_story_a2_job_contract.py:855) |
| FIX-3 | closed | [minimum guard](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2198-fix1/orchestrator/campaign/paper_story_a2_certification.py:2169)、[test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2198-fix1/orchestrator/tests/test_paper_story_a2_certification.py:5010) |
| FIX-4 | closed | [import block](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2198-fix1/orchestrator/campaign/paper_story_a2_certification.py:20)。`tempfile` の残存参照なし |

## 実装した内容

- `paper_story_a2_certification.py`
  - FetchContent 4 値へ `_lexical_absolute_path` と NUL 拒否を適用。
  - 到達不能な path-segment 下限検査を削除。
  - 未使用 `tempfile` import を削除。
- `submit_paper_story_a2_certification.sh`
  - `realpath -e` 後に既存と同じ安全値 loop を再実行。
- `test_paper_story_a2_certification.py`
  - NUL、`/../`、相対 path を独立 parameter で検査。
  - 実 `buildcache._v2_commands` の canonical argv 正例を追加。
  - 短縮 argv の期待を残存 minimum guard の例外へ一意化。
- `test_paper_story_a2_job_contract.py`
  - symlink 祖先を経て canonical path に comma が現れる負例を追加。

## 実走結果

- `test_paper_story_a2_certification.py`: rc=0、158 passed。
  - `::test_trace0_fetchcontent_path_values_match_producer_domain[nul]`
  - `::test_trace0_fetchcontent_path_values_match_producer_domain[lexically-noncanonical]`
  - `::test_trace0_fetchcontent_path_values_match_producer_domain[relative]`
  - `::test_trace0_accepts_canonical_argv_from_v2_producer`
  - `::test_trace0_configure_argv_rejects_short_path_segment`
- `test_paper_story_a2_job_contract.py`: rc=0、57 passed。
  - `::test_submitter_rejects_unsafe_path_after_canonicalization`
- `test_hooks.py`: rc=0、474 passed、1 skipped。
- `git diff --check`、`bash -n`、対象 Python の `py_compile`: rc=0。

## 受理・拒否挙動の変化

- NUL 入りおよび lexically noncanonical な FetchContent path が新たに拒否される。
- 相対 path、空値、prefix 違い、順序違い、余分 token は引き続き拒否される。
- `realpath -e` 後に comma、`=`、改行を含む submitter path が拒否される。
- 実 producer が生成する canonical argv は引き続き受理される。
- 冗長 guard の削除による受理集合の変化はなく、緩和はない。

## 波及の静的列挙

- `_exact_trace0_configure_argv` の直接 consumer は `validate_trace0_evidence`。A-2/A-6 が同じ検査を共有する。
- `_lexical_absolute_path` 自体は変更しておらず、CCBench source root など既存 caller の意味は不変。
- submitter の canonical 値は qsub `-v`、inline Python、submission receipt が共有する。
- 共有 fixture `_positive_results`、`_raw_cell`、`_run_submitter_harness` を通した全 harness が緑。
- hook/admission registry consumer も既存 harness で確認済み。

## 未了・停止した項目

なし。policy、golden、docs、README は無変更。commit、push、branch 作成も行っていない。

## 総括

FIX-1〜FIX-4 はすべて closed。
受理集合は producer が生成可能な path 側へ狭まり、submitter の canonicalize 後 mapping 破損も遮断した。
短縮 argv は残る単一 guardから `CertificationError` になる。
関連 harness は合計 689 passed、1 skipped、すべて rc=0。