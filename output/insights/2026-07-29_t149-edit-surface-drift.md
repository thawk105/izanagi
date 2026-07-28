# [T-149] 編集面の独立 hard-code ドリフト — 導出化の棄却と機械検査テストによる封鎖

**位置づけ:** dev-wave 全 9 段 (source_digest = 正しさ防壁への接触があり軽量版不可)。
実装 commit = `4b4fb76` (テスト 7 本 + stale 記述訂正)、fix = `a01857d` (段 6 must-fix 4 件)、
`069ae42` (再レビュー RR-1)。production の挙動変更は 0。
一次資料 (逐語) = `2026-07-29_t149-review-verbatim/` (段 2 プラン 1 + 段 3 敵対相談 2 +
段 6 敵対レビュー 2 + 焦点再レビュー 1、変異 harness と台帳 JSON を含む)。

**結論:** T-149 の当初案「編集面 hard-code の単一正本からの導出化」は**採用しない**。
ドリフト封鎖は literal 正本を維持したまま、関係式の機械検査テスト (完全一致 + 型付き例外)
で行う — T-140 段 3 N2 の原処方に一致する。

---

## 1. 段 1 実測 — 編集面 hard-code の出現と分類

| # | 出現 | 分類 (段 3 A-5 の裁定後) |
|---|---|---|
| 1 | `source_digest.py` EVOLVE_BLOCK_SOURCES | **正本** |
| 2 | `source_digest.py` ALLOWLIST | 独立 gate (編集認可面。型付き例外 = Options.cmake) |
| 3 | `hooks/guard_write.py:37` | live copy (hook 単体動作要件。既存一致 assert あり) |
| 4 | `s6_proposal_rounds.py` freshness の `ebs`/regen | **凍結時点記録** (2026-07-13 面) |
| 5 | `s1_known_axes_freeze.py` SILO_CMAKE_REL | 歴史的凍結レシピ (generator 自己 hash pin) |
| 6 | `.claude/agents/coder.md:13` | live copy (stale だった → 正本ポインタへ訂正) |
| 7 | `tests/s1_expected_goldens.py` の CMake path | 独立 golden (統一対象外) |

段 1 の親 brief はこの分類を欠いたまま全部を「ドリフト面」と一括した — それが導出化という
誤 scope の根。**定数統一系の wave は出現を live copy / 独立 golden / 凍結 snapshot /
歴史記録に分類してから scope を切ること** (§6 改善候補)。

## 2. 導出化の棄却 — 段 3 の 2 レンズが独立に到達した 3 経路 (逐語 = lensA/lensB.md)

1. **[A-2] ALLOWLIST 導出は fails-closed 反転。** EBS 拡張と編集認可面拡張は独立二段の
   trust-boundary review (axis-onboarding §手順が明示)。導出は「EBS 追加だけで認可面が
   自動拡大」= 以前 `assert_worktree_within_allowlist` が止めた入力を通す。
2. **[A-3] s6 freshness の live 参照化は stale packet を通す緩和 ((P1) refuted)。**
   freshness が読むのは可変な N1_PROVENANCE であり frozen payload ではない。N1 を現行面へ
   更新すると、旧 hard-code なら止まった stale packet が live 参照では通る。凍結時点
   hard-code は「凍結記録」として正しい。残穴 = [T-163] (§5)。
3. **[A-1/B-1] s1 は編集自体が F27 再演 ((P2) refuted)。** `known_axes_freeze.json` が
   generator 自己 hash + sources pin を持ち、`verify_document` は値を見る前に
   bytes 不一致で拒否する。評価値が同じでも成立しない。

## 3. 実装形 (最終) — テスト 7 本 + 訂正 2 件、production 0 byte

- `test_campaign.py`: T1 = ALLOWLIST == frozenset(EBS) ∪ {OPTIONS_CMAKE} (完全一致 +
  型付き例外) + EBS tuple literal pin (順序 = digest pre-image)。T3 = 3 driver
  (p3_s4_loop / p3_s4_loop_sort / axis_trigger_gating) の SOURCE_REL **driver 別 literal pin**
  (所属だけでは編集面内の軸取り違えを全通しする — 段 6 RA-2)
- `test_s6_proposal_rounds.py`: 構造検査 = freshness_check 実装 AST から `ebs` literal を
  直接抽出し live EBS と突合 (テスト側に面の写しを置くと lockstep 更新で沈黙 — RR-1)。
  behavioral 3 本 = 抽出面 ∪ live EBS ∪ 反例 2 種の母集団で全緑 + 双方向 positive control
  (編集面外 opened=True / 編集面内 opened=False — 片方向だと述語弱体化が生存、RA-1)
