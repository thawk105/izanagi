## 変更内容

所有対象の4ファイルだけを変更し、docs・Python helper・identity 定数には触れていません。commit / add / push も未実施です。

- [floor_campaign.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-b/tools/pegasus/floor_campaign.sh:29)
  - 最初の script mutation である `mkdir "$TMPDIR"`（97行）より前に preflight を追加。
  - receipt の `source_commit` を重複 key 拒否付きで抽出。
  - `git cat-file blob "$source_commit:orchestrator/campaign/certified_writer_preflight.py"` を `python3 -I -B - floor ...` の stdin へ接続。
  - hash literal は追加していません。
  - preflight 用 interpreter と、既存の attempt 作成後の operational interpreter 選定を分離し、既存 failure-marker 挙動を残しました。

- [t126_qualification.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-b/tools/pegasus/t126_qualification.sh:63)
  - receipt 公開待ちと preflight を、最初の `mkdir -p "$QUAL_ROOT/job-staging"`（128行）より前へ追加。
  - helper は receipt の `source_commit` にある blobから stdin 実行。
  - helper 非0時は trap 設置・job-staging 作成前にそのまま停止します。

- [test_pegasus_floor_tools.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-b/orchestrator/tests/test_pegasus_floor_tools.py:200)
  - commit Aのfixture helperと、commit Bへ進めた checkoutを作る実 wrapper harnessを追加。
  - M6/M7負例は出力root・`/scr`対象の前後snapshot、非0、stderr、mkdir/driver sentinel、failure marker不在を検査します。
  - 負例は418行、P-2のwrapper境界正例は443行、blob/no-hash検査は467行です。

- [test_t126_pegasus_tools.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-b/orchestrator/tests/test_t126_pegasus_tools.py:735)
  - 同等の実 wrapper harnessを追加。
  - 負例は1520行、正例は1544行、blob/no-hash検査は1567行です。
  - 既存のwrapper実行fixtureにも、`REQUIRED_CODE_IDENTITY_PATHS`へ追加しないcommit内stubを補いました。
  - 既存M11b fixtureのassertionは変えず、preflight通過に必要なsource commitだけ補完しました。

## 検査結果

次のnodeを `python3 tools/run_tests.py -q` で指定しました。

- `test_pegasus_floor_tools.py::test_floor_shell_syntax`
- `test_pegasus_floor_tools.py::test_floor_wrapper_preflight_rejection_is_nonmutating_and_starts_no_driver`
- `test_pegasus_floor_tools.py::test_floor_wrapper_accepting_source_commit_preflight_reaches_first_write`
- `test_pegasus_floor_tools.py::test_floor_wrapper_streams_helper_blob_without_hash_literal`
- `test_t126_pegasus_tools.py::test_shell_scripts_pass_bash_syntax`
- `test_t126_pegasus_tools.py::test_t126_wrapper_preflight_rejection_is_nonmutating_and_starts_no_driver`
- `test_t126_pegasus_tools.py::test_t126_wrapper_accepting_source_commit_preflight_reaches_first_write`
- `test_t126_pegasus_tools.py::test_t126_wrapper_streams_helper_blob_without_hash_literal`

結果は `qstat -Q preflight rc=1` による dispatch infrastructure failure、runner rc=16でした。pytest本体は起動していないため、全nodeとも未実走であり緑とは主張しません。`--collect-only` も同じrc=16でした。

静的検査は以下のとおりです。

- `bash -n tools/pegasus/floor_campaign.sh tools/pegasus/t126_qualification.sh` — rc=0
- 両test fileの `ast.parse` — rc=0
- `git diff --check` — rc=0
- `external/ccbench` 未初期化の警告は出ましたが、pytest未起動のためsubmodule由来のskip・赤は発生していません。

## 受理・拒否挙動の差分

変更前は、両wrapperともscratch/job-staging/attemptを作ってtrapを設置した後にreceipt・source identity・protocol/control・calibration・site検査へ到達していました。そのため後段で拒否されてもfailure markerやterminal resultが残り得ました。

変更後は次を最初のwrapper管理書込み前に拒否します。

- nonce、receipt、`source_commit` が不正
- source commitにhelper blobがない
- preflight interpreterがない
- helperが静的admissionをexit 3/4で拒否する

この場合、attempt/job-staging、failure marker、terminal result、driver起動はありません。診断はstderrのみです。

helperがexit 0なら既存後段へ進みます。後段のdefense-in-depth、interpreter failure marker、PBS directive、driver rc処理は変更していません。受理拡大はありません。commit A receiptとcommit B worktreeのdriftは、Aのhelper blobを使うため誤拒否しない設計です。

## 所有外への波及

- floor wrapper bytesが変わるため、今後のsubmit receiptに入る `job_script_sha256` は変わります。既発行receiptは記録済み`source_commit`の旧blobで検証されるため書き換えません。
- T126 wrapperは既存の`script_identity`対象なので、今後の`script_identity`、`series_identity`、submission receipt、job-result/collector chainが変わります。
- helperは`REQUIRED_CODE_IDENTITY_PATHS`へ追加していません。v1のexact key setは不変で、歴史seriesのkey-set互換性を壊しません。
- frozen output、admission registry、protocol/calibration bytesは変更していません。
- A側helperの実pathまたはCLIが段4契約から変わる場合、wrapperとの統合調整が必要です。

## 保護できる範囲

段4 §2 Cどおり、言える範囲は次です。

> PBS がjob bodyを開始した後、当該wrapperが明示的に管理するdurable outputおよびscratchを初めて変更する前に、submission/source identity・current registry・protocol/control・calibration bytes・compute-siteの静的read-only admissionを完了する。

言えない範囲は次です。

- qsub側のreceipt / ledger
- PBS spool / prologue / epilogue
- schedulerが作る `$TMPDIR`
- filesystem atime
- full hardware attestation probeのscratch
- submitterがjob開始前に作った成果物

したがって「write-zero」や「全書込みを契約で保護した」とは主張しません。

## 未完・A待ち

- `orchestrator/campaign/certified_writer_preflight.py` はこのworktreeに存在せず、実装子A待ちです。
- テストfixtureでは段4のCLI境界だけを表すcommit内stubを使用しています。正しいreceipt・protocol・calibration・compute siteを実helperが受理するdomain-level P-2は、A統合後に実走が必要です。
- focused pytest、関連file全走、meta-testはいずれもdispatch rc=16のため未実走です。

## 総括

B1〜B5のwrapper側実装と、M6/M7を最終rejectではなく書込み・driver起動の不在で観測するテストを追加しました。変更は所有4ファイルのみです。静的検査は通っていますが、A helper未統合かつpytest未実走のため、現状は「実装済み・未実走／A待ち」です。