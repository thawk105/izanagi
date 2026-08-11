# [T-810] 段 4 裁定 — real/refuted、採否、scope、プラン v2

段 3 の 2 レンズはいずれも NO-GO (レンズ A: blocker 6 + nit 1、レンズ B: blocker 8 + must-fix 2 + nit 1)。
親は各所見を裁定し、**親自身が実物で再計算・再確認した結果**を根拠に採否を決めた。
子の所見をそのまま採らない (F1 同型の再発防止)。

---

## 1. 親が独立に確認した事実 (子の主張の裏取り)

| # | 子の主張 | 親の検証 | 判定 |
|---|---|---|---|
| V1 | `--certify` は registered へ自動 publish する | `orchestrator/calibrator/cli.py` の certify 経路が staging→`registered/calibration-<digest16>.json` を `_rename_noreplace` で publish するのを直接読んだ | **real** (親の F-3 の記述が誤っていた。訂正済み) |
| V2 | 既定 durable root は repo `output/` だけ | `orchestrator/campaign/layout.py` の `default_durable_root_policy` が `approved_roots=(repo output,)`、`authorize_output_root` が非該当を拒否 | **real**。ただし policy は引数で注入可能で、docstring 自身が「機械固有 path は注入側だけが持つ」と書いている → 壁ではなく**明示行為の要求** |
| V3 | calibration ディレクトリを wildcard 走査する consumer が居る | `orchestrator/campaign/screening_driver.py` の `load_between_run_floor` が `between_run_noise_*.json` を glob | **real** (既定 dir は linux-baremetal だが、族としての危険は実在) |
| V4 | 依存が `/scr` に残ると binary 配布が成立しない | `certify_calibration.sh` は gflags/glog を `-DBUILD_SHARED_LIBS=OFF` で static build する (F-8) | **partially refuted** — gflags/glog は静的。残るのは libstdc++ 等の system runtime だけで、`ldd` 記録で閉じられる |
| V5 | 実 record に drift がある | 親が自前で相関を計算: bnode048 は r=−0.659 (t=−2.48, df=8, 両側 5% 有意)、bnode011 は r=−0.299 で非有意。lag-1 系列相関は両者ほぼ 0 (F-9) | **real、ただし機序は自己相関でなく傾き** |
| V6 | `N=12,R=10` は最小でない | 親が F 分位を自前実装して再計算。`N=9,R=13` が同条件を満たし 117<120 (F-10)。さらに**推定量を τ へ直すと `N=12,R=10` は assurance 0.7926 で目標 0.80 に届かない** | **real、かつ子より強い結論** |
| V7 | `noise.repetitions` は実在しない | 実 record の key は `noise_floor.throughputs` (長さ 10) | **real (nit)** |

---

## 2. 所見の裁定

### 採用 (real、scope 内、プラン v2 へ反映)

