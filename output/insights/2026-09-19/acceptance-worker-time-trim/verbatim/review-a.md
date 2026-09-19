## 判定

**NO-GO。** 新 U1 正例の既知の失敗に加え、custom basetemp で session 外の memo を再利用する経路があります。
既存 test の本文・decorator・parametrize の不変性は確認しましたが、変異 kill 集合の同一性は未証明です。
本レビューは静的検査のみです。焦点走の結果は提供資料を参照しました。

## 所見

以下、F＝`orchestrator/tests/test_s8b_ratified_freeze.py`、R＝`orchestrator/tests/test_run_tests_preflight.py`、RT＝`tools/run_tests.py`。

1. **must-fix — F:1387、1427：新正例が multi-thread worker で失敗する。**

   **失敗集合への影響：** 無変異でも `test_emitter_memo_copy_matches_fresh_build` が追加の失敗 node になります。

   現物にも `@in_sealed_fixture_process` がありません。最初の fresh 構築が `s8b_expected_materialization.py:1420–1421` の OS thread 数検査で拒否され、memo の比較まで到達しません。提供された `focus1-summary.md` の失敗理由と一致します。

   既存の F:1700 のように、正例全体を fork 子へ入れる修正が必要です。

2. **must-fix — F:1003–1009、1014–1017：名前による祖先探索は session 境界を保証しない。**

   **失敗集合への影響：** 同じ worktree で構築側変異を入れて再実行しても、前走の正常 memo を拾うと M3 の既存 consumer が失敗せず、kill 集合が縮み得ます。

   具体例は、存在する `/tmp/pytest-of-u/pytest-7` の下で、別々の pytest 起動に `--basetemp=/tmp/pytest-of-u/pytest-7/run-a`、続いて `run-b` を指定する場合です。両方とも探索結果は外側の `pytest-7/izanagi-emitter-memo`。各 basetemp の掃除ではこの memo は消えません。key に session ID・production 内容は含まれません。

   非標準配置は常に「memo なし」になる、という author 報告はこの場合成立しません。実際の session basetemp を明示的に渡すか、確証のない配置では迂回する必要があります。通常の一意な worktree を毎変異に作る matrix は root key によってこの経路を避けられますが、実装自体の session 分離とは別です。

3. **must-fix — F:1427–1437、650–674：新 U1 正例が実 repo を複数回直接読む。**

   **観測への影響：** fresh 構築と seed／再構築の間に実 tracked 入力が更新されると、異なる入力から作った HEAD・tracked bytes を「同一入力」として比較し、新 node が失敗します。

   `_prepare_emitter_base` は `_REAL_V1`、selector source/schema/role/parser を実 repo から読みます。少なくとも freeze JSON、selector Python、role Markdown が tracked であることを確認しました。新正例は fresh・seed・marker 削除後の再構築でこれを繰り返します。

   新 node は real-repo 登録簿にありません。`conftest.py:2285–2303` のロックは登録 access に依存するため、この読取りを保護しません。逐語資料の「新 test の実 root 読取りは shared base 構築に閉じ込める」という条件にも未適合です。

   単に登録を足すだけでは繰返し読取りの条件は満たせません。実入力を共有取得し、fresh／memo 比較はその同じ入力から構築する設計が必要です。なお、現行 serialization test は任意の直接 `read_bytes()` を検出するものではなく、未登録だから必ず赤になるとは言えません。

4. **nit — R:1403–1460：四象限全除外の根拠は過度に保守的。**

   local 3 枝は、採用済み 8 関数と同様に安全に小 repo を使えます。さらに、この test の dispatch 枝も preflight 3 本は既存 stub、dispatcher は `Mock(return_value=7)` です。

   RT:1536–1567 では整数結果に `child_started=True` がないため、RT:1616–1619 の記録開始にも入りません。実 `_default_dispatch` の `_REPO` 利用（RT:1322）には到達しません。したがって、現物では四象限全体への fixture 適用も可能と判断します。現状の除外は正しさの不具合ではなく、削減機会の残置です。

## author 報告の裏取り表

| 主張・確認面 | 現物による結果 |
|---|---|
| F/V の既存168 test 本文・decorator 不変 | **確認。** HEAD と現物の AST 比較で F 63→64、V 105→105。既存本文・引数・decorator に差なし |
| R の既存 test 不変、8関数への引数追加のみ | **確認。** 113→114。本文・decorator 不変、指定8関数の引数だけ変更。7 flags を含め14 node 相当 |
| helper 不変 | **確認。** F の既存 helper 変更は `build_production_emitter_g1` のみ。V の既存 helper は全て AST 不変 |
| caller 列挙 | **確認。** oracle driver/report/manifest、verdict、t080 migration の直接 caller を検索で確認。V の `_build_launch_repo` 呼出し元70関数、baseline 8関数も AST で一致 |
| U1 `DIRECT_CALL_PASS` | **独立裏取り不能。** 提供された差分・報告には実行ログがない。小 repo の直接検証と、本 builder の成功は別。後者の新正例は焦点走で失敗 |
| U3/R の直接検証未実行 | 報告は未実行と明記。焦点走資料では新正例は成功。静的にも RT:2201 の実 fingerprint と5 commands を通り、新たな stub はない |
| 8関数では `_REPO` が fingerprint 以外に影響しない | **確認。** scope は既存 mock。実 `Popen(cwd=_REPO)`（RT:2016）へ進まず、parent preflight 前に return／例外。RecordingSession は import 時 root を保持するが、記録開始に到達しない |
| 非標準 basetemp は迂回 | **条件付き。** 一致する祖先がなければ迂回。一致する外側祖先があれば所見2 |
| nodeid・parametrize・group・hold・登録簿不変 | 差分は F/R のみで既存定義は不変。新 test 各1本。ただし新 U1 の実 repo 読取りは所見3 |
| 新2本の real-repo reader 判定 | U1 は **該当**。U3/R は tmp repo のみを fingerprint し、実 repo tracked file の走査には該当しない |

