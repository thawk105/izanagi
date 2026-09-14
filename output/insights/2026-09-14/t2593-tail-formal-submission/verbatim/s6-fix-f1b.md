## 所見1 — `--help`

- 直した内容：事前走査を撤去。位置別の期待表と理由コメントを追加し、rc=0／2の両側を検査します。新flag認識後の `--help` が意図的にrc=0となる専用ケースも追加しました。
- 赤を確かめた方法：未実走。対象は `test_submit_help_at_every_argument_position`（30ケース）と `test_submit_help_after_new_explore_flag_intentionally_returns_zero`（1ケース）。

## 所見2 — 正規化時の末尾改行

- 直した内容：番兵で末尾改行を保持し、`realpath` の出力終端だけを除去して文字集合を検査します。`--output-parent` は変更していません。
- 赤を確かめた方法：未実走。`test_submit_rejects_trailing_newline_explore_before_side_effects`（直接指定／alias-dotの2ケース）で、rc=2・qsubを含む全stub未呼出し・receipt不在を検査します。

## 所見3 — group ID

- 直した内容：成功投入の日時を起動前後の実測UTC窓と照合。同じ引数で出力親だけを変えて2回起動し、IDが異なる検査を追加しました。
- 赤を確かめた方法：未実走。既存成功テストへの追加検査と `test_submit_repeated_arguments_produce_distinct_group_ids`（5ケース）が対象です。固定値への変異検査も未実走です。

## 所有外への波及可能性

- caller：文書の投入コマンドと直接CLI呼出し。未知引数より後のhelpはrc=2に戻り、末尾改行の解決先は拒否されます。
- consumer：`b10_backoff_grid.sh` のexplore入力、`test_backoff_extended_sweep.py` の逐語pin、`test_hooks.py` の登録検査が関連します。所有外の共有fixture・consumer testは編集していません。
- 任意検索先の `pyproject.toml` は存在しませんでした。

## 総括

- 所有2ファイルを修正。変更差分も2ファイルのみで、指定consumer testは差分なしです。commit・stageはしていません。
- **実装済み・未実走**。pytest実走nodeidは0件。ランナーが `qstat -Q` 事前確認でrc=16となり、子プロセス未起動でした。Bash構文・Python AST・差分形式検査は成功しました。
- 裁定との実装上の相違はありません。赤／緑の確認は未達です。ランナーが自動生成した4ファイルは除去済みです。