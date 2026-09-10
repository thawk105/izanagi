実装は完了しました。指定 3 ファイルのみ変更し、docs 編集・commit は行っていません。

### 変更内容

- [git_state.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:90)
  - `commit-diff` から `-m` を削除。
  - parent 列取得と `parent → merge commit` 用 `tree-diff` を argv 表へ追加。
  - cutoff 指定時、cutoff の祖先である parent がちょうど 1 個なら、その parent との差分だけを検査。
  - trusted parent が 0 個・複数、または cutoff 未指定なら全 parent 差分を検査。
  - root／single-parent は従来の `--root` commit 全体検査を維持。
  - parent 出力の空・複数行・不正 SHA・非 ASCII、Git rc≠0、diff path の非 UTF-8を fail-closed 化。
- [dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1788)
  - declared-fold／no-fold の両検査へ `tested_main` を cutoff として伝播。
- [test_dev_waves_git_state.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:422)
  - 正規 main-fold merge 正例。
  - trusted main 上の fragment 削除、FOLDED resolution 改変、trusted parent なし、複数 trusted parent octopus の負例。
  - cutoff 未指定時の全 parent 走査、argv、異常 Git 出力の契約テスト。
  - `test_n31_landed_interval_cannot_hide_an_earlier_fold` と既存期待値は変更していません。

### 受理集合

修正前は non-merge と merge の全 parent 差分を走査し、正規 main fold の未変更取り込みも拒否していました。修正後に新たに受理するのは、cutoff 指定時、trusted parent が一意であり、その parent→merge 差分に既存の二署名がない場合だけです。

cutoff 未指定、trusted parent 0 個／複数、non-merge、既存の fragment `D`／rename source、`M FOLDED.md` は従来どおり拒否します。

### 検査結果

成功した静的検査:

- `python3 -m py_compile` — 変更した Python 3 ファイル
- `git diff --check`
- `python3 tools/check_codex_agents.py` — rc=0
- `python3 tools/check_docs.py` — rc=0

pytest は実走できておらず、緑を主張しません。以下を計算ノード dispatch しようとしましたが、すべてテスト開始前に infrastructure failure となりました。

- 修正前: `test_landed_interval_allows_main_fold_merge_from_trusted_cutoff`
- 修正後: `test_dev_waves_git_state.py` 全体
- 修正後: 同ファイル全体＋meta-test `test_plain_runner_coverage.py`

原因は `qstat -Q` の `NQSconnect: [API ESYSCAL] Can't create socket. (errno: 1)` です。したがって要求された「新正例の修正前赤」のnodeid実走確認は未完です。既存実 merge `ee28642...` では旧 `-m` 相当の wave-parent 差分から `M docs/spool/FOLDED.md` が出ることまでは Git object で実測しました。

### 所有外への波及

- `checker.py` と `daemon.py` は cutoff を渡していません。schema v2 経路は全 parent 走査を維持し、正規 main-fold mergeを引き続き拒否します。schema v1 の helper 迂回も不変です。
- 実 merge `ee28642...` の parent 差分で `M FOLDED.md` を実測したため、両 consumer は `landed-fold-owned-path`／recovery 不一致へ進みます。
- `test_dev_wave_land.py` の直接 helper 呼び出しは cutoff 未指定のままですが、対象 fixture は non-merge なので受理集合は不変です。
- parent 数取得により landed commit ごとに Git subprocess が増え、共有 30 秒 deadline 超過時は拒否へ倒れます。
- submodule index-lock 由来の偽赤は発生していません。

## 総括

- trusted main cutoff の外側で加えた変更だけを merge 署名判定へ掛ける v2 を実装した。
- cutoff 未指定、trusted parent 0／複数、octopus ambiguity は全 parent 走査を維持した。
- 既存二署名、path 集合、`test_n31`、既存テスト期待値は変更していない。
- 変更は指定 3 ファイルのみで、docs・commit はない。
- py_compile、diff check、Codex agent check、docs check は成功した。
- pytest と修正前赤のnodeid実走は PBS 接続失敗により未確認である。