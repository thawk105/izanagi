## 前提の検証

指定された射影 9 ファイルはすべて読み取り可能。以下は静的読解による計画であり、ファイル変更・pytest 実行はしていない。行番号は現状のソースを指す。

- **latency の出所は正しい。** `external/ccbench/common/result.cc:52-56` は throughput と `1e9 * thread_num / throughput` を出力する。ただし分子の正確な定義は通常 commit 数と batch commit 数の合計である。
- **2 経路の名称が brief と逆。** `runner.py:1050-1060` は `capture_measure_point` 内の `open_measurement_point`、`:1287-1304` が通常の `measure_point`。いずれも偶数有効 rep 数では上側 throughput を選ぶ。
- `model.py:83-87,236-242` の throughput は真の中央値。`:95-101` の leading indicators は 5 key を持ち、abort_rate / latency_ns は保存済み field をそのまま返す。
- **奇数時の互換性に例外がある。** 現行は中央 throughput と同値の rep のうち、実行順で最初を選ぶ。「stable sort 後の中央要素」へ置換するだけでは、同値 rep がある場合の bytes が変わる。
- **既存テストの赤は 2 件ではなく 4 件。** `test_critic.py:667,683` に加え、`:729-732,803` の辞書全体比較も変更対象。

consumer ごとの確認結果は次のとおり。

| consumer | 確認箇所 | latency を `GenomeLI.li` から落とした影響 |
|---|---|---|
| 通常 critic digest | `p3_s4_loop.py:1141-1162` | `render_text` が生成する列・軸行が減る。固定列の数値パーサではない |
| closed critic | `p3_b4_closed_critic.py:478-498,923-930` | `projected_digest` は文字列。payload の key 集合は変わらない |
| online digest | `online_digest.py:45-57` | `build_digest` と `render_text` に追随。genome 数の検査は影響なし |
| wiring probe | `p3_b4_wiring_probe.py:1677` | 同じ renderer を使うため追随 |
| `GenomeLI.li` 直読 | `backoff_sweep_report.py:83-87,187-189` | throughput / abort_rate / ipc のみ参照。欠落による破損なし |
| WAL 直読・layer3 | `pipeline.py:1455-1468`、`layer3_report.py:315` | `ScalePoint.leading_indicators()` を変えないため 5 key を維持 |
| 8c 射影・b10 | `s8c_generation_projection.py:61,78-81`、`backoff_extended_sweep.py:1013,1104` | latency key は残る。偶数有効 rep 数では値の意味が変わる |

追加で、brief が列挙していない **`pipeline.py:2366-2373` の bench-first screening が abort_rate を読む**。これは設計上の懸念で後述する。

## 変更計画 (file:line 粒度)

**1. `orchestrator/critic/digest.py`**

- `:7-8`：指標列挙から latency を削除。
- `:11-13`：帰属例を、例えば「BACK_OFF 0→1 で throughput と abort_rate がともに低下した場合、abort 低減だけでは性能改善を説明できず、cache miss / IPC も調べる」に変更。観測だけで機序を断定する文にしない。
- `:62-64`：`INDICATORS` と `HIGHER_IS_BETTER` から `latency_ns` を削除。残る順序は throughput、abort_rate、llc_miss_rate、ipc。
- `:1220-1221`：`_fmt` の latency 専用分岐を削除。
- `:779` の辞書射影、`:1186-1191` の軸集約、`:1264-1268` の表、`:1273-1280` の軸描画は変更不要。いずれも `INDICATORS` に追随する。WAL の latency を削除する処理は加えない。

**2. `orchestrator/calibrator/runner.py`**

`:803` の `capture_measure_point` より前に、private helper `_summarize_rep_results(rep_results)` を 1 つ置く。返値は既存の代入に対応する次の 5 要素とする。

```python
(counters, walltime_s, maxrss_kb, abort_rate, latency_ns)
```

helper の処理は以下に限定する。

