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

### {{F:worktree-cwd-only-scan}}. worktree の占有判定が cwd だけを見て稼働中の worktree を残骸と誤った [手順漏れ]

- 事象: `.claude/commands/cleanup-branches.md` §2 は他セッション使用中の判定を
  「`/proc/*/cwd` の readlink 走査で実測」と規定していた。2026-08-12 に並行セッションが本手順どおり
  5 本 (`dev-wave-t139-land2-s2` / `t756-trace-v2` / `t786-docs-budget` / `t810-node-variance` /
  `t812-lease-self-renew`) を残骸と判定して撤去したところ、直後に同 path が再作成され codex worker が
  一斉起動した。こちらで独立に `/proc` を走査した実測では、**5 本とも cwd 走査のヒットが 0 件、
  cmdline には 2〜4 件**あり (`codex_worker_launch.py` の argv に worktree の絶対 path)、
  cwd だけを見る規定の手順では稼働中を稼働中と判定できないことが確定した。未コミット差分は
  ゼロだったため作業自体の損失は無い。
- 根本原因: worker は worktree を **argv で指すが cwd にはしない**ため、cwd だけが占有の代理指標に
  なっていなかった。加えて launcher が周期投入するので、バッチの合間は滞在プロセスも HEAD 更新も
  無く、規定の 2 条件 (滞在プロセスあり・HEAD 直近) がどちらも偽になる時間帯が定常的に存在する。
  `ListAgents` にも対応セッションが出ないため、セッション一覧でも補えない。
- 恒久対応: 同 §2 を `/proc/*/cwd` と `/proc/*/cmdline` の両方を走査する形へ是正した本 commit と、
  memory `worktree-occupancy-needs-cmdline-scan`。
- 再発検知: **機械検査は無い (prompt 規律)。** 撤去は不可逆に近く、再作成された live path を
  再度消す事故は手順だけが防いでいる。占有走査を機械化する (削除前に cmdline 走査を強制する
  checker) 可否は裁定へ返す。
