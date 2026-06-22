# P2-3: critic が leading indicators から silo の性能差を設計選択に帰属

- **日付:** 2026-06-22 (Phase 2 P2-3, env=linux-baremetal)
- **種別:** critic エージェントの実証 (leading indicators → 設計選択への帰属 → 次手)
- **入力:** P2-2 を leading indicators 付きで再計測した 3 workload × 8 genome の WAL
  (fitness は元 P2-2 と再現一致、最速構成不変)。digest = `orchestrator/critic/digest.py`
- **位置づけ:** roadmap §3.5 (throughput スカラーだけでは探索が停滞する → leading indicators)。
  critic は読み取り + 解析のみ (実装・fitness を書き換えない)。出力は次の variant 生成への指示

## なぜこれをやるか (P2-3 の狙い)

throughput だけ見ると「BACK_OFF=0 が速い、no-wait は workload 次第」で終わる。**なぜ**速いか
(機序) を leading indicators (abort_rate / latency_ns / llc_miss_rate / ipc) で説明できないと、
次にどの軸を攻めるかが決まらず探索が停滞する (Jitskit)。critic はこの帰属を行う。

## critic の帰属 (要旨。全文は critic エージェント実行ログ)

### BACK_OFF=1 はなぜ遅いか — abort は減らせている。殺しているのは latency と ipc
- backoff は **contention 低減には成功** (abort_rate: read 15.6→4.5% / balanced 65.3→18.1% / write 59.7→12.1%)。
- **にもかかわらず throughput が落ちる** (限界効果 read -77% / balanced -61% / write -22.5%)。原因は
  **ipc が全 workload で 1.4–1.6 → 0.4–0.5 へ崩壊** + latency 増 (read 5.7→25μs)。コアが backoff 待ちで
  実命令を発行できていない = 典型的 over-throttling。llc_miss_rate も微増で cache でも得していない。
- **機序の裏付け:** backoff の損は abort baseline が高いほど**小さい** (write -22.5% < read -77%)。abort が
  元々多い workload では待った分だけ無駄 retry を実際に削れて相殺、abort の少ない read では純損。
- → **BACK_OFF=1 (8 genome 中 4) は全 workload で利得ゼロ。恒久的に探索から外してよい。**

### no-wait 政策 (L=即abort / T=tictoc retry) — workload で最適が反転する
- **read-heavy: 無差** (限界効果 +0.4%、最速 2 構成の差 0.50% も noise floor 2.28% 内)。L/T 区別不能。
- **balanced: L 優位** (+19.6%)。L は ipc 1.62 と高命令発行で稼ぐ (abort は高いが回せる)。
- **write-heavy: T 優位** (+12.7%)。T は abort (50.8→21.0%) と latency を同時に下げる。
- → **L と T の最適が balanced↔write で反転。** 「単一の no-wait 政策が全 workload で最適」は否定される。
  critic なしの「全 workload で最速 genome を 1 つ選ぶ」探索はこの反転を見落とし片方で取りこぼす
  (= critic の ablation 価値)。

### WAL=1 — 純損、書込比率に単調比例
- 限界効果 read -1.9% (noise内) / balanced -6.8% / write -13.4%。abort 不変・latency/miss 増 →
  正しさや contention でなく純粋にログ書込 I/O のコスト。性能探索軸でなく永続化要件として外生固定すべき。

## critic の次手 (recommend / avoid)

- **recommend:** BACK_OFF=0 固定 (空間が即半分)・WAL=0 既定・no-wait は workload 出し分け
  (balanced=L / write=T / read=任意)。**新軸の提案: 中間/適応 backoff** (高 contention 時のみ短く発動) —
  現 8 genome に無い未探索帯で、「ipc を 1.0 未満に落とさず abort を下げられるか」が監視点。
- **avoid:** BACK_OFF=1 全 genome 再訪不要 / WAL=1 を性能目的で試さない /
  read-heavy で L vs T を作り分け続けるのは情報利得ゼロ。

## critic が明示した uncertainty (honest-by-construction)

- read-heavy 最速 2 構成 (8.49M vs 8.45M, 0.50%) は noise floor 内 → **順位を主張しない**。
  read の no-wait/WAL 限界効果も noise 内で符号すら不確定。
- 各 genome は 1 round 計測 (CV は round 内分散で run 間再現性でない)。floor 近傍の差は要再測。
- 限界効果は周辺化平均で**交互作用項を分離していない**。balanced の L/T 差は tictoc validation 経路
  そのものの寄与を含み、「待ち政策の違い」だけに帰属するのは過剰単純化。
- 中間 backoff の挙動は**完全に未測定 (外挿)**。on/off 2 点間が単調かは不明。
- skew0.9 / 48thread / 1m の 1 動作点に限った帰属。

## P2-3 完了条件との対応

「critic が leading indicators から具体的な次手を出せる」を達成。critic は throughput 単独でなく
abort/latency/ipc/miss の組で機序を推定し、設計選択 (BACK_OFF / no-wait / WAL) に帰属させ、
recommend/avoid/uncertainty を返した。**ablation の原理** (L/T 反転の見落としを critic が防ぐ) も提示。
定量的 ablation (critic 誘導探索 vs ランダムの到達 iteration) は P2-5 の主実験で行う。
