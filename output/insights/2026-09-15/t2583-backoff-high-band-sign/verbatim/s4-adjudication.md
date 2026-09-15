# 段 4 裁定 — [T-2583] 高域での勾配符号の振る舞い

親が段 2 プランと段 3 敵対 2 本を裁定し、プラン v2 と**事前登録**を確定する。
本節は **probe を 1 度も走らせる前に**書いた。以後、結果を見てから閾値・向き・語彙・帯域・
対照・推定量を変えない。

## 1. 所見の裁定

| # | 所見 (出所) | 判定 | 採否 | scope |
|---|---|---|---|---|
| A-1 | `FunctionType` でグローバルを差し替えた実行は「既存経路の実行」ではない (A, blocker) | **real** | **採用** | 内 |
| A-2 | 広窓側の既知最大値 12 µs から主帯域の不成立は既に含意され、盲検とは呼べない (A, major) | **real** | **採用** | 内 |
| A-3 | 「実行不可」が trace・設計・閾値の 3 原因を 1 語に畳む (A, major) | **real** | **採用** | 内 |
| A-4 | `2p(1-p)` は少数標本で下方偏り、標本数差だけで支持方向を作れる (A, major) | **real** | **採用** | 内 |
| A-5 | 測っているのは歩行中の差分勾配の符号混合であり「戻れない理由」ではない (A, major) | **real** | **採用** | 内 |
| B-1 | 不成立理由を独立に検算できる生の計数が JSON の確定 field に無い (B, major) | **real** | **採用** | 内 |
| B-2 | 100 行の成立根拠が無く、追加分析が予算を圧迫する (B, major) | **real** | **採用 (部分)** | 内 |
| B-3 | セル逐次処理は loader の全セル同時保持を解消しない (B, minor) | **real** | **採用 (記録のみ)** | 内 |
| B-4 | probe の退避だけでは実装面差分ゼロを保証しない (B, minor) | **real** | **採用** | 内 |
| B-5 | brief に `DW-O09` 閉包の結論が書かれていない / 「pin 皆無」は言い過ぎ | **real** | **採用** | 内 |
| B-6 | T-2188 の取りこぼし率 68.9% は算術誤り (正しくは 69.90%) | **real** | **採用 (追記のみ)** | 内 |
| C-1 | `spec_from_file_location` による import が壊れる | **refuted** | — | — |
| C-2 | 取りこぼしにより `_load_new_trace` が `_fail` で落ちる | **refuted** | — | — |
| C-3 | CLI 必須入力 (`--stock-readme` 等) が無いと loader を呼べない | **refuted** | — | — |
| C-4 | 140 MB なので login node では資源的に危険 | **refuted** | — | — |
| C-5 | `analyzer` / `preregistration` の SHA field 自体が「台帳追加」に当たる | **refuted** | — | — |
| C-6 | 刻み軸の記述が更新間隔軸の代用になる (プランの防壁が文面だけ) | **refuted** | — | — |

**C-1〜C-3 は親が現物で確認した。** 解析器 (`orchestrator/campaign/backoff_nonmonotonicity_analysis.py`)
の import は 8〜16 行目の標準ライブラリだけで相対 import が無く、module 直下は定数と関数定義、
CLI は末尾の `__main__` guard 内にある。`_load_new_trace` に `allow_overflow` 引数は無く、
`retained + dropped == updates` は 6 セルとも成立する。D1935 の対象は producer 側の
`_parse_backoff_trace` であって本 loader ではない。
**C-4 も親が確認した。** login node の空きメモリは 197 GiB、想定ピークは 1 GiB 未満である。

## 2. 親 brief の訂正 (段 3 の指摘を受けて)

1. **旧 J1 が `not_supported` だった理由を書き違えていた。** 旧 J1 は共通辺 12 本で
   登録閾値 10 を**満たしており**、不支持の理由は差 0.0402 < 0.10 と 3 区間の向き不一致である。
   低域限定はその判定の**射程**であって、不支持の原因ではない。
