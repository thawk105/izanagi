## 赤の原因

1. `test_retry_success_uses_only_success_attempt_values_and_v3_schema`
   - schema v3 literalと、`flake_nodeids` を欠く outer receipt の exact field 集合が旧契約でした。
   - 是正箇所: [test_dev_wave_wait.py:9506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1302-r2-nonattrib/orchestrator/tests/test_dev_wave_wait.py:9506)

2. `test_retry_red_check_binds_second_attempt_main_and_tip`
   - retry 用 fake が、新しい runner の object type 検査 `git cat-file -t` に応答できず、`AssertionError` が `unexpected-error` へ変換されていました。
   - 是正箇所: [test_dev_wave_wait.py:1311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1302-r2-nonattrib/orchestrator/tests/test_dev_wave_wait.py:1311)

3. `test_verdict_attempt_is_never_retried[red-check-success]`
   - 2 と同じ fake の欠落です。verdict 後の retry 制御自体は原因ではありませんでした。
   - 検査本体: [test_dev_wave_wait.py:9325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1302-r2-nonattrib/orchestrator/tests/test_dev_wave_wait.py:9325)

## 直した内容

Production 側:

- 変更なしです。
- `_RedCheckResult` は既に両集合を保持し、retry 第 2 attempt の checker 結果を receipt へ渡していました。
- runner blob の object type と main/tip 等値検査も既に有効です。

テスト側:

- retry fake に runner の `blob` 型と専用 blob SHA 応答を追加しました。
- テスト名と schema pin を v4 へ更新し、outer receipt の exact field 集合へ `flake_nodeids` を追加しました。
- retry 第 2 attempt に有効な flake node を与え、`red_nodeids` と `flake_nodeids` が別集合のまま receipt へ届くことを追加検査しました。
- 変更は [test_dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1302-r2-nonattrib/orchestrator/tests/test_dev_wave_wait.py) だけです。

## 保全した検査意図

- 成功 attempt の main、tip、log hash、scheduler、環境値だけを使う検査は維持しています。
- retry 第 2 attempt の main/tip 束縛 assertion は維持し、flake 搬送検査を追加しました。
- verdict 到達後の `submissions == 1` と claim 回数の検査は変更していません。
- 非帰属 exact 3 field、flake exact 5 field、各 rc、整列、一意、互いに素、runner blob 検査は一切緩めていません。

## 未了・懸念

- 指示どおり pytest は未実走で、緑は主張しません。
- AST parse、`git diff --check`、変更対象制限、結合文字不在は確認済みです。
- 残る schema v3 literal は land の旧 schema 拒否テストです。改名後の旧テスト名 pin はありません。
- commit、docs 更新は行っていません。

## 総括

3 件の合成不整合をテスト側で是正しました。  
production の retry 経路は既に `flake_nodeids` を正しく運んでいました。  
main 側の retry 検査意図と T-1302 の厳密な受理集合をともに維持しています。  
是正済み・pytest 未実走・未 commit です。