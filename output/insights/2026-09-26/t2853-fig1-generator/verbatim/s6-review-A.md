## 所見

- **A-M1** — `tools/plotting/plot_p2_5_search_cost.py:241`: p 注記は固定文字列です。再計算値と凍結値が一致する別の入力でも、図だけが `2.5×10⁻⁴` のままになります。`d['p']` から有効 2 桁で生成し、test も計算値との対応を検査してください。
- **A-M2** — `tools/plotting/plot_p2_5_search_cost.py:174`: caption と図中にスレッド数・レコード数・skew・env がありません。測定条件を示さない後継図が受理され、作図規約 §6 に反します。WAL・lock から条件を抽出し、caption に記してください。
- **A-M3** — `tools/plotting/plot_p2_5_search_cost.py:268`、`orchestrator/tests/test_plot_p2_5_search_cost.py:121`: 着地 bundle の closure が生成器の**現行** SHA-256 も比較します。着地後に生成器だけを直すと、図の bytes が不変でも test が恒常的に赤になります。生成器 hash は生成時の記録として残し、着地検査では入力・出力を照合してください。
- **A-S1** — `tools/plotting/plot_p2_5_search_cost.py:174`: caption は点・横棒・四角・ひげ・点線・破線の意味を説明しません。平均と中央値、分位範囲を読者が取り違え得ます。各記号と線種を一文で定義してください。
- **A-S2** — `tools/plotting/plot_p2_5_search_cost.py:141`、`:245`: `8/12 mis-converged` の分子は summary の `guided_failures` を直接表示し、`_reconcile` の対象外です。注記を変えても照合を通ります。凍結値が出所であることを明記し、少なくとも件数の範囲と予算上限 8 の点数との整合を検査してください。
- **A-S3** — `orchestrator/tests/test_plot_p2_5_search_cost.py:47`: landscape の合成例に未 commit・重複 genome・crash tail がなく、WAL 全 frame 検査の負例もありません。これらの読み出し規則を壊しても現在の test では検出できません。各規則を通る負例を追加してください。

旧図の題・軸名・1〜8 の目盛り・panel 順・色・記号・注記の文言と桁は、生成器と一致します。`landscape_from_records` の committed variant 採用と同一 genome の上書きは `replay.load_landscape` と同形で、E0 は fig2b と同じ `HISTORICAL_RAW` の扱いです。ただし実走による確認ではありません。

## 裏取りした観察

- **(a) real** — p 注記は固定文字列（生成器 241 行）。計算した `d['p']` を描画に使っていません。
- **(b) real** — caption に測定条件と記号・線種の意味がありません（174〜181 行）。条件は provenance の `run_cmd` 等に一部残るだけです。
- **(c) real** — closure は `provenance['generator']` を含む全参照の SHA-256 を現物と比較します（268〜278 行）。着地 test はその closure を呼びます。

## 変異の帰属

| 変異 | 殺す test | 単一理由性 |
|---|---|---|
| M1 | `test_reconciliation[greedy]` | あり。greedy mean の不一致を見逃すため |
| M2 | `test_reconciliation[A]` | あり。A の不一致を見逃すため |
| M3 | `test_reconciliation[p]` | あり。p の不一致を見逃すため |
| M4 | `test_landscape` certified 負例 | あり |
| M5 | `test_landscape` 7 genome 負例 | あり |
| M6 | `test_real_data` ほか実データ test | **なし**。複数 workload の照合と度数 assert に波及 |
| M7 | `test_real_data` ほか実データ test | 同一の E0 admission 拒否だが複数 test に波及 |
| M8 | `test_end_to_end` | あり。中央値棒の値が中央値と異なる |
| M9 | `test_closure` | あり。改変 PNG を受理する |
| M10 | `test_layout` | あり。重複 text を受理する |

## 判定

**NO-GO。** A-M1〜M3 を直してから着地判定が必要です。

## 総括

値の主要系列は追跡下の summary と P2-2 記録から組み立てられています。p の表示、caption、着地後の closure に受理上の欠陥があります。テストは実行していません。