2. **「高域の勾配符号は 1 度も測られていない」は広すぎた。** 符号は trace に記録済みで、
   `_edge_observations` は帯域を絞らず抽出する。未充足なのは
   **高域に限定した集計と、高域での条件比較の報告**である。
3. **(P2) `min(edge) > 50` は「両端 > 50」と同一**であり、独立な感度ではない。感度は
   `max(edge) > 50` の 1 本だけとする。
4. **(P3) の「実行できる」の定義が結論を先取りしていた。** 以下の 3 つを分けて報告する —
   (i) 値が計算できるか、(ii) 共通台があるか、(iii) 登録閾値 10 を満たすか。
5. **`DW-O09` 閉包の結論を正確に言い直す。** 親が測ったのは
   「**解析器を現行 bytes に固定する live gate は repo 内に無い**」であり、「pin が皆無」ではない。
   trace 冒頭の `prereg_sha256` / `driver_sha256` / `pbs_sha256` / `patch_stack[*].sha256` は
   既存測定の出所束縛として実在する。本 wave はそれらを**編集しない**。

## 3. プラン v2 (確定仕様)

### 3.1 生死確認の主経路 — 既存 J1 を**そのまま**呼ぶ

A-1 を採用し、`FunctionType` によるグローバル差し替えは**行わない**。

1. `_load_new_trace(trace_path)` で `(resolved, runs)` を得る。
2. `_j4_effective_update_interval(runs)` の第 2 戻り値を `coverages` とする。
3. **無改変の `_j1_sign_instability(runs, coverages)` を呼ぶ。**
4. 返った `overall.edges` の各 `unordered_edge` を帯域で分類し、
   **主帯域 (両端 > 50 µs) に属する共通辺が何本あるか**を数える。
5. これが「既存 J1 経路が高域を出すか」の答えである。**差し替えも再接続もしない。**

### 3.2 高域の記述統計 — 既存**部品**による再解析

3.1 だけでは高域の符号の振る舞いは出ない。そこで既存部品
(`_edge_observations` / `_edge_counts` / `_fixed_edge_comparison`) を、**帯域で絞った観測へ適用する**。
これは「既存経路の実行」ではなく「**既存部品による再解析**」と呼ぶ。報告でも区別する。

- `_edge_observations(runs[cell]["events"])` を全 6 セルについて**帯域を絞らずに**呼ぶ
  (元列の隣接関係を壊さないため)。返った観測を辺の帯域で**後から**選別する。
- 主帯域・感度帯域それぞれについて `_edge_counts` を掛け、セルごとの辺別集計を得る。
- 主対照 (`nm-step1` × `nm-step1-u2560`) について `_fixed_edge_comparison` を高域観測へ掛け、
  共通辺数・重み総和・比較値を得る。共通辺ゼロなら比較値は `null`。

### 3.3 帯域の定義 (凍結)

辺は直前 event の順序なし対 `sort(backoff_before, backoff_after)` とし、現在 event の
`gradient_sign` を割り当てる。**event を先に間引かない。**

- **主帯域: 両端が厳密に `> 50 µs`。** `min(edge) > 50` と同一であり、別の感度とは数えない。
- **感度帯域: `max(edge) > 50 µs`。** 境界をまたぐ辺を含む。
- 境界横断辺 (`min <= 50 < max`) の本数を別に数える。`50` ちょうどは主帯域に含めない。
- 自己辺 `(b, b)` は既存処理が除外しないので維持し、本数を明示する。
- 50 µs は J2 事前登録の `P(Backoff_ > 50 µs)` と、上限 50 µs の自然実験との接続から取る。

### 3.4 測る量 (凍結)

推定量は既存の辺別 `d = 2p(1-p)`、`p = n+ / (n+ + n-)`、`gradient_sign == 0` は推定から除外し
**除外数は保存する**。共通辺上の重みは `min(n_L, n_R)` を両条件共通に使う。

