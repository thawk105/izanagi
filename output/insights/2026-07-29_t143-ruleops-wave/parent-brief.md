# T-143 RuleOps — 親 brief

- scope: tracked な `orchestrator/tests/test_*.py` と `output/insights/` の RuleOps を最小実装する
- 確定裁定: RuleOps 導入は 2026-07-27 のユーザー裁定 (4) で承認済み
- 不変条件: correctness gate、受理集合、certified 選択、proof chain の bytes / 判定を変えない
- 不変条件: 年齢・size・参照数だけを削除可の根拠にせず、安全意味論の判断を自動化しない
- 不変条件: campaign WAL / lock、freeze、正式 report、CCBench submodule は inventory 対象外
- 成果物: 決定的な read-only inventory / 候補検査 CLI、機械可読な候補台帳、運用文書、境界テスト
- 成果物影響: 未実装のままだと守りとレポートが単調増加し、高価値証拠の発見性と反復コストが悪化する
- `(P1)` 親の provisional 裁定・攻撃対象: CLI は候補提示と fail-closed 検査だけで削除を実行しない
- `(P2)` 親の provisional 裁定・攻撃対象: test 候補には代替防壁・発火実績の意味検索・変異証拠、
  insight 候補には参照閉包・authority / artifact 区分を要求する
- `(P3)` 親の provisional 裁定・攻撃対象: 既存 348 件の全登録を必須化せず、動的 inventory と
  明示候補 ledger の二層にして通常追加の負担を増やさない
- 今 wave では既存 test / insight を削除・移動せず、具体的 retirement は個別ユーザー裁定へ残す
- 新しい検査の純増検出力は、候補 schema 欠落・対象逸脱・参照残存・証拠欠落を拒否すること
- 受入は本 worktree の `tools/run_tests.py` 全走。性能値としては扱わず、計測環境は使用しない
- 分割: read-only plan 1、敵対相談 2 レンズ、author 実装 1、実装後 review 2 レンズを隔離 Codex で行う

## 前提実測

- tracked test: 97 files / 2,896,319 bytes
- tracked insight: 251 files / 7,922,057 bytes
- Git の最終変更、file size、repo 内の literal path 参照は既存 checkout から取得可能
- 既存被覆: 未 stage 削除検出、pytest 実行漏れ検出、dev-wave L2 節の限定削除 gate
- 未実装: 横断 inventory、候補台帳、retirement 証拠の機械検査
