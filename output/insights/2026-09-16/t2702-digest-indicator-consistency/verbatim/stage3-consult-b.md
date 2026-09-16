## 所見

本段は静的読解と具体的反例による相談結果。ファイル変更・pytest・変異実行はしていない。以下の `plan-v1.md` は指定された親の plan を指す。

1. **real — 奇数 tie-break の変異を、指定 fixture では検出できない。**

   **根拠:** `plan-v1.md:110,138` は `[200,100,200]` で「stable sort 後の中央要素」への変異が赤になるとしている。しかし rep に実行 index を付けると、整列結果は `[(100,1),(200,0),(200,2)]`。中央は index 0 であり、現行の `min(..., key=abs)` と同じである（`orchestrator/calibrator/runner.py:1055,1292-1294`）。abort/counters を非単調にしても、選ばれる rep が同じなので検出できない。

   `[200,200,200]` にして各 rep の指標を変えれば、現行は index 0、変異は index 1 となる。あるいは `[200,200,100,300,200]` なら現行 index 0、整列中央 index 1 となる。

   **放置時の成果物への影響:** 奇数有効 reps の WAL・レポート値を変える実装が通過し、「bytes 不変」の変異裏取りが成立しない。

   **推奨: 採用。** 同値 fixture を差し替える。さらに、相異なる throughput の奇数 fixture と「中央から上側へずらす」変異を対応させ、中央選択と同値 tie-break を別々に検証する。

2. **real — (a) の解消は通常 digest に限られ、8c の役割入力には latency が残る。**

   **根拠:**
   - `orchestrator/campaign/p3_s4_loop.py:1162` は `render_text(build_digest(...))` を使う。`orchestrator/critic/digest.py:779,1186,1264-1280` は `INDICATORS` に追随するため、plan で列・軸から除去できる。
   - `orchestrator/critic/online_digest.py:45,57` も同じ処理を使う。この経路が修正漏れになる懸念は **refuted**。
   - `orchestrator/campaign/p3_autonomous_workload_trial.py:1994-2009,2020-2029` は WAL を直接読み、`latency_ns` を役割 payload に再掲する。
   - `orchestrator/campaign/s8c_generation_projection.py:58-81` は latency を perf・source・diagnostic の列挙に含む。
   - `orchestrator/campaign/autonomous_trial_completeness.py:435-440` もその契約を保持する。これは表示元ではないが、8c 側だけ列を削除する変更は整合しない。
   - `orchestrator/campaign/backoff_sweep_report.py:83-87,187` は throughput/abort/ipc のみで、(a) の残存経路ではない。

   **放置時の成果物への影響:** 通常 critic のテキストは改善する一方、8c の planner/coder/critic 入力では冗長な latency 信号が残る。

   **推奨: scope 外の裁定パッケージ候補。** 閉列挙契約を勝手に変更しない判断は妥当。ただし「本題の二点だけ」は変更する問題の限定であって、同じ欠陥が残る経路を解消済みとする根拠にはならない。完了報告を「通常 digest と今後の runner 集約」に限定し、8c と role 文書の残件を明記する。

3. **real — runner の変更は過去 WAL と T-2588 の人手射影を修復しない。**

   **根拠:** `orchestrator/critic/digest.py:768,779` は保存済み `leading_indicators` を読み、rep から再集約しない。指定の `t2588-findings-verbatim.md` には throughput `719324.5`、速い側 rep `727985`、latency `5494.6187`、人手射影した abort `7.75%` が記録されている。plan の変更には既存記録の再計算経路がない。

   したがって、過去 WAL から再生成した通常／online digest は latency 列こそ消えるが、旧代表 rep の abort 値を引き続き表示する。人手の `current_perf` も自動では更新されない。新規測定では、中央両 rep に値がある場合、案 A の abort 集約が downstream に届く。

   **放置時の成果物への影響:** 新旧集約方式のレポートが併存し、T-2588 の `7.75%` を修正後の集約値として再利用すると誤る。

   **推奨: 採用。** 完了条件の適用を今後の測定に限定する。過去成果物の書換えは不要だが、「再表示しただけでは (b) は直らない」と引継ぎに明記する。

