---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1726-freeze-rederive
seq: 3
---

## 新規

### {{F:launcher-failure-artifacts-break-output-snapshot}}. launcher テストの失敗診断が同じ全走の output snapshot 検査を連鎖的に赤にする [テスト代表性] [計測汚染]

- 事象: 受入全走 attempt 2 (claimed_main `f4c2c5ded29d72d8f06bca66992a5ef5694fcb51`) が
  13 failed で戻った。内訳は `test_s8b_floor_campaign.py` の official / pilot 系 **11 件**と
  `test_codex_worker_launch.py` の 2 件である。
  前者は全件 `assert repo_before == _real_output_snapshot()` 型で、差分本文は
  `At index 13837 diff: ('dir', 's1-budget') != ('dir', 'runs/pytest-launcher-failures/0-948253.nqsv--bnode042')`。
  同 wave の attempt 1 は launcher 9 件 + floor 0 件で、**落ちる組み合わせが巡ごとに入れ替わる。**
- 根本原因: `orchestrator/tests/test_codex_worker_launch.py:55` の `_FAILURE_ARTIFACT_ROOT` は
  実 repo の `output/runs/pytest-launcher-failures` であり、`_failure_run_directory()` (87-92 行) が
  `<PBS_JOBID>--<hostname>` を**失敗時にだけ**掘る。一方
  `orchestrator/tests/test_s8b_floor_campaign.py:1451` の `_real_output_snapshot()` は
  `output/` 全体を除外なしで walk する。xdist 並列の全走では両者が同時に走るため、
  launcher が負荷で 1 件でも落ちた瞬間にその directory が floor_campaign の before/after 窓へ入る。
  **floor_campaign の赤は launcher の赤の連鎖であり、件数でなく生成タイミングと窓の重なりで決まる。**
  `output/runs/` は `.gitignore` 済みのため git 系の検査には現れず、
  ファイルシステム走査の検査にだけ現れる。
- 既載との違い: F62 と F115 は**親が全走中に `output/` を書いた**型である。
  本件の書き手は同じ全走の中の別テストであり、親は attempt 1 / 2 の実行中に `output/` を
  一切書いていない。既載の再発検知 (「走行中の `output/` 書き込みをまず疑う」) は本件を説明しない。
- 恒久対応: 判定は `DW-O18` の既存規律へ寄せる — 差分が到達しえないファイルの赤は単独再走で
  再現性を実測してから扱う。本エントリがその起票実体である。
  **機構 (snapshot 側で `output/runs/` を除外するか、launcher の失敗 artifact root を
  実 repo の `output/` 外へ移すか) は受理集合と診断保存の設計択一であり、裁定パッケージへ返す。**
- 再発検知: 受入が赤で、`test_s8b_floor_campaign.py` の `_real_output_snapshot` 系と
  `test_codex_worker_launch.py` が**同じ巡で**落ちているときは本件型を疑う。
  差分本文に `runs/pytest-launcher-failures/` が現れるかを見る。
  両 file の単独走が緑なら実装差分へ帰属させない。本 wave の実測は
  `test_codex_worker_launch.py` 単独 `--force-dispatch` = 202 passed / 8.83s / rc=0、
  `test_s8b_floor_campaign.py` 単独 `--force-dispatch` = 455 passed / 2 skipped / 34.21s / rc=0。
