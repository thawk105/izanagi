# 事前登録 — MoCC TRACE=1 の G2 再現率 study ([T-1892])

**この文書は結果を見る前に凍結する。** この文書を含む commit の HEAD が、本 study の全 run の
outer identity である。**結果が出た後にこの文書の述語・分母・分子・区間・判定文を緩めてはならない。**

- wave: dev-wave-mocc-g2-repro-20260826
- 状態: **凍結 (段 4 で確定)**
- 一次資料 (前 wave): `output/insights/2026-08-26_mocc-trace-pair.md`
- 段 4 裁定: `output/insights/2026-08-26_mocc-g2-repro/s4-adjudication.md`

## 0. この study が答える問い、答えない問い

前 wave は同一 outer commit・同一 ccbench source・同一 workload で TRACE=1 を 3 本走らせ、
うち 1 本が non-serializable (G2 anomaly 1 件) で fail-closed した。これが
「MoCC 実装の性質」なのか「izanagi の trace hook の取り違え」なのかは確定していない。

**この study が確定するのは、下で固定する pipeline における verifier-reported G2 の
run 単位の再現率だけである。**

**この study が確定しないこと (結果にも必ず書く):** 再現率は、原因が
(1) MoCC 実装の性質、(2) trace hook の記録の取り違え、(3) verifier の版順序仮定の不成立
のどれであるかを分けない。**因果を主張する副次解析を行わない。**

## 1. 固定する対象 (この組み合わせ全体が estimand の一部である)

- outer commit: 本文書を含む commit (各 `submit-receipt.json` の `source_commit` が正本)
- ccbench source: `058d0c4e5f237d88ec1c2ebe0739113d82906e47` (base `511c9538e4e8efa54b45cda62e72389ed3b706ec`)
- cmake target: `ycsb_mocc.exe`、`CCBENCH_TRACE=1`
- workload: records=10,000 / threads=48 / zipf skew=0.9 / read ratio=50 / RMW=0 /
  max operations=10 / extime=3 秒
- 環境: Pegasus `gen_S`、1 node、Intel Xeon Platinum 8468、48 physical cores、HT off
- 判定器: `orchestrator/verifier/` (本 wave では**一切変更しない**)
- 実走口: `tools/pegasus/submit_mocc_trace.sh` と `tools/pegasus/mocc_trace_pilot.sh` の
  **[T-1894] 実装前の版**。receipt は `mocc-trace-pilot-receipt/v3` で、計数 field と
  現行の source 検査の限界を持つ。**[T-1894] の効力を本 study へ遡及させない。**
- **並行度 6 も estimand の一部として固定する** (§2)。

## 2. 反復数 N と投入手順

**N = 42。** N は「scheduler が request ID を発行した run」の数で数える。

- request ID 発行前の preflight / qsub 失敗は運用失敗として記録し、N に数えない。
  同じ未使用 ordinal を再投入してよい。
- **一度 request ID が発行された ordinal は、結果にかかわらず固定する。代替 run を足さない。**
- 42 request ID を超えて投入しない。
- 投入は **7 batch × 6 本**。前 batch の全 job が terminal になってから次を投入する。
  6 本は前 wave が実測した同時投入の実績値である。**ただしその実測は TRACE=1 が 3 本と
  TRACE=0 が 3 本の混合であり、6 本すべて TRACE=1 も 7 batch 反復も未観測である。**
- **輻輳 fallback (事前登録):** ある batch で `third_party` / `source_materialization` /
  `allocation` / `glog` / `gflags` のいずれかの stage 失敗が 1 件でも出たら、
  以後の batch は 3 本へ落とす。**失敗 stage は anomaly の有無と独立なので分子にバイアスを
  与えない。** anomaly の有無で並行度を変えることは禁止する。
- batch 番号と ordinal は投入順で決まり、結果に依存しない。
- **各 run について host と batch 番号を記録し、batch 別・host 別の感度表を出す** (§6)。

**N=42 の検出力 (親が実測、依存なしで再計算可能)。** H0: p=0 に対し、

| N | k=0 の上側 95% (Clopper-Pearson) | p=0.10 に対する検出力 |
|---|---|---|
| 30 | 0.11570 | 0.9576 |
| **42** | **0.08408** | **0.9880** |

