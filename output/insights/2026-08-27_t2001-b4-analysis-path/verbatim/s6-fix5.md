## 前提の確認

指定された3文書を全文確認し、R1〜R9、fix4、段4裁定を維持しました。Web検索、docs編集、commitは行っていません。

## 対応

`partial`

- caller census を正当な2件へ更新しました。
- 生産経路と検証 probe の役割をコメントと docstring で区別しました。
- probe が分析結果を返さず `None` を返すことをテストへ追加しました。
- 実走は rc=16 で開始されなかったため、`closed` とはしていません。

## 変更したもの

[test_p3_b4_analysis_path.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_path.py:356) のみ変更しました。

- census の期待値を以下の exact 2件へ更新
  - `p3_b4_analysis_path.py::evaluate_b4_artifacts`
  - `p3_b4_analysis_prereg_consumer.py::_assert_rank_and_threshold_behavior`
- 前者が唯一の artifact 生産経路、後者が結果を外へ出さない検証 probe であることを明記
- `_assert_rank_and_threshold_behavior() is None` の挙動検査を追加

consumer 本体、他の8ファイル、docs、`evaluate_analysis()` は変更していません。self-runner も維持しています。

## census の exact 性

census の実測リストと2要素の期待リストを `==` で完全一致比較しています。したがって、走査対象内に静的に認識される3件目の caller を追加すると、実測側に余分な tuple が入り、この node は赤になります。

件数の下限比較や module 名の前方一致にはしていません。R5どおり、動的 lookup や外部 Python からの直呼びまで不可能にする検査ではありません。

## 実走結果

次の2 nodeidを runner 経由で要求しました。

- `test_p3_b4_analysis_path.py::test_public_evaluate_analysis_production_caller_inventory_is_pinned_not_closed`
- `test_p3_b4_analysis_path.py::test_rank_and_threshold_verification_probe_exports_no_analysis_result`

結果は `qstat -Q preflight rc=1` による dispatch infrastructure failure、runner rc=16、`child_started=false` でした。テストは1件も実行されておらず、緑とは報告しません。

その後の静的AST検査では以下を確認しました。

- 両ファイルが構文解析可能
- census の期待集合が exact 2件
- probe の戻り値注釈が `None`
- probe 自身に値を返す return 経路がない

## 未了と限界

親による対象2 nodeidおよび5ファイル一括の再実走が必要です。親が確認済みの150件についても、今回の環境では回帰の有無を再確認できていません。

## 総括

要求された census 修正と非返却性の固定は実装済みです。静的検査は通過しましたが、rc=16で実走できなかったため最終状態は `partial` です。