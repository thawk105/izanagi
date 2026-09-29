## 総括

指定の 2 file に、pair を系列 iteration ごとの計測 campaign で実行する変更と、別 process で直列起動する焦点 test T1〜T3 を実装しました。**実装済み・未実走**です。commit・git add はしていません。

## 実装前の現行挙動

現行の pair は候補と stock に系列 cfg を使い、Pegasus の claim も系列 campaign ID に結び付きます。同じ out_root で 2 本目を起動すると既存 claim により `ClaimError` となり、stock の skip 判定には到達しません。

## 変更内容 (file:line)

- [p3_s4_loop_policy.py:216](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2871-author/orchestrator/campaign/p3_s4_loop_policy.py:216): 系列履歴に `measurement_campaign_id` を追加。非 pair の行は `null` です。
- [p3_s4_loop_policy.py:434](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2871-author/orchestrator/campaign/p3_s4_loop_policy.py:434): counter を進めた直後に系列 state を保存。候補評価と admitted view は計測 cfg/layout を使い、履歴と digest は系列 layout に保存します。
- [p3_s4_loop_policy.py:652](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2871-author/orchestrator/campaign/p3_s4_loop_policy.py:652): pair 分岐で系列 state を一度読み、次番号から計測 cfg/layout を作成。同じ cfg/layout と authorization session を候補・stock に渡し、candidate stdout に計測 ID を追加しました。`run_campaign` の呼出しは 2 本のままです。

## 焦点 test (追加・変更した test 名と各 assert の意図、変更した既存 assert の列挙)

- [test_p3_s4_loop_policy.py:811](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2871-author/orchestrator/tests/test_p3_s4_loop_policy.py:811) T1: 2 process の別 claim、各計測 WAL の候補・stock、両 stock の `certified-stock`、系列 state・履歴 2 行、2 本目の admitted view 由来の digest を確認します。
- [test_p3_s4_loop_policy.py:856](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2871-author/orchestrator/tests/test_p3_s4_loop_policy.py:856) T2: claim 取得後の build 中に強制終了し、次番号の claim と候補・stock 評価、系列履歴の欠番を確認します。
- [test_p3_s4_loop_policy.py:883](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2871-author/orchestrator/tests/test_p3_s4_loop_policy.py:883) T3: state を直前へ戻した再起動が実 `ClaimError` となり、計測 attempt が増えないことを確認します。
- 既存 assert の変更: `test_drive_exception_records_history` の履歴 key 集合に新 field を追加。`test_pair_orders_candidate_then_stock_in_one_session` に系列・計測の cfg/layout、共有 state と stdout ID の確認を追加。`test_pair_stock_failure_returns_one_after_candidate` の candidate stdout 期待値に計測 ID を追加しました。

## 実走した検査と結果 (未実走はそう書く)

`python3 -m py_compile` と `git diff --check` は成功しました。pytest、`tools/run_tests.py`、Pegasus 実走は**未実走**です。焦点 test を緑とは報告しません。

## 所有外 caller・共有 fixture・consumer test への波及 (静的列挙)

`test_campaign.py:5520,5603` の `run_campaign` 2 本 pin は維持。`test_official_perf_closure.py:62` の所属も維持。`tests/README.md` は file 単位の pytest 専用一覧で、今回の test 追加による変更は不要です。共有の claim・reservation・authorization session 実装と fixture file は編集していません。

## 変異の事前登録 (裁定 §5 の M1〜M5) に対する見込み (どの assert が赤になるか、単一理由性の懸念)

| 変異 | 赤になる見込み |
|---|---|
| M1 | T1 の 2 本目成功・claim 2 file |
| M2 | T2 の次番号 claim・2 本目成功 |
| M3 | T1 の stock `certified-stock` |
| M4 | T1 の**1 本目直後**の系列 state・履歴 assert |
| M5 | T1 の digest と 2 本目 admitted view の照合 |

M4 は 1 本目直後にも確認するため、後続の claim 衝突と理由を分けられます。M5 は系列 dir の admitted view 読込み時に先に失敗する可能性があり、単一理由性は焦点走で確認が必要です。

## 未解決・判断が要る点

判断を要する設計事項はありません。親による焦点 test 実走と変異の単一理由性確認が残っています。