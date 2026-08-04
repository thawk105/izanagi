# 壁 1 (campaign を計算ノードで回す経路) の生死確認 — dev-wave 逐語 (2026-08-04)

- `authority: none`
- `default_effect: no-state-change`

CC 合成 campaign の 1 iteration (build → verify → bench) を Pegasus 計算ノードで 1 周
通せるかの生死確認 (`DW-G01`)。**恒久実装は行っていない。** 可変状態の正本は
`docs/worklog.md` の該当エントリと `docs/decisions.md` / `docs/failures.md` の該当項であり、
本ディレクトリは一次資料を凍結するだけである。

anchor = `504ed6d`

| ファイル | 内容 |
|---|---|
| `RESULT.md` | 親による結果の確定 (実測値の正本) |
| `driver/` | 使い捨て driver 一式 (driver / job script / 再現手順) |
| `evidence/run-001/` | request 882490 の progress・依存 build 証拠・計算ノード marker |
| `evidence/scheduler-logs/` | qsub stdout と NQSV 会計サマリ (`.e` / `.o`) |

## この wave が閉じたこと

- **壁 1 を塞いでいるのは transport でも LLM 分割線でもない。**
  Pegasus の実行時 attestation (`effective_clock.samples_mhz`) が build 前に fail-closed で止める。
- **その attestation は登録済み較正自身を通さない。** 参照データの 1 要素 (3080.935 MHz) が、
  同じ較正が宣言する許容帯 [2058.98, 2143.02] の外にある。実行時は「48 コアのうち 1 つでも
  ブーストしていれば不合格」になり、これは再現性のある機器特性ではない。
- **依存 prologue は計算ノードで通る。** pin 済み gflags / glog の build+install は 11 秒で成功し、
  `CMAKE_PREFIX_PATH` を export できた (D87 決定 4 の形がそのまま動く)。
- **計算ノードは単一 NUMA ノードで、`numactl` は存在する。** ログインノードには無い。
- **背景 job セッションからの qsub は F49 (ii) の 3 検査をすべて満たした。**

## この wave が閉じていないこと

- **build / verify / bench の transport 自体は未検証。** attestation で止まったため到達していない。
  肯定・否定いずれの証拠も持たない。
- `pipeline.py` の numactl gate (D36 決定4-4) が S2 verify を Pegasus で塞ぐ件は**静的確認のみ**。
  実機では attestation が先に落ちるため未到達。
- 恒久実装の設計択一 (D131 の (a)/(b)) は未決。裁定へ返す。

## 8c CLI を使わなかった理由

`p3_autonomous_workload_trial.py` の CLI は `--provider fixture` と実 build が排他であり、
Pegasus compute の build opt-in は `claude-headless` provider 専用で LLM transport receipt を
要求する。あの CLI 経由では「LLM を使わずに計算ノードで build する」経路が構造的に存在しない。
そのため fixture をコードとして再利用し、素の proposal を受ける `drive_iteration` を直接呼んだ。
**LLM は経路に一切現れない。**
