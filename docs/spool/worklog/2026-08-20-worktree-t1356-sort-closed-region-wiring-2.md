---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: worktree-t1356-sort-closed-region-wiring
seq: 2
title: '[T-1356] 受入全走で発見した originless baseline 未追随を修正した (テスト、branch worktree-t1356-sort-closed-region-wiring)'
---

## 本文

- 受入全走 (1回目) で `test_reflux_originless_compatibility.py` の赤を検出。
  当初「別waveのplanner-v4 pin変更が原因」と誤診断し main 側の解消待ちで無人ループしたが、
  acceptance-red-check.json の実測 (`main_rerun_rc=0`・`wave_rerun_rc=1`) を精査して
  **本 wave 自身 (auditor.md 編集) が原因**と訂正した。詳細は {{F:originless-baseline-role-hash-drift}}。
- 一時計装 (assert 直前に実際値/期待値を JSON dump) で正確な新旧 hash 値
  (`role_file_sha256`・`effective_prompt_sha256`) を特定し、Codex fix で
  `_PRE_WAVE_ORIGINLESS_BASELINE` を追随させた (commit 済み)。
- **セッション異常: 計装除去に `git checkout --` を使い、まだ commit 前だった Codex fix の
  内容ごと2回巻き戻した。** uncommitted な複数レイヤー (fix + 自分の一時計装) が同一
  ファイルに重なっているとき、`git checkout --` は全部消す。教訓は memory
  `git-checkout-dash-dash-wipes-all-uncommitted-layers` に保存し、以後は
  「fixを当てたら計装を足す前に必ずcommitする」を徹底する。
- **セッション異常: main 取り込みで別 wave (`workload-policy-hint-impl`) と
  `review_ledger.py` の別キーが file 単位で重複し、merge commit が D95 (Codex role=author
  必須) に抵触して待ち手の自動 merge 手順が進めなくなった。** known-violation 台帳
  ([T-614] 裁定、2026-08-07) は6件限定の裁定が根拠で新規追加の標準裁定と読めなかったため、
  ユーザーへ確認 (「あなたが作った赤ですか」「今も変わらないですか」「何が悪いのか分からない、
  仕事を進めて」) の上、`git rebase main` で線形履歴化し回避した (5 commit 無競合で自動適用、
  再監査 rc=0)。rebase 後は commit hash が変わるため、既に書いた insights README の hash
  参照を訂正する追加 commit を1本挟んだ。

## 次の一手差分
