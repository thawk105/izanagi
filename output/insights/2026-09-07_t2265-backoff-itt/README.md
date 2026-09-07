# [T-2265] adaptive backoff の反実仮想 ITT — 事前登録を凍結し、12 seed で実測した

2026-09-07。branch `worktree-dev-wave-t2265-backoff-itt`。base `cf4273f56`。
機構の一次資料は `output/insights/2026-09-07_t2265-backoff-counterfactual/README.md` (実測なしの回)。

## 0. この wave が主張すること・しないこと

**主張する:**

1. 反実仮想試験の**事前登録を、腕の outcome を 1 つも見る前に凍結した**
   (`docs/backoff-counterfactual-preregistration.md`、sha256
   `ee7617f57bf6816fd8bfb42b5830926be1174ebcca617ed122c3fbca62f127a6`、commit `a27543ab2`)。
2. **事前登録した 12 seed の実測を完了した。** 12 job すべてが完走し、成果物はいずれも
   事前登録の sha256 を束縛として記録している。
3. **事前登録した推定量を当てた結果、主判定は `inconclusive` である。** これは事前登録した
   除外規則が発火した結果であり、規則どおりの帰結である (§3)。

**主張しない:**

- **腕の効果の有無を主張しない。** 主判定は判定不能であり、効果があるともないとも言えない。
- **性能結果ではない。** 測定は trace 有効 build の診断であり、絶対規律 1 に従い throughput の
  性能主張には使わない。
- **policy≠0 の cell は未認証である。** 正しさは主張していない。

## 1. 事前登録 (最初の成果物)

結果を見る前に固定したものは次のとおり。詳細は文書本体。

| 項目 | 固定した内容 |
| --- | --- |
| 推定対象 | trace 有効な診断系における、割当についての 1 窓先の局所 ITT |
| 符号 | `D[r] = mean(Y | Z=0) - mean(Y | Z=1)` (推奨方向 minus 反転方向) |
| outcome | `Y = ln(T[i+1] / T[i])`、`T = window_commits / window_us` |
| 主層 | policy 2 / write-heavy / 48 threads のみ |
| 集約 | run を cluster とする等重み平均、`R = 12` |
| 等価域 | `±ln(1.03) = ±0.029558802` (対称 log 域) |
| 判定 | 等価は 90% CI の TOST、優越は 95% CI |
| 除外 | 後続 event を持たない最後の更新だけ。ほかは一切除外しない |
| seed | 12 値を逐語で列挙 (`izanagi-t2265-policy2-seed-NN` の SHA-256 先頭 8 byte) |
| 停止 | 固定 12 job、途中解析なし、結果を見てから足さない |

**この文書は盲検の holdout ではない。** 何を見たうえで設計したかを §0.1 に列挙している
(既存の v1 診断、静的 backoff 曲線、そして腕自身の**構造データ**)。「腕の出力を一切見ていない」
とは言えないことも明記した。

## 2. 実測

- 固定 checkout `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-backoff-itt/itt-tree`
  (detached、実装 commit `a719a228a`、tracked-clean)。
- **12 job を 1 本ずつ直列に投入**した (同時 build による build cache の取り合いと、
  共有 git 管理領域の破壊を避けるため)。job `981402` 〜 `981503`。
- 出力は `/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-itt/` の 12 file。
  **12 件すべてが事前登録の sha256 `ee7617f5…` を `counterfactual_preregistration` に記録している。**
  seed も 12 値すべてが一致する。1 job あたり 18 run (3 腕 × 3 workload × 2 threads)。
- **投入経路の契約は 1 byte も変えていない。** 既存の投入スクリプトが反実仮想の 3 腕を
  既に受理形として持っていた。新しい Pegasus 実行体は作っていない (F660 の判定は段 1 で済ませた)。

### 2.1 生死確認 (段 1、DW-G01)

反実仮想の腕を計算ノードで走らせたのは本 wave が初めてである。事前登録を凍結する**前**に
job `981337` で構造だけを確認した。逐語は `verbatim/stage1-liveness.md`。

- 腕は 3 本とも設計どおり: policy 0 は反転 0.000、policy 1 は 1.000、policy 2 は 0.517〜0.530。
- policy 2 では割当の約 98% が実際の反転として実現する。
- **policy 1 の write-heavy 48 だけが異質**で、割当 1.000 に対し実現は 0.492、割当前に両方向可は
  0.246 しかない。**常に反転する腕はこの regime で backoff を clamp 領域へ追い込む。**
  「常に反転」が同一軌跡上の反実仮想ではないことの直接の証拠である。

## 3. 判定 — 事前登録した規則により inconclusive

解析結果の正本は `analysis-result.json`。

**主層 (policy 2 / write-heavy / 48 threads) の cluster 数は 12 で揃った。** しかし事前登録 §7 の
「`window_commits = 0` の event が 1 件でもあれば、その event だけを落とさず主判定全体を
inconclusive にする」が発火し、**主判定は `inconclusive`、副次 14 層もすべて同じ理由で判定不能**である。

原因を数えた (これは構造の計数であって outcome の値ではない):

- policy 2 の全 72 run、総 event 51,748 件のうち、窓の commit が 0 の event は **57 件 (0.110%)**。
- **そのうち 55 件は `seq = 0`**、すなわち run の最初の窓である。この窓は最初の割当が当たる前に
  閉じるので、**処置とは無関係な走り出しの窓**である。残り 2 件は `seq = 10` と `seq = 11`。
- 各 run の最初の event の `seq` は例外なく 0 である。

**規則は結果を見た後に変えていない。**「`seq = 0` を位置だけで落とす」は、最後の更新を落とすのと
同じ型の処置前の規則であり筋は通るが、**結果を見た後にそれを採るのは後付けであり、事前登録の意味を
壊す。** したがって本 wave では採らない。

