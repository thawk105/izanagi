---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1551-stale-registry-gate
seq: 1
---

## {{D:flaky-stale-delegation-by-dsession}}. flaky-hold stale 検査の委譲は分配器の実在で決める

**決定:** `orchestrator/tests/conftest.py` の完全 collection 判定は、xdist hook へ検査を委ねるか
自分で行うかを **`dsession` plugin が登録されているか**だけで決める。`-n` / `numprocesses` の
要求値、`--dist` の値、`sched` や `numnodes` の状態は委譲判定に使わない。
完了判定 (何 worker 揃ったか) は従来どおり別の述語が持ち、不正な値では例外を投げずに
「まだ完了していない」を返す。

controller 側の再検査は**防御の二重化であり、受理集合の正しさゲートではない**。
実 xdist では各 worker が完全 collection に対して同じ検査を自分で行うためである。
ただし同じ hook が行う hold 集約は冗長でなく、controller 側の集計出力の唯一の入力である。

**理由:**
- 要求値と実効値は一致しない。`--collect-only` は xdist の分配自体を無効にするので、
  `-n` が付いていても分配器は作られない。要求値で委譲すると、委ねた先が存在しないまま
  どちらの経路も検査しない状態が生まれる (実測: 注入した stale registry に対し rc=0)。
- 委譲の可否と完了判定を 1 つの述語に混ぜると、分配器は登録済みだが scheduler が
  まだ用意されていない時点を「不正」と判定して受入を止めうる。xdist の実装では
  scheduler は実行ループに入るまで存在しない。分けておけば、この時点差は結果を変えない。
- worker が同じ検査を行うことは xdist が worker へ controller の argv をそのまま渡す
  実装から従う。したがって controller 側の再検査を正しさゲートと記録すると、
  変異の kill 件数を配線の証明として過大に数えることになる。

**却下した選択肢:**
- 共有 helper で `numnodes` まで検証し、不正なら停止する — 上記の時点差で受入を止めうる。
- 委譲先が実際に hook を配送するかまで確かめる — 任意 plugin の登録は
  conftest 自体の抑止と同じ入口であり、この検査だけで塞ぐ対象ではない。
- 上位集合 (suite root に別 target を足した形) も完全と見なす — 既存の
  重複 root 迂回防止の契約と衝突する。
