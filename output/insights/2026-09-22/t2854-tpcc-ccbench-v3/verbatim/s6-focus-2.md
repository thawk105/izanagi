| 所見 | 判定 | 重大度（元所見） | fix 2 後の根拠・放置時の影響が解消したか |
|---|---|---|---|
| N1：R 全欠落を受理 | **closed** | must-fix | `probe/v3check.py:245` で R/W 総数の正数検査を復元、`probe/selftest.py:140` に全 R 削除＋nR=0 の負例を追加。C4／D1 の誤合格経路は閉じた。 |
| A1：M2 自身の診断発火未確認 | **closed 維持** | must-fix | `probe/run_probe.py:703,713`：marker・worker C≥1000・rc=0・witness・E=C・C>commits・理由集合完全一致を維持。時間切れだけによる誤 kill 攻撃は不成立。 |
| B1：M4 の二重理由 | **closed 維持** | must-fix | `probe/v3check.py:103,107,112,245`：署名基準の表検査を維持。種別交換は R/W 総数を変えず、理由併発による誤拒否攻撃は不成立。 |
| A2：単独変異と単一理由の混同 | **closed 維持** | should | `probe/selftest.py:184`、`probe/run_probe.py:724,739`：理由集合完全一致と M1 の先頭理由ポリシーを維持。検出理由の過大評価は再発していない。 |
| A3：C1/C2 分割未照合 | **closed 維持** | should | `probe/run_probe.py:226,234,254`：各区間の変更ファイル集合の照合・記録は不変。分割違反を通す攻撃は不成立。 |
| B2：不要な build・全ファイル復元 | **closed 維持** | should | `probe/run_probe.py:571,606,614`：初回 configure のみ、変異後 build、変更 bytes のみ復元を維持。不要な再 compile の回帰なし。 |
| B4：spec の未知 key・version 未拒否 | **closed 維持** | should | `probe/run_probe.py:746,748,755,793`：key 集合・version を出力ディレクトリ作成前に検査。未知指定の黙殺攻撃は不成立。 |
| 親 P1：build 並列度16固定 | **closed 維持** | should | `probe/run_probe.py:89,188`：`os.cpu_count() or 1` を build に使用。固定上限による並列度制限の回帰なし。 |

パスは `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/review/` 基準です。必読資料はすべて読めました。静的検査と指定ログの照合のみで、書込み・自己試験の再実行はしていません。

## 新規所見

**なし。今回の範囲で成立する新たな攻撃、正常 fixture の誤拒否、既存 7 所見の回帰は見つかりませんでした。**

## N1 と番号条件の確認

- **全 R 削除＋各 C の nR=0：攻撃不成立。** `v3check.py:184,210` の件数検査は通りますが、`:245` が R 総数0を検出します。W の署名・表構成と witness は保持されるため、結果は `reasons == ['content-table']`、`passed=False`。追加負例は両ファイルを処理し、`:152` でこの理由集合を指定、`:184` で完全一致を検査しています。
- **全 W 削除＋各 C の nW=0：攻撃不成立。** `v3check.py:245` が W 総数0を検出します。ただし署名も失うため、`:103` の検査が先に発火し、理由集合は **`['content-txtype', 'content-table']`** になります。`content-table` による拒否は復元されていますが、単一理由ではありません。このケースの専用負例は追加されておらず、ここは静的判定です。
- **OrderLine の番号による誤拒否：攻撃不成立。** fix 1 前の `ol_min is None or ol_min != 0` と注文内の密連番条件は戻っていません。`v3check.py:116,252` は観測・記録のみです。`selftest.py:166,171` の「全件1始まり」「{0,2}」の正例と観測値検査も保持されています。したがって元 B3 も **partial → closed** と判断します。

## 差分・M3／M4・正常 fixture

fix 2 前後のディレクトリ差分は、次の **2ファイル・各1 hunkだけ**です。

| ファイル | 変更 |
|---|---|
| `probe/v3check.py:245` | R または W の総数が0なら `content-table` とする2行を追加 |
| `probe/selftest.py:140` | 全 R 削除＋各 C の nR=0 の変換と負例1件、計14行を追加 |

`run_probe.py` と `mutation-spec.template.json` は同一 bytes。既存自己試験の期待値変更・削除はありません。

**M3** は表6→5の置換で R/W 件数を保存します。NewOrder 署名は残り、表構成だけが崩れるため、`v3check.py:109` による `['content-table']` を維持します。復元した正数検査は発火しません。

**M4** は宣言種別だけを交換し、R/W 件数・操作署名・表構成を保存します。`v3check.py:104` による `['content-txtype']` を維持します。`run_probe.py:724` の完全一致条件も不変です。

正常 fixture は `selftest.py:10,21` から **R=4、W=16、C=E=commits=4**。両種別が存在し、NewOrder の表5／6の同一 key は別 Counter で比較され、Payment の表構成も満たします。追加条件による誤拒否はありません。

全 R 欠落を M2／M4 に併発させた場合には追加の `content-table` により完全一致を満たさなくなりますが、これは欠落を伴う入力の拒否であり、正常な単独変異の kill を壊す回帰ではありません。

## 親の自己試験ログ

[selftest-fix2.log:2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/review/selftest-fix2.log:2) は **193/193 passed、failures=0**。既存192件に負例1件を追加した差分と整合し、M3／M4 の理由集合完全一致・OrderLine 正例の検査も実装上保持されています。

ログ自体に終了コードの記載はないため、fix 報告の `rc=0` を独立に確認したとは扱いません。計算ノードでの build・実 trace・変異 kill 成立も今回の検証対象外です。

## 総括

- **GO：fix 2 の焦点再レビューとして、N1 は closed。既存 closed の7所見に回帰なし、B3 も closed。**
- **must-fix：なし。**
- M3／M4 の理由集合完全一致、正常 fixture の受理、OrderLine の記録のみという条件は維持されています。