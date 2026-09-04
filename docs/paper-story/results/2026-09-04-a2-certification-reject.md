# A-2 正式 certification の結果節 — 採用静的 backoff は 2 つの独立 campaign とも無 backoff 対照を下回り、外側の protocol status は `reject` (2026-09-04)

**これは投稿本文ではない。** 論文の結果節・表・negative result へ落とすための、**一次資料に束縛した執筆者向けの日本語統制稿**である。
D12 が定める機械射影の材料レポートではない (数値は provenance JSON から転記し、散文は執筆者の判断を含む)。
英語化のときは事実命題を足さず、本稿の表と一次資料へ再照合する。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である。数値・日付・protocol status の出所は一次資料だけであり、版 (`2026-09-02.md`) の記述を出所にしていない。
本稿と図 5 が使う入力は、既存 attempt `t2022-20260828c` の権威 bytes・raw manifest・WAL だけである (provenance JSON の `tracked_inputs` / `external_inputs`)。

---

## 0. 位置づけ — 何を書き、何を書かないか

- **書くもの:** attempt `t2022-20260828c` (2026-08-28) の exact 4 cell が出した値、その protocol が出した外側の status `reject`、
  その status が言えること・言えないこと、図と表、限定の一覧。
- **書かないもの:** 「なぜ旧系列と符号が違うか」の原因 (未同定)、旧系列の値を分母にした効果 (policy が禁じている)、
  研究として成功か失敗かの宣告 (D12)、read-heavy についての主張 (A-6 として未取得)、計算資源の余裕
  (「正式 A-2 fan-out に対する 32 GB のメモリ余裕」は D1263 で取り下げ済みで、本稿は資源余裕を一切主張しない)。
- **`reject` は protocol の status であって、研究の失敗宣告ではない。** protocol は「採用構成の median throughput が
  同一 workload の無 backoff 対照を上回るか」を 2 workload の論理積で問い、その答えが「上回らない」だった、という事実である。
- **negative result の枠 (2026-09-02 版 §9 と同じ区別):** 論文の第 3 幕には 2 種類の負の結果がある。
  (1) 登録した複合主張 S' が測って成立しなかった失敗報告 (S-1a など、既知結果の追試の失敗)、
  (2) **正式な certification protocol が採用構成を `reject` と判定した結果 (本稿の A-2、現行環境での前向きな測定)**。
  両者を 1 つの「うまくいかなかった」へ畳まない。本稿が扱うのは (2) だけである。

---

## 1. 結果節の統制稿

A-2 の性能、別走行の correctness、旧系列との関係の 3 段に分ける。**1 文へ畳むと、同じ run で正しさも性能も確認済みと読まれる**ので分ける。
旧系列の値は本稿の結果の前に置かない (前に置くと前後比較に読まれる)。

### 1.1 A-2 の性能 — 2 つの独立 campaign で、採用静的 backoff は無 backoff 対照を下回った

attempt `t2022-20260828c` は、write-heavy (rratio=5) と balanced (rratio=50) の 2 workload × {無 backoff, 採用静的 backoff} = exact 4 cell を、
Pegasus・CCBench pin `511c953`・Izanagi source commit `639c1dbad4b00d8c51993a653cfc1ebfd22cf300` の正式 protocol
(`paper-story-a2-certification-policy/v2`、protocol SHA-256 `136b823e…d9f4`) で測った。
**各 workload は独立に環境契約された campaign 1 本** (write-heavy: request `954194.nqsv`、bnode141。balanced: request `954195.nqsv`、bnode064。別時刻) であり、
**外側の certification status は policy の workload 順の論理積で決まる** (D1169)。「4-cell run」という短縮はこの構成を隠す。
性能は trace-disabled build の別 run で 5 標本を取った (規律 1 の分離)。

**結果: これら 2 つの campaign では、採用静的 backoff は 2 workload とも無 backoff 対照を下回った。** median throughput の比は
write-heavy (fixed 10 µs) で **−46.3902%**、balanced (fixed 5 µs) で **−65.9080%**、外側の certification status は **`reject`** である (表 1、図 5)。

**この効果に付く限定 (効果の直後に置く)。** 成果物 (`certification.json`) の `a4_noise_floor_status` は `open`、`global_minimality_established` は `false`、
`smallest_observed_sufficient_in_this_two_point_protocol` は `null` であり、**成果物は信頼区間も有意差判定も持たない。**
status は事前定義された median 比の符号だけで決まっている。本稿の表が付ける 95% 信頼区間は執筆者が同じ 5 標本から再計算した記述であり、
効果や status の判定材料ではない。

