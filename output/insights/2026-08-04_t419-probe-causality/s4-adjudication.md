# 段 4 裁定 — [T-419] probe 実験

レンズ A (因果推論・測定機序) 13 件、レンズ B (運用・規律・成果物) 16 件。
**refuted は 0 件。全件 real。** ただし採否・射程は下記のとおり親が裁定する。

## 総括裁定

両レンズの総括「現状の brief のままでは因果を立証できない / 投入してはいけない」を **採用**する。
plan v2 を確定してから実装し、投入する。

## 採用 (実装する) — 実験設計

| # | 所見 | 裁定 | plan v2 での実装 |
|---|---|---|---|
| 1 | A-1 帯外集合に含むかは対照差でない (全 CPU 帯外でも偽 CONFIRMED) | **採用・最重要** | A1 の判定を **paired contrast** に置換。各 CPU *i* について「pin=*i* の読みで *i* が帯外」の率と「pin≠*i* の読みで *i* が帯外」の率を比較する。pin 順は seed 固定でランダム化 |
| 2 | A-2 APERF/MPERF の cache と warm-up で R=5 が疑似反復 | 採用 | affinity 変更後の **最初の読みを anchor として破棄**し、以降は固定間隔 (既定 50 ms) を置く |
| 3 | A-3 介入が複合 (pin + driver 前処理 + 測定 IPI) | 採用 (A-1 と統合) | pin≠*i* の読みが「reader は別 CPU、対象 *i* を観測」の対照そのもの。critical window では JSON 構築・log を行わない |
| 4 | A-4 / B-7 read 前後の processor では migration を立証不能 | 採用 (**格下げ**) | A4 は記述的 arm。P2 の migration 部分は **UNRESOLVED** のまま残し、因果判定に使わない |
| 5 | A-5 CPU ID の連続性を仮定している | 採用 | sweep 対象は `sorted(sched_getaffinity(0))`。`processor` ID → vector 位置の map を保存。要素数 48 を assert (不一致なら INVALID) |
| 6 | A-6 / B-8 「厳密 2101.0」は canonical 述語でない | **採用・重要** | 主判定は canonical comparator と同一 = 凍結較正の `median(expected samples) ± tolerance_pct%` (実測 pin: median 2101.0、tol 2.0、帯 [2058.98, 2143.02])。厳密一致率は **P5 用の副次診断**へ分離 |
| 7 | A-7 α の推定量が一意でない | 採用 | α = **本番相当 (unpin) で K 回連続の full-vector read、位置ごとの累積最小**。K=5、10 ブロック。k=1..5 の各段で収束率を出す。下側外れも別に数える |
| 8 | A-8 感度と特異度を分けていない | **採用・重要** | 同一 raw vector に α/β/γ を適用する **2×3 判定表**。should-pass = quiet/self-only、should-reject = 持続的な非 self busy (A2)。γ が should-reject を通せば **偽陰性 = 環境逸脱の見逃し** (規律 2 の観点で失格側) と記録 |
| 9 | A-9 busy helper の対照がない | 採用 | 同一 reader CPU・同一 *k* で **sleeping child (sham) と busy child** をランダム順で比較。帯外 indicator に加え MHz 差も採る |
| 10 | A-10 arm 間の持ち越し (P-state hysteresis・熱) | 採用 | 実行順を **quiet 群 (A0/A1/A4/A3 単独) → A2 群 (busy/sham) → A3+A2 併走** に固定。ブロック初回破棄、child は terminate → wait → 生存確認、1 秒 cooldown |
| 11 | A-11 login 実測の転移 | 採用 | login 実測は **仮説生成のみ**。CONFIRMED の分母・成功数に一切混ぜない (README に明記) |
| 12 | A-12 P5 は kernel fallback を無視 | 採用 | `uname -r/-v`、boot cmdline、policy の `affected_cpus`/`related_cpus`/min/max/`cpuinfo_cur_freq` 可読性を記録。P5 の結論は **「hybrid source と整合的」まで**に制限 |
| 13 | A-13 busy user process を IRQ/C-state/熱から分離できない | 採用 (**境界限定**) | arm の**前後だけ** per-CPU `/proc/stat`、interrupts、cpuidle usage/time、thermal throttle count を採る。診断読みは primary outcome の**後**。trial ごとには採らない (規律 4) |
| 14 | B-1 有効性と因果判定の混同 | **採用・重要** | `execution_validity ∈ {VALID, INVALID}` と `causal_verdict ∈ {CONFIRMED, REFUTED, NOT_EVALUATED}` を分離。全 arm の期待件数・例外・欠測・環境 gate が完全なときだけ verdict を生成 |
| 15 | B-2 PBS 実行包絡が成果物にない | 採用 | PBS script を成果物に含め、`python3.10` 明示、計算ノード marker、`PBS_JOBID`、rc、`.o/.e`、`qstat` 記録を証拠へ |
| 16 | B-3 単独性が記録項目どまり | **採用・重要** | 単独性は **admission gate**。自 process tree を allowlist し、arm 前後 + 各 arm 中 (in-process の `/proc/stat` 差分) で競合を監視。競合検出・可視性不足なら当該 arm を INVALID |
| 17 | B-4 補助観測が critical window を汚す / 本番と別 parser | 採用 | critical window では subprocess を起動しない。読みは本番同型 (`Path.read_text`)。生 text を数件保存し、**本番 `_parse_cpuinfo` と自前 parser の一致**を window 外で照合 |
| 18 | B-5 集約規則が未定義 | 採用 | 判定単位は個々の読み (240 件)。self の定義 = 読み直前に記録した `sched_getaffinity` の単一要素 (pin 時) / `/proc/self/stat` processor (unpin 時)。欠測は INVALID 側 |
| 19 | B-6 介入成立の証拠がない | 採用 | busy/sham child の PID・affinity・`/proc/<pid>/stat` の utime+stime 増分・liveness を記録し、増分が閾値未満なら当該対を INCONCLUSIVE |
| 20 | B-9 統計配分 | 採用 (**再配分、総量は据置**) | A1 = 48×5 = 240 (対照は 47×5 = 11,280 の非 pin 観測)、A3 = 10 ブロック × K=5 = 50、A2 = 8 CPU × (busy/sham) × 5 = 80、A0 = 30、A4 = 30。計 約 430 読み + arm 境界診断。数秒 |
| 21 | B-10 再現・反証に足りない | 採用 | schema version 付き JSON、no-clobber の `<jobid>` dir、manifest に全 file の sha256、commit/dirty・driver sha256・argv・seed・`sys.executable`・kernel・queue・開始終了時刻・rc |
| 22 | B-11 cpufreq が可読性だけ | 採用 | policy→CPU 対応、exact path/value/unit/errno を arm 前後に時刻付きで記録。「不在」「不可読」「値あり」を区別 |
| 23 | B-13 非 certification である印がない | 採用 (安価) | schema に `non_certifying: true`、`counterfactual_only: true` を持たせ、calibration/receipt と異なる形にする |
| 24 | B-15 生 argv は外部入力 | 採用 (規律 6) | 記録は pid/uid/comm/state/cpu/cgroup の allowlist のみ。**argv・env は保存しない**。process 情報は untrusted data と明記 |

