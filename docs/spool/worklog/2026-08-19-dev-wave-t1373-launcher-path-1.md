---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-t1373-launcher-path
seq: 1
title: T-1373 (親の固定起動点を main checkout 側 launcher 絶対 path へ移す) を検討し実装しないと裁定した (docs のみ、branch worktree-dev-wave-t1373-launcher-path)
---

## 本文

- [T-1373] の当初アプローチ (dev-wave.md の受入 lease claim/release 呼出しを main checkout 側の
  絶対 path から起動する形に書き換える) を段2 codex plan・段3 敵対相談 2 レンズで検証した結果、
  D403 (受入投入前に待ち手の束縛 source bytes と新 tip の blob を照合する決定) が明示的に却下した
  設計と実質的に同型の帰結 (待ち手を編集する wave が main 側 waiter との sha256-mismatch で
  恒久的に受入不能になる) を招くと判明し、実装しないと裁定した。
- D524 (2026-08-18) は本アプローチを「起動権を wave tip の外へ出す唯一の形」と認めつつ D253
  抵触懸念を理由に本タスクへ先送りしていたが、D403 との整合性確保の方法までは示していなかった
  — 今回この欠落を {{D:waiter-main-launch-conflicts-with-d403}} で明確化した。
- 段2 codex plan が提案した main 絶対 path をメタ変数として argv へ埋め込む記法、および段3
  レンズB が代案とした main checkout を cwd にして起動する案のいずれも、waiter CLI の現行設計
  および `docs/pegasus-runbook.md` の既存復旧手順と技術的に整合しないことを、段3 の独立した
  2 レンズ (正しさ境界・受入実効性 / 実効性・所有範囲) が file:line で実証した。
- 副次的発見: 前 wave (段3 レンズA、2026-08-18 (659)) の byte 見積もり「2 occurrence で
  10 bytes 空く」は不正確で、実測は 12 bytes だった (今回は未実装のため非適用)。また
  dev-wave.md 現行文言「`tools/dev_wave_wait.py acceptance` で `release`」は技術的に不正確
  (`acceptance` は claim/release サブコマンドでなく内部で `tools/wave_land_window.py` を呼ぶ)
  という既知問題を再確認した (`docs/archive/worklog-phase3-0816-573.md` に既記録、本 wave では
  未修正)。
- 代替設計 (未実装、ユーザー裁定待ち): (a) acceptance_launcher.py と同型の bootstrap 層を
  waiter にも新設する、(b) 「起動権を外に出す」目的を launcher 呼出しの正しさを land 側で
  より厳密に検証する方向へ転換する、(c) 現状維持し協調境界 ([T-696]) に残す。
- [T-1337] の残件 (launcher 層の時点証明、8c 分類 API) とは編集面の重複なしを確認済み
  (worklog 596-599 行の本文照合)。

## 次の一手差分

### 完了

- [T-1373] 当初アプローチ (main checkout 側絶対 path からの直接起動) は D403 と構造的に
  矛盾するため実装しないと裁定した。代替設計 3 案をユーザー裁定へ返す。
  remaining: none
  base: ca277e5c50ca1f654b38a7539edfac5eadc25c1596c635ac964eac056d21552c
