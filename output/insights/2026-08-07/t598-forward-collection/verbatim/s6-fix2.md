所見 1 件は **partial（実装済み・未実走）** です。

- `_validated_out()` を `.git` file、または `HEAD` が存在する `.git` directory の場合だけ repository と判定するよう修正しました。[collect_wave_usage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:150)
- 合成 path で `.git` file／`HEAD` 付き directory の拒否、空 directory の受理を固定しました。[test_collect_wave_usage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:426)
- 第1巡のままでは赤くなるテストは `test_output_below_any_git_marker_is_rejected[directory]` です。拒否の assert は変えず、fixture を `HEAD` 付き directory に具体化しました。
- site・status・collector・subprocess・呼出しカウンタには触れていません。docs 編集、add、commit もしていません。

## 総括

- (a) 対応: repository 判定を指定条件へ限定し、3形の合成テストを実装。
- (b) 検査: 2ファイルの AST parse は成功。焦点 nodeid は `tools/run_tests.py` で2回、collect-onlyも1回試しましたが、予約台帳をsandbox内から更新できず、続く `qstat -Q` preflightも失敗してすべて rc=16。テスト本体は未実走です。
- (c) 残した穴: 実走による緑確認のみ未完了です。親環境で上記3 nodeidの再走が必要です。