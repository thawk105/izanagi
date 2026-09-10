# 親の独立実測 — 段 3 の子所見に対する裏取り

本 wave の親が worktree `dev-wave-t419-generation-migration` (base main `b7142712`、
submodule pin `511c9538`) で取得した実測。子の報告を額面どおりに採らないための独立確認。

## M-1 実行時の受理帯は g1 と g2 で同一である

`execution_guard.effective_clock_comparison_passes` は期待列の**中央値だけ**を使い、
帯検査は**観測列にのみ**適用する (`execution_guard.py:405-414`)。

| 世代 | n | median | tolerance_pct | 帯 | 期待列の帯外 |
|---|---:|---:|---:|---|---:|
| g1 | 48 | 2101.0 | 2.0 | [2058.98, 2143.02] | **1 件** (3080.935) |
| g2 | 48 | 2101.0 | 2.0 | [2058.98, 2143.02] | **0 件** |

**帯が同一なので、活性化は実行時の合否を変えない。**

`compare_profiles` の 21 field のうち g1/g2 で値が違うのは 4 件だけで、いずれも合否を変えない。

- `tsc.raw_samples_mhz` / `tsc.median_mhz` — `round(median)` 比較で両者 2100 (`env_attestation.py:942-949`)
- `effective_clock.samples_mhz` — 帯が同一
- `effective_clock.method` — M-2 を参照

## M-2 `effective_clock.method` の比較は恒真ゲートである

`_recorded_verdict` は当 field を「expected と observed が**ともに非空 str**」だけで pass にする
(`env_attestation.py:935-939`)。値の一致を見ない。

- g1 の期待側 = `"proc-cpuinfo"` (素朴法)
- g2 の期待側 = `"proc-cpuinfo-rotating-min/k5/interval-ns50000000/sysfs-affinity-intersection-evenly-spaced-v1"` (方式 α)
- 実行時 observed = `EFFECTIVE_CLOCK_METHOD` = 方式 α (`env_attestation.py:38-42,680`)

**g1 が active である限り、receipt は「期待は素朴法・観測は方式 α」という実体不一致を
pass と記録し続ける。** 恒真ゲート自体の是正は受理集合を縮小する変更であり、段 4 で scope を裁定する。

## M-3 壁 1 (実行時 attestation) は g1 のままでも構造上開いている

- certified 経路 `execution_guard` は `_env_attestation.probe` (方式 α) を使い
  `compare_profiles` で照合する (`execution_guard.py:580,611-612`)。
- `EFFECTIVE_CLOCK_METHOD` を要求する consumer は probe 自身 (`env_attestation.py:680`) だけで、
  登録較正側の `method` が素朴法でも `calibration_verify` は拒否しない (method 検査が無い)。
- 一次資料 `output/insights/2026-08-04_t419-probe-causality/README.md` の 2x3 判定表は、
  方式 α が **静穏時 9/9 通過・過剰拒否 0** であることを、
  **凍結較正の中央値 2101.0 の帯そのもの**に対して実測している。

**したがって「g1 が active だから計算ノードで何も走らない」は成り立たない。**
親が段 3 レンズ A へ渡した対案 (X) の前提はこの実測で崩れる。
ただし本 wave は certified campaign の実走を測っていない。

## M-4 移行前 baseline (凍結 floor protocol)

復元後の g1 木で `output/s8b-freeze/floor_protocol.json` を検証した。

| 検証 | g1 (現状) | g2 (一時変異) |
|---|---|---|
| `validate_protocol` (歴史) | OK | OK |
| `validate_protocol_against_current` (live) | OK | **拒否** (`protocol.contract_sha256 と resolver が返した env 契約が不一致`) |

live 拒否は本 wave が導入する新しい縮小であり、既存の赤の露出ではない。

## M-5 【レンズ B-02 の反証】silo の完全検証入口は既に赤である

レンズ B-02 は「g1 の silo 証拠は g2 活性化後に公開 `verify-result` で
`current calibration/pin binding mismatch` になる」と主張した。
`validate_current_bindings` が `env_contract.lookup("pegasus")` の current contract と
照合する点 (`silo_ladder_rung1.py:3564-3572`) は親も独立に確認した。

**しかし当該入口は今日すでに赤である。** 実走:

```
$ python3 -m orchestrator.campaign.silo_ladder_rung1 verify-result \
    --json output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json
{"failures": [{"detail": "correctness provenance values mismatch", "reason_code": "schema"}], "ok": false}
```

失敗は `validate_evidence` 段 (`silo_ladder_rung1.py:1393`) で、
`correctness_provenance["ccbench_pin_full"] != PIN` による。実測値:

- module 定数 `PIN` = `511c9538e4e8efa54b45cda62e72389ed3b706ec` (`silo_ladder_rung1.py:57`)
- 証拠側 `ccbench_pin_full` = `d706650cdb31e442bef45b9b4216951d4fb40969`

短絡するため `validate_current_bindings` には到達しない。

**したがって B-02 の「今動いている能力が壊れる」という severity は成立しない。**
正しい言い方は「同じ入口に 2 つ目の current-binding 不一致が加わる」である。

## M-6 【DW-G03】歴史検証器と live 検証器の分離は独立 2 例を満たす

M-5 は、**契約世代とは独立の pin 前進 (ccbench PIN) が、既に同型の破綻を 1 度起こしている**
ことを示す。本 wave の契約世代前進は 2 例目である。producer も consumer も異なる。

- 例 1: `silo_ladder_rung1` — module 定数 `PIN` の前進が凍結証拠の完全検証を赤にした (実現済み)
- 例 2: `s8b_floor_campaign` / `certified_writer_admission` — 契約世代の前進が
  凍結 protocol の live admission を赤にする (本 wave が導入)

`DW-G03` の閾値 (同型欠陥が異なる producer/consumer で独立に 2 件) を満たすため、
**「凍結成果物は記録時の値で検証し、live 適格性は別 API で検査する」の族一般化は正当化される。**
