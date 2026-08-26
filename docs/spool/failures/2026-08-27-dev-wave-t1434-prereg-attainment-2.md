---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1434-prereg-attainment
seq: 2
---

## 新規

### {{F:mid-checkout-worktree-reads-as-dirty}}. 編集面重複走査が、作成途中の worktree を「編集中」と誤検出した [手順漏れ]

- 事象: [T-1434] の段 1 で、対象文書 `docs/phase3-t189-model-routing-preregistration.md` を触る
  他 wave を全登録 worktree の `git status --porcelain -- <対象 path>` で走査したところ、
  `dev-wave-t1380-prereg-artifacts` が **2 行**を返した。名前も `prereg` を含むため、
  同じ事前登録文書を書き換える併走 wave に見えた。数分後に同じ command を再実行すると
  **0 行**で、branch tip も `main` と同一、対象 path の三点 diff も 0 件だった。
  実体は、その worktree が 01:00 に作成された直後で `git checkout` が進行中だったため、
  未展開の tracked file が一時的に差分として見えていたことである。near miss —
  偽の衝突として本 wave を止めるか、逆に「dirty は checkout のせい」という誤った一般化を
  作るかのどちらにも倒れえた。
- 根本原因: 重複走査が **1 回の `git status` の出力を終局的な事実として扱っていた**。
  worktree の中身は作成中・submodule 初期化中・別 wave の一時変異中 (`DW-O19`) に
  不安定であり、その瞬間の porcelain 出力は編集予約を意味しない。
  走査面の広さ (F606 の型) ではなく、走査した**時点**の安定性が問題である。
- 恒久対応: 重複走査の hit は、次の 3 点で live 判定してから結論する。
  (1) 同じ走査を再実行して安定を確認する、(2) `git -C <wt> log --oneline -1` と
  `git diff --name-only main...<branch> -- <対象>` で branch 側の実体を見る、
  (3) `/proc/*/cwd` の走査でその worktree を cwd に持つ process を特定し、
  cmdline から何の wave かを確かめる (memory `worktree-liveness-needs-cmdline-scan` と同じ作法)。
  1 回の porcelain 出力だけで collision とも非 collision とも結論しない。
- 再発検知: 段 1 の brief に「重複走査の hit / 非 hit をどの時点でどう安定確認したか」を
  書かせる。本 wave の brief と handoff は実際にこの再検査の経緯を残しており、
  それが誤検出だと判定できた唯一の根拠だった。

### {{F:ruling-not-projected-to-plan-child}}. 既裁定の逐語を射影されなかった子が、その裁定を超える規則文を起草した [手順漏れ]

- 事象: [T-1434] の段 2 で、親は plan 子へ brief・前 wave の文面案・対象文書・実装 source を
  射影したが、**wave の前提である既裁定 D932 の逐語を射影しなかった** (brief 内の 1 行要約だけ)。
  plan 子が起草した §10 の規則文は、D932 が裁定していない分母規則 (観測不能な試行を
  `attempt_count` へ算入しない) を新設していた。段 3 のレンズ B には D932 の逐語を射影しており、
  そのレンズが「越境」として must-fix で捕まえた。plan 子自身も出力末尾に
  「親は執筆前に D932 正本と逐語照合すること」と書いて自分の射程不足を申告していた。
  near miss — 親がこの文案をそのまま採れば、事前登録に既裁定を超える受理規則を密輸していた。
- 根本原因: `DW-O02` は「必読資料は job dir へ取り出して渡す」と定めるが、**何が必読かの
  列挙に既裁定が入っていなかった。** 裁定に依存する wave では、裁定の逐語こそが子の
  scope 境界を決める資料であり、要約では境界を判定できない。
- 恒久対応: `DW-O02` の射影義務を「**必読資料と前提の既裁定は逐語を** job dir へ取り出して渡す」へ
  改めた (本 wave の段 8)。同じ wave で、逐語を渡したレンズと渡さなかった子の結果が実際に割れた
  ことが根拠である。L1.5 の byte 予算が満杯だったため、同節の既存文を意味等価に縮約して
  収めた (731 bytes、改訂前 744 bytes)。
- 再発検知: 段 3 / 段 6 の敵対レンズへ「提案が既裁定を超えていないか」を明示的に探させる
  prompt 節 (本 wave で実際に発火し、この F を生んだ経路そのもの)。

## 再発

### F606

- **再発: 2026-08-27** — [T-1434] の段 1 で編集面重複走査を組んだ際、F606 の恒久対応が要求する
  **repo 外 job directory の走査を掛けなかった**。走査面は「全 local branch の三点 diff」と
  「全登録 worktree の porcelain」だけで、段 1〜4 の間 repo へ 1 行も書かない併走 wave の
  編集予約は原理的に捕まえられない状態だった。偽の結論には至っていない (near miss) —
  たまたま作成途中の worktree を dirty として掴み、そこから台帳で scope を確かめる経路に入ったため。
  段 7 の記録前に、稼働中 worktree に対応する job directory を対象文書名で全件 grep して
  **hit 0 件**を確認し、走査面を埋めた。型は F606 と同じ「走査の網が実際の編集予約より狭い」で、
  今回は**恒久対応が既に台帳にあるのに参照されなかった**ことが差分である。
