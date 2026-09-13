## 所見

対象は `268ac929767a6a7e1bbf73207369bc7991c58ea6`。編集・commit・pytest は行っていません。以下の行番号はこの commit のものです。

以降、`F` は [b10_backoff_static_tail_formal.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2566-tail-formal-driver/orchestrator/campaign/b10_backoff_static_tail_formal.py)、`T` は同名の新規テストファイルを指します。

### B1 — 共通 source identity に、workload ごとに異なる点の source token を使う

- **主張:** **real**。正常な実走 cohort を identity 不一致で拒否する構造になっている。
- **根拠:** `F:672` は `resolve_evidence(genomes[0], ...).src_token` を `ccbench_source_digest` に入れる。独立に生成した最初の点は次のとおり。

  | workload | 物理値 | raw |
  |---|---:|---:|
  | write-heavy | 2500 | 4500 |
  | balanced | 1250 | 3250 |
  | read-heavy | 3535 | 5535 |

  `source_digest.py:2107` の preimage は genome の実効 defines で前処理される。`patches/silo-backoff-fixed.patch:70` の式には `BACKOFF_FIXED` 自体が現れるため、これらは異なる正規化 bytes になる。`source_digest.py:2276` の token は、この点依存性を取り除かない。`F:533` は三者の完全一致を要求する。
- **壊れ方:** 同じ checkout・toolchain の三走でも、測定順の先頭が違うだけで `cohort identity: ccbench_source_digest` になる。正例 fixture は `T:222` で全 workload に `"a"*64` を渡し、この生成経路を通さない。
- **成果物影響:** 正常な三走の集約 verdict が誤って `invalid` になる。
- **深刻度:** **高／must-fix**。

### B2 — 不正・不完全な入力ほど、要求された失敗報告へ到達しない

- **主張:** **real**。事前登録の「失敗理由と観測済み値を記述的に報告する」が、loader での拒否を覆っていない。
- **根拠:** `F:382` の未完了 cell、`F:407` の不正 rep、`F:412` の不完全な点集合などは例外になる。`F:713` は全 loader を完了してから `materialize_report` を呼び、例外を報告へ変換しない。時間切れも `F:624` の `SweepDeadline` により `F:682` の実行 receipt 発行へ到達しない。
- **壊れ方:** 一点の欠測・整数カウンタ欠損・時間切れによって、残る正常な観測も正式な失敗 report に出ない。`analyze_cohort` 内の例外処理では、その手前の失敗を拾えない。
- **成果物影響:** 本来必要な `invalid` の記述的 report と失敗理由が発行されず、観測が WAL 等に取り残される。
- **深刻度:** **高／must-fix**。

### B3 — balanced schedule では整数記録 opt-in が黙って失われる

- **主張:** **real**。共有 API が受理した新引数を、別の実行経路が消費しない。
- **根拠:** `loop.py:747` で opt-in を転送し、`:766` の balanced 分岐でも prepared object に入る。しかし `pipeline.py:2876` の測定呼出しは `record_rep_integer_counters` を渡さず、`:3031` の payload も整数 `reps` を発行しない。併用拒否も無い。
- **壊れ方:** `balanced_schedule` と `record_rep_integer_counters=True` を同時指定しても、整数記録なしの成功成果物ができる。
- **成果物影響:** 呼び手が要求した rep ごとの整数カウンタが WAL から欠落する。
- **深刻度:** **中／must-fix**。formal driver 自身はこの組合せを使わないため、既定経路の回帰とは区別する。

### B4 — 「loop 転送の probe」が loop を実行していない

- **主張:** **real**。名前と検査範囲が一致せず、M12 を保証しない。
- **根拠:** `T:309` の `test_probe_4_five_real_verifier_records_and_loop_forwarding` は、`run_campaign` の signature に `correctness` があることだけを確認する。実際の記録生成は `T:242` の `pipeline.evaluate(..., correctness=...)` 直接呼出し。
- **壊れ方:** `loop.py:745` の転送を削除しても、この probe の検査内容は変わらない。現実の driver は既定一回へ戻る。
- **成果物影響:** 実走は一 cell 一本の verify record になり、五本要求で cohort が拒否されるのに、probe がその退行を検出しない。
- **深刻度:** **中／must-fix（検証）**。現物の転送そのものは存在する。

