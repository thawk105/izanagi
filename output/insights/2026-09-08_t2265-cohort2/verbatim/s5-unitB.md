## 実装内容

変更は指定された4ファイルだけです。

- cohort 2 の exact 3-cell、extime 6、terminal 5,000,000 µs、schema v4、事前登録 SHA を追加。
- raw trace v3を追加し、`terminal_flush`、`trigger=terminal`、連続 `seq`、terminal の一意性と末尾性、summary 4-key 契約を厳密検査。
- certification を exact 4-cell の閉じた表へ拡張。旧2-cellは extime 3、新p1/p2は extime 6。
- policy 2 certification は明示 seed を拒否し、既定 seed `11400714819323198485` の genome に限定。
- performance artifact に cell別 extime と、cohort 2では既定 seed genome の束縛を追加。
- PBSへ cohort 2 raw literal、`IZANAGI_T2187_EXTIME`、terminal define、cell別 trace/cert gate、明示的 `--extime` を追加。
- ASTからbuild sinkを再導出し、pinを `3375` と `3749` に更新。理由文も `exact 4 cell` に更新。

## cohort 1 の保持根拠

- `TRACE_SCHEMA_VERSION`、旧事前登録path、旧cell literalは変更していません。
- trace契約表の旧2エントリは同じcell tupleとextime 3へ束縛。
- `_artifact_contract_metadata` のcohort 1述語はそのまま残し、その後へ独立したcohort 2分岐を追加。
- raw v1/v2 parserの受理を維持し、全既存testを含む123件が通過。
- cohort 1事前登録SHA `526d9384...495a` とcohort 2 SHA `8b4127f4...a9e9`を再確認済み。

## certification の受理形拡張署名

受理には、raw literal、parsed Cell、cell別extime、claim、事前登録、namespace、row、24-row group、published receipt、performance artifact identityの全条件一致が必要です。prefix一致や任意の正extimeは導入していません。

通る正例:

```text
cells=cw-as-dyn-c2-p1:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:1
workloads=balanced
threads=48
extime=6
reps-per-job=1
rep-index=0
```

落ちるnear-miss:

```text
cells=cw-as-dyn-c2-p1:1:1:1000:2560:10000:9223372036854775806:1:1:4:1:1
```

capが1小さいため `certification-cell-mismatch` で拒否します。

## unit Aとの照合

unit A完了報告の逐語書式と一致しました。

- raw eventは `v=3`、`terminal_flush` は末尾。
- terminalは `trigger=3`、`assigned_invert=-1`。
- summaryは `updates retained dropped flushes` の順。
- parserはraw `trigger=3`を `trigger="terminal"` へ写像。

食い違いはありません。

## 実走結果

- `tools/run_tests.py`による指定5 nodeid走行はqueue preflight失敗の `rc=16`。子testは未起動。
- 自走harness `PYTHONPATH=. python3 orchestrator/tests/test_t2187_adaptive_const_probe.py`
  - ファイル全体: `123 passed`
  - PBS内の実 `/bin/bash -n` 検査も通過。
- 自走harness `PYTHONPATH=. python3 orchestrator/tests/test_ccbench_spawn_sites.py`
  - ファイル全体: `44 passed`
- `git diff --check`: passed。
- U+0300からU+036F: 検出なし。
- build、benchmark、統合後producer-consumer test: 実装済み・未実走。

## 所有外への波及

静的に残る波及候補です。

- unit Aの `test_dynamic_backoff_transitions.py::test_emitter_stdout_parses_with_the_real_parser`: A+B統合後の実走が必要。
- `condition_meaning_gate.py`、`screening_driver.py`と各test: 新define `BACKOFF_TRACE_TERMINAL_US` の登録が必要。
- unit Cのcohort 2解析器、plot、consumer test: schema v4、extime 6、新cell、terminal summary、新patch identityへの追随が必要。
- 共有fixture: cohort 2 certification fixtureにはextime 6、新事前登録SHA、既定seed genomeが必要。
- qsub/direct caller: cohort 2では `IZANAGI_T2187_EXTIME=6`、traceではterminal 5,000,000 µsが必要。
- cohort 1解析器と既存成果物は旧schema・旧patch hashの歴史的束縛として変更禁止。

## 所有外なので触らなかったもの

- unit A所有のpatch C、patch README、遷移test。
- unit C所有の解析器、plot、各test。
- `condition_meaning_gate.py`、`screening_driver.py`と各test。
- `source_digest.py`: ALLOWLIST拡張は禁止かつ不要。
- `docs/`、`patches/`、handoff、worklog。
- commit、git add、branch操作、pushは未実施。

## 総括

実装: cohort 2 trace v4、PBS追随、exact 4-cell certification、AST spawn pinを実装。  
実走結果: 所有2 test fileは合計167件passed、bash構文検査とdiff検査もpassed。  
残っている赤: unit B単体はなし。統合後のunit A producer-consumer testと所有外condition registryは未実走・未追随。