| ID | 出典 | 裁定 |
|---|---|---|
| **R1** | A-3 | **主推定量を `κ=σ_a/σ_e` から `τ=σ_a/μ` (ノード CV) へ変更する。** κ は測定系の診断的副次量へ降格。理由: κ は「検出しやすさ」であって運用上のノード差ではなく、**測定が騒がしいほど「差は小さい」と結論する逆向きの判定**になる。V5 の drift 実測がこれを補強する — drift が σ_e を膨らませると κ が縮む |
| **R2** | A-1 + F-9 | **materiality は運用尺度で先に決める。**1.774% は記述統計に封じ、閾値の逆算根拠にしない。親の既定は **τ\* = 0.6% = 実測 within-run CV (1.25%) の半分**。理由 = 「1 回の走行内で既に許容している揺らぎの半分より小さいノード差は、どの判断も変えない」。Q1 として裁定へ回す |
| **R3** | A-5 + F-10 + V6 | **N・R は目的関数を先に固定してから導く。**親の目的関数 = 「assurance ≥ 0.80 を、**1 ノード脱落後も**保つ最小設計」。理由 = protocol は開始後の差し替えを禁じるので、脱落は現実の主要リスクである。τ\*=0.6% での解は **N=12, R=12** (full 0.8769、1 脱落後 0.8385)。N=12,R=11 は脱落後 0.7970 で割れる。N=6/9/13 系はいずれも脱落 1 で割れる |
| **R4** | A-4 + F-9 | **仮定破れへの備えを主設計に入れる。**反復ごとの時刻・実効 clock を記録し、drift 診断 (index との相関と傾き) を必ず報告する。主推定は τ の F/χ² 反転による上側限界、**副次に頑健要約** (node 平均の median/IQR/range、log scale、事前固定 cluster bootstrap) を必ず併記する。事後に scale や手法を選ばない |
| **R5** | A-2 | **T-139 への用途を「共通乗数モデル下の感度上限」に限定する。**pilot の標本共分散・臨界値・受理確率・`J` のいずれも変えない。加法/乗法の loading は単一 arm では識別できないと明記する |
| **R6** | A-6 + B-3/6/10 | **事後の自由度を閉じる。**exact な boolean validity 述語、状態機械 (`premeasurement_invalid` / `incomplete_after_start` / `valid`)、開始境界、release 後の差し替え禁止、release 前の最大 attempt 数、最初の適格 attempt 採用、全 attempt の報告を literal に固定する |
| **R7** | B-1 | **env 契約 hash を pin し、legacy build 経路を fail-closed で拒否する。** |
| **R8** | B-2 + F-8 | **binary の同一性は bytes だけで主張しない。**`ldd`/`readelf` の依存名・解決 path・hash、module list、`LD_LIBRARY_PATH`、`/scr` 参照検査を builder と全ノードで記録し、release token に束縛する |
| **R9** | B-5 + V1 | **`calibrator --certify` の使用を機械的に禁じる。**calibration writer capability を持たない専用 runner だけを許す。「使わない」という約束に依存しない |
| **R10** | B-6 + B-7 + V2/V3 | **保存先は repo 外の専用 root。**`DurableRootPolicy` を T-810 専用に**注入**し、repo 全体を forbidden root にする。期待ファイル集合の exact 列挙は補助監査であって主防壁ではない (主防壁は書けないこと) |
| **R11** | B-4 | **静穏 preflight は既存 `run_probe.py` では代替できない。**専用 wrapper に load 閾値・local pgrep・host receipt・canary を束ねる |
| **R12** | B-8 | **B 系並走ガードは「設計のみだから自明」で終わらせない。**本 wave については計算ノード未使用で (i)(ii) は充足だが、**文書は将来の実施時の機械化手順** (`qstat -u` の exact parser、unknown-state 拒否、A 優先 receipt、競合時の T-810 取り下げ) を必須要件として持つ |
| **R13** | B-9 | **予算 admission 規則を持つ。**builder + N job + liveness + retry 上限の総量が残枠内のときだけ投入する |
| **R14** | A-7 | 現 record は `len(noise_floor.throughputs)==10` と正確に書く。新 schema では `planned_repetitions` と実測配列長の一致を検査する |
| **R15** | B-11 | 新文書は docs 間を行番号で参照しない (節名・schema ID・commit hash で参照)。`docs/README.md` の地図へ 1 行足す |
| **R16** | 段 2 §8 | **生死確認 (DW-G01) を N=2, R=2 で先に行う。**推定にも N の再設計にも使わないことを事前に宣言する |

### 一部 refuted

| ID | 所見 | 親の裁定 |
|---|---|---|
| **X1** | A-2 の「単一 arm の出力は T-139 pilot を**支えない**」 | **強すぎるので一部 refute。**共通乗数モデル `m_A,wj = q_j·m°_A,wj` の下では、cluster 間分散のうちノード起因の成分は `τ²·E[N]²` 程度と書ける。`τ` と pilot 自身の `E[N]` から**ノード起因で説明しうる分散の上限**が計算でき、これは「同時信頼領域の幅の解釈」への実質的な入力である。**識別できないのは loading の形 (加法か乗法か) であって、上限の計算ではない。**したがって目的の削除 (A-2 の選択肢 A) は採らず、R5 の scope 限定を採る |
| **X2** | A-1 の「`CV/√10` は独立性未確認なので SE でない」 | **機序を訂正して一部採用。**親の実測では lag-1 系列相関は両 record ともほぼ 0 (−0.11 / −0.01) なので、自己相関による SE 過小評価は支持されない。実在するのは**傾き (drift)** であり、これは SE ではなく σ_e 自体を膨らませる。結論 (1.774% を閾値の逆算に使わない) は採用、理由は差し替える |

### scope 外 (実装しない。文書は「実施前に閉じるべき gate」として要求だけ書く)