**A-4 により、次を限界として必ず記録する。** `d` の期待値は独立 Bernoulli の下で
`2q(1-q)(1 - 1/n)` であり、**標本数 n が小さい側ほど系統的に 0 へ寄る**。
したがって標本数が大きく違う 2 条件の `d` の差は、符号生成確率が同じでも正になりうる。
`d` を報告する場所には必ず辺別 `n` を併記する。支持条件を満たしても、広窓の符号安定化や
計数ノイズの寄与の証拠へ昇格させない。

### 3.5 実行可能性の判定 (凍結) — A-3 により 3 つを分けて出す

| 実測状態 | 報告する語 | 帰属先 |
|---|---|---|
| 広窓側に主帯域の辺対が 0 | `no_high_band_observation` | **記録された trace** |
| 辺対はあるが非ゼロ符号が 0 | `no_nonzero_high_band_sign` | 記録された trace |
| 両側に非ゼロ観測があるが共通辺 `K = 0` | `no_common_high_band_edge` | **既存 J1 の共通辺設計** |
| `1 <= K < 10` | `insufficient_common_support` | **登録閾値 10** |
| `K >= 10` | `executable` | — |

**閾値 10 は変更しない。** `K < 10` は「高域の符号の記述統計が計算不能」を意味しない。
結論の文は「**当該 trace の固定 2 条件では、高域 J1 比較の共通台条件を満たさない**」とする。
入力不正・import 失敗・メモリ不足は `measurement_incomplete` とし、構造的な実行不可と区別する。

`K >= 10` の場合だけ、支持方向 `D_10 - D_2560 >= 0.10` かつ既存の保持 event 添字三等分すべてで
差 `> 0` を報告する。揃わなければ `direction_unstable`。空区間の差は `null` とし安定性に数えない。

### 3.6 既知情報の申告 (凍結) — A-2 により盲検を主張しない

**本 wave は盲検ではない。** 設計時点で次を知っていた。

- J2 の時間加重 `P(Backoff_ > 50)`: `nm-step1-u2560` = 0.0000、`nm-step0.5` = 0.0000、
  `nm-step1` = 0.8412、`nm-step2` = 0.9819、`nm-step25` = 0.9617、`nm-step100` = 0.9547。
- `backoff_before` の event 加重最大値: `nm-step1-u2560` = **12.0**、`nm-step0.5` = 22.0、
  `nm-step1` = 358.0、`nm-step2` = 444.0、`nm-step25` = 1000.0、`nm-step100` = 1000.0。
- 旧 J1 の共通辺は 12 本で、すべて `Backoff_` <= 12 µs だった。

**したがって主帯域の共通台不成立は、既存報告から予測済みである。** 本 wave が新たに与えるのは
(a) その予測の原 trace 上での確認、(b) **未報告だったセル別の高域符号集計**、
(c) 不成立の帰属先の切り分けである。事前登録が抑えるのは
**新しい集計を見た後に仕様を動かす余地**だけであって、独立な盲検判定への改善ではない。

### 3.7 対照 — 刻み軸を更新間隔軸の代用にしない (凍結)

刻み軸 5 セル (`nm-step0.5` / `nm-step1` / `nm-step2` / `nm-step25` / `nm-step100`) は
更新間隔 10 µs で固定されており、**更新間隔を変えた効果を言えない**。
B-2 を採用し、全 10 組の**比較値は出さない**。出すのは各組の**共通辺数だけ**とし、
「どの対照なら高域で共通台を作れるか」という構造の提示に限定する。

報告に次の文を固定する。

> 更新間隔 10 µs に固定した刻み条件間の記述である。更新間隔 10 対 2560 µs の高域対照を
> 補完するものではなく、広窓による符号安定化の証拠には用いない。

### 3.8 主張しないこと (凍結) — A-5

