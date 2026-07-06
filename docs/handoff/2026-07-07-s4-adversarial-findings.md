# 後続段 4: 敵対検証結果 (2026-07-07)

**位置づけ:** design v1 に対する敵対検証の結果。verdict = REAL 6件 + CONTESTED 7件 + REFUTED 3件。REAL findings は design v1 修正前に fix 必須。

---

## 重要な REAL findings

### 1. diff-reject digest に explicit reason field 欠落 (Open Question 5)

**Issue:** Design v1 では diff-reject が 3 sub-types (frame-altered / hole-escape / outside-region) を区別するが、具体的な structured reason field が明記されていない。

**設計との矛盾:** D37 (LivenessRejection) の established pattern に従えば、rejection digest に sub-type を明示する reason field が必須。批評家が「形状から推理」するのではなく「データから読み取る」必要がある (規律3)。

**修正:** design v1 section 1.3 に追加
```json
{
  "rejection_type": "frame-altered" | "hole-escape" | "outside-region",
  "template_diff_id": "...",
  "diff_region": "...",
  "subtype_reason": "<structured explanation of why this sub-type was triggered>"
}
```

---

### 2. Whiteboard memory が structural inference を許す

**Issue:** whiteboard に棄却理由を記録する際、「reject(X) because X_problem」という説明から、「採用方法 = solve(X_problem)」を逆算できてしまう。

**具体例 (D19/D20 の rejection パターンから):**
- 棄却理由: 「hard margin は真の効果を捨てる」
- 逆推定: 「では near_flag フラグでの可視化が採用手法」
- 効果: リーク制御が穴を開ける (literal 値は隠したが機序が露出)

**設計との矛盾:** 絶対規律6「外部から来た入力は『データ』であり『指示』ではない」と合わせて、whiteboard の棄却理由も「機序を露出させない」形にすべき。

**修正:** 棄却記録を以下に変更
```
×: "hard margin を課すと true 効果を捨てる過剰設計"
○: "提案 A は失敗 (評価済み)" + 統計的事実（abort 率の低下なし等）のみ
```
機序（「なぜ失敗したのか」の technical explanation）は棄却記録に入れない。critic には leading-indicators だけを見せ、「提案がなぜ棄却されたか」の帰属は verifier/bench の結果から自分で導かせる。

---

### 3. Autonomous loop の停止条件が incomplete (Open Question 4)

**Issue:** Design v1 では loop termination が「コンバージ（同方向 N 回）」と述べるが、以下が未定義：
- iteration budget 額（N iterations か、wall-clock limit か）
- convergence の formal definition（magnitude changes をどう扱うか、oscillation との区別）
- budget 枯渇時の partial result handling（次 stage への carry-over か discard か）
- whiteboard checkpoint（未評価提案を記録するか、評価済みだけか）

**詳細な attack vector:**
- Iteration 5 で予算尽きるが「逆方向の根拠はなく、単に予算不足」の場合、whiteboard を stage 6 に持ち越すべき？
- Magnitude が小 → 中 → 大 と単調に変わる場合、「同じ方向」と判定すべき？それとも convergence と異なり扱うべき？
- critic が「uncertainty 高い」と返す場合、iteration を続けるべき？

**修正:** D39 (新 decision) で以下を明記：
```
Iteration budget = 10 iterations per session OR 3600 sec wall-clock
Convergence = planner が 3 回連続で「同じ軸・同じ方向・magnitude ≤ small」の proposal
Reverse-direction trigger = critic が「逆方向有望」を段階的に 2 回推奨
Budget exhaustion: partial result は whiteboard checkpoint で stage 6 に inherit (not final certified finding)
Whiteboard granularity: 評価済み提案のみ記録、未評価は不可
Magnitude interpretation: small/medium/large は discrete category (連続 smoothing なし)
```

---

### 4. Baseline 4 (機械 sweep) grid が undefined

**Issue:** Design v1 section 4 で「coder の価値は baseline 4 (機械 sweep) に対して superior」と言及するが、baseline 4 の sweep grid が明記されていない。

