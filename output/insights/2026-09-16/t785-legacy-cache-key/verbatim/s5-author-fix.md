## 実装した内容 (所有 path ごとの差分要約)

- `orchestrator/campaign/buildcache.py`: `cache_key` の省略条件を `("gcc-13", "g++-13")` に固定し、該当docstringを更新。
- `orchestrator/tests/test_campaign.py`: 指定位置へ回帰テスト1本を追加。裁定§6の(a)(b)(c)を検査。

## 修正前後の受理・拒否挙動

修正前は、変更後の `DEFAULT_*` と一致する要求が歴史キーへ衝突します。修正後は新toolchainを分離し、歴史的組のキーを維持します。

現行既定では比較条件が等価なので、全入力のキーは変わりません。引数既定・admission検査・既存期待値は変更していません。

## 実行した確認と結果

`python3 -B - <<'PY' … PY` でテストmoduleをimportして直接呼出しました。

- 初回：`ModuleNotFoundError: No module named 'skiputil'`。
- テストディレクトリを `sys.path` に追加後：新規テスト成功。
- 比較先を一時的に `DEFAULT_*` へ戻す：`assert changed_key != historical_key` で `AssertionError`。**M1検出成功**。
- 修正復元後：新規テストと指定の既存3本すべて成功。goldenも維持。
- `git diff --check`：出力なし、成功。
- `git diff --stat` / `git diff -- <所有2パス>`：指定範囲のみ、31行追加・2行削除。

pytest・焦点集合・受入全走・修正後の実compiler probeは**未実走**です。

## 所有外 caller・共有 fixture・consumer test への波及可能性 (静的列挙)

- legacy caller：pipeline、backoff_profile、between_run_floor、pegasus_floor_scoping、s1/s2/s3/s5、T2187/T1683/T2000 probe。
- 共有fixture：既存 `_admission_for` を利用し、変更なし。
- consumer test：裁定§9のcampaign・build/site・v2・p3 loop・serialization・各floor/profile/probeテストが確認対象。
- 現行キーは不変。既定変更時のlegacyキー分離だけが挙動変更です。

## 総括

実装済み。直接呼出で修正後の成功と修正前条件の失敗を確認しました。pytestは未実走です。所有外ファイルの編集、`git add`、`git commit` は行っていません。