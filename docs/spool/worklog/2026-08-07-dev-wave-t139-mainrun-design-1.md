---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t139-mainrun-design
seq: 1
title: [T-139] 本走の実験計画を起草し 11 件の裁定へ分解した — 親の実測主張 1 件を artifact 検索で自ら覆した (docs のみ、実装差分なし、branch worktree-dev-wave-t139-mainrun-design)
---

## 本文

- **段 2 と段 3 の 2 レンズが独立に NO-GO を返した。** 実験計画そのものは起草できたが、
  投入前に閉じるべきユーザー裁定が 11 件残る。裁定パッケージ =
  `output/insights/2026-08-07_t139-mainrun-design/package.md`、設計判断は {{D:t139-mainrun-design}}。
- **親の誤りを 5 件認めた。うち 1 件は、親が「実測で確認した」と報告した内容が誤りだった。**
  親は段 1 で「D162 決定 (10) の発火条件 3 点のうち (i)(ii) は request `892042` で成立、
  残るは (iii) consumer だけ」と handoff と中間報告に書いたが、レンズ B の指摘を受けて
  artifact を全文検索したところ **`env_tag` も `attestation` も hit 0 件**であった。
  (ii) は 4 項の連言であり、checkout と pin はあるが前 2 者が無い。**成立は (i) だけである。**
  裁定文が含む事実認定の鮮度を実測する規律は `DW-S01` にあるが、
  **親はその実測を「artifact に当該 field が実在するか」まで下ろさず、
  probe が 3 arm・事前登録済みであることだけを見て (ii) を成立と宣言した。**
- **ただし続けて実測したところ、機構自体は既に存在した** (`orchestrator/qualification/contract.py`
  が `env_tag: "pegasus"` と `attestation_mode: "required"` を exact 契約として持つ。[T-296] は
  (162) で閉じている)。**欠けているのは機構ではなく probe がそれを発行していないことだけ**であり、
  この差が着手順序の推奨を変えた — 段 2 の「9 層を原子的に許可」もレンズ B の
  「新 probe を取るか D162 を明示 supersede するか」も不要で、**pilot 自身を発火条件 (i)(ii) を
  満たす計測にできる**。
- **受理条件を 1 つ書き落としていた (最も重い誤り)。** 親 brief (P3) は primary を
  `N>0 かつ D>δ_D` の 2 条件としたが、裁定済みの受理条件は `G>0` (元の版に未達) を含む 3 条件である
  (正本は worklog (142) と Q9。**D162 ではない** — 段 2 の引用も誤りで、レンズ B が両方を訂正した)。
  `D = N + G` なので 2 条件では `RF ≥ 1` の stock 超過候補を排除できず、段 2 が示した W2 の負例が
  実際の反例になる。
- **標準化効果の量を取り違えていた。** 親は brief に「W1 は N=93,373 に対し within sd 4,009」と
  書いたが、4,009 は modeX arm 単体の sd で、paired contrast の sd は **5,175** である
  (親が再計算して確認)。訂正後の within-cluster 標準化効果は W1 で `N` 18.04 / `D` 69.72 / `G` 106.34、
  W2 で 42.14 / 126.93 / 98.70。**ただしこれは cluster 間設計の根拠にならない** (レンズ A 所見 11)。
- **親が段 3 の後に見つけた新事実を 1 件加えた (段 2 も両レンズも触れていない)。**
  段 2 は 9 層すべてを新規と見積もり「実装被覆 0/9」としたが過大である。
  `orchestrator/qualification/` に T-126 環境適格性のための試行台帳・系列 FSM・投入束縛・
  原子公開・identity が既にあり、Q10 の「計測開始受領証・全 attempt の双射・親系列 ID」に
  構造的に対応する。**D162 決定 (8) が禁じたのは T-126 の artifact を 3 arm 正例と読み替えることで
  あって、コードの再利用ではない。**
- **段 3 の 2 レンズは計 23 件の所見を返し、親は全件を real と裁定した** (nit 3 件を含む)。
  refuted は 0 件。主なもの: 同時信頼領域と Fieller を別構成で二重に課すと恒真な検査になる
  (同じ `q` と共分散なら `LCB(N)>0 ∧ LCB(G)>0` と「有界区間が `(0,1)` 内」は同値)、
  分母条件 `E[D−κS]>0` は Q2 の一意な帰結ではない (親が反例を検算: `(S,D)=(100,10),(1000,50)`、
  `κ=0.06` で比の平均は pass・総量の比は fail)、段 2 の `d_plan` は pilot 結果を見て
  目標効果量を引き下げるため裁定 (142) と逆方向、6 反復 + 待機は 1 時間の allocation に収まらない
  (現 probe は内部期限 3300 秒に対し最悪 3298 秒で余白 2 秒)。
- **資源を実測した。** `rbudgetcheck` = SFC 残 5236.04 / 初期 6000、`pegasusinfo` = gen_S は
  104 request 中 31 running。**1 allocation あたりの point 消費は測れない** — 残高照会は group 単位で、
  104 request が併存するため差分を [T-139] に帰属できない。総額上限の先行裁定へ返した。
- **実装差分がないため、変異 matrix と受入全走は射程外である。** コード・テスト・gate・schema・
  凍結 bytes・certified 選択・材料レポート・proof chain・受理集合はいずれも 1 byte も変えていない。
- 段 8 の自己改善候補は 1 件を routing した ({{F:ruling-fact-finding-staleness}})。

## 次の一手差分

### 更新

- [T-139] **P1・本走の設計は起草済み → 11 件のユーザー裁定待ち + 段 A〜D の実装待ち**:
  実験計画・受理条件・状態閉表・事前登録草案を起草し、裁定項目 11 件へ分解した。
  **投入不可の理由は 3 つ** — (a) allocation 間分散が J=1 の probe から 1 点も推定できず J を
  固定できない、(b) 6 反復 + 待機が 1 時間の allocation に収まらない、
  (c) D162 発火条件は **(i) だけ成立**で (ii)(iii) が未成立。
  推奨する着手順序は `producer 実装 → pilot → validator/consumer 実装 → 本走` で、
  **pilot 自身が発火条件 (i)(ii) を満たすため D162 の supersede は不要**である。
  裁定項目は U1 分母条件の母数 / U2 `κ_w` の値 / U3 roadmap 例外の記録手続き /
  U4 検出力目標と `d` 固定 / U5 pilot 本数と非 pool / U6 反復数と実行順序 / U7 arm 代表値 /
  U8 有意水準の family 割当てと候補上限 / U9 着手順序 / U10 point 総額上限 / U11 待機と時間予算。
  **U1 と U2 が先**であり、これらが決まらないと他は形式的にしか決められない。
  正本 = `output/insights/2026-08-07_t139-mainrun-design/package.md`、
  事前登録草案 = 同 `preregistration-draft.md`、設計判断 = {{D:t139-mainrun-design}}
  base: 9a7d05284a2b927b22a37a193a7bbdebc88c754b9ea3e490ff3be70eadbc21ed