**測定条件の関門について。** 測定条件の「供給」と「実行側の意味」を独立に見る関門族 (D1198) は、本走行 (2026-08-28) の後、
2026-09-01 に driver 全体へ義務化された。**本走行にはこの関門族が適用されていない。** 本走行の条件の同一性が依るのは、
genome の記録 (`raw/<cell>.json` と `certification.json` の `genome`)、build admission receipt (WAL `build_start` / `commit` payload の
`build_admission_receipt_sha256`)、source-routed evidence (`raw/<cell>.json` の `build_evidence.compile_out_evidence_scope` が
「artifact hash 単独では compile-out の証明にならない」と自ら限定する) までである。**`reject` は当時の protocol 出力として不変である (規律 7)。
意味関門の証拠範囲は本走行について未確立であり、後日 A-2 経路が関門を通っても本走行を遡及的に認証しない。逆に関門が本走行の条件の
意味差を示した場合は、新しい日付の results file で改める (本系列は append-only)。**

### 1.2 別走行の correctness — 4 cell とも certified。性能の判定ではない

同じ 4 cell について、性能を測った workload そのもので trace-enabled build による直列化可能性の検査を**性能 run とは別に**行い、
**4 cell すべて `certified` (anomaly 0)** だった。各 cell は legacy correctness 1 回と full-scale correctness 5 回がすべて pass である。
`certified` が言うのは、その cell で観測した point-key trace が verifier の射程で直列化可能だったことまでである (限定レジストリ `L01`。
verifier の保証範囲は本走行で 1 ミリも広がらない)。**correctness 実行の argv と executable hash は既存 pipeline が独立記録しておらず、後付けも再走もしない**
(`workload_argv_observation = not-independently-recorded-by-existing-pipeline`、D1257)。legacy correctness の観測反復は各 cell 1 回である。
**この段の緑は、§1.1 の性能の status を 1 bit も変えない。** read-heavy (fixed 2 µs) は本 protocol の対象外であり、そこは今も機序論証による外挿である
(但し書き 2、A-6)。

### 1.3 旧系列との関係 — 本稿の結果は旧系列の反証でも再現失敗でもない

論文の exact claim (2026-09-02 版 §8) が持つ旧 `linux-baremetal`・CCBench `6656e93` の記述的 sweep の値は、本稿の comparator ではない。
本稿は旧系列の値を再掲せず、旧値を分母にした効果を計算しない (A-2 policy 自身が旧 commit の役割を
`"originating historical campaign only; never a current comparison value"` と限定している)。
一致しないのは CCBench commit、環境、toolchain (旧は gcc/g++-13、本走行は GCC 11.4.0)、`clocks_per_us` (1800 対 2100)、
numactl (`--interleave=all` 対 なし)、計装 (旧 sweep は `perf stat` 下、本走行は perf 無し)、workload 被覆 (旧は read-heavy を含む 3、本走行は 2) である。
`max_ope` は本 policy が 10 とするが、旧 sweep の条件表に欄が無く一致を確認できない。
**したがって本稿の `reject` は、旧系列の反証でも、再現失敗でも、「Pegasus で一般に効かない」ことの証明でもない。符号差の原因は同定されていない。**
「環境依存である」も原因としては未実証なので断定しない。旧系列の但し書き 1・3 は本稿によって外れない。

---

## 2. 表 1 — exact 4 cell の値 (attempt `t2022-20260828c`)

| workload | cell | genome | throughput 5 標本 (tps、実行順) | median (tps) | mean ± 95% CI (tps) | cv | abort 率 (集約 1 点) | correctness の証拠 (別の trace-enabled run) | 効果 (median 比) |
|---|---|---|---|---:|---:|---:|---:|---|---:|
| write-heavy (rratio=5) | rr5-stock | `BACK_OFF=0`, `BACKOFF_FIXED=-1` | 2715421, 2565367, 2496060, 2470354, 2527542 | 2,527,542 | 2,554,949 ± 119,798 | 0.0378 | 0.7767 | certified (legacy 1 + full-scale 5) | 分母 |
| write-heavy (rratio=5) | rr5-fixed10 | `BACK_OFF=1`, `BACKOFF_FIXED=10` | 1348263, 1355011, 1345709, 1387690, 1362175 | 1,355,011 | 1,359,770 ± 20,944 | 0.0124 | 0.1189 | certified (legacy 1 + full-scale 5) | **−46.3902%** |
| balanced (rratio=50) | rr50-stock | `BACK_OFF=0`, `BACKOFF_FIXED=-1` | 3894140, 3683727, 3636364, 3627357, 3662448 | 3,662,448 | 3,700,807 ± 136,990 | 0.0298 | 0.6903 | certified (legacy 1 + full-scale 5) | 分母 |
| balanced (rratio=50) | rr50-fixed5 | `BACK_OFF=1`, `BACKOFF_FIXED=5` | 1245023, 1196920, 1248603, 1261810, 1260445 | 1,248,603 | 1,242,560 ± 32,945 | 0.0214 | 0.2048 | certified (legacy 1 + full-scale 5) | **−65.9080%** |

