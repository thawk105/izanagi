---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-04
wave: dev-wave-t244-p6-contract
seq: 2
---

## {{D:p6-inductive-contract}}. 択一 7 の P6 は「健全な再導出」ではなく明示的帰納契約として設計する — 実測した候補だけを禁止する cut は受理集合への限界効果がゼロだと示し、実装は発火 artifact 0 件のため行わない

**背景:** D121 決定 (4-b) は、exact-mask no-good cut だけでは軸 (i) を満たさず、
軸 (i) を名乗るには「構造化 anomaly から禁止範囲を独立に再導出する契約」(前提条件 P6) が要ると
自認し、その設計を裁定パッケージの択一 7 として返した。ユーザー裁定 (worklog (126)) は
「P6 を先に設計する」であり、本 wave の指示は「設計だけ (実装なし)」であった。
設計本文と逐語の正本 = `output/insights/2026-08-03_t244-p6-contract/`。

**決定 (1): 中心定理を記録する — 実測した候補だけを禁止する cut は、受理集合への限界効果がゼロである。**
P6 に「実測した候補だけを禁止する」健全性を課すと、導出集合 `B` の各元は
qualifying red を実測した mask に限られる。ところが赤を実測した各 mask は**それ自体が
exact-mask cut の 3 条件を満たす**ので、`B` の各元は exact cut として独立に追加される。
したがって `C ∪ {p} ∪ B = C ∪ {p} ∪ (⋃{m})` であり、`B` は受理集合に 1 点も足さない。
座標 cut も、名乗る条件が半空間 16 点すべてでの再現なので、成立時点で 16 点とも exact cut 済みである。
**段 3 の敵対レンズ 2 本が独立にこの結論へ到達した** (合議ではない)。
D121 決定 (4-b) の「候補 A (現状維持 = 封じ込め) に**近い**強度しか持たない」は、
**受理集合に関しては「近い」ではなく「同一」**であった。本決定はこの点を訂正する。

**決定 (2): 択一 7 の問いの形が変わる — 連続的な「中間」は存在しない。**
択一 7 は exact-mask と座標 cut の「中間」の設計を問うていた。決定 (1) の系として、
P6 が受理集合を狭めるには**少なくとも 1 つの未実測候補を禁止する**必要があり、
それは測定からは導けない**帰納段**である。よって中間は連続体ではなく、
帰納段を踏むか踏まないかの二者択一である。「根拠が要る」の正体は**帰納の正当化**であって
測定の量ではなく、測定を増やしても帰納段を踏まない限り効果はゼロのままである。
これが D106 残余 1 から 9 wave にわたって本件が解けなかった構造的理由である。

**決定 (3): したがって P6 は明示的帰納契約として書く。** 契約は (a) 仮説クラス・反証テスト・
外挿集合を source failure より前に hash 固定する `PrecommittedHypothesis` を必須入力とし、
(b) **`B \ C_exact ≠ ∅` を成立条件にして効果ゼロを「成立」と呼ばせず**、
(c) 事前登録した反証テストが仮説を反証したら origin を seal し (仮説の差し替えを許さない)、
(d) 主張を「その仮説のもと、この origin・この environment に限り」へ有界化し、
外挿部分について「証明した」と名乗らない。結果型は 4 値とし二値化しない。

**決定 (4): 入力は candidate 起因の正しさ証拠の閉じた和とする。**
段 2 案は clean な DSG cycle witness だけを入力にしていたが、これは verifier 正本が
「trace-hook の問題ではなく variant が引き起こした CC 正しさ違反」と明記する 3 counter
(`lock_coverage_violations` = D38、`write_intent_violations` = T-152、
`permutation_violations` = D41) を構造的に取りこぼす。除外すると**失敗を cycle channel から
integrity channel へ移すだけで P6 を回避できる**。よって入力を
`CycleWitness ∪ IntegrityWitness` の閉じた和とし、未知の witness kind は fail-closed とする。
なお `IntegrityWitness` の構造化表現は現行に存在せず、その新設は裁定パッケージへ返す。

