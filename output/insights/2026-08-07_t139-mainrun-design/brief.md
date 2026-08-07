# [T-139] 本走の設計 — 段 1 brief (2026-08-07、凍結)

```text
authority: none
default_effect: no-state-change
```

本書は凍結する。誤りは README の §訂正 を正とする。

## scope

代替 X (modeX) の**生死確認は両 workload で成立済み** (request `892042`、W1 13.5% / W2 14.4%、
J=1 の engineering screen)。本 wave は、RF 統計設計 (Q1〜Q11 全件裁定済み) に準拠した
**本走 = 正例 artifact 生成 study の実験計画**を設計し、**裁定パッケージで返す**。
cluster 数 J、標本配分、事前登録の骨子、着手順序の 4 点が対象。
**実装差分ゼロ** (コード・テスト・gate・schema・凍結 bytes・certified 選択・受理集合すべて不変)。
したがって変異 matrix と受入全走は射程外。

## 不変条件 (緩めない)

- Q1=総回復率 `E[N]/E[D]`、Q2=`δ_D` は stock 比の相対量で workload 別・primary endpoint は
  trace-disabled `throughput_tps` 1 本、Q3=scalar floor でなく同時信頼領域、Q4=1 allocation =
  1 immutable subcampaign、Q5=二段階 (pilot 先行)・d≈1.0 が既定・**結果を見てから J を足さない**、
  Q6=schedule / carry-over / washout / sharp か weak かを事前登録、Q7=IUT・Holm・系列台帳の 3 分割
  (BH 不採用)、Q8=correctness anomaly は終端 reject、Q9=Fieller primary・分母 screening 廃止・
  `RF>1` は帰属しない、Q10=D116 方式の RF 拡張、Q11=独立 validator が raw receipt から再計算。
- D162: producer は適格性を宣言しない / raw receipt は適格性 field を closed schema で拒否 /
  権威は独立 validator / consumer は同一呼出し内で validator を再実行。
- D126 決定 (4): 結果を見てからの事後調整をしない。
- T-479 択 (b): 種別軸の field は `artifact_role` を使わず別名 (第一候補 `declared_use_class`)。

## 親の provisional 裁定 (すべて攻撃対象)

各項に「これを反証しうる最も安い実測」を併記する (`DW-S01`)。

- **(P1) 二段階は external pilot とし、pilot データを本走へ pool しない。**
  反証実測: 既存 D116 / 8c 事前登録に internal pilot の前例があるか repo 意味検索し、
  pool 時の型 I 誤り膨張を閉形式で 1 本示す。
  成果物影響: pool すれば同じ raw から受理が反転しうる。
- **(P2) cluster 内は probe と同一の 5 rep balanced schedule に据え置き、標本は cluster 側で増やす。**
  反証実測: 実測済み within-cluster RF sd (W1 0.00575 / W2 0.00366) を使い、
  cluster 間 sd が within の何倍のとき rep 増が J を減らすかを解く。
  成果物影響: 配分を誤ると同じ point 消費で検出力が落ちる。
- **(P3) primary は「両 workload で `N>0` かつ `D>δ_D`」の IUT 1 本。RF 点推定と Fieller 区間は
  報告するが受理条件へ入れない。**
  反証実測: Q9 の境界閉表 (有界/非有界/不連結 × 0 と 1) が primary から外すと恒真化しないか、
  package.md Q9 の状態表を引いて照合する。
  成果物影響: family の取り方で `all_pass` の意味と多重補正の要否が変わる。
- **(P4) `δ_D` は probe 実測の劣化幅 (W1 `D/stock`=88.2%、W2 90.2%) より十分小さい保守値を
  workload 別に事前登録する。**
  反証実測: probe が別 study であることを prereg §7 の分岐条項で確認し、
  `δ_D` を probe 値から導くことが D126 決定 (4) の事後調整に当たらないかを判定する。
  成果物影響: `δ_D` 単独で正例の成立/不成立が反転する (Q2 の記載どおり)。
- **(P5) 目標効果量は Q5 既定の d≈1.0 (J≈11) を据え置き、予備 cluster を事前順序固定で足す。**
  反証実測: `N>0` の within-cluster 標準化効果 (W1 は N=93,373 に対し within sd 4,009 → d≫10) から、
  cluster 間分散が within の何倍で d=1.0 まで落ちるかを逆算し、pilot の判定線として書けるか確かめる。
  成果物影響: J 不足は恒常的な判定不能、J 過剰は point の空費。
- **(P6) 本走の投入前に producer (D162 決定 2 の closed schema raw receipt) の実装が要るが、
  validator と consumer は本走の後でよい。**
  反証実測: D162 決定 (4) の consumer 契約を読み、consumer 不在のまま raw を取った場合に
  certified artifact へ到達できるか、および receipt schema が後で変わったとき J 本の
  allocation が再走になるかを判定する。
  成果物影響: 順序を誤ると 11 allocation 相当を捨てるか、逆に発火条件不成立のまま実装を先行させる。

## 成果物の形

`output/insights/2026-08-07_t139-mainrun-design/` に、brief / s2-plan / s3-lensA / s3-lensB /
s4-adjudication / **package.md (ユーザー裁定パッケージ)** / **preregistration-draft.md** を置く。
package.md は裁定項目を番号付きで列挙し、各項に選択肢・推奨・成果物影響・費用を書く。
canonical 3 台帳は spool fragment 経由でのみ触る。

## 並列分割方針

段 2 は codex read-only 1 本。段 3 は 2 レンズ並列 —
レンズ A = 統計的妥当性 (推定量・分散成分・検出力・多重性・区間)、
レンズ B = 手続き整合と実行可能性 (裁定条文との整合、D162 の順序、資源と queue、事前登録の実体化)。
段 5・6 は実装差分がないため飛ばす見込み (段 4 で確定する)。
