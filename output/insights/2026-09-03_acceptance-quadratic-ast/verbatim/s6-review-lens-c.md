## 所見

must-fix はありません。新 helper は CPython 3.10.12 と同じ結果を返し、guard 生成も保存されています。

### 境界テストが 3 種の非改行文字を個別固定していない

- 区分: nit
- 根拠: [test_p3_b4_wiring_probe.py:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-quadratic-ast/orchestrator/tests/test_p3_b4_wiring_probe.py:238) は form feed、`\x1c`、`\x85`、U+2028、U+2029 を含みますが、`\x0b`、`\x1d`、`\x1e` は含みません。
- 成果物への影響: 現実装には影響なし。ただし将来この 3 文字のどれかで分割する回帰が入ると、guard、証拠 JSON、digest の変化を境界テストが直接検出できません。
- 推奨対応: separator の組へ `\x0b`、`\x1d`、`\x1e` を追加する。

現実装は [p3_b4_wiring_probe.py:727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-quadratic-ast/orchestrator/campaign/p3_b4_wiring_probe.py:727) で `\n` と `\r` だけを分岐対象としているため、この 3 文字を含む全指定文字で CPython 3.10.12 と一致することを小型 oracle でも確認済みです。

### 裁定 A3 の「終端空要素」という説明が CPython 3.10 と一致しない

- 区分: nit
- 根拠: [stage4-adjudication.md:37](/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_acceptance-quadratic-ast/stage4-adjudication.md:37)、[p3_b4_wiring_probe.py:741](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-quadratic-ast/orchestrator/campaign/p3_b4_wiring_probe.py:741)、[test_p3_b4_wiring_probe.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-quadratic-ast/orchestrator/tests/test_p3_b4_wiring_probe.py:254)。
- 成果物への影響: valid な `ast.parse` 由来 node には影響せず、現在の受理集合、証拠 JSON、digest、台帳は不変です。
- 推奨対応: 製品コードは変更せず、裁定文だけを親側で訂正する。CPython 3.10.12 では空 source は `[]`、`"value\n"` は `["value\n"]` となり、該当 synthetic node は双方とも `IndexError` です。

## 禁止事項の照合

- `ast.unparse` だけへの置換禁止: 遵守。抽出は [p3_b4_wiring_probe.py:804](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-quadratic-ast/orchestrator/campaign/p3_b4_wiring_probe.py:804) の helper 優先で、fallback、`guard.strip()`、else の `not (...)` も同 804-810 行に残っています。
- stdlib private API の製品利用禁止: 遵守。製品コードに `ast._...` はありません。テスト内 reference の [test_p3_b4_wiring_probe.py:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-quadratic-ast/orchestrator/tests/test_p3_b4_wiring_probe.py:157) だけです。
- 既存テストの期待値変更、反転、緩和、skip、削除禁止: 遵守。射影 2 ファイルの差分は新規 4 テストと単位 B の呼出順変更だけです。`attempts == 1` は同ファイル 597 行、`["exec", "import"]` は 1140 行に保存されています。
- node 削減、検査削除、parametrize 集約による高速化禁止: 遵守。差分に該当する削除や集約はありません。
- `_build_inventory`、`seal`、`_static_module_manifest`、`_proof_switchpoint` の意味論変更禁止: 遵守。これらの定義には差分がありません。依頼文の `_static_method_manifest` という名前は現物にはなく、裁定どおり `_static_module_manifest` を照合しました。
- docs 編集と commit 禁止: 判定不能。実装子報告では未実施ですが、射影外を含む worktree 全体の status と履歴は確認していません。

単位 B も遵守です。

- 1 箇所目は [test_p3_b4_wiring_probe.py:563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-quadratic-ast/orchestrator/tests/test_p3_b4_wiring_probe.py:563) で static、runtime、inventory、seal の順を保存しています。
- 2 箇所目は [test_p3_b4_wiring_probe.py:1122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-quadratic-ast/orchestrator/tests/test_p3_b4_wiring_probe.py:1122) で static、runtime、seal の順を保存しています。

## 未実走・未確認

- pytest は未実走です。緑とは判定しません。
- 全 45 module の oracle test と分割回数 spy は再実走していません。
- CPython 3.10.12 との小型 oracle は実行し、UTF-8 byte offset、単一行、複数行、`end_col_offset == 0`、空 source、終端空行、padding、location 欠落、指定された全 separator で一致を確認しました。
- 射影外の caller、テスト、docs、worktree 状態は未確認です。

## 総括

- must-fix はありません。
- guard 文字列と fallback は CPython 3.10 の挙動を保存しています。
- 受理集合、inventory、seal、証拠 JSON、digest を変える現行不具合は見つかりませんでした。
- 単位 B の 2 箇所と指定期待値は契約どおりです。
- 残件はテスト網羅の nit と裁定文 A3 の説明訂正だけです。