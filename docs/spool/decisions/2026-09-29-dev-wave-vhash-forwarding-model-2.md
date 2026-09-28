---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: dev-wave-vhash-forwarding-model
seq: 2
---

## {{D:vhash-forwarding-model-spec}}. VHash の選択的 forwarding を、出典メモ §4 の Cicada 前提を模した小モデルの仕様 v1 と、状態の全探索で検査する

**決定:**

1. 仕様は出典メモ §18 の 5 状態 (候補時刻・確認済みの整合性・GC への保護下限・物理参照の保護・確定の印) を txn の別々の量として持ち、`rts` は「見える区間の終わり」と別の量にする (§13.3)。**通常 read は rts を書かず**、rts を書くのは forwarding の確認と commit 時の検証だけにする (メモ §4 の validation 順に合わせた設計選択)。
2. 書き込み側の直前版 rts 検査は、wts 未満の版を降順にたどって **PENDING 版をすべて越え、最初の COMMITTED 版まで** 見る (R9')。直前版 1 つだけを見る v0 は、後で abort しうる PENDING 版に遮られて下の確定版の rts を見落とし、3 txn・2 キーで閉路反例を出した。
3. forwarding は「既読版の rts を候補時刻へ上げる → 版列を観測し直して可視確認 → 確定 → GC 公開」の順にする (R5〜R7)。確認済み区間で commit 時の検証を省く O(1) 検証 (O1) は選択肢として扱い、上の順序が前提条件であることを探索で示した。
4. 検査器は orchestrator/verifier を import せず、package 内の小さい判定器 (依存グラフの閉路・timestamp 順・GC 安全) を持つ。GC 安全は protocol が公開した下限でなく txn の論理状態 (cand_ts・read log・物理参照・残り操作) で判定する。明示的な「thread 停止」遷移は持たない (安全性は途中で閉じた性質で、停止は「以後選ばれない schedule」として全探索に含まれる)。
5. 「反例なし」は固定した場面の初期状態からの全 interleaving に限って書く。一次資料は `output/insights/2026-09-29/vhash-forwarding-model/README.md`。

**理由:**
- 通常 read ごとに rts を書くと、提案 (Cicada に forwarding を足す) の実装形と離れ、read の cache line 書き込みという費用の議論 (メモ §14.2) も歪む。
- R9' は v0 の反例 (場面 S8) を止め、10 場面の全探索で v1 に反例が出なかった。
- orchestrator/verifier は同日に別 wave (md_3) が編集しており、API の結合を避けた。判定器の検出力は手作りの正例・負例、危ない版 8 種、検査器への変異 11 種 (10 KILLED、1 は到達状態で等価) で確かめた。
- 公開された下限で判定すると、公開を早める危ない版を判定器自身が見逃す。

**却下した選択肢:**
- 通常 read のたびに rts を上げる設計 (段 2 の plan 初稿) — Cicada の前提から離れ、forwarding 固有の順序問題を消してしまう。
- orchestrator/verifier の依存グラフを直接使う — 同時編集中の API に結合する。将来の独立照合の候補として残す。
- 明示的な STOP 遷移 — 安全性の探索では冗長で、状態数だけを増やす。