- `test_s1_known_axes_freeze.py`: T4 = SILO_CMAKE_REL == "external/ccbench/" +
  `_PROTOCOL_CMAKE`(silo) の外部関係検査 (s1 本体 0 byte)
- 訂正: coder.md の designated ソース列挙 → 正本ポインタ化 (**review_ledger +
  role-adapter の明示更新を伴う** — 段 4 の「pin なし」は output pin だけを掃引した誤実測で、
  初回受入全走の test_codex_agents 赤で検出。前例 e427194 と同手順で closure)。
  p3_s4_loop.py:70 の「唯一メンバ」コメント訂正

## 4. 変異台帳 — 9/9 KILLED (最終 commit `069ae42` に対する本走)

主張射程 = **focused 9 node 集合内での期待 node 完全一致** (段 6 RA-4 の訂正。全 suite の
挙動は受入全走 3148 passed / 18 skipped rc=0 ×2 が別途担う)。生値 =
`2026-07-29_t149-review-verbatim/mutation-results-v2.json`、harness = 同 dir。

| 変異 | 内容 | 期待赤 (観測一致) |
|---|---|---|
| V1 | EBS へ偽メンバ追加 | T1 + s6 4 本中 3 本 + hook 一致 |
| V2 | ALLOWLIST から Options 欠落 | T1 + 既存 allowlist 挙動 |
| V3 | s6 ebs から transaction 欠落 | s6 behavioral 3 + 構造検査 |
| V4 | s6 regen から backoff 欠落 | s6 behavioral 3 |
| V5 | p3_s4_loop の SOURCE_REL 逸脱 | T3 |
| V6 | _PROTOCOL_CMAKE typo | T4 |
| V7 | EBS 縮小 | T1 + hook + s6 4 本 + T3 |
| V8 | s6 述語の片方向化 | 逆方向 control のみ |
| V9 | sort 軸取り違え (EBS 内) | T3 |

M08 新旧両走の差分: **V3/V4 のみ新テストが唯一の検出者** (V5 は既存 test_p3_s4_loop も
FileNotFoundError で検出する — RA-4 の指摘により当初主張を訂正)。

## 5. 段 6 所見の裁定 (詳細逐語 = reviewA/reviewB/rereview.md)

- must-fix real 採用 → fix 済み closed: RB-1 (ledger closure)、RB-2 (母集団の live 自己参照
  = 縮小死角)、RA-1 (片方向 control)、RA-2 (軸取り違え)、RR-1 (テスト側凍結写しの
  lockstep 死角 → AST 抽出で写し廃止)。再レビュー表 = closed 5 / partial 2 / regressed 0
- **[T-163] 起票 (scope 外 real、A-3/RR-1 の残穴):** `cmd_verify` が `n1_provenance_sha256` /
  `submodule_pin` / `population_sha256` を hash 台帳と再照合しない。freshness は可変 N1 を
  読むため、「N1 更新 + 旧 frozen payload」の stale 組合せを verify が通す。束縛追加は
  凍結実験 (S-2/C4/C5) の検証設計変更 → ユーザー裁定待ち
- **[T-164] 起票 (backlog、RA-3 残余):** fake ls-tree の引数完全 pin と opened の int/bool
  型境界。G05 成果物影響 1 行を書けないため must-fix にしない (DW-S06-C)
- R2 (s1 統一の恒久化): freeze migration (pin 閉包の再発行) が前提で価値低 — 見送り、
  T4 の関係検査で十分。R3: axis-onboarding の二段拡張手順は literal + テスト方式では
  現行のまま有効 (追随編集不要を確認)

## 6. dev-wave 改善候補 (段 8 routing: `DW-O09` へ自動統合済み)

**候補: 定数統一系 wave の出現分類 (live copy / 独立 golden / 凍結 snapshot / 歴史記録) と、
output 外の review ledger (role source pin) の pin 既定対象化。** 根拠 = §1 (未分類の一括
認定が A-1/A-2/A-3 の誤 scope を生み、coder.md の review pin 見逃し (RB-1) も同根)。

当初「予算封鎖 (余裕 13 bytes) のため裁定パッケージ送り」と書いたが、これは F39 (07-26)
時点値の転写で stale だった (F1 型の自己再演)。段 8 で実測 = 23,542/24,000 (T-160 の
DW-O07 削除で原資回復) を確認し、routing 規約 (既存 leaf 節への統合) どおり `DW-O09` へ
追記 + F39 へ再発記録して閉じた。
