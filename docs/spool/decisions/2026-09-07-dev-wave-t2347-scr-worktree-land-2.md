---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-t2347-scr-worktree-land
seq: 2
---

## {{D:fold-gate-absent-registration}}. fold gate の登録 worktree 検査は「解決できたか」でなく「path が存在しないか」で分岐する

**決定:** `tools/dev_wave_land.py` の `_registered_worktree_paths` は、`Path.resolve(strict=True)` が
`FileNotFoundError` を上げた登録を**捨てずに**、解決しない絶対 path として返り値へ残す。それ以外の
`OSError` と `UnicodeError` は従来どおり `_FoldGateFailure` にする。`git worktree list --porcelain` の
出力は行単位で走査し続け、`prunable` 行を読まない。record 単位の分割もしない。land は
`git worktree prune` を実行しない。

受理集合が広がるのは「path が存在しない登録があっても fold gate が赤にならない」ただ 1 点である。
fold gate 隔離 dir との重なり検査の被覆は狭まらない — 不在 path も比較対象に残るため、
隔離 dir が不在登録の path と一致すれば従来どおり拒否する。

**理由:**
- 計算ノード job が共有 repo へ登録する scratch worktree は、job 稼働中ずっと login node から
  path が見えない。これを一律 fail-closed にすると、job 1 本で repo 内の全 wave の land が
  塞がれ、緑の受入が 1 本ずつ捨てられる (F851)。
- 「登録を捨てない」ことが本決定の核である。捨てる設計は、fold gate の非接触検査から
  その登録を外してしまい、受理集合を意図より広げる。
- 分岐の根拠を「git が `prunable` と報告したか」に置く案は、実測 3 点で退けた。
  (1) `git worktree list --porcelain -z` はこの機体の git 2.34.1 に無く (`rc=129`)、record 境界を
  一意にできない。(2) `prunable` は path 不在を意味しない — directory が実在し `.git` file だけ
  壊れた登録も `prunable gitdir file points to non-existent location` と報告される。
  (3) path に改行を含む**実在**の worktree は、porcelain 上で `worktree <前半>` の次行に
  `prunable <後半>` を出せるため、marker を偽装できる。
- `FileNotFoundError` を分岐条件にすると、git が `prunable` を出さない状態
  (登録が locked のまま path だけ消えた場合など) も同じ経路で通る。marker 方式はここを取り逃す。

**却下した選択肢:**
- `prunable` marker で record を除外する — 上の実測 3 点により、実在 worktree の取りこぼしと
  marker 偽装を招く。
- `resolve(strict=False)` へ一律に緩める — 権限不足や decode 不能まで黙って通り、
  不変条件 (`FileNotFoundError` 以外は fail-closed) を破る。
- job script 側を job 専用 clone へ変える (F851 の案 (b)) — land 側で直せば他の job script も
  同型で塞がなくなり、既に登録済みの scratch worktree にも効く。clone のコストは本 wave で
  実測しておらず、採否の理由には使っていない。共有 registry 依存そのものを切る価値は残るため、
  別タスクとして台帳に残す。
