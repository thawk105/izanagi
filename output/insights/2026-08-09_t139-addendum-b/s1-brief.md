# [T-139] 追補 B 起草 — 段 1 brief (2026-08-09)

```text
authority: none
default_effect: no-state-change
```

## scope

凍結事前登録 core (`output/insights/2026-08-07_t139-mainrun-design/preregistration.md`) §14 が
閉集合として列挙する **追補 B** の 3 field — `b01` 候補数上限 / `b02` 個別公表系列の累積 spending
関数の数値割当て / `b03` 累積台帳を束縛する正規の根の同定方法 — を、逐語の数値と手続きで埋めた
**草案** 1 本を書く。あわせて裁定パッケージと README を書く。**凍結・発効はしない。**

成果物 (すべて docs、**実装面ゼロ**):

- `output/insights/2026-08-09_t139-addendum-b/addendum-b.md` (草案、`authority: none`)
- 同 `package.md` (ユーザー承認パッケージ)、`README.md`、段 2〜6 の子成果物
- `docs/spool/` の worklog fragment

## 確定済み裁定 (前提。本 wave では動かさない)

- **U8 = 別台帳** (2026-08-07、一次控え §40)。primary 系列と個別公表系列に別々の累積台帳を置き、
  候補数上限と累積量を最初の正式試行より前に固定する。台帳は正規の根へ束縛し、新しい親系列 ID の
  自己申告でリセットできないようにする。個別公表は primary の成否にかかわらず 6 セル全件を固定表で公表する。
- **U11 = (a) + 予備 (b)** (同上)。時間予算の組み直しが主経路、要求 walltime 延長が予備。
  数値は追補 A の `a01`/`a06` が確定済みであり、B は触らない。
- **Q7** (2026-08-03) — 候補系列は「親系列 ID + 累積 alpha 台帳 + spending 関数 + 候補数上限」。
  個別公表は Holm / closed testing。**BH (FDR) は採らない。**
- **追補 A (再発行版) は段階 2 発効済み** (2026-08-09 Q1 (a))。`a01`〜`a13` が確定し、`a13` が
  primary の `familywise_alpha = 0.05`、`alpha_k = 0.05/(k(k+1))`、本 study `k = 1`、`alpha = 0.025`、
  正規の根 `F = 88d68f9127b31df5aafc3d59607896626a1652e8` を束縛済み。
- 従属先 core の三つ組を親が実測: `path = output/insights/2026-08-07_t139-mainrun-design/preregistration.md`、
  `commit = 88d68f9127b31df5aafc3d59607896626a1652e8`、
  `sha256 = ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9` (`F` は HEAD の祖先)。

## 不変条件 (破ったら停止)

1. **追補は core の文章を変更しない。**field は `{b01, b02, b03}` を過不足なく設定する (exact-key。
   欠落も余剰も解決失敗)。field key の解決規則は追補 A と同じ envelope grammar に従う。
2. **B は `q` に影響する量を一切持たない。**`a11` の `q(J, α_k)`、`a13` の `α₁`、`a10` の `J` 導出手続きへ
   触れない。primary の判定基準は pilot より前に完全に固定されたままにする。
3. **pilot の raw に依存しない。**B の数値は候補通し番号 `k` と事前固定定数だけの関数とする。
4. core §14 の「越えてはならない線」は B にも効く — 恒真化する判定を作らない、性能測定の開始後の失敗を
   開始前の infra failure へ写さない、§9 の失敗分類を増やさない。
5. **自己 digest を本文へ書かない** (自己参照の禁止)。従属先 core の path・commit・blob digest の
   三つ組は明記する。
6. **発効しない。**本書は承認する決定が canonical 台帳へ fold された後にのみ効力を持つ。本 wave は
   `authority: none` の草案と裁定パッケージまでで止める。
7. **実装面をゼロに保つ。**resolver・producer・validator・consumer・台帳の実体化は producer 実装 wave の
   責務であり、本 wave はコードもテストも追加しない。

## 親の provisional 裁定 (P1〜P5。攻撃対象)

- **(P1)** 個別公表の「6 セル」= `{W1, W2} × {N, H, G}` と読む。根拠は `a12` の逐語
  「成分 = 6 (W1/W2 × N/H/G)」。段 2 プラン期の `D/N/G` 案は採らない。
- **(P2)** `b02` は `k` の関数として総額 `0.05` を配分し、未使用 tail の回収も再配分もしない
  (`a13` と同じ規律)。配分の**形** (等分 / 調和 `0.05/(k(k+1))` / 打ち切り正規化) は段 2〜4 で確定する。
- **(P3)** `b01` は有限 cap を置く。cap の数値は pilot 非依存の量から導く。候補根拠は `a12` の
  familywise Monte Carlo error `δ_MC = 0.001` — 較正の解像度を下回る名目水準は事前 simulation で
  検証できないので、Holm の最小段 `α^pub_k / 6` がこれを下回らない最大の `k` を cap とする。
- **(P4)** `b03` は `a13` と同じ create-only 予約形を個別公表台帳へ適用する。根は `F`、本 study は `k = 1`。
  primary とは**別台帳** (U8) だが ordinal を独立に主張できないよう、公表側 entry が primary 予約 entry の
  digest を親として記録し、validator がその実在と一意性を再計算する。
- **(P5)** 個別公表 family の**検定統計量**は core にも追補 A にも書かれていない。B に書けば余剰 field の
  疑いがあり、書かなければ `b02` の数値が適用先を持たない。**これは B で決め切らず裁定パッケージへ返す**
  (親の推奨案を 1 つ添える)。

## 成果物影響 (`DW-G05`)

`b01`/`b02` を緩めると候補を跨いだ個別公表の FWER が膨張し、certified でない候補についても
「W1 の `N` は有意」型の公表主張が材料レポートへ累積する。`b03` が無いと親系列 ID の自己申告で
公表台帳をリセットでき、累積 spending の防壁が空文になる。(P5) を未解決のまま凍結すると、
`b02` の数値が適用先を持たないまま本走の投入 gate を通る。

## 分割・段の運用

受理集合が変わるため軽量版にはしない。段 2 = codex read-only プラン 1 本、段 3 = 2 レンズ
(統計的正当性 / 凍結境界・exact-key・自己申告経路)、段 5 = docs のみにつき親が執筆 (実装子なし)、
段 6 = 敵対レビュー 2 本 + 焦点再レビュー。**変異 matrix は実装差分ゼロにつき D237 で免除**、
受入全走は免除しない (受入 lease を claim してから背景投入)。