**決定 (5): 非適用を二分する。** 段 2 案は「generalized cut を導入しなければ P6 = 非適用」と
していたが、これは **P6 を 1 行も実装せずに承認上限の引上げを通せる**恒真化である。
`NOT_IMPLEMENTED` (handler・全 witness-kind adapter・正負 calibration・未知 kind の
fail-closed が未実装) は FAIL、`NOT_CLAIMED` (実装済みで generalized cut を主張しない) だけを
免責とする。D121 決定 (7) の「非適用を無条件必須にすると cap が永久解除不能になる」という懸念は
この二分で回避できるが、**記録済み決定の改訂にあたるため裁定パッケージへ返す**。

**決定 (6): exact-mask cut を P6 から独立・先行させる。** 段 2 案は exact cut の追加を
P6 の結果式の中にだけ置いており、exact cut が P6 の予算・発火可否・crash 復旧に従属していた。
qualifying red の直後に exact cut を原子的に append し、P6 の eligibility も予算も参照しない。
install 後に generalized proof が欠落した場合は cut を外さず origin 全体を seal する
(外すと受理集合が再拡大するため)。cut key には origin manifest・emitter・verifier policy・
environment contract・IR schema の hash を束縛し、いずれかが変われば新 origin として持ち越さない。

**決定 (7): 実装しない。** 根拠は 3 つあり互いに独立である。(a) ユーザー裁定が「設計だけ」である。
(b) `DW-G04` の発火 gate を満たす既存 artifact path も計測 ID も**書けない** — 実 campaign 30 本の
WAL census で、構造化 non-serializable witness は fixture 由来の 1 件 (帰属が偽) だけである。
(c) 決定 (2) の帰納段はユーザー裁定を要し、実装すれば未裁定設計を既成事実にする。
したがって設計メモに留める。承認上限 1 は変えず、cap-lift の結線もしない。

**決定 (8): 軸非依存にできるのは外側 dispatch envelope までとする。**
witness 契約と axis adapter の意味契約は軸ごとに別に書く。cycle witness と integrity witness は
型・verdict・同値関係が異なり、単一署名では扱えない。
また trigger-gating を**永久非適用としない** — 現時点で発火不能なのは
(i) proposal が canonical IR でなく自由 1 行 C++、(ii) 実 campaign の構造化 anomaly が 0 件、
(iii) 唯一の witness が fixture 由来で帰属が偽、の 3 点によるものであって、
「因果路が構造的に存在しないから」ではない。

**却下した案:** (a) 段 2 案のまま「実測した mask だけを禁止する健全な導出」として確定する —
決定 (1) により受理集合への効果がゼロであり、`Derived` と名乗ると proof chain と承認判定だけが
実体より強い主張を行う。(b) 帰納段を暗黙に含めて「再導出」と呼ぶ — 帰納を証明と偽る名乗りであり、
規律 3 の「なぜ」を満たしたと誤認させる。(c) 座標 cut を無条件に禁じて exact-only で閉じる —
それは還流の放棄であり、本件を未解決のまま残す。放棄するなら決定として明示的に閉じるべきであり、
これは裁定パッケージへ返す。(d) trigger-gating を永久非適用として本件を閉じる — 決定 (8) のとおり
前提が誤りである。

**この決定が確定していないこと:** crash window の正規回復状態機械、replicate 数と
schedule / seed policy、generator への 0 bit の end-to-end 証明 (artifact path・mtime・size・
cache hit・同一 UID 観測を含む observable surface の閉集合が未定義)、sort 軸の同値関係、
build 上限と計数規則。いずれも設計本文に「書けなかったもの」として明示した。

**研究状態への影響: なし。** 本 wave は docs と insights のみで、production 挙動、実験の受理集合、
certified 選択、材料レポート、proof chain、凍結 bytes はいずれも不変である。
実装差分が無いため変異 matrix と受入全走は対象外である。
