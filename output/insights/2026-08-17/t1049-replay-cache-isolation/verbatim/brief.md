# T-1049 段 1 brief (再開 r2 / 現 main 699c9cae で改訂)

## scope

pytest process 内で `orchestrator/campaign/reflux_formal_consumer.py` の
`_OPERATION_REPLAY_CACHE` が test 間に残ることによる汚染だけを、test 側で隔離する。

## 確定済み裁定 (親)

- 第一候補は test 側の autouse fixture または test-scoped cache。
- production の replay 検出は緩めない。production 変更が必要と判明したら実装せず裁定へ返す (規律 2)。

## 不変条件

- 同一 `operation_id` と異なる payload は引き続き `FormalReceiptError(REPLAY)` で拒否する。
- 同一 test 内の replay 検出状態を途中で消さない。

## 事実 anchor (現 main 699c9cae で実測)

| 内容 | 所在 |
|---|---|
| module 全体で共有される replay cache | `orchestrator/campaign/reflux_formal_consumer.py:277` |
| replay mismatch の raise | `orchestrator/campaign/reflux_formal_consumer.py:1045-1051` |
| cache への書き込み | `orchestrator/campaign/reflux_formal_consumer.py:1065-1067` |
| 唯一の間接呼出し点 | `orchestrator/campaign/reflux_origin_client.py:252` |
| 失敗 anchor の test | `orchestrator/tests/test_p3_autonomous_workload_trial.py:6720` |
| 失敗 anchor が使う helper | `orchestrator/tests/test_p3_autonomous_workload_trial.py:6365` |
| helper の terminal_operation_id 導出 | `orchestrator/tests/test_p3_autonomous_workload_trial.py:6493-6497` |
| 既存の clear fixture (1 file 限定) | `orchestrator/tests/test_reflux_formal_consumer.py:196-202` |
| 共通 conftest (autouse 3 本) | `orchestrator/tests/conftest.py:148,279,295` |

## 段 1 で実測した新事実 — 前提を覆す可能性がある

1. 失敗 anchor の衝突源だった定数 `terminal_operation_id="public-origin-terminal"` は
   2026-08-15 の commit `89723b89` (`feat(t244)`) で
   `"public-origin-terminal-" + sha256(str(tmp_path))` へ変更済み。
   `_origin_public_inputs` を呼ぶ test は 5 本 (行 6564 / 6652 / 6678 / 6698 / 6723)。
   変更前は 5 本すべてが同一 operation_id を異なる payload で使っており、xdist の同一 worker に
   2 本以上載れば必ず衝突した。変更後は tmp_path ごとに一意。
2. `consume_formal_consumer_receipt` に到達しうる test file の閉包は 6 本。
   `test_p3_autonomous_workload_trial.py`, `test_reflux_origin_client.py`,
   `test_reflux_formal_consumer.py`, `test_reflux_origin_ledger.py`,
   `test_reflux_originless_compatibility.py`, `test_trial_registry.py`。
3. 直列単一プロセス走 (6 file, `-n 0`) = **403 passed / 204.78s**。汚染は再現しない。
4. clear fixture を持つ `test_reflux_formal_consumer.py` を外した 5 file 直列走 =
   **353 passed / 210.40s**。clear が衝突を隠している可能性も否定された。
5. 並列 (loadgroup) 4 file 走 = 285 passed / 119.88s。
6. `pytest-randomly` は未導入 (`ImportError: No module named 'randomly'`)。
   本 repo の test 順序はファイル順で決定的であり、ランダム順序による別の衝突は起こらない。
7. 赤の観測履歴は archive worklog (519) と (535) の 2 回のみ、いずれも 2026-08-13。
   例外文言は `operation_id was already used with different payload bytes`。
   2026-08-15 の fix 以降、台帳に再発の記録は無い。

## 攻撃対象の provisional 前提

- (P0) **新設**: 「失敗 anchor の衝突源は `89723b89` で解消済みで、現 main に残る衝突は存在しない」。
  親の provisional 裁定であり最優先の攻撃対象。
- (P1) 共通 `orchestrator/tests/conftest.py` の autouse fixture が最小で、formal consumer state を
  利用する全 test を隔離できる。
- (P2) fixture の before/after clear と、その fixture 無効化を殺す回帰 test が必要十分。

## 成果物影響 (DW-G05)

- 隔離も pin も入れず、かつ (P0) が偽なら、受入全走が順序依存の infra red になり
  tested tip の受入可否を誤って変える。
- (P0) が真なら、残る成果物影響は「将来 operation_id を定数へ戻す変更が入ったとき、
  同じ順序依存 red が無警告で復活する」ことだけになる。

## 分割方針

manager は brief・裁定・変異・受入・記録・land、read-only Codex は plan/review、
workspace-write Codex author は code/test のみ。

## 受入環境

Pegasus login node から `python3 tools/run_tests.py`。場所と memory dispatch は同 tool に委ねる。
