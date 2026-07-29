段6裁定の全 accepted finding を実装し、指定検証はすべて緑です。commit・docs・正式 artifact は変更していません。

## 変更ファイル

fixer が追加修正したのは次の4ファイルです。

- [tools/ruleops.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py)
- [tools/run_tests.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/run_tests.py)
- [orchestrator/tests/test_ruleops.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py)
- [orchestrator/tests/test_run_tests_preflight.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_run_tests_preflight.py)

所有対象の `tools/check_docs.py` と `orchestrator/tests/test_check_docs.py` は、開始時からの段5差分を保持し、fixer からは編集していません。

## RA/RB 対応表

| Finding | 対応 |
|---|---|
| RA-1 | Git local configを上書き。署名、external diff、textconv、submodule再帰をconfigとcommand optionで無効化。偽署名commitとpoisoned `gpg.program`・diff/textconv helperの未起動testを追加 |
| RA-2 | 開始OIDを`ls-tree`、全`log`、`grep`、pickaxeへ固定。emit直前のHEAD再取得で`head-moved`拒否 |
| RA-3 | control pathspecをliteral化。path付きpickaxeを使い、現在のexact control blob導入eventだけを除外。旧non-control履歴を保持 |
| RA-4 | `ledger-candidate-alias`を追加。ledgerはclean tracked HEAD blobかつstrict artifactの場合だけcontrol扱い。dirty/untracked draftは非control |
| RA-5 / RB-7 | byte 0から始まる単一canonical typed markerへ固定。quote、fence、先頭ゴミ、重複、非canonical/duplicate JSONを拒否 |
| RA-6 / RB-6 / RB-9 | rationale/queryをstrip後nonempty・control-free化。replacement nodeをPython ASTで確認。receiptのtarget、review、guard、failed nodeをcandidateと相互照合 |
| RA-7 | inspect/check双方で上限超過を`evidence-overflow`として明示拒否 |
| RA-8 | ledgerを同一fdの`fstat`→bounded readで処理。receiptはtree sizeをblob read前に検査 |
| RA-9 | synthetic hit/historyをliteral expectedへ変更。poison helper、HEAD drift、control reuseなど独立negativeを追加 |
| RA-10 / RB-10 | argparseを含む全argument errorを`ruleops: cli-args: ...`、rc=2、traceback無しへ正規化 |
| RB-1 | `inspect --draft`へ完全な`mutation_receipt_draft`を追加。inspect→receipt commit→candidate commit→checkのE2Eを追加 |
| RB-2 | blob/grep/pickaxe memoization、batch blob取得、tokenごと1回のpath付きpickaxeへ集約。candidate上限8、query上限4 |
| RB-3 | M8 fixtureに曖昧basenameのliteral consumer/historyを追加 |
| RB-4 | M5をexact current controlと旧履歴で分離。M6はcycleを除けば両候補が個別にvalidであるpositive control付き |
| RB-5 | real checkoutでinventory非空、既知hit、非空candidate、committed evidence、runner preflightまで確認 |
| RB-8 | runner側のledger定数と`--ledger`指定を削除し、RuleOps CLI defaultへ一本化 |

## 受理・拒否境界

受理時の出力は従来どおり次の3 fieldだけです。

- `candidate_count`
- `human_approved: false`
- `structurally_valid: true`

削除安全、eligibility、approval、受理集合同値は主張しません。

主な新規拒否境界は、HEAD移動、ledger alias、dirty/untracked control特権、marker grammar違反、架空AST node、receipt不整合、空白・制御文字、上限超過、oversize evidenceです。

裁定どおり、index/staged-tree binding、`PYTEST_ADDOPTS`のD97 classifier、preflight refusalのtask-run記録は実装していません。

## 検証結果

- `python3 -m pytest -q orchestrator/tests/test_ruleops.py`
  - **64 passed in 56.30s**
- `python3 -m pytest -q orchestrator/tests/test_run_tests_preflight.py`
  - **83 passed in 0.55s**
- `python3 -m pytest -q orchestrator/tests/test_check_docs.py`
  - **125 passed in 12.74s**
- `python3 orchestrator/tests/test_plain_runner_coverage.py`
  - **3 passed**
- `python3 tools/check_codex_agents.py`
  - **OK**
- `python3 tools/check_docs.py`
  - **違反なし**
- `py_compile`、所有6ファイルの`git diff --check`
  - **緑**

real-checkoutの非空candidateをrunner経由のtimeout付きsubprocess `check`で測定し、**1.258秒**でした。60秒を十分下回ります。

## 親が更新するdocs項目

- typed insight markerのexact grammar:
  `<!-- ruleops-insight: {"authority":"none","default_effect":"no-state-change","schema_version":"ruleops-insight/v1"} -->`
  をbyte 0に一意に置くこと
- `inspect --draft`の新しい`mutation_receipt_draft`
- receiptの`review_state`と、draft=`pending`／check時=`reviewed`
- receipt受理条件: `candidate_excluded=true`、baseline/restored rc=0、各mutant=`KILLED`、guard/node集合のcandidate照合
- candidate最大8、semantic query最大4、evidence最大128
- rationale/queryのstrip・control-free規則
- clean tracked strict HEAD artifactだけがcontrolになること
- HEAD epoch固定と`head-moved`
- 新しい安定reason code群と`cli-args`
- runnerがCLI default ledgerへ委譲すること

## 所有監査と未解決事項

`git status --short`と所有6ファイルの全diffを監査しました。親所有のtracked docs/README差分ハッシュは開始時と同じ
`2ab3f716...cabc1b`で、指定された裁定・review artifactのハッシュも不変です。

一方、親所有の `s6-fix.log` は開始時のハッシュから変化していました。周辺runnerが管理する進行ログで、fixerから書き込んでいませんが、所有外変更として最終監査時点で検出したため、以後の編集を停止しました。

commitおよびcommit後provenance検査は、禁止契約に従い実施していません。Codex hookが発火したとの主張もしていません。

## 総括

Accepted RA-1〜RA-10／RB-1〜RB-10の修正範囲は実装・実走済みで、非空production相当preflightも1.258秒で緑です。残件は親によるdocs同期、明示deferされた3項目、ならびに親管理の進行ログ変更の確認です。