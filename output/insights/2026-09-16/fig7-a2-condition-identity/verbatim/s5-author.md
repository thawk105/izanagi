## 総括

実装は完了しましたが、テストは未実走です。
runner は pytest 起動前に dispatch 失敗（rc=16）となりました。
旧 fig5・fig6 の成果物、docs は変更していません。
図の生成・commit・push は行っていません。

## 変更した file と差分の要点

- `tools/plotting/plot_a2_certification.py`：凍結 prefix 列挙、legacy caption・目盛の訂正、条件説明の `caption_source` を追加。current-full 分岐と数値・内部 identity は維持。
- `orchestrator/tests/test_plot_a2_certification.py`：裁定の 5 項目を追加。既存の 2 行 assertion は保持し、そのテスト内の出力名を凍結 prefix に変更。

## 実走した検査

- AST 構文解析（変更した 2 file）：rc=0。
- `git diff --check`：rc=0。
- 以下は runner rc=16、`child_started=false`。nodeid は実走されていません。
  - `orchestrator/tests/test_plot_a2_certification.py` 全体。
  - `orchestrator/tests/test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests`
  - 独自に発見した `orchestrator/tests/test_plain_runner_coverage.py` 全体。

旧 fig5 closure・新旧目盛・追加負例も未実走です。fig7 着地検査は未着地時の skip 条件を実装しましたが、成功には数えません。

## 期待赤 / 既知の赤

実測したテストの赤はありません。検査基盤が `qstat -Q preflight rc=1` で失敗しています。

## 波及可能性

- 直接 caller は生成器の `main` と同テスト file。既存の `make_figure(data)` 呼出しは継続可能です。
- 共有 fixture の定義は変更していません。
- 所有外 consumer は figures README・保存 provenance を使う closure 検査。親による新図の着地・全走・変異検査が残ります。
- 凍結列挙外の legacy 出力は訂正 caption・目盛・3 行 provenance になります。

## 裁定との差

実装方針の差はありません。ただし実走による検証は未完了です。

所有制約に対する副作用として、検査 runner が `output/pegasus-dispatch/` 内に失敗 receipt を 2 件自動保存しました。所有外のため削除していません。