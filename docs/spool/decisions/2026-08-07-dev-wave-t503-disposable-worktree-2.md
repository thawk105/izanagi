---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-07
wave: dev-wave-t503-disposable-worktree
seq: 2
---

## {{D:disposable-mutation-worktree}}. 変異本走の隔離は「共有木を修復する」でなく「専有木を捨てる」で実装する

**決定:** 変異復元耐久化の第一 slice は、`tools/mutation_worktree.py` が固定 commit から repo 外へ
detached worktree を作り、その中で既存 harness を `--repo` として走らせ、完走時だけ木を捨てる形とする。
`tools/mutation_harness.py` は変更しない。実装の細目は次のとおり。

- **大域 `git worktree prune` を使わない。** teardown は自分の admin dir
  (`<common>/worktrees/<name>`、`gitdir` file が自 container を指すことを確認したもの) だけを消す。
- **lock は `--out` へ束縛する** (`<out>.lock`)。harness の `flock` は repo 絶対 path 由来なので、
  scratch を変えると分裂し、同じ台帳を後勝ちで上書きできる。
- **teardown は完走時だけ行う。** 未完了は container を保持し、wrapper の `--resume` で再開する。
- **自動 stale GC を作らない。** 既存 container は拒否し、削除しない。
- **`DW-M05` は変更しない。** wrapper は必須ではなく、`docs/dev-wave/**` の hard ceiling に
  余裕が無い。運用規約は `docs/mutation-restore-durability-design.md` §9.3 に置く。

**主張の射程:** 共有木の観測点間で `git status` / `git submodule status` の stdout bytes が
不変であることだけを主張する。file bytes 全体の不変でも、物理ノード死後の永続性でもない。
設計 §9.1 の必須 6 点の充足は 0/6 である。

**理由:**
- canonical state root・worktree incarnation nonce・quiescence の**発行者が現時点で存在しない**。
  専有・使い捨てなら「捨てる」で置換でき、consumer 契約と族一般化そのものを回避できる。
- `--repo` は harness の既存の第一級 seam であり、harness を触らずに成立する。
  測定器を被試験物にしないので、本 wave の変異 matrix を従来経路で走らせられる。
- 大域 prune は共有 `.git` 全体への mutation であり、並行 wave の admin 登録を巻き添えにしうる。
  自分の admin dir だけの削除で同じ効果が得られることを実測した (登録 9→8、`prunable` 0、
  他 worktree と共有 submodule は無傷)。
- 使い捨て木で受入全走が共有木と一致する (6806 passed / 20 skipped) ことを実測したので、
  測定の同値性を根拠づけられる。

**却下した選択肢:**
- **journal + fsync + 再開時修復を先に作る** — 発行者不在の 3 件が未解決のまま基盤だけが増え、
  配線しない限り成果物の値を変えない。前回の実装 wave がこれで停止している。
- **`output/pegasus-dispatch` を repo 外への symlink にする** — 実測すると `.gitignore` の
  `output/pegasus-dispatch/` が末尾スラッシュ付きで symlink を ignore せず、clean gate に映る。
- **`DW-M05` で wrapper を必須化する** — 機械的 admission が無い状態の「必須」は prose-only であり、
  旧 direct 経路も台帳 consumer も拘束しない。活性化は独立 wave の裁定に委ねる。
- **同一 spec を両経路で走らせる対照走行** — 12 変異で 28 dispatch を要する一方、共通 harness の
  共通欠陥・outer identity 欠落・teardown 失敗を通す。透明性テストと E2E テストに置換した。