**`seq = 0` を除いた推定値は計算していない。** 計算して記録すれば、次の事前登録がその値を見た後の
ものになり、追試の価値が失われるためである。

## 4. 次の一手が測定のやり直しでない理由

**12 の成果物は凍結済みで、束縛 (事前登録 sha256、patch stack、seed、binary sha) もすべて揃っている。**
次 wave は「`seq = 0` を位置だけで除く」規則を**結果を見る前に**事前登録し、
**この 12 件をそのまま解析するだけ**で確認的判定を出せる。計算ノードへの再投入は要らない。

## 5. 実装

| 変更 | 中身 |
| --- | --- |
| seed の引数化 | `--step-policy-seed` / `IZANAGI_T2187_STEP_POLICY_SEED`。10 進 uint64 のみ。policy 2 の cell を含む走行で必須。seed は policy 2 の genome にだけ届き、policy 0/1 の binary は変わらない。cell literal は不変 |
| 事前登録の束縛 | `counterfactual_preregistration` を `pending` から新事前登録の sha256 へ。付与するのは exact な 3 腕と exact な軸で走った成果物だけ |
| 解析 module | `orchestrator/campaign/backoff_counterfactual_analysis.py`。offline 専用、公開 CLI なし、公開面は関数 1 本 |

既存 validator、認証の exact 2 cell 契約、patch A の hard pin、既存の逐語 pin、patch C は
いずれも変更していない。

## 6. 段 6 のレビューが見つけたもの

敵対レビュー 2 本 (因果推論のレンズと実装規律のレンズ) が**独立に同じ欠陥**を挙げた。
逐語は `verbatim/s6-review-lensA.md` / `s6-review-lensB.md`、裁定は `verbatim/s4-ruling.md`。

1. **恒真ゲート (must-fix)。** 判定の定数 (90% の t 値、等価域の幅) をテストが実装 module 自身から
   取っていたため、定数と実装を同時に変えると緑のまま通り、事前登録した変異 M13 / M14 を
   検出できなかった。逐語の期待値で固定し、さらに「90% なら等価だが 95% なら等価でない」
   合成 cluster を足して挙動でも赤くなるようにした。
2. **認証要求の受理集合の拡大 (must-fix、絶対規律 2)。** seed の引数を共通の引数解析へ足したことで、
   driver を直接呼ぶ認証要求が seed 付きでも受理され、seed が黙って無視されていた。明示拒否させた。
3. **解析の build 検査が部分一致 (must-fix)。** 並行性制御そのものの compile flag が違う binary の
   測定値を受理しえた。exact 一致へ変えた。
4. **解析が patch と事前登録の束縛を検査していなかった (must-fix)。** 呼出し側が渡した任意の file を
   事前登録として信用していた。凍結 sha256 を module 内の独立な定数として pin した。

## 7. 段 3 の相談が親の草稿の誤りを 2 件見つけた

どちらも親が現物で検算して**異議が正しい**と確認した。

1. **等価域の算術が誤っていた。** `ln(0.97) = -0.030459`、`ln(1.03) = +0.029559` であり、
   throughput 比 `[0.97, 1.03]` の log 域は `±0.029559` ではない。対称な `±ln(1.03)` へ直した。
2. **主層の根拠の一般化が誤っていた。** 親 brief は「他 regime は勾配 0 が 39〜51%」と書いたが、
   親自身の表の balanced 48 は **2.1% / 7.4% / 8.1%** である。主層は維持しつつ
   「唯一腕が届く層」という一般化を撤回した。生死確認でも policy 2 の全 6 regime で
   割当前の両方向可が 0.967〜0.982 あり、処置は全 regime に届いている。

ほかに、決定的 LCG を「厳密に独立」と呼ばないこと、最後の更新の除外が処置依存であること
(影響は主層 583 件中 1 件 = 0.17%)、throughput 0 の更新を個別に落とすのが処置後除外であることを、
いずれも限定または規則として事前登録へ書いた。

## 8. scope から外したもの

**trace 無効の性能 7 block は本 wave では実施しない** (段 4 裁定 §2)。

1. 依頼が名指しした推定量ではない。`p1 / p0` の run 全体比較は反実仮想ではない。
2. 7 block とも腕の測定順が固定で、腕と job 内時刻が完全に交絡する。旧事前登録は block ごとに
   開始位置を巡回させてこれを避けていた。巡回順の組み直しは別の実験の設計である。
3. policy≠0 の cell は未認証である。
4. 規律 4・5 (実験規模を無造作に大きくしない、段階導入)。

## 9. 変異検査

probe → 本走の 2 段。詳細と erratum は `mutation-notes.md`。

- **probe** (`mutation-probe-spec.json` / `mutation-probe-report.json`): baseline PASSED。
  **10 変異すべてで赤が出た。生存 0。** KILLED 4 / MISMATCH 6。MISMATCH はすべて
  「親が予測した赤の node 集合が実際と違った」型である。
- **本走** (`mutation-spec.json` / `mutation-main-report.json`): 観測された完全集合を登録し直して再走。

## 10. 未了と次の一手

- **`seq = 0` を位置だけで除く規則を事前登録し、既存の 12 成果物で確認的判定を出す。**
  再投入は不要。
- policy 腕の trace 無効な性能測定 (巡回順の block 設計 + 独自の事前登録)。
- policy≠0 の cell の直列性認証。
- driver の共通 `not_certified` 文言が診断成果物と矛盾している件の修正 (事前登録 §1 に記録)。
- 全ての割当に後続窓を保証する trace の延長 (事前登録 §4 の限定を外すため)。
