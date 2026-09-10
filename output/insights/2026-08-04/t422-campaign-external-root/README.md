# [T-422] campaign 実行先の worktree 外部化 — wave 逐語・変異台帳 (2026-08-04)

F98 択 (iii) の 2026-08-04 ユーザー裁定 (一次控え = rulings-inbox 2026-08-03 §5) を実装した
dev-wave の逐語凍結。設計判断は decisions の当該 D (spool fragment 経由で land)、実装 commit は
`[T-422]` で始まる統合 commit を参照。

## 地図

- `brief.md` — 段 1 親 brief (前提実測 5 点、provisional 裁定 P1〜P3 込み)
- `s2-plan.md` — 段 2 codex プラン (gpt-5.6-sol / reasoning=max / read-only)
- `s3-lensA.md` / `s3-lensB.md` — 段 3 敵対相談 (正しさ境界 / 整合・実効性)。real 11 件
- `s4-ruling.md` — 段 4 親裁定 (plan v2、gate 署名、変異事前登録)
- `s5-author.md` — 段 5 実装子報告 (Codex role=author / workspace-write / reasoning=high)
- `s6-reviewA.md` / `s6-reviewB.md` — 段 6 敵対レビュー 2 本 (must-fix 7 + nit 3)
- `s6-fix.md` / `s6-refocus.md` — fix 第 1 巡と焦点再レビュー第 1 回 (NO-GO: official 過剰拒否
  の回帰 new-1、8c pin 迂回 new-2、A-5 残穴、変異証拠 new-3)
- `s6-fix2.md` / `s6-refocus2.md` — fix 第 2 巡と焦点再レビュー第 2 回 (コード面全 closed、
  変異 matrix の M14/M15/M16 追補で親が GO 裁定)
- `prompts/` — 親が各子へ渡した prompt 全文 (11 本)
- `guard_probe.py.txt` / `guard-probe-results.txt` — 段 1 前提実測 3 (guard_bash は repo 相対
  判定で、/work 配下の同形 path の rm は現行コードでも ALLOW)。結果は凍結時の再実行で再現。
  probe と `mutation/gen_mutation_specs.py.txt` は親 (Claude) 作の使い捨てで、実行資材ではなく
  凍結証拠として `.py.txt` で保存する (実装面の Codex author 契約の対象にしない)
- `mutation/` — 変異検査一式。`mutation-manifest.json` (グループ → spec sha256 → runner node)、
  spec 9 本、ledger 9 本、driver log、spec 生成器

## 結果の要点

- 変異: 9 グループ 16 変異 = **16/16 KILLED (全て期待 node と一致)**。runner を期待 killer node に
  絞り、単一理由の検出力を変異ごとに証明する構成 (harness の kill 判定は failed nodes の完全一致)
- 事前登録からの再照準 1 件: 「resolve 後 suffix 再検査の単独除去」は等価変異 (到達可能な区別
  入力は `..` 拒否と resolve 前 walk が先に塞ぐ) のため登録せず、実効 gate (`..` 拒否 = M08) へ
  再照準 (F28 の型)。post-resolve walk は walk-resolve 間の変化に対する冗長防壁として残置
- 受入: 焦点 13 node 緑 (計算ノード)、全走は worklog 当該エントリの値が正本
- 段 1 実測の含意: 外部 root は repo hooks の campaign tree 防護の外にある使い捨て領域。
  certified 材料・proof chain 素材は従来どおり repo 内 official 経路のみ (docs 側にも明記済み)
