## 所見

1. **real — plan v2 の「None は現行より増える方向だけ」は同値 tie で成立しない。**

   **根拠:** `plan-v2.md:8` の主張に反例がある。`runner.py:810` の旧代表選択は同値の先頭、`:815-817` の偶数分岐は stable sort 後の中央 2 件を採る。実行順の `(tps, abort)` が `(80,None),(80,.1),(80,.1),(80,.9)` なら旧値は `None`、新値は `.1`。現物から helper と `_median` だけを抽出した計算でも確認した。baseline tps=100、abort=.1、factor=2、k=2、floor=.05 なら、`pipeline.py:2366-2375` により旧 verify 送りから新 screen-reject へ変わる。

   **成果物への影響:** 欠損を含む同値反復でも、certified 候補集合・COMMIT 集合が縮み得る。

   **推奨: nit。** 裁定 4 は既に両方向の変化を許容しているため実装の阻害事項ではないが、裁定 2 の単調性保証は撤回する。中央 2 件の厳格 None 規則自体は実装どおり。

2. **refuted — helper の plan 違反、奇数互換性の破壊、空入力の新規例外経路は認めない。**

   **根拠:** `runner.py:805-822` は指定の 6 段に一致する。奇数では変更前と同じ `min(abs(tps-median_ref))` を使い、5 field をそのまま返すため、同値先頭・None・counter オブジェクトを維持する。偶数の sort は throughput のみを key とし、同値順は有効 rep の実行順を保持する。`model.py:242-248` の 2 要素 `_median` は算術平均。有効 0 件では実際の `rep_results` 要素が tuple（`runner.py:1061`, `:1284`）なので、`[-1][1:]` も従来と同じ 5 要素 tuple。空 list は両呼出元の raise が先行する。

   **成果物への影響:** 奇数有効数の 5 field と、有効 0 件の最後の解析値に変更はない。

   **推奨: scope 外（修正不要）。**

3. **refuted — direct／deferred の配線や前後順序は維持されている。**

   **根拠:** deferred は `runner.py:1067-1077`、direct は `:1294-1305` で、いずれも「全失敗判定 → helper → `rep_observations` の辞書コピー」の順。deferred の呼出しは `open_measurement_point` 内に残る。patch は throughput 蓄積、strict mode、完全性検査、returncodes、timestamps、raw counter 証跡を変更していない。

   **成果物への影響:** 開封前の指標導出や、失敗を成功扱いする新経路は生じない。

   **推奨: scope 外（修正不要）。**

4. **refuted — digest の latency 除外漏れ、WAL からの削除は認めない。**

   **根拠:** `digest.py:65-67` は明示の 4 指標。`:782` の射影、`:1189` の軸集約、`:1265-1281` の表・軸描画がこれに追随する。`_AXES`（`:309`）は設計フラグの列挙で latency に依存しない。ファイル中の latency 記述は除外理由の docstring のみで、rejection 系にも依存は残らない。`model.py:101-107` の WAL 向け 5 key は維持されている。

   **成果物への影響:** digest 表・軸だけが 4 指標になり、WAL の latency と rejection の情報境界は維持される。

   **推奨: scope 外（修正不要）。**

5. **real — 新しい帰属例も、観測から言えることを断定しすぎている。**

   **根拠:** `digest.py:11-13` は throughput 低下・abort 率不変から「競合を減らしておらず」「待ち時間のコストだけ」と読ませる。しかし abort 率は比率であり、競合回数・待機時間・実行コストを一意に特定しない。例えば commits/秒と aborts/秒が両方半減すれば比率は不変になる。これは plan v2 の例文自体に由来する。一方、`:15-16` の恒等変換の説明は「CCBench の通常出力」に限定され、`result.cc:52-56` と整合する。

   **成果物への影響:** 数値は変わらないが、帰属説明を参照したレポートが未確認の機序を確定事項として扱い得る。

   **推奨: nit。** 「abort 率の改善は観測されず、待機コスト増が仮説となる」程度に限定する。

6. **refuted — model コメントと実装の代表規則・平均・None 規則に矛盾は認めない。**

   **根拠:** `model.py:70-74` は上側中央・同値先頭、奇数の代表値、偶数の中央 2 rep 平均と片側欠損時 None を記載し、`runner.py:808-821` と対応する。ただし有効 0 件の最後の rep への fallback はコメントに明記されていない。

   **成果物への影響:** 通常の集約値の説明は一致する。有効 0 件でも診断 field が残る点だけはコメント単独では分からない。

   **推奨: nit。** 必要なら有効 0 件の例外を一文補足する。

7. **refuted — fitness・verifier・payload key の変更、規律 2／6 の緩和は認めない。値の変化は consumer に届く。**

   **根拠:** throughput 蓄積と中央値計算は不変。`pipeline.py:1455-1468` は指標を WAL に渡し、`:2388-2440` は screening 通過後も全 verify の通過を要求する。8c の閉列挙は `s8c_generation_projection.py:58-81`、値の射影は `p3_autonomous_workload_trial.py:2004-2029` のまま。layer3 の共有検証も変更されていない。新規コードに外部文字列を指示として扱う処理はない。

   追加の注意として、`backoff_sweep_report.py:86,187` は既存の `abort_rate or 0` により、新しく生じる None も 0% と描画する。また `plot_b10_extended_backoff.py:619-622` の逆数検査は、`:605-606` で有効 throughput 5 件を必須とするため、今回の偶数変更による破損例にはならない。

   **成果物への影響:** 偶数時の WAL・8c・layer3 の値、screening の受理集合、レポートの値は変わり得るが、verify を迂回した certified 化は起きない。

   **推奨: scope 外。** backoff レポートの欠損を 0% とする既存挙動は別件として残す。key 不変を値・解釈不変とは扱わない。

8. **未実測 — author 報告との実装上の食い違いは見つからないが、受入成功は未確認。**

   **根拠:** patch と統合 commit の変更対象は報告どおり 5 ファイル。追加 5 関数・9 node、calibrator 自走 harness の拡張も対応する。plan 末尾の「4 file」は列挙との数え違い。`author-1.md:19-20,36-62` は calibrator 成功と critic の 48 失敗・対象断言未到達を明示しており、成功を装ってはいない。本レビューでは pytest・変異 matrix・受入全走を実行していない。

   **成果物への影響:** 現時点では critic の対象断言と変異感度を受入証拠として確定できない。

   **推奨: scope 外（親の予定済み検査）。** 統合後の焦点走・変異 matrix・受入結果で確定する。

## 総括

GO（レンズ A の静的レビュー。must-fix なし）。
helper・配線・key 維持・verify 必須条件は plan v2 に一致する。
ただし「None は増える方向だけ」は同値 tie の反例があり、裁定の説明訂正を推奨する。
帰属例には機序の断定が残るため、仮説としての表現が適切。
親の焦点走・変異 matrix・受入全走は未実施であり、本判定はその成功を代替しない。
