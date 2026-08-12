---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: cleanup-branches-cherry-3stage
seq: 1
---

## 新規

### {{F:cherry-path-existence}}. cherry の取り残し判定が安価な代理指標を見て両方向に誤った [手順漏れ]

- 事象: `.claude/commands/cleanup-branches.md` §1 が「`+` 行が真の取り残しで、ファイルが main に
  無ければ取り込み漏れとして §5 で報告する」と指示していた。2026-08-12 の実行で 3 種の誤判定を実測した。
  (a) **偽陽性**: 着地済みの `docs/spool/worklog/2026-08-11-dev-wave-t675-address-edge-lint-3.md` を
  「取り込み漏れ」と判定しかけた (fold が fragment を削除して本文を台帳へ畳むため不在が正常)。
  (b) **偽陰性**: 未 land の `.claude/commands/rulings.md` 編集 2 件 (branch
  `worktree-rulings5-20260812` / `worktree-rulings6-20260812`) を、ファイルが main に実在するという
  だけで「着地済み」と見なしかけた。
  (c) **逐語 grep の偽陰性**: 代替として台帳を逐語 grep したところ、`worktree-dev-wave-t737-loader-issuer-pin`
  の DW-O18 統合分を「未着地」と**誤って報告した**。実際は同義の規則が別文言で
  `docs/dev-wave/operations.md` に実在し、wave 自体は作り直した別 branch
  `worktree-dev-wave-t737-rebuild` から land 済みだった (`docs/archive/worklog-phase3-0811-391-392.md`)。
  並行セッションの直読が誤りを検出し、こちらで独立に裏を取って撤回した。
- 根本原因: 判定対象が内容でなく代理指標だった。fold は着地の証として fragment を**消す**ので不在は
  着地の証拠になり、既存ファイルへの編集は path が在るまま未着地になりうる。さらに逐語一致は
  land 時の文言変更で外れ、wave が別 branch (rebuild) から land した経路も見落とす。F118 の恒久対応が
  持つ既知限界 (「判定は path 名の有無だけを見る」) と同型の誤りが、dangling 監査ではなく cherry 段の
  散文手順の側に残っていた。
- 恒久対応: memory `cherry-plus-judged-by-content-not-path` (path 実在 / main との diff /
  台帳と `docs/archive/*.md` の照合を ledger ごとに独立に行い、逐語 NO HIT では文言変更と
  別 branch land を疑う) と、同 §1 を「`+` 行は実在でなく内容で判定する (spool の不在は fold で正常)」
  へ是正した本 commit。
- 再発検知: **機械検査は無い (prompt 規律)。** command §1 の是正文と上記 memory だけが防壁であり、
  「代理指標を根拠に着地/未着地を書いた報告」を機械では止められない。恒真な保証にしないため
  ここに明記する。lint 化の可否は裁定へ返す。

## supersede 追記

- F251 **supersede: 2026-08-12** — 恒久対応の D342 (生存判定に `/proc/*/cmdline` を含める) を入口へ反映した。`.claude/commands/cleanup-branches.md` §2 の使用中判定を `/proc/*/cwd` の readlink 走査だけから cwd と cmdline の両走査へ是正し、再発検知が求めていた「掃除手順の生存判定に cmdline 走査が含まれること」を手順側で満たした (branch `worktree-cleanup-branches-cherry-3stage`)。同事象を削除された側から観測した独立実測 (撤去された 5 本すべてで cwd 一致 0 件・cmdline 一致 2〜4 件) も F251 の実測と一致しており、新規 F は起票しない。機械強制の checker を作るかは裁定へ返す。
