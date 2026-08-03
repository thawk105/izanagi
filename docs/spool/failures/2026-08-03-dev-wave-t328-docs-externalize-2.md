---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-03
wave: dev-wave-t328-docs-externalize
seq: 2
---

## 再発

### F84

- **再発: 2026-08-03** — [T-282] の残留計測で、job tmp の PBS script から
  `IZANAGI_TEST_TRIGGER=final python3 tools/run_tests.py` を直接呼び **116 failed / 2,085 errors**
  (request `878392`)。interpreter を `python3.10` へ固定しても、テストが `bash` 経由で起動する
  孫 process が PATH の `python3` を拾うため **19 failed** が残り (request `878395`)、
  `PATH` 先頭へ `python3` → `python3.10` の shim を置いて初めて **5,226 passed / rc=0**
  (request `878402`) になった。**赤の 19 件も `test_t126_pegasus_tools.py` という失敗面も F84 と同一**で、
  投入器が `_job_script` の interpreter 選択と `export PATH="$(dirname "$selected"):$PATH"` を
  写していなかった点まで一致する。F84 の対象が変異 harness の手書き投入器だったのに対し、
  本件は残留計測用の使い捨て PBS script であり、**「使い捨てだから写さなくてよい」という判断が
  同じ穴を再生産する**ことを示す 2 例目である。マシン固有の手順 (既定 `python3` の版・shim の要否・
  `-o`/`-e` の落ち先) は `docs/pegasus-runbook.md` §3 が正本。