B-3 (group barrier / revocation)、B-4 の wrapper 実装、B-5 の argv validator、B-6 の capability 実装、
B-8 の qstat parser、B-9 の予算換算器。**いずれも実装面であり、本 wave は設計のみである** (ユーザー指示
「実走はせず設計のみ」)。文書はこれらを**実施の前提条件**として列挙し、
「本文書だけでは走行を許可しない」と明記する。実装は別 wave で Codex `role=author` が書く。

---

## 3. プラン v2 (確定した事前固定値)

| 項目 | 確定値 | 根拠 |
|---|---|---|
| 目的 | 同一 binary・同一 workload の throughput のノード間相対ばらつきを、上限つきで推定する。用途は (a) job 間性能比較の可否判断、(b) T-139 同時信頼領域の幅に対するノード起因上限の感度表の 2 つに限定 | R5, X1 |
| 主推定量 | `τ = σ_a/μ` (ノード CV) とその片側 95% 上側限界 | R1 |
| 副次量 | `κ=σ_a/σ_e`、ICC、node 平均の min/max/range、median/IQR、drift 診断、`MS_A`/`MS_E`/`F` | R1, R4 |
| materiality | `τ* = 0.6%` (実測 within-run CV の半分) | R2 / Q1 |
| N, R | **N = 12, R = 12** | R3 |
| 割付け | scheduler 割当て (無作為抽出ではない)。同一 occasion に N 本を同時確保し、ready barrier 後に共有 release。ノードは選ばない | R3, R6 |
| binary | 専用 builder job で 1 回だけ build → repo 外 read-only store → 各ノードへ byte copy → 前後 SHA-256 + runtime manifest 照合 | R7, R8, F-2, F-8 |
| 保存先 | repo 外専用 root (`DurableRootPolicy` を注入、repo 全体を forbidden) | R10 |
| 非流入 | calibration writer capability なし + repo 全体 deny + 期待集合 exact + 前後 inventory 監査 | R9, R10 |
| 生死確認 | N=2, R=2、推定へ非統合を事前宣言 | R16 |
| 効力 | 段 4 の全裁定 + 実装完了 + liveness 成功のすべてが揃うまで走行を許可しない | scope 外項目 |

---

## 4. 変異事前登録 (DW-M01)

**変異 matrix は免除する。**理由 = 本 wave の実装差分はゼロ (docs のみ) であり、
kill を観測できる受理集合も fail-closed 挙動も 1 つも新設しない。機械 gate を 1 つも作らないため、
変異を注入する面が存在しない。先例は worklog (418) の docs-only wave (同じ理由で免除)。

**受入全走は免除しない。** `docs/pegasus-runbook.md` を実 repo から読むテストが実在するため
(段 7 で nodeid を実測して記録する)。

---

## 5. ユーザー裁定へ回す設計択一 (裁定パッケージ)

親は既定値を決めて文書へ書く。下は**覆しうる価値判断**であり、覆す場合は文書の該当 field だけを差し替える。

- **Q1 materiality `τ*`:** (a) 0.6% = within-run CV の半分 【親推奨】 / (b) 0.3% 厳格 (N≈21, R≈24 に膨らむ) / (c) 1.2% = within-run CV と同等 (N≈4〜5 で済む)
- **Q2 目的の範囲:** (a) 単一 arm のまま、T-139 へは共通乗数モデル下の感度上限としてのみ入れる 【親推奨】 / (b) T-139 目的を落として単独 snapshot に限定 / (c) 2 構成の交差設計へ拡張して加法/乗法を識別する (費用増、pilot と重複)
- **Q3 N・R の目的関数:** (a) 1 ノード脱落後も assurance を保つ最小設計 = N12/R12 【親推奨】 / (b) 総ノード秒最小 = N6/R24 (脱落 1 で割れる) / (c) 総測定回数最小 = N9/R14 (脱落 1 で割れる)
- **Q4 occasion:** (a) 1 occasion のみ。node と node×occasion の合成であると明記 【親推奨】 / (b) 2 occasion 目を追加 (同一 host 再確保は保証できない) / (c) 同一 host を指定して複数 occasion (scheduler が許すか未確認)
- **Q5 runbook §7.5 の stale 記述:** (a) 本 wave で訂正する 【親推奨、実施済み前提で受入全走を走らせる】 / (b) 別 wave へ送る