1. `enumerate(rep_results)` から throughput が `None` でないものを抽出。元の index を保持する。
2. 有効 rep がなければ、現行どおり `rep_results[-1][1:]` を返す。空リストは既存の呼出元の例外処理で排除済み。
3. 有効数が奇数なら、`_median` で中央 throughput を求め、**現行と同じ `min(..., key=abs(tps-median))`** で元順序から代表を選ぶ。その `rep[1:]` を加工せず返す。
4. 有効数が偶数なら、throughput を key とする stable sort から中央 2 rep を採る。
5. counters / walltime / maxrss は中央 2 rep の元 index が小さい側から採る。tuple 全体の比較や `list.index` は使わない。
6. abort_rate と latency_ns はそれぞれ中央 2 rep の値を取り、`None` を除いた 1～2 個に `_median` を適用する。空なら `None`。2 個の `_median` は算術平均なので案 A と一致する。

`runner.py:41` の model import に `_median` を追加する。`model.py:236-242` は変更しない。

helper を runner に置く理由は、入力 tuple と実行順が runner 内部の表現であり、model に subprocess 集約の規則を持ち込む必要がないため。critic の `_mean` は import しない。既存 `_median` の再利用なら層をまたぐ追加依存も不要。

置換箇所は次の 2 か所。

- `:1050-1060`：helper の返値を `pt` の 5 field に代入。
- `:1287-1304`：同じ返値を `point` の 5 field に代入。

両者とも、直前の全失敗判定、直後の `rep_observations` コピーを維持する。deferred 側では helper 呼出しを必ず `open_measurement_point` 内に残す。

throughputs の蓄積順、例外処理、strict mode、完全性検査、returncodes、timestamps、raw counter 証跡、fitness 計算、verifier は変更しない。

**3. 編集範囲**

実装は `digest.py`、`runner.py`、テストは `test_critic.py`、`test_calibrator.py` の計 4 ファイルで足りる。deferred API の新規集約テストも `test_calibrator.py` に置き、既存 `test_calibrator_deferred_output.py` は回帰確認に使う。docs 編集・commit は author の担当外。

## テスト計画

**赤になる既存 assert の全列挙**

| file:line / 関数 | 赤になる理由 | 修正 |
|---|---|---|
| `test_critic.py:667` / `test_load_sorts_by_throughput_and_marginal_back_off` | `bo.means["latency_ns"]` が消える | latency 不在を断言。`:647` の誤った帰属コメントも修正 |
| `:683` / `test_no_wait_axis_is_categorical_LT` | `nw.means["latency_ns"]` が消える | latency 不在と abort_rate の L=0.40、T=0.50 を断言 |
| `:729-732` / `test_load_workload_uses_committed_retry_attempt_only` | 期待辞書に latency が残る | 期待値を明示的な 4 key にする |
| `:803` / `test_load_workload_preserves_legacy_commit_without_build_attempt_id` | WAL の 5 key と射影後の 4 key を比較している | 期待値を明示的な 4 key にする |

WAL fixture の latency 値は残す。期待辞書を実装の `INDICATORS` から組み立てると、latency 再導入の変異を見逃すので避ける。

`test_calibrator.py:165-174` の `test_scalepoint_leading_indicators` は変更不要。WAL 用 5 key を維持することの既存確認になる。指定された calibrator の 2 テストファイルには、今回の集約変更で必然的に赤になる既存 assert は見当たらない。

**新規 fixture の作り方**

`test_calibrator.py:453-458` の `_completed_process(returncode, stdout=...)` を再利用する。`:645-654` の既存例と同様、closure 内の呼出回数または iterator で rep ごとに異なる stdout を返す。

```python
outputs = iter(rep_stdout_strings)

def fake_run(argv, **kwargs):
    stdout = next(outputs)
    if not kwargs["text"]:
        stdout = stdout.encode("utf-8")
    return _completed_process(0, stdout=stdout)
```

