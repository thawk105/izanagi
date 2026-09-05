# Silo 上の Cicada 型 adaptive backoff の 3 定数を動的化する変異 — 事前登録

D1505 (律速は更新間隔、上限は効かない) と D1506 (基準線は無 backoff と調整済み adaptive の 2 本) の
先にある問い「定数を固定せず、走行中の観測から更新の発火・刻み・上限を決めたら、調整済み adaptive
に対して何が変わるか」の事前登録である。一次資料は
`output/insights/2026-09-02_cicada-adaptive-three-constants.md`。測定対象の protocol は Silo
(`ycsb_silo.exe`) であり、「Cicada」は adaptive backoff 算法の由来を指す。

## 0. 本書の版と発効

**v1.1 (2026-09-05)。** v1 (commit 3b0d7a1cb、段 4 で凍結) を、段 6 の敵対レビュー 2 本の所見に従い
**性能値を 1 つも見る前に**改訂した。変更は次の 6 点で、腕・値・workload・threads・反復数・判定式・等価域・
仮説の受理条件は変えていない。(1) §3 に hostname 重複の扱いを足した。(2) §4 に仮説単位の三値判定の規則を
明記した。(3) §5 の診断 run を rep index 0 の exact 1 job、各 run に更新 ≥1 件と固定した。(4) §6 に
「partial block の表は親が journal から作る」と、点欠落時の対比の n を明記した。(5) §8 の図の入力を
「利用可能な 6 または 7 complete block + 診断 1」に直し (§6 の n=6 と矛盾していた)、記録する束縛 field を足した。
(6) 段 6 の時点で投入済みだった canary 2 job (perf rep0 = `977999.nqsv`、診断 = `978000.nqsv`) は、この改訂と
patch B の修正 (計数窓の時刻を counter 走査の後で取る) の前の実行体で走ったため、事前登録の block には数えず
Pegasus 経路の生死確認とだけ位置づける。その性能値は本書の改訂前後を問わず判定に使わない。

v1 は dev-wave `dynamic-backoff-mechanism` の段 4 で凍結し、性能値を 1 つも見る前に
commit した。本走 (perf / 診断 / 認証) は本書を含む commit を指して起動し、成果物 JSON は
その commit hash (`repo_head`) と本書の bytes の sha256 (`prereg_sha256`) を記録する。
結果 commit より後に書かれた変更は事前登録として数えない。発効後の変更は旧版を Git 履歴に残したまま
新しい commit で行い、変更理由と時点を本節へ明記する。

**本書は盲検の holdout ではない。** T-2187 (3 定数の格子) と T-2216 (機序解析) の結果を既に見たうえで
腕と仮説を決めている。前向きに固定できるのは「本 grid の throughput を一度も観測していない時点で
§2〜§7 を固定した」ことだけである。

## 1. 主張してよい範囲と限界

- **すべて未認証の性能値である。** trace-disabled build の throughput は直列性の検査を通していない
  (絶対規律 1・2)。認証 (§7) は正しさだけを対象にし、性能値を認証しない。
- 単一環境 (Pegasus gen_S、48 物理コア、HT 無効)、単一 protocol (Silo)、YCSB 3 workload、
  records 1,000,000 の下でしか言えない。
- 基準線は D1506 の 2 本 (`none`、`tuned`) である。**既定 adaptive (`stock`) 単独比の優位は書かない。**
  `stock` は probe が構造的に要求する陽性対照であり、§4 の H6 にだけ使う。
- 24 点のうち都合のよい点を選んで「どこかで勝った」とは書かない。判定は §4 の複合条件だけで行い、
  全 24 点の CI を伏せずに表へ出す。

## 2. 腕 (7 cell)

機械 label と exact な cell 文字列 (probe の 5 field / 11 field 書式):

