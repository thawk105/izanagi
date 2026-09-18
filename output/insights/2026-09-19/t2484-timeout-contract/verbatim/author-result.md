## 総括

**実装済み・テスト未実走です。** 所有2ファイルのみ変更しました。追加198行・削除4行で規模上限内です。docs・stage・commit・子起動・追加レポート作成は行っていません。

- `tools/mutation_harness.py`：helper と3 callerへ `max(spec, P+Q+W+G+A+C)` を配線。P=180秒、既定予算5130秒。stderrへ理由・区間内訳・実効値を出力します。
- collection は既定W、baseline・mutation は既存W overrideを使用。dispatch の短いhang監視を撤去し、localの短いhang値を維持しました。
- 内側期限・回収・hold・復元・resume処理は変更していません。

**受理・拒否は維持しています。** collection gateには元spec値を渡します。Q=1800/G=600では2399を拒否、2400を受理して実待機6330秒。overrideなしの小specは従来どおり受理します。不正overrideに新たな拒否条件を追加していません。

**追加テストは33ケースです。**

- `test_t2484_timeout_budget_arithmetic`：M1–M7/M13/M14の算術。
- `test_t2484_callers_reach_communicate_with_effective_timeout`：M8–M15のcaller配線・gate境界・local値。
- `test_t2484_timeout_diagnostic_is_nonrejecting`：診断専用。kill判定には使いません。
- `test_t2484_inband_rc16_preserves_receipt_hold_contract`：rc16でも残存可能ならholdを維持。

helper・callerはstubせず、最終プロセスsinkを捕捉します。P0はmax引数交換の等価性を維持しています。**変異のKILLED/SURVIVED実測は未実施**です。

検証結果：

- `check_codex_agents.py`、`check_docs.py`：通過。
- 変更2ファイルのAST解析、`git diff --check`：通過。
- `tools/run_tests.py orchestrator/tests/test_mutation_harness.py -k t2484 -n 0 -q`：`qstat -Q preflight rc=1` によりrc=16、`child_started=false`。緑と報告できるpytest nodeidはありません。

所有外への影響は、`mutation_worktree.py`、`mutation_fanout.py`／`mutation_fanout_contract.py`のharness呼出し・identity束縛です。共有fixture・consumer期待値は変更していません。関連meta-testとしてT2337 parser同値検査、flaky holdの登録node検査、acceptance duration ledgerの実collection網羅率検査を特定しましたが、未実走です。

親では上記meta-testと、既存local hang・dispatch hold／残存・復元・resume・失敗node完全一致の回帰、および固定anchorでM1–M15/P0を実走してください。docs検査の赤は観測しておらず、未着地DW-M06/M07以外の赤を期待赤として扱っていません。