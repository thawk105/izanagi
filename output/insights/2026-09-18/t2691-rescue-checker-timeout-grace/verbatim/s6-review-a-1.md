## 裁定との一致

所見なし (検査した根拠: `s5-author-1.patch:104`、`tools/check_branch_rescue.py:38`、`:1572`)。

- production の変更は定数・コメント追加と外側 timeout 1 行のみ。実装前ファイルに提示 patch をメモリ上で適用し、現物との完全一致を確認した。
- 子の `--timeout-seconds`、早期 return、JSON 検証、rc↔verdict 対応、返却 dict は不変。
- コメントは観測12走・最大0.134秒・約15倍・高負荷未測定を含み、高負荷での回収を保証していない。`2 / 0.134 ≈ 14.93` も整合する。
- 子の期限起点は `tools/check_branch_landed.py:1675`、JSON 出力と rc 決定は同 `:2074` と整合する。

## test の実効性

所見なし (検査した根拠: `orchestrator/tests/test_check_branch_rescue.py:145`、`:1956`、`:1977`、`:1990`)。

新規3本は親の subprocess・時計を差し替えず、`_landed_assessment` の実 subprocess 経路を通る。helper は `--timeout-seconds` の直後を `float` として読み、末尾を OID としている。

正例 payload を `tools/check_branch_rescue.py:1524` 以降で追うと、非 landed unit が1件、有効な evidence が1件、必須キーが揃い、summary 件数も一致する。そのため `complete=True`、`missing_reason=None`、commit 一致、`reason_counts={"assessment-timeout": 1}` になる。

時間境界にも恒真はない。正例の下限0.8秒は子の sleep、沈黙負例の下限は定数参照、overall の上限3秒は cap 除去時の7秒待機を検出する。

**疑い・nit:** 極端なスケジューリング遅延では時間依存の失敗余地が残る (`test_check_branch_rescue.py:1960`、`:1987`、`:1998`)。正例にも実 subprocess の2.5秒期限があるため、assert の上限を省いても完全には除去されない。今回の原ログに発生証拠はなく、裁定どおりの実装である。
影響: test 所要増大・偽陰性の可能性。production の JSON・台帳・rc の欠陥を示すものではない。

## 変異 anchor と単一理由性

所見なし (検査した根拠: `tools/check_branch_rescue.py:44`、`:1585`、`:1591`、`test_check_branch_rescue.py:1962`、`:1987`、`:1998`)。

old 文字列は3種類とも現物内で各1件。m2/m4/m5 の共通 anchor も一意である。

以下は机上検査であり、変異実走の結果ではない。

| 変異 | 担当 test の予測 | 他の新規 test |
|---|---|---|
| m1 | 正例が0.5秒で打ち切られ赤 | 沈黙下限も0.8秒へ変わるため緑。overall も緑 |
| m2 | overall が7秒待ち、上限3秒で赤 | 正例・沈黙は緑 |
| m3 | 子が2.8秒眠り、親2.5秒で打ち切られて正例が赤 | silent は引数によらず60秒眠るため残り2本は緑 |
| m4 | 沈黙を2秒で打ち切り、下限2.8秒だけで赤 | 正例0.8秒は親2秒以内。overall は0.5秒のまま |
| m5 | 全3本が緑の予測 | 有限数値の `min` 引数順交換なので等価 |

m4 の kill 根拠は時間契約であり、JSON 受理の変化ではない。既存 test に別の赤を生む経路も静的には見当たらない。高負荷時まで単一理由性を保証するものではない。

## author 報告と実体

所見なし (検査した根拠: `artifacts/dev-wave-t2691-rescue-checker-timeout-grace/s5-author-1.md:3`、`:10`、`:18`、`:28`、`:39`)。

- 変更箇所・anchor 件数は現物と一致。
- production caller は `tools/check_branch_rescue.py:2072`。新 helper と定数の所有外 Python consumer は検索で検出されなかった。
- author は test を「緑」と報告しておらず、未実走・未判定と明記している。後続の親の成功記録と矛盾しない。
- 構文解析と差分範囲は今回も確認した。過去のフック拒否・runner rc=16 は報告内容として扱い、今回再現した結果ではない。
- 「現行挙動と含意」の2文は、観測と回収範囲の拡大を述べており、JSON 検証述語や時間を含む受理集合を混同していない。

## 既存 test への波及

所見なし (検査した根拠: `test_check_branch_rescue.py:89`、`:1797`、`:1828`、`:1863`、`test_branch_rescue_ledger.py:187`、`:199`)。

既存 `_make_fake_landed` は変更されていない。monkeypatch 型 timeout test は timeout 引数に依存せず例外を投げるため、定数追加の影響を受けない。実 checker の `(30, 30)` は `min(32, 30)=30` で従来と同じ。

docs pin は台帳フィールド・解決状態・stale 通知契約を検査しており、今回の helper・定数追加では変わらない。親の `focus-1.log:18` にも対象を含む127件成功の記録がある。ただし、これは親の実走記録の確認であり、レビュー側の再実行ではない。

## 親の実測値と一般化

**real・nit:** `s6-parent-measurements.md:17` の「unit 0 件 = 列挙前に期限」は現物と矛盾する。

`missing_reason=None` は `tools/check_branch_rescue.py:1562`〜`:1567` により、`summary.files_enumerated is True` を必要とする。列挙前の期限なら子は `tools/check_branch_landed.py:2003` で件数を `None` とし、親の missing reason も `None` にはならない。また `unproven_count=0` は未証明 unit が0件という意味で、全 unit が0件とは限らない。記録は「未証明 unit 0件、詳細射影 complete」に限定すべきである。
影響: JSON・`assessment_reason`・rc・test 所要は変わらないが、実測記録が期限到達フェーズと unit 回収の実証範囲を誤って説明する。

それ以外の数値は原ログと整合する。

- `probe/parent-repro-after.txt:2`、`:4`、`:7`、`:8` より期限 JSON 回収は **4/4**。依頼文の「2/2」は現行記録の集計ではない。
- T=8 の2件は3.827414秒・7.815290秒で完走し、`landed`／rc=0。期限回収の分母に含めていない。
- `focus-2-new3.log:9`〜`:14` より、表示された call 時間の和は `3.02 + 0.84 + 0.50 = 4.36秒`。pytest 全体は6.39秒。
- `focus-1.log:18` の127件・68.44秒は一致。開始終了記録の差は83秒で、runner 全体と pytest 所要は区別が必要。
- 同条件の変更前 baseline が示されていないため、「既存全体の所要増分が5秒以内」はまだ立証されていない。新規 call 合計4.36秒だけでは代替できない。
- checkout 差による対照の限界は `s6-parent-measurements.md:16` に明記され、高負荷保証への一般化もしていない。

## 総括

**production の must-fix は検出なし。real の nit は親実測記録の「列挙前に期限」という誤説明1件。** 時間依存 test の高負荷時の偽陰性は疑いとして残る。

裁定との一致、anchor 一意性、変異の担当 test と単一理由性は静的に確認した。変異 matrix・受入全走・変更前後の所要増分確認は未完了であり、本レビューをその成功証拠にはできない。ファイル変更・pytest 実行は行っていない。