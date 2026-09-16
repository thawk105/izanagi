# K2 ループ次巡の認可を求める裁定パッケージ — 保存済み proposal-2 (`value=25`) を 1 回評価し、その実測を proposal-3 へ戻す 1 巡 (2026-09-17)

authority: none / default_effect: no-state-change (裁定パッケージ。可変状態の正本ではない)

wave: `dev-wave-k2-loop-round2-package` / branch `worktree-dev-wave-k2-loop-round2-package`
基点 main: `abc7085ae`。**docs のみ、実装差分ゼロ、実走していない。**
起票: [T-2588] の続き (台帳 ID は fold で採番、本書は番号を書かない)。
正本 (1 巡目の一次資料): `output/insights/2026-09-16/t2588-k2-loop-roundtrip/README.md`、
`docs/archive/worklog-phase3-0916-1548.md`。

## 一行で

**T-2588 で保存した proposal-2 (`double now_backoff = 25;`) は未評価のまま止まっている。
評価する認可が無い。** D2044 項 9 の「1 回評価」は entry 1548 で消費済み、D1936 項 1 の 1 本は
T-2581 で消費済み、T-2588 の carry は閉じており、第 20 回裁定 (D2044、39 項) にも次巡は無い。
本書は「次の 1 巡」の認可を求める。

## 何を決めるか

保存済み proposal-2 を既存経路で 1 回評価し、その実測を planner-3 / coder-3 へ戻して proposal-3 を
保存する (評価しない) — この 1 巡を認可するか、認可の形 (1 巡 / 複数巡 / 不認可) をどうするか。

## 1 巡目の結果 (逐語、T-2588 README より)