4. **real — baseline も変更されることを考慮しても、certified 到達集合は不変ではない。規律 2 の迂回になる懸念は refuted。**

   **根拠:** `orchestrator/campaign/screening_driver.py:491-512` は新規 baseline の WAL abort を screening に設定する。候補側だけを変更する比較では不十分である。ただし両側を同じ規則で集約しても比率は保存されない。

   具体的反例として、throughput 順の abort を baseline `(.1,.1)`、候補 `(.1,.5)`、`high_abort_factor=4` とする。旧方式は `.5 > .1×4` で high-abort、新方式は `.3 <= .1×4` で high-abort でなくなる。候補 throughput が棄却閾値未満かつ stable なら、verify 送りから screen-reject へ変わる。候補を `(.9,.1)` とすれば逆方向も作れる。

   分岐は `orchestrator/campaign/pipeline.py:2366-2375`。screen-reject は明示的な uncertified reject（`:2377`）。通過側も verify を実施し、成功後にのみ `res.certified=True` となる（`:2388-2440`）。

   **放置時の成果物への影響:** 同じ raw rep でも screen-reject／verify 到達、certified 記録の有無、後続選択が変わり得る。未検証候補を certified にする変更ではない。

   **推奨: 採用。** 「verdict 不変」を verifier 自体の判定規則に限定する。上の両方向の境界を、baseline も集約する fixture で確認する。screening を改変して旧結果に合わせる必要はない。

5. **real（規則上）／未実測（実環境の大きさ）— 早い中央 rep の採用は warm-up 偏りを除去しない。**

   **根拠:** `orchestrator/calibrator/model.py:38-51,95-100` は選ばれた counters から LLC miss rate と IPC を直接算出する。例えば二反復が次なら、

   | 実行順 | throughput | LLC miss rate | IPC |
   |---|---:|---:|---:|
   | 先 | 100 | .4 | .5 |
   | 後 | 200 | .1 | 2 |

   案 A の digest 行は throughput `150`、LLC `.4`、IPC `.5` になる。「throughput の高低を直接優先しない」は正しいが、「throughput 方向の系統偏りを持たない」は実行順と性能が相関する場合には成立しない。実際にこの warm-up が存在するか、その大きさは本段では未実測。

   なお、CCBench は各 rep を別プロセスで起動する（`runner.py:663`）。ここで問題になるのはプロセス間に残る cache・温度等の順序効果であり、存在を自明とはしない。

   **放置時の成果物への影響:** perf が有効な環境では、throughput/abort と LLC/IPC の行内集約差が残り、機序帰属に実行順の影響が混ざり得る。

   **推奨: 採用。** 案 A は限定的な決定規則として採用可能だが、無偏の主張は削る。単一 rep を必ず選ぶ制約下では、後側固定・hash 選択にも一般的な無偏保証はない。中央二反復の counter 比率集約は別の意味変更なので、必要なら scope 外の裁定パッケージ候補とする。

6. **real — producer 列挙には追加漏れがある。ただし s8b の偶数固定値は確認できない。**

   **根拠:** 親が訂正済みの二経路に加え、`orchestrator/campaign/pegasus_floor_scoping.py:37,143-148` も `WITHIN_REPS=10` を使い、`:162` で代表 abort を成果物に保存する。呼出元は `tools/pegasus/floor_scoping.sh:307`。floor は raw throughputs から計算するので不変だが、記録 abort は変わる。

   また calibrator の既定は `sweep_reps=3, noise_reps=10`（`orchestrator/calibrator/sweep.py:154-155`、`cli.py:151-152`）であり、「calibrator は reps=5」は API の既定と実 driver 設定の混同。

   `s8b_experiment_numbers.py:15` は `APPROVED_REPS=5`。floor と oracle はその値を参照・検査する（`s8b_floor_campaign.py:1319`、`s8b_oracle_manifest.py:445`）。今回の検索では本番 `reps=4` producer は確認できず、`test_calibrator.py:657` の 4 はテスト用。

   凍結・pin は区別が必要である。
   - calibration 成果物には実際に path/SHA pin がある（`env_contract.py:261-279,301-306`）。runner を変えても既存 JSON 自体は変わらないので、これだけで pin 破損とはならない。
   - Pegasus scoping は repository 外への出力を要求する（`pegasus_floor_scoping.py:107-117`）。その外部成果物の凍結有無までは未確認。
   - `output/s8b-freeze/holdout_freeze.json:95-105` の `between_run_floor.py` は検索の `hit_paths` であり、producer の bytes pin を示す項目ではない。

   **放置時の成果物への影響:** 変更対象となる記録 abort の範囲を過小報告する。一方、floor 値や既存 pinned JSON の破損を断定する根拠はない。

   **推奨: 採用。** producer 一覧を補正し、「ソース pin」「成果物 pin」「数値計算への影響」を分けて報告する。

