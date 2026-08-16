---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t1250-decider-version-generation
seq: 2
---

## 新規

### {{F:cli-double-import-collapses-diagnostics}}. 判定器を `-m` で走らせると全条件が同じ理由へ潰れ、その出力を brief の一次資料にした [計測汚染]

- 事象: 段 8c 事前登録の段 1 brief が、不変条件として「C01〜C12 は `evaluator-exception`」と
  書いた。実際の vector は条件ごとに 4 種の理由コードへ分かれており、`evaluator-exception` は
  1 件も出ていない。誤りは段 3 の敵対相談が指摘し、親が独立に再現して機序まで特定した。
- 根本原因: `python3 -m orchestrator.campaign.s8c_preregistration check` は判定器 module を
  `__main__` としても読み込む。評価器は `from . import s8c_preregistration as core` で
  別の module object を掴むため、返る `core.PredicateResult` が `__main__` 側の
  `PredicateResult` と `isinstance` で一致しない。`_normalize_predicate_results` が
  `predicate-result-type` を上げ、`_default_registry_results` の包括 except が全 12 条件を
  `evaluator-exception` へ倒す。CLI は正常に走って rc も返すため、壊れていることが出力から
  見えない。安全側 (未発効) には倒れるが、規律 3 が要求する構造化した不充足理由が失われる。
- 恒久対応: memory `judge-diagnostics-via-library-not-cli` — 判定器の診断 vector は
  CLI ではなく library 経路 (`activation_report_at`) で取る。CLI 側の欠陥そのものは
  {{T:s8c-cli-diagnostics-collapse}} で直す。
- 再発検知: 同一値が全要素へ並ぶ診断出力は、別経路で 1 度裏を取るまで一次資料にしない。
  本件では library 経路が 4 種の理由へ分かれることで即座に判別できた。
