# 段 4 裁定 — md_11 Cicada baseline 較正 (2026-09-29 JST、親)

入力: s1-brief.md、plan.md (段 2)、consult-a.md (規律・正しさ・妥当性)、consult-b.md (実効性・過剰・見積り)。裁定 inbox 再走査: 開始後の main 前進は ab5fd6bd9 ([T-2852]、本件と無関係) のみ。

## 所見の裁定

| ID | 裁定 | 採否・扱い |
|---|---|---|
| A-F1 / B-B2 (GC=10 選抜で他 GC の最速を見逃す) | real | 採用。J1 で rr50 は全 24 点 × GC {10,100,1000} を測る (後続比較の格子)。他 workload は GC=10 選抜の限界を一次資料の結論名に書く (「GC=10 で選抜した候補中の観測最良」)。rr50 は「GC {10,100,1000} 上の 24 点全体の観測最良」まで名乗れる。 |
| A-F2 / B-B7 (表示行では binding を示せない) | real | 採用。build ごとに `CMAKE_EXPORT_COMPILE_COMMANDS=ON` で `compile_commands.json` を出し、ycsb_cicada.exe を構成する cc/cicada の TU の compile command に `-DTRACE=0`・`-DADD_ANALYSIS=0`・各 genome macro 値・(待機型のみ) `-DWORKER1_INSERT_DELAY_RPHASE=1` と `-DWORKER1_INSERT_DELAY_RPHASE_US=1000` が期待どおり現れることを照合し、不一致・欠落はその build を無効にする。`#ShowOptParameters()` 照合は「表示値の照合」と呼び、PROMOTION の実効は OPT との組で説明する。 |
| A-F3 (選抜と推定を同じデータで行う) | real | 採用。J1 = 探索 (選抜だけ)、J2 = 確認。最良・同等集合・図 (b) の値は J2 のデータだけから計算する。J2 の job 割付けは条件 (workload) 単位で、J1 の genome 単位の割付けと別になる。 |
| A-F4 / B-B5 (CV 幅と候補差は別の量) | real | 採用。名称は「観測した control の job 間 CV 幅内の候補集合」。探索用の記述的リストで、同等性・採否の証明ではないと明記。全点が入れば全点を列挙、control が最大なら control を best と書く。 |
| A-F5 (floor と誤読) | real | 採用。`between_run_noise_*`・calibration の公式 floor・compare・採否に接続しない。D145 の意味の Cicada floor は未取得と明記。値には control 構成・job 数・投入時刻 cluster 数・host 数を付ける。 |
| A-F6 / B-B4 (待機型の代表性) | real | 採用。W5 は「worker 1 の commit 前に 1 ms の固定待機を入れた診断 workload」と定義し別枠で報告。100 操作型・1 ms は固定した試験条件で、長さ一般へ外挿しない。 |
| A-F7 (perf 付き値の流入) | real | 採用。perf 付きの走は較正記録専用。within-run 10 reps・J1・J2 は perf なし。順位・図は perf なしの走だけから。 |
| A-F8 (genome × job の交絡) | real | 採用。各 rep で genome 順を事前固定の seed で並べ替え、control を毎 rep に含める。run ごとに開始時刻・load average・直前 run を記録。 |
| A-F9 / B-B6 (飽和の断定) | real | 採用。「観測範囲内の飽和候補」/「D15 の RSS 下限採用」/「飽和未判定 (perf 不可)」を分けて書く。 |
| A-F10 (正しさ未検査) | real・scope 外 | 実装しない。全値を「正しさ未検証の診断値」と書く。最良設定を md_3 の trace build で検査する作業を次の一手として台帳へ (INLINE_VERSION_OPT=1 かつ PROMOTION=1 は現行 trace patch で compile 不能と明記)。 |
| B-B1 (共通動作点) | real | 採用。rr50 の較正 N が 1M でなければ、J2 に rr50@1M × GC {10,100,1000} × (上位 3 ∪ control) を足す。1M なら J1/J2 の rr50 がそのまま共通点。 |
| B-B3 (build 数・見積り) | real | 採用。待機型は別 build (genome ごとに 2 build)。各 job は計測前に全 build を並列で済ませ (計測中は build しない)、J0 で通常型・待機型の build 秒・DB load 込みの run 秒を別々に測る。W5 の全 24 点走は既定から外す (下記)。 |
| B-B8 (private helper) | real | 採用。`s3_mocc_lock_coverage` の `_resolve_toolchain`・`_prepare_dependencies` の利用を driver 内の 1 関数に閉じる。policy 読込と configure 引数は新 driver が現 pin 用に持つ。 |
| B-B9 (J0 判定表) | real | 採用 (下記 J0 判定表)。 |
| plan (P4) perf 不在時 | real | 採用 (plan の RSS 下限 pure 関数)。 |
| plan (P8) mocc policy | real | 採用 (plan の修正どおり)。 |

