## 所見ごとの対応表

| レビュー | 種別・所見 | 判定 | 根拠 |
|---|---|---|---|
| A | must-fix: m12 が artifact stem の誤変更を検出できない | closed | basename の独立 literal assert を追加。`test_backoff_extended_sweep.py:687-693` |
| A | nit: m13 の事前登録位置が等価変異 | 不採用 (親裁定) | `tuple` 正規化は従来どおり。`backoff_extended_sweep.py:856-865`、凍結入力は `test_backoff_extended_sweep.py:673-677` |
| A | nit: m11 が直接の非呼出 oracle でない | closed | `M.materialize_t2418_report` の spy と、0回／1回 assert。`test_backoff_extended_sweep.py:1349-1374,1419-1427` |
| A | nit: positive prebuild assert が冗長 | 不採用 (親裁定) | assert は維持。`test_backoff_extended_sweep.py:1074-1075`。validator の正例・負例は同`:1131-1165` |
| B | must-fix: runtime meaning witness が成果物にない | closed | 定数は `backoff_extended_sweep.py:99-101`、search config は`:647`、JSON は`:1168`、`.dat` provenance は`:1275` |
| B | nit: short write の例外文が T-2266 固有 | 不採用 (親裁定) | 共有 helper の文言は維持。`backoff_extended_sweep.py:393-400` |

## F1 の殺傷力

m12 は殺せる。

`materialize_t2418_report()` の stem（`backoff_extended_sweep.py:1252`）を `t2266-backoff-static-tail-*` に変えると、`test_t2418_frozen_wal_view_flows_through_capture_loader_and_reports` が赤になる。

実行順上、最初に失敗するのは `.dat` の assert（`test_backoff_extended_sweep.py:688-690`）。単独に評価すれば `.json` の assert（`:691-693`）も失敗する。いずれも production 定数や返却値から期待名を組み立てず、T2418 basename の独立 literal と比較している。

## F2 の pin の非恒真性

恒真ではない。

- 定数値は production 定数自身ではなく、literal と比較している（`test_backoff_extended_sweep.py:517-519`）。
- search config は対象 key を直接取得し（`:556-565`）、literal 値を含む辞書と比較する（`:566-585`）。
- JSON top level は `document[key]` を使って検査する（`:697-727`）。
- `.dat` provenance は別に parse した辞書から同じ key を取得する（`:748-752`）。

したがって3か所のどれか1か所だけを削除すれば、対応する辞書内包表記で `KeyError` となり赤になる。JSON と provenance は同じ `expected_disclosure` を共有するが、それぞれ別の実データから key を取得するため、片方だけを落とす変異も生存しない。

## F3 の spy の実体名指し

実体を名指ししている。

spy は production module の `M.materialize_t2418_report` を直接差し替えている（`test_backoff_extended_sweep.py:1361-1365`）。検査対象の `run_workload()` と完走 guard は実体のままであり（`backoff_extended_sweep.py:1451-1460`）、4/5 の初回は0回（test`:1374`）、5/5 の2回目は累計1回（test`:1427`）を確認する。

`run_campaign` と materializer 本体は stub だが、その間の完走判定と具体的 materializer への dispatch は stub ではない。両層の抽象的性質だけで通る形にはなっていない。

## fix による退行の有無

静的には退行なし。

- fix-only 差分の対象は、production と test の2ファイルだけ（`s6-fix-only.diff:1-2,37-38`）。
- 統合差分全体は4ファイル（`s6-combined.patch:1,634,1314,1373`）だが、追加の2 shell file は元の実装差分であり、fix-only への混入ではない。
- `EXTENDED_SWEEP_US`（production`:55-58`）、`encode_static_backoff_us`（`:64-69`）、全 `T2266_*`（`:81-90`）、`_require_distinct_*`（`:226-321`）、`_write_create_only_*`（`:373-407`）に fix hunk はない。
- 既存期待値は、F2 の必須 key 追加とF3の4/5→5/5二段検査以外に変更されていない。既存値の差し替えもない。

本検査ではテストを実行しておらず、fix 後の緑は判定していない。

## 所有外 consumer への波及

射影された根拠内に、T2418 JSON の全 key 集合を完全一致で検査する所有外 consumer はない。

`test_backoff_extended_sweep.py:697-727` は指定 key の projection を比較しており、文書全体の key 集合比較ではない。既存 T2266 consumer の検査（`:758-774`）も T2418 JSON ではなく凍結 WAL view を入力とする。

また、レビュー B が確認した `backoff_extended_sweep_report.py` は extended 分岐だけで呼ばれ、T2418 report を処理しない（`s6-review-b.md:45-50`）。したがって、射影範囲で名指しすべき破損 consumer はない。

## must-fix

新規 must-fix はなし。元の2件はいずれも closed であり、stem 誤変更による成果物探索失敗と、meaning witness 欠落による成果物の意味の誤読を防ぐ oracle が入った。

## nit

新規 nit はなし。不採用の3件は親裁定どおり未変更で、fix による新たな問題ではない。

## 総括

F1・F2・F3 はすべて静的に closed。m12 は新しい basename assert で殺せ、F2 は production 定数に依存しない literal と3か所別々の取得で pin され、F3 は実際の `materialize_t2418_report` symbol への呼出回数を検査している。

fix-only の対象は指定された2ファイルだけで、既存機構への意図しない変更や、射影内の所有外 consumer 破損は見つからなかった。テストは未実走。