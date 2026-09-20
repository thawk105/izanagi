### F975. land の共通 lock 待ち窓を lock 外の provenance 監査が食い潰し、6 wave が 1 時間 26 分 main を進められなかった [資源競合] [手順漏れ]

- 事象: 2026-09-14 05:43:32 の `640e5d431` を最後に、main が **2 時間 30 分以上**進まなかった
  (08:15 時点でも同じ tip)。直前は 05:10 / 05:11 / 05:16 / 05:25 / 05:29 / 05:43 と
  数分おきに進んでいた。同時刻に `tools/dev_wave_land.py` が最大 **12 本**走っていた。
  参加していた 7 wave の実測を合わせると次のとおり。

- **lock 自体は壊れていない。** 排他保持は実測 1 分 27 秒で回っている。
  当初「保持者が枠を跨いで 10 分持ち続けた」という見立てが出たが、根拠が `lsof` の
  1 発のスナップショットだけで保持時間を測っておらず、提案者自身が撤回した。
  **スナップショットで誰が握っていたかは、握りっぱなしかどうかの証拠にならない。**

- **`rc=29` は 3 つの異なる原因で立ち、いずれも provenance の内容違反ではない。**
  ある wave の land log 40 回の実測では、rc=29 が 8 回出てその内訳は次であった。

  | 件数 | reason |
  |---|---|
  | 5 | `provenance full-history audit did not complete authoritatively (rc=16)` |
  | 2 | `provenance audit failed: TimeoutExpired after 480 seconds` (発生時 load average 75.33) |
  | 1 | `main/wave heads or collision paths changed during the provenance audit` |

  **主因は「lock 外の全史監査が完走できないこと」であり、head 移動はむしろ少数である。**
  同 wave は当初、最初に見た 2 回 (どちらも head 移動) から「rc=29 は監査中の head 移動」と
  一般化して報告し、40 回を数え直して自ら訂正した。**少数例からの一般化に注意する。**
- **窓の食い潰しの定量値。** 同 wave の `lock-busy` 27 回のうち、`waited_s` が 180 に達したのは
  **7 回だけ**で、残る **20 回 (74%)** は `window_elapsed_s` が 180 を超えているのに
  `waited_s` はそれ未満であった。最悪は `waited_s=96.368` / `window_elapsed_s=638.545` で、
  窓 180 秒に対し 638.5 秒消費し、lock 待ちに使えたのは 96.4 秒である。
  全史 provenance 監査の所要は load average と強く相関する (ある wave の実測)。

  | load average (1 分) | 監査の所要 | 出所 |
  |---|---|---|
  | 約 35.84 | 268.8 秒 | 別 session |
  | 約 37.97 | 302.1 秒 | 別 session |
  | 約 70 | 419.2 秒 | 別 session |
  | 75.33 | 480 秒で timeout (未完) | 本 wave |
  | 87.94 | 367.148 秒 | 本 wave |
  | 126.76 | 574 秒で完走 (rc=0、`9786 件、新規違反なし`) | 本 wave |

  **監査そのものは通る。落ちているのは所要時間だけである。**
  同じ wave の直近の land は `phase=post-provenance, waited_s=0.007,
  window_elapsed_s=367.148` で、**lock は即座に取れていた** (別 session の 3 点も
  `waited_s` ≤ 0.055 秒)。したがって順番待ちで解けるのは `phase=initial` 型だけで、
  **`post-provenance` 型は負荷が下がるまで誰も通らない。**

  **180 秒の窓に対応する load の閾値は決まっていない。** 本 fragment は当初、
  本 wave の 2 点だけから「約 5.4 秒/load、閾値はおおよそ 40 前後」と外挿していたが、
  別 session の 3 点を足すと同じ外挿は 25 付近を指す。6 点は単調でもなく
  (75.33 で未完、87.94 で 367 秒)、load average 以外の項 (同時に走る受入の本数、
  lustre 側の混み方) が効いている。**単一の閾値を運用の判定器にしてはいけない。**
  当座の運用は「load が下降局面にあるときに 1 本ずつ投げ、
  `window_elapsed_s` を毎回記録して点を増やす」。
- 再発検知: main の先端 commit 時刻と現在時刻の差。30 分以上開いていて `dev_wave_land.py` が
  複数走っていれば本件である。`status=lock-busy` かつ `waited_s << limit_s` かつ
  `window_elapsed_s > limit_s` の組が `post-provenance` 位相の署名、
  `waited_s == window_elapsed_s == limit_s` が `initial` 位相の署名になる。
- **supersede: 2026-09-16** — 恒久対応「未実施」は `0ec8d0faf` (2026-09-14) で実施済み。候補 (a) 窓の起点の移動を D1996 として実装し、`_LAND_LOCK_WAIT_SECONDS` は累積競合待機予算になった (値 180 秒と、監査を lock の外で走らせる設計は不変)。候補 (b) 受領証の再利用は D2044 項 6 で却下。実体は `orchestrator/tests/test_dev_wave_land.py` の `test_cumulative_wait_budget_*` 8 本で、満額補充・絶対期限の復活・reason 文面・窓前の key 省略を固定する。
