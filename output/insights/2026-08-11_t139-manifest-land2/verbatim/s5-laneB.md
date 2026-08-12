## 総括

実装は完了していますが、pytest は実行基盤の制約で未実走です。したがって本 lane は `closed` とは申告しません。commit / `git add` は実行していません。

変更前の受理・拒否挙動:

- 40/64 桁 lowercase hex の `commit` / `sha256` と canonical repo-relative `path` を受理。
- 非文字列、不正桁、大文字・非 hex、空 path、NUL、改行、絶対・非 canonical path などは拒否。
- ただし形状が正しい `str` subclass は受理・保持され、反射比較による digest 迂回が可能でした。
- 素の `str` の digest 不一致は従来どおり `BlobDigestMismatchError` でした。

実装内容:

- [blobref.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-impl-b/orchestrator/preregistration/blobref.py:55)
  - 従来検査を先に実施し、`str.__str__(value)` で subclass の `__str__` を迂回。
  - exact built-in `str` 化後に再検査し、frozen field へ格納。
  - `path` / `commit` / `sha256` の全 field に適用。
  - digest は文字列比較を廃止し、32-byte digest 同士で比較。
- [test_t139_blobref_digest_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-impl-b/orchestrator/tests/test_t139_blobref_digest_binding.py:1)
  - `sha256` subclass による不一致迂回。
  - `commit` subclass の exact `str` 化。
  - `path` subclass の正規化と非 canonical path の迂回拒否。
  - 素の `str` による正例。

### 検査結果

走らせた pytest nodeid: **0 件**。

次の範囲を `tools/run_tests.py` で試行しましたが、pytest 本体へ到達していません。

- `orchestrator/tests/test_t139_blobref_digest_binding.py`
- 同範囲の `--collect-only`

理由は、Pegasus user slice が約 12.05 GiB 使用中で local 安全枠を確保できず、dispatch も `qstat -Q preflight rc=1` / `EACCTAUTH Unknown user-id` で失敗したためです。実装済み・未実走です。

事前指定した期待赤集合は空集合です。観測した test の赤もありませんが、これは未実走のためであり、dispatch infrastructure failure は test finding とは数えていません。

静的検査:

- `py_compile`: 成功
- `git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 違反なし

### 波及可能性

全数検索した production 側は以下です。

- `orchestrator/preregistration/__init__.py`: `BlobRef` / `read_pinned_blob` の export。変更なし。
- `orchestrator/preregistration/erratum.py`: `compose_core` が core と erratum の各 `BlobRef` を消費。署名変更なし。
- 既存 `test_t139_preregistration_binding.py`: 全 fixture は素の `str` で、静的には従来受理のままです。編集していません。

`erratum.py` と既存共有 test は lane A が同時編集する所有面です。ファイル所有は交差しないため直接の textual conflict はありませんが、lane A の consumer は今後 exact `str` 化された field を受け取ります。また、`compose_core` の独立した `expected_composed_sha256` 比較は本 lane の `BlobRef` scope 外であり、変更していません。