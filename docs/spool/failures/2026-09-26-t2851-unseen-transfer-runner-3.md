---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-26
wave: t2851-unseen-transfer-runner
seq: 3
---

## 再発

### F649

- **再発: 2026-09-26** — [T-2851] の転移の実行器で、検証の certified 到達性を誰も検査していなかった。親が段 5・6 の実装子 prompt で「verifier の外部呼び出しは既存 seam で
  fixture 化してよい」と許したため、新設 test は verifier の戻り値を作り置きし、`verify_trace_dir` を `ccbench_root` なしで呼ぶ実装 (証明面が unavailable で
  `Integrity.clean()` が常に偽) のまま、review 2 本と焦点再レビュー 2 巡で指摘されなかった。事前登録した変異 12 件はどれも写像や計数の変異で、この経路を対象にしていなかった。計算ノードでの錨の生死確認 (29210.nqsv) で、serializable・anomaly 0 なのに
  indeterminate になって初めて判明した ({{D:t2851-transfer-runner-contract}} 項 4、`output/insights/2026-09-26/t2851-transfer-runner/README.md` §3)。
  今回の穴は実装子の選択ではなく**親が prompt で検査対象の機構そのものの stub を許した**ことで、`DW-S05-C` の「依存先を stub しない」の例外句が機構の中心に掛かった。
  fix で、実 verifier のまま最小 trace で certified / indeterminate を切り替える正例・負例 test を足した (変異 M13 で検出を確認)。
