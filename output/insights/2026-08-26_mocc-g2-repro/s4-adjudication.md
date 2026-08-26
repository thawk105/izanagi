# 段 4 裁定 — dev-wave-mocc-g2-repro-20260826

段 2 plan と段 3 の 2 レンズ (sol = 測定設計、luna = 受理集合と規律) の所見を裁定する。
親自身の brief も裁定対象とした。

## 0. 親 brief の誤りの訂正 (両レンズが独立に指摘)

- **[S-12] / [L-12] real・採用。** brief の「投入から完了まで約 85 秒」は算術が合わない。
  同じ行の epoch は submit 1787735041 → 完了 1787735142 で **101 秒**である。
  85 秒は scheduler 開始 (1787735057) から完了までの区間だった。始点を書かずに
  「投入から」と書いたのが誤り。以後 **submit-to-completion = 101 秒**を使う。
- **brief の成果物影響が過大** ([S-1] の指摘)。この study を完走しても
  「MoCC の性質か trace hook の取り違えか」は解消しない。増えるのは固定 pipeline の
  k/m・区間・run 台帳の参照だけである。brief の該当行はこの裁定で上書きする。
- **brief の 3 batch × 10 は撤回。** 一次資料が支持する同時投入の実績は 6 本である。

## 1. 測定設計の裁定

### [S-1] N=30 では k=0 でも p=0.10 を排除できない — real・採用

k=0・m=30 の両側 95% 上限は 0.1157 で、これは 0.10 を上回る。目的が
「flake か低頻度の実在か」の判別である以上、この N では目的を達しない。

**裁定: N = 42 (7 batch × 6) へ引き上げる。** 親が実測した値は次のとおり。

| N | k=0 の上側 95% | p=0.10 に対する検出力 |
|---|---|---|
| 30 | 0.11570 | 0.9576 |
| 36 | 0.09739 | 0.9775 |
| 40 | 0.08810 | 0.9852 |
| **42** | **0.08408** | **0.9880** |
| 48 | 0.07397 | 0.9936 |

42 なら k=0 のとき p >= 0.084 を排除できる。費用は約 63 点 (残 13,428 点)、
実時間は 7 batch × (queue 待ち + 101 秒) で 30 分前後。**これは結果を見る前の決定である。**

### [S-2] / [L-8] estimand と推定量の不一致 — real・採用

宣言した estimand は「固定 pipeline が 1 run で G2 を返す確率」だが、k/m は
「verdict が確定した run に条件付けた確率」である。除外は informative missingness でありうる。

**裁定: 3 つ全部を報告する。**
- `k/N` (N=42 基準。欠測を全部 non-G2 とみなした下限)
- `k/m` (条件付き `p_det`。**これが一次報告値**、m を必ず併記)
- 識別区間 `[k/N, (k + 欠測数)/N]`
- k=0 の判定文と区間は **m で分岐**させる。m=42 用の 0.08408 を m<42 の結果に流用しない。

### [S-3] / [L-9] anomaly run が構造的に分子から消える懸念 — refuted・規則維持

job は verifier JSON と rc を保存してから rc=1 で fail-closed する
(`mocc_trace_pilot.sh:1039-1050`)。分母規則はこの run を拾う。
**裁定: 規則を維持し、正例として凍結する** — 「rc=1・non-serializable・G2 あり・
failure.json あり・completed receipt 無し」の組を必須の正例とする。

### [S-4] 30 本という集合が機械的に固定されていない — real・採用

submitter に ordinal も study ID も無いので、どの run を受理集合に入れるかを後から選べる。
**submitter は変えない** (probe で緑を確認した版のまま走らせるため)。代わりに閉包で塞ぐ。

親が実測した事実: submission directory は **qsub の前に create-only で作られ**
(`submit_mocc_trace.sh:218-227`)、`qsub.stdout` / `qsub.rc` もその中に書かれる
(`:350-362`)。したがって `attempts/submissions/*` の全列挙が投入の完全集合である。

**裁定: 次を事前登録する。**
- 解析時に `attempts/submissions/` を**全列挙**し、各 `submit-receipt.json` の
  `source_commit` が凍結 commit と一致するものを本 study の投入集合とする。
