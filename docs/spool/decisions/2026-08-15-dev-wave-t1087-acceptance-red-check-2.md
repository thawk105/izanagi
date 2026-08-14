---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-15
wave: dev-wave-t1087-acceptance-red-check
seq: 2
---

## {{D:dispatch-residue-deleted-not-excluded}}. 非帰属 checker の dispatch 副作用は、清浄性検査の緩和ではなく受領証の即時削除で解く

**決定:** probe worktree の清浄性検査 (`git status --porcelain=v1 --untracked-files=all
--ignored=matching --ignore-submodules=none` が空 tree の sha256 と一致すること) は 1 bit も
緩めない。checker 自身が投入した dispatch の受領証は、権威 stdout を読み終えた直後に、
検証済み nonce directory・fallback receipt・exact `output/pegasus-dispatch` root の順で削除し、
削除完了を fail-closed で検証する。root が空でなければ削除せず判定不能 (rc=2) で止める。
再帰削除も glob も使わない。

**理由:**
- 除外案 (清浄性検査から dispatch 受領証 path を落とす) は、ignored な副作用の検出力を
  そのぶん落とす。既存契約は rerun node が作った ignored file を必ず拒否することを要求しており、
  path 単位の除外はこの防壁に穴を開ける。正しさゲートを緩める方向の変更であり採らない (規律 2)。
- 外出し案 (受領証を probe worktree の外へ置く) は D216 が既に実測で却下している。
  `.gitignore` の `output/pegasus-dispatch/` は末尾スラッシュ付きのため symlink を ignore せず、
  clean gate に映る。producer 側の出力先を checker のために動かす影響面も広い。
- 削除案は「作らせない」ではなく「作った直後に消す」なので、検出力を 1 bit も落とさずに済む。
  異物があれば保持して止めるため、他者の成果物を巻き添えにもしない。
- **実測で成立を確認した (2026-08-15、Pegasus)。** 合成 log 1 red = 78 秒 rc=1、
  実受入 log 2 red = 155 秒 rc=1。いずれも実 dispatch (PBS request_id 実在) で受領証が
  probe worktree 内へ書かれ、後続の清浄性検査を計 6 回すべて通過して判定へ到達した。
  受領証が残っていれば必ずそこで判定不能になるため、この通過が削除の証拠である。
  receipt の削除 path field は削除より前に組み立てられる自己申告なので根拠にしない。

**主張の射程:** 不再現を実証したのは**正常な preferred / fallback child receipt 経路**に限る。
告知が無い・非一意・child rc 不一致の経路は削除へ入る前に例外となり、root が空でなければ
削除もしない。いずれも倒れる向きは判定不能であって受理集合は緩まないが、
「残渣経路は存在しない」という主張はしない。

**却下した選択肢:**
- 清浄性検査から dispatch 受領証 path を除外する — 上記のとおり検出力を落とす。
- 受領証を probe worktree の外へ出す — D216 の実測却下と同じ面。
- checker が作った ignored file を一括削除する — bytecode 等まで巻き込み、
  rerun node の副作用を検出する既存防壁を壊す。bytecode 側は producer の env allowlist で
  「作らせない」向きに解決済みであり、削除で解いてはならない。
