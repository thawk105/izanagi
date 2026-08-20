---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1012-sort-oracle-collection-import-guard
seq: 1
title: '[T-1012] sort SWO oracle の pytest collection時 import を real-repo 直列化から保護した (コード+テスト、branch worktree-dev-wave-t1012-sort-oracle-collection-import-guard、変異matrix = baseline 30 passed/1 skipped・3/3 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- 前提の実測: `resolve_oracle_environment` を親プロセスで monkeypatch し `--collect-only`
  (テスト実行ゼロ) を走らせると実呼び出しが1回発火することを確認 (archive entry 524 の懸念を裏取り)。
- 段2 codex plan (1本、rc=0) は新規ノード数を「23件・89件」と誤記したが、段3 敵対相談2レンズが
  独立に「24件・90件」と訂正した (lensA/lensB とも real 所見)。
- 段4親裁定: 候補B (`_ENVIRONMENT`をpytest fixture化) を採用。段3後に `docs/decisions.md`
  D531/D532 を読み、候補C (controller-prewarm、鎖を伸ばさない設計) を検討したが実装複雑度と
  未検証の hook 順序前提を理由に本waveでは見送り、D531の方法論 (実装してから同一branch上でA/B実測)
  に従った。詳細は {{D:t1012-collection-import-guard}}。
- 段5実装: 1回目 attempt はコード自体正確・完全 (親が`git diff`で監査済み) だったが、
  親のprompt作成ミスで`## 総括`見出しの指示を書き忘れ、`check_codex_output.py`相当の検証で
  自動却下 (`accepted=false`, `launcher_rc=1`)。既存差分は変更せず検証+報告のみを行う2回目attemptで
  正式受理した。
- real-repoチェーンA/B実測 (同一commit上、node列挙による直接比較): 79.02s→119.34s
  (+40.32秒・+51%)。D531/D532 (鎖はwallの74〜78%) に照らし軽微ではないが、段4事前登録どおり
  候補B実装のまま進めた。再検討の余地は {{T:sort-oracle-collection-guard-chain-cost}} に記録。
- 変異matrix: baseline 30 passed/1 skipped、M1〜M3 全てKILLED (単一理由、matches_expectation=true)。
- `python3 tools/check_ai_provenance.py` (既定full-history) = 4468件、新規違反なし。

## 次の一手差分

### 完了

- [T-1012] pytest collection時のCCBench submodule importをREAL_REPO_SERIAL_NODESの直列化から
  独立に保護する機構 (pytest fixture化 + REAL_REPO_SERIAL_NODES/golden 24件追加 + collection
  回帰テスト) を設計・実装した。
  remaining: none
  base: 7c54fa007d25c733b7175bbd67cc84641df1206df247ae08e19878019e4dab0f

### 新規

- {{T:sort-oracle-collection-guard-chain-cost}} **P3・新規**: T-1012 が real-repo 直列鎖へ
  実測+40.32秒 (+51%、79.02s→119.34s) を追加した。D531/D532 (鎖はwallの74〜78%) に照らし
  小さくない。controller-only prewarm barrier 方式 (`real_repo_receipt_memo.py` 型、鎖を
  伸ばさない設計、候補Cとして検討済み) は実装複雑度と未検証のhook順序前提を理由にT-1012では
  見送った。鎖短縮の優先度が上がった時点で再検討する。
