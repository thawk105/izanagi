## real

以下、`M`＝`orchestrator/campaign/paper_story_a2_certification.py`、`S`＝submitter、`J`＝job body（ともに指定された `tools/pegasus/` 配下）。

1. **P1 の configure argv 完全一致は、予定された実行方式では成立しない。**  
   対象：[brief.md:52](/home/SFC/tanab/.claude/jobs/f6bf33bb/brief.md:52)。  
   `J:340–355` は request ID ごとに異なる dependency／FetchContent path を作る。`M:2386–2443` の configure argv はこれらの絶対 path と build directory を含むため、3 request の argv は異なる。完全一致を要求すると正常な完走でも P1 未充足となり、差を無視して「一致」と書くと成果物と矛盾する。  
   **最小修正：**「同じ genome・controlled defines・source digest から workload ごとに個別 build」と記述する。configure argv は実値を残し、固定引数と toolchain を比較し、配置先 path の差を明記する。「同一 binary」の主張はしない。

2. **今回の source binding は、T-1998 prereg の固定 digest 一致を保証しない。**  
   対象：[brief.md:52](/home/SFC/tanab/.claude/jobs/f6bf33bb/brief.md:52)、[plan-out.md:333](/home/SFC/tanab/.claude/jobs/f6bf33bb/plan-out.md:333)。  
   `M:1338–1361` は pin・genome・source root を照合し、`M:1398–1405` は adopted token が非 `stock` であることを検査する。`M:2800–2812` は当該走行の receipt と raw token を比較するが、prereg の `678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12` は比較対象にない。3 workload 相互の digest 比較もない。したがって、collect 成功だけから prereg と同じ source identity を結論できない。  
   また `src_token` と `source_bytes_sha256` は別フィールドである（`source_digest.py:2307–2322,2455–2456`）。  
   **最小修正：**親の稿作成手順に、3 adopted arm の `source_bytes_sha256` と [prereg:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/docs/t1998-balanced-stock-inline-preregistration.md:87) の全桁比較を明記する。不一致なら「fixed5 の設定を採用したが、prereg の source digest との一致は未成立」と書く。新 gate は不要。

3. **「A-6 は nodes=5 で73分」は実測の取り違え。**  
   対象：[brief.md:55](/home/SFC/tanab/.claude/jobs/f6bf33bb/brief.md:55)。  
   [A-6 submission-receipt.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/output/insights/2026-09-08_t2411-paper-story-a6-certification/submission-receipt.json:1) の `qsub_argv` は **`-b 1`**。[実走記録:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/output/insights/2026-09-08/t2411-a6-readheavy-submitted/README.md:29) は4382秒、同:141–144 は本走検査約7分×5×2 cell と説明している。  
   **壊れ方：**現行 policy の nodes=5 を過去走行へ遡及して、今回の所要根拠にしている。「nodes=1 なら数時間」もこの73分の実測からは導けない。  
   **最小修正：**「A-6 の当該実測は nodes=1、約73分。今回の rr95/fixed5/nodes=5 の所要は未測定」と訂正する。

## refuted

- **全件経路に、追加で緩める必要のある固定2-workload境界は見つからない。**  
  submission／completion は policy 件数と順序を照合する（`M:1531–1543,1882–1893`）。finish は全 workload 成功で full manifest を作る（`M:2302–2304`）。producer は `6×N` members、`3×N` campaign members（`M:4057–4059`）、loader は6 raw＋3 condition receipts＋9 campaign members＝18を受理する（`M:4320–4332`）。condition receipt の4行制約は workload ごとの2 cell に対するもの（`M:1367–1375`）。

- **request ID 順序・materialize も3 workloadに適合する。**  
  `M:2035–2037,2972–2978,4734–4746` は policy 順を要求する。提案順 `rr5,rr50,rr95` は JSON のキーソート順とも一致する。`M:4789–4803` は acquisition から再導出して report を照合し、`M:4813–4817` は fresh exact leaf を要求する。新 destination を事前作成しないという plan は正しい。

- **partial の exact two-workload は正しい。**  
  writer `M:2305–2309`、consumer `M:1930–1933` が境界。3 workload 中1件または2件成功では full completion の manifest が `null` となり、partial 認証へ流れない。

- **submitter の2条件変更は必要で、plan が brief の漏れを補っている。**  
  実箇所は `S:273` と `S:365`。brief:36 の263行目というアンカーは誤り。後者を残すと receipt の環境集合が `M:1577–1589` に拒否される。plan:21–22 は両方を含む。

- **`-b 5` を通すための追加変更は不要。**  
  `M:5127–5134`／`2208–2213` は投入 argv の基本形だけを検査し、nodes と policy の一致は `M:1565`。`J:151–159` は head＋4 sibling を要求する。この境界を新たに緩める計画ではない。