## 採用 (実装する) — 成果物・終端

- **B-14 / B-1 の 3 終端を明記する。** `VALID+CONFIRMED` / `VALID+REFUTED` / `INVALID(または
  INCONCLUSIVE)` のいずれでも raw・README・hash 参照を残し、**F108 には実際の結論だけ**を追記する。
  「因果立証済み」を前提にした fragment 文言は撤回する。
- **B-12 の受理集合表を裁定パッケージの中核にする。** 要素数 (48/48・47/48) では書かない。
  各方式について「入力領域・量化条件・受理式・最小反例・実測 pass/fail・変更対象
  (method 文字列 / schema / predicate / 凍結 artifact / pin) ・撤回と再発行コスト」を表にする。
- **B-16 の外的妥当性を明記する。** 結論は今回の exact node / job / config に限定し、
  fleet 一般化は未立証と書く。追加 job は自動で増やさず次段の裁定へ返す。

## 不採用・scope 外

- なし (全所見を採用)。ただし**是正の実装は引き続き scope 外** — probe の変更、較正の再取得、
  凍結 bytes と pin の更新は U-2 の所有であり、本 wave は 1 bit も動かさない。
- レンズが提案した「scheduler trace による migration の厳密立証」(A-4) は権限と規模を増やすため
  **実装しない**。P2 の migration 部分は UNRESOLVED として裁定パッケージへ返す。

