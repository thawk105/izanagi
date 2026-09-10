## 総括

FIX-1〜5を、指定された9ファイル内で実装しました。  
同一 process の SH→EX は同じ fd を昇格し、終了時に SH へ戻す構造です。  
静的検査は通過しましたが、pytest は2走とも dispatch rc=16、child未起動でした。  
したがって実装済み・未実走であり、`closed` とは申告しません。

## 現行の受理・拒否挙動

受理: `current_commit_snapshot` の parent SH 中でも、同一 process/thread の `repository_candidate_commit` は同じ2 fdをEXへ昇格して通り、終了後はSHへ戻ります。正例は新設した `test_current_snapshot_reader_upgrades_for_same_process_candidate_fixture` です。

拒否: 別 process が旧 key をEX保持している場合、readerはcommon-dir resolverへ進まず、短いdeadlineで従来どおりfails-closedになります。

## 修正内容

- FIX-1: [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/conftest.py:1010)

  - resource/keyごとに1 process 1 fd、参照count、`read < write` のmode優越を実装。
  - 同一threadはSH→EX昇格、EX終了時はfdを閉じずSHへ降格。
  - 全holderが抜けた場合だけunlock/close。
  - 別thread間は従来のreader/writer互換性を維持。
  - 実fixtureを同時生存させる正例と、別process EX holderの負例を追加。

- FIX-2: G6を3本目のnested collection nodeとしてinventory、parent SH golden、変異対象へ追加。

- FIX-3: 旧key取得後にcommon-dirを解決し、新keyを取得する順序へ変更。別processの旧EX保持中にresolverが一度も呼ばれないことを実lockで記録します。

- FIX-4: [test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/test_real_repo_serialization.py:1206)

  - function fixtureもlive collectionへ含めました。
  - 4 fixture、全15 consumerの独立literal/live一致と、96 resource nodeとのdisjointを検査。
  - snapshot module SHとcandidate function EXの同時生存時に、有効modeがEX、終了後SHとなる契約を固定。

- FIX-5: fixture unwrapをpytest内部属性依存から`inspect.unwrap()`へ修正。実fixture本体のbuilder/read/yield/teardown記録は維持しています。

## 検査結果

`tools/run_tests.py`による焦点走を2回試行しました。

- 1走目: lock manager、snapshot C2、既存lock契約の3 node
- 2走目: 上記、9 mutation instance、collection/C3、shard、decorator、G6を含む16 node予定

両方とも`qstat -Q preflight rc=1`、dispatch rc=16、`child_started=false`でした。実行されたpytest nodeは0件です。

赤の内訳:

- 親の修正前実測: 4 failed / 1180 passed / 7 skipped。4件ともfixture unwrap不全。
- 本段のpytest実装赤: 未観測。
- dispatch infrastructure failure: 2走。
- submodule index-lock由来のsandbox偽赤: 0件。child未起動のため発生していません。

静的には`git diff --check`、編集した8 Pythonファイルの`py_compile`、許可9ファイル限定、禁止ファイル・`docs/`無変更、結合文字なしを確認しました。

## 受理・配置・期待値の変更

HEAD比でcollectionは通常test 2本とparametrize 9 instance、計11 node増えています。既存nodeのmarker変更は、resource登録6 nodeとcampaign fixture consumer 6 nodeの計12 nodeです。skipとselection縮小はありません。

fixture scopeはinvariant candidateがsession→module、predicate candidateがsession→function、repository scanがsession→moduleです。既存期待値ではG6のwork-unit契約と、旧・新2 key取得回数を更新済みで、今回C3をfunction fixtureとmode互換性まで強化しました。

## 静的な波及面

直接のlock callerはpytest node protocol、controller prewarm 2系統、および3 fixture moduleだけでした。共有fixtureのconsumerはinvariant candidate 5、predicate snapshot 3、predicate candidate 1、campaign scan 6です。

波及可能性は、96 resource nodeのlock取得、3 nested collection node、T810 3 node、上記15 fixture consumer、全acceptance shard割付です。長寿命fixtureの3 loadgroupは統合せず、別groupのまま維持しています。commit、add、stash、branch操作は行っていません。