- **正しさ gate は同じ経路を通る。**  
  plan の共通6項目は現 A-2 JSON と値比較で一致した。`M:489–492` は TRACE=0、`M:2552–2579` は configure／binary 証拠、`M:2591–2600` は trace/performance 別 build を検査する。anomaly は `M:2634–2654 → 2873–2876 → 2985–2986` で reject。rr95 固有の迂回はない。なお anomaly 時は median／effect が欠け得るため、全件報告では欠測理由を記す。

- **A-6 先例の残り3ファイルは、今回は変更不要。**  
  `60605bec3` の8ファイルを確認した。job body の当時の変更は policy 選択と workload membership 導入で、現 `J:103–130` が既に担う。registry は既存 script path の分類（`tools/pegasus/admission_registry.json:124,370`）、`test_hooks.py:3362,3608` はその説明文との対応であり、新 study の allowlist ではない。

- **凍結 pin は現在の基準なら維持可能。**  
  現在値を再計算した：

  | policy | bytes SHA-256 | protocol SHA-256 |
  |---|---|---|
  | A-2 | `f8a7780600766e6c8e0248ae0e3aff70a2e1c28150f8932842cdbf67f988472c` | `d99f08bcc50c605d24d443d387a2c3144c16b9e670c9b9e247227c5db1be7f9c` |
  | A-6 | `682e0f4ed980b74d509426d8f074f51f5b8062a1ca7cf82cd8dbbaae93c4446a` | `21427e71793ea744777d11bd90429ce2db1a8d3333ea9e2e0f227ecf377c25dc` |

  plan:310 の旧 A-2 bytes hash は brief:93 で訂正済み。テストの現 pin は `test_paper_story_a2_certification.py:1869–1873,2052–2054`。plotter:48–62 が pin するのは過去成果物と埋込み歴史 policy であり、現 A-2/A-6 JSON 両方の live pin ではない。新 policy 追加では壊れない。  
  現時点で `657e1e5a7` から両 policy・指定された既存 attempt leaf の差分は空。author 後も**この基準から全対象の差分が空**であることを確認する必要がある。brief:79 の「両 file は無変更」は、テストファイルを拡張する scope と矛盾するため「既存 pin は無変更」と読むべき。

- **床値の全桁は正しい。**  
  各 `between_run_noise_t48_skew0p9_rr{5,50,95}_rmw0.json:37` は順に `0.009536033056996148`、`0.00725042525457718`、`0.0022283754708938273`。t2489 の「約12分」も記録:21 の680秒／728秒と整合する。

## 未確認

- **新 policy の実行成功・テスト成功。** 静的検査のみ。親が plan の3-workload full finish→collect→materialize、負例、partial 拒否を `tools/run_tests.py` 経由で確認する。
- **実 source／build identity。** 親が比較できる記録は次のとおり。

  | 成果物 | 記録 |
  |---|---|
  | raw cell JSON | `src_token`、`trace0_evidence.configure_argv`／controlled defines（`M:3581–3603,3642`） |
  | WAL `build_start` | genome、`src_token`、`build_admission.source` 内の source evidence（`pipeline.py:1899–1910`） |
  | WAL `build_done` | `perf_configure_cmd`（`pipeline.py:2078`） |
  | condition receipt | `source_bytes_sha256` を含む source evidence。各 workload の2／4行目（`M:1379–1394`） |
  | `certification.json.cells[]` | `src_token`、genome、binary hashes。configure argv／`source_bytes_sha256` は含まない（`M:2904–2928`） |

  tracked leaf だけでは raw／WAL 全文は揃わない。raw-manifest に束縛された durable 側の実ファイルも参照する。

- **P5 の lock 原因・「2 cell は数分差」。** t2489 記録:32–33 自身が lock 原因を「強い推測、立証ではない」と限定している。今回の待ち時間や cell 間隔は未測定。親は scheduler 開始時刻に加え、各 arm の WAL の bench 時刻を報告する。
- **author 後の凍結。** 現在の差分なしは確認したが、将来の変更を保証するものではない。policy pin 検査に加え、旧 attempt ディレクトリ全体の差分確認が必要。

## 裁定パッケージ候補

なし。指摘は説明訂正と、既存成果物を使う親の照合手順で扱える。新 protocol・追加 gate・partial 拡張は不要。

## 総括

closed-set 拡張と3-workload全件経路の計画は、静的には成立する。  
必須訂正は P1 の argv 一致、prereg digest との照合手順、A-6「nodes=5で73分」の3点。  
凍結基準は取込み後の `657e1e5a7` と現 pin に統一する。  
書込み・pytest・性能測定は実施していない。