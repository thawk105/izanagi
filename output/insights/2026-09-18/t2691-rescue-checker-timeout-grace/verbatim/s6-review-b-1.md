## 最小差分か

裁定超過の所見なし (検査した根拠: `s5-author-1.patch:9,57,78,91,104,118`、`s4-ruling.md:32–52`)。

production は定数・comment の追加と timeout 式1行の変更のみ。test は helper 1個・3本で、assert も裁定どおり。未証明 unit の payload は指定された回収正例に必要であり、削除対象にしない。

**real / nit — comment の観測内訳は削除可能。** `tools/check_branch_rescue.py:41–42` の `T=1 x10 / T=8 x2` と最小値 `0.087` は、必須4点に含まれない。削除候補として名指しするが、現状も将来計画や一般論への逸脱はない。
成果物影響: 放置しても test 所要・受入 wall・判定 JSON・台帳の値は変わらず、comment の情報量だけが増える。

## test 所要と flake

指定値からの再計算は以下。

| test | 公称所要の算出 | 親の実測 |
|---|---|---:|
| timeout JSON | sleep `0.5 + 0.3`、親 timeout `2.5` | 0.84 s |
| silent | `min(1.0 + 2.0, 100.0)` | 3.02 s |
| overall cap | `min(5.0 + 2.0, 0.5)` | 0.50 s |
| 合計 | 4.30 s＋起動・回収等 | 4.36 s |

根拠: `orchestrator/tests/test_check_branch_rescue.py:155,1960,1981,1994`、`s6-parent-measurements.md:21`。**新規3本の call 所要は5秒以内で、残りは0.64秒。**

**real / nit — 受入 wall の増分は未確認。** `s6-parent-measurements.md:20–21,28` には変更前の同条件測定がなく、単独走の `6.39 s` も増分ではない。4.36秒から受入全体の「+5秒以内」まで確定してはいけない。
成果物影響: 放置して完了扱いすると、受入 wall の増分に関する記録が実測の射程を超える。現在の未実施記載は維持する。

**疑い / nit — 高負荷時の flake は排除できない。** `orchestrator/tests/test_check_branch_rescue.py:1960,1974,1987,1998` について、

- 正例は公称0.8秒から親打切り2.5秒まで約1.7秒の余裕。elapsed 上限 assert がなくても、子の起動・実行遅延で JSON 回収に失敗し得る。
- silent の下限2.8秒には公称3秒から0.2秒、上限10秒には7秒の余裕がある。
- overall の上限3秒には公称0.5秒から2.5秒の余裕がある。
- m4 の検出は公称2秒と下限2.8秒との差0.8秒に依存し、遅延で変異が生存する可能性がある。

親の新規3本は load 11〜28 の観測であり、load 60超や計算ノードの保証にはならない (`s6-parent-measurements.md:21`)。
成果物影響: 高負荷時に正常実装の test が赤になる、または m4 が SURVIVED となり、受入 wall・変異台帳が揺れる可能性がある。発生実測はないため must-fix にはしない。

残留 process の所見なし (検査した根拠: `orchestrator/tests/test_check_branch_rescue.py:145–158`、`tools/check_branch_rescue.py:1583–1595`、`/usr/lib/python3.10/subprocess.py:503–519`)。fake は孫 process を生成せず、環境の `subprocess.run` は timeout 時に直接の子を `kill()` 後 `wait()` する。通常の timeout 経路で60秒 sleep の子を置き去りにしない。

## scope 外の混入

所見なし (検査した根拠: `s5-author-1.patch:1–126`、`tools/check_branch_rescue.py:38–44,1583–1595`)。

T-2686、`_audit` deadline、GRACE の CLI 化、`check_branch_landed.py` 改修、既存 test の置換・緩和、他 subprocess への一般化、retry、production の sleep は含まれない。既存 `_make_fake_landed` も変更されていない。

## docs の過不足

実装不一致の所見なし (検査した根拠: `docs/unreachable-object-ledger.md:91–95`、`tools/check_branch_rescue.py:1591–1595,1630–1640,2078–2082,2148–2149`)。

期限報告回収時の `assessment-timeout` と、親打切り時の `checker-timeout` を分け、親の待機に overall cap を含めている。「いずれも rc 2」は rescue 本体の終了コードとして一致する。親打切り時の `checker_rc=None` と矛盾しない。

**real / nit — 2秒の重複記載は1箇所に減らせる。** `docs/unreachable-object-ledger.md:92,94`。数値は運用見積りに有用だが、同じ数値を2箇所に置く必要はない。94行の置換案は逐語で以下。

> 応じて上げ、判定件数 × (子予算 + 終了余裕) に inventory 等の時間を足した見積りが全体の `--timeout-seconds`

成果物影響: 放置しても現時点の台帳説明は正しいが、定数変更時に片方だけ更新すると待機見積りが食い違う。追記は不要。

## 変異 matrix の本数と帰属

m1〜m3 の重複・単一理由性違反の所見なし (検査した根拠: `s4-ruling.md:63–65`、`orchestrator/tests/test_check_branch_rescue.py:1960–1963,1994–1998`)。

m1 は余裕消失、m2 は overall cap 消失、m3 は子予算への誤加算。同じ正例が m1/m3 を検出しても、別の誤変更なので代替とはいえない。

m4 の登録削除を要する所見なし (検査した根拠: `s4-ruling.md:66`、`orchestrator/tests/test_check_branch_rescue.py:1987`)。m1〜m3 では sum→max を検出できず、m4 は待機時間の契約を検査する。ただし JSON 受理の検出実績とは分けるべきである。実行後の raw status が KILLED なら保持し、集計の内訳を「m1〜m3」「時間契約 m4」に分ける。現時点では全件未実行で、KILLED は期待値にすぎない (`s6-parent-measurements.md:28`)。

**real / nit — m5 は削減候補だが、削除には裁定変更が必要。** `s4-ruling.md:67`。引数順交換はこの有限値の呼出しでは等価で、production の欠陥検出には寄与しない。価値は harness が SURVIVED を扱えることの確認だけである。
成果物影響: 維持すると変異実行が1走増える一方、判定 JSON の回帰検出範囲は増えない。新規3本を全実行する構成なら公称4.3秒＋実行基盤の費用が加わる。

本波では裁定済みの1件に限定し、同種の等価変異を追加しない扱いが妥当。

## author 報告の過大主張

所見なし (検査した根拠: `s5-author-1.md:10–16,26,39,43–49`、`s5-author-1.patch:1–126`、`s6-parent-measurements.md:15–21,25,28`)。

- 「すべて」は変異 anchor 3文字列の件数に限定され、現物でも各1件と確認した。
- 「closed」は「closed とはしません」という否定であり、網羅性の主張はない。
- test 未実走・回帰未判定・親側の残作業を明記している。
- 親実測は期限到達事例4/4の回収を記録しているが、T=8は期限事例ではない。author 報告にも T=8 の同条件対照成功や高負荷保証への拡張はない。

## 総括

**must-fix なし。** 削減候補は comment の観測内訳、docs の2秒の重複、裁定変更を伴う m5。production・helper・test 本数に裁定超過はない。

新規3本の call 所要は親記録で4.36秒。受入 wall の増分、高負荷時の安定性、変異の実結果は未確認として残す。

本レビューは静的検査のみ。ファイル変更・pytest 実行は行っていない。