外側の certification status: **`reject`** (2 workload の論理積、D1169)。

**表の脚注。**

- 数値は図 5 の provenance JSON (`fig5_a2_certification_reject.provenance.json`、SHA-256 は §5) の `cells` から転記した。provenance の値は WAL の 5 生値からその場で再計算され、
  `certification.json` の median と effects に一致することを生成器が fail-closed で検算している。転記と provenance の突き合わせは作業記録 (`output/insights/2026-09-04_a2-reject-results-section/`) に残した。
- 効果 = `adopted median / stock median − 1`。protocol が判定に使う量であり、論文本文もこの量だけを使う。mean ± CI は不確かさを見せる付記であり、
  **効果を平均比で計算し直さない** (平均比と median 比は同じ生値の別の要約であって丸め違いではない。fig2b の前例と同じ区別)。本稿は平均比の値を書かない。
- 95% CI は 5 標本の t 分布 (`t_{0.975,4} = 2.7764`、半幅 = `t · s / √5`) で再計算した。**`certification.json` 自身は信頼区間も有意差判定も持たない** (§1.1)。
- abort 率は WAL の `leading_indicators.abort_rate` の集約 1 点で、反復値が無い。descriptive な指標であり、CI は付けられず、機序の同定にも使わない。
- correctness の欄は**別の trace-enabled run** の判定である (`L01`: point-key trace の射程まで。D1257: argv は独立記録なし。legacy は各 cell 1 回)。性能の判定ではない。
- 共通条件: threads 48、records 1,000,000、zipf 0.9、rmw 0、max_ope 10、extime 3 s、reps 5、trace-disabled 性能 build、perf 無し、
  gcc/g++ 11.4.0、Pegasus bnode141 (rr5、request `954194.nqsv`、Elapse 3671 s) / bnode064 (rr50、request `954195.nqsv`、Elapse 3594 s)。
- 絶対スループットは論文の headline 値の出所にしない (既存図と同じ扱い)。本稿の主張は同一 workload 内の比だけである。

---

## 3. 限定 (登録表と、本文での実配置)

| # | 限定 | 出所 | 実文の位置 |
|---|---|---|---|
| L-A2-1 | correctness 実行の argv と executable hash は独立記録されておらず、後付けも再走もしない | `certification.json` の `independent_observation_limits`、D1257 | §1.2、表 1 脚注 |
| L-A2-2 | legacy correctness の観測反復は各 cell 1 回 | `cells[].correctness.legacy_repetitions_observed` | §1.2、表 1 脚注 |
| L-A2-3 | read-heavy は protocol の対象外 (A-6 として未取得)。但し書き 2 は外れない | policy の 2 workload 定義、2026-09-02 版 §8 | §1.2、§0 |
| L-A2-4 | `a4_noise_floor_status = open`、`global_minimality_established = false`、`smallest_observed_sufficient… = null`。成果物に CI も有意差判定も無い | `certification.json` | §1.1 (効果の直後)、表 1 脚注 |
| L-A2-5 | 32 GB のメモリ余裕の主張は取り下げ済み。本稿は資源余裕を主張しない | D1263 | §0 |
| L-A2-6 | D1198 の関門族は本走行の後に義務化され、本走行には適用されていない。条件の同一性は genome 記録・admission receipt・source-routed evidence に依る。当時の status は不変 | D1198、D1611、WAL `build_start` / `commit` payload、`raw/<cell>.json` の `build_evidence` | §1.1 (測定条件の関門)、図 5 caption |
| L-A2-7 | 2 workload は別 request・別 host・別時刻の独立 campaign であり、外側の status はその論理積 | D1169、`raw-manifest.json` の `campaign_claims` | §1.1 冒頭、図 5 caption |
| L-A2-8 | 旧 sweep との条件差。符号差の原因は未同定。旧値を comparator にしない | 2026-09-02 版 §2 (f)、policy の `historical_context` | §1.3、図 5 caption |
| L-A2-9 | 性能値は trace-disabled build、perf 無し。絶対値は headline の出所にしない | `raw/<cell>.json` の `build_evidence.performance_trace_disabled_build`、D20 | 表 1 脚注 |
| L-A2-10 | verifier の保証範囲 (`L01`) は本走行で広がらない | claim-evidence 2026-08-26 §3 | §1.2、表 1 脚注 |
| L-A2-11 | 図の平均 ± CI は効果・status・median の信頼区間ではない。abort 率は descriptive な集約 1 点で機序を同定しない | 作図規約 §2 / §4、fig2b / fig4 の前例 | 表 1 脚注、図 5 caption |