## plan v2 (要点)

- **workload** (全て 48 thread、skew 0.9、rmw 0): W1 rr5 / W2 rr50 / W3 rr95 (各 max_ope 10)、W4 many-ops = rr95・max_ope 100、W5 read-then-wait = rr50・max_ope 10 + worker 1 に commit 前 1 ms (build 時 define)。
- **genome**: `CICADA_SPACE` の 24 正準点。control = CMake 既定の正準点 (BACK_OFF=1, INLINE_VERSION_OPT=0, INLINE_VERSION_PROMOTION=0, REUSE_VERSION=1, WRITE_LATEST_ONLY=0)。※ plan の「全 5 軸 0」は採らない (CMake 既定の cache は BACK_OFF=1・REUSE_VERSION=1、Options.cmake)。
- **J0 (1 job)**: 依存準備、control の通常 build と待機 build。(a) 待機の生死確認: thread_num=2・rr50・N=1M・3 reps で待機あり/なし。(b) 較正: W1〜W4 を 1M→2M→4M→8M (early stop は run_sweep の条件) × 3 reps、perf あり。W5 の N は W2 と同じ。(c) within-run: 各 workload の確定 N で control 10 reps (perf なし)。(d) 単価: 依存準備秒、build 秒 (通常・待機)、run 秒 (workload 別、DB load 込み)。
- **J1 (探索、4 job)**: 24 genome を 6 点ずつ + 各 job に control。条件 = W1・W3・W4 は GC 10、W2 は GC {10,100,1000}。reps 3、各 rep 内で (genome, 条件) 順を固定 seed で並べ替え。W5 は J1 で走らせない。選抜 = 各条件で job 内 control 比 (その job の同条件 control の rep median に対する比) の median 上位 3 genome (W2 は GC 3 点の最大値で順位)。同率は canonical genome 順。
- **J2 (確認、workload 単位で最大 4 job)**: 各 workload の上位 3 ∪ control × GC {1,10,100,1000,10000} × reps 3。W5 は W2 の上位 3 ∪ control を待機 build で GC {10,100,1000}。各 job に GC=10 の control を含む (session 標本を兼ねる)。rr50 の N≠1M なら B-B1 の追加条件。
- **ばらつき**: workload・N・GC=10・control genome の job 別 session median (その job の control rep の median) の標本 CV。J0 (within-run 10 reps の median を 1 標本)、J1 の 4 job、J2 の該当 job。job 数・投入時刻 cluster 数・host 数を併記。
- **最良・集合 (事前固定)**: workload w について J2 の各 (genome, GC) の score = 同 job の GC=10 control の rep median に対する比の rep median。best = score 最大。集合 = score ≥ score_best × (1 − cv_w)。cv_w 欠落・session 数 < 3・候補欠測はその workload の集合を判定不能。計算は一次資料 (と生成器) で行い、compare・gate に入れない。throughput の絶対値 (tps の median) も併記する。
- **図**: (a) workload 別の設定ごとの throughput (J1 の 24 点、control 比と絶対値、探索値と明記)、(b) gc_inter_us (対数) と throughput (J2、workload 別、上位 3 と control、maxrss を副表示)。
- **出力**: `output/env/pegasus/vhash-cicada-baseline-tuning/<job-id>/` に create-only の runs.jsonl・job manifest・stdout 原文。job id は親が spec で発行。
- **置き場**: `tools/vhash_cicada_tuning/` (driver・model・analysis)、`tools/plotting/plot_vhash_cicada_tuning.py`、`orchestrator/tests/test_vhash_cicada_tuning.py`・`orchestrator/tests/test_plot_vhash_cicada_tuning.py`、`tools/plotting/README.md` 追記。

## J0 判定表 (結果前に固定)