通常 API は `measure_point(...)`、deferred API は `capture_measure_point(...).open()`。各 API の実行前に iterator を作り直す。単純な指標テストは `use_perf=False` を使う。

stdout は `throughput[tps]`、`abort_rate`、`latency[ns]`、`maxrss` を明示する。None fixture では対象行を省略し、abort の欠損時は abort/commit counts の fallback も成立させない。counter の選択を確認する場合は既存例どおり `argv` の `-o` に rep ごとに異なる perf CSV を書く。

**新規テスト：すべて `orchestrator/tests/test_calibrator.py`**

各テスト内で通常・deferred の両 API を通す。

| 関数名 | fixture と期待値 |
|---|---|
| `test_measure_point_even_reps_average_central_indicators` | 実行順 `(tps, abort, latency)` を `(400,.9,10M),(100,.8,40M),(300,.6,14M),(200,.2,20M)`。throughputs は元順序、throughput=250、abort=.4、latency=17M。2 reps の `(200,.2,20M),(300,.6,14M)` も確認 |
| `test_measure_point_even_reps_keep_earlier_central_resources` | 中央 rep の実行順を両方向で試す。maxrss と perf counters を rep ごとに変え、早い側をそのまま採ることを確認。walltime は時計を固定して同様に確認 |
| `test_measure_point_odd_reps_preserve_legacy_bytes` | 1・3・5 有効 reps、非単調な abort 値、さらに throughput `[200,100,200]` の同値ケース。後者は最初の 200 rep を採る。時計を固定し、固定期待 `ScalePoint` と `dataclasses.asdict` の JSON bytes を比較。新 helper を期待値計算に使わない |
| `test_measure_point_central_indicators_handle_none` | 中央 2 rep の各 field について `(None,x)`、`(x,None)`、`(None,None)`、`(0,x)`。期待値は x、x、None、x/2。外側 rep に値を置き、中央外から補完しないことも確認 |
| `test_measure_point_summary_uses_valid_reps_and_preserves_fallback` | throughput 欠損 rep を除いて中央を選ぶ。有効 0 件なら最後の解析成功 rep の 5 field を保持。全実行失敗は既存例外のまま |

奇数 bytes 比較では、実測壁時計や timestamps の自然変動を比較対象に混ぜない。固定入力・固定時計で従来の選択結果を明示する。

**新規テスト：`orchestrator/tests/test_critic.py`**

`test_digest_omits_latency_from_projection_table_and_axes` を `:806` 付近に追加する。

- `_tmp_layout`、`_write`、`_view` で BACK_OFF の異なる committed genome を 2 件作る。
- WAL には latency を含む 5 指標を保存する。
- `GenomeLI.li` と全 `AxisEffect.means` が明示した 4 key であることを確認。
- `render_text` のヘッダーが `genome | throughput_tps | abort_rate | llc_miss_rate | ipc` で、テキスト全体に `latency` がないことを確認。
- WAL の `bench_done.leading_indicators.latency_ns` は残っていることを確認。
- `HIGHER_IS_BETTER` も明示した 4 key の期待辞書と比較する。

受入時は既存の正しさ・失敗伝播・deferred 封印テストを含めて確認する。実行は親の環境規律に従い `tools/run_tests.py` 経由。本段では実行していない。

## 変異候補

各変異は単独適用し、指定の焦点テストで評価する。

