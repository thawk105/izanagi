---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-13
wave: dev-wave-login-unreclaimable
seq: 1
---

## {{D:login-headroom-unreclaimable}}. ログインノードの admission 判定量を回収不能メモリにする

**決定 (2026-08-12 ユーザー裁定、rulings 第 6 束の追加指示)。**

1. **admission の判定量は user slice の回収不能メモリ量**とする。ユーザー発話
   「メモリ使用量ってファイルキャッシュも含めてみてる？ 回収不能メモリ使用量を気にしてほしい。
   ファイルキャッシュが溢れることは問題ない」に従う。これは **D209 決定 3 の
   「reclaim 可能な file cache を差し引く案は採らない — 差し引けば実効許容量はほぼ倍になるが
   別裁定が要る」を supersede する**。同決定 3 が要求していた「別裁定」がこれである。
   **上限 16 GiB・天井 14 GiB・予備 2 GiB の運用値は変えない。**
2. **算出式**は `回収不能量 = 基準値 − clean file cache − 回収可能 slab`。
   `clean file cache = max(0, file − shmem − file_dirty − file_writeback − unevictable)`。
   参照実装は Pegasus の `memwatch.sh` の「回収不能」行だが、**2 点で意図的に保守側へ寄せる**。
   - **dirty / writeback を回収不能側に数える** (memwatch は回収可能側に入れる)。書き戻し完了前の
     ページを空きと数えないため。倒れる向きは DISPATCH 側で fail-closed。
   - **`unevictable` を回収可能側から除く。** mlock / pin されたページは clean file に見えても
     回収できない。実機にも 4.4 MB 存在する。
3. **`memory.current` を `memory.stat` の前後で 2 回読み、大きい方を基準値にする。**
   この 2 つは同一 snapshot ではない。cache が増えた場合は後の読みが、減った場合は前の読みが
   大きくなるため、max を取ると両方向で保守側に倒れる。
4. **degrade は 2 経路だけとし、いずれも従来の `memory.current` 相当の保守判定へ戻す。**
   (a) `slab_reclaimable` または `unevictable` が `memory.stat` に無い、
   (b) 回収可能量が基準値を超える (snapshot 不整合)。
   **後者を 0 へ clamp してはならない** — それは最も緩い値を返す fail-open である。
5. **既存 5 キー (`anon`, `file`, `shmem`, `file_dirty`, `file_writeback`) の required 契約は
   縮めない。** 欠落・破損は従来どおり観測失敗 (`None`) → 必ず dispatch とする。
   新規 2 キーだけを optional にする。
6. **公開 field の意味を変えない。** `occupied_bytes` / `current_bytes` / `headroom_bytes` は
   raw `memory.current` 由来のまま残し、admission は新設の `admission_bytes` を使う。

**理由:**

- 実測で、判定量が `memory.current` のままだと **ログインノードの local 実行が恒常的に閉じていた**。
  観測時点の user slice は合計 12.66 GiB (うち file cache 3.47 GiB、回収可能 slab 1.70 GiB) で、
  天井 14 GiB − 予備 2 GiB = 12 GiB を合計が超えるため、要求サイズに関わらず必ず dispatch していた。
  同時点の回収不能量は 7.54 GiB で、実装後は同じ天井のまま local が成立する。
- ファイルキャッシュは上限に当たればカーネルが捨てる。捨てられない量 (匿名メモリ・tmpfs・
  カーネル構造体) だけが OOM の危険量であり、swap の無い本環境ではそこが上限に届いた時点で
  OOM kill になる。判定すべきはこちらである。
- admission は資源の入場ゲートであり、**緩める方向の変更は採らない** (絶対規律 2)。
  上記 2・3・4・5 はいずれも「迷ったら DISPATCH 側」に倒す設計である。

**却下した選択肢:**

- **`memory.stat` の required 集合を縮小して欠落キーを current fallback にする案** — 現行は
  キー欠落で観測失敗 → 必ず dispatch なので、これは今日の受理集合を拡大する fail-open である。
  独立した敵対レビュー 2 本が同じ判定を出した。
- **memwatch の式をそのまま使う案** — dirty / writeback を回収可能側に入れるため admission には
  楽観的すぎる。監視用ヒューリスティックとしては成立するが、ゲートの正本にはできない。
- **`headroom_bytes` を `天井 − 回収不能量` に変える案** — 物理的な余裕と admission 用の
  回収後余裕を混同し、cgroup 上限の直前でも大きな余裕を表示する。
- **`RESERVE_BYTES` の縮小や天井の引き上げ** — 判定量の定義変更で得た余裕を、さらに予備を
  削って広げることはしない。

**残る不確かさ (記録):** `slab_reclaimable` 全量が常に即時回収できるとは限らず、GUP/DMA pin の
ように専用 stat を持たない回収不能 file page も原理的にはありうる。予備 2 GiB がこの残差の
吸収域であり、超過が観測されたら予備でなく判定式側を見直す。
