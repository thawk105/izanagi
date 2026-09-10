## 対応表

| 所見 | 判定 (closed / partial / regressed) | 根拠 (file:line) |
|---|---|---|
| F1 | closed | 2 fixture に canonical genome が追加された (`orchestrator/tests/test_layer3_report.py:3565`, `:3871`)。`_floor_protocol_and_basis` はこれを `protocol_from_floor_genome` に渡し silo と解釈する (`orchestrator/campaign/layer3_report.py:477-492`)。系列単位除外・between-run 維持の assert (`test_layer3_report.py:3581-3592`) と、pin-missing 時の除外 assert (`:3879-3895`) は変更されていない。 |
| F2 | closed | `scanned_files == 1` が追加された (`orchestrator/tests/test_layer3_report.py:3500`)。走査を再帰化すると registered 配下の g1・g2 が入り、g1 は pin と辞書上で重複排除されるため実際の件数は 2 だが、いずれにせよ assert は赤になる (`orchestrator/campaign/layer3_report.py:518-544`, `:613-615`)。 |
| N1 | closed | exact identity の完全一致時に全 within-run 候補を空にすることと、samples/tolerance を再検査しないことを明記している (`orchestrator/campaign/layer3_report.py:25-28`)。実装の契約と一致し、過剰主張はない (`:539-543`, `:579-586`)。 |

## 退行

無し。

## 総括

F1、F2、N1 はすべて closed。
fix 増分は裁定どおり、docstring 2 行、fixture genome 2 件、`scanned_files` assert 1 件だけである。
production の実行コード、既存テストの期待値・literal・pinに変更はない。
静的再レビューのみで、pytest は実走していない。