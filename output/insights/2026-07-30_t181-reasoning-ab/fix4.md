## 総括

指定された2ファイルだけを修正しました。docs編集・commitは行っていません。

[codex_reasoning_ab.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:612) では、「全submodule初期化済み」という不変条件を置換しました。.gitmodulesと各repositoryのindexを再帰的に照合し、manifestへsubmoduleのsnapshot相対path、gitlink commit SHA、`initialized`／`uninitialized`を構造化して記録します。初期化済みの場合だけHEADとgitlinkの一致を確認してobject store閉包検査を実施します。未初期化はworktreeが不在または空で、`.git` markerと管理用object storeも存在しない場合に限り受理します。object storeの痕跡があるのに検査できない状態は未初期化へ格下げせず、fail-closedで拒否します。従来の無条件な`git submodule status`の`-`拒否は削除しました。

manifest全体とは別にsubmodule状態集合のSHA-256を生成し、scheduleの全slotへ拘束しました。POS/NEG間でpath、gitlink SHA、初期化状態のいずれかが異なるscheduleは拒否されます。supervisor開始時とreplay時にもsnapshot oracleとの一致を再検証するため、snapshot構築後にgitlinkが変わった場合や、未初期化submoduleが黙って初期化された場合も検出されます。

[test_codex_reasoning_ab.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:858) には、初期化済み親submoduleの中に未初期化の入れ子submoduleを持つ合成snapshotの正例、未初期化submoduleのgitlink SHA変更拒否、初期化済みsubmoduleへのanswer blob注入拒否、POS/NEGの初期化状態不一致拒否を追加しました。既存のgrafts検査、root object storeへのanswer commit再注入、および指定された500-byte境界、st_mode、untracked、prompt replacement、pair timing、post-treatment denominator、attempt=4、pair片側retry、`ls-files` option併用禁止の負例は維持しています。

許可された `python3 -m py_compile tools/codex_reasoning_ab.py orchestrator/tests/test_codex_reasoning_ab.py` は成功しました。一方、ユーザー指示どおりpytest、`tools/run_tests.py`、snapshot build、fixture実走、submodule update、外部cloneは一切実行していません。したがってテスト緑やbuild-snapshot成功は主張しません。

波及点として、schedule schemaに`submodule_manifest_sha256`が必須になり、oracleの`submodules`は生のstatus文字列から構造化rowへ変わりました。親側では新しいPOS/NEG oracleからscheduleを再生成する必要があり、旧形式の凍結artifactはreplay時に意図どおり拒否されます。計算ノードではPOS/NEG build-snapshot、追加4負例を含む対象pytest、および既存受入集合の全走で実測してください。