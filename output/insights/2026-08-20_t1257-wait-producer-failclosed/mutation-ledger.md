# [T-1257] 変異 matrix 台帳 — producer 完了確定 fails-closed 検査

対象: `tools/dev_wave_wait.py` の `_ProducerState.complete` / `_producer_state_outcome`。
repo_head (mutation 対象 commit): `54bc579dfc880cc973b693e3e16a0dbb4ca90719`。
runner: `python3 tools/run_tests.py orchestrator/tests/test_dev_wave_wait.py -rf --force-dispatch`
(`--runner-mode dispatch`)。生の JSON (baseline stdout・失敗時 pytest 全文を含む) は
`/work/1/SFC/tanab/dev-wave-jobs/2026-08-20_t1257-wait-producer-failclosed/codex-artifacts/`
の `mutation-spec.json` / `mutation-result.json` (probe、1回目) / `mutation-result2.json`
(補正後、確定) に残っている。

## 実測経緯 (DW-M08 の「初回 probe → 完全集合再登録」)

1回目 (`mutation-result.json`, `--wrapper-attempt 1`): baseline PASSED (394 passed)。
M1/M2 とも実際にはテストを失敗させていたが、親が事前登録した `expected_nodes` が
不完全だったため harness 判定は両方とも `MISMATCH` だった。具体的には、既存の
`_FakeEffects` ベースの `test_producer_check_only_missing_condition_is_fail_closed`
(新設テストとは別に元々あったテスト) も、mtime 読み取り未キューによる `AssertionError`
経由で診断文字列 (`producer-dead`/`done-file`/`artifact-file`) が変わることを検出しており、
親はこれを事前に見落としていた。

2回目 (`mutation-result2.json`, `--wrapper-attempt 2`, 実測値で `expected_nodes` を補正):

| id | 変異内容 | expected_status | 実際の status | matches_expectation |
|---|---|---|---|---|
| M1 | `_ProducerState.complete` から `producer_dead` 条件を除去 | KILLED | KILLED | true |
| M2 | `_producer_state_outcome` の 3 条件 gate を `if True:` へバイパス | KILLED | KILLED | true |

baseline: PASSED (394 passed, 0 failed, dispatch 48 workers, 63.30 秒)。
SURVIVED 0、MISMATCH 0。

## 変異が検出された経路 (2 種類、独立)

- **新設テスト** `test_producer_receipt_gate_rejects_incomplete_state_with_real_files`
  (`_ProducerState` を直接注入し実ファイルで検証): `assert outcome.rc == RC_FAIL_CLOSED` が
  `0 == 70` で失敗 (receipt が実際に publish されてしまう)。
- **既存テスト** `test_producer_check_only_missing_condition_is_fail_closed`
  (`_FakeEffects` 経由): `assert expected_missing in diagnostic.err` が失敗
  (`producer-dead`/`done-file`/`artifact-file` の代わりに `receipt-publish` 例外の
  診断文字列になる)。段6レンズBは「このテストは検出できない」と指摘したが、
  実測では**別の assertion (診断文字列) 経由で正しく検出していた**ことが probe 走で判明した。
  当初の懸念 (rc だけを見れば検出できない) は妥当だったが、テスト全体としては
  冗長に守られていたことになる。

## 単一理由性 (DW-M01)

各変異のオラクルは check-only の rc と receipt 実在 (新設テスト)、または診断文字列
(既存テスト) だけを見ており、親の手動 3 点照合など他の防御層と併用していない。