**本設計は「p >= 0.084 を k=0 で排除する」ことを目的とし、
「p が 0.02 程度の実在を高い検出力で排除する」設計ではない。** この限界を結果にも書く。

## 3. 投入集合の閉包 (どの 42 本かを後から選べないようにする)

submitter には ordinal も study ID も無く、submitter は本 study では**変更しない**。
代わりに次の閉包で塞ぐ。親が実測した事実として、submission directory は
**qsub の前に create-only で作られ** (`submit_mocc_trace.sh:218-227`)、
`qsub.stdout` / `qsub.rc` もその中に書かれる (`:350-362`)。

- 解析時に `output/env/pegasus/mocc-trace/attempts/submissions/` を**全列挙**する。
- 各 `submit-receipt.json` の `source_commit` が凍結 commit と一致するものを本 study の
  投入集合とする。**この集合の要素数はちょうど 42 でなければならない。**
  多くても少なくても不整合として報告する。
- ordinal 1..42 は投入順に親が create-only の台帳へ書く。**台帳の nonce 集合と上の列挙が
  完全一致すること**を検査する。
- 凍結前の投入 (dry-run 1 件、生死確認 probe `950267.nqsv` 1 件) は `source_commit` が
  異なるので自動的に外れる。

## 4. 分母 m

分母は、**verifier JSON が出力され、`results[0].verdict` が `serializable` または
`non-serializable` である run** の数とする。判定は job が書く値だけで機械的に決まり、
事後の裁量を入れない。

| 観測される値 | 分母 | 分子 |
|---|---|---|
| `failure.json` 無し + `mocc-trace-pilot-receipt.json` 有り (verifier rc=0) | 入れる | 入れない |
| `failure.json` の `stage=verifier` かつ `rc=1` (cycle 検出) | 入れる | §5 の述語で判定 |
| `failure.json` の `stage=verifier` かつ `rc=3` (indeterminate) | **除く** | 除く |
| `failure.json` の `stage=verifier` かつ `rc=2` (verifier の使用法・実装不在) | 除く | 除く |
| その他の `stage` (build / third_party / source_materialization / glog / gflags / trace / allocation / reservation / policy / environment / source_identity / submit_binding / job_result_report_binding) | 除く | 除く |
| request ID 発行後に scheduler 都合で開始不能・cancel・kill | 除く | 除く |

- **除外した run は 1 本残らず、ordinal・job ID・失敗段階・rc・根拠 artifact の SHA-256 とともに
  全件報告する。代替 run は足さない。**

**なぜ `stage=verifier` を一律に除外しないか。** anomaly を出した run は、まさに anomaly のせいで
job が rc=1 で fail-closed する。「落ちた run を除外する」規則を素朴に書くと、**分子が構造的に
消える。** 前 wave の `949964.nqsv` がその形である。job は verifier JSON と rc を保存してから
落ちる (`mocc_trace_pilot.sh:1039-1050`) ので、この run は分母にも分子にも残る。

## 5. 分子 k

分母に入った run のうち、次を**すべて**満たす run の数。

- `results[0].verdict == "non-serializable"`
- `results[0].total_cycles >= 1`
- 報告された `anomalies` に `phenomenon == "G2"` が 1 件以上ある

- 1 run に複数の G2 があっても分子は 1 とする (run 単位の再現率である)。
- **G0 / G1c だけの run は分母に入るが分子には入れない。** 別分類で件数を報告する。
- **integrity が clean かどうかは、分子から run を除く条件にしない。**
- **報告される witness は 1 run あたり最大 20 本である** (`orchestrator/verifier/cli.py:46-47`
  の `--max-report` 既定 20、job は上書きしない)。`anomaly_count` は報告された witness 数
  (`report.py:134`)、`total_cycles` が全 cycle 数 (`:135`) である。

## 6. 推定・報告する量

**3 つ全部を報告する。1 つだけを取り出して引用しない。**

- `k/N` — N=42 基準。欠測をすべて non-G2 とみなした**下限**。
- `k/m` — **一次報告値** (条件付き `p_det`)。**m を必ず併記する。**
  区間は等裾 Clopper-Pearson 両側 95% exact interval。
- 識別区間 `[k/N, (k + 欠測数)/N]` — 欠測をすべて non-G2 / すべて G2 とした両端。

