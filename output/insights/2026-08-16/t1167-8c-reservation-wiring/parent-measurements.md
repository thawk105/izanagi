# 親の実測 — [T-1167] 8c launch path の allocation provenance

2026-08-16、worktree `dev-wave-t1167-8c-reservation-wiring`。
子の結論と独立に親が測った値だけを置く。子の逐語は `verbatim/` にある。

## 1. `check_reservation` の実 call site

`grep -rn "check_reservation" --include=*.py` を repo 全体に対して実行 (worktree 群を除外)。
非テストの hit は 3 件、系統は 2 つ。

- `orchestrator/qualification/t126_driver.py:901`
- `orchestrator/campaign/s8b_oracle_driver.py:921`
- `orchestrator/campaign/s8b_floor_campaign.py:4858`

8c launch path (`orchestrator/campaign/p3_autonomous_workload_trial.py`) からの hit はゼロ。
**依頼の前提は正しい。**

## 2. 契約が要求する symbol は存在しない

`orchestrator/campaign/reservation.py` の top-level def を列挙したところ、
`check_reservation` (218) と `is_reservation_required` (273) はあるが
`single_process_required` は無い。契約が `allocation_consumer` として指すのはこの module である。

## 3. C12 の 4 入力を実 tree に対して評価

評価器自身の helper を使って `run_trial` からの到達集合を取った。到達 call は 179 件。

| 要求 | 実測 |
|---|---|
| `lookup` が到達集合にある | 無い |
| `attest_and_build_receipt` が到達集合にある | 無い |
| `single_process_required` が到達集合にある | 無い |
| `single_process` / `allow_resume` が属性集合にある | 無い |

`reservation.py` 側の def 集合にも `single_process_required` は無い。
したがって C12 は**最初の関門** (environment / guard) で落ち、allocation 節へ到達しない。

## 4. 現在の C12 は述語が走っていない

契約 JSON の 12 条件すべてが `machine_checkable: false`。registry を実 HEAD に対して走らせた結果、

```
C12: PredicateStatus.EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable
```

これは `_evaluate_undefined` の経路であり、`_evaluate_c12` は実 tree に対して一度も走っていない。

## 5. 反転したときの実測値 (契約改訂側へ渡す値)

契約 row を in-memory で反転し、実 HEAD の blob に対して `_evaluate_c12` を直接実行した
(repo は変更していない)。

```
C12 if machine_checkable flipped -> PredicateStatus.UNSATISFIED / environment-contract-consumer-absent
```

**この reason は誤りである。** 指している 2 つの consumer は pegasus 経路で実際に走る (§6)。
反転は赤を出すのではなく、実在する強制を「不在」と報告する。

## 6. 8c の実行 chain

```
p3_autonomous_workload_trial.run_trial:2726
  -> drive 既定 = p3_s4_loop_trigger_gating.drive_iteration:718   (:2774-2775 で解決)
  -> loop.run_campaign                                            (:70 で import、:595 で call)
  -> loop._authorize_measurement:59
       :66 execution_guard.require_certified_writer_authorization
       :76 execution_guard.attest_and_build_receipt
```

`env_contract.lookup` は `p3_s4_loop_trigger_gating.py:101` の `_lookup` 別名を
`_admit_env_contract:324` が呼ぶ。

**訂正 1 (親 brief の誤り):** 当初 brief は `lookup` が `loop.py:68` で走ると書いたが誤り。
`loop.py:66` は writer authorization、`:76` が attestation で、`lookup` は trigger gating module 側。

**訂正 2 (親 brief の誤り):** 「8c は attestation を通る」は pegasus 契約に限る。
`env_contract.py` の linux-baremetal は `attestation_mode="none"` かつ
`IsolationPolicy(single_process=False, allow_resume=True)` であり、
`_authorize_measurement` は attestation へ進まず return する。
当初の二分はこの経路を落としていた。段 3 レンズ A の指摘を実測で確認した。

## 7. `check_reservation` が実際に照合するもの

本文を読み下した結果、照合しているのは 4 つだけ。

- `PBS_JOBID` env と binding の一致 (scheduler 由来なので権威あり)
- `/proc` から読む boot ID と binding の一致 (権威あり)
- `scheduler_started_epoch` が未来でないこと
- 残時間が `required_s + safety_margin_s` を満たすこと

**照合していないもの:** `host`、`script_sha256`、`nonce`。binding に載るだけで何とも突き合わせない。
プロセス単独性も一切証明しない。よって配線しても得られるのは *allocation binding* であって、
C12 が名前で謳う single-process exclusivity ではない。

**この権威不足は既に裁定済みの別タスクが所有していた**ため、本 wave では新規起票しなかった。

## 8. 供給側 launcher

`IZANAGI_RESERVATION_*` を export する production launcher は `tools/pegasus/` 配下の
床値 campaign と t126 qualification の 2 本だけで、8c 用は存在しない。
したがって今 fail-closed 検査を置けば、捏造 fixture だけが通り正当な計算ノード実行は落ちる。

## 9. 並行 wave の所有面

起動時と裁定直前の 2 回確認。契約 JSON・評価器・凍結世代記録は稼働中の別 wave が所有していた。
本 wave はこれらを 1 byte も触っていない。
