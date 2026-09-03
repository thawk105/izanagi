---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-b10-preflight-fixes
seq: 3
title: B-10 正式走の投入前必須修正を実装した — 5 件のうち 1 件は既に着地しており、段 6 が親の裁定を 2 件訂正した (コード + テスト + docs + insight、branch worktree-dev-wave-b10-preflight-fixes、変異 7/7 KILLED)
---

## 本文

- **依頼の前提を最初に実測し、1 件が既に着地していることが分かった。** 設計文書 §6 (1) の
  シグナル処理は commit `2d6f2dbf5` で main へ着地済みで、挙動テストも入っていた。
  実装 scope を (2)〜(5) の 4 件に絞り、設計文書側の記述を訂正した。
- **§5.1 の律速測定は稼働中の T-2191 と重複していたので §6 だけで閉じた** (依頼の指示どおり)。
  起動時に全 branch の三点差分と全 worktree の未 commit 差分を走査し、編集面の重複 0 件を確認した。
- **段 6 の敵対レビューが親の裁定を 2 件訂正した。** どちらも実装の生死に関わる。
  1. キャッシュ置き場の鍵を投入ごとの識別子にすると再開性が壊れる
     ({{F:cache-key-choice-breaks-resume}}、{{D:b10-build-cache-keyed-by-workload}})。
  2. 凍結集合の照合が実効経路へ繋がっているかを検査していなかった
     ({{F:frozen-set-gate-not-wired-tested}})。事前登録した変異が生き残る形だった。
  加えて、段 2 のプランが cross-job の bytes 一致テストを実装の先行条件に置いており、
  そのままなら §6 (3) は構造的に実装不能だった。レンズが否定的実測を持ち出して棄却した。
- **段 3 のレンズが挙げた「採用 campaign 集合が未裁定」は親の実測で refuted。** 官製 output を
  全数読むと、性能セルを持つ write-heavy は 1 本だけで、balanced / read-heavy の旧 campaign には
  記録ディレクトリ自体が無かった。選択の余地が無いのでユーザー裁定へ返さずに閉じた。
- **旧記録の限定受理は有限集合へ閉じた** ({{D:b10-legacy-45-exact-digest-set}})。
  段 2 の「歴史的な束縛の形で受理する」案は、封筒が自己 hash であるため改変記録が判定へ入る。
  段 3 のレンズ A が real な受理集合の拡大として棄却し、親が採用した。
- **完全性の開示と受理規則の境界を引き直した** ({{D:b10-completeness-is-disclosure-only}})。
- **変異は 7/7 KILLED。** 事前登録した 1 件は段 6 で意味保存と判明したため実効 gate へ照準し直した。
  probe で観測ノードを集めてから本走で完全一致を要求している。
- **子の実走はゼロだった。** 実装子と fix 子は計算ノードの queue 拒否 (`qstat -Q preflight rc=1`、
  dispatcher rc=16) で pytest を 1 件も走らせられず、テストの実測はすべて親が行った。
- **非帰属赤を推測でなく再走で実測した。** consumer 走で 3 件赤になったが、
  単独再走で 3 件とも緑。うち 2 件は迷子の `/tmp/.git` による既知の環境汚染 (F457 の型) で、
  台帳の指示どおり空 directory を `rmdir` で除去した。1 件は並行投入の直列化テストの timeout。
- submodule 初期化 tool が本 wave の 3 つ目の worktree で 2 回連続して落ち、3 回目で通った
  (F810 の再発。既存記述の「1 回目が必ず落ち 2 回目で通る」は覆る)。

## 次の一手差分

### 新規

- {{T:b10-historical-campaign-reuse-rule}} **P1・ユーザー裁定待ち**: 次の B-10 系列で
  歴史的な束縛を持つ campaign を集約へ再利用する規則を定める。今回の限定受理は
  `e3de15eb` に固定した**この系列限り**の規則で、次に driver を編集すると
  今回作る balanced / read-heavy も歴史的な束縛の側へ回り、この経路では再集約できない。
- {{T:b10-report-termination-evidence}} **P2・新規**: 集約が全ジョブの終端を機械的に確かめる
  経路を作るかどうかを決める。現在は 135 セルの照合が終端を証明せず、保証は投入手番である。
  他ジョブの終端記録へ到達する配線が要るため、本 wave では実装せず但し書きに留めた。