| J0 の観測 | 後続 |
|---|---|
| 待機の生死確認で「あり/なし」の throughput 比 ≥ 0.75 (2 thread で worker 1 が 1 ms 待てば総 throughput はほぼ半減するはず) または待機 build が compile 不能 | W5 を欠測として残し、J2 から除く。他は続行 |
| perf が使えない | D15 の RSS 下限 (maxrss×1024 ≥ 4 × L3) で N を決め「飽和未判定」と記す。L3 は実測 (sysfs) を使い、110,100,480 B と違えば記録 |
| 8M でも RSS 下限・飽和とも不成立 | その workload は N 未決定。1M で続行せず後続から除く |
| control build・run が失敗・binding 不一致 | 停止 (後続を投入しない) |
| 予算 (下記) を超える | 縮小梯子を上から適用、全段で超えるなら投入せずユーザー確認 |

## 予算と縮小梯子 (結果前に固定)

- 線 = 合計 120 node 分 (job の walltime 上限の和で判定。J0 は実 Elapse で置き換える)。開発検査の予約 = 40 node 分 (受入 2 回 × 15 分 + 焦点走・変異 10 分)。計測の上限 = 80 node 分 (J0 含む)。J0 walltime = 00:20:00。
- J1/J2 の walltime = (依存準備秒 + 並列 build の実測秒 + Σ run 単価 × run 数) × 1.5 を分に切り上げ。
- 縮小梯子 (超えたら順に適用): R1 J2 の上位 3 → 2。R2 J2 の GC 格子 {1,10,100,1000,10000} → {10,100,1000,10000}。R3 J1 の reps 3 → 2。R4 W4 を J1 から外し J2 で control + W3 の上位 2 だけ。R5 (なお超過) 投入せず、見積りと梯子を一次資料と最終報告に書いてユーザー確認。

## 変異の事前登録 (実装後に位置と単一理由性を確認し、成り立たなければ登録を外して再照準)

| ID | 変異 | 殺す test (予定) |
|---|---|---|
| M1 | genome 列挙から promotion 制約を外す (32 点) | 24 点・制約の test |
| M2 | ShowOpt 表示値照合で 1 軸 (WRITE_LATEST_ONLY) を比較しない | 1 軸だけ違う負例 |
| M3 | compile command 照合で `TRACE=0` を見ない | TRACE=1 の compile command 負例 |
| M4 | RSS 下限の比較 `>=` を `>` に | 境界ちょうどの正例 |
| M5 | 集合の境界 `(1 − cv)` を `(1 + cv)` に | 境界の正例・負例 |
| M6 | CV を母標準偏差に | 数値 test |
| M7 | rr20/rr80 の拒否を外す | rr20 の負例 |
| M8 | 作図の重なり検査を no-op に | 重なりを作る実 Figure の負例 |
| M9 | J0 の待機生死判定の閾値の向きを反転 | 比 0.5 と 0.95 の正例・負例 |

## 実装子への分割
所有単位 1 (driver・analysis・model・plotter・test 2 本・README 追記は相互依存)。Codex author 1 本。

## 追補 (段 5 後、J0 投入前、親)

- R-add1: 親の J0 前レビューで、Cicada は `#ShowOptParameters()` を印字しない (定義のみ、呼出しは cc/ss2pl/ss2pl.cc:117 だけ) と判明。brief (P8) と plan・相談の前提の誤り。表示値照合を外し binding は compile command 照合 + binary sha256 に一本化 (fix-1)。変異 M2 は compile command 照合の WRITE_LATEST_ONLY 1 軸へ再照準。
- R-add2: fix-1 で build の -j を CPU 数 / 同時 build 数に、静定待ちを 180 秒・未静定は記録して続行に、perf event 名の修飾子を既存 parser で処理。
- R-add3: J0 walltime を 00:20:00 → 00:30:00 (較正最大 48 run・8M 点・within 50 run・build 2 本・依存準備を 20 分に収める根拠が無い)。予算判定は裁定どおり J0 の実 Elapse で置き換えるので線の式は不変。
- R-add4 (段 6 fix へ): `analysis.j2_best` は session < 3 のとき best まで判定不能にしているが、裁定は「集合だけ判定不能」。W5 は session が J0 + J2 の 2 本で常に該当する。best と score は出し、集合だけ判定不能にする。
