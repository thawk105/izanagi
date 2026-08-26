---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t826-acceptance-closure-split
seq: 2
---

## {{D:acceptance-shard-three}}. 受入経路の shard 数を明示 3 にする — D724 の「床が動かない」は排他鎖の細分化で失効した

**決定:** `tools/dev_wave_wait.py` の acceptance 経路が launcher を起動するとき、次を**すべて**
満たす場合に限り子プロセスの環境へ `IZANAGI_ACCEPTANCE_SHARDS=3` を入れる。

- 呼び出し元が同変数を設定していない (空文字は `tools/run_tests.py` と同じく未指定として扱う)。
- site が Pegasus LOGIN である。
- `orchestrator.campaign.queue_state.dispatch_possible()` が `ENA=ENA` かつ `STS=ACT` を
  観測して True を返した。**観測不能・例外・契約外の戻り値では注入しない** (run_tests は
  観測不能を可用側へ倒すが、本注入は逆へ倒す)。

**既定値 (`tools/run_tests.py`) は変えない。** D838 のユーザー裁定により当該 file を変更した
wave は受入を通せないためである。したがって焦点走やその他の経路は従来どおり K=2 / K=1 に解決する。

**理由:**

- **実測で pytest wall が 43.6% 縮んだ。** 同一 tip (実装差分ゼロ) で shard 数だけを 2 と 3 に
  切り替えた 2 走。最遅 shard の pytest wall は 285.52 秒 対 160.92 秒、最遅 worker は
  211.99 秒 対 101.70 秒、残差は 73.53 秒 対 59.22 秒。差 124.60 秒は D1019 が記録した
  走間ばらつき 32.27 秒の 3.9 倍である。
- **直列総仕事量そのものが 1.53 倍縮んだ** (16609.9 秒 対 10830.1 秒)。1 node あたりの worker 数は
  どちらも 48 で同じなので、これは容量の増加ではなく node あたり総負荷の低下による競合の減少である。
  K は容量を増やすだけでなく仕事量を減らす。
- **D724 が K=3 を却下した根拠は失効した。** 却下理由は「床が動かないのに request 数と故障面だけ
  増える」であり、その床は D710 実測時点の排他鎖 103.0 秒であった。同鎖は
  「受入の real-repo 排他鎖を資源別 RW lock へ細分化する」変更で取り除かれ、本測定の
  `group_to_workers` でも `real-repo` は 40 worker へ分散している。
- **K=3 で既に単体テストの床に達している。** 最長単体は K=2 で 165.17 秒、K=3 で 100.32 秒。
  K=3 の wall 160.92 秒は最長単体 100.32 秒 + 残差 59.22 秒でほぼ説明できる。したがって
  これ以上 K を上げる余地は、単体テストを速くしない限り存在しない。K の受理値が
  `{1,2,3}` に留まっていることと物理的な頭打ちが一致している。
- **queue 条件は D724 の配置契約を守るために要る。** 明示指定は login admission の配置判定を
  迂回するため、queue が使えないときに従来ローカル実行できた受入まで rc=16 で終端しうる。
  queue が可用と観測できたときだけ注入すれば、queue 不可時は従来経路へ戻る。
- 受理集合は変わらない。2 走とも collected 17455 で、選択 node の合計も一致した。

**残す限界を決定の一部として明記する。**

- 受入 receipt は shard 数を証明しない (D724 が明示的に受容した既知限界)。K=3 で走った証拠は
  受入 child log 中の `IZANAGI_ACCEPTANCE_SHARD_ARTIFACTS_V1` 行であり、`log_sha256` が束縛する。
- queue が可用でも login admission がローカル実行を選べた場合、本注入は dispatch を選ばせる。
  D724 の「どこで走るか は変えない」に対する逸脱はこの 1 点に限る。受入全走は 48 worker を要し
  bounded local 予算 (min 4 GiB) に収まらないため、実運用でこの分岐が起きる余地は小さいと見るが、
  **これは推定であって実測していない**。
- 注入判定は `_default_launch_launcher` の内部にあり、acceptance 以外の caller が同関数を
  再利用すると漏れる。現在 production の caller は acceptance 1 本だけである。

**却下した選択肢:**

- **既定値を 2 から 3 へ変える** — 実装は `tools/run_tests.py` の 1 行だが、D838 のユーザー裁定に
  より当該 file を直す wave は受入を通せない。判断はユーザーへ返す。
- **queue 条件を付けずに注入する** — queue 不可時にローカル退避を失う。段 6 の 2 レンズが
  独立に指摘し、実装子自身が `qstat -Q preflight rc=1` を実際に踏んだ。
- **K を 4 以上にする** — 受理値が `{1,2,3}` に閉じており、かつ K=3 で既に単体の床に達している。
- **duration 重み割付を併せて入れる (D1019 の再訪)** — D1020 の引き金は K=2 の makespan shard では
  成立するが、K=3 では仕事量を完全に均衡させても容量 75.2 秒が最長単体 100.32 秒を下回らず、
  makespan が動かない。本決定を入れた後の regime では D1019 の結論が再び成立する。
- **`real-repo` の shard affinity を分離して K の上限を上げる** — 段 3 の 2 レンズが、
  排他閉包が今も閉じていない (登録外の実 repo writer と collection 窓が残る) ことを
  file:line で示した。閉包が確定していない排他を差し替えない。
