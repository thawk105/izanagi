# [T-673] 残余 (3) 裁定パッケージ — 本番側 guard D の検出力とコスト

2026-08-10〜11 / wave `dev-wave-t673-d-guard-measurement` / 計測 base `44e35c8b`
(対象 2 ファイルは先行 wave 実測 tip `86842ee0` と byte 同一で、land 時点の main でも本番 module は不変)

**この wave は D を採用していない。本番編集も test の land も行っていない。**
ユーザー裁定 (rulings-inbox §56、2026-08-10「推奨通りで」) は
**「(3) D 計測可・本番編集禁止恒久」**であり、本書はその計測結果である。
D の採否と、本番編集禁止を解くか否かは、本書を読んだうえでのユーザー裁定に属する。

**先行 wave の正本** = `output/insights/2026-08-09_t673-transition-quantifier-ruling/RULING-PACKAGE.md`
(A / A′ / B1 / B2 / C1 / C3 の測定。本書はその §5 の「D. 本番側の走査完全性 guard —— 本 wave では未測定」を埋める)

## 証拠の強さ (先行 wave の区別を踏襲)

- **[台帳]** = 変異台帳に記録された実測。事前登録との一致まで機械照合済み
- **[親測定]** = 親が走らせた計測。逐語を本 directory へ凍結
- **[静的]** = コードを読んで導いた推論。実走していない

---

## 1. 何を測ったか

対象は `orchestrator/campaign/env_contract_activation.py::_validate_activation_transition` の
2 つの量化点 — **G** (`for successor in successor_rows:`) と **P** (`for predecessor, successor in changed:`)。

**D = 走査完全性 guard**: 走査前に期待件数を保存し、loop body 到達件数と一致しなければ通常の `if` で
`ActivationRecordError` を送出する。`assert` を使わないので `python -O` でも消えない。
本番差分は **+20 行 / -0 行、1 ファイル** [台帳]。

D は**配置の異なる 2 変種**を作って両方測った。差は検査位置だけで、検査式と診断文は同一である。

| 変種 | G の検査位置 | P の検査位置 | 意図 |
|---|---|---|---|
| **D₁ (late / 診断保存型)** | 既存 no-op 拒否の**後** | 既存 `first_failure` 再送出の**後** | 既存の失敗診断を 1 件も奪わない |
| **D₂ (early / 診断上書き型)** | loop 直後 (no-op の前) | `first_failure` 再送出の前 | 切り詰めの真因を正確に報せる |

### 測定台