- その集合の要素数はちょうど 42 でなければならない。多くても少なくても不整合として報告する。
- ordinal は投入順に 1..42 を親が create-only の台帳へ書く。台帳の nonce 集合と
  上の列挙が**完全一致**することを検査する。
- 凍結前の投入 (dry-run 1 件、生死確認 probe `950267.nqsv` 1 件) は `source_commit` が
  異なるので自動的に外れる。

### [S-5] 5 batch × 6 を独立試行として扱う根拠 — real・部分採用

前 wave の実測は「TRACE=1 が 3 本 + TRACE=0 が 3 本の混合 6 本」であり、
**6 本すべて TRACE=1** も **7 batch 反復**も未観測である。

**裁定:**
- batch 6 は維持する (1 本ずつ 42 回直列にすると queue 待ちが 42 回に増え、
  かえって時間帯の交絡が大きくなる)。
- **IID 仮定を事前登録文へ明記する。** 「並行度 6 を estimand の一部として固定する」と書く。
- run ごとに **host と batch 番号を記録**し、事前登録済みの batch 別・host 別感度表を出す。
- **輻輳による fallback を事前登録する。** ある batch で `third_party` /
  `source_materialization` / `allocation` / `glog` / `gflags` のいずれかの stage 失敗が
  1 件でも出たら、以後の batch は 3 本へ落とす。**失敗 stage は anomaly の有無と独立なので
  分子にバイアスを与えない。**

### [S-6] 原因を分けられない点の過大主張 — refuted・維持

plan も draft も非帰属を明記している。**裁定: 非帰属文を結果の必須定型として維持し、
因果を主張する副次解析を禁じる。**

### [S-7] 副次解析の観測集合が未定義 — real・採用 (non-must-fix だが安い)

**裁定: 観測集合を「verifier が報告した witness (1 run あたり最大 20 本)」と定義する。**
親が実測: `--max-report` の既定は 20 (`orchestrator/verifier/cli.py:46-47`) で job は上書きしない。
`anomaly_count` は**報告された witness 数** (`report.py:134`)、`total_cycles` が全 cycle 数
(`:135`) である。**分子の述語には `total_cycles >= 1` を使い、cycle 長が 2 以外の場合の
表示法も先に決める。** p 値・因果推論は出さない。

### [S-8] 本走を [T-1894] の前に置くか後に置くか — real・**親が明示裁定する**

sol は「post gate を先に実装してから本走せよ」、plan は「本走を先に」と正反対である。

**裁定: 本走を先に置く。** 理由は 3 つ。

1. **[L-2] により、plan が設計した post gate は endpoint drift しか検出しない。**
   先に実装しても S-8 が求める保証は得られず、名前が付くだけである。
2. probe で緑を確認したのは**現行の job script** である。未検証のコードを study 本体の
   前提にすると、段 6 の fix が 42 本の再走を強いる。
3. 同じ窓は**親側の運用規律でより広く塞げる** — 「jobs が飛んでいる間、wave worktree へ
   一切書かない・commit しない」は endpoint だけでなく全区間を覆う。

**代償として次を義務づける。**
- **段 5 を study と並行させない。** 42 本が全部 terminal になるまで実装子を起動しない。
- 各 batch の投入前と完了後に親が HEAD と clean を確認し、台帳へ記録する。
- **残余リスクを結果へ明記する** — job 側の source 検査は開始時 1 回だけであり、
  本 study の provenance は機械 gate ではなく親の運用規律と submit receipt の
  `source_commit` に依っている。**これを「TOCTOU を塞いだ」と書かない。**

### [S-9] DW-G05 の一行が主要測定項目に無い — real・採用

**裁定: 事前登録の各項目へ「未実装なら変わる値・受理集合・参照」を書き、
値も集合も動かない項目は non-must-fix と明示する。**

### [L-13] G2 の別 thread 帰属を repo 内資料で独立確認できない — 保留・採用

親は repo 外の trace 原本を読んで thid 40 / 21 を得たが、repo 内の結果文は thid を載せていない。
**裁定: pilot anomaly の構造化投影を repo へ置く** (txid・thid・commit version・
trace file 名・その file の SHA-256)。これは規律 3 の「なぜ壊れたかを構造化して返す」に当たる。