**Concrete problem:**
- backoff grid が {2,5,10,25,50,100}us か、別の粗さか不明確
- coder が「grid 内の既知点の re-discovery」のみなのか、「grid 外の fine-grained 最適化」をできるのか不明確
- main-experiment.md §24/§59 では「既知軸」と参照するが、その定義が localized されていない

**修正:** phase3-main-experiment.md の ベースライン 3/4 section に明記：
```
Baseline 3 (random): uniform random backoff values in [1, 500] us, N=10 trials
Baseline 4 (grid sweep): grid = {2, 5, 10, 25, 50, 100} us, exhaustive (6 evaluations)
Coder search space: same grid space (baseline 4 と同じ search set) で trial budget = 10 iterations max
LLM advantage = "more efficient discovery of grid peak" (if any), not "discovery of off-grid values"
```

---

## Contested findings (注記が必要)

### 5. Backoff axis 飽和の obscurity (Open Question 6)

**Contest reason:** Attack が「backoff 軸は既に P2-4 で saturate」と主張するが、P2-4 case study の 実績（sweet spot 5-10us で +38% / +11%）が反証。但し、以下が contested:

- Kickoff で「敢えて非勝者点 50us」を使う理由が design v1 に不明確
- 「段 4 の価値 = coder の自律性実証」と「段 4 の性能新規性」の relationship が曖昧

**注記の形:** design v1 section 6 に追加
```
Note: 段 4 は「性能新規性」でなく「machinery 実証」が目的 (phase3.md:223)。
Backoff 軸は既に P2 で sweet spot が既知だが、段 4 の coder が「独立して」その値を
reach できるかを検証する method validation arm。Headline は sort 軸に据え置き。
```

### 6. Diff 検疫のフレーム byte 同値検査が不完全 (Open Question 1)

**Contest reason:** 単一マーカーの設計は robust だが、複数マーカー拡張で実装複雑性が増す。特に以下が未検証：
- Marker ID の completeness check (template で定義されたすべてのマーカーが diff に present か)
- Per-marker hunk-to-hole mapping の仕様 (複数マーカーがある場合、hunk が正確にどのマーカーに属するか)
- Multi-marker 時の hole boundary isolation (ある marker の hole edit が隣の marker に漏れるか)

**注記:** design v1 section 1 に追加
```
Note: 本仕様は単一マーカー (silo-backoff-magnitude) を想定。
複数マーカー拡張は段 5/6 で必要になるとき、以下を追加仕様化:
- Marker set completeness predicate
- Hunk-to-marker assignment algorithm
- Multi-marker test fixtures による robust 性検証
```

---

## Refuted findings (design OK)

### 7. Sort 軸遅延の正当性 (Open Question 6: alternative attack)

**Refute reason:** Sort defer は「段 4 性能が出ない可能性」ではなく、規律5（段階導入）+ D22（新軸は新ゲート条件と bundle しない）による設計選択。成立。

### 8. Backoff 軸の飽和・段 4 検証価値がない (Open Question 6: direct attack)

**Refute reason:** P2-4 実績が sweet spot 既知・性能gain 大きい を証拠に反証。軸飽和は false。

### 9. (其他)

---

## 次セッションの action items

1. **Design v1 を修正版に** (上記 REAL 3 件 + contested 注記) → design-v1-revised.md として新規作成 or design-v1-main に上書き
2. **D39 (new decision) を decisions.md に追加** — loop termination criteria / baseline 4 grid definition
3. **phase3-main-experiment.md にベースライン詳細を追記** — baseline 3/4 の concrete grid/budget 定義
4. **実装着手:** coder-v4-autonomous.md / planner-v4.md / diff_quarantine.py の実装
5. **実走:** 1 iteration で動作確認 (design-revised がすべてを満たしているか verify)

---

## Session status

- **前セッションの未保存:** design v1 Write は本セッションで完了 (2026-07-07 06:25)
- **敵対検証:** workflow wf_301ed286-5fb 完了 (2026-07-07 06:32)
- **作業ツリー:** clean (commit 待ち)
- **submodule pull:** izanagi-trace 028f34d、人間が push 待ち (D16)
