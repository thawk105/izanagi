## 総括

should-fix「構築後の subclass 再注入」を実装・検査済みです。

- [`read_pinned_blob`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-fix2f/orchestrator/preregistration/blobref.py:102) の入口で `path` / `commit` / `sha256` が exact built-in `str` か再確認。
- 3 field をローカルへ退避後、`BlobRef` を再構築して形状も再検査。
- subclass 再注入は `InvalidBlobRefError` で fail-closed。
- 素の `str` で構築した正常系は従来どおり通過。
- 既存期待値、fixture hash、所有外ファイルは変更していません。

### 走らせた nodeid・範囲

[`test_t139_blobref_digest_binding.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-fix2f/orchestrator/tests/test_t139_blobref_digest_binding.py:56) 全 7 node: **7 passed**

- `test_sha256_subclass_cannot_bypass_digest_mismatch`
- `test_commit_subclass_is_stored_as_exact_builtin_str`
- `test_path_subclass_is_normalized_and_cannot_hide_noncanonical_path`
- `test_post_init_sha256_subclass_reinjection_is_rejected`
- `test_post_init_commit_subclass_reinjection_is_rejected`
- `test_post_init_path_subclass_reinjection_is_rejected`
- `test_plain_str_positive_reference_remains_accepted`

consumer 回帰範囲:

- `orchestrator/tests/test_t139_preregistration_binding.py` 全 node
- `orchestrator/tests/test_t139_approval_payload.py` 全 node
- 合計 **74 passed**

追加検査:

- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- `git diff --check`: OK

`tools/run_tests.py` は双方とも `qstat -Q preflight rc=1` で `rc=16` となったため、指示どおり素の pytest へフォールバックしました。実走範囲に残る赤はありません。全リポジトリ test suite は未実施です。

### 入口再検査を消すと赤くなる nodeid

- `test_post_init_sha256_subclass_reinjection_is_rejected`
- `test_post_init_commit_subclass_reinjection_is_rejected`
- `test_post_init_path_subclass_reinjection_is_rejected`

### caller 全数検索と波及可能性

`rg -n --glob '*.py' '\bread_pinned_blob\b' .` で全数検索しました。

- `approval_payload.py`: `load_approval_payload` が固定 D282 ref を読む。
- `erratum.py`: `compose_core` が core ref と各 erratum ref を読む。
- `__init__.py`: public re-export のみ。
- 直接・mock consumer test は上記 3 test file。

波及は、pickle 復元や `object.__setattr__` で破壊された ref が Git 実行前に `InvalidBlobRefError` となる点です。通常の plain-`str` caller、共有 fixture、既存 consumer test への破壊的影響は確認されませんでした。`erratum.py` と `approval_payload.py` は変更していません。

変更は指定された 2 file のみで、`git add` / `git commit` は実行していません。