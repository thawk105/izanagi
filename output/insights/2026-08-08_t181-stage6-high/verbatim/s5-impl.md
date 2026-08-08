実装済み・pytest 未実走です。変更は checker とテストの2ファイルのみで、docs 編集・commit はしていません。

### 実装内容

- [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dw-t181-impl/tools/check_docs.py:264)
  - S02=max、S03=max、S06-A=high、S06-C=high を節別 exact-list で pin。
  - 既存 S02/S03 finding の逐語は不変。
  - S06-A/C の time-invariant finding を追加。
  - S05-A、S06-B は pin 対象外。
- [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dw-t181-impl/tools/check_docs.py:3393)
  - 文書全体を先に可視化してから節抽出。
  - canonical literal の exact-one と `values == [expected]` を併用。
- [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dw-t181-impl/tools/check_docs.py:3658)
  - 必須 H2 inventory も可視 text から抽出。
- [orchestrator/tests/test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dw-t181-impl/orchestrator/tests/test_check_docs.py:4842)
  - S06 正例、B の literal 不在、A/C の誤値・欠落・複数値・alias・引用符・曖昧値を追加。
  - whole-section fence/comment の pin 直接検査と、`main()` 経由の exact finding 検査を追加。
  - comment/fence 内 decoy を無視する既存正例を4節へ拡張。

### 受理・拒否挙動

変更前は S02/S03 の値列だけを検査し、H2 全体を不可視化しても pin と inventory を通過しました。また alias の expected 値単独や `high/max` 等を expected 値として誤認できました。

変更後は可視な canonical literal が各節にちょうど1件ある場合のみ受理します。節内の comment/fence decoy は引き続き無視し、S06-B の literal 不在も受理します。不可視な orphan H2 も inventory 対象外となり、文書全体で可視性規則が統一されました。

事前指定した production finding 集合は次のとおりです。

- S06-A の値変異・曖昧値: `{S06-A pin finding}`
- S06-C=max: `{S06-C pin finding}`
- S06-A 全体の fence/comment 化: `{S06-A pin finding, H2 DW-S06-A が 0 件}`

テストでは substring ではなく `_finding_set(res)` の exact 一致を要求しています。

### 検査結果

成功した静的検査:

- `python3 tools/check_docs.py` → `check_docs: 違反なし`
- `python3 tools/check_codex_agents.py` → OK
- 変更2ファイルの AST parse
- `git diff --check`
- 曖昧値抽出 probe：`high/max`、`high.max`、`high:max`、`high"` をそれぞれ値全体として抽出

pytest は以下を `tools/run_tests.py` 経由で投入しましたが、いずれも runner rc=16 で未実走です。

- `orchestrator/tests/test_check_docs.py -k reasoning_effort`
- `orchestrator/tests/test_plain_runner_coverage.py`（meta-test）

local reservation ledger を sandbox から更新できず dispatch に移り、`qstat -Q preflight rc=1` で停止しました。テスト赤ではありませんが、緑とも報告しません。

### 静的な波及範囲

- production caller: `_check_command_docs_guard()`
- 共有 fixture: `_write_command_guard_docs()`、`_build_min_repo()`
- consumer tests: command guard positive controls、synthetic baseline、real-repo clean
- `REQUIRED_REFERENCE_SECTIONS` を使う全 reference inventory
- `tools/codex_reasoning_ab.py` の歴史 snapshot hash は変更ファイルを列挙していますが、凍結証拠なので更新していません
- `DEV_WAVE_AGGREGATE_BYTES` と `REFERENCE_LIMITS` は不変です

## 総括

- 4節の reasoning pin、whole-section 不可視化、曖昧値の3件を実装しました。
- docs と commit には触れず、変更は checker とそのテストだけです。
- `check_docs.py`、Codex agent checker、AST、diff 検査は成功しました。
- pytest と meta-test は runner infrastructure rc=16 のため未実走です。
- 親側で同じ焦点範囲と全受入を再走する必要があります。