## 2. [T-1894] の裁定

### [L-4] 「導出不能化」は成立しない — real・**主張を狭める**

CCBench の stdout は count と throughput を直接印字し (`058d0c4e:common/result.cc:47-56`)、
trace の `C` 行は committed transaction そのものである。receipt から 3 field を消しても、
同一 run directory の他成果物から同じ値が出る。

**裁定: (i) の主張を「pilot receipt の性能 field の redaction」に狭める。**
**「TRACE=1 成果物から性能値を導出できなくした」とは書かない。**
機械的な利用拒否は consumer gate の仕事であり [T-1893] (裁定待ち) の scope である。

### [L-5] 成果物の棚卸しが receipt 以外に及ぶ — real・採用

**裁定: job が書く全成果物を `correctness evidence` / `performance evidence` /
`operational diagnostic` の 3 分類で台帳化し、TRACE=1 での利用禁止を成果物単位で書く。**

### [L-1] legacy v2 を外部 anchor 済みにする案は循環 — real・採用

**裁定: legacy v2 は `consistency_checked_but_unanchored` とする。**
独立に保持された pin が提示されない限り anchor sidecar を発行しない。
親が実測した「blob SHA-256 が一致する」事実は**内部整合性であって anchor ではない**。

### [L-2] post 再検査は endpoint drift だけ — real・採用

**裁定: 保証名を「pre/post endpoint consistency」に狭める。TOCTOU を閉じたと書かない。**
判定中の一時変更と post 後の窓が残ることを receipt と docs に明記する。

### [L-3] source-state が pair checker の受理述語へ届いていない — real・採用

**裁定: pre/post capture を独立 leg input とし、`validate_leg` と CLI で
bytes SHA・phase・HEAD・clean・capture path を検査する。receipt 内の SHA だけを信用しない。**

### [L-6] v4 生成受理と historical v2 検証は別集合 — real・採用

**裁定: 2 集合を分けて裁定する。P05 の正例は synthetic shape ではなく
保存済み v2 の exact bytes を使う。**

### [L-7] 旧 version を読む内部経路が残る — real・採用

**裁定: job-result writer にも exact pilot schema assertion を置く。
anchor verifier は v2 / v3 を明示分岐し、暗黙 fallback を禁じる。**

### [L-10] M04 は二重防壁で単一理由性を満たさない — real・採用

**裁定: M04 を再照準する** — v4 shape と valid witness を持ち schema label だけ v3 にした入力へ
向ける。M05〜M10 は新設実装後に前後の拒否を再監査してから本走に載せる。

### [L-11] runbook と admission registry への編集要求は無い — refuted・確認

**裁定: 両 file を触らない。** 稼働中 b10 系 2 wave との編集面衝突は発生しない。

## 3. scope 外 (裁定パッケージ候補)

- **[T-1893] の consumer gate。** [L-4] が示すとおり TRACE=1 成果物から計数を数学的に
  消すことは trace の性質上できない。headline・floor・oracle・fitness への利用を本当に
  機械拒否するには別 scope の consumer gate が要る。**本 wave では作らない (裁定待ち)。**
- **原因帰属のための ground truth 観測。** 同じ trace を同じ verifier で再検査するのではなく、
  実際の read-from・write version・commit 順序を独立に束縛する観測、または決定的な
  schedule replay が要る。Silo 対照だけでは MoCC 固有の hook 経路を除外できないので不十分。
  CCBench 側の追加計装を伴う別 wave として裁定へ回す。

## 4. 段 5 の所有 (study 完了後に起動する)

- **(A)** `tools/pegasus/mocc_trace_pilot.sh` — (i) redaction + counter witness、
  (ii) pre/post endpoint consistency capture、job-result writer の schema assertion。
- **(B)** `orchestrator/campaign/mocc_trace_pair.py` + 新規 anchor verifier —
  caller pin、source-state の独立 leg input、v2/v3 明示分岐。
- **(C)** study の per-run 台帳生成器と検査 test。**scipy が無い** (親が実測、numpy はある) ので
  Clopper-Pearson は `math.comb` による厳密二項 CDF + 二分法で組む。
  k=0・m=42 の上側 0.08408 を独立に再計算できること。
