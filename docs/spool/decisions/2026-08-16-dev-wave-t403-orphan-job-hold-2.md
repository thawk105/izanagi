---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t403-orphan-job-hold
seq: 2
---

## {{D:orphan-hold-latch}}. 孤児 job の後始末は「残っているかもしれない」を唯一の署名とし、create-only latch で 4 層を止める

**決定:** D142 の gate が qdel を見送った場合の後始末を、dispatch receipt の
`qdel.job_may_remain is True` **だけ**を署名とする create-only latch
(`output/pegasus-dispatch/orphan-hold.json`) で表現する。免除条項は置かない。
成立中は次の 4 経路を fail-closed で止める。

1. 次回投入 — 既存 F47 ラッチ検査の直後、nonce 作成と scheduler command より前に拒否する。
2. 変異 source の復元 — 変異 harness は変異 bytes を残したまま停止し、別 file の停止記録を書く。
3. 変異 worktree の廃棄 — 通常経路と plan-only 例外 fallback の双方で container を保全する。
4. 受入赤の再確認 probe の掃除 — worktree 強制削除も成果物削除も行わず判定不能で止める。

qsub の結果を観測できないまま抜ける経路でも latch を先に作り、request ID の照会は後に行う。
**この決定は qdel を実行する経路を 1 本も増やさない。**

変異 harness は dispatcher の生存に依存せず、(a) latch の存在、(b) dispatch 試行の timeout、
(c) receipt 由来の `job_may_remain` / hold 書込み失敗を独立に判定する。latch を書けなかった場合と
dispatcher が強制終了された場合を、この二重化が塞ぐ。

**latch 自体を書けない storage 障害では、harness が書く停止記録 `<--out>.orphan-stop.json` が
権威になる。** この記録が残る限り harness は fresh でも `--resume` でも runner を 1 本も起動せず、
変異 worktree も container を保全する。判定不能 (`lstat` の `OSError`) は成立側へ倒す。

**理由:**
- 不在・終端の「実証」に見える観測は偽陽性になりうる。照会が rc=0 でも対象が見えないのは
  投入直後の未反映と区別できず、監視ループの終端観測は対象非束縛 parser 由来のことがある。
  段 3 の敵対レンズが既存テストの固定値からこの false negative を実証した。
- D142 の非対称性 (走行中を殺すと受入証拠が失われて取り戻せない / 止め過ぎは人間が確認して
  解除できる) を、qdel の可否だけでなく後始末側へそのまま延長する。
- 計算ノードの job は login 側 checkout の source をその場で読む。孤児が生きている間に
  復元・再変異・削除を行うと、変異台帳の「注入して走らせた」記録と実際に走った bytes が
  食い違い、KILLED / SURVIVED の判定値そのものが誤りになる。

**保証の射程:** latch は latch であって相互排他 lock ではない。同一 checkout で harness を
経由しない並行 dispatch を運用上作らない契約の下でのみ、後続 consumer を止める。
qsub 前の永続 claim を作らないため、SIGKILL と照会中の再 signal の窓は残る。
保護範囲は `dispatch_compute` 経由の dispatch と変異 harness / 受入 checker に限り、
直接 qsub する submit script 群、campaign の patch harness、local 実行経路は対象外である。
これらは謳わず、実装の docstring・停止記録・runbook で射程を明示する。

**却下した選択肢:**
- 免除条項つきの署名 (照会で不在 / 終端観測を安全側とする) — 上記の偽陽性で false negative になる。
- qsub 前の永続 claim を本 wave で導入する案 — 解決 (削除) 経路を新設することになり、
  その経路の欠陥が全 dispatch を恒久停止させる。解除の安全性設計を先に済ませる別作業とした。
- F47 の submission-disabled ラッチへ相乗りする案 — 原因も回復手順も異なり、
  既存 F47 の受理集合と文言を変える。
- 過去 receipt の走査で孤児を判定する案 — 既存の孤児 receipt が残る checkout では
  dispatch を永久に封じる。evidence の再実体化で worktree を分けても隔離されない。
- 停止記録を通常の変異台帳へ上書きする案 — 保全した campaign の `--resume` が
  schema 不一致で必ず失敗し、一時停止が campaign 再作成へ悪化する。
