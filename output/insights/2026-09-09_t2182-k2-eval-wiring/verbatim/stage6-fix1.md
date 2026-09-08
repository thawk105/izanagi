## 所見の対応表 (closed / partial / regressed)

| 所見 | 状態 | 根拠 |
|---|---|---|
| condition gate が campaign build より先に `_v2_commands` を呼ぶ | partial | 実装修正済み。必須テストは実行基盤障害で未実走 |
| M1: prebuild token の生成器束縛 | partial | 既存の生成器突き合わせテストを維持。未実走 |
| M2: receipt 無しでは空 argv | partial | 既存分岐を維持。未実走 |
| regressed | 検出なし | 静的検査のみ。テスト未実走のため closed とはしない |

## 実装した内容

[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2182-fix1/orchestrator/campaign/p3_s4_loop.py:330) を修正しました。

- production 経路から `buildcache._v2_commands` 呼び出しを除去。
- 不要になった `Genome`、toolchain、未使用 build dir の構築を除去。
- source dir は既存の `_normalize_fetchcontent_source_dirs` で正規化し、token は `_fetchcontent_source_defines` から生成。
- base dir と dependency prefix の token のみ `p3_s4_loop.py` 側で構築。
- [M1 正例](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2182-fix1/orchestrator/tests/test_p3_s4_loop.py:7853) にある `_v2_commands` との生成器突き合わせは変更せず維持。
- 禁止対象、単位 B、docs、既存テスト期待値は編集していません。commit もしていません。

## 実走結果

必須コマンドを 2 回実行しました。

```text
python3 tools/run_tests.py -rf orchestrator/tests/test_p3_s4_loop.py
```

両方ともテスト開始前に以下で終了しました。

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"dispatch-error"}
runner rc=16
```

したがって、実装済み・未実走です。実走した pytest nodeid と pass 件数はありません。

静的検査結果:

- `p3_s4_loop.py` と `test_p3_s4_loop.py`: AST parse 成功
- production の `_v2_commands` 呼び出し: 0 件
- U+0300 から U+036F: 0 件
- trailing whitespace: 検出なし

## 保証の含意

保証すること: prebuild receipt がある経路では、base dir、3 本の source dir、非空なら dependency prefix の token を campaign build と同じ source-define producerから組み立て、condition gateへ渡します。

保証しないこと: 今回の未実走状態ではテストの緑、実 configure の完走、その後の build や評価完了までは保証しません。

正例は、prebuild receipt と非空 dependency prefix がある場合に M1 テストが condition gate の 5 token と `_v2_commands` の FetchContent 関連 5 token を一致検査するケースです。

## 波及可能性

- 所有外 caller: 射影範囲内では helper の production caller は [1 箇所](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2182-fix1/orchestrator/campaign/p3_s4_loop.py:1728)のみです。射影外は指示に従い検索していません。
- 共有 producer: read-only の `buildcache._normalize_fetchcontent_source_dirs` と `_fetchcontent_source_defines` に依存します。`buildcache.py` は未変更です。
- 共有 fixture: `_observe_iteration_condition_gate_configure_argv`、`_write_prebuild_receipt`、`_PrebuildProbeStop` は未変更ですが本修正を観測します。
- consumer test: M1、M2、および fixture/proposal 両経路の `test_prebuild_reaches_production_build_v2_and_v2_commands_in_both_main_routes` が直接の確認対象です。

## 総括

must-fix の実装は完了し、元の probe が condition gate 側で先に発火する原因を除去しました。ただし正規 runner が Pegasus preflight で 2 回停止したため、所見は `partial`、実装済み・未実走です。