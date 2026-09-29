---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: dev-wave-ro-gc-publish
seq: 3
---

## {{D:cicada-ro-commit-mainte-variant}}. Cicada の read-only commit でも `mainte()` を通す variant と、その検査・計測の組み方

**決定:**
1. Cicada の ro commit で GC の公開を進める変更は、ro commit の後始末 (`read_set_`・`node_map_` を消した後、`return true;` の前) で既存の `mainte()` を呼ぶ形にする (`patches/cicada-ro-gcflag-variant.patch`、macro `IZANAGI_CICADA_RO_GCFLAG`、既定 0)。ro の rts・ThreadRtsArray・版の選び方は変えない (固定 snapshot の意味は不変)。他 thread が代わりに flag を立てる代行は採らない。
2. 版の回収の安全を担うのは per-thread の rts slot を tx の間変えないことで、GC flag の時機ではない、を前提にする。根拠は小モデル (`tools/vhash_forwarding_model/ro_gc_publish.py`) の 5 構成 × 6 腕の全探索 (ro の途中で flag を立てても違反 0、slot を tx の途中で上げる・∞ にすると違反) と、md_14 の実測。YCSB (delete なし)・`group_commit=0` の範囲に限る。
3. 計器あり・計器なし・trace の 3 build で同じ ro 手続き生成を使うため、workload patch (`patches/cicada-ro-gcflag-workload.patch`、macro `IZANAGI_CICADA_ROGC_WORKLOAD`) を新設し、vlife 側の ro 書換えと長い tx 用 macro は使わない。
4. Cicada の trace を判定器に掛けたときの受理は「判定器 rc ∈ {0, 3}・巡回 0・integrity の数値項目がすべて 0・判定器の txn 数 = 実行の commit 数・`READ_WTS_MISMATCH` 0」とし、`integrity.clean` を要求しない。Cicada には証拠面 (X/P/I) が無いので `clean` は常に偽になる。結論は「巡回なし (上限 indeterminate)」と書き、certified とは書かない (md_14 の検査起動器と同じ受理)。variant の経路を踏んだ証拠として計数 macro (`IZANAGI_CICADA_RO_GCFLAG_COUNT`) の flag 立て回数 > 0 を要求する。
5. 性能の比較は、各条件の stock と variant を同じ job・同じノードで均衡順序 (AB BA AB BA AB BA) に対で走らせ、対ごとの比で示す。

**理由:**
- md_15 が、ro commit が flag を立てないことによる公開の停止・遅れを観測した (T-2911 の根拠)。`mainte()` 全体を呼ぶのは Cicada の「commit・abort の後は `mainte()`」の規則に ro を揃える最小の形で、ro だけを続けた worker の gc queue も処理される。
- 実測 (一次資料 `output/insights/2026-09-29/vhash-readonly-gc-publish/README.md`): 長い ro 1 本で stock の公開は 36/36 走で 0 回、variant で 289〜299 回 / 3 秒。throughput の比は長い ro で 1.56〜16.83、長い ro なしで 0.964〜1.073。trace build 24 走で巡回 0。

**却下した選択肢:**
- flag だけを立てる形 (GC 実行を含めない) — 小モデルでは安全だが、ro だけを続けた worker の gc queue が処理されない。効果の分解は測っていないので、Cicada の規則に揃える方を採った。
- 他 thread (leader) が ro 中の worker の flag を代わりに立てる — worker が参照を手放したかを leader は知らず、安全条件の根拠を作り直す必要がある。
- ro の途中で slot を新しい MinWts−1 へ上げて境界を進める — snapshot を動かす変更で、固定 snapshot を要求する ro を壊す。小モデルでも、途中の flag と組むと回収に届く。
- 受理に `integrity.clean` を要求し続ける — Cicada では到達不能 (F110 の型)。
