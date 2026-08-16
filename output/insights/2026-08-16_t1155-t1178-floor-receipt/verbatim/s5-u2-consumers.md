## 1. 実装内容

- [s8b_floor_stats.py:595](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_stats.py:595)
  - pure verifier に keyword-only 必須 `expected_holdout_admission` を追加。
  - live admission 非保証の境界を日本語 docstring に明記。
  - [live 公開入口:916](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_stats.py:916)を新設し、caller から expected admission を受け取らない署名に固定。
  - result v4、holdout ごとの `sort_best` 一意、canonical cell ID 集合・件数完全一致を必須化。
  - binaries 無しの後方互換 skip を削除し、conditional binary key helper を使用。

- [s8b_ratified_freeze.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:183)
  - result に `holdout_admission` を必須化し、manifest v3/result v4 のみ受理。
  - journal 検証後・result 検証前に [live 公開入口:3058](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:3058)を実行。
  - official path 由来の run ID/run relative pathを使用。
  - 到達不能を `floor-admission-unverifiable`、不一致を `floor-admission-mismatch` に分類。
  - SWO receipt の軸漏洩許可を固定 leaf key の列挙に限定。subtree は許可していない。
  - `_RUN_BASENAMES` は変更していない。

- [s8b_holdout_freeze.py:1318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_freeze.py:1318)
  - result v4と `holdout_admission` を要求。
  - v1 freeze から full cells/schedule を再導出。
  - sibling manifest を nofollow で読み、bytes SHA-256を独立照合。
  - [live 公開入口:1419](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_freeze.py:1419)を使用し、到達不能・不一致を別 prefix で拒否。

- [s8b_oracle_driver.py:949](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_oracle_driver.py:949)
  - portable binary の直接検査を conditional exact-key 対応。
  - receipt 発行経路は追加していない。

- [s8b_v2_freeze_fixture.py:363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/s8b_v2_freeze_fixture.py:363)
  - tmp repo 専用の sort receipt、manifest bytes hash、独立 admission evidence を追加。
  - admission digest は U0 の test-only canonical calculatorを使用し、production inspector/projectorで期待値を生成していない。

- Positive control:
  - [公開入口の自己投入不能 meta-test:588](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_floor_stats.py:588)
  - [binary 4拒否ケース:910](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_floor_stats.py:910)
  - [ratified 到達不能・claim不一致:799](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_ratified_verify.py:799)
  - [axis leaf 列挙・subtree拒否:2240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_ratified_verify.py:2240)
  - [oracle conditional key回帰:4554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_oracle_driver.py:4554)
  - [report rc 2・出力未作成:1497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_oracle_report.py:1497)

dev-wave スキルの実装子境界に従い、コードとテストのみを編集しました。docs、freeze hold、git、commitには触れていません。

## 2. 実走 nodeid と結果

pytest 実走 nodeidは **0件**、緑0件です。

以下を `tools/run_tests.py` 経由で試行しました。

- 指定3ファイル全体
- 新設した焦点10 nodeid
- `--force-dispatch` を付けた焦点3 nodeid

すべて nodeid 実行前に `Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1`、rc=16で停止しました。queue state は観測不能のため可用扱いであり、login node へ直接 pytest を迂回していません。

補助検査は成功しましたが、pytest の緑には数えていません。

- 変更11ファイルの `py_compile`・AST parse・NFC・結合文字検査
- pure verifier の正例と binary 3変異の手動 smoke
- pure/live API署名の meta smoke

状態は「実装済み・pytest未実走」です。

## 3. 期待赤とそれ以外の赤

事前登録したU1未完了由来の期待赤は次の3ファイルです。

- `test_s8b_floor_campaign.py`
- `test_s8b_materialization.py`
- `test_s8b_freeze_io.py`

xfail・skip化はしていません。pytest 自体が開始されなかったため、実際の期待赤集合と、それ以外の回帰赤は未観測です。

直接 import smokeでは `test_s8b_holdout_freeze.py` の既存 growth hold が発火しました。これは指示どおり解除・迂回しておらず、pytest結果には含めていません。

## 4. 現行から変更後の受理・拒否差分

| 面 | 変更前 | 変更後 |
|---|---|---|
| pure admission | admissionを検査しない | 必須の外部expectedと完全一致 |
| 公開consumer入口 | callerが自己申告expectedを渡せる設計余地 | expected引数自体が無く、inspectorを内部実行 |
| binary欠落 | `expected_binaries=None`なら省略可能 | 常に拒否 |
| binary coverage | 座標pair集合中心で重複cell aliasを見逃す | canonical cell ID集合＋件数の完全一致 |
| binary key | common単一集合 | `configuration_id` 条件付きexact key |
| sort_best | verifier前段の一意性検査なし | holdoutごとにちょうど1件必須 |
| ratified schema |旧result/manifest文言・admission無し | result v4/manifest v3のみ |
| ratified live root | 台帳削除後も通過可能 | 到達不能もfail-closed拒否 |
| admission分類 | 分類なし | unavailableとmismatchを別reason |
| holdout manifest | result自己申告hashのみ | sibling bytesをnofollow独立hash |
| axis許可 | SWO receipt用許可なし | 固定leafのみ許可、subtree拒否 |
| oracle driver | central validatorへの暗黙委譲 | conditional keyを直接固定。意味論は維持 |
| report | ratified層にlive拒否なし | unavailableでrc 2、出力未作成 |

実在する旧floor成果物2件はlegacy v2で、既に従来のv3要求から拒否対象です。generator bytes pinは実在し既に不一致・hold中という裁定を維持しました。

## 5. 所有外への波及

- U1所有の `test_s8b_floor_campaign.py` に残るpure verifier直接呼出しは、新しい必須 `expected_holdout_admission` への追随が必要です。
- U1 producer本体には既にlive入口接続用 helperが入っており、本U2 API署名と一致します。
- `test_s8b_materialization.py`、`test_s8b_freeze_io.py` はresult v4/manifest v3、sort receipt、admission fixtureの波及対象です。
- U0共有fixture・inspector・schema定数・key helperの署名は変更していません。
- `test_pegasus_floor_tools.py` はU0の `enumerate_cells` sort gateによる静的波及可能性があります。
- `s8b_oracle_report.py` production codeは変更せず、ratified拒否の伝播だけをテストで固定しました。
- `freeze_verification_hold.py` と `output/s8b-freeze/holdout_freeze.json` は未編集です。

## 総括

完了: consumer実装、fixture、positive control、静的検査は完了。docs・git・commit・holdには未接触です。

残した赤: pytestはdispatch障害で0 nodeid実走。期待赤3ファイルと、それ以外の回帰有無は未判定です。

U1への申し送り: pure verifier直接テストへ必須admissionを渡し、U1統合後に指定3ファイルとconsumer/report全焦点nodeidをwrapperで再実走してください。