| label | cell 文字列 | 役割 |
| --- | --- | --- |
| `none` | `none:0:100:1000:10` | 基準線 (D1506)、`BACK_OFF=0` |
| `stock` | `stock:1:100:1000:10` | 陽性対照 (probe が要求)、H6 のみ |
| `tuned` | `tuned:1:1:1000:2560` | 基準線 (D1506)、刻み 1 µs / 上限 1000 / 更新間隔 2560 |
| `tuned-u10240` | `tuned-u10240:1:1:1000:10240` | 対照: 時間のみで更新間隔を 10240 µs にした腕 |
| `cw` | `cw:1:1:1000:2560:10000:10240:0:100:100:0` | 計数窓のみ (K=10000、最小 2560 / 最大 10240 µs) |
| `cw-as` | `cw-as:1:1:1000:2560:10000:10240:1:1:4:0` | 計数窓 + 適応刻み (1→2→4 µs、反転で半減) |
| `cw-as-dyn` | `cw-as-dyn:1:1:1000:2560:10000:10240:1:1:4:1` | + 動的上限 (上限で負勾配なら半減、下限 50 µs) |

11 field の意味は `label:back_off:step_us:ceiling_us:update_us:count_window:count_cap_us:step_adapt:step_min_us:step_max_us:dyn_ceiling`。
K>0 のとき `update_us` は「counter を読む最小間隔」、`count_cap_us` は「最大間隔」であり、更新は
経過 ≥ `update_us` かつ (commit 数 ≥ K または 経過 ≥ cap) で起こる。`step_min_us`/`step_max_us` は
`step_adapt=0` のとき inert (stock 既定 100/100 を書く)。

**値の根拠。** K=10000 は `tuned` の 2560 µs 窓に write-heavy 48 スレッド (約 3.95 M tps) で入る commit 数
(約 10,100) と同じ計数である。read-heavy 48 スレッド (約 10.2 M tps) では同じ窓に約 26,000 入るので
K は約 1 ms で到達し、`cw` は最小間隔 2560 µs で更新する (= `tuned` と同じ発火)。6 スレッド
(約 1.3〜1.6 M tps) では K 到達に 6.4〜7.6 ms かかり、実効窓は 2560 µs より長く 10240 µs より短い。
cap=10240 は T-2187 段 3 で更新間隔 2560 とほぼ重なった点で、`tuned-u10240` がその対照である。
刻みを整数 µs に限るのは、`last_backoff_` が `uint64_t` で sub-µs の刻みが偽ゼロ勾配を作るため
(T-2216 §3)。上限の下限 50 µs は T-2187 段 3 が測った既知点。

**新 define の既定値はすべて stock 同値**で、5 field cell の genome は拡張前と byte 同一である。

## 3. 測定条件