**本番編集禁止を守るため、D は izanagi の外に置いた。** `--shared` clone を repo 外に作り
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-d-guard-measurement/probe-clone`)、その中だけに
C0 (driver のみ・本番不変) / C1 (+D₁) / C2 (+D₂) を作った。**izanagi の object DB には本番編集 commit が
1 つも無い** [親測定、§8 に検証法]。side branch 案は「land しない commit でも ref と object は残り、
cherry-pick → revert で land 履歴に一度入れられる」という敵対レビューの指摘で撤回した。

### 件数の正しい読み方

**distinct な変異は 32 種類**である (直接 slice 14 / guard 破壊 4 / 両層 2 / 縮退形 7 / 意味保存 5)。
これを 11 arm へ適用したので **最終 ledger entry は 107 件**である。
**「107 変異」ではない。** ほかに事前登録を訂正する前の探索走 77 件があり、うち 47 件は
訂正後の走行で置き換えた (§9 の erratum)。実行した変異走行の総数は 154 回である。

---

## 2. 検出力 [台帳]

### 2.1 既存テストの下では、D は検出力を 1 マスも増やさない

既存テスト 2 node (4 env の downgrade / 2 env の no-op) を対象に、直接 slice 14 種を 3 tree へ入れた。

| 変異 | F0 (D なし) | F1 (D₁) | F2 (D₂) |
|---|---|---|---|
| G-N1 | KILLED [downgrade] | KILLED [downgrade] | **KILLED [downgrade, no-op]** |
| G-N2 / G-N3 | KILLED [downgrade] | KILLED [downgrade] | KILLED [downgrade] |
| G-N4 / N8 / N63 / N64 | SURVIVED | SURVIVED | SURVIVED |
| P-N1〜N64 (7 件) | SURVIVED | SURVIVED | SURVIVED |

**F0 と F1 は 14 セル全同一。** frontier (最初に生き残る N) は D の有無で動かない。
理由は先行 wave の結論と同じで、**fixture の env 数を超える `N` では `[:N]` が恒等になる**からである。
D は「切り詰めが起きたか」を実行時に見る機構なので、切り詰めが起きない入力では発火しようがない。

テストファイル全体 (77 node) を対象にした探索走でも、**frontier は 3 tree で同一**だった
(G は N≤3、P は N≤3 が赤、N≥4 は全 tree で SURVIVED) [台帳・§9 の erratum 付き]。
違いは**赤くなる node の数**に出た。

| 変異 | C0 の赤 node 数 | C1 (D₁) | C2 (D₂) |
|---|---|---|---|
| G-N1 | 25 | 40 | **43** (うち no-op 系 3、発行 tool 系 5) |
| G-N2 | 0 | 6 | 6 |
| G-N3 | 0 | 3 | 3 |
| P-N1 | 10 | 15 | 15 |

**D₂ だけが既存の pin 済み no-op 診断 3 件と発行 tool のテスト 1 件を追加で壊す。** D₁ は壊さない。
これは「D をどこに置くか」が実データで分かれる唯一の点であり、**D₁ を採るべき理由**である。

### 2.2 切り詰めが実際に起きる入力では、D は 43 セルで誤受理を拒否へ変えた

env 65 個の合成 chain を公開 API `validate_activation_records()` と loader
`load_activation_state()` へ通す driver を作り、同じ 14 変異を C0 / C1 へ入れた。

- **C0 (D なし)**: 不正行が切り詰めで落ちると **誤受理**になる。位置 middle (index 32) と
  last (index 64) の入力が、N の値に応じて赤くなった。
- **C1 (D₁)**: 同じ入力が**すべて拒否**された。

**C0 が誤受理し C1 が拒否したセルの総数 = 43** [台帳]。これが **D 固有の限界便益**である。
内訳は G 変異 31 セル、P 変異 12 セルで、うち 7 セルは loader 層 (`load_activation_state` 経由) である。

**この 43 セルは driver の検出ではなく D の作用である**ことを、両層変異で裏取りした。
`G-N4 + G guard を if False` / `P-N4 + P guard を if False` の 2 件では、赤くなる node が
C0 と同じ集合へ戻った [台帳、BL arm]。**guard を外すと便益が消える。**

### 2.3 **計測 base 以降に [T-737] が land し、この 43 セルの大半は既存テストが吸収した**

本 wave の計測 base は `44e35c8b` である。その後 **[T-737] (worklog 2026-08-11 (391)) が land し、
既存テストに 65 env の chain を 3 層 (leaf 直呼び / production loader / 発行 tool) へ通すテストが
8 本増えた。** 不正行はいずれも **末尾 (index 64)** に置かれている。

これは本 wave の結論の前提を覆す新事実なので、**land 前に測り直した** (arm F3、現行 main `39e993cb`、
既存 8 node を対象、同じ直接 slice 14 種)。

| arm | tree | 結果 |
|---|---|---|
| F3 | 現行 main (D なし) | **14/14 KILLED、MISMATCH 0** |

**すなわち現行 main の既存テストだけで、登録した直接 slice 族は N = 1〜64 の全域・両量化点・3 層すべてで
既に殺される。** 末尾に不正行を置いた 65 env の chain は、`[:N]` (N ≤ 64) が必ずその行を落とすためである。

したがって **§2.2 の 43 セルは「計測 base 時点の既存テストに対する」限界便益であり、
現行 main に対する D の CI 検出上の限界便益は、この族についてゼロである。**
残るのは次の 2 つだけになる。

- **N ≥ 65 の切り詰め** — 既存テストの M が 65 なので、`[:65]` 以上は恒等になり検出されない。
  D は件数比較なので `N < M` の全域を閉じる [静的] が、本 wave が実測したのは N ≤ 64 までである。
- **runtime での fail-closed** — テスト corpus に無い入力 (将来の env 数、別位置、別構文) に対する
  防御。ただし §4 のとおり D が閉じない形は実在する。

### 2.4 実際に効く 3 層のうち、2 層を測り 1 層は測れない

| 層 | 状態 | 根拠 |
|---|---|---|
| private gate 直呼び | **測定済み** | 既存テスト 2 node と probe の全 node がこの経路 [台帳] |
| production loader (`load_activation_state`) | **測定済み** | driver の loader 2 node。43 セルのうち 7 セルがこの層 [台帳] |
| 発行 tool (`tools/issue_env_contract_activation.py`) | **測定済み (D 抜きで)** | 本 wave の driver では露出できなかった (実 catalog が env 2 個で N≥2 の切り詰めが恒等になるため) が、
[T-737] が合成 65 env catalog を monkeypatch して発行 tool 経路を通すテストを land したので、
§2.3 の F3 arm でこの層も測れた。**D を入れない現行 main で 14/14 KILLED** である |

**本番の実入力に対しては、依然として発行 tool 層で切り詰めを露出できない** — 実 catalog は env 2 個の
ままだからである [静的]。測れたのは合成 catalog を注入したテスト経路である。

---

## 3. コスト

### 3.1 実行時間 — **今回は順位が付いた** [親測定]

計算ノード `bnode070` で、base と D₁ を同一 process 内に別 module として読み込み、
`validate_activation_records()` 1 回の所要を対で測った。ABBA と BAAB を各 8 本 (計 32 対)、
順序は固定 seed で無作為化、warm-up は破棄、outlier は 1 件も除外していない。
逐語は `cost-result.json`。

| M (env 数) | base の 1 call | D₁ の増分 (中央値) | bootstrap 95% CI | 相対 | 順位判定 |
|---|---|---|---|---|---|
| 2 | 80.4 µs | **+949 ns** | [862, 1096] ns | +1.18 % | **付いた** |
| 8 | 147.5 µs | **+1101 ns** | [1063, 1189] ns | +0.75 % | **付いた** |
| 64 | 742.2 µs | **+1564 ns** | [1319, 1716] ns | +0.21 % | **付いた** |

事前登録した 3 条件 (CI が 0 を跨がない / 同符号 8 割以上 / 中央値が測定器ノイズの 95 パーセンタイル超) は
**3 つの M すべてで成立**した。測定器ノイズは同一 arm 同士の差の p95 が 290 / 408 / 717 ns、
空 callable の p95 が約 39 ns である。

**したがって「D₁ は測定可能に遅い」と言える。** 大きさは **1 call あたり約 1〜1.6 マイクロ秒**である。
`validate_activation_records()` は **loader の process あたり 1 回**、**発行 1 回あたり 1 回**しか
呼ばれないので、1 operation あたりの増分も同じ約 1 µs である。

**実用上これを許容するかの閾値は、親は決めない。** 判断はユーザーに属する。

### 3.2 既存の受理集合と診断への影響 [台帳・親測定]

- **未変異のとき、D は何も変えない。** C0 / C1 / C2 の 3 tree で、既存 77 node + probe 17 node の
  **94 node すべてが緑**である [親測定]。
- **切り詰めが起きたときは、診断が変わる。** D₁ でも、G を切り詰めると **P loop 自体が走らない**ため、
  述語違反の意味的診断が走査診断へ置き換わる (probe の理由 node が全位置で赤) [台帳]。
  「D₁ は既存の失敗診断を 1 件も奪わない」と言えるのは **既存テストの corpus に対してのみ**であり、
  一般には奪う。
- **D₂ は既存の pin 済み診断を実際に奪う** (§2.1 の 3 + 1 node)。

### 3.3 偽陽性 — 意味保存リファクタでは 1 件も赤くならない [台帳]

意味を変えない 5 種の変更 (G の tuple 化 / P の tuple 化 / `changed` の rename / 診断 loop の追加 /
コメント追加) を C0 と C1 の両方へ入れた。**両 tree とも 5/5 SURVIVED**、すなわち偽陽性ゼロである。

先行 wave の C1 (AST 構造検査) は、意味保存リファクタ **3/3 で誤検出**した (先行 §3.3)。
**D は構文でなく実行時不変量を見るので、この費用を持たない。** ここが C1 との決定的な差である。

### 3.4 測っていないコスト (誠実のため明示)

- PR ごとの累積 CI 時間、full-suite 差分、shard / collection への影響
- 実 traffic での activation edge 頻度、失敗時の切り分け人時
- 本番リファクタ時に guard を追随させる所有者
- Python / CPU / site を変えたときの overhead 順位の再現性 (1 ノード 1 回の測定である)
- D を land しない場合の再現コスト (probe clone を捨てれば再構築が要る。逐語は本 directory に凍結済み)

---

## 4. 残穴 — D が閉じないもの [台帳]

**D は「走査の完全性」を名乗るが、実際に見ているのは loop の反復回数である。**

| 縮退の形 | D は閉じるか | 根拠 |
|---|---|---|
| 直接 slice `[:N]` (G / P) | **閉じる** | §2.2 の 43 セル |
| 別名へ slice し、期待件数は原集合から取る | **閉じる** (2/2) | RA arm |
| 別名へ slice し、**期待件数も別名から取る** | 閉じない | RA arm。guard 自身が縮退する |
| 関数冒頭 `return` | 閉じない | guard に到達しない |
| **counter の直後に `continue`** | **閉じない** | 件数は 65 対 65 で一致し、**述語を 1 度も評価しないまま素通しする**。捕まえたのは driver だけ |
| guard の削除 / `if False:` 化 | **検出できない (4/4 SURVIVED)** | 既存 77 node + probe 17 node のどれも赤くならない |

**とくに重い 2 点。**

1. **D は body の実行を保証しない。** P の counter 直後に `continue` を入れると、D は通過し、
   誤受理が復活する [台帳、RA-P-COUNTER-CONTINUE]。D を「全 env を検査したことの保証」と
   書いてはならない。正しくは「**予定した反復回数だけ loop に入ったことの保証**」である。
2. **D 自身が無保護である。** guard を消しても現行 main と同じ挙動に戻るだけなので、
   既存テストは 1 件も赤くならない。D を採るなら、**D 自身を殺す正例テストの追加が前提**になる
   (そのテストは本 wave では land していない)。

---

## 5. 先行 wave の候補との比較について [静的]

**「D は B1 (stdlib 生成テスト) より強い」とは書けない。** 測定条件が違うからである。
先行 wave の A / A′ / B1 / B2 / C1 / C3 は **既存 4 env fixture の frontier** で比べられており、
本 wave の D は **M=65 の合成 driver** で測っている。同じ土俵で比べるには、B1 を同じ M 集合・
同じ不正位置・同じ層へ通し直す必要がある。それは本 wave では行っていない。

言えるのは次の 3 つだけである。

- **既存テストの frontier では D は B1 に何も足さない** (D は frontier を動かさない、§2.1)。
- **D はテスト候補と排他ではない。** テスト候補は「CI で回帰を捕まえる」、D は
  「runtime で誤受理を止める」。§2.2 の 43 セルは **driver を land しなくても production で効く**性質である。
- **D の偽陽性費用は C1 より小さい** (5/5 対 3/3、§3.3)。

---

## 6. 実測が支持する結論 (ここまでが親の断定)

1. **D は既存テストの検出力を増やさない。** frontier は D の有無で 1 マスも動かない [台帳]。
2. **D は、切り詰めが実際に起きる入力に対して誤受理を拒否へ変える。** 計測 base の corpus に対し
   43 セルで実測。guard を外すと消えるので、これは D の作用である [台帳]。
   **ただし [T-737] の land により、現行 main ではこの 43 セルの検出を既存テストが自前で行う
   (N ≤ 64 の全域で 14/14 KILLED)。現行 main に対する D の CI 検出上の限界便益は、
   この族についてゼロである** [台帳、§2.3]。
3. **D は測定可能に遅い。** 1 call あたり約 1〜1.6 µs、相対 0.21〜1.18 %。
   1 operation あたりの呼出は 1 回である [親測定]。
4. **D₁ (診断保存型) を採るべきである。** D₂ は既存の pin 済み診断 4 件を追加で壊し、
   得られる情報は診断文の精度だけである [台帳]。
5. **D は「走査の完全性」を保証しない。** 反復回数しか見ておらず、body を飛ばす形と
   guard 自身を殺す形は通す [台帳]。
6. **D 単体では不十分である。** 採用するなら D 自身を殺す正例テストが前提になる。

---

## 7. 親が決めないこと (ユーザーの裁定を仰ぐ)

1. **(主) D を採用するか。** 採用するなら「本番編集禁止恒久」を解く裁定が要る。
   **本 wave の実測は、現行 main では D を採る根拠が弱いことを示している** — この族の CI 検出は
   [T-737] のテストが既に全域で担っており (§2.3)、D の費用 (1 call 約 1 µs、本番 +20 行、
   切り詰め時の診断置換、guard 自身が無保護) だけが残るからである。
   採るとすれば根拠は **N ≥ 65 の領域と、テストに書かれていない入力への runtime 防御**に置くことになる。
   親の推奨は **「採るなら D₁、かつ D 自身の正例テストと同時に」**までで、採否そのものは決めない。
2. **overhead 約 1 µs / call を許容するか。** 実用閾値は測定では決まらない。
3. **D を採る場合、D 自身の正例テストをどう作るか。** 本番へ届く手段は、
   (i) M > 4 の合成 registry を通す integration テスト (本 wave の driver 相当) の land、
   (ii) [T-737] の loader / issuer pin に相乗り、のいずれか。**両方とも本 wave では land していない。**
4. **本 wave の probe を保存するか。** probe clone は repo 外にあり、逐語と SHA-256 は
   本 directory に凍結済みである。clone 自体を残すか消すか。
5. **発行 tool 層 (UNMEASURED) を [T-737] の scope に含めるか。**

---

## 8. 検証のしかた (この報告を疑うために)

- **本番不変**: land tip で `git diff <base> HEAD -- orchestrator/ tools/` が空。
  さらに land 範囲の**各 commit** に `orchestrator/` / `tools/` の path が 1 件も無いこと。
- **probe が izanagi に無い**: `git cat-file -e 101e8f2b^{commit}` / `85afbbe8` / `a7f5be04` が
  すべて失敗する (probe clone の外には存在しない)。
- **台帳**: `ledgers-round2/` の 6 arm (`f0` `f1` `f2` `f3` `v1` `ra`) と `ledgers-round1/` の 5 arm
  (`v0` `ga` `bl` `fp0` `fp1`) が最終集合。各 `summary.matching == summary.registered` かつ
  `MISMATCH == 0`。合計 107 entry。
- **未変異での不変**: `verbatim/base-green-C{0,1,2}.out` の `94 passed`。
- **コスト**: `cost-result.json` の `measurements[].statistics`。
  `ranked` と `missing_conditions` を見る。生 block も全部入っている。
- **D の逐語**: `verbatim/d1-guard.diff` / `d2-guard.diff` (本番への +20 行)、
  `verbatim/test_t673_d_probe.py.txt` (driver 258 行)、
  `verbatim/test_t673_d_cost.py.txt` (測定器 569 行)。
- 全ファイルの SHA-256 は `SHA256SUMS.txt`。

---

## 9. erratum — 事前登録を 2 回誤り、訂正して再走した

**どちらも親の導出誤りであり、実装 (driver・D) の欠陥ではない。** 第 1 巡の台帳は
`ledgers-round1/` に残してある (消していない)。

1. **F arm の runner 範囲**: 先行 wave の *focal 4 node* 実行から期待 node を写したのに、
   runner にはテストファイル全体 (77 node) を渡した。範囲が違うので必ず不一致になる。
   → 対象を 2 nodeid に限定して再走した。第 1 巡の結果は §2.1 の「赤 node 数」の
   **探索的観測**として使い、事前登録された結果としては扱っていない。
2. **G 先取りの見落とし**: D₁ の G guard が発火すると **P loop 自体が走らない**ため、
   述語違反の意味的診断は位置によらず全部置き換わる。親の規則は `pos ≥ N` としていた。
   → 規則を訂正して V1 の G 7 セルと RA 1 セルを再走した。訂正は**コードから導いた規則**で行い、
   観測値の写し取りはしていない。

再走後、**10 arm・93 entry すべてが事前登録と完全一致した (MISMATCH 0)**。

第 1 巡では arm の rc をスクリプトが握り潰していた欠陥も見つかり、第 2 巡で是正した
(各 arm の rc を保持し、1 本でも失敗したら非 0 で終わる)。
