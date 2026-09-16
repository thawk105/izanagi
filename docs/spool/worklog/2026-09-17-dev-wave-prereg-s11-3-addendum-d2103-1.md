---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-prereg-s11-3-addendum-d2103
seq: 1
title: 事前登録 §11.3 の「生成器は本書を読まない (D1377)」を D2103 の現在地で追補訂正した (docs のみ、branch worktree-dev-wave-prereg-s11-3-addendum-d2103、変異 matrix = 実装面差分 0 で免除)
---

## 本文

- ユーザー依頼は entry 1595 [T-2723] の残存項 (台帳 ID 未起票)「`docs/phase3-b4-reflux-ablation-preregistration.md` §11.3
  末尾の『生成器は本書を読まない (D1377)』が陳腐化しているので、§11 の『未裁定の案であり規範ではない』位置づけを保ったまま
  追補で訂正する。§5 の値セルと条件契約の bytes は変えない。docs のみ・実装差分ゼロ、`check_docs.py` と凍結 hash test を
  通す。追補 1 箇所だけ」。
- **閉じた。** 一次資料は `output/insights/2026-09-17/prereg-s11-3-addendum-d2103/README.md`。設計判断は新設なし
  (D2103 の反映)。
- **現物確認で、依頼が名指す 1 行は [T-2424] 追記 (2026-09-08) が既に訂正済みだった。** 純増は T-2723 / D2103 以降の
  読み方 — floor セルの読取が §5 固定表の admission 解析 + 責任者行述語を通り、不在は strip 後 raw の `未記入` だけ、
  他欄は検査しない、D1377 の向き (floor を caller から受け取らない) は不変 — を [T-2424] 追記の直後に追記 1 箇所で書いた。
  §11.3 末尾項の条件「材料レポート側の floor 接続が裁定され実装されていること」は充足、他の条件は未充足で §7.1 の
  4 分類は実効化していない、と明記した。
- **brief の (P1)「未起票なので D70 の採番で T 番号を起票」は `docs/spool/worklog/README.md` に反証された** (次の一手に
  未登録の wave 自身へ想像の番号を title・slug・branch に使わない)。追記文・branch 名から番号を外し、角括弧 ID なしの題で
  記録した。worktree dir 名だけ EnterWorktree 命名のまま残る (dir / branch 不一致、insight に記録)。
- 実測 (login node): `check_docs.py` 違反なし (2 回)、§5 表 (行 154〜167) sha256 `1762b7cc…` と §5 全体 sha256 `cf809f11…` は
  変更前後で一致、文書の変更前 sha256 は tracked / output ともに pin 0 件、焦点走 1 (実文書を直読 6 file + 間接 4 file)
  826 passed / 370 s、焦点走 2 (最終 bytes、凍結 hash・floor issuer・admission・材料レポートの 4 file) 207 passed / 181 s。
  受入全走は記録 commit 後の最終 tip に land 前 1 回。
- 残存 (scope 外、記録のみ): §11.0「事実 (重要な限定)」段落の [T-2424] 追記にも D2103 の反映は無い (依頼が追補 1 箇所だけと
  定める)。
- 記録 commit 後の再走: `test_s8b_repo_scan_invariant` + `test_s8c_preregistration_invariant` は 15 passed / 6 skipped
  (全件 growth hold、走っていない)。実 repo の三軸語走査は `s8b_holdout_freeze search` rc=0 で直接実測。provenance full
  10,908 件・新規違反なし。
- 段 8 (自己改善): 候補 1 件「未起票の依頼に T 番号を想像で採らず branch・slug・title を主題だけにする」を `DW-S01` へ
  1 文統合しようとしたが L1 unique footprint 10,771 > 予算 10,625 bytes で赤。D782 / D730 の原則 (実害 3 例未満は実施
  しない — spool README の実害 2 例 + 本 wave の near miss) に従い実施せず、編集を戻した。上限引き上げに至らないので報告のみ。
- 工数: codex 子 0 本 (docs-only、DW-C00 の既定軽量版)。親の実測は check_docs 3 回、sha256 照合、焦点走 3 本、
  三軸語走査 1 回、provenance full 1 回。

## 次の一手差分