符号不一致率の高低から「計数ノイズが高域で符号を支配する / しない」へ**進まない**。
同じ辺でも歩行履歴と窓の状態で throughput 差は変わるため、計数ノイズが無くても符号は混ざる。
旧 insight の「少なくとも低域では主要因ではない」という読み方を、高域へ延長しない。
自己辺を含む値は保存符号の記述として扱う。

### 3.9 probe の仕様

- 置き場所: `output/insights/2026-09-15/t2583-backoff-high-band-sign/probe.py`。
  **最初から追跡しない** (`git add` しない)。段 6 後に repo 外へ退避する。
  B-4 により、「退避した」ことと「実装面差分ゼロ」は別の事実として報告する。
- 入力: `--trace <絶対 path>` 必須。ディレクトリ探索や他 trace の読込みをしない。
- 出力: `--output <絶対 path>` 必須。
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2583-backoff-high-band-sign/t2583-high-band-sign.json`
  の 1 本だけ。既存 file を上書きしない (create-only)。
- 解析器の import: `importlib.util.spec_from_file_location` で worktree 内の絶対 path を指定する。
  **解析器の bytes を 1 byte も変えない。** `python3 -B` で bytecode を残さない。
- 予算: 空行と comment を除いて **100 行以内**。収まらなければ 3.7 の共通辺数 → セル内低域対比の
  順に削り、**削った項目を JSON の `omitted` へ明記する**。生の計数は削らない。

### 3.10 JSON に必ず入れる生の計数 (B-1)

セルごとに、`_load_new_trace` が返した `events` から直接数えた次を保存する。
**派生値だけを残して生の計数を捨てない。**

- `event_count`、`nonzero_gradient_count`、`zero_gradient_count`
- `backoff_before_min/max`、`backoff_after_min/max` (**広窓側の高域不到達を J2 の丸め値でなく
  生値で示すため**)
- `high_band_pair_count` (主・感度それぞれ)、`high_band_positive/negative/zero`
- `high_band_unique_edge_count`、`self_edge_count`、`boundary_crossing_edge_count`
- 主帯域の辺別 `[edge, n_plus, n_minus, n_zero, p, d]` の全件
- 低域 (両端 <= 50) の同じ集計 (セル内対比・**記述のみ**)

主対照については `common_edge_count`、`fixed_weight_sum`、`feasibility` の語、比較値 (または `null`)。
既存 `_j1_sign_instability` の無改変の戻り値も `existing_j1_unmodified` として丸ごと保存する
(その `estimator_specified_after_data: true` は**書き換えない**)。

## 4. 変異事前登録 (`DW-M01`)

**本 wave の実装面 repo 差分はゼロである** (probe は非追跡で、段 6 後に repo 外へ退避する)。
`DW-S04` の「実装面 (D95 決定 2) の差分ゼロの wave だけ変異 matrix を免除する」に該当するため、
**変異 matrix は免除**とする。**受入全走は免除しない。**

## 5. 成果物

- `output/insights/2026-09-15/t2583-backoff-high-band-sign/README.md` と `verbatim/`。
- `docs/spool/` の worklog / decisions fragment。failures は B-6 の算術誤りを追記する場合のみ。
- 実装面 (コード・テスト・probe) の repo 差分はゼロ。

## 6. 規律の確認

- **絶対規律 2:** 本 wave は verifier・correctness gate・受理集合に触らない。段 3 の 2 本とも
  「緩める方向の変更は無い」と判定した。
- **絶対規律 7:** 2026-09-10 の J1 判定 `not_supported` を遡って昇格・撤回しない。
  本 wave は別に固定した高域再解析の**追記**である。B-6 の算術誤りも追記で訂正し、
  原記録の bytes を書き換えない。
- **非認証:** `headline_eligible = false`、`throughput_scope = diagnostic_only`。
  射程は write-heavy / 48 スレッド / records 1,000,000 / extime 3 秒 / 1 rep / Pegasus。