### B5 — scheduler parser の実環境との接続は未証明

- **主張:** 保存済み実形式への未対応は **real**。新コマンドの live 成否は今回未実測。
- **根拠:** `F:637` は `qstat -f -F json` と `Jobs[id].stime` の数値を前提にする。一方、既存投入経路は `b10_backoff_grid.sh:271` で `0:` を外して `qstat -f` を実行し、`:305` で日時文字列を解析する。保存済み `output/env/pegasus/smoke/0:867860.nqsv/qstat_job.stdout:35` も `Started Request Time = Sun Jul 19 ...` という形式。
- **壊れ方:** 新しい JSON 形式の取得を実環境が提供しなければ、`run_campaign` より前に停止する。新規テストには `scheduler_coordinates` の呼出しが無い。
- **成果物影響:** 接続不成立の場合、formal campaign と実行 receipt が一件も発行されない。
- **深刻度:** **nit／接続確認事項**。`-F json` の実際の戻り値を確認していないため、確定した起動障害として must-fix には数えない。

## hash の独立検算

文書を `read_bytes()` で読み、完全一致する marker 行を探し、内側の fence 二行だけを除去しました。実装の正規表現とは別の行分割方式です。

| 対象 | 独立検算結果 |
|---|---|
| spec の範囲 | **`[33673, 60884)`** |
| spec の長さ | **27211 bytes** |
| `document_blob_sha256` | `8084be04dc1fc6a78b0fa1ac4a16986add796945d8c4ecace86ed2df4c44a45a` |
| `spec_sha256` | `08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef` |

`F:78` の実抽出関数をそのまま用いた結果とも **bytes が完全一致**しました。`F:239` は raw document bytes の SHA-256 を束縛し、Git blob ID を代入していません。hash 不一致の疑いは **refuted**。

spec の因果経路もあります。

- 格子は `F:148` で生成規則から再計算し、`:243` で seed による順列を再生成する。
- 動作点は `F:252 → :676 → pipeline.py:1360` を通る。
- 独立計算で `execution.records` を `1000000 → 1234567` にすると、実 `performance_config` の値が変わった。
- 同じ率 `[.098,.099,.100,.101,.102]` の CV は `0.015811388300841864`。spec の閾値を `.02 → .01` にすると、実 `cell_statistics` の gate が **True → False** に変わった。
- 等価幅・効果幅・持続区間数も `F:188–203` で取り出され、`:519`、`:579` に届く。

ただし全面的なデータ駆動とは言い切れません。`F:564` は anomaly を `0` に固定する一方、`:324` は spec の値を使います。`maximum_anomalies_per_rep=1` は parser が受理しました。現登録値は零なので現成果物への差はありませんが、**受理する spec と二つの consumer の解釈が一致しない nit** です。

## 既定 False の同一性

**同じ入力・外部観測を与えた場合、既定 False の production 経路は値まで従来同一と静的に判定します。実走比較を行ったという意味ではありません。**

両 runner の変更は、False なら sink の自動生成も整数 parser 呼出しも実行しません。throughput の追加順、代表 rep の選択、丸めた abort 率、notes、return codes、例外処理は変更されていません。

pipeline も False なら `_measure` の追加 kwargs と `reps` の組立てを飛ばします。既存 payload の値を計算する式は不変です。loop は新引数を非既定時だけ転送します。

三つの疑いへの回答は次のとおりです。

1. **sink 自動生成と break:**  
   **False の回帰という主張は refuted、True の挙動変更は real。** `runner.py:833` の自動生成により、遅延側の `:908`、`:933` にある `rep_observations is None` 条件は変わります。True・`require_all_reps=False` では、従来停止した一般例外でも後続 rep を捕捉しうる。通常側も `:1197` の一般例外が再送出から記録・継続へ変わります。formal pipeline は strict を立てるため、この継続には依存しません。

