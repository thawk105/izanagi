---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2009-checker-mutation-power
seq: 1
title: [T-2009] 検査器を骨抜きにする 5 変異はすべて既存テストが捕まえた — 穴は 0 件で、代わりに同一性層が等価変異を 53 node で赤にすることが出た (docs のみ、branch worktree-dev-wave-t2009-checker-mutation-power、変異 7/7 期待一致・生存は等価対照 1 件のみ)
---

## 本文

- 絶対規律 7 が「弱体化の検出は同一性でなく挙動で行う」と定めた挙動検査に、実際の検出力が
  あるかを初めて実測した。D799 決定 (2) が「g6 / r8 の対は通してしまう」と挙げた 5 件
  (分類器が常に G2 / 版比較が epoch 無視 / 長さ 4 以上の巡回を無視 / framing violation を
  常に 0 / fixture の hash や dir 名で答える) を変異として書き、**全件 KILLED**。
  本測定の範囲で規律 7 が開けた穴は **0 件**である。詳細と数値の正本は
  `output/insights/2026-09-02_t2009-checker-mutation-power/`。
- D799 の記述は誤りではない。5 件は **`g6` / `r8` の対**の射程についての記述で
  あって、既存スイート全体の射程ではなかった。この区別を実測で確定したのが本 wave の成果である。
  後続レビューが D799 を「スイートに 5 つの穴がある」と読むのは誤読になる。
- **狙っていなかった実測が 1 件出た。** 等価対照として置いた変異 (`u != v` を
  `not (u == v)` に書き換えるだけ) が、分母を絞らない probe 走で **53 node** を赤にした。
  理由はすべて `IdentityMismatch: contract-loader-drift: disk bytes が記録 commit blob と
  不一致` で、`CONTRACT_LOADER_RELATIVE_PATHS` の HEAD blob pin である。同じ 53 node は
  検査器を壊す正例対照 (rw 反依存辺を落とす) でも赤になる。**同一性層は「壊した変異」と
  「何も変えない変異」を区別できない**という規律 7 の主張の、この repo の現物による実測。
  正例対照の赤 72 件のうち 53 件 (74%) がこの層だった。詳細は {{D:identity-layer-attribution}}。
- **台帳の記述に誤りを 1 件見つけた。** `orchestrator/tests/fixtures/README.md` は長さ 4 以上の
  巡回について「どの fixture も担っていない」と書くが、`r5_nonlatest_transitive` が
  長さ 4 の G2 witness (`T2 → T3 → T4 → T50 → T2`) を持つ。同節の「規模で買えない限界」の
  測定自体は否定しない — 対象が実 emitter 由来 fixture に限られていただけである。
  **本 wave では訂正しない** (「塞がず裁定へ返す」境界)。訂正の可否は裁定へ。
- 段 2 プランと段 3 レンズ A が**そろって**「同一性 pin はこの分母では発火しない」と静的に結論し、
  実測で覆った。呼び出し関係の追跡は正しかったが、分母に入れた 2 file がその経路を通っていた。
  静的結論のまま進めていれば正例対照の検出力を 72 node と記録していた (実際の挙動検出は 19)。
  詳細は {{F:static-pin-scope-refuted-by-measurement}}。
- 実装面の差分はゼロ。repo の tracked file は 1 byte も変えていない (変異は固定 commit
  `28ebff456` の使い捨て worktree 内のみ)。段 5 の実装子は立てていない。
  変異 matrix は免除せず実走した (7/7 期待一致、baseline PASSED)。
- 子は 3 本 (plan 1・consult 2)、いずれも rc=0 で採用 gate 緑。

## 次の一手差分

### 完了

- [T-2009] 検査器を骨抜きにする 5 変異を書いて実走し、既存テストが全件捕まえることを確定した。
  同一性層が等価変異を 53 node で赤にすることも実測し、insight として構造化した。
  塞ぐ実装は行わず裁定へ返した。
  remaining: none
  base: 8e0aa64ada385104b83a3c2ffcee16e074e56abcc50b7905336219ebde155e21

### 新規

- {{T:len4-clean-negative-fixture}} **P2・ユーザー裁定待ち**:
  長さ 4 以上の巡回を **clean な入力**で捕まえる負例が無い。`r5_nonlatest_transitive` は
  `missing_txids=46` で integrity が unclean なので、当該変異を当てても
  `non-serializable → indeterminate` までしか動かず、**certified へ倒れる経路を張っていない**。
  密な txid を持つ手製 fixture を足すかどうかを裁定する。D799 却下案 (a) が
  「実 prefix を大きくしても長さ 4 は買えない」を確定させているので、足すなら手製になる。
  実装面のため Codex `role=author` が要る。
- {{T:fixtures-readme-len4-correction}} **P2・ユーザー裁定待ち**:
  `orchestrator/tests/fixtures/README.md` の「長さ 4 以上の巡回はどの fixture も担っていない」を
  訂正するかどうか。`r5_nonlatest_transitive` が担っていることを本 wave が実測した。
  同記述は D799 決定 (2) に基づいて書かれているので、訂正は D799 の射程の記述にも触れる。
  **r5 が担うのはグラフ事実の検出までで、certified への遷移は担っていない**点を落とさずに
  書けるかが論点。
