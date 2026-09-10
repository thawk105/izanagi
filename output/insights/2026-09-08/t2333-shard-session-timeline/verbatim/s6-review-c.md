## 総括

静的レビューの結果、must-fix、nit ともにありません。実装は D1647、D1620、および段 4 裁定に適合しています。pytest は実行していません。

## must-fix

なし。

観測値だけを原因として certified 選択、受理 rc、report、receipt、台帳の値や参照を誤って変える経路は見つかりませんでした。

## nit

なし。

## 裁定との適合

1. 裁定 2

   [validate_report_evidence](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/tools/acceptance_shards.py:518) と [merge_reports](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/tools/acceptance_shards.py:603) に変更はなく、両者とも `report["session_timeline"]` を読みません。追加された `_observed_epoch` と `_observed_lock_intervals` は producer 側の観測値無害化にのみ使われ、受理判定には接続されていません。

2. positive control

   [test_session_timeline_contents_do_not_change_merge_verdict](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/orchestrator/tests/test_run_tests_shards.py:960) は `_merge` を呼び、そこから実物の `SH.merge_reports` に入ります。破損値も、配列、空 dict、NaN と不正 workers、必須 key 欠落という具体的な実体です。少なくとも配列と空 dict は規定された timeline 形を明確に破っています。

   このテストは恒真ではありません。例えば `validate_report_evidence` に timeline の非空検査を追加すれば、最初のケースで `report-invalid` となり赤になります。また `_REPORT_FIELDS` から field を外しても、未知 key として赤になります。

3. 既存の受理・拒否経路

   `_REPORT_FIELDS` への必須 key 追加以外に `merge_reports` の受理条件は変わっていません。

   `_controller_state` では次の既存条件がそのまま維持されています。

   - payload が空なら `worker-payloads-missing`
   - digest の型または一致が不正なら `worker-collection-mismatch`
   - records と selected を持つ authority が一つでなければ `worker-authority-count`

   新しい collection 時刻と lock interval の集約は、これら三条件を通過した後に行われます。3 要素から 5 要素への戻り値拡張は呼出側の unpack と同期しており、既存条件の発火順や集合を変えていません。

4. 観測例外と rc

   `_observed_epoch` は型、float 変換、有限性、正値を確認し、巨大整数、NaN、無限値、文字列、欠測を `None` に落とします。lock interval も不正な入力を空または除外済み list に落とします。

   try 外の `_worker_payload` に残る `state["records_digest"]`、`state["selected_digest"]`、gw0 の `records` と `selected` は変更前から存在した添字参照です。新規追加部分は `state.get(...)` と例外を出さない無害化 helper だけなので、観測欠測による新しい KeyError 経路はありません。

   conftest 側の時計取得も例外、型不正、非有限値、非正値を `None` に落とします。lock 取得失敗、解放失敗、内側 protocol 例外では記録処理まで到達しません。正常時だけ、解放後に有限な二時刻を記録します。

5. collection 終端

   acceptance plugin の `pytest_collection_finish` は `trylast=True`、conftest 側は `tryfirst=True` です。したがって同じ finish hook 内では conftest の prewarm 後に acceptance の時計が読まれます。

   pytest の collection 制御では `pytest_collection_modifyitems` の呼出し全体が完了してから `pytest_collection_finish` に進みます。pluggy wrapper の yield 後処理は modifyitems 呼出しが戻る前に完了するため、conftest の検査、suffix 除去、LPT 並べ替えより後の時刻になります。合成 plugin テストも wrapper の `modify-after`、finish の tryfirst、acceptance の trylast の順を具体的に確認しています。

6. 期待値と台帳

   `author.patch` の全削除行を確認しました。既存テストの assertion、期待 rc、期待 reason の削除または書換えはありません。削除は ledger count、conftest の lock context 呼出し、既存関数の戻り値拡張に伴う実装行だけです。

   台帳は追加 node 16 件がすべて `0.0` で登録され、`nodeid_count` と `duration_seconds_by_nodeid` の実要素数はいずれも 19557 です。閾値、schema、unit は変更されていません。

   `SCHEMA` は v1 のままで、receipt や D1620 の測定面にも変更はありません。

## 攻撃したが破れなかった点

- timeline を配列、空 dict、NaN、key 欠落にしても merge 判定が内容を読まないこと。
- timeline 必須 key 自体を消した場合だけ既存 exact-key gate が拒否すること。
- worker payload の timeline 欠測や異常が既存三つの `ShardError` 条件を変えないこと。
- xdist crash report の epoch 0、非有限値、巨大整数、属性欠測が worker bounds に混入しないこと。
- report 到着順を逆転しても worker ごとの最小 start と最大 stopになること。
- config 不在、shard spec 不在、`access is None` で従来の lock 経路を維持すること。
- lock 取得失敗、解放失敗、内側 protocol 例外で偽 interval を残さないこと。
- serial が config-local state、xdist が worker payload を使い、collection 時刻は最大値になること。
- conftest の modifyitems wrapper 後処理と collection finish の tryfirst 処理より後に時計を読むこと。
- 追加テストの node ID、台帳件数、実 map 長が一致すること。