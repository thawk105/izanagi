## 総括

X1〜X10 の修正を指定 2 ファイルだけへ実装し、commit はしていません。  
正常 fixture、独立 projection oracle、campaign guard、commit marker 公開、Markdown provenance、standalone bootstrap を更新しました。  
ただし指定テストは 2 回とも Pegasus の `qstat` preflight で `rc=16` となり、テスト本体は未実走です。以下の `closed` は差分上の対応判定であり、テスト緑を意味しません。

## X1〜X10 の対応表

| X | 判定 | 対応内容・根拠 |
|---|---|---|
| X1 | closed | canonical `ROLE_FILE` を使う ABORT fixture、seed/replica 不変条件、assembly/binding/result の非 None assertion を追加。[test_p3_b4_material_report.py:52](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/tests/test_p3_b4_material_report.py:52) |
| X2 | closed | campaign lock の parent、または WAL の `parents[1]` から実 campaign root を導出。equal/below/above も実 root で検査。[p3_b4_material_report.py:996](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/campaign/p3_b4_material_report.py:996) |
| X3 | closed | artifact 在否を planned leaf ごとに一度だけ frame へ凍結し、row と oracle が同じ凍結値を参照。[p3_b4_material_report.py:283](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/campaign/p3_b4_material_report.py:283) |
| X4 | closed | `_rows_from_inputs` を正解側に使わない全 field 独立 oracleへ変更。M03 は ABORT の `diff-quarantine` を null 化。Markdown 全必須列との一致検査も追加。[p3_b4_material_report.py:498](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/campaign/p3_b4_material_report.py:498) |
| X5 | closed | root discovery を `complete`/`partial` と unresolved provenance に分離。partial 時の `output/.../campaigns` 配置を限定的に fail-closed 化。[p3_b4_material_report.py:1013](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/campaign/p3_b4_material_report.py:1013) |
| X6 | closed | JSON/Markdown を fsync 後に create-only linkし、directory fsync後、hash付き `report.complete` を最終 commit point として公開。rollback failure は typed error 化。[p3_b4_material_report.py:1130](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/campaign/p3_b4_material_report.py:1130) |
| X7 | closed | Markdown に publication root、artifact hash、再現 argv、assembly typed reason を追加。backslash→pipe→CR/LF の順で escape。[p3_b4_material_report.py:828](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/campaign/p3_b4_material_report.py:828) |
| X8 | closed | test file 冒頭に repo-root bootstrap を追加。[test_p3_b4_material_report.py:15](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/tests/test_p3_b4_material_report.py:15) |
| X9 | closed | M13 を `runs/..` lexical alias に変更。M16 を early、pre-publish race、create-only link の3 nodeに分割。[test_p3_b4_material_report.py:556](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/tests/test_p3_b4_material_report.py:556) |
| X10 | closed | 未使用 fixture `root` を削除。`contract_binding` は provenance へ射影し、再照合にも使用。[p3_b4_material_report.py:754](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/campaign/p3_b4_material_report.py:754) |

## 実走結果

指定コマンドを実行しました。

```text
python3 tools/run_tests.py orchestrator/tests/test_p3_b4_material_report.py
```

- 1回目: `rc=16`、約 0.12 秒。`qstat -Q preflight rc=1`、child 未起動。
- 許可された再実行: `rc=16`、約 0.07 秒。同じく child 未起動。
- nodeid 範囲: file 全体を要求したが、収集・実行 0 node。
- passed/failed: 未取得。緑とは報告しません。

補助確認は成功しています。

- 2ファイルの AST parse: rc=0
- repo 外 cwd、`PYTHONPATH` 無しの test-file import-only probe: rc=0
- clean CLI `--help`: rc=0
- U+0300〜U+036F 不在確認: rc=0
- `git status`: 指定された未追跡 2 ファイルだけ

## 所有外への波及 (静的列挙)

- 現在の repository 内に generator の所有外 caller は見つかりませんでした。
- test fixture は既存 raw-producer test の private helper群を共有しますが、共有元は変更していません。
- 新しい `report.complete` commit marker と `B4MaterialReportWrite.report_commit_path` は、将来の consumer が公開完了を判断する surface です。
- 新規 test file に波及する collection/plain-runner/import-invariant meta-test は、dispatch 障害のため未実走です。
- producer、ledger、evaluator、既存 fixture・既存 test の byte 変更はありません。

## 受理・拒否挙動の変化

- 正常 assembly は ledger/evaluator まで進み、完全な source row を材料化する設計です。
- missing/malformed leaf でも disjoint な出力先なら partial report を許可します。
- campaign root が完全に証明できない場合、`output/.../campaigns` 配置だけを新たに拒否します。
- 実 campaign の equal/below/above と lexical alias を拒否します。
- JSON/Markdown は commit marker が無い限り公開完了ではありません。
- 既存 pair、publish 前 race、create-only link collision はそれぞれ独立に拒否します。
- 一般化した official-root admission や certified-selection connection は追加していません。

## 未完・未解決

- 焦点 suite と meta-test は Pegasus queue preflight 障害により未実走です。親環境で指定コマンドの再実走が必要です。
- commit は禁止事項に従い作成していません。