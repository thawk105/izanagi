---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: dev-wave-t810-test-isolation
seq: 2
---

## {{D:t810-skip-unlocked-absent-registration}}. t810 coordinator の登録走査は、gitdir も locked も無い管理 dir を飛ばす

**決定 (ユーザー裁定):** `tools/pegasus/t810_coordinator.py` の `repository_roots_from_git_identity` は、
共有 git dir の `worktrees/<名前>/gitdir` が不在 (open が FileNotFoundError) で、かつ同じ管理 dir の
`locked` が lstat で不在のときだけ、その管理 dir を飛ばす。`locked` が在れば (種類不問) 従来どおり
`cannot read worktree registration: file is absent` で拒否し、lstat の他の失敗は
`cannot inspect worktree registration lock` で拒否する。symlink・非 regular・読み中変化・非 UTF-8・
解決不能・管理 dir が file の場合の拒否は変えない。D1101 のうち「production の登録 scan は変更しない」
「`missing_ok` 相当は roots を減らす方向なので採らない」の 2 点を、ユーザー指示 (2026-09-29、md_4 の
「本番の関数も直す案も実施する」) で改める。D1101 の「production へ再試行を置かない」「live authority の
3 node は hermetic にしない」と D1102 は有効のまま。

**理由:**
- 他 wave の撤去途中に `modules` だけが残り `gitdir` が無い管理 dir が数分続き、受入全走の live 3 node と
  本番の `prepare_group` / `coordinate` を止めていた (F633)。ユーザーは「無関係な worktree の出現・消失を
  受入が気にする理由はない」と判断した。
- 実測 (git 2.34.1、job dir 配下の一時 repo、strace 各 1 回): `worktree add` は管理 dir → `locked` →
  作業木 → `gitdir` の順に作り、`worktree remove` は作業木 → `gitdir` の順に消す。`tools/dev_wave_cleanup.py` は
  unlock → 作業木削除と不在確認 → 管理 dir 削除の順。観測したこの 3 経路では「gitdir 不在かつ locked 不在」は
  作業木が未作成か削除済みの状態で、add 途中の「locked あり・gitdir 無し」は作業木が在りうるので拒否に残す。
- 列挙の後に add が始まった登録を飛ばした結果は、その管理 dir が列挙の直後に作られた場合と同じ roots で、
  並行 session が現行で取れる timing を超えない。

**受理集合の変化 (検査の意味は変わる):** gitdir も locked も無い登録の作業木だった path の中の
work_root / output_root を外部として受理する。手で gitdir だけを消した生きた作業木は roots から落ちる
(git 自身もそれを prunable と扱う)。submodule 付きの木・Lustre 上の中断・move / repair / prune は実測していない。

**却下した選択肢:**
- md_4 の逐語案 (gitdir 不在なら locked を見ずに一律に飛ばす) — add 途中で作業木が在る登録まで飛ばす。
- locked の判定に `os.path.lexists` を使う — 確認時の失敗を「不在」に畳み、確認不能で飛ばしうる。
- live 3 node を hermetic fixture へ寄せる — 設置先から anchor を導く検査の意味が消える (D1101 と同じ理由)。
