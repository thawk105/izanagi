## 総括

B-1 は **partial（実装済み・未実走）** です。  
非凍結 legacy CLI の argv・完全 provenance・描画分岐を同時検査するテストを追加しました。  
既存の凍結 CLI テストと期待値は変更していません。  
runner が dispatch 前処理で停止したため、closed とは判定しません。

## 所見対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| B-1 | partial | 実際の `main` → 描画 → publish を通し、全4軸の目盛と下段の軸ラベルを検査するテストを追加。pytest 未起動のため実証待ち。 |

## 変更した file と差分の要点

[test_plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/fig5-a2-fix1/orchestrator/tests/test_plot_a2_certification.py:1471) に1テスト、53行を追加しました。

- 仮 repo に改訂稿の実ファイルをコピー。
- `fig5_fixture` で repo 相対 argv、provenance 全キー、入力3行を検査。
- 実 publish に委譲する観測関数で axes を取得し、`BACK_OFF=0/1` と軸ラベルを検査。
- 生成器・共有 helper・既存テストは変更なし。

## 実走した検査

`tools/run_tests.py` の呼出しは **rc=16**。`qstat -Q preflight rc=1` により **child_started=false** でした。以下はすべて未実走です。

| file | 指定 nodeid |
|---|---|
| `orchestrator/tests/test_plot_a2_certification.py` | `::test_default_legacy_cli_provenance_argv_and_axis_labels` |
| 同上 | `::test_cli_writes_complete_provenance_with_repo_relative_argv` |
| `orchestrator/tests/test_plain_runner_coverage.py` | ファイル全体（集合制約 meta-test、3件） |
| `orchestrator/tests/test_pytest_collection_config.py` | `::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests` |

静的検査は AST parse、`git diff --check` ともに rc=0。親の全走・変異走行は未実走です。

## 波及可能性

- 所有外 caller：生成器の API・挙動への変更なし。
- 共有 fixture：変更なし。追加の monkeypatch は当該テスト内のみ。
- consumer test：静的検索では他テストから当該モジュールへの参照なし。
- テスト収集数が1件増加。集合制約 meta-test の検査は実行環境復旧後に必要です。

## 裁定との差

検査を完走できませんでした。また、必須 runner が所有外に次の receipt を自動生成しました。

`output/pegasus-dispatch/3559da2d0bc1384d568b4e5e9360102c/receipt.json`

Git 上の変更は指定テストファイルのみです。commit・push は実施していません。