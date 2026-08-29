---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-29
wave: dev-wave-t2072-t2073-flaky-hold-rootfix
seq: 2
---

## 再発

### F273

- **再発ではなく解消の記録: 2026-08-29** — 2026-08-28 の再発
  (`test_check_receipt_reads_v1_field_sets_with_explicit_skip_diagnostics[False]` が
  空 stdout の `JSONDecodeError` で落ちた件) について、**空 stdout を生む経路を実測で特定し、
  その経路を閉じた。** 機序はこうである。checker の判定表は `schema_version` が 4 / 5 の
  ときだけ `preparation_wall_clock_s` と `finalization_wall_clock_s` を引き、
  v1 / v2 / v3 では **launcher プロセス全体の実時間**をそのまま
  `wall_clock_admission_bound_s` と比べる。互換テストの上限は 3 秒だった。
  同一 receipt の `actuals.wall_clock_s` **だけ**を変えた 7 点の制御実験で、
  3.0 秒までは rc=0 で 202 byte の JSON、3.001 秒からは rc=2・stdout 0 byte・
  stderr `NG: receipt truth table が不正` になることを確かめた。無負荷の計算ノードでの
  内訳は attempt 0.211 秒・全体 0.681 秒で、差の 0.470 秒 (全体の 69%) が
  引き算されない準備・後始末である。実受入負荷下では準備だけで 1.926 秒、全体 5.290 秒に
  達した実測が別 wave の failure archive に残っていた
  (`0-948382.nqsv--bnode033`、2026-08-26、v4 receipt)。
- **原因確定ではなく再現である。** T-1958 の赤の junit は残っており `s = ''` で stdout が
  空だったことは確定するが、`checked.stderr` と当時の receipt は残っていない。
  `NG: receipt truth table が不正` は複数の述語が共有する最終例外なので、同じ stderr を
  再現しても経路を一意に識別しない。当該 node の junit `time` は 5.368 秒で、
  `acceptance_duration_ledger.json` の公称 1.3 秒に対し 4.1 倍という状況証拠が加わるだけである。
- 恒久対応は 2 つある。第一に、この赤が長く診断不能だった直接の原因は、テストが
  `json.loads(checked.stdout)` を `assert checked.returncode == 0, checked.stderr` より
  **先**に置いていたことである。rc と stderr が捨てられ JSONDecodeError だけが残っていた。
  該当 2 箇所の順序を入れ替えた (`orchestrator/tests/test_codex_worker_launch.py` の
  `test_check_receipt_marks_self_asserted_limits_and_accepts_external_expectations` と
  `test_check_receipt_reads_v1_field_sets_with_explicit_skip_diagnostics`)。
  第二に、露出する 3 関数 (v1 / v2 / v3 の各 2 param、計 6 node) の fixture 上限を
  10 秒 subprocess watchdog より大きい値へ上げ、**測定値は 1 byte も書き換えずに**
  admission 上限を判定の律速から外した。予算変更が効いていることは、receipt 上限が
  watchdog 秒数を上回るという定数比較の assert が固定する。
  上限超過の legacy receipt がなお拒否されることは、新設した決定的な
  `at-bound` / `over-bound` の 2 node が両側から固定する。
- **修理後の再発検知条件を署名別に分ける。** legacy 降格後の truth-table rejection
  (`NG: receipt truth table が不正`) が上記 6 node で再び出た場合、**単独再走が緑でも
  負荷 flake と断じてはならない。** 修理差分からの到達性、checker の stderr 本文、receipt の
  総 wall・phase wall・attempt wall を検査する。従来の「単独再走が緑なら差分へ帰属させない」
  条件は、child pid・manifest・producer の max-wall 系の署名に限って残す。
- **本 wave が閉じたのは、accepted v5 receipt を v1 / v2 / v3 へ降格して検査する
  legacy 6 node の 3 秒 admission 経路だけである。** launcher と checker の 10 秒 watchdog、
  child pid の 2 秒 deadline、manifest 観測の 3 秒、late rollout の 3 秒、fake barrier の 5 秒は
  残存する。file 全体の flake 解消は主張しない。
