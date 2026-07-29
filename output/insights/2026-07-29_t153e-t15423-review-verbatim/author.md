実装完了です。docs 編集・commit・所有外編集は行っていません。

変更:

- [check_ai_provenance.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423-author/tools/check_ai_provenance.py)
  - canonical `interpret-trailers --parse --no-divider`
  - repo 外 cwd、Git config/env/repo discovery 隔離、separator `:` 固定
  - raw/parsed CAB 件数検査
  - AI-Agent 欠落・形式・scope・`none` と CAB finding の併存
  - commit ancestry 単位の `git log -S` policy 適用
- [check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423-author/tools/check_docs.py)
  - 独立 `PROVENANCE_LIMITS` と 9,000-byte 上限
  - budget consumer へ合流、dispatch allowlist は非拡張
- 両テストへ指定境界を追加。9000/9001、divider、config/env、CRLF、重複、lineage、policy 削除後などを固定。

検査結果:

- 編集前 baseline: `137 passed`
- 指定 runner: `166 passed`
  - `test_check_ai_provenance.py`: 40 nodes
  - `test_check_docs.py`: 126 nodes
- bare runner:
  - provenance: `40 passed`
  - docs: `126 passed, 0 failed`
- plain-runner meta-test: `3 passed`
- 実履歴 provenance: `495 件、違反なし`
- `check_docs`: 違反なし
- `check_codex_agents`: OK
- `py_compile`、`git diff --check`: OK
- 赤: 0件。親 docs 未landを直接検査する node はなく、期待赤もありません。

静的波及:

- 所有外 caller は `tools/task_run_check.py`、`tools/dev_waves/checker.py`、`tools/dev_waves/daemon.py`。
- `validate_message()` の3要素戻り値を使う caller は所有内の main とテストだけです。
- `test_check_docs.py` の共有 `_build_min_repo`、`_pad_to_bytes`、列挙対象選択へ provenance registry を反映しました。
- `test_s8b_selector_output.py` は `check_docs` を import しますが、新 registry への直接依存はありません。
- 変更ファイルは指定された4ファイルのみです。

## 総括

plan v2 の単一受理集合を、CAB placement gate と provenance 文書予算の両面で実装しました。CAB parser は ambient alias・separator・Git env・repository config に左右されず、物理行の raw candidate 数と Git が最終 trailer block と認識した canonical CAB 数を比較します。履歴では各 commit ancestry の policy needle 変更を用いるため、pre-policy は非遡及、別 lineage と policy 削除後は適用継続となります。`AI-Agent: none` を含む早期 return でも CAB finding は失われません。文書予算は `PROVENANCE_LIMITS` として全 budget consumer に接続しつつ normative dispatch allowlist を広げていません。指定 runner 166件を含む全実走は赤0件で、docs・commit・所有外ファイルは変更していません。