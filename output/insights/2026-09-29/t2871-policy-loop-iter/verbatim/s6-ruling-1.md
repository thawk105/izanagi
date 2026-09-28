# [T-2871] 段 6 裁定 1 (親) — レビュー A (codex/review-a.md)・B (codex/review-b.md) の採否

対象: wave commit 14beca40c (実装) + b6c824675 (runbook)、base 51f896352。焦点走 1 回目 (32588.nqsv) は queue-wait-timeout で child 未起動 (rc=16、テストの赤ではない)。2 回目 (32592.nqsv、D612 の待ち上書き 3600/600) を実行中。

| # | 所見 | 出所 | 裁定 | 処置 |
|---|---|---|---|---|
| R1 | T1 の digest 期待値を stock 実行後の admitted view から作っていて、実装 (候補の後・stock の前に digest を作る) と時点がずれる | B must-fix | real・採用 | fix-1 (Codex) |
| R2 | `stopped-before` の stdout に計測しなかった番号の `measurement_campaign_id` が載る | A should・B should | real・採用 | fix-1 (Codex) |
| R3 | runbook「系列 dir には 3 file だけ」は誤り (login の record-reject は系列 WAL に書く) | B should | real・採用 | 親 (docs) |
| R4 | runbook の欠番の扱いが裁定より強い | B nit | real・採用 | 親 (docs)「完了した pair の評価結果として数えない」へ |
| R5 | runbook §1(g) の「campaign dir」を「系列 dir」に揃える | B 簡略化 | 採用 | 親 (docs) |
| R6 | T1〜T3 が compiler 不在で skip する | A should | 不採用 (scope 外) | 同じ file の既存 test 9 箇所がすべて同じ skip 慣習。T1〜T3 だけ fail にすると慣習が割れ、要求外の検査強化になる。代わりに親が焦点走・受入の skip 内訳 (`-rs`) を実測し、T1〜T3 が実行されたことを記録する |
| R7 | M5 は digest 比較より前に admitted view の読込み (系列 dir に lock・WAL が無い) で赤になる | A should | real・変異登録で対処 | M5 の期待赤を「pair が admitted view で例外 → T1〜T3 の子 rc≠0」に再照準し、probe で失敗 node を集めて登録する (DW-M01)。赤の理由は 1 つ (admitted view の読み先) |
| R8 | test の簡略化 (claim 集合一致だけで足りる、variant 確認の重複、T3 を T1 に統合、子 process の import を軽く) | B 簡略化 | 不採用 | 統合は変異の単一理由性を崩す。import の軽量化は fixture の重複移設を伴う。所要は焦点走の実測で判断し、全体 5 分の上限を脅かす場合だけ別途扱う |

## fix-1 の仕様 (Codex、所有 = driver と焦点 test の 2 file)

- R1: T1 の digest 検査から「stock 実行後の admitted view で作った digest との全文一致」を外す。代わりに、系列 dir の digest が (a) 2 本目の候補の証跡を含み、(b) 2 本目の job の stock の証跡を含まないことを確かめる。(b) が恒真にならないよう、同じ判定語が stock 実行後の admitted view から作った digest には**含まれる**ことも同じ test で確かめる。
- R2: `main` の pair 分岐の `stopped-before` (candidate の `ran is False`) では `measurement_campaign_id` を付けない。これを確かめる assert を既存の該当 test (無ければ最小の新 test) に足す。
- 受理・拒否の含意: R1 は test の期待値だけを直し、driver の受理集合を変えない。通る正例 = 候補の後・stock の前に digest を書く現行実装。R2 は stdout の field を 1 つ減らすだけで、claim・計測・履歴を変えない。通る正例 = 予算停止した pair の stdout が `stopped-before` だけを示す。
