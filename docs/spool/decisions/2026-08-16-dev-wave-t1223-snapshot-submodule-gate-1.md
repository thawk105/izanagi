---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t1223-snapshot-submodule-gate
seq: 1
---

## {{D:snapshot-submodule-initialization-gate}}. snapshot oracle は submodule の初期化を無条件に要求する

**決定:** `verify_snapshot` は submodule manifest の**全行**について `initialization == "initialized"`
を要求し、満たさない行ごとに reason を積む。この検査は `expected` (spec) を一切参照せず、
`git_object_closure` の分岐の外に置く。したがって caller は spec でも closure 設定でも
受理集合を広げられない。oracle document の key 集合は変えないので、受理され続ける snapshot の
`manifest_sha256` と schedule 突合・replay bytes 比較は不変である。

**理由:**
- 既定 spec は 9 key しか pin せず submodule 系を含まないため、pin 済み manifest との照合節は
  既定経路で常に不発だった。CCBench の作業木を持たない snapshot が「pin された木」として
  certified 選択の材料になりうる状態が、この wave まで残っていた。
- 深さを限定しない根拠は運用契約の実測である。受入 claim 前の `preflight-submodule-ready` は
  再帰 status の未初期化を拒否し、runbook も投入前の再帰初期化を要求する。したがって
  「正当に運用された作業木」は全深度が初期化済みであり、全深度要求は正規の運用を壊さない。
- 深さ算術を持たない設計は、兄弟 path (`deps/a` と `deps/ab`) を祖先と誤認する型の欠陥を
  構造的に排除する。

**却下した選択肢:**
- 深さ 1 だけを要求する — 親の初期案。非再帰の起動手順だけを production 契約と見なしており、
  受入 preflight の実装を見ていなかった。初期化済みの top-level の下に未初期化の依存が
  残る snapshot を受理し続ける。
- 既定 spec に `submodule_manifest_sha256` の実値を pin する — submodule pin の更新ごとに腐る。
- 緩和 key (`require_initialized_submodule_depth` 等) を spec に新設する — caller が正しさゲートを
  緩められる lever を作ることになり、規律 2 に反する。独自 spec 経路だけを検査して
  production が fail-open へ戻る型の回帰も残る。
- 初期化済み submodule の内容同一性 (HEAD tree・index・worktree の三者照合) まで同時に要求する —
  検査層と実行コストが変わるため本 wave の scope 外とし、別タスクとして起票した。
