# T-2520 — 外側genomeを使う入れ子buildの誤分類を修正

- authority: none
- default_effect: no-state-change
- 正本: D1936項18、F927、`output/insights/2026-09-09/t2213-probe-condition-gate/README.md`。
- 実装anchor: `f5e3315b8fbe6383551cd9c3829518871b564067`。

`_certify_main._build_trace_binary` が外側の `genome` を参照する経路について、
既存の入力依存判定へPythonの自由変数情報を渡した。実装面は
`orchestrator/tests/test_ccbench_spawn_sites.py` の1本だけで、既存の繰延べentryは維持する。
親scopeの値を解析する汎用機構、production gate配線、13macro witnessは追加していない。

## 挙動の実測

| 条件 | 結果 |
|---|---|
| 実certify sink・繰延べあり | deferred 14、proven-unreachable 24 |
| 同entryだけ除去 | 同sinkの14 macroがfailure-reachable。他sinkの分類は不変 |
| macro字面なしの閉包genome | failure-unresolved 1 |
| 内側でgenomeを固定値に束縛 | proven-unreachable 1、failureなし |
| 既存S1/S8b正例 | S1 covered 4 / proven-unreachable 34、S8b covered 38を維持 |

14は既存source inventoryから導かれた分類件数であり、14 macroの実行時到達や意味の証明ではない。
明示macro優先など既存分類器の全般的な完全性は主張しない。

## 独立検証

- plan 1、敵対相談2、Codex author 1、独立レビュー2。全6走accepted、launcher/validator/child rc0。
- 両レビューは対象実sinkと直接回帰についてGO。追加realなし。既存期待値・skip・繰延べ台帳の緩和なしを照合。
- 修正前の専用worktree: 44 passed / 76.26s、計算ノード991679.nqsv、tools/run_tests.py経由。
- 修正後の焦点走: 47 passed / 161.04s、runnerのbounded local・serial、同じrunner経由。
- 自由変数集合を空にするM1は、新集合でKILLED。失敗nodeは実sink回帰とopaque closure回帰のexact2件。
- 同一M1は変更前から存在した44テストの集合ではSURVIVED（失敗0）。新旧とも基準走行成功・一意注入・復元をharnessが確認し、期待結果と完全一致、wrapper rc0。
- 実装commit後provenance: 9631件、新規違反なし、known-violations 56（不可逆53・baseline後3）。
- 統合版 `7544087a3411f8b7b9a210fb2263a132bc5b2c9c` の受入全走は23,071 passed / 68 skipped、3shardsすべてchild rc0、最終receiptはchild-green。tested mainは `7b975a735c12dc7d112d7d8953e2402b4ca0a9e4`。
  受入中にmainが進んだため、その後の文書競合解消を含む版の受入を別走とする。

初回main側の焦点走はrunnerのメモリ上限で未完走となり、再投入は既存orphan holdで子未起動だった。
この2走を成功に数えず、他wave所有のholdを変更せず、専用worktreeの計算ノード走で確認した。
起動時はT-2417 recoveryとT-1851 D2の同検査変更がmainへ統合済みであることを確認し、
稼働T-2397のA-1変更との衝突可能性も継続照合した。

`verbatim.json` はbrief・裁定・各worker最終報告をtextとして収録し、原文のbyte数・SHA-256を併記する。
各textをUTF-8で書き出せば末尾空白を含む元bytesを復元できる。
