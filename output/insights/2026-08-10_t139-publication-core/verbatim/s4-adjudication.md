# 段 4 裁定 — [T-139] 公表手続きの新 core 起草 (2026-08-10)

段 2 プラン 1 本と段 3 敵対 2 レンズ (A = 統計的正当性 / sol、B = 凍結境界・抜け穴 / luna) の
所見を real / refuted、採用 / 不採用、scope 内 / 外に裁定する。両レンズとも NO-GO を返した。

## 0. 親が独立に実測した事実 (子の主張を額面で採らない)

repo 外 probe `verify_counterexample.py` / `verify_power.py` で親が自分で計算した。

| 事実 | 実測値 | 子の主張 | 判定 |
|---|---|---|---|
| `t_{12, 1−0.025/6}` | `3.152681312170` | 同じ | 一致 |
| `p_2 = 0.0045` からの `T_2` | `3.111245194702` | 同じ | 一致 |
| `L_2^Bonf` | `−0.011492311245` | 同じ | 一致 |
| Holm 棄却 かつ 下限が 0 を含む | 成立 | 成立 | 一致 |
| `q_primary(13, 0.025)` | `3.449997` | `3.449997402` | 一致 |
| `d=1.0` の成分 primary 検出力 (`J=13`) | `0.57628` | `0.57628` | 一致 |
| `L_J` (`J=4..13`, `d=1.0`) | **全て 0.000** | `L₁₃ = 0` | 一致 |
| `J=13` で `L_J ≥ 0.80` に要る `d` | `1.5623` | 約 `1.562` | 一致 |

**親が新たに得た事実 (どちらのレンズも明示していない形):**
`q_primary > c_B` が候補 `J = 4..13` の**全てで**成立する (実測表を参照)。
`T_k > q_primary` (primary pass) は `T_k > c_B` を含意し、これは
`L_k^Bonf = (s_k/√J)(T_k − c_B) > 0` と `p_k < α_pub/6` を同時に含意する。
したがって **primary が pass する枝では、6 成分すべての Bonferroni 下限が正で、
Holm は第 1 段で 6 件すべてを棄却する。非整合は primary が pass しない枝でしか起こらない。**
この事実を新 core 本文へ書く (下記 D-4)。

## 1. レンズ A の所見

| # | 所見 | 判定 | 処置 |
|---|---|---|---|
| A1.1 | 成分間の線形従属が周辺 t を壊す | **refuted** | 不採用。周辺が非退化正規なら成分間依存は周辺 t を壊さない |
| A1.2 | 正定値 guard は文面だけ / 公表側 `6×6` を正定値必須にすると `J≤6` で必ず失敗 | **real** | **採用 (scope 内)**。新 core は `6×6` の正定値を要求せず、計算不能の枝は source の `S_w` gate から継承すると書く。機械執行が無いことは明記する |
| A1.3 | 片側性の向き | **refuted** | 不採用。3 成分とも `H_0: μ_k ≤ 0` で向きは正しい |
| A2 | Holm 調整済み p 値の式と tie-break | **refuted** | 不採用。式は正しく、tie-break は棄却集合を変えない |
| A3.1 | 数値例の算術 | **refuted** | 不採用。親も再現した |
| A3.2 | 反例が 3-arm 標本として実現不能 | **refuted** | 不採用。`Q = diag(25/41, 25/41, 16/41)` で `s_GG = s_DD + s_NN − 2s_ND` を満たす構成が示された |
| A4 | `C_w(q)` 不採用の理由づけが弱い | **real (nit)** | **採用 (文面)**。不採用理由を「Holm 非互換」ではなく「同時正規性の追加要求」と「`α_pub/2` 配分による保守化」に書き換える |
| A5.1 | 360 セル設計が Holm の FWER を押さえるか | **refuted** | 不採用。真の帰無数 `r` に対する `α_pub/r` の marginal bound で依存によらず上界が出る |
| A5.2 | 非正定値・`s_k=0` の synthetic dataset の数え方が未定義 | **real — blocker** | **採用 (scope 内)**。数え方を一意に定める (下記 D-6) |
| A5.3 | 計算量 (6,000 万 dataset) | **real (非 blocker)** | **採用 (文面)**。dataset 数を明記し、実行時間の裏付けが無いことも書く |
| A5.4 | seed が旧 core digest を含むこと | **refuted (A) / real (B BL-7)** | **B を採る** (下記 D-7) |
| A6 | permutation / randomization を退けた 3 理由 (weak null に exact でない / `J≤13` で漸近保証に頼れない / 固定 seed の block 順は割当て分布を作らない)、および sign-flip の対称性仮定 | **いずれも refuted** (限界そのものは real) | **採用 (文面)**。`t` は marginal 正規 model に条件付きと明記し、「分布自由」「permutation より頑健」を否定する。**この行は初版の裁定表から脱落しており、段 6 レビュー C の指摘で追記した** |
| A7.1 | 公表表が全部非有意になりやすい | **refuted** | 不採用。成分検出力の下限は約 67% |
| A7.2 | `d=1.0` で 6 成分同時 80% は不可能、`L_J = 0` | **real — blocker** | **scope 外**。凍結済みの core と追補 A の問題であり本 wave は直せない → 裁定パッケージ C-1 |

