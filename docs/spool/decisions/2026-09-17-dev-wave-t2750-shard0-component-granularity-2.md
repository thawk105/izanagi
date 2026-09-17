---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2750-shard0-component-granularity
seq: 2
---

## {{D:shard0-component-granularity-no-wall-gain}}. 受入 shard 割付の連結成分を file 粒度から node 粒度へ変えない — 固定 duration model では最遅 shard の下限が不変で、素直な変更は real-repo の跨ホスト排他を外す

**決定:** `tools/acceptance_shards.py` の `_components` / `allocate` / `assignment_closure_gate` が file と xdist group を頂点にして連結成分を作る現行の粒度 (D711 gate 4 の file 閉包を含む) を維持する。「成分単位を file から node へ」も「大 file の real-repo node を別 file へ分離」も実装しない。受入短縮の次の対象は shard の負荷の総和ではなく、最遅 shard の最長 node (t080 e2e の b5 群) の単体所要と、xdist の初期配布が最長 node の worker へ対にする 2 個目の unit (約 20 秒) とする。

**理由:**
- 48 worker では shard の wall は「最長 node + 相方 + 固定費」で決まり、負荷の総和では決まらない。台帳 refresh 後の受入 20 走 (他 wave の受入 = 同時刻対照) で、shard-0 の最忙 worker は 20 走すべてで item 2 個 (最長 node 225〜500 秒 + 相方、相方は 17 走で約 20 秒)、平均 worker 負荷 (直列和 ÷ 48) は 161〜417 秒で 20 走すべてで最長 node より小さい。wall − 最大占有の固定費は中央値 66 秒。
- 案 (a) の offline 割付では負荷が 7523 / 5372 / 5372 秒 → 6089 秒 × 3 に均等化されるが、D1019 の makespan 式 max(最長 node, 負荷/48) + 固定費 による最遅 shard の予測は 3 通りとも 306.1 秒で同値である。予測 wall の合計はむしろ 690 → 748〜838 秒へ増える (最長 node 群が別 shard へ散り床を作る)。この model は下限であり実 wall の期待利得 0 の証明ではないが、実 wall 改善の経路は「同 host 競合の低減で最長 node 自身が速くなる」だけで、既存 99 session からは分離できず (最長 node の所要は同 shard の他 worker 占有と r=0.993、別ノードの shard とは r=0.07、ただし同一割付内では仕事量が一定なのでノード状態で説明できる)、期待値を数値化できない。上限の目安は相方の約 20 秒 (最遅 shard wall 中央値の 5.8%) で D357 の「変化なし」域に入る。
- 素直な案 (a) (file union の削除) は規律 2 の防壁を外す。`orchestrator/tests/test_s8c_preregistration_predicates.py` の候補 commit 生成 fixture の consumer は xdist group 無し・real-repo inventory 外だが、function fixture が実 repo の object store へ `git add` / `write-tree` / `commit-tree` で書き、同 file の group 付き node との file 閉包だけで衝突成分と同じ host に留まっている (fixture-owned golden がその依存を明記)。file 閉包を外すと別 host の shard へ配置可能になり、`/tmp` の flock (同一 host 限定) では閉じられない。inventory golden は実 repo アクセスの網羅的検出器ではない (宣言済み inventory 内の分類一致と、resource node と交差する module/session fixture を seed にした閉包であり、seed の無い fixture・function fixture・import 副作用は探索外) ので、安全に実装するには明示 affinity の補完、D711 gate 4 の裁定改訂、衝突閉包 (resource node + fixture-owned consumer + 明示 affinity) の独立検査の新設が要る。後 2 者は依頼が scope 外とした「追加 gate・検査」に当たる。
- 受入短縮の既存裁定「効果を先に測り、未確認のまま実装しない」と D104 決定 3「効果を示せない機構は land しない」に従う。

**却下した選択肢:**
- 案 (a) を明示 affinity 補完つきで実装し、同一 tip の paired 測定 (旧/新割付を交互 n≥3) で採否を決める — 実装すべき側の最強の形として real と認める。ただし現証拠が支持するのは条件付きの試作・測定までで、land すべきという結論は成立しない。安全化を含む費用が本 wave の scope を超えるため、次の一手として起票し本 wave では払わない。
- 案 (b) (大 file の real-repo node を別 file へ分離) — real-repo marker 付き関数だけを移すと fixture 経由の未登録 consumer を取り残し同型の保護喪失を生む。nodeid の変更で台帳 key と golden の file 名 pin にも触れる。
- 「期待利得 0 を実測で証明した」「一次資料の『成分が shard-0 の床』は偽」と記録する — 段 3 の 2 レンズがともに飛躍と判定した。一次資料の主張は負荷の命題としては真で、wall への波及が未実証である。