`m < 42` の場合は「計画検出力を達成しなかった」と明記し、実効検出力 `1 - 0.9^m` も報告する。
**k=0 の判定文と区間は m で分岐させる。m=42 用の 0.08408 を m<42 の結果に流用しない。**

判定文は次の 2 つだけを用意し、結果を見てから作らない。

- **k = 0 のとき:** 「42 本 (うち verdict 確定 m 本) では G2 を再現しなかった。p = 0 を
  確定したのではない。95% CI 上限は (m から計算した値) である。単発観測の原因は未決のままである。」
- **k >= 1 のとき:** 「固定した MoCC TRACE=1 / trace hook / verifier の組で G2 signal を
  再現した。条件付き再現率は k/m、95% CI は [下限, 上限]、下限側の無条件率は k/42 である。」

**どちらの場合も、原因が §0 の (1)(2)(3) のどれかを、この study だけでは確定しない。**

## 7. 事前登録する副次解析 (追加走行ゼロ)

記述統計に限る。**副次解析から新しい判定閾値を作らない。p 値・因果推論を出さない。**

- (a) 全 G2 witness (1 run あたり最大 20 本) の cycle 長・edge の種別・key・
  read/write version と、その均質性。**cycle 長が 2 以外の witness は、
  「cycle 長」「関与 transaction 数」「edge 種別の多重集合」の 3 列で表にする**
  (2 transaction 前提の列は空欄にし、埋めない)。
- (b) anomalous run ごとの全 integrity counter と `clean`
- (c) cycle 内の transaction の thid が同一か別か、commit version の辞書式順序、
  epoch / tid の差、txid の差と隣接性
- (d) G2 以外の non-serializable verdict と indeterminate の理由別件数 (一次 accounting)
- (e) batch 別・host 別の k と m の感度表

## 8. 禁止事項

- **結果を見てから run を追加しない。**
- **anomaly の有無・integrity・txns・実行時間・batch・job ID・host で run を捨てない。**
- **分子・分母・G2 述語・区間・判定文を事後に緩めない。**
- **anomaly の有無で並行度・batch 構成を変えない** (輻輳 fallback は失敗 stage だけで発火する)。
- 生死確認 probe `950267.nqsv`・dry-run・前 wave の全 run は、N・m・k のいずれにも入れない。
- 得た結果は `official_certification=false` のままとし、**headline・certified な選択・floor・
  oracle・fitness の根拠に使わない。**
- pair receipt の `prohibited_uses` は**宣言であって強制ではない** — それを必須入力として読む
  consumer は repo 内に存在せず、下流利用を機械的に止めるものは無い ([T-1893] は裁定待ち)。
- 正しさゲートは緩めない (規律 2)。anomaly が出ても verifier の受理集合は変えない。

## 9. provenance の残余リスク (結果にも書く)

- job 側の source 検査は**開始時 1 回だけ**である (`mocc_trace_pilot.sh:241-249`)。
  判定後の再検査は無い。
- したがって本 study の provenance は、機械 gate ではなく
  **(a) 親の運用規律** — 42 本が全部 terminal になるまで wave worktree へ書かず commit せず、
  各 batch の前後で HEAD と clean を確認して台帳へ記録する — と
  **(b) 各 submit receipt の `source_commit`** に依っている。
- **これを「TOCTOU を塞いだ」と書いてはならない。**

## 10. DW-G05 — 各項目を実装しない場合に変わるもの

| 項目 | 実装しない場合に変わる値・受理集合・参照 |
|---|---|
| N=42 | k=0 時の上側限界と判定文。certified 選択・floor・oracle・fitness は変わらない |
| 分母規則 | m・k/m・区間・run 台帳の受理集合 |
| 投入集合の閉包 | どの run が受理集合に入るかを後から選べる。k・m・区間すべて |
| 3 通りの報告 | 報告値の解釈 (無条件か条件付きか)。§8 C-1 の参照値 |
| 輻輳 fallback | batch 構成と m (分子には影響しない) |
| 副次解析 (a)-(e) | 副次表と説明文だけ。k・m・区間・verifier の受理集合は変わらない (**non-must-fix**) |
| 残余リスクの明記 | provenance に関する主張の正しさ。値は変わらない |
