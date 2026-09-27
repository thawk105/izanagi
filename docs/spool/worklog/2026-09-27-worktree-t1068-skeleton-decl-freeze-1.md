---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-27
wave: worktree-t1068-skeleton-decl-freeze
seq: 1
title: [T-1068] trigger 骨格の凍結を abort() 宣言行から BEGIN 行頭直前まで広げ、R4 / R5 / R7 の提示形と同じ関数内への移設形を build admission で拒否した。受理形は骨格のみと骨格 + S8a 計装の 2 つ、変異 7/7 KILLED (コード + テスト、branch worktree-t1068-skeleton-decl-freeze)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = `output/insights/2026-09-27/t1068-skeleton-decl-freeze/verbatim/request.md`): 2026-08-16 /rulings 全件 第 3 回 項 22 の実装。設計判断は {{D:trigger-abort-prefix-freeze}}、記録は同 insight の README。
- 起点 = local main `ad114fba0` (fresh worktree、開始 gate rc=0)。全 9 段 (設計択一が割れ、正しさ防壁に触り、受理集合が変わるため軽量版にしない)。
- 段 1 の前提確認: [T-1068] は 2026-09-26 の持ち越し整理 (D2257) で残す側、D2260 項 2 (正しさ防壁の束縛拡張の停止) の対象外。wave 開始後に T-1068 へ触れる新しい裁定は無し (裁定 inbox を段 4 直前に再走査)。
- 設計の決着: 段 1 の provisional (関数冒頭から凍結) を段 2 plan・段 3 の 2 レンズとも支持。段 6 レビュー A の must-fix 1 件 (buildcache の fixture が借用 checkout の `Transaction::abort()` を探せない) と、
  焦点走 f1 で初めて出た赤 3 件 (合成 checkout に canonical head の `#if ADD_ANALYSIS` が入り、source_digest の未知マクロ検査が fail-closed) を fix 1 巡で直した。検査は緩めず、fixture に実 CCBench と同じ形で ADD_ANALYSIS を供給した。
  レビュー B の should (import 時の宣言行 assert は plan 外) は不採用 — 切り出しの前提を守る既存 hole の RuntimeError と同型。静的レビュー 4 本は ADD_ANALYSIS の件を見落とした。
- 検査: 焦点走 f1 (commit `56b810852`、34 file) 10 failed / 5,159 passed (赤は全て fixture の形)。f2 (commit `4ea4d601d`、fix した 2 file) 271 passed。単独走は M3 で `test_campaign.py` 1 file (458 passed / 3 skipped)、
  `test_build_admission.py` は変異 probe の baseline が単独走を兼ねる。変異 final (commit `4ea4d601d`、runner = `test_build_admission.py`) baseline PASSED・7/7 KILLED・MISMATCH 0、contract-loader drift の node 0。
  受入全走は本 fragment を含む記録 commit の tip で行う (記録時点では未実施)。
- 並走: main は B-4 事前登録・T-2867・T-2207・T-2850 などの着地で前進したが、編集した 6 file・借用 fixture・source_digest・patches には触れていない (着地通知ごとに diff で確認)。
- エージェント工数: Codex 子 = plan 1・consult 2・author 1・review 2・fix 1・焦点再レビュー 1 (全て gpt-6-sol / medium)。Claude 子 = sonnet 1 (producer の棚卸し、read-only)。計算ノード job = 焦点走 2・単独走 1・変異 probe / final (各 8 run)・受入。

## 次の一手差分

### 完了

- [T-1068] trigger 骨格の宣言側と呼出依存を凍結した ({{D:trigger-abort-prefix-freeze}})。R4 / R5 / R7 の提示形と、abort() 宣言行から BEGIN 行頭直前までの領域内への移設形を拒否する。
  残る限界 (宣言行より前・前処理器・他 file・R1・R3・R6・source 不在の受理) は docstring と insight に明記し、R6 は [T-1069] のまま。
  remaining: none
  base: 224c3c3ef7451ad78c3d52a4f6c7548561cc44c00f11d7573a1d8d08e733745a
