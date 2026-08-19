# D230 統一述語の実装 — [T-619] 実装 wave (2026-08-20)

依頼: 「[T-619] D230 の統一述語を既定監査へ導入する。2026-08-07 /rulings で5点裁定済み
(entry 299)。着手前に T-614/T-618 がこの一連の実装をどう扱ったかを確認し、同じ整理形を踏襲すること」

計測 checkout = `.claude/worktrees/dev-wave-t619-provenance-unified-predicate`、起点
`f5677a66a91474478b65fe178ba9ed2eeee1e6cc`。実行環境は Pegasus。統合 commit `a05d107a`、
受入 tested_tip `3b31e25b`。

## 結論

D230 (`docs/decisions.md:10798`) の恒久形と、2026-08-07 /rulings 第5回 (entry 299) の5点裁定を
実装した。既定監査 (`--range`/`--message-file` 無し) の選択集合と scope/implementation/CAB 3層の
epoch 適用述語を、統一述語

```text
applies_R(C) := C∈Anc(H) ∧ ((∃p∈seeds(R): p∈Anc(C)) ∨ (¬∃p∈seeds(R): C∈Anc(p)))
```

へ揃えた。HEAD 一度解決+終了時 drift rc=2、shallow/graft/replace/非一意 policy add の rc=2 を
新規実装し、既知違反台帳へ `333605d680ec` を追加、`docs/ai-provenance.md` の非遡及規定4箇所を
1文へ統合して family を net -168 bytes 縮約した。明示 `--range`/`--message-file` は無改修。

変異 matrix: baseline PASSED・12/12 KILLED・SURVIVED 0・MISMATCH 0。受入全走:
verdict=non-attributable-only (無関係な既知flake1件のみ)。

## 実測で確認した前提 (段1 brief、F1 discipline)

設計時 (2026-08-07, `bb824d8b`) の実測前提を、実装直前の HEAD (`f5677a66`, 12日後・
数百 commit 後) で出荷済み関数を import する使い捨てスクリプトを使い再実測した。

| 層 | epoch commit | ancestry-path | plain | gap | 新規 finding |
|---|---|---:|---:|---:|---:|
| base | `50c1ef4e` | 4349 | 4349 | 0 | 0 |
| scope | `2f0245c1` | 4227 | 4227 | 0 | 0 |
| implementation | `8c6d3f3b` | 3886 | 3888 | 2 | 1 |
| CAB | `9b26b3bd` | 3830 | 3854 | 24 | 0 |

gap は設計時と完全に同一の26 commit (実装面2件+CAB24件)。新規 finding は `333605d680ec` の
missing-codex-author 1件のみで、他25件は0件。26件はいずれも当時の台帳 (42 entries) に未登録
だった。`AI-Agent-Correction:` trailer を持つ commit は全履歴で `6d7141dc` の1件のみ (forward
correction の受理集合拡大懸念は base 層 gap=0 により今日は no-op)。byte 予算は
family 8977B/9000B (slack 23B) で、−168B 案は安全に収まると確認した。

## 段2 codex プランの成果 (`verbatim/s2-plan.md`)

`authoritative: bool` フラグを `_commit_range`/`_audit_history`/`_normal_commit_audit`/
`_build_ancestry`/`_Ancestry.has_cab_policy`/`_ledger_policy_is_visible` へ一貫して配線する
file:line 設計。brief 自身の誤り (`_policy_commit()` の非一意検査を `-S` pickaxe と誤記していたが
実コードは `--diff-filter=A`) を自己修正した。

## 段3 敵対相談2レンズの成果 (`verbatim/s3-lensA.md`, `verbatim/s3-lensB.md`)

計8所見、全件 real・採用 (裁定は `s4-adjudication.md`)。主な採用点:

