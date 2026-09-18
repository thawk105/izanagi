## 総括

**GO（固定 tip `2b1015486096566210386b138333a89b7f94a526` の静的監査）、must-fix 0件。**

今回の実走はありません。旧受入 rc=70、2回目の `test_sigterm_ignoring_child_is_killed` の10秒 timeout は未解決の受入残余であり、受入緑・land 可とは判定しません。

## 所見

real の実装修正事項はありません。行番号は固定 tip 基準です。

- **refuted／規律2の緩和** — `tools/spool_fold.py:3474`。例外時は引き続き `TransactionError`、構造的拒否の分岐も不変。現行 producer の値域では受理集合を変えません。最小修正：不要。
- **refuted／F649・恒真テスト** — `orchestrator/tests/test_spool_fold.py:2452`。健全状態を実 verifier で確認後、実 Git の dangling HEAD を作り、wrapper を直接呼びます。先行検査は明示 SHA を使い、`git_state.py:1068` の実 `head` 操作へ到達する構造です。最小修正：不要。
- **refuted／生 path・子出力の追加** — `git_state.py:209` → `schema.py:101` → `spool_fold.py:3478`。追加表示は sanitize 済み detail。到達経路の producer 値は固定診断語・allowlist 内の operation・固定 label で、stdout/stderr や path を混入しません。最小修正：不要。
- **refuted／consumer 取り残し・scope 拡張** — `spool_fold.py:3501,3526`、`dev_wave_land.py:5343`。caller は例外を拒否として扱い、land は message を reason に格納します。変更文字列への判定依存は見つかりません。実装差分は指定2ファイルのみで、導入 commit に Codex `role=author` の記録があります。最小修正：不要。

## 検証範囲と限界

- 既存変異記録は `08aa6cf99` の結果です。実装2ファイルと指定 producer 3ファイルは固定 tip と差分なし。記録内 stdout の digest も一致しましたが、今回の再実走証拠ではありません。
- baseline・M0 は各188 passed。**M1は診断感度の証拠**で、拒否能力の kill には数えません。**M2は fail-open を検出する正例**で、新テストだけが「TransactionError を返さなかった」で失敗しています。
- 新テストは wrapper の例外経路を検証します。mark/finalize には先行 HEAD 検査があり、この入力で land 全経路を通した証拠ではありません。
- sanitizer は許可キー内の任意の path 文字列まで一般的に除去する保証を持ちません。安全性判断は今回追跡した producer 値域に限定します。同じ detail に縮約される原因、`return_code` の欠落、非 `DevWavesError` の既存表示は残ります。
- コード・docs・commit・tmp の書込み、新受入・land・テスト起動は行っていません。