2. **`require_all_reps=True` の無条件設定:**  
   **formal の五本全数要求には整合し、既定 False に副作用はありません。** 一方、新 opt-in は保存だけでなく非零終了・実行失敗時の受理も厳しくします。欠測した点を従来の残存 rep の中央値で採用しないという判断は妥当です。ただし失敗前の観測の保存・報告は B2 のまま残ります。

3. **失敗 rep と index:**  
   runner 単体の非 strict 経路では、sink は元の rep index を維持し、`throughputs` は成功値だけを詰めるため、位置対応は崩れえます。**formal writer で誤対応したまま採用する疑いは refuted**。`pipeline.py:1488` の双方の長さ検査、`:1498` の index・型・値一致検査が拒否します。formal loader も `F:300` で再検査します。

焦点走の対象漏れも確認しました。

- `test_screening_opt_in.py:32` の全文検査対象に、`ScreeningConfig`／`screening=` は **ともに存在しません**。この抵触の疑いは refuted。
- 全文／AST を読む既存検査は他にもあり、`test_campaign.py:7823,8231`、`test_t674_qualification_contract_lanes.py:279`、`test_paper_story_a2_certification.py:5545`、`test_s8b_floor_campaign.py:7930`、`test_layer3_report.py:1094`、`test_official_perf_closure.py:802,816` が該当します。
- private symbol の repo 検索では、定義元以外に `_run_bench` は **5ファイル**、`_prepare_evaluation_core` は **6ファイル**、`_bench_prepared` は **1ファイル**、`_PreparedEvaluation` は **4ファイル**に参照があります。最後には `loop.py` と `manual_probes/test_t2397_a1_source.py` も含みます。
- `measure_point` の production consumer は定義元と説明のみの参照を除いて **9ファイル**。既存 family の二つの捕捉 wrapper、floor 系、calibrator sweep、`t2187_adaptive_const_probe.py` を含みます。`capture_measure_point` の production consumer は `s8b_floor_attempt_launcher.py` **1ファイル**です。

## 未更新の登録簿と、登録すべき件数

**五つすべてが、未更新なら必ず赤になる仕組みではありません。**

| 登録簿 | 現物から数えた追加 | 現時点の検査の振る舞い |
|---|---|---|
| `test_official_perf_closure.py` | `_REVIEWED_PERF_FILES` に **1ファイル**。`_REVIEWED_PREDICATES` に `load_formal_campaign → validate_perf_observation` **1 call site**（`F:396`） | `test_outer_perf_file_and_added_guard_inventory_is_exact` は未登録ファイルで赤になるはず。一方、predicate 検査は登録済み path だけを走査する（`:587`）ため、新 path 未登録のままでは見逃す |
| `test_p3_build_authority_cli.py` | `MACHINE_CALLERS` に `b10_backoff_static_tail_formal.py: BACKOFF_SWEEP` **1項目**。実 call site は context 発行 `F:657` と generator receipt 発行 `F:659` が各一つ | `test_machine_callers_use_closed_generator_receipts` は既登録項目を巡回するだけ（`:1203`）。**未登録そのものでは赤にならない** |
| 同上 manual-build 系 | **追加0件** | 新 module に `--build` は無い。`MANUAL_BUILD_FILES`／`ADMITTED_MANUAL_BUILD_FILES` を増やす根拠は無い |
| `test_ccbench_spawn_sites.py` | `_git → subprocess.run` **1件**（`F:225`）、`scheduler_coordinates → subprocess.run` **1件**（`F:637`）。計 **2 call sites** | `test_reviewed_process_launch_inventory_is_recursive_and_exact` と `test_reviewed_ccbench_measurement_launches_use_bounded_sites` は未登録差分で赤になるはず |
| `test_campaign.py` | `expected_inventory` に `(新path, campaign.loop.run_campaign): 1`。`expected_run_calls` に新 filename **1件**。対象は同じ `F:676` | `test_certified_writer_authorization_caller_inventory_is_closed` は前者で赤。合計 pin は run_campaign **20→21**、legacy raw-AST 側 **16→17**。evaluate の **5** は不変 |
| `acceptance_duration_ledger.json` | 新規テスト **47 nodeids**。AST 上は19関数、parametrize 展開後47件。現在の登録 **0件** | `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` は **90% 閾値**であり、47件未登録だけで赤になるとは断言できない |

