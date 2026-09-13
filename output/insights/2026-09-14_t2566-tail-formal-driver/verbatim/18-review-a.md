## 所見

対象は統合 commit `268ac9297`。以下は静的読解による判定です。編集・テスト実行はしていません。

### 1. cohort 正例は loader で拒否され、非 invalid 到達性を証明できない — real

- **主張:** 完全 cohort の正例に、loader が必須とする `perf_observation` がありません。
- **根拠 (file:line):** `orchestrator/tests/test_b10_backoff_static_tail_formal.py:242` の `evaluate()` は `perf_preflight_receipt` を渡していません。既定値は `pipeline.py:2621` の `None`。`orchestrator/calibrator/perf_preflight.py:342` はこの場合 observation を生成せず、`pipeline.py:1480` も WAL key を追加しません。一方、`orchestrator/campaign/b10_backoff_static_tail_formal.py:396` は無条件に検証し、`perf_preflight.py:376` が `None` を拒否します。
- **壊れ方:** 正例の `_emit_campaign()` → observation のない WAL → `_positive_cohort()` 内の loader が例外 → `analyze_cohort()` の期待 verdict 検査へ到達しません。先行する別の失敗がなくても、この切断が残ります。
- **成果物影響:** 完全な正常 cohort から formal report を生成できるという受入条件 A1 が未充足のままになります。
- **深刻度:** **must-fix**

### 2. records の因果試験が replay の実行経路へ接続されていない — real

- **主張:** spec の変更を argv で観測する試験は、注入した `subprocess_runner` が呼ばれる条件を満たしていません。
- **根拠 (file:line):** `orchestrator/tests/test_b10_backoff_static_tail_formal.py:201` は `require_all_reps`・`require_complete_metrics`・`rep_observations` を指定していません。通常測定側の `orchestrator/calibrator/runner.py:1157` は、そのいずれかが有効な場合だけ `subprocess_runner` を `run_once()` へ転送します。`run_once()` の既定は同ファイル `:589` の実 `subprocess.run` です。
- **壊れ方:** spec の records を変更 → replay が呼ばれず、`/fixture/ycsb.exe` を含む実コマンドの起動経路へ入る → 意図した argv 証跡を取得できません。さらに試験 `:202–203` の `all(...)` は、`seen` が空なら両方とも真です。
- **成果物影響:** spec を無視して records を固定する実装を検出する、採用済み受入条件 B2／変異 M7 の証拠が成立しません。
- **深刻度:** **must-fix**

### 3. loader 段の失敗では invalid report と観測値の開示が生成されない — real

- **主張:** §7 の失敗条件の一部が、`invalid` として報告されず例外終了します。
- **根拠 (file:line):** `orchestrator/campaign/b10_backoff_static_tail_formal.py:713` は全 loader の成功後にだけ `:714` の materializer を呼びます。loader は `:395` で正しさ、`:409` で整数 rep を検査し、不適合を例外にします。ここに失敗結果を収集する処理はありません。
- **壊れ方:** 整数カウンタが欠けた formal campaign → `performance_reps()` が拒否 → CLI が materializer 前に終了 → §7 が要求する失敗理由付きの記述的 report が出ません。
- **成果物影響:** 不適合標本は受理されませんが、観測済みの値と失敗理由を残す formal report／完了成果物が欠落します。
- **深刻度:** **must-fix**

### 4. 「loop forwarding」試験は loop を実行していない — real

- **主張:** probe 4 は反復の実 writer を検査しますが、名前にある転送の挙動を検査しません。
- **根拠 (file:line):** `orchestrator/tests/test_b10_backoff_static_tail_formal.py:309` の試験は、`:311` で signature を見るだけです。`:312` から呼ぶ `_emit_campaign()` は `:242` で `pipeline.evaluate()` を直接呼びます。
- **壊れ方:** `orchestrator/campaign/loop.py:745–746` の転送だけを削除し、signature を残す → この試験は変更を観測しません。実 driver は既定の正しさ 1 回へ戻り、formal loader が拒否します。
- **成果物影響:** 5 本を発行できない退行が probe 4 に検出されず、実走後の cohort 拒否として現れます。
- **深刻度:** **must-fix**

## 非 invalid 結末の到達性

**正例の現物はありますが、実際に非 `invalid` を返す正例としては成立していません。**

`test_b10_backoff_static_tail_formal.py:263–290` は、3 workload × 8 cell、性能・正しさ各 5 rep を production writer で組み、literal `indeterminate-in-region` を要求しています。しかし所見1により loader で止まります。実走による到達確認も今回していません。

解析本体については、次を確認しました。