- **レンズA (正しさ境界)**: `_ledger_policy_is_visible` への `authoritative` 配線が呼び出し箇所で
  明示されていない (blocker)。`ancestry=None, authoritative=True` の組み合わせに oracle 側の対応が
  無い。CAB seed 空集合の意味論が数式と実装で食い違いうる。
- **レンズB (整合性・消費者・回帰)**: 明示 `--range` 経路で `_scope_policy_commit(None)` のように
  明示 `None` を渡すと既存 zero-arg monkeypatch が `TypeError` になる (本物の regression)。
  DW-M01単一理由性のため side-branch fixture を scope-only/implementation-only に分割すべき。
  台帳 ruling 文字列は self-locating 記法へ揃えるべき。D230 は書き換えず新 D を追記すべき。

## 段4 親裁定 (`s4-adjudication.md`)

8所見全て採用。gate 新設の禁止署名と通る正例を明記し、DW-M01 変異事前登録12項目を確定した。
`ancestry=None, authoritative=True` は fail-fast で拒否 (oracle 二重実装は規律5により追加しない)。

## 段5 実装 (`verbatim/s5-implementation-report.md`)

`tools/check_ai_provenance.py` (+209/-なし相当の diff) と
`orchestrator/tests/test_check_ai_provenance.py` (+424 行) を Codex `role=author` が実装。
親が独立に実走し 317 passed / 0 failed を確認 (計算ノード)。この repo に対する既定監査の実走で
4350 commit・known-violations=43・新規違反なし (rc=0) を確認 — `333605d680ec` が統一述語で
正しく検出され、台帳へ吸収されることを実地で確認した。

## 段6 敵対レビュー2本 + fix (`verbatim/s6-review1.md`, `verbatim/s6-review2.md`,
`verbatim/s6-fix-report.md`)

blocker/must-fix 0件、nit 5件。2件を fix (docstring の陳腐化、HEAD drift テストの検出力不足)、
3件は見送り (裁定文書の byte 数記載ミスは本 README で訂正: 実測 family は8869B、裁定時点の見積り
8809B から `PR-A02` の実文言確定で微増。追加境界テストは不要と判断。`docs/ai-provenance.md` の
別1箇所の文言統一は今回の裁定範囲外として backlog)。fix 後、親が独立に再実走し 317 passed を再確認。

## 変異 matrix (`mutation-spec.json`, `mutation-result.json`)

12項目を実装後にコードで単一理由性を確認してから本登録した。probe走 (全件 SURVIVED 期待) で
実際の kill node を実測し、11/12 は事前予測どおり、M10 (台帳 entry 削除) のみ予測より1件多い
node で kill された (台帳 entry 削除が `test_t619_authoritative_ledger_visibility_wiring_is_explicit`
の前提も壊すため、論理的に妥当)。本登録は baseline PASSED・12/12 KILLED・SURVIVED 0・MISMATCH 0。

## 受入全走

1回目は他 wave の land (`301d62d13a0b`) と競合し `rc=70
reason=receipt-waiter-sha256-mismatch classification=restart-required` で失敗 (コード起因ではない、
残骸なし、単純再投入で解消)。2回目: `verdict=non-attributable-only`
(`tested_tip=3b31e25b`, `tested_main=7d8b8a87`, red_nodeids は
`test_spool_fold.py::test_cli_base_digest_real_corpus_resolves_active_and_rejects_completed` の
1件のみで非帰属checker (`checker_rc=0`) が無関係と確認済み)。

## 一次資料

- `s4-adjudication.md` — 段4 裁定表、gate 新設の禁止署名、DW-M01 変異事前登録12項目。
- `verbatim/` — 段1 brief、段2 プラン、段3 レンズA/B、段5 実装報告、段6 レビュー2本+fix報告。
- `mutation-spec.json` / `mutation-result.json` — 変異事前登録と本走結果の逐語。
- 先行設計 wave: `output/insights/2026-08-07_t619-provenance-range-permanent-design/`
  (統一述語の導出、却下した代案の理由は再訪せず前提として使用した)。
