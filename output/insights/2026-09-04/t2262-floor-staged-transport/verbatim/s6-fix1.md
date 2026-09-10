## 所見対応表

| must-fix | 状態 | 対応 |
|---|---|---|
| MU6 の実効 dataflow | partial（実装済み・pytest 未実走） | classifier 前の `fetchcontent_base_dir` 再束縛を AST で拒否する assertion を追加。既定 staging と空 seam basis の確認は維持。 |
| 起動点台帳 | partial（実装済み・pytest 未実走） | 現物を AST で再確認し、4705 / 8625 へ計 4 箇所を更新。entry の追加・削除なし。 |

## must-fix 1 の受理・拒否の含意

検証済み binding の payload が既定 staging され、raw `fetchcontent_base_dir=None` のまま classifier に入り seam basis が空になる正例を通します。  
導出した staging base を同名の `fetchcontent_base_dir` へ再代入してから classifier に渡す回帰は、classifier 前の `Store` 検出により拒否します。

## 実走した検査

- 対象 nodeid 2 件を通常実行および `--force-dispatch` で試行: いずれも rc=16、`child_started=false`。pytest は未実走です。
  - `orchestrator/tests/test_s8b_floor_campaign.py::test_default_staging_and_claim_seam_basis_keep_raw_argument_separate`
  - `orchestrator/tests/test_ccbench_spawn_sites.py::test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink`
- MU6 in-memory 変異 probe: rc=0。現行 source は再束縛なし、classifier 前へ同名再代入した変異は検出されました。
- 変更 2 ファイルの AST parse: rc=0。
- `git diff --check`: rc=0。

## 変更した既存期待値

起動点の exact 行番号だけを、指定どおり更新しました。

- `4543` → `4705`: 2 箇所
- `8457` → `8625`: 2 箇所

機能上の期待値、entry 集合、真偽、skip は変更していません。

## 波及可能性

変更はテスト 2 ファイルだけです。production code・受理集合・18 名集合・refreeze 判定式には変更ありません。将来 campaign source の行が動けば、起動点台帳は再更新が必要です。

## 停止した項目

pytest 実走は Pegasus の `qstat -Q` preflight が rc=1 となり停止しました。runner が生成した dispatch 一時成果物は削除し、作業ツリーには指定された 2 ファイルの変更だけを残しています。

## 総括

must-fix 2 件のテスト側修正を実装しました。  
親の実測値 4705 / 8625 は現物の AST と一致しました。  
MU6 の同名再代入回帰は in-memory probe で拒否を確認しました。  
pytest は infrastructure failure のため未実走です。  
変更は未 stage・未 commitです。