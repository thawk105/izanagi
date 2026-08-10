---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-10
wave: dev-wave-t674-d125-supersession
seq: 2
---

## 新規

### {{F:acceptance-lease-behind-livelock}}. 受入 lease の behind 検査が高頻度 land 下で livelock し、実走 0 のまま 2 時間空費した [手順漏れ] [コンテキスト浪費]

- 事象: 2026-08-10 の docs-only wave が受入 lease へ 3 回並び、3 回とも**取得できた**のに
  その時点で local main が 7 / 3 / 5 commit 先行しており、`docs/pegasus-runbook.md` §7.3 の
  behind 検査で lease を返して親へ戻った。親が取り込んで並び直すたびに他 wave が land し、
  **受入全走を 1 度も走らせないまま約 2 時間**を空費した。3 回目は待ち行列にいる間に先行を
  検知して lease を消費せず戻る形へ直したが、それでも取り込み → 並び直しの間に追い越された
- 根本原因: §7.3 は「取り込みは投入前に親が merge commit として済ませ、待ち手は
  `git rev-list --count HEAD..main` が 0 であることの検査に留める」と定めるが、これは
  **取り込みから lease 取得までの間に main が動かない**ことを暗黙の前提にしている。
  並行 wave が複数稼働し land が数十分間隔で入る時間帯ではこの前提が成立しない。
  同節が禁じている実体は**待ち手内の `--ff-only`** (wave が自前 commit を持つと必ず失敗する)
  だが、代替として `--no-ff` merge を許す記述が無いため、親へ戻す以外の出口が書かれていない
- 恒久対応: memory `acceptance-lease-poll-30s` の「取得後の取り込み」節 — lease を取ったら
  behind が 0 でなくても親へ戻さず、その場で `--no-ff` merge して走る。安全側の配線 3 点
  (親が用意した message template へ SHA だけ差し込む / 競合・provenance preflight 非 0 なら
  merge 中止と lease 返却 / 走行前の behind 再検査と `git status --porcelain` 空検査) を必須とする。
  runbook §7.3 本文への明文化は head-of-line blocking と引き換えの設計択一のため裁定へ返す
- 再発検知: 1 wave 内で lease の claim ログに behind 由来の返却が 2 回以上出たら同型

## 再発

### F66

- **再発: 2026-08-10 ([T-674] wave の立ち上げ)。** 背景 job が新規 worktree を作り
  `tools/check_wave_startup.py` を走らせたところ、2026-08-01 / 2026-08-08 とまったく同じ
  `NG: submodule is not initialized ... 親セッションで submodule を初期化する` で停止した。
  対処も同じく当の worktree で `git submodule update --init --recursive` を走らせることだった。
  **独立 3 例目**であり、恒久対応にある「`DW-O20` への導線追記」は 9 日経っても未着手である
  (`docs/dev-wave/**` の byte 予算)。[T-641] の裁定に従い、本 wave でも文書側は変えず記録だけを厚くする。