## 2. レンズ B の所見

| # | 所見 | 判定 | 処置 |
|---|---|---|---|
| BL-1 | 時点独立性が文書宣言だけ | **real** | **scope 外 (機械執行)**。新 core の「主張しないこと」へ明記し、配線は裁定パッケージ C-5 |
| BL-2 | 公表 dataset の identity が未固定で、結果を見て `J` 個を選べる | **real — blocker** | **採用 (scope 内)**。dataset を「source validator が確定した適格 cluster の**全件**」に一意固定し、部分集合を禁じる (下記 D-5) |
| BL-3 | 条件 5 が結果後の第 2 公表 core を公式に開く | **real — blocker** | **採用 (scope 内)**。条件 5 を**削除**し、同一 source dataset に対する第 2 の公表 core を禁じる (下記 D-8) |
| BL-4 | 現 B を新 core へ差し替える経路 / 二重束縛 | **real** | **一部 scope 内**。新 core は現 B を参照も継承もしないと書く。現 B の発効可否と `main_admission` は**ユーザー裁定** → C-2 |
| BL-5 | `ledger_kind` の自己申告リセット経路 | **real** | **採用 (scope 内、部分)**。`ledger_kind` を新 core が定める閉じた 2 値 enum とし、呼び手が名乗り分けられないと書く。台帳実体は C-5 |
| BL-6 | roadmap 限定例外との関係 | **real** | **scope 外**。roadmap 改訂は本 wave が行わない → 裁定パッケージ C-3 |
| BL-7 | seed が raw core digest を指し、erratum 適用後の effective core と食い違う | **real** | **採用 (scope 内)**。seed preimage から source core digest を**外す** (下記 D-7) |
| BL-8 | `p` 用 exact-key envelope が存在しない | **real** | **scope 外 (実装面ゼロ)**。新 core は機械執行を主張しない。実装は C-5 |
| BL-9 | producer → validator → consumer → 台帳の全層が未接続 | **real** | **scope 外**。層の表を「主張しないこと」へ写し、実装は C-5 |

**レンズ間の食い違い 1 件 (A5.4 vs BL-7) を親が裁定した。** A は「raw blob identity は不変だから stale に
ならない」と言い、B は「effective core は erratum 適用後の `d1782b04…` であり、同じ seed が
別の有効規則へ再利用される」と言う。**B を採る。**A の論点 (blob は不変) は正しいが、
seed が特定の core digest を含むこと自体が「この乱数列はその core に束縛されている」という
読みを生む。乱数 stream の domain separator に provenance の意味を持たせない方が安全である。

## 3. 親の provisional 裁定 (P1〜P7) の帰結