- `b10_backoff_static_tail_formal.py:533` の跨 job 比較は spec の列挙項目を使用し、workload 座標を含みません。自身の workload 行との比較は `:543` に分離されています。
- `:587–588` は §4.5 の順序で最初の一致を採ります。失敗が他の結末に優先します。
- 正例の数値 `abort=100, commit=900, throughput=1000000` が各 5 回なら CV は両方 0。正値・分散なしのため `:511–513` から `indeterminate-in-region` になる構成です。
- 他の結末をコード上で到達不能にする条件は見つかりません。ただし、このテストファイルには全 aggregate verdict を通す正例はありません。

## 既定 False の同一性

**同じ入力・同じ外部結果に対する payload key 集合、値の計算、失敗時分岐は、静的には従来と同一です。**

経路は `loop.run_campaign()` → `pipeline.evaluate()` → `_prepare_evaluation_core()` → `_bench_prepared()` → `_run_bench()` → `runner.measure_point()` です。

- `loop.py:747` と `pipeline.py:2506` は opt-in 時だけ転送します。
- `_run_bench()` の `rep_observations=[]` と `require_all_reps=True` の追加は `pipeline.py:1345` の内側です。
- 通常／遅延 runner の自動 sink 生成は、それぞれ `runner.py:1101`／`:833` の opt-in 内です。False で例外処理や return-code 処理を変える追加はありません。
- payload の既存値を作る `pipeline.py:1455–1485` は変更されていません。新 key の発行は `:1486` の内側です。

したがって、**False でも失敗時挙動が変わるという疑いは refuted**。ただし実行時間などの揮発値の実走一致を証明したものではありません。

## 恒真な検査の一覧

| 検査 | 判定 |
|---|---|
| `test_b10_backoff_static_tail_formal.py:202–203` の `all(...)` | **real。** 空の `seen` に対して恒真。所見2の転送欠落と組み合わさっています。 |
| `b10_backoff_static_tail_formal.py:314` の再計算率 `[0,1]` 検査 | **real・nit。** `:310` の非負整数・正の和と `:313` の式から含意されます。独立した防壁の証拠にはなりませんが、現状の成果物を誤らせません。 |
| probe 4 の loader 後の「5 本・全 certified」検査 (`test_…py:314`) | loader の `:320–324` が成功すれば含意されます。ただし上流 writer が5本を発行する検査としては意味があります。**loop 転送の証拠にはならない**点が所見4です。 |

「両側を stub すれば通る正例」という疑いは、cohort の verifier／整数 parser／解析本体については **refuted**。これらは実処理を通しています。ビルドと trace 生成は fixture なので、実バイナリの生成・別走行そのものの実証にはなりません。

CV の因果試験 (`test_…py:170–176`) は、**同じ観測に対して spec 閾値を 0.02→0.01 と変更し、真→偽を要求する試験**です。単なる定数一致ではありません。格子も実装 `:148–162` が規則から再生成して照合しており、派生値の pin だけではありません。

## 所見が無い面と、その理由

- **丸め値の解析混入：無し。** `performance_reps():313` で整数比を計算し、`analyze_cohort():560` でも再計算した値だけを `:571` の統計へ渡します。runner の印字率は既存 leading indicator に残りますが、数値解析へ接続されていません。欠損・不正値は拒否され、補完されません。
- **正しさの権威の取り違え：無し。** loader `:323` と analyzer `:564` は `payload.certified is True` と anomaly 0 を要求します。`"serializable"` などの verdict 文字列や report point の `certified` を権威にしていません。
- **実装の反復・即 reject・別ビルドの弱体化：無し。** driver `:676` は5回を渡し、`loop.py:745` が転送します。`pipeline.py:2016–2017` は別 trace 設定でビルドし、`:2185–2188`／`:2436–2437` は失敗時に先へ進みません。転送のテスト不足は所見4と区別します。
- **規律7を理由とした束縛の緩和：無し。** 探索 mode は `:329` の historical read で取得します。事前登録は `:237–240`、formal lock は `:376–377` で束縛を検査します。今回の追加に「現行コードとの差だけ」を新たな拒否理由にする処理は見つかりません。
- **既存テストの反転・skip・削除：無し。** 変更された既存 test は `test_layer3_report.py`。conditional key 数は新 key に合わせて3→4ですが、旧出力期待集合は明示した `_LEGACY_BENCH_PAYLOAD_KEYS` に維持されています。既存 golden に現行 hash や揮発 payload を差し込む変更もありません。

## 総括

丸め値の遮断、`payload.certified` の権威、既定 False の互換性は静的読解では破れませんでした。  
一方、must-fix は4件あります。  
正常 cohort 正例と records の因果試験には、具体的な接続不良があります。  
loop 転送の試験も、対象の転送を実行していません。  
loader 拒否時には、失敗理由と観測値を開示する成果物が生成されません。  
したがって、非 invalid 到達性と投入前条件の充足を、この統合状態で確認済みとは扱えません。