7. **refuted — 新 fixture が deferred 経路に届かないという懸念。ただし既存 fixture は集約回帰の証拠にならない。**

   **根拠:** `plan-v1.md:91-104` は `kwargs["text"]` に応じた bytes 化、API ごとの iterator 初期化、`capture_measure_point(...).open()` を明記する。実際の spawn は `runner.py:663`、deferred の解析は `:698-734`、集約は `:1050-1060`。通常側は `:1287-1304`。この設計なら両方を通せる。

   一方、`test_calibrator_deferred_output.py:197-207` の二反復は同じ `_completed()`、throughput は `[1000,1000]`、maxrss は双方 `100`。これは上側選択・平均・早い側選択を区別できない。新 fixture の代用にはならない。

   **放置時の成果物への影響:** 新規の異値 fixture を省くと、一方の経路だけ旧集約を残しても既存 deferred テストが緑になり得る。

   **推奨: 採用。** plan の両 API 実行を維持する。API ごとに別 node にすると、片側失敗で他方が未実行になる問題も避けられる。

8. **real — 変異の「赤」と DW-M03/DW-M08 の kill を区別する必要がある。**

   **根拠:** `docs/dev-wave/mutation.md:18-20,61-62` は診断文字列だけの赤を kill とせず、受理集合を変えない構造化シグナルの検査を `diagnostic sensitivity pin` に分ける。plan の latency 再導入、latency 平均、resource 選択の焦点テストは主として表示・構造化値の検査であり、certified 受理集合の変化を観測していない。abort は screening に実効性があるが、単なる `.4` 対 `.6` の assert だけではそこまで証明しない。

   また `plan-v1.md:124` の「手書き WAL fixture の latency が残る」確認は、reader が WAL を変更しないことの確認であり、producer が今後 latency を保存することの独立な証拠ではない。producer の五 key は既存 `test_calibrator.py:165-174` と役割を分けるべきである。

   **放置時の成果物への影響:** 変異台帳で表示感度の証拠を受理集合の防護証拠として過大計上する。

   **推奨: 採用。** 診断感度の変異は別枠で登録する。abort の実効 kill を主張するなら所見 4 の screening 境界まで観測する。

## 変異候補への判定

以下は静的判定であり、実装後の注入・失敗 node 確認は未実測。

| plan の候補 | 単一理由性・検出力 | 判定 |
|---|---|---|
| resources を上側 rep 固定へ戻す | 早い側が下側の fixture なら resource 選択だけが変わる。逆順 fixture も必要。counter の欠損を避ければ前段 parser による拒否は不要 | **採用**。診断感度として記録 |
| abort 平均を上側へ戻す | `.4 → .6` で独立に赤。latency/resources を変更しなければ単一理由 | **採用**。受理集合の証拠には screening fixture を追加 |
| latency 平均を上側へ戻す | `17M → 14M` で独立に赤。CCBench の式との一致を parser が要求する経路ではないため、合成値で集約を隔離できる | **採用**。診断感度として記録 |
| 奇数を整列中央の直接採用へ | 指定 `[200,100,200]` では同じ rep を選ぶため赤にならない | **現 fixture は不採用**。全同値などへ差替え |
| 片側 None を常に None にする | `require_complete_metrics=False` かつ abort counts fallback を除けば、欠損が helper まで届き単一理由にできる | **条件付き採用**。field ごとに分けると帰属が明確 |
| `INDICATORS` に latency 再導入 | 射影 key 集合と表・軸が変わる。複数 assert は同じ原因の downstream 観測であり、それ自体は別の拒否層ではない | **採用**。診断感度として記録。単なる `KeyError` を期待赤にしない |

追加すべき候補は次の三つ。

- **奇数の中央選択をずらす変異:** 相異なる三反復で中央 rep の選択自体を独立に検証する。
- **片方の呼出経路だけ helper 使用を外す変異:** 通常／deferred の配線を独立に検証する。
- **有効数でなく要求 reps の偶奇を使う変異:** 要求 5・有効 4 と要求 4・有効 3 を置き、親の訂正が実装に反映されることを検証する。

既存 deferred の同値 fixture は今回の選択規則に対して不変であり、検出力の根拠から外す。「どの実装でも緑」とまでは言えないが、今回比較する集約方式を区別しない。

## 総括

案 A と通常 digest の修正方針は採用可能だが、奇数 tie-break の指定変異 fixture は修正必須。
8c の latency 提示と過去 WAL の旧 abort 値は残るため、全面解消とは報告できない。
baseline も再集約してなお screening 到達集合は変わり得るが、verify 必須という規律 2 は維持される。
producer の追加漏れと warm-up に対する保証範囲を補正し、診断感度と実効 kill を分ける。
本段では変更・pytest・変異実行を行っていない。
