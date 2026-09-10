実装は完了しました。許可された4パス以外は変更しておらず、commit・stage・禁止された docs 編集は行っていません。実行環境の dispatch 障害により pytest は未実走扱いです。

## 総括

- 変更ファイル

  - [tools/check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py)
    - `malformed-ai-agent` kind、note/value 検証、完全 prefix による分類 helper、値一致照合、常時可視化を実装。
    - ruling 定数2本と、TSV順の23件を登録。22件は指定値、`2c1929...` のみ `missing-codex-author`。
    - 既存7件、許可値集合、`ForwardCorrectionSpec` は変更なし。
  - [test_check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py)
    - 既存3テストを30件対応へ更新。
    - note/value 制約、固定 prefix、値照合、未登録・stale、受理言語不変性を検証する8テストを新設。
    - 既存期待値の反転・緩和・skip・削除なし。
  - `probe_split_window.py`
    - 指示どおり削除。
  - [probe_split_window.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/output/insights/2026-08-09_t659-activation-deploy-window/verbatim/probe_split_window.md)
    - 元ソース全文を逐語 fence へ移行し、元ファイルの SHA-256、外部コピー、限界説明を記録。
    - fence 内ソースの SHA-256 は元ファイルと一致。

- pytest 実行範囲と結果

  - 全体対象:
    - `orchestrator/tests/test_check_ai_provenance.py`
    - 3回試行（通常2回、待機後1回）および `--collect-only` を試行。
  - 更新3件＋新設8件の `-k` 集合も試行。
  - meta-test:
    - `orchestrator/tests/test_check_ai_provenance.py::test_every_checker_main_call_in_this_suite_pins_the_site`
    - `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
    - `orchestrator/tests/test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries`
  - すべて `tools/run_tests.py` 経由で試行したが、`qstat -Q preflight rc=1` により `rc=16`。ローカル側も予約台帳を sandbox から安全に更新できず dispatch 判定となった。
  - 実数: collected 0 / passed 0 / failed 0。pytest 自体が起動していないため、緑・closed は申告しない。
  - 静的確認として AST parse、`git diff --check`、30件・22 malformed・TSV順、probe の digest 一致は成功。

- 受理・拒否挙動

  - 変更前:
    - `AI-Agent` は現行の厳密な product/model/reasoning/role/scope 文法のみ受理。
    - registry kind は `missing-ai-agent` と `missing-codex-author` のみ。
    - note は任意で、抑制は SHA＋kind 一致。
    - malformed trailer は登録不能で、通常 finding として残る。
  - 変更後:
    - trailer 自体の受理・拒否文法は一切変更なし。`ROLES`、`IDENT`、`AGENT_VALUE` の許可集合も不変。
    - `malformed-ai-agent` は、非空の固定期待値と安全な1行 note がある場合のみ registry で受理。
    - note/value の制御文字および U+200B/U+200C/U+200D/U+FEFF を拒否。
    - 他kindへ非空値を設定した場合、または malformed の値・note が空の場合は拒否。
    - 登録済み malformed は SHA＋kind＋値の完全一致時だけ抑制。値違い・未登録は finding のまま。
    - 既存kindは引き続き SHA＋kind で照合し、空noteも受理。
    - したがって trailer の受理集合は不変で、ledger 抑制集合だけが裁定済み22件の完全一致へ限定して拡張。

- 未実走・未確認

  - 上記 pytest は環境障害によりすべて未実走。
  - 受入全走と `python3 tools/check_ai_provenance.py` は指示どおり未実行。
  - 親担当の README/package 更新前なので、削除した `.py` へのリンク切れは現時点で想定済み。
  - 禁止パスへの変更、commit、stage は行っていない。

- 所有外への波及可能性

  - checker の終了コード・出力を扱う `tools/dev_wave_land.py` と Pegasus dispatch consumer。
  - `orchestrator/tests/test_hooks.py` の checker 起動契約。
  - テストファイル内共有 fixture `_known_spec` と、main 呼び出しを制約する meta-test。
  - plain-runner coverage の allowlist/meta-test。
  - 親所有の insight `README.md` / `package.md` に残る旧 `.py` 参照。
  - decisions/worklog/archive にある履歴上の `.py` 参照は意図的に未変更。