## 実装面の配置 (plan v2)

先例 `tools/pegasus/probes/t293_perf_site_probe.{pbs,py}` に揃える。

| path | 中身 |
|---|---|
| `tools/pegasus/probes/t419_probe_causality.py` | 実験 driver + 純粋な解析関数群 (verdict は解析関数が出す) |
| `tools/pegasus/probes/t419_probe_causality.pbs` | PBS wrapper (`python3.10` 明示、binding 検査、no-clobber) |
| `orchestrator/tests/test_t419_probe_causality.py` | 解析関数の合成 fixture テスト (変異の的) |
| `output/env/pegasus/t419-probe-causality/<jobid>/` | 計算ノードの生出力 (job が書く) |
| `output/insights/2026-08-04_t419-probe-causality/` | brief・レンズ逐語・README (因果判定 + 方式表) |

`DW-G01` の趣旨 (専用機構や LLM driver を先に作らない) は守る — 単一 file の使い捨て driver であり、
恒久機構ではない。100 行を超えるのは上記の妥当性要件のためであり、その旨を worklog に書く。

## 変異事前登録 (DW-M01)

的 = `tools/pegasus/probes/t419_probe_causality.py` の解析関数。
gate は `orchestrator/tests/test_t419_probe_causality.py` の合成 fixture。
**同じ入力を拒否する層は前後に無い** (解析関数が唯一の判定層であり、PBS wrapper は実行環境しか見ない)。
harness = `tools/mutation_harness.py` (`DW-M05`)。

| ID | 変異 | 期待 |
|---|---|---|
| M1 | paired contrast の比較を恒真化 (pin 有無で率が同じでも「効果あり」) | KILLED — no-effect 合成例が赤 |
| M2 | `execution_validity` の欠測・例外検査を無効化 | KILLED — 欠測入り合成例が VALID になり赤 |
| M3 | canonical 述語を「厳密 2101.0 一致」へ差し替え | KILLED — 帯内だが非 2101.0 の合成例が赤 |
| M4 | α の累積最小を累積最大へ差し替え | KILLED — α 収束合成例が赤 |
| M5 | 単独性 gate (競合検出 → INVALID) を無効化 | KILLED — 競合入り合成例が赤 |
| M6 (正例) | should-reject 判定を「常に reject」へ倒す | KILLED — should-pass 合成例が赤 (過剰拒否の検出力) |

各変異の期待赤 node は実装完了後、anchor 逐語とともに `mutation-spec.json` へ確定する (`DW-M07`)。

## gate の禁止 (署名) と通る正例

本 wave は gate を新設しない。解析関数の契約は次の署名で書く。

- `evaluate(observations, calibration, environment) -> Verdict` は
  `execution_validity == INVALID` のとき **`causal_verdict` を必ず `NOT_EVALUATED`** にする。
- **通る正例**: 全 arm が期待件数を満たし、競合なし、pin=*i* の帯外率が pin≠*i* を有意に上回る
  合成観測 → `VALID` + `CONFIRMED`。

## erratum-1 (2026-08-04 23:35、段 6 レビュー R1-8 を受けた親の訂正)

事前登録の読み数を **430 → 445** に訂正する。arm 一覧には A3+A2 (α under contention、
3 ブロック × K=5 = 15 読み) を最初から含めていたが、規模欄の合計 (約 430) がこの 15 読みを
計上していなかった。**arm を増やしたのではなく、合計の書き落としを直す訂正である。**

- 内訳: A0 30 + A1 240 + A4 30 + A3 quiet 50 + A2 80 + A3+A2 15 = **445**
- 実装は `EXPECTED_PRIMARY_READS` の合計が 445 であることを assert し、
  manifest へ `preregistered_primary_reads: 445` として書く。
- 445 を「最初から登録済み」と書いてはならない。この erratum が訂正の一次記録である。
