---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: lively-juggling-ripple
seq: 2
---

## {{D:t1434-4-wave-ab-narrow}}. T-1434(4) codex_reasoning_ab.py model軸refactorはWave A+Bへ narrow し、Wave C/Dは後続waveへ送る

**決定:** `tools/codex_reasoning_ab.py`をmodel軸拡張向けに横断的refactorする段5実装scopeを、
段2プランが提案したWave A (manifest/schema/provenance層) → B (argv/launch/identity層) →
C (supervise_pair/collect_run) → D (schedule validation/adjudication/aggregate/replay/output)
の4分割のうち、A+Bだけに narrow する。C/Dは実装しない。

**理由:**
- 段3敵対相談レンズB (scope境界) が独立に「17領域・13000行超は1waveに大きすぎる、Wave A+Bへ絞れ」
  と提案した (規律5 段階導入/盛らない)。
- 段3敵対相談レンズA (正しさ境界) が独立に「Wave Cの`supervise_pair`はWave D所有の
  `_validate_schedule`に直接依存し、A→B→C→Dの逐次順ではCの実装・テストが成立しない」という
  構造的な依存誤りを発見した。C/Dを本waveから外すことでこの依存問題自体が解消する。
- レンズAのblocker所見のうち2件 (model-axis aggregate/decision schema未定義、reveal後
  private binding比較先が不在) はWave D領域固有であり、Wave D自体を先送りすれば
  「次wave着手時に設計する」という形で未閉包のまま残さずに済む。
- Wave A+Bだけでも、`requested_model`をroutingauthorityとしてargv・identity・receiptへ通す
  配線と、task_idキー方式のmanifestへの一般化は完成し、既存POS/NEG凍結benchmarkの動作を
  壊さない独立した増分になる (段6敵対レビューで292 passed・0 failed・変異9/9 KILLEDを実測)。

**却下した選択肢:**
- Wave A→B→C→Dを1waveで一括実装する — レンズBの規模超過懸念とレンズAの依存関係の誤りが
  未解決のまま残り、規律5に抵触する。
- Wave Aだけに留める (Bも先送り) — argv/launch/identityのmodel対応はAの`TASK_MANIFEST`と
  疎結合であり、Bまでは1waveで完結可能と段4裁定時点で判断した (実際に段6で292 passed・
  変異9/9 KILLEDを実測し裏付けられた)。
- Wave Dの`_validate_schedule`本体だけを先に配線する — 配線には Wave C の pair 検証拡張
  (stage/task_type/oracle_kind/oracle_sha256/price_snapshot_sha256) が前提になり、
  Cを飛ばしてDだけを触ると新たな未閉包を生む。

## {{D:t1434-4-benchmark-task-id-naming}}. `codex_reasoning_ab.py`のtask一般化フィールド名は`task_id`でなく`benchmark_task_id`にする

**決定:** T-181/T-189のtask manifest一般化で新設するフィールド名を、既存の
`orchestrator/dev_waves/checker.py`・`orchestrator/tests/test_spool_fold.py`等が使う
「dev-wave task-run追跡ID」という別概念の`task_id`と区別するため、`benchmark_task_id`にする。

**理由:**
- D75 (decisions.md:3007) の恒久教訓「設計docのgate記述はその入力が成果物のどのfieldに
  実在するかを書く前に実物で確認する」に従い実測したところ、`grep -rn "\btask_id\b"
  orchestrator/ tools/`で既存の別概念衝突が実在すると判明した。
- 両者は別ファイル・別schemaで実行時の混線は無いが、同じdev-wave生態系内で同名の別概念が
  併存すると可読性上の曖昧さが生じる。

**却下した選択肢:**
- `task_id`のまま実装する — D75の教訓に反する。将来この2概念が同じ文書・ログに並んだときの
  混同リスクを残す。