| 位置（file:function） | 変異内容 | 赤になる test 関数 | 赤理由を 1 つに絞る根拠 |
|---|---|---|---|
| `runner.py:_summarize_rep_results` | resource 用代表を早い中央 rep から上側 throughput rep 固定へ戻す | `test_measure_point_even_reps_keep_earlier_central_resources` | abort/latency の平均処理を変更せず、早い側が下側の fixture で resource 選択だけが違う |
| 同上 | abort_rate の平均を中央上側の値に戻す | `test_measure_point_even_reps_average_central_indicators` | throughput・latency・resources は保持し、abort の期待 .4 に対し .6 だけが違う |
| 同上 | latency_ns の平均を中央上側の値に戻す | 同上 | abort には触れず、latency の期待 17M に対し 14M だけが違う |
| 同上 | 奇数時を整列後中央要素の直接採用へ変更 | `test_measure_point_odd_reps_preserve_legacy_bytes` | 同値 throughput `[200,100,200]` で従来の最初の rep を保持しなくなることだけを検出 |
| 同上 | 片方 None なら無条件に None を返す | `test_measure_point_central_indicators_handle_none` | 両値あり・両欠損の挙動を変えず、片側欠損時の規則だけが違う |
| `digest.py:INDICATORS` | `latency_ns` を再挿入する | `test_digest_omits_latency_from_projection_table_and_axes` | WAL fixture は同じで、除外対象の指標が射影・表示へ戻ることだけを検出 |

## 設計上の懸念

**(P1) 案 A を採る。ただし奇数時は現行 tie-break を維持する。**

B は単一 rep のまとまりを保持でき、実在した観測値として解釈しやすい。一方、偶数時の abort/latency は片側の値に留まり、throughput と同じ中央 2 rep の演算にはならない。C は各指標自身の中央値として説明しやすいが、指標ごとの rep 対応を失い、奇数時も変わる。この課題には A が適合する。

A にも次の限界が残る。

- counters 由来の IPC / LLC miss rate は単一 rep。行全体が同じ集約方式になるわけではない。
- abort 比率の算術平均は、合算 abort 数を合算試行数で割った比率とは異なる。
- 平均 latency は、平均 throughput の逆数ではない。WAL に残る偶数時の latency を「単一代表 rep の値」と説明してはいけない。
- 「実行順が早い」は throughput の高低を直接優先しないが、時間ドリフトに対して統計的に無偏とは保証できない。

**(P2) role 文書は変更しない。**

author の許可範囲と brief に従う。ただし `critic.md:14,26-27`、`critic-experiment.md:36-38` の説明は生成される digest と不一致になる。親への既知残件とし、文書を据え置いたことだけでアーム条件全体が不変とは主張しない。

**(P3) None 規則は採用するが、「同じ rep 集合」の例外を明記する。**

片側欠損時は残る側を保持し、0 を欠損扱いしない。両側欠損時のみ None とする。これは情報を残す方針だが、throughput が 2 rep、abort が 1 rep というケースは残る。「同じ rep 集合・同じ演算」は両値が存在する場合の保証になる。新 gate は加えない。

**brief の修正が必要な前提**

1. 2 経路の名称が逆で、通常側の代入終端は `:1304`。
2. 既存赤 assert は 4 件。
3. 奇数の stable-sort 中央選択だけでは同値時の互換性を守れない。
4. 偶奇は要求 `reps` ではなく**有効 throughput の個数**で決まる。要求 5 reps でも 1 件失敗すれば案 A の変更対象になる。「奇数 reps の bytes 不変」は、有効数が奇数の runner 集約結果に限定しないと矛盾する。digest bytes 自体は latency 列除去により変わる。
5. `pipeline.py:2366-2373` の screening consumer が欠落している。abort 平均化で high-abort 判定を跨ぐと、screen reject／verifier 到達の結果が変わり得る。**verifier の判定規則と fitness の計算式は不変だが、pipeline の全 outcome 不変までは保証できない。** 親は「verdict 不変」の対象をこの区別に沿って整理する必要がある。author が screening を別途改変して帳尻を合わせることは提案しない。

## 総括

latency は digest の射影・表・軸から除去し、WAL の key は保持する。
案 A の集約を runner の helper 1 つに寄せ、両経路で使う。
奇数有効 reps の同値 tie-break と、欠損時・失敗時の既存挙動を保つ。
既存 assert 4 件を更新し、偶数・奇数・None・両 API を固定 fixture で検証する。
親への重要な補正点は、奇数 bytes 保証の範囲と screening outcome への影響である。