| 項目 | 値 |
| --- | --- |
| workload | write-heavy (rr 5) / balanced (rr 50) / read-heavy (rr 95)、zipf 0.9、rmw 0、max_ope 10 |
| threads | 6, 12, 18, 24, 30, 36, 42, 48 |
| records | 1,000,000 |
| extime | 3 秒、1 job あたり 1 rep |
| 反復 | 7 ノード × 1 rep = n 7 (block = job = node)。1 job が全 7 腕 × 3 workload × 8 threads = 168 process を回す |
| 腕の実行順 | rep i (0..6) は 7 腕の巡回順を開始位置 i から回す (時間ドリフトと腕の交絡を抑える)。順序と hostname を JSON に記録する。scheduler が複数 block を同じノードへ置くことは拒否せず、hostname の重複を provenance に列挙する (block = job であり、ノードの一意性は主張しない) |
| build | trace-disabled (`CCBENCH_TRACE=0`、`BACKOFF_TRACE=0`)、perf 計測なし。perf build に診断 symbol・文字列が 0 個であることを probe が検査し JSON に記録する |
| ccbench | pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` + `patches/cicada-adaptive-params.patch` (sha256 `9b2153e0547e167888ba2616750951365c4a075a80f9a95be6000e60b6f8f54b`) + `patches/cicada-adaptive-dynamic.patch` (本書を含む commit で凍結) |
| driver | `tools/pegasus/probes/t2187_adaptive_const_probe.py` / `.pbs` (performance mode、拡張 cell 書式、結果 schema v2) |
| 出力 | `/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf/` (点ごとの append-only journal + 最終 JSON) |
| 集約 | 生値。腕の比較は同一 block 内の対内 log 比 (§4)。単独系列の 95% CI は t 分布 (n=7) |

**見積もり (投入前)。** 1 process ≈ 4.25 s (T-2187 段 2 の実測 8.5 分 / 120 process、worklog (1204)) なので
168 process ≈ 11.9 分、build 7 本 ≈ 3.5 分、prologue ≈ 2 分、計 ≈ 17.5 分/job。walltime は 40 分。
queue 待ちは別勘定で見積もりに含めない。

## 4. 仮説と判定式

block i (= job = node)、workload w、threads t について、腕 a と b の対内 log 比
d_i(a, b; w, t) = ln(TPS_{i,a,w,t} / TPS_{i,b,w,t}) を取り、n block の平均 d̄ と s_d から
95% CI = d̄ ± t_{0.975,n−1} · s_d / √n (n=7 なら t=2.4469、n=6 なら 2.5706) を出し、
端点を 100·(exp(x)−1) % で示す。**等価域は throughput 比 [0.97, 1.03] (±3%)** とする
(B-10 の等価域と同じ幅。本機構の CI 幅 (T-2187 で ±1〜1.4%) より広く、実用差として意味のある下限)。

判定語 (対比 a/b):
- **実用優越**: CI 下端 > +3%。
- **非劣性**: CI 下端 > −3%。
- **等価**: CI 全体が [−3%, +3%] 内。
- **実用劣化**: CI 上端 < −3%。
- それ以外は **inconclusive**。非有意を等価と呼ばない。

「robust benefit」= 全 24 点で非劣性、かつ (write-heavy, 48) と (balanced, 48) の両方で実用優越
(intersection-union 判定。結果を見てから endpoint を選ばない)。

| 仮説 | 対比と受理条件 | 答えられる問い | 答えられない問い |
| --- | --- | --- | --- |
| H1 全動的機構 | `cw-as-dyn / tuned` が robust benefit | 全機構を積んだ実装が調整済み adaptive に追加価値を持つか | どの部分が効いたか、別環境・別 workload |
| H2 no-backoff safety | read-heavy 8 点すべてで `cw-as-dyn / none` が非劣性 | backoff 不要域で実用的な損を避けたか | 機構が backoff を無効化したか |
| H3 計数窓 | `cw / tuned` が robust benefit | 計数窓 (実効窓 2560〜10240 µs) が tuned より有効か | 計数そのものと長い実効間隔のどちらか (H7 と併読) |
| H4 適応刻み | `cw-as / cw` が robust benefit | 刻みの走行中伸縮の増分効果 | 勾配推定の正しさ |
| H5 動的上限 (「効果なし」の予測) | 全 24 点で `cw-as-dyn / cw-as` が等価 | 動的上限がこの範囲で実用差を生まないという予測 | 固定上限一般、未測の低い上限 |
| H6 陽性対照 | 48 スレッドの 3 workload すべてで `stock / tuned` が実用劣化 | 既知の stock 劣化が今回も再現するか | 動的腕が優れていること |
| H7 長い間隔の対照 | 全 24 点で `tuned-u10240 / tuned` が等価 | 更新間隔を 10240 µs にしただけでは変わらないという T-2187 段 3 の再現 | — |

**仮説単位の判定 (三値)。** 各 H について、`accepted` = 受理条件の全述語を満たす。`rejected` = いずれかの点の
CI が受理条件を満たし得ないことを示す (robust benefit なら「いずれかの点で CI 上端 < −3%」または「endpoint の
CI 上端 ≤ +3%」、非劣性なら「いずれかの点で CI 上端 < −3%」、等価なら「いずれかの点で CI 全体が等価域の外」、
実用劣化なら「いずれかの点で CI 下端 > −3%」)。それ以外は `inconclusive`。判定対象の点は H1・H3・H4・H5・H7 が
全 24 点、H2 が read-heavy の 8 点、H6 が 48 スレッドの 3 点であり、図と provenance は判定対象外の点を
区別して示す。全点 n ≥ 6 でないときは accepted / rejected を出さず inconclusive とする (§6)。

H3 は H7 と組で読む: H7 が等価で H3 が優越なら「計数で決まる可変窓」の効果、H7 が非等価なら
H3 の差は「間隔の長さ」を含む。H5 が棄却された場合は向きを問わず D1505 の再評価を次の一手に立てる。
H1〜H7 以外の対比も全点 CI 付きで表に出すが、事前登録した判定には数えない。family-wise の主張が
要るなら対比ごとに 24 検定を Holm 補正する。abort 率は副次指標 (同一 block 内の percentage-point 差) で、
判定には使わない。

## 5. 診断 run (別 build・別 run、headline 不適格)

`BACKOFF_TRACE=1` の診断 build で、動的 3 腕 (`cw`, `cw-as`, `cw-as-dyn`) × 3 workload × threads {24, 48}
を **rep index 0 の exact 1 job** (18 process) で走らせる (別の rep index は受理しない。各 run に更新 record が
1 件も無ければその JSON は完了しない)。leader スレッドの更新ごとに (seq, tsc, 窓の経過 µs, 窓の commit 数,
発火理由 count|cap|time, 更新前後の `Backoff_`, 勾配符号, 刻み, 上限, 上限変更, parity 分岐) を記録し、
probe が offline で**方向的中 (directional success)** = 更新 i の action 符号 (後 − 前) と、更新 i+1 で
観測した throughput 差の符号の一致率 (action 0 は unscored) を計算する。これは内部推定器の
自己一致ではなく、行動が次窓の throughput を上げたかの一段先の指標であり、「accuracy」とは呼ばない。
**診断 build の throughput は headline に使わず**、図と本文で「診断 build 由来・計装系の軌跡」と明記する。
perf build の binary に診断 symbol (`izanagi_backoff_trace` 接頭辞) と文字列 (`IZANAGI_BACKOFF_TRACE`) が
0 個であることを `nm` と `strings` で示す。ring は 65,536 件で、overflow (`dropped > 0`) の run は
要約に使わない。

## 6. 欠測規則

- 原則 7 complete block。1 block が完走しない (walltime 超過・例外) 場合は全点共通で n=6 (df=5) で判定し、
  補完・外れ値除外はしない。n < 6 なら確認的判定をせず「n 不足」と書く。
- journal に残った部分 block の点は、表には出すが判定には使わない。この表は親が journal (`<out>.journal.jsonl`)
  から insight に作る。図と判定の入力は complete block の JSON だけである。
- 点の欠落 (timeout) がある対比は、両腕の row がある block だけで対内比を取り、その点の n を provenance に書く。
  n < 6 の点の判定語は `inconclusive` (理由 `n-insufficient`)。
- infra 失敗 (queue・ノード障害、metric を見ていない) だけは同じ rep index を新しい job で再投入してよい。
  複数の有効 receipt ができたら最初に完走した job を採る。
- 1 process が timeout (180 秒) で落ちた点は欠測とし、その block はその点だけを欠く。欠測は理由と job ID を
  表に残す。

## 7. 認証 (正しさのみ)

T-2189 が main に置いた `--mode certify` (連言 10 項、陽性対照、24 request の group receipt、verifier identity
の事前固定) を、動的腕のうち全機構 on の `cw-as-dyn` 1 腕に対して 3 workload × 8 slot = 24 request で
走らせる。連言・陽性対照・identity 束縛・24 request のいずれも緩めない。**認証するのは
「full-on build の観測 24 走行が serializable」であり、機構の各枝 (K 発火・刻み倍増・上限変更) の
被覆は認証しない。** `cw` と `cw-as` は compile-time の部分集合だが**未認証**と明記する。
認証は perf/診断の完了後 (performance artifact の path/sha を束縛する契約上、同時投入は不可) に
pilot 1 本 → 残り 23 本の順で投入する。1 job の見積もりは prologue + trace build + run + 陽性対照 +
verify (T-2189 実測 87〜459 秒) で 15〜25 分、walltime 2:15 (上限 24 × 2.25 ノード時間)。
出力は `/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/certify/`。

## 8. 束縛

- 成果物 JSON (perf / 診断 / 認証) は `repo_head`、`repo_status_clean`、`prereg_sha256`、ccbench pin (短縮 `ccbench_commit` と
  full `ccbench_head`)、`patch_sha256` (A)、`dynamic_patch_sha256` (B)、順序付き `patch_stack` と `patch_stack_sha256`、
  `driver_sha256`、`pbs_sha256`、`driver_argv`、hostname、腕の実行順 (`cell_order`)、prologue と job 全体の所要を記録する。
  投入 (qsub) の argv と job ID は親が job dir の台帳 (`submitted-jobs.txt`) と insight に記録する。
- 図は `tools/plotting/plot_dynamic_backoff.py` で計測機の外で生成し、provenance に全入力 (利用可能な 6 または 7 の
  complete block + 診断 1 file) の sha256、対内 CI と判定、abort 率の対内 pp 差、生成器 sha256 を記録する。
- insight は `output/insights/2026-09-05_dynamic-backoff-mechanism/` に書く。
