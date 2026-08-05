# 事前登録 erratum 3 — 十分性式の射程と `R_restore_bound` の到達可能性 (2026-08-05、[T-471])

- `authority: none`
- `default_effect: no-state-change`
- 本文書は `verdict-preregistration.md` の erratum である。初回凍結文は消さない。
  判定式・語彙・閾値も変更しない。本文書が足すのは**射程の明示**だけである。

## 対象

「grace の読み方と十分性」節の判定式
`G_usable_lower ≥ 5 s + 5 s + R_restore_bound` と、その変数 `R_restore_bound`。

## [T-471] が示した 3 点

### (1) この式は片側の certify 器である

左辺は凍結された代入規則により「実際に使えた時間の**下限**」(`cleanup_elapsed`) に固定される。
右辺は production cleanup が必要とする**予算**である。下限が予算に届かないことは
「予算が足りなかった」ことを意味しない。したがって不等式が偽になっても
**「実 grace が物理的に不足した」の証明にはならない**。成立したときにだけ十分性を certify できる。

### (2) T-399 attempt の判定は `R_restore_bound` の値に依存しない

T-399 authoritative attempt の左辺は `cleanup_elapsed = 5.013 s`。`R_restore_bound ≥ 0` である以上、
`5.013 ≥ 10 + R` は **R の値によらず偽**である。すなわち **R をどれだけ精密に測っても、
この attempt から十分性を certify することはできない**。「R を測れば条件 3 が閉じる」という
見通しは成り立たない。条件 3 を閉じるには、cleanup が実際に 10 s + R 相当の仕事をして
なお完走した attempt (または grace 予算に依存しない復元設計) が要る。

### (3) `R_restore_bound` は「上限」であり、実測では確定しない

凍結文は `R_restore_bound` を `_restore_targets` の**上限**と定義している。この操作は
Lustre 上の file 書込みと `__pycache__` entry の unlink であり、関数内 timeout も latency SLA も
持たない。非定常な分布に対する有限標本の最大値は上限ではない。[T-471] は観測分布を
`R_restore_observed` の名前で測り、**凍結記号 `R_restore_bound` は `null` のままとした。**
凍結分岐 (`R_restore_bound = null` ⇒ 十分性 = `UNKNOWN`) は維持される。

## 予算に含まれていない項 (同名で呼んではならない)

`5 s + 5 s + R_restore_bound` は signal 受信から「repo が安全な状態に戻る」までの全時間ではない。
次は凍結 R の範囲外であり、`R_restore_bound` の名前で指してはならない (同名識別子の二義化の禁止)。

| 別名 | 実体 | 根拠 |
|---|---|---|
| `H_stop_overrun` | `_stop_process` の `wait(timeout=5)` × 2 の期限超過分。10 s は timeout 引数の和であって wall-clock 上限ではない | `tools/mutation_harness.py:1098-1113` |
| `H_head` | 復元直後の `_assert_head`。`_repo_head` 経由で git subprocess を起動する | 同 :1330-1332, :605-608 |
| `H_exit` | signal handler 復旧、例外 unwind、lock close、stderr write | 同 :2084-2101 |
| `D_delivery` | PBS warn signal の要求時刻から Python parent 受信までの遅延。未計測 | — |

合成量を書くときは `C_repo_known_safe = H_stop_actual + R + H_head` のように別名を用いる。

## 復元の fault model (射程の明示)

`_restore_targets` は `write_text` 後に同一 node から `read_text` するだけで、file の fsync も
親 directory の fsync も行わない (`tools/mutation_harness.py:767-788`)。遅延できるのは
SIGINT / SIGTERM だけで SIGKILL は防げない (:733-764)。一方 T-399 の canary は
fsync + atomic replace + directory fsync を行う別契約である
(`output/insights/2026-08-03_t361-t362-cluster-probes/driver/signal_probe.py:63-103`)。
**canary の耐久性を production の `write_text` へ転用できない。**

本式が支えうるのは「live node・Lustre client 生存・`_restore_targets` return 後に process だけが
kill される」という限定された契約までであり、書込み途中の SIGKILL・node 障害・power loss に
対する durability は支えない。

## 判定への影響

初回判定 (mitigation 構成は捕捉可能、十分性 = `UNKNOWN`) は**変更しない**。
条件 1〜4 の当てはめも不変である。本 erratum が足したのは、
十分性 `UNKNOWN` が「まだ測っていない」ではなく
**「この attempt からは R の値によらず certify できない」**という、より強い射程の明示である。
