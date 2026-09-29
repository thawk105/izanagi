---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: dev-wave-vhash-hot-block-cicada
seq: 2
---

## {{D:vhash-hot-block-seqlock-prefix}}. VHash の hot block (構成 B) は、key ごとの seqlock で守る「物理的な版の列の先頭 K 件の {wts, Version*} の写し」として inert patch で Cicada に入れ、第 1 段の走査だけを置き換える。条件 gate への登録は自分の 3 macro と driver の行だけとし、COUNT には companion K=1 を固定する

**決定:**
1. **hot の中身:** key (Tuple) ごとに `latest_` の直後へ seq・件数・K 個の `{wts, Version*}` を置き、物理的な版の列の先頭 min(K, 長さ) 件を写す。ABORTED・PENDING の版も含み、状態は写さない。値は置かない。K はコンパイル時の値 (1/2/4/8) で K ごとに別 binary。
2. **一貫した読み:** key ごとの seqlock (Boehm 2012 の形: 書き手は偶→奇の CAS acq_rel・release fence・relaxed store・奇→偶 release store、読み手は acquire load・relaxed load・acquire fence・再読込)。奇数か変化なら spin せず stock の走査へ落ちる。pointer は再確認の後だけ参照する。
3. **読みと保守:** `read_internal` の第 1 段 (新しすぎる版を飛ばす走査) だけを hot の走査に置き換え、`later_ver` は物理の直前の記述子にする。第 2 段以降は stock のまま。validation の版の挿入 (位置探索と CAS) と GC の切り離しを書き区間の中で行い、GC は hot から古い記述子を消してから版を再利用へ回す。lock の順は `gc_lock_` → hot の一方向。
4. **macro と登録:** `CICADA_VHASH_K`・`CICADA_VHASH_COUNT`・`CICADA_VHASH_WL` (IZANAGI_ 接頭辞なし、未定義で stock と前処理一致、分岐は owner TU `cc/cicada/transaction.cc` と include する 2 header だけ)。条件 gate (`orchestrator/campaign/condition_meaning_gate.py`) と連動する在庫へ、自分の 3 macro と新 driver の行だけを足す (依頼の所有の外だが、patch に新しい #if があると登録簿の test が赤になり build も gate を要するので必要最小、D2288 と同じ理由)。`CICADA_VHASH_COUNT` は分岐の多くが `#if CICADA_VHASH_K` の内側にあるので companion `CICADA_VHASH_K=1` を固定する (D2288 の `CICADA_FWD_COUNT` と同じ形)。
5. **ro 指定率の制御は variant patch の WL に置き、stock 対照も同じ patch (K=0・WL=1) で build する** (計器 patch の中にしか無い制御では性能値を取れないため)。`patches/ledger.json` には載せない (D2279・D2288)。

**理由:**
- hot を「物理列の先頭の写し」に限ると、読み手が選ぶ版は seq を確かめた時点の物理列で stock の第 1 段が止まる版と同じになり、validation の read 再検査が辿り始める点も変わらない。安全性を stock へ帰着させて論じられる (一次資料 §2)。
- 実測 (一次資料 `output/insights/2026-09-29/vhash-hot-block-cicada/README.md`): この実装で K = 1, 2, 4, 8 は 3 つの trace cell で判定器を通り (巡回なし、上限 indeterminate)、壊し 2 本は検出・帰属した。性能は ro 95% で stock 比 0.98〜1.01、更新中心で 0.23〜0.80 倍 (書き区間の待ちが主因)。
- 値を置かないのは、Cicada の値が HeapObject の別確保であり、md_5 で K=8 の inline 値は最新版の読みで散在 linked より遅かったため。
- smoke1 で COUNT の meaning が宣言 20 / 観測 8 で拒否された (gate の probe は K 未定義で前処理するので K の内側の分岐が見えない)。

**却下した選択肢:**
- ABORTED を hot から外して評価計画草稿 §2 の数え方に合わせる — `later_ver` の意味と物理列との一致が崩れる反例がある (段 2)。構成 D を作るときに「hot miss = 論理 K 境界」の対応を取り直す。
- 挿入の CAS の後に hot を遅れて更新する (書き区間を CAS の外に出す) — 読み手が過去の列の状態を見る窓ができ、安全の論証が変わる。更新中心の費用を下げる本命の候補だが、本 wave では論証を書いていないので採らず、次の一手に回した。
- 値も hot に置く — 上の理由。
- 条件 gate の登録を避けて patch を patches/ の外に置く — 検査逃れで D18 の inert patch 方針から外れる。
- 共通 header `include/ycsb.hh` に ro 指定率の制御を置く — 他 protocol の TU を変え、gate の owner TU の観測範囲の外になる (先例 md_15 は transaction.cc の begin() に置いた)。