builder 全引数の分類は次のとおりです。

| 分類 | 引数 | 確認 |
|---|---|---|
| campaign 前に効き、key に含む | `now`、`cert_at_generation`、`perf_available`、`compiler_input_rel` | F:1012–1017、1139–1178 |
| key に含み、真なら迂回 | `selector_valid_cell`、`selector_payload_hit` | F:1190–1195 |
| 配置／迂回 | `tmp_path`、`receipt_root` | root を決定。receipt は迂回 |
| campaign 後に適用 | `mutate`、`mutate_g1`、`extra_closure`、`journal_manifest_before_g`、`executable_role`、`generation_strings_escaped`、`result_schema`、`mutate_attempt_registry` | key 不要。schema の入力拒否は memo 前に維持 |
| 前段へ渡すが前段で未使用 | `selector_extra_files` | F:643–692 では参照せず、F:1202–1205 で初めて適用 |

その他の境界確認：

- **JSON 復元：** `v1` は元から JSON、`base` と `checkpoint["C"]` は文字列です。raw bytes は hex 復元。後段で作る topology の tuple は metadata を経由せず、型変化の経路は見つかりません。
- **prepare 属性：** F:1199–1200 で `ccbench_dir` と `cache_root` の両方を copy 先へ再設定しています。
- **Git 観測：** refresh は `check=True` で、失敗を無視していません。porcelain 一致は全 index 観測の同値証明ではありませんが、ratified consumer は status／blob bytes を使います。別 production の `tools/codex_reasoning_ab.py:1927` にある `diff-index --cached` が、この fixture 消費経路に入る証拠はありません。
- **needle：** 構築元を含む追加は確認。既存 caller で構築元 path が正当に artifact に入る例は見つかりませんでした。任意の mutation payload に元 path を埋めれば検査は強くなりますが、現行 node の誤検出とは認定しません。
- **fork／lock：** key lock は test body の fork 後に開き、構築・copy 完了まで保持。通常終了・例外・`os._exit` で fd は閉じられます。内部の同期 fork が一時継承するだけで、親 worker が同じ fd を保持し続ける経路は見つかりません。
- **公開／欠損：** `os.replace` は全木 copy 後。協調する worker は同じ lock 内なので途中の entry を消しません。外部削除なら copy は失敗し、成功 hit として返りません。ただし marker だけ残った破損 entry を自動再構築する実装ではありません。

## 変異 mask の検査表

| 変異 | 再実行／保存される経路 | mask 判定 |
|---|---|---|
| M1 frozen-head | copy 後にも loader／launch を実行 | memo による判定再利用なし。kill 集合の実測は未確認 |
| M2 closure-sha | copy 後の closure 検査 | 同上 |
| M3 argv-root-leak | campaign 生成物を保存し、各 consumer で両 root の needle 検査 | fresh memo なら検出を維持する構造。**所見2の前走 memo では構築変異を隠す** |
| M4 launch-start-sha | journal を保存し、後段で再読込み・検査 | fresh memo なら変異 bytes が伝播。前走 memo では隠す。元来 SURVIVED の可能性は未確定 |
| M5 child-rc | RT の CHILD_RC return を毎回実行 | 小 repo 化は return/assertion を迂回しない |
| M6 fingerprint-compare | CAP_OOM の前後比較 | 対象の fingerprint mock は不変。今回の8関数は CHILD_RC／infra／interrupt 系で、比較経路の差替えなし |
| P0 equivalent | loader の等価条件変更 | memo による追加差は見つからず。ただし所見1の無変異 failure を先に解消する必要あり |

共通条件として、**変異適用後の新 interpreter と新 memo** が必要です。fresh directory だけでは fork 前 import の残留は解消しません。prefix 構築中の例外では marker は公開されません。後段 assertion の失敗時は prefix が残りますが、後段 assertion 自体は各 consumer で再実行されます。

## 総括

既存 test の構造と U3/R の置換範囲は概ね裁定どおりです。
U1 は fork decorator、session 境界、新正例の実 repo 入力共有を修正する必要があります。
四象限 local 3枝の除外は不要で、現物では dispatch 枝も適用可能です。
focus1 の成功分だけでは変異 kill 集合同一性や全 key の観測同一性は証明できません。