---

## 4. 図 5 — キャプション正文と再現

図の現物は `docs/paper-story/figures/fig5_a2_certification_reject.{png,pdf}`、provenance は同名 `.provenance.json`、
生成器は `tools/plotting/plot_a2_certification.py`。**キャプション正文は provenance の `caption` と byte 一致させる**
(fig4 と同型)。正文は `docs/paper-story/figures/README.md` の fig5 の節に置き、本稿はそれを指す。図が描く量と本稿の表 1 は同じ生値から同じ計算で出す。
図は上段に 5 標本・median 短線・標本平均と t 分布 95% CI・無 backoff median の破線 (効果の分母)、下段に abort 率の集約 1 点 (descriptive) を描き、
`outer status: reject` と「correctness は別の trace-enabled run の証拠であり性能の certification ではない」を分けて表示する。

再現は repo root から**計測機の外**で行う (規約 §7)。コマンドは `docs/paper-story/figures/README.md` の fig5 の節が正本。
provenance に記録された生成器の SHA-256 は**生成時の bytes の記録**であり、現行 source を縛る pin ではない (`tools/plotting/README.md` の同旨)。

---

## 5. 一次資料と provenance

- 実走の索引: `output/insights/2026-08-28_t2022-a2-certification-run/README.md`
- 権威 bytes: `output/insights/2026-08-24_paper-story-a2-certification/certification.json`
  (SHA-256 `f685b40d194c9e4b40eed6337b294f38a7ff4aef731829317fd2e83940fbda40`、上の run README が記録している値と一致。schema `paper-story-a2-certification-result/v3`)
- 入力 hash 束縛: 同 dir `raw-manifest.json` (SHA-256 `12d8be7a9cabd404ab3147301c2df7998a731b310ec51a93f9a99b37705a7c35`、schema `paper-story-a2-raw-manifest/v3`)。
  WAL 2 本と raw cell JSON 4 本の SHA-256 を持つ
- 生反復値 (repo 外の durable authority): `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2022-20260828c/`
  の `jobs/<rr5|rr50>/campaigns/<campaign>/runs/wal.jsonl` (`bench_done.payload.tps`) と `jobs/<w>/raw/<cell>.json` (`performance.samples_tps`)。
  両者は 4 cell とも完全一致 (本稿作成時に再計算して確認)
- 図 5 の provenance JSON: `docs/paper-story/figures/fig5_a2_certification_reject.provenance.json` — SHA-256 は本稿の凍結時点で
  `30113d5000f66a15dce5a50ccaa70cd70f79e7b8912e6617451379a1cdae3fef`
- 裁定 (本稿が引くもの): D1169 (outer は workload 単位 campaign の論理積)、D1257 (argv の独立記録は後付けしない)、
  D1263 (32 GB 余裕の取り下げ)、D1198 (測定条件の 2 関門族)、D1611 (inert 比較の差分分類)、D1074 (図が凍結判定値を権威にする限定例外)
- 本稿の作業記録: `output/insights/2026-09-04_a2-reject-results-section/`

---

## 6. この文書が確かめていないこと

- 符号差の原因。旧環境の再測定も、現行環境での旧 commit の測定も行っていない。
- read-heavy の同一 workload certification (A-6)。
- correctness 実行の argv・executable hash の独立観測 (D1257 により後付けしない)。
- 本走行の条件が実行側で同じ意味を持ったこと (D1198 の関門族は未適用)。
- 本走行の 5 標本が within-run noise floor に対してどこにあるか (`a4_noise_floor_status = open`)。
- 図の値は本稿の表と同じ生値から出しているが、図の bytes の同一性は provenance JSON と専用テストが守る範囲までである。
