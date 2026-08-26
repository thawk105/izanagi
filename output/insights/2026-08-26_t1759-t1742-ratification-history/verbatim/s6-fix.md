## 所見ごとの対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| batch 成功応答の query 束縛 | closed | `%(rest)` に commit を付与し、期待 commit と完全照合 |
| blob byte 数と batch size の照合 | closed | OID ごとの size を保持し、取得後の `len(raw)` と照合 |
| `_load_rows` の線形重複検査 | closed | 返却順は list のまま、重複判定を set 化 |
| 台帳親1 + 非台帳親1の拒否例 | closed | 行置換 merge の拒否テストを追加 |
| octopus の拒否例 | closed | 第3親の行を落とす merge の拒否テストを追加 |
| 不正中間遷移テストが浅い | closed | 不正遷移後に正常 commit を3段置く履歴へ変更 |
| graft と replace ref の同居 | closed | 独立した2テストへ分割 |
| batch 異常系の負例 | closed | query 不一致と size 不一致を Git 偽装なしで注入 |

`partial`、`regressed` はありません。

## 変更したファイル

- [enforcement_source_ratification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:108)
  - `_load_rows` の重複検査を set 化。
  - `_parse_batch_object()` を抽出し、成功応答の第4 field を期待 commit に束縛。
  - format 付き `--batch-check` と、commit を後置した query を使用。
  - ledger blob の size を保持し、実取得 byte 数と照合。
  - subprocess 起動口は `_git()` の1か所のまま。
- [test_enforcement_source_ratification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/tests/test_enforcement_source_ratification.py:232)
  - 採用された拒否例、batch 境界テスト、履歴深化、graft/replace 分割を反映。

## 足した・変えたテスト

| nodeid | 検出する誤実装 |
|---|---|
| `::test_batch_success_response_is_bound_to_requested_commit` | 成功応答を query commit に束縛しない実装 |
| `::test_blob_bytes_must_match_batch_checked_size` | batch size を捨てる、または blob 取得後に照合しない実装 |
| `::test_merge_with_bearing_and_nonbearing_parents_cannot_replace_rows` | 非台帳親を含む merge の検査を丸ごと省略する実装 |
| `::test_octopus_merge_omitting_third_parent_row_is_rejected` | octopus の第3親以降を無視する実装 |
| `::test_invalid_middle_history_transition_is_rejected` | HEAD 近傍だけを検査し、古い不正遷移を見ない実装 |
| `::test_empty_graft_file_is_accepted` | 空 graft を過剰拒否する実装 |
| `::test_unrelated_replace_ref_is_accepted` | 無関係な replace ref の存在だけで拒否する実装 |

旧 `::test_empty_graft_and_unrelated_replace_ref_are_accepted` は、上記2 nodeへ分割しました。

batch 異常系は Git を偽装せずに注入できています。query 不一致は純粋な応答 parser に直接注入し、size 不一致は実 Git に保存した blob を取得したうえで、不整合な batch size を `_rows_by_blob_oid()` に渡します。`_git` や `_require_git` の monkeypatch は使用していません。

## 受理・拒否挙動の不変性

段4の評価順、受理・拒否規則、既存4メッセージは変更していません。正常な Git 応答に対する既存履歴の判定も不変です。

意図的に変わるのは、成功応答の commit 不一致と blob size 不一致を新たに fail-closed で拒否する境界だけです。重複 digest の拒否内容とメッセージも不変です。

既存テストの期待値は変更していません。変更した既存テストは、裁定で許可された履歴深化と graft/replace 分割だけです。

## 未了・注意点

- pytest は実走していません。実装済み・未実走です。
- AST 構文解析と静的 pin 確認は完了しています。
- production の `subprocess.run` は1か所です。
- tree mode は `100644` / `100755` のままです。
- 棄却された全世代保持・process 数の再設計は実装していません。
- docs、その他のファイル、Git index、commit には触れていません。

## 総括

採用8件はすべて closed です。指定された2ファイルだけを変更し、段4の履歴規則と既存の正常系判定を維持しました。テスト実測は親作業に残しています。