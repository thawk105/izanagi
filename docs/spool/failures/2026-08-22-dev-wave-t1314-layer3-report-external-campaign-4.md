---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-22
wave: dev-wave-t1314-layer3-report-external-campaign
seq: 4
---

## 新規

### {{F:t126-mutation-transform-anchor-missed-by-path-grep}}. DW-O09のpath grepがT126独自mutation登録の逐語anchorを見落とした [恒真ゲート] [手順漏れ]

- 事象: 段1のDW-O09監査 (`grep -rln "layer3_report" --include=*.py .`) は
  `orchestrator/tests/test_t126_pegasus_tools.py` を hit として列挙していたが、その中身が
  `T126_MUTATION_REGISTRY`/`_T126_MUTATION_TRANSFORMS` という、layer3_report.py の**逐語コード
  テキスト**を `old_anchor` として保持する独立したmutation登録インフラであることまでは
  深掘りしなかった。段5の実装 (`_reject_qualification_ancestry(campaign_dir,
  output_root.resolve().parent)` を新helper呼び出しへ書き換え) がこの逐語anchor
  (`_T126_MUTATION_TRANSFORMS["M2a"]`) を壊し、段9の正式受入全走で初めて
  `test_t126_pegasus_tools.py::test_fr3_mutation_node_registry_is_exact_and_complete`
  のattributable-redとして発覚した。段6の敵対レビュー2本・焦点再レビュー1本、変異matrix
  MUT-1〜7、self-check再走6回のいずれも、T126の別mutation登録という**別subsystemの
  逐語pin**までは検出範囲に入っていなかった。
- 根本原因: `DW-O09` (`docs/dev-wave/operations.md`) は「path検索が見つけるのはpathを
  keyにするpinだけである。review ledgerのようにrole名をkeyに張るpinはkey側でも検索し、
  pathのhit0件をpinなしと結論しない（F30）」と明記済みだが、本waveでは path のhit が
  0件ではなく複数件あったにもかかわらず、各hitの**中身** (それが単なる import/文字列参照か、
  逐語コードテキストを保持するmutation registryかどうか) まで1件ずつ判別しなかった。
  F30は「hit 0件を鵜呑みにしない」という片側だけを扱っており、「hitが複数件あるとき
  各hitの性質を判別する」という反対側の落とし穴は既存の型に含まれていなかった。
- 恒久対応: `orchestrator/tests/test_t126_pegasus_tools.py` の
  `_T126_MUTATION_TRANSFORMS["M2a"]` の `old_anchor` を新しい実装 (3行の関数呼び出し) へ
  差し替えて修正した (本waveの段9追加fix、Codex `role=author`)。DW-O09自体への
  「複数hitでも各hitの性質を判別する」旨の追記は、本waveでは
  `docs/dev-wave/operations.md` の予算 (L1.5 unique footprint) に収まる保証がなく、
  {{F:consult-lane-job-id-collision}}・{{F:mutation-attempt-out-pairing}}と同じく
  ユーザー裁定へ委ねる (docs側の追記は未実施)。
- 再発検知: 未整備。`T126_MUTATION_REGISTRY`のようなkey付きmutation anchorを持つ
  registryファイルを機械的に列挙し、DW-O09監査の出力へ「この pathはmutation anchor
  registryである可能性がある」という注記を自動で付ける仕組みが候補になりうるが、
  本waveのscope外。
