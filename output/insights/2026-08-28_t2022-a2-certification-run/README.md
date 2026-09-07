# [T-2022] A-2 fan-out 4-cell certification 実走

## 結論

attempt `t2022-20260828c` の4 cellはすべてcorrectness certifiedだったが、adopted backoffは両workloadでstockを下回った。outer certification statusは`reject`である。性能差を成功・tieへ読み替えない。

| workload | stock median TPS | adopted median TPS | effect |
|---|---:|---:|---:|
| rr5 | 2,527,542 | 1,355,011 (`fixed10`) | -46.3902% |
| rr50 | 3,662,448 | 1,248,603 (`fixed5`) | -65.9080% |

各cellはlegacy correctness 1回とfull-scale correctness 5回がすべてpass。性能は別のtrace-disabled build/runで5 samplesを取得した。anomalyは0、performance statusは4 cellすべて`complete`。

## 実行identity

- source commit: `639c1dbad4b00d8c51993a653cfc1ebfd22cf300`
- CCBench pin: `511c953`（full HEAD `511c9538e4e8efa54b45cda62e72389ed3b706ec`）
- policy SHA-256: `42bfee487c9e517b9876fbb41f8a4b4de53266ced1543263087bbd637ecc897e`
- protocol SHA-256: `136b823e60a4b43e07dbbb4e3f8b5be48964226c955e143d59955325f0e0d9f4`
- rr5 request: `954194.nqsv`、Elapse 3671s、bnodeはreservation receipt参照
- rr50 request: `954195.nqsv`、Elapse 3594s、bnodeはreservation receipt参照
- submission/completion/acquisition/raw-manifest SHA-256: `c89d2acd...a0104d29` / `b7b1538a...fa5b1026` / `05fd829c...4614cb6` / `12d8be7a...05a7c35`

durable authorityは `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2022-20260828c/`。tracked materializationは `output/insights/2026-08-24_paper-story-a2-certification/`。`certification.json` SHA-256は`f685b40d194c9e4b40eed6337b294f38a7ff4aef731829317fd2e83940fbda40`。

## 実走で閉じた欠陥

1. pre-existing `t2022-20260827` はqueue待ち中にlive worktreeが消え、source digest不能。
2. `t2022-20260828` はpolicy `SILO`が実source `cc/silo`と不一致で4 cell identity-error。
3. `t2022-20260828b` はfull pinとshort authorityの不一致、およびBACKOFF_REPRO capability未配線で4 cell admission-error。
4. `t2022-20260828c` の初回collectはLustre上の`RENAME_NOREPLACE` EINVAL。既知site fallback修理後、同じacquisitionの再提示だけでpublishした。

失敗attemptはすべて別leafのまま保持し、成功attemptへ混ぜていない。`t2022-20260828`と`...b`は各々finish-groupをexact 1回実行し、raw manifest無しのcompletion/acquisitionで閉じた。attempt cも両終端後にfinish-groupをexact 1回だけ実行した。

## 開発検査

- focused: 103 passed、consumer/meta 4 passed、protocol 73 passed、admission 118 passed、materialize 83 passed、spawn inventory 2 passed。
- mutation final matrices: baseline PASSED、M1〜M12の12/12 KILLED、SURVIVED 0、MISMATCH 0、TIMEOUT 0。probeの期待node訂正とhash転記失敗はjob dirに保全した。
- acceptance: queue既定900sのinfra失敗後、D612 opt-in 3600s/600sでchild-green。spawn inventory追随後の最終全走は記録commit後に再実行する。

## 既知限界とscope外

- correctness run argvは既存pipelineが独立記録しない。report自身の`independent_observation_limits`に明記し、独立観測を主張しない。
- sibling driver failure時のpartial raw anomaly lattice、attempt選別一般化、publish fallbackのnon-cooperating writer耐性は本waveで拡張しない。
- A4 noise floorはopen、global minimalityは確立していない。今回の結論はexact 2点 protocol内のrejectに限定する。