| # | 親案 | 帰結 |
|---|---|---|
| P1 | 同一測定を入力とする公表専用 study | **維持**。ただし dataset の全件性を明文化する (D-5) |
| P2 | `T_k` の片側 t | **維持**。両レンズとも倒せなかった |
| P3 | Holm | **結論は維持、理由を訂正**。「closed testing より劣らない」は**誤り**。正しい理由は「任意の依存に耐え、必要なのは marginal p 値の妥当性だけ」である |
| P4 | Bonferroni 同時下限 + 非整合の明記 | **維持し、強化**。非整合は primary が pass しない枝でしか起こらないことを実測して本文へ書く (D-4) |
| P5 | `α_pub` を値として引き継ぐ | **維持** |
| P6 | 非正規性は解消せず stress check + 限界明記 | **維持**。permutation を退けた 3 理由はいずれも refuted されなかった |
| P7 | field id は `p01`… | **維持**。ただし機械執行が無いことを明記する (BL-8) |

## 4. 採用する設計判断 (plan v2)

- **D-1.** 新 core は公表専用 study の core とし、現 core の測定 protocol・primary 判定・状態表・
  失敗分類を**参照だけ**して所有しない。現 core の文章を複製しない。
- **D-2.** 未調整 p 値 = `p_k = 1 − F_{t,J−1}(T_k)`、`T_k = √J·μ̂_k/s_k`。統計量は追補 A `a10` と同一。
- **D-3.** 多重調整 = Holm。理由は「任意の依存に耐える」。BH / FDR / 相関推定型 maxT へ実行時に
  切り替えることを禁じる。
- **D-4.** 同時区間 = `α_pub` を 6 成分へ Bonferroni 配分した片側同時下限。Holm の棄却集合とは
  一致しないことを明記し、**非整合が起こりうるのは primary が pass しない枝だけである**ことを
  親の実測 (`q_primary > c_B` for `J=4..13`) とともに書く。
- **D-5.** 公表 dataset = source validator が確定した適格 cluster の**全件**。部分集合・並べ替え・
  除外を禁じ、`J` は source から受け取るだけとする。
- **D-6.** stress check の縮退枝: synthetic dataset で対象成分の `s_k = 0` または `6×6` 標本共分散が
  特異になった場合、その dataset は **`u_r` を下回った件数へ数えない (非棄却として数える)** と定める。
  除外・再抽出はしない (除外は分母を変え、再抽出は分布を変える)。この規則を逐語で書く。
- **D-7.** stress check の seed preimage から source core digest を外し、公表 study 固有の literal
  だけにする。自己 digest も書かない。
- **D-8.** 同一 source dataset に対する第 2 の公表 core を禁じる。公表系列の ordinal は
  **新しい候補 (新しいデータ)** のためのものであり、同じデータの再解析に消費できない。
- **D-9.** `ledger_kind` は新 core が定める閉じた 2 値 enum (`primary_series` / `individual_publication`)
  とし、呼び手が新しい値を名乗れないと書く。
- **D-10.** 新 core は機械執行を一切主張しない。producer / validator / consumer / 台帳の未接続を
  「主張しないこと」の節に層ごとの表で書く。

## 5. 変異事前登録 (`DW-M01`)

**本 wave の実装差分はゼロである** — コード・テスト・script・機械設定を 1 つも追加・変更しない。
差分は `output/insights/` の文書と `docs/spool/` の fragment だけである。
変異させる gate も受理集合も存在しないため、`DW-S04` の免除規定
(「実装差分ゼロの裁定の変異 matrix だけ」) に該当し、**変異 matrix は登録しない。**
受入は免除せず、段 7 の記録前に判定する。

## 6. ユーザー裁定へ返すもの (scope 外の real 所見)

| # | 論点 | 由来 |
|---|---|---|
| C-1 | `d = 1.0` では `L_J = 0` で候補 `J` が 1 つも適格にならない (凍結済み core と追補 A の問題) | A7.2、親が実測で確認 |
| C-2 | 現 B の発効と `main_admission` — 新 core だけでは本走は解禁されない | BL-4、段 2 プラン §8 |
| C-3 | roadmap 限定例外が新 study の下流解析を許すか | BL-6 |
| C-4 | 新 core の承認そのもの (段階 1 → 段階 2) | B4 (a) の帰結 |
| C-5 | 機械執行 (p envelope、公表台帳、validator、consumer) の実装 wave | BL-1 / BL-8 / BL-9 |
