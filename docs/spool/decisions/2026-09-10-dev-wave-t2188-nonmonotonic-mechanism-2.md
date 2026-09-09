---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-10
wave: dev-wave-t2188-nonmonotonic-mechanism
seq: 2
---

## {{D:backoff-nonmonotonicity-is-residency}}. 刻み応答の非単調性の機序は `Backoff_` の滞在分布とする

**決定:** Silo 上の Cicada 型 adaptive backoff で刻みに対する応答が非単調になる機序は、
**歩行がどの `Backoff_` へ居着くか (滞在分布)** である。更新窓が狭いと歩行は高い `Backoff_` へ
暴走し、その滞在先の静的な性能がそのまま throughput になる。刻みは、歩行がどこまで暴走するかを
決める従属変数である。

この判断の射程は **write-heavy・48 スレッド・records 1,000,000・extime 3 秒・1 rep・Pegasus** に限る。
値はすべて非認証であり、variant 採用・headline・formal B-10・floor・fitness に使えない。

**理由:**
- 実測した滞在分布を既測の静的 `T(b)` へ時間加重で混ぜると、6 セルすべてで実測 throughput を
  **−9.1% 〜 +4.7%** で再現する。
- 刻みを 1 µs に固定して更新間隔だけを 10 → 2560 µs へ広げると、`Backoff_` 中央値が
  **88 → 6 µs**、throughput が **2,201,348 → 4,030,122 (1.83 倍)** になる。他の軸はすべて同一である。
- 事前登録した J2 (高域への滞在) は時間加重・event 加重の両方で支持された。
  谷の時間加重 `P(Backoff_ > 100 µs)` は 0.946、最良点は 0.000 である。

**却下した選択肢:**
- **計数ノイズが勾配符号を支配するという説明を主機序に据える** — 事前登録した J1 は不支持だった
  (窓 10 で 0.498、窓 2560 で 0.458、差 +0.040 < 閾値 0.10)。さらに 3 区間で向きが揃わない。
  ただしこれは両条件が重なる低域 (`Backoff_` <= 12 µs の 12 辺) だけの比較であり、
  **計数ノイズの寄与を否定するものではない。**
- **静的曲線を歩行の正解方向ラベルとして採点に使う** — 「動的に `Backoff_`=b のときの性能は
  b で固定した静的性能に等しい」という、まさに検証したい仮定を正解として使う循環になる。
  混合の検算は記述統計に留め、`mixture_assumption_required` を付けた。

## {{D:t2216-negative-conclusion-scope-narrowed}}. 歩行 model の否定的結論の射程を狭める

**決定:** `output/insights/2026-09-02_t2216-adaptive-backoff-nonmonotonicity-mechanism.md` §4-bis の
「素直な滞在説では足りない」という否定的結論は、**混合の仮定が誤っていたのではなく、
model が予測した滞在分布が実測と違っていたことによる。** 滞在分布を実測すれば混合は閉じる。
過去の記録は追記でのみ訂正し、当時の判定は書き換えない。

**理由:**
- 同 §4-bis は刻み 25 µs で実測 1,241,671 に対し 2,827,148 を予測し、相対誤差 130% だった。
  実測滞在での混合は同じセルで比 1.019 (+1.9%) である。
- 同 model が容疑 3 として挙げた「窓あたり commit 数を Poisson としたこと」は、
  時間トリガ窓の Fano を実測して閉じた。谷で **482.8**、最良点で **4.42** であり、
  model が用意した ablation (Fano 2.0 / 4.0) は最良点にしか当てはまらない。
- 同 §2 の「実効更新間隔は `Backoff_` とともに伸びる」は、全走行の実測で確認した。
  名目 10 µs に対し最良点 1.38 倍、谷 **9.11 倍**である。

**却下した選択肢:**
- **旧 insight を書き換えて結論を差し替える** — 絶対規律 7 により、当時の判定は当時の道具で
  得られた事実である。追記による訂正だけを行う。

## {{D:directional-success-is-not-an-accuracy}}. 保存済み `directional_success` を的中率として読まない

**決定:** `tools/pegasus/probes/t2187_adaptive_const_probe.py` の `_directional_success` が返す値は、
**独立な正解に対する勾配符号の的中率ではない。** 機序の判定に使わない。
既存成果物に残るこの値を「符号の的中率」と説明する記録は成り立たない。

**理由:**
- この指標は、適用された action の符号と次窓 throughput 差の符号が一致した回数を数える。
  次 event の勾配は**同じ throughput 差を直前の action で割った量**であり、両者は同じ観測量から作られる。
- 記録済み 468 走行・event 対 359,969 件の分割表で、一致は **99.93%** (食い違い 260 対)。
- 一方、走行ごとの合計は 101,857 = 101,857 で**完全一致する**。
  **合計だけを比べると相殺で一致し、同一性を示したことにならない。**

**却下した選択肢:**
- **走行ごとの合計一致を根拠にする** — 上記のとおり相殺を許す。event 対ごとの分割表が要る。

## {{D:trace-overflow-acceptance-scoped-to-new-cellset}}. trace の取りこぼし受理は新セル集合だけに閉じる

**決定:** `_parse_backoff_trace` の「取りこぼしゼロ・`seq` は 0 から連続」という強制は、
**新しい非単調性セル集合の literal と exact 一致するときだけ**緩める (`allow_overflow` の既定は偽)。
緩めた場合も `updates == retained + dropped`、`retained == min(updates, 65536)`、
`len(events) == retained`、先頭 `seq == dropped`、末尾 `seq == updates - 1`、間が連続、
のすべてを exact に要求する。

**理由:**
- 既存の反実仮想 2 cohort の解析器は、`seq` の 0 始まり連続性と `dropped == 0` を要求し、
  さらに乱数を先頭 event から逐次再生して割当整合性を検査する。
  取りこぼしを全集合へ許すと、**事前登録 SHA が付いた不適格な成果物を producer 側で作れてしまう。**
- 更新間隔 10 µs では 3 秒で最大 21.8 万更新になり、ring 容量 65,536 を超える。
  新集合だけは末尾 slice を受理しないと測れない。

**却下した選択肢:**
- **ring 容量を広げて取りこぼしを無くす** — `patches/cicada-adaptive-dynamic.patch` の変更になり、
  同 patch は事前登録が凍結している。patch sha・build cache key・binary sha がすべて動く。
- **取りこぼしを無条件に受理する** — 上記のとおり既存 cohort の推定対象を壊す。