---

## 測定条件の実体 (2026-09-07 追記、D1645)

**上の本文は 1 バイトも変更していない。絶対規律 7 に従い、追記でのみ訂正する。**
`certification.json` の bytes、当時の protocol 出力 `reject`、測った値、4 cell の correctness 判定は
いずれも変えない。変えるのは「その `reject` がどの命題を支持するか」の読み方だけである。

### 何が起きていたか

attempt `t2022-20260828c` の 4 cell は、**patch が 1 つも当たっていない stock の CCBench 木**で build された。
当時の driver は patch harness を呼んでおらず、pipeline は patch を当てない契約だった (`docs/failures.md` の
F707 と、その 2026-09-04 の再発記録)。

**adopted cell が要求した `BACKOFF_FIXED` は cmake の argv には渡っていた。**
届いていなかったのではない。渡ったうえで、pin の CCBench に対応する option 定義が無いため
compile definition へ転送されず、build の条件にならなかった。

一次資料は durable authority
`/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2022-20260828c/` の
WAL 2 本 (`jobs/<rr5|rr50>/campaigns/<campaign>/runs/` 配下) の `build_start` 4 record である。
4 record すべてが次を記録している (rr5 / rr50 の両方を本追記の作成時に読み直して確認した)。

| 記録 field | 4 record すべての値 |
|---|---|
| `payload.src_token`、`build_admission.source.src_token` | `stock` |
| `build_admission.source.tracked_clean` | `true` |
| `build_admission.source.tracked_diff_sha256` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (空 bytes の SHA-256) |
| `build_admission.source.tracked_paths` | `[]` |
| `build_admission.source.ccbench_commit` | `511c953` |
| `build_admission.source.source_root` | 4 record とも同一の共有木 |

**patch 不在はこの 4 つの連言から導いている。** `src_token = stock` だけでは「木が HEAD どおり」を意味しない —
`src_token` が言うのは、その genome で正規化した digest が同じ genome の baseline digest と等しいこと
までである (`orchestrator/campaign/source_digest.py` の `resolve_evidence`)。追跡木が無変更であることは
`tracked_clean`・`tracked_diff_sha256`・`tracked_paths` が別に担う。

同じ理由で、`source_bytes_sha256` が cell 間で異なること (stock 側 `2d691b45…`、adopted 側 `6454d9f3…`) は
patch の証拠ではない。この値は genome を入力にした前処理後 digest だからである。

### 実際に効いた条件差

`build_done.payload.perf_configure_cmd` に記録された実 cmake 引数は次のとおりである。
genome の記録は資料ごとに載る範囲が違う。`BACKOFF_FIXED` と `BACK_OFF` は `certification.json` の
`cells[].genome` にある。`BACKOFF_NOINLINE` はそこには無く、WAL の genome 文字列 (`BACKOFF_NOINLINE=0`) と
policy の `controlled_define_base.CCBENCH_BACKOFF_NOINLINE` (値は文字列 `"0"`) にある。

| cell | role | 要求した条件 | 実 cmake 引数の backoff 部分 |
|---|---|---|---|
| `rr5-stock` / `rr50-stock` | stock | `BACKOFF_FIXED=-1`, `BACK_OFF=0` (+ 共通 `BACKOFF_NOINLINE=0`) | `-DCCBENCH_BACKOFF_FIXED=-1 -DCCBENCH_BACKOFF_NOINLINE=0 -DCCBENCH_BACK_OFF=0` |
| `rr5-fixed10` | adopted | `BACKOFF_FIXED=10`, `BACK_OFF=1` (+ 共通 `BACKOFF_NOINLINE=0`) | `-DCCBENCH_BACKOFF_FIXED=10 -DCCBENCH_BACKOFF_NOINLINE=0 -DCCBENCH_BACK_OFF=1` |
| `rr50-fixed5` | adopted | `BACKOFF_FIXED=5`, `BACK_OFF=1` (+ 共通 `BACKOFF_NOINLINE=0`) | `-DCCBENCH_BACKOFF_FIXED=5 -DCCBENCH_BACKOFF_NOINLINE=0 -DCCBENCH_BACK_OFF=1` |

