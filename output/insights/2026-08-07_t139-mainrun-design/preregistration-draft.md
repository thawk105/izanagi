# [T-139] 本走 — 事前登録の草案 (2026-08-07)

```text
authority: none
default_effect: no-state-change
```

**本書は草案であり、事前登録ではない。** 11 件のユーザー裁定 (`package.md` §1) が未確定であり、
確定していない箇所は `【U#】` で明示する。**この状態のまま実走へ束縛してはならない。**
正式な事前登録は、裁定確定後に実装 wave が実走前に commit する (Q10 = D116 方式の RF 拡張)。

## 1. 問い

代替 X (modeX) は、意図的に取り除いた最適化による劣化を、部分的に回復するか。
**部分回復とは、劣化版より速く、かつ元の版に達していないことをいう。**
元の版を超えた場合は「回復」と呼ばず「stock 超過」とだけ述べ、機序の帰属には別証拠を要求する。

## 2. arm と workload

| arm | 内容 |
|---|---|
| `stock` (S) | 元の版 |
| `mode1` (Dg) | 意図的に最適化を 1 つ外した劣化版 |
| `modeX` (X) | 合成システムが作った回復候補 (4 stripe、`alignas(64)` 分離、固定回数 mixer) |

workload は W1 (高競合 write) と W2 (中競合 mixed) の 2 本。
候補の exact bytes は request `892042` の `run_commit = 425ed190` に束縛する。

## 3. 量の定義 (cluster = 1 allocation、`j` を cluster 添字とする)

`m_{A,wj}` を workload `w`・arm `A`・cluster `j` の代表値とする。
**代表値は算術平均とする 【U7】。**

```text
N_wj = m_X,wj  − m_Dg,wj      回復量
D_wj = m_S,wj  − m_Dg,wj      劣化幅
G_wj = m_S,wj  − m_X,wj       元の版までの残り
```

恒等式 `D = N + G` が成り立つ。primary endpoint は trace-disabled の `throughput_tps` 1 本
(Q2 裁定済み)。abort 率等は説明用の副次指標であり、受理条件の family へ入れない。

回復率は `RF_w = E[N_w] / E[D_w]` (Q1 = 総回復率、裁定済み)。

分母条件の contrast `H_w` は **【U1】** で確定する。
- (a) 総量の比を採るなら `H_w = D_w − κ_w · S_w` とし、`E[H_w] > 0` を検定する。
- (b) 比の平均を採るなら `H_w = D_w/S_w − κ_w` とし、`E[H_w] > 0` を検定する。

`κ_W1` / `κ_W2` の数値は **【U2】**。候補の結果と独立に定める。

## 4. 受理条件 (primary)

workload ごとに、cluster level の標本平均・標本共分散から構成した**同時信頼領域** `C_w` について

```text
P_w  :=  inf_{C_w} N_w > 0
     AND inf_{C_w} H_w > 0
     AND inf_{C_w} G_w > 0
```

とし、primary は両 workload の連言 `P_W1 AND P_W2` **1 本**とする (Q7 の `all_pass` 型。
intersection-union なので多重補正は不要)。

**区間推定は同じ同時領域の ratio projection として導出する。**
別構成の Fieller を二重に課さない — 同じ標本共分散と同じ臨界値 `q` から作れば、
Fieller 集合の `r=0` 検査は `N` の検査、`r=1` 検査は `−G` の検査であり、
「有界な集合が `(0,1)` に含まれる」ことと `N>0 ∧ G>0` は**同値**である。
別構成にすると、正当な手続き差を「データ破損」として拒否する偽陰性経路になる。

Fieller 係数は
`A = D̄² − q²s_DD/J`、`B = N̄D̄ − q²s_ND/J`、`C = N̄² − q²s_NN/J` に対し `Ar² − 2Br + C ≤ 0`。

## 5. 状態の閉表 (2 軸。exact-one)

**軸 1 — 区間の形 `interval_shape`:**

| 値 | 条件 |
|---|---|
| `bounded` | `A > 0` |
| `unbounded_connected` | `A ≤ 0` かつ解が連結 |
| `disjoint` | `A < 0` かつ解が非連結 |
| `empty` | 解なし (例: `D_j ≡ 0`, `N_j ≡ 1` のとき `A=B=0, C=1`) |

**軸 2 — 適格性の状態 `qualification_status`:**

| 値 | 条件 | 正例 |
|---|---|---|
| `partial_recovery` | `bounded` かつ集合全体が `(0,1)` の内側、かつ `P_w` 成立 | **true 候補** |
| `below_degraded` | `bounded` かつ全体が 0 未満 | false |
| `stock_exceeding_unattributed` | `bounded` かつ全体が 1 超 | false |
| `boundary_ambiguous` | `bounded` かつ 0 または 1 を含む / 等しい | false |
| `weak_denominator_not_certifiable` | 分母の信頼集合が 0 を除外できない | false |
| `not_certifiable` | 上記以外の `unbounded_connected` / `disjoint` / `empty` | false |

`empty` は有効な raw からも生じるので、表現不整合 (`invalid_representation`) と分離する。
`RF > 1` は「回復」とも「新規改善」とも帰属させず、stock 超過とだけ述べる (D162 決定 6)。

## 6. 標本数の決め方 (二段階。Q5 裁定済み)