process 在庫のキーは次の二つです。

```text
("campaign/b10_backoff_static_tail_formal.py", "<module>._git"): 1
("campaign/b10_backoff_static_tail_formal.py", "<module>.scheduler_coordinates"): 1
```

Git は既存 family の read-only Git wrapper と同じ分類、qstat は非 CCBench process として、それぞれ理由を明記して登録すべきです。**wrapper の実行回数と AST call-site 数を混同しないこと。** 所要時間は未計測値を推定登録せず、実測値を使う必要があります。

## 恒真な検査の一覧

**新規47件の中に、候補集合の定義だけで主要述語が必ず成立する厳密な恒真検査は見つかりませんでした。** 拒否検査は parser／validator を実際に呼び、数値検査には独立した期待値があります。親の集計だけでは個別の39件の成功 nodeid は確定できないため、以下を「実測済みの緑」とは追加認定しません。

ただし保証範囲の弱さはあります。

- **派生値の pin:** `test_probe_1_spec_binding_and_production_configuration`（`T:42`）は格子・PerfConfig・search_config を検査しますが、`run_workload` の identity 生成・scheduler・実発行は検査しません。B1 を見逃します。
- **正例の生成器を迂回:** `test_analyze_cohort_complete_production_positive_and_two_mutants` は writer を通しますが、source identity は `"a"*64`、binary digest は fixture が設定し、実行 receipt も `T:245` で直接作ります。両側がこの fixture 値に追随しても通るため、実 driver が同じ正例を生成できる証明にはなりません。
- **配線を迂回:** `test_probe_4_five_real_verifier_records_and_loop_forwarding` は B4 のとおり。signature の存在を、転送の実効性へ読み替えられません。
- **限定された数値正例:** `test_interval_zero_and_dispersion_precedence` はゼロ・分散零を検査しますが、正分散時の区間計算から持続飽和・集約 verdict までを保証しません。Student-t の四つの参照値検査も、その結合経路の代わりにはなりません。
- **記録形式の pin:** `test_layer3_report.py:1092` の AST 検査は key 集合を閉じますが、False 時の payload の**値**の同一性や、True が balanced 経路へ届くことは保証しません。

## 投入経路の穴の形

現物には、Python CLI の `run` と `report` が存在します。`report` は三つの campaign path を明示指定すれば loader と materializer へ進む入口です。`run` は workload 一つを受け、設定生成・事前ビルド・`run_campaign`・実行 receipt 発行を意図しています。

しかし既存の運用入口では、

1. `submit_b10_backoff_grid.sh:36` が旧三 run kind 以外を拒否する。
2. `b10_backoff_grid.sh:186` も同じく拒否する。
3. 拒否だけを越えても、`:587` の実行対象は旧 `backoff_extended_sweep.py` のまま。
4. `:627` 以降の完了検査は旧 campaign／report stem を期待する。
5. 三 job を新しい `report` CLI へまとめて渡す投入側の入口が無い。

したがって、**新 consumer の Python 入口は存在するが、既存の三 job 投入・完了確認・cohort 集約からは到達できません。** さらに、この scope 外の配線を仮に満たしても、B1・B2 と scheduler 接続の未証明は Python 側に残ります。

## 総括

hash の対象 bytes と二つの SHA-256 は独立検算で一致しました。  
既定 False の値を変える production 回帰は、今回の差分からは見つかりませんでした。  
ただし実 driver の source identity 生成には、正常 cohort を拒否する欠陥があります。  
失敗入力の報告欠落、balanced opt-in の消失、loop 転送 probe の迂回も real です。  
登録簿の追加は上記件数で必要ですが、未登録を必ず赤にする検査ばかりではありません。  
**39 passed を、実 driver の完走・受理・失敗報告の保証には数えられません。**