pin `511c9538` の CCBench には `CCBENCH_BACKOFF_FIXED` と `CCBENCH_BACKOFF_NOINLINE` が**木全体のどこにも無い**
(`cmake/Options.cmake` だけでなく全 file を検索して 0 件)。両者は patch が供給する option である。
定義が無い以上、`-D` で与えられた値は使われない cache 変数として残るだけで、compile definition にはならない (F707)。
一方 `CCBENCH_BACK_OFF` は `cmake/Options.cmake` に実在し、`ccbench_universal_definitions` が
compile definition `BACK_OFF` として全 protocol target へ渡し、silo の `transaction.cc` の `#if BACK_OFF` が
消費する。

**genome の差は `BACKOFF_FIXED` と `BACK_OFF` の 2 つだけで、前者は build に効いていない。したがって
4 cell の間で実際に効いた条件差は `BACK_OFF` の `0` と `1` だけである。**

**binary hash の差はこの結論の根拠にならない。** 同一の記録 genome を持つ `rr5-stock` と `rr50-stock` でも
`performance.perf_bin_sha256` は異なる (`9d3dba7c…` と `f84d0c7b…`)。一次資料はこの差の原因を記録していない。
hash 単独を compile-out の証拠にしない。

### `BACK_OFF=1` が有効にする機構

CCBench の `include/backoff.hh` にある `Backoff` クラスである。これは**適応制御**で、直近区間の
スループット変化を待機量の変化で割った勾配を見て、共有待機量を固定幅 `kIncrBackoff = 100` だけ
増減し、`kMinBackoff = 0` から `kMaxBackoff = 1000` の範囲に収める (勾配 0 のときは commit 数の
最下位ビットで増減を選ぶ)。**指数的に増える機構ではない。**

`cmake/Options.cmake` の option 説明文だけが `exponential backoff on abort` と呼んでおり、
D1645 の文言「内蔵指数 backoff」はこの説明文に由来すると見られる。本追記は機構名を実装に合わせて
「CCBench 内蔵の適応 backoff」と書く。**D1645 が定めた訂正の内容 (支持する命題を `BACK_OFF` の
有効/無効へ書き換えること) はそのまま実行している。**

### `reject` が支持する命題

**支持する:** `BACK_OFF=1` (CCBench 内蔵の適応 backoff **有効**) の構成は、`BACK_OFF=0` (**無効**) の
対照より median throughput が低い。write-heavy (rratio=5) で **−46.3902%**、
balanced (rratio=50) で **−65.9080%**、外側の status は 2 workload の論理積で `reject`。

**支持しない:** 採用静的 backoff (fixed 10 µs / fixed 5 µs) が対照を下回った、という命題。
静的量は build に効いておらず、本走行は採用構成を測っていない。
`certification.json` の `cells[].genome` が `BACKOFF_FIXED=10` / `=5` を持つのは、
**要求された genome の記録**であって、build に効いた条件の記録ではない。

**変わらない:** 当時の protocol 出力 `reject`、4 cell の correctness `certified` (anomaly 0)、
測った値、`certification.json` の bytes。当時その道具でその測定をし、その結果が出たという事実は
後から変わらない (絶対規律 7)。

### 下流

- 論文素材からは、正しい identity で取り直した attempt が出るまで A-2 の結論を外す (D1645)。
  凍結された図 5 も、取り直しまで論文の A-2 の結論や図には使わない。
- 結果節の統制稿は `docs/paper-story/results/` の 2026-09-07 付 file が担う。
  同系列は append-only なので、2026-09-04 付の稿は凍結物として残る。
- 取り直しは、adopted cell の canonical identity を pin と patch に束縛した `src_token` で計算する
  実装 (D1644 / T-2337) の後に行う。取り直しは本 attempt を触らない。