| 項目 | 値 |
|---|---|
| job / campaign | `1216.nqsv` / `p3-s4-loop-s4-autonomous-409e13f8` |
| variant / genome | `8a84a7b00103` / `silo\|BACKOFF_FIXED=20,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |
| verdict | `serializable` / `certified=true` / anomalies 0 (commits 469618 / aborts 83034) |
| 性能 | median **719324.5 tps** (2 反復 `[727985, 710664]`、run 内 CV 1.70%、`settled=true`) |
| perf 指標 | `llc_miss_rate` / `ipc` は null (計算ノードに `perf` 無し、欠測であって 0 ではない) |
| 終端 / 停止判定 | `1 committed / 0 aborted / 0 skipped`、`outcome=certified`、`iteration=1`、**`continue`** |
| proposal-2 | planner `decrease` / `small`、coder `value=25`、`confidence=medium`、`classification=known_result_conditioned_derivative`、`prior_critic_reverse=false`。production 検査 3 本 (schema / 文法 / loader) OK。**未評価** |

知識源は測定記録 1 件 (manifest digest `396cd559…`、WAL sha256 `2163b794…`、`env_tag=linux-baremetal`、
機体は本走と別)。`value=25` は 20 / 30 / 40 のいずれでもない未評価の値である。

## 次巡の目的

1. proposal-2 を評価して terminal verdict を得る (正しさ → 性能の順、anomaly は即 reject)。
2. その実測 (同機体・同配線の 2 点目) を planner-3 / coder-3 の型付き入力へ戻し、proposal-3 を保存する。
   同機体 2 点なので whiteboard の `delta_pct` を初めて非 null で書ける。
3. 「役割が作った提案 → 評価 → 実測の還流 → 次提案」の往復が **2 巡連続で** 既存経路だけで閉じるかを示す。

**目的でないもの:** 新 CC 構造の合成、B-4 正式実験、性能優越の主張、critic 診断の機械還流。

## 範囲 (既存経路のみ、新機構なし)

- 実行主体・入力・出力は run-card `output/insights/2026-09-10_cc-next-precheck/run-card.md`
  の表と同じ。親が射影、登録 role (`planner-v4` / `coder-v4-autonomous-k2` / `critic`) が生成・診断、
  評価は `tools/pegasus/p3_s4_loop_pegasus.sh` を計算ノードへ 1 本 (`IZANAGI_S4_PROPOSAL_PATH` に
  proposal-2、`IZANAGI_S4_CODER_ROLE=coder-v4-autonomous-k2`)。
- 知識源・manifest は 1 巡目と同じ bytes。K2 射影は 1 巡目の `materials/leakproof-context-k2.md` を再利用する
  (T-2703 の `src/coder-leakproof-context.md` 配線規模不一致は未了 (carry 1594) で、1 巡目と同じく射影側で回避する。
  file は直さない)。
- **submit-tree は現行 main で新規に切る** (提案 (P2))。1 巡目の tree (`d97c423bd`) は再利用しない。理由:
  T-2702 (entry 1565、`106c0ec04`) が digest の集約を是正済みで、2 巡目はその runner で走るべきである。
  campaign ID は identity 5 key が同じなので `409e13f8` のまま、新規 WAL、skip は起きない (1 巡目で実測)。
  規律 7: 現行コードとの差は 1 巡目の測定を無効にしない。
- 1 巡目以後の経路変更は 2 件だけ: `c79437d24` (driver 直起動で sources 非空なら `--coder-role` 必須。job body
  は元々 env で渡しており影響なし)、`106c0ec04` (T-2702)。PIN `511c9538…` = gitlink、verifier 無変更。
- 変えないもの: 正しさゲート・identity・検疫・帰属照合・machine budget・scale (records=100000 / threads=4 /
  rr50 / skew0.9 / rmw=false / extime=1 / reps=2)。承認管理の新機構・gate・台帳は作らない。

## 予算 (run-card と同値、新設ではない)

- 親の上限: 評価 job **1 本**、critic **1 回**、planner-3 / coder-3 **各 1 回**。再投入・再抽選・比較 arm なし。
- 既存 machine budget 10 iteration / 3600 秒、reservation 3 時間はそのまま (10 本走らせる認可ではない)。
- 本 wave の相談・codex 子はゼロ。実走 wave の工数は 1 巡目と同規模 (Claude role 3 種 + 計算ノード job 1 本)。

## 停止条件 (すべて既存 harness・runbook の規則)

1. schema / 指示検出 / 帰属 / 検疫の赤 → proposal-2 を拒否、実走せず記録して終了。
2. anomaly ≥ 1 → variant 即 reject (規律 2)。性能を推定しない。構造化診断を記録し、harness の停止判定に従う。
3. job rc ≠ 0、trace parse / build failure、verifier terminal 不取得 → 停止、再投入しない。
4. harness の `check_stop` が `continue` 以外 → 停止、proposal-3 を作らない。
5. `continue` → critic 1 回 → planner-3 / coder-3 → proposal-3 を保存して**終了** (3 巡目へ進まない)。
6. proposal-3 が既知値 (20 / 25 / 30 / 40) または検査赤 → そのまま記録、再抽選しない。
7. 2 点の差が run 内 CV (1.70%) 以内なら改善とも退行とも読まず、whiteboard の `result` は harness の既存規則で書く。

## 既知限界 (2 巡目でも変わらない)

- **critic の診断は次生成の型付き入力へ届かない。** 届くのは測定値・5 field の whiteboard・
  `planner_direction` だけで、`prior_critic_reverse` の消費者は `_fold_critic_reverse` と停止判定のみ。
  親の解釈を介した runbook 上の還流と機械的消費を同一視しない (T-2588 段 3 の 2 レンズが独立に指摘)。
- perf 欠測 (`llc_miss_rate` / `ipc` null) は同機体なら続く。役割はこの 2 軸を使わない。
- T-2702 後は digest 行から latency が消え、偶数 reps の abort_rate が中央値演算になる。1 巡目の digest
  (abort 7.75% は速い側の代表 rep) とは集約規則が異なるので、2 巡目の planner 射影ではこれを開示する。
- 役割の自己申告 `classification` と呼び手宣言は driver が照合しない (1 巡目で一致したが機構の保証ではない)。
- legacy critic を使うため B-4 ablation には非適格。

## 選択肢と推奨

- **A (推奨): 1 巡だけ追加認可する** — D2044 項 9 と同形、予算・停止条件は上のとおり、既存経路のみ。
  帰結: proposal-2 が評価され、同機体 2 点の還流が閉じる。3 巡目には再び認可が要る (今の運用と同じ)。
- **B: 停止条件付きで最大 N 巡 (例 3 巡) を包括認可する。** 帰結: 巡ごとの裁定往復が減る。ただし各巡で親の射影と
  Claude role 起動が要り無人ではなく、critic 還流の限界を抱えたまま巡を重ね、「1 巡は改善の実証ではない」
  (T-2588) の段階で探索の有効性が未実証。蹴る理由: 停止条件が harness の `check_stop` と予算しか無い。
- **C: 認可しない (T-2703 と critic 還流経路の整備を先にする)。** 帰結: 主経路が止まる。T-2703 は射影で回避済み、
  critic 還流は新機構で run-card の範囲外。蹴る理由: 待つ理由が無い。

主経路 (CC 自動合成) との距離: **主経路そのもの**。

## 保留の影響

主経路の 2 巡目が止まり、proposal-2 は未評価のまま残る。他の作業は止まらない。

## 返答例

「A で。1 巡だけ、既存経路のみ、予算と停止条件は本書のとおり。submit-tree は現行 main で新規に切る。」

## 主張しないこと

- 2 巡目が閉じても、合成による改善や探索の有効性の実証にはならない。
- 新しい値は固定 backoff の初期値であって新しい CC 構造ではない。
- proposal-2 の評価結果が certified でも、候補間の certified な選択ではない。
- 1 巡目の 719324.5 tps は同機体 2 点目との比較にだけ使い、歴史測定 (`linux-baremetal`) との差を性能優越の根拠にしない。

## 裁定パッケージ

- 裁定待ち: **K2 ループ次巡 (proposal-2 `value=25` の 1 評価 + proposal-3 への還流) の認可** — 選択肢 A / B / C、推奨 A。
- 起票元: 本 wave (T-2588 の続き)。台帳 ID は fold 採番。/rulings の収集 1 (worklog 次の一手の新規項)・2 (本節)・
  3 (repo 外 `dev-wave-jobs/rulings-inbox/2026-09-17-k2-loop-round2-authorization.md`) のいずれでも索引される。
- 結果: **未裁定** (本書は認可ではない。裁定は decisions へ記録されるまで効力を持たない)。

## 証拠の所在

- 1 巡目: `output/insights/2026-09-16/t2588-k2-loop-roundtrip/` (README、`materials/proposal-2.json`、
  `verbatim/`、`evidence/`)。repo 外原本は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2588-k2-loop-roundtrip/`。
- run-card: `output/insights/2026-09-10_cc-next-precheck/run-card.md`。
- 裁定の逐語: `docs/decisions.md` D2044 項 9、D1936 項 1。
- 本 wave の brief と handoff: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-round2-package/brief.md`、
  同 `handoff/dev-wave-k2-loop-round2-package.md`。
