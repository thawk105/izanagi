# 結果の確定 — 壁 1 の生死確認 (2026-08-04)

- `authority: none`
- `default_effect: no-state-change`

本ファイルは実測値の正本である。可変状態の正本は `docs/worklog.md` の該当エントリと
`docs/decisions.md` / `docs/failures.md` の該当項であり、ここは一次資料を凍結する。

anchor = `504ed6d` (main), branch = `worktree-wave-a-transport-smoke`

## 判定

**壁 1 は越えられていない。build に一度も到達しなかった。**
ただし**塞いでいる原因を特定した**。原因は transport でも LLM 分割線でもなく、
**Pegasus の実行時 attestation が、登録済み較正自身を通さない述語になっている**ことである。

## 実測 (request 882490.nqsv, bnode002)

| 段 | 結果 |
|---|---|
| qsub 投入 | rc=0、`Request 882490.nqsv submitted to queue: gen_S.` |
| ジョブ開始 | 投入 7 秒後 (08:50:53 → 08:51:00) |
| 依存 prologue (gflags/glog build+install) | **成功**。11 秒 |
| leg A = `legacy+s2` | **例外で停止**。`ExecutionGuardError`。build 未到達 |
| leg B = `legacy` 単独 | **例外で停止**。同じ `ExecutionGuardError`。build 未到達 |
| driver rc | 1 |
| ジョブ全体 | rc=1、Elapse 20 秒 |

`build_done` / `verify_done` / `bench_done` はどの脚でも WAL に 1 件も書かれていない。
**したがって本 wave は build / verify / bench の transport について肯定的な証拠を持たない。**

## 停止した理由 (一次資料 = `evidence/run-001/driver-progress.jsonl`)

両脚とも `env_attestation` → `execution_guard.attest_and_build_receipt` で停止した。
失敗した比較はちょうど 1 件、`effective_clock.samples_mhz` である。

```
expected median = 2101.0   tolerance_pct = 2.0   許容帯 = [2058.98, 2143.02]
observed idx 34 = 3076.13  ← 帯の外
expected idx 40 = 3080.935 ← 参照側にも帯の外の値がある
```

`execution_guard.py` の比較述語は、期待サンプル列の**中央値**を中心に据え、
**観測サンプルの全要素**がその ±`tolerance_pct` に収まることを要求する
(添字ごとの対応比較ではない)。

### 決定的な事実: 登録済み較正は自分自身の判定を通らない

`output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json` の
`attestation_profile.effective_clock.samples_mhz` を**観測値として同じ述語にかけると、
index 40 (3080.935) が許容帯を外れて不合格になる**。参照データが自分自身の受理条件を
満たしていない。

物理的な意味は単純である。48 コアのうち**サンプリング時にたまたま 1 コアがブーストしていた**
状態が較正へ焼き込まれており、実行時にも「どれか 1 コアがブーストしていれば不合格」になる。
どのコアがいつブーストするかはスケジューラと熱の都合であり、**再現性のある機器特性ではない**。

## 副次的に確定した環境事実

- **計算ノード bnode002 の NUMA ノードは 1 個だけ** (`available: 1 nodes (0)`、48 CPU が node 0、
  127476 MB)。`numactl --interleave=all` は交互配置する相手がいないため実質的に恒等である
- **計算ノードに `numactl` は存在する** (`/bin/numactl`)。**ログインノードには存在しない**
- したがって `env_contract.py` の Pegasus 契約 `numactl=()` には実質的な根拠がある

### ただし S2 verify は別の理由で塞がっている

`pipeline.py` は「S2 相当 (`fullscale_isolated=True`) を含む verify 構成で `numactl` が空なら
build 前に `ValueError`」と定める (D36 決定4-4)。Pegasus 契約は `numactl=()` なので必ず発火する。
**gate が見ているのは「numactl prefix が非空か」という代理条件**であり、本来の目的である
「verify と bench でメモリ配置を揃える」は**単一 NUMA ノードでは自明に満たされている**。
今回は attestation が先に落ちたため、この gate には到達していない (静的確認のみ)。

## F49 (ii) 投入有効性検査

| 検査 | 結果 |
|---|---|
| (a) 計算ノード側が書いた marker の実在 | **合格**。`compute-visible.json` = `{"pbs_jobid":"0:882490.nqsv","hostname":"bnode002"}` |
| (b) `qstat` で request が可視 | **合格**。STT=PRR で可視、権限系エラーなし |
| (c) 終了後の PBS 会計痕跡 | **合格**。`izanagi-wave-a-smoke.e882490` に NQSV 会計サマリ (Elapse 20S) |

## この wave が変えていないもの

`dispatch_compute.py`、`TASKS`、transport policy、env 契約、attestation 述語、
`pipeline.py` の numactl gate、既存の受理集合はいずれも未変更である。
新規追加は本 insight 配下の使い捨て driver 3 ファイルと証拠だけである。

**正しさゲートは 1 つも緩めていない。** attestation で落ちたことを「通った」と書き換えず、
numactl を偽装せず、verify 構成を弱めていない。

## 変異 matrix

対象外。受理集合を変える実装差分がなく、gate も検査も新設していない。
