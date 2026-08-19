---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-19
wave: dev-wave-t1408-stale-closure
seq: 1
---

## supersede 追記

- F417 **supersede: 2026-08-19** — 恒久対応は完了に訂正する。commit `4cc60864` (D551、`fix(s8c): 凍結世代の検証から履歴長比例のコストを取り除く`) が `_batch_oids` の走査対象を凍結 namespace を触った commit + 直接親 + 境界へ絞り、判定4種を維持したまま履歴比例 cost を解消した (50,105要求→385要求)。現行 main (`bf9f6713`) で対象2テストを含む `test_s8c_preregistration_invariant.py` + `_core.py` 計408件を Pegasus dispatch 実走し全件合格を確認した (request 924423.nqsv、57.34s)。同根本原因は F418 としても独立発見されている。worklog [T-1408] は完了として carry から落とした。
- F418 **supersede: 2026-08-19** — 「再発検知: 8c側で確認するとよい (本waveでは未確認)」を解消する。`4cc60864` が追加した回帰テスト `orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_batch_is_bounded_by_frozen_touch_points` (no-touch commit数を変えた2ケースで要求数合計が一致することを固定) の存在と合格を確認した。現行 main (`bf9f6713`) でこのテストを含む計408件の Pegasus dispatch 実走が全件合格した (request 924423.nqsv、57.34s)。同根本原因を指す F417 (T-1362 由来、worklog [T-1408] として発行、本 wave で完了扱い) も参照。
