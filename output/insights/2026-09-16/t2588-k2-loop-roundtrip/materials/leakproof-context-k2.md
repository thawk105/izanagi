# Coder Context (K2 射影) — Phase 3 段 4 / silo-backoff-magnitude

本文は親が `src/coder-leakproof-context.md` から作った **K2-compatible な射影**である。
K0/K1 向けの「外部知識を参照するな」という禁止条項は、K2 では宣言済み知識の利用が許されるため
**射影から外してある**。代わりに、実際に走る配線規模を現物へ合わせて訂正してある (下の「訂正」節)。

---

## Background: CCBench と backoff 軸

**CCBench** は並行性制御 (Concurrency Control) のベンチマーク。SILO, Masstree, TicToc, Cicada などの
アルゴリズムが提供され、それぞれの「abort を許す代わりに restart を速くする」戦略を測る。

**Cicada** は in-memory OLTP 用の CC の一種で、abort 時に adaptive exponential backoff を使う。
各トランザクションが restart の前に待機時間を挟み、その間に競合が落ち着くのを期待する。

**SILO** は Cicada と似た in-memory OLTP CC だが、backoff はより単純である。

**backoff 軸** は CCBench の SILO の backoff パラメータを変えるもの。
「abort 後の待機時間が長い / 短い」で throughput と latency の trade-off が生じる。

## 段 4 の目標

backoff 値を調整して **baseline より性能が改善するのか**、それとも **baseline が既に最適に近いのか**
を検証する。coder は planner の方向ヒント (値ではなく「増やす」「減らす」「両方試す」) を受けて
具体的な backoff 値を提案する。

## backoff の直感

- **abort が多い (contention が高い) workload**: abort 後、競合相手が同じ resource へ急いで
  アクセスし直す可能性が高い。少し待つことで競合相手の実行完了を期待でき、競合が減って
  throughput が上がりうる。
- **abort が少ない (contention が低い) workload**: abort 自体が稀なので待機時間を増やす利点は薄く、
  待機は latency penalty として効く。待機時間が短い方が throughput が上がりうる。

## Cicada の適応機構 (参考)

Cicada は実行中に abort 率を観測して backoff を自動調整する (abort 率が高ければ増やし、低ければ
減らす)。この適応は workload ごとに収束する傾向を持つが、最適値は workload の特性に依存する。
段 4 は「Cicada の適応では到達しない値」や「別の値の方が性能が出る」可能性を調べる。

---

## 訂正: 実際に走る配線規模 (現物から)

`src/coder-leakproof-context.md` の "Measurement Setup" 節は
`1m_records / t48_threads / extime3 / 3 runs` と書いているが、**本 loop が実際に走らせる規模は
これとは異なる。** 現物 `orchestrator/campaign/p3_s4_loop.py` の `default_perf()` は次である。

| 項目 | 値 |
|---|---|
| records (`ycsb_tuple_num`) | 100000 |
| threads (`thread_num`) | 4 |
| read ratio (`ycsb_rratio`) | 50 |
| zipf skew (`ycsb_zipf_skew`) | 0.9 |
| read-modify-write (`ycsb_rmw`) | false |
| 実行時間 (`extime`) | 1 秒 |
| 繰り返し (`reps`) | 2 |

これは kickoff と同じ**配線規模**であり、性能比較用に calibrator が決めた規模ではない (規律 4)。
固定フラグは `NO_WAIT_LOCKING_IN_VALIDATION=1`、`NO_WAIT_OF_TICTOC=0`、`WAL=0`。

## 測定の手順

1. **Build:** 提案値を hole へ挿入して build する (trace 版と perf 版の 2 本)。
2. **Verify:** verifier が correctness trace を読み、serializability を検査する。
   **anomaly が出た候補は即 reject であり、性能は測られない。**
3. **Bench:** 上の規模で計測し、繰り返しの中央値を throughput とする。
4. **Result:** verdict と leading indicators (throughput / abort 率 / latency / LLC miss 率 / IPC) が返る。

## 実装の制約 (受理文法)

- 編集面は `include/backoff.hh` の marker `silo-backoff-magnitude` の hole 1 箇所だけである。
- `implementation` は `double now_backoff = <数値リテラル>;` の**ちょうど 1 文**とする。
- 初期化子は**接尾辞なしの strict C++ numeric literal 1 個**だけとする。
  計算式・関数呼び出し・括弧・三項演算子・条件・追加の文は受理文法が拒否する。
- `value` は有限な整数 1..1000 とし、`implementation` の literal と**数値が一致**しなければならない。
  不一致は harness が AttributionMismatch で止める。
- `implementation` の中に `//`、`/*`、行末 backslash を書かない。説明は `justification` へ書く。
- stock 枝、検証、測定、identity、hook は編集対象ではない。

## whiteboard の意味

whiteboard には評価済み提案が**抽象で**記録される (方向・magnitude・結果・delta)。
具体値と機序は載らない。本 iteration の whiteboard は空である (この campaign での評価履歴が無い)。
