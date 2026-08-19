---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-19
wave: dev-wave-t1352-b-verdict-floor-removal
seq: 2
---

## {{D:s8b-verdict-condition3-removal-is-intended-admission-expansion}}. 最終判定層の条件3・scale gate 撤去は意図的な受理拡大であり、[T-1336]/8b §10.1 が明示承認している

**決定:** `orchestrator/campaign/s8b_verdict.py` の `judge_combined` から旧条件3
(oracle per-pair floor 超過判定) と scale gate を撤去し、結論を条件1 (on/off 予測差の
存在量化) ∧ 条件2 (swapped 追従の全称量化) の2条件連言へ縮退させる。この変更は
「floor を判定基盤から外す」という設計変更であって、受理集合を変えない中立的な整理では
ない — 具体的な反例 (条件1 が成立するが旧条件3 は floor 未超過だった holdout の組み合わせで、
旧結論 REFUTED/INDETERMINATE が新結論では HOLDS になる) が存在する。これは規律2 が禁じる
無許可の検証弱体化ではなく、`docs/phase3-8b-descriptor-design.md` §10.1/§10.3 と D510
(2026-08-18) が between-run floor・scale gate・oracle unique-best 確定・両構成
eligibility 判定の4保証の撤去を名指しで明示承認した範囲内の実装である。

**理由:**
- §10.6 が「最終判定層の現用実装は依然として旧条件3とscale gateを使う。本節はその実装を
  変更しない。実装の追随は別waveが行う」と明記しており、本 wave が名指しされた「追随」に
  当たる。
- production consumer はゼロ (`judge_combined` を外部 import するのは
  `test_s8b_verdict.py` のみ、CLI `main` は in-module entrypoint) であり、実際の
  certified selection 受理集合への実害はない。

**却下した選択肢:**
- 「受理を広げる操作ではない」という当初の brief の理解のまま実装する — 段6 敵対レビューが
  具体的な反例で反証した。裁定済みの意図的な設計変更として正確に記述する方を採った。

## {{D:s8b-verdict-schema-v2-retained}}. `COMBINED_VERDICT_SCHEMA` は v2 のまま維持し v3 bump を撤回する

**決定:** `s8b_oracle_artifacts.py` の `COMBINED_VERDICT_SCHEMA` を `"8b-combined-verdict/v2"`
のまま維持する。段4裁定では出力 shape 変更 (floor/scale フィールド消滅) に合わせて v3 へ
bump する方向を一度採用したが、これを撤回する。

**理由:**
- `s8b_oracle_artifacts.py` 自体の source bytes の sha256 が
  `test_s8b_oracle_manifest.py::PIN_GATE_SPEC_RAW` (generator_versions.artifacts.sha256) に
  literal pin されていることを、bump 判断時 (段4) には見落としていた。bump した状態で受入を
  投入したところ、この pin との不一致で無関係な2テストが赤になった。
- schema version の実体との乖離は production consumer ゼロのため実害がなく、bytes pin を
  壊してまで解消する価値がない。

**却下した選択肢:**
- pin (`PIN_GATE_SPEC_RAW` 内の sha256 literal) を新しい bytes へ更新する — このテストが
  「production serializer から独立した golden」として意図的に固定した値であり、意味を
  理解しないまま書き換えるのは危険。schema 変更自体を撤回する方が安全側。
