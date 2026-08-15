---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-15
wave: dev-wave-t1038-tracked-handoff
seq: 2
---

## {{D:handoff-main-provenance}}. 起動検査の handoff 受理条件は index 登録でなく main provenance にする

**決定:** `tools/check_wave_startup.py` の `_check_worktree_handoff` は、`docs/handoff` 直下の
entry を次の連言を満たすときだけ通す。

1. index record の tag が `H` (assume-unchanged / skip-worktree 等の flag が付いていない)
2. stage が `0` (未 merge でない)
3. index mode が `100644` または `100755`
4. `refs/heads/main:<path>` が解決でき、その OID が index の OID と一致する
5. worktree の entry が regular file である

条件を満たさない直下 index record は、worktree に同名 entry が無くてもそれ自体を failure にする。
述語ごとに別の診断文字列を出す。`README.md` の名前による無条件例外は廃止し、同じ規則で判定する。

**理由:**

- 裁定文の「tracked file を foreign control-plane として通す」の *foreign* は、land が
  `docs/handoff` 直下の削除を rc=21 で拒んで守っている対象、すなわち main が持つ file を指す。
  自 wave が自 branch へ commit した handoff は foreign ではない。
- index 登録だけを条件にすると `git add docs/handoff/x.md && git commit` の 1 手で起動 gate を
  黙らせられる。正しさゲートを 1 コマンドで迂回できる形は絶対規律 2 が禁じている。
- 不適格 record を「受理候補から外す」だけにすると、`git update-index --skip-worktree` で
  worktree から file を消したときにその index 状態がどこにも現れず、集約経路でも rc=0 になる。
  拒否を failure として保持することでこの経路が閉じる。
- 述語ごとに独立した failure を出すことで、mode / stage / tag の各検査が後続の `rev-parse` の
  成否に依存せず単独で発火する。これは検出力の問題でもある — 分類前の実装では、
  これらの述語を無効化する変異が後続検査に隠れて生存した。

**却下した選択肢:**

- **index 登録だけを条件にする (裁定文の literal)** — 上記の 1 手迂回が残る。
  狭める方向の逸脱なので実装したうえで、literal が意図だった場合の緩和方法を裁定へ返す。
- **`git status` から untracked を引いて判定する** — 未知の XY 状態・ignored・rename record を
  「tracked」と誤読する fail-open になりやすい。「tracked である」を肯定的に測るほうが安全。
- **worktree の raw bytes を blob hash して main と照合する** — clean/smudge filter や EOL 変換の
  ある path では clean-tree との連言が raw bytes 一致を含意しない、という指摘は正しい。
  ただし対象 path に filter が適用されないことを `git check-attr` で実測したうえで、
  checker の出力がいかなる成果物の provenance にも記録されないため成果物影響を書けないと判断した。
  残存限界として docstring と台帳に明記する。
- **main 側 mode も検査する** — `ls-tree` を read-only subcommand allowlist へ足す必要があり、
  防壁を 1 つ狭めるために別の面を広げる取引になる。成立条件 (main が symlink、worktree が
  同一 bytes の regular file、両者とも commit 済み) も極めて限定的である。
- **`README.md` の名前例外を残す** — untracked な `README.md` を無条件で通すため、
  「untracked は拒否」という不変条件に穴が残る。名前例外を廃止すると規則が 1 本になり、
  main が持つ `README.md` は provenance 条件で自然に通る。
