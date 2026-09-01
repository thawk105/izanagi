## 総括

段 4 裁定 R1〜R9 に従い、指定された新規 2 file だけを実装しました。  
assembly rejection 時も 201 block／402 arm を報告し、raw 値は補完しません。  
既存 file は変更せず、commit・add 等の禁止 Git 操作も実行していません。  
pytest は Pegasus の `qstat -Q` 障害で子が起動せず、実装済み・未実走です。

## 実装したもの

- [p3_b4_material_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/campaign/p3_b4_material_report.py:172)

  - publication loader、producer assembler、ledger binding、既存 evaluator を合成。
  - JSON／Markdown の決定論的生成、完全射影検査、no-overwrite writer、直接起動 CLI を実装。
  - 正規コマンド:
    `python3 orchestrator/campaign/p3_b4_material_report.py PUBLICATION_ROOT [--output-root PATH]`

- [test_p3_b4_material_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/tests/test_p3_b4_material_report.py:45)

  - module-scope immutable publication fixture。
  - real `invoke()` を on/off 各 1 回と検査。
  - xdist group により fixture を単一 worker へ固定。
  - pytest 自走 harness を備え、README allowlist の変更は不要。

| 裁定 | 実装 |
|---|---|
| R1 | assembly 前に 402 arm frame を固定。拒否理由、各 planned artifact の観測在否、過去 rejection の復元不能を出力 |
| R2 | exact source UTF-8 と無加工の構造化 source objectを保持。派生行を source／manifest／registry と照合 |
| R3 | `floor=None` 固定。evidence-only、§5 未発効、`protocol_violation`／`floor_domain_error` を機械可読化 |
| R4 | output の symlink component と campaign との一致・配下・祖先の三方向を拒否 |
| R5 | `anomaly_class` は明示的 absent。precursor red classes と evidence issues は別名で完全射影 |
| R6 | issuer／ledger 例外だけを理由付きで変換。assembly rejection と evaluator invalid は独立経路 |
| R7 | clean subprocess は repo 外 cwd、`PYTHONPATH` 除去、`PYTHONNOUSERSITE=1`、`-B` を使用 |
| R8 | CLI は同じ argv で 2 回起動。2 回目は publication 再評価前に既存出力を拒否 |
| R9 | registry の `initial_proposal_sha256`、`binding: transcribed`、producer 非保証を同じ行へ収録 |

## 実走結果

- `python3 tools/run_tests.py orchestrator/tests/test_p3_b4_material_report.py`
  - 2 回試行。
  - いずれも rc=16、`qstat -Q preflight rc=1`。
  - `child_started=false` のため passed／failed は 0 件ではなく、pytest 未起動です。
  - 新規 file 単独所要は未計測です。

- `python3 -B tools/check_subprocess_bytecode_guard.py --repo .`
  - rc=0、18.09 秒。

- 構文、直接 CLI bootstrap、自走 harness、U+0300〜U+036F 不在の静的検査
  - rc=0、0.4 秒。

## 一覧検査・meta-test

試行コマンド:

`python3 tools/run_tests.py orchestrator/tests/test_pytest_collection_config.py orchestrator/tests/test_plain_runner_coverage.py orchestrator/tests/test_campaign_import_invariant.py`

結果は rc=16、`child_started=false`、0.13 秒でした。meta-test 自体は未実走です。

静的には以下を確認済みです。

- campaign module は正規 bootstrap より後に relative import。
- test file は `pytest.main([__file__])` 自走 harness を保持。
- Python subprocess は 2 箇所だけで、双方が bytecode guard 適合。
- `git status` 上の変更は指定された新規 2 file だけ。

## 所有外への波及 (静的列挙)

- 新 generator は既存の issuer、producer、ledger、evaluator 公開 API を consumer として呼びます。
- 新 test fixture は既存 raw producer test の real seed／replica helper に依存します。
- 新しい `campaign/*.py` と `test_*.py` のため、campaign import invariant、plain-runner coverage、pytest collection 検査の走査対象になります。
- 既存 closure file、共有 fixture、docs、hook、既存テスト期待値には変更がありません。

## 現行の受理・拒否挙動

- 既存 API の受理集合は変更していません。
- 正常 assembly は 402 source と分析結果を完全射影します。
- assembly rejection は report を拒否せず、全 frame と観測在否を出力します。
- issuer／ledger rejection、output alias／交差、既存出力は 1 file も公開せず拒否します。
- evaluator の floor 不在 invalid result は report に保持します。
- 昇格 validator、official-root admission、certified-selection connection、qsub／build／campaign 実走入口は追加していません。

## 未完・未解決

- Pegasus dispatch infrastructure の復旧後に、焦点 test と 3 meta-test の実走、および新規 test file 単独所要の計測が必要です。
- 権威ある floor artifact と durable producer rejection ledger は裁定どおり本 wave の scope 外です。