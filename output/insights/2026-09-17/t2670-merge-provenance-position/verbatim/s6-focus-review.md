## 対応表 (R1: closed / partial / regressed と根拠)

| 所見 | 判定 | 根拠 |
|---|---|---|
| R1 | closed | fix は `test_dev_wave_wait.py:8641` の `env["PYTHONDONTWRITEBYTECODE"] = "1"` 追加のみ。期待値・assert の変更なし。現物の静的 scan は違反・解析エラーともに0件。メモリ上で追加行だけ除くと、元の `8703:14:run` 違反1件を再現した。 |

本レビューでは pytest を実行していない。親報告の checker rc=0・385 passed と静的結果は整合する。

## 所見 (受理・拒否挙動と env 継承)

`_real_waiter_repo` は1112行で同じキーを `"1"` に設定して返す。fix は通常の dict に対する同値の再代入であり、waiter に渡す環境は変更前後で同一。

偽 checker・runner へ継承される値にも差はない。偽 checker は Git の到達性で判定し、runner の計数処理もこのキーを参照しない。負例で runner は起動されない。

したがって、main-only 違反による `merge-history-provenance` 赤（rc=70、source_rc=1）、runner 計数0、lease 解放、2親 merge の保持、違反 commit の到達性、監査 trace の期待は変わらない。

## 所見 (同型の残り)

P1 は明示的な `env=` と Python を先頭に持つ list/tuple argv の直接 subprocess 呼び出しを対象とする。P2 は `-B`、dict literal、同一関数内の guard literal、同一ファイルの単純代入から1段の関数参照を認識する。tuple 分解代入は追跡しないため、今回の明示が必要だった。

対象ファイルを AST で全件列挙した結果、該当する呼び出しはすべて `subprocess.run([sys.executable, ...], env=...)` の13件で、全件 guard 認識済み。

| guard の形 | 呼び出し行 |
|---|---|
| 関数内の明示代入 | 1701、4917、8604、8704、8810、8927、9237、9371、9396 |
| 関数内の dict literal | 9087 |
| `env=` の直接 dict literal | 3454、9483、9600 |

同型の未対応は残っていない。この結論は checker の静的検出範囲内。

## 所見 (裁定への影響)

`ruling-s6.md` の結論には追記が必要。「code の fix 0件」「焦点再レビューを行わない」「author patch のまま」は、現在は「テストの guard 明示1件（7562001c4）、焦点再レビュー実施」に更新する。

A4 の受理集合変化、D fragment・F206 supersede・最終報告への明記方針には影響しない。production code、監査位置、checker 意味論を変えないため、他の裁定も維持できる。read-only のため文書更新は未実施。

## 総括

GO