**pilot (external、非 pool)。** `J_p = 8` + 予備 2 **【U5】**。
pilot の raw は本走の推定・p 値・区間へ**一切合算しない**。
pilot が推定するもの: 割当て間共分散、cluster 内残差と位置・直前 arm の効果、
待機後の環境復帰、割当て実時間と infra failure 率、**ポイント単価**。

**planning alternative は `d = 1.0` に固定する 【U4】。** pilot の下側効果が 1 を下回っても
`d` を引き下げない (引き下げは結果依存の費用裁定変更にあたる)。下回る場合は
`design_not_feasible` を終端状態として本走を投入しない。

**本走の J。** 目標は **「6 成分の同時受理確率 ≥ 80%」【U4】**。
`J` は pilot 母数の**共同信頼集合上の最悪検出力**で評価し、
候補 `J` 全体に同時保証を掛けた上で最小の適格値を選ぶ。
**単一の scalar `d` から一意に決めない** — 6 成分の相関と区間形状で受理確率が変わるため。
正規近似の目安は成分ごと 80% で `J≈11`、全体 80% で `J≈13`。**これは sanity 値であって本走値ではない。**

`J_max`、pilot 本数、再設計の禁止は **pilot 前に固定する**。
`design_not_feasible` は当該候補・親系列の**終端状態**とし、
再開は全試行を保持した新 study・新しい有意水準割当てに限る。

**本走開始後の追加は一切行わない** (D126 決定 4)。

## 7. 実行順序と待機 【U6】【U11】

**cluster 内は 6 反復、3 arm の全 6 順列を各 1 回**とする (位置・直前 arm がともに exact 2 回)。
block の実行順は事前 seed で許容集合から選び、runtime 乱数を使わない。
W1 / W2 の block 順は cluster 間で差 1 以内に均衡させる。

**帰無仮説は weak mean null を primary とし** (estimand が平均 contrast のため)、
sharp null は副次感度分析とする。weak null の型 I 誤りは、同じ許容 schedule 集合を使う
事前 simulation で較正する (Q6 裁定済み)。

待機の原案は arm 間 30 秒・block 間および workload 切替時 60 秒 **【U11】**。
待機後に事前登録した環境指標が pre-run の範囲へ戻ることを要求する。
**現データはこの十分性を実証していない。**

**時間予算は未解決である 【U11】。** 現 probe は walltime 3600 秒 / 内部期限 3300 秒に対し
最悪 3298 秒で余白 2 秒。6 反復と待機を足すと収まらない。
**実行可能な予算表が確定するまで pilot を投入しない。**

## 8. 欠測と失敗 (Q8 裁定済み)

- **correctness anomaly は候補の終端 reject。** 削除も置換もしない (規律 2 の直接適用)。
- 性能測定の**開始前**の infra failure だけ、結果を見る前に外部証拠で確定した上で
  事前順序固定の予備から置換可。
- 性能測定の**開始後**の失敗は reject または判定不能。予備で置き換えない。
- 救済する場合は worst-case bound と感度分析を併記する。

## 9. 記録項目 (raw receipt。producer が書き、validator が読み直す)

適格性状態・pairing の成否・受理状態・validator の identity / 結果は
**closed schema で拒否する** (D162 決定 2)。producer が宣言できるのは
利用意図を示す閉集合の種別 (field 名は T-479 択 (b) に従い実装 wave の新 D で確定) と
raw な実行事実・証拠 pointer だけである。

必須項目:

- 環境タグ (`pegasus`) と**環境証明** — `attestation_mode: "required"`。
  **request `892042` はこの 2 つを持たない。** 発火条件 (ii) はここで初めて成立する。
- 測定 checkout (repo / CCBench の head)、依存の pin、build identity、compile argv
- 割当て ID・node・時刻・会計痕跡・単独性検査の結果
- 3 arm の source / binary / compile identity
- 計画した実行順序と**実際の**実行順序、各 run の位置・直前 arm・timestamp・raw TPS
- correctness の**証拠** (boolean の申告ではなく、verifier が再実行できる形)
- liveness、admission telemetry
- **全 attempt**、理由コード、置換関係、親系列 ID

## 10. 必須の否定検査 (実装時に必ず kill する変異)

1. 失敗した投入を台帳と raw の**双方**から落として双射を成立させる。
2. 新しい親系列 ID を自己申告して累積有意水準をリセットする。
3. correctness anomaly を clean と申告する。
4. 適格性 field を raw へ足す (closed schema が拒否するか)。
5. 事前登録した `J` に対し cluster が 1 本足りない状態で受理する。
6. 実際の実行順序が計画と異なる / 待機が不足している状態で受理する。

## 11. 本走の後

`RF` の点推定と区間、6 セルすべての調整済み p 値と同時区間を、**primary の成否にかかわらず
固定表で公表する** (成功セルだけを抜き出さない)。
機序の帰属は本 study では行わない (3 変更を同時に入れたため。ablation は別の事前登録 study)。

## 12. 未確定一覧 (再掲)

【U1】分母条件の母数 / 【U2】`κ_w` の値 / 【U3】roadmap 例外の記録手続き /
【U4】検出力目標と `d` の固定 / 【U5】pilot 本数と非 pool / 【U6】反復数と実行順序 /
【U7】arm 代表値 / 【U8】有意水準の family 割当てと候補上限 / 【U9】着手順序 /
【U10】ポイント総額上限 / 【U11】待機の数値と時間予算
