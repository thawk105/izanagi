---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: rulings-t1490-known-violation
seq: 1
title: [T-1490] known-violation 台帳登録を採用する方針をユーザー裁定で確定した (docsのみ、branch worktree-rulings-t1490-known-violation)
---

## 本文

- `/rulings all 説明付き` の索引で提示した T-1490 (commit `09ce607b` に AI 関与を示す
  trailer が一切無く、全履歴 provenance 監査で `missing-ai-agent` として検出される件) に
  ついて、ユーザーが rulings の推奨案をそのまま採用する裁定を下した (2026-08-22)。
- 採用: `tools/check_ai_provenance.py` の `KNOWN_PROVENANCE_VIOLATIONS` へ、
  commit `09ce607b` (`chore(ccbench): MOCCへcorrectness trace v2 hookを追加
  (pin 511c9538→ef9328a3)`、author=thawk105、AI 非関与の直接 commit、本文・trailer
  とも空) を kind=`missing-ai-agent` として登録する。直近の
  `dev-wave-t1479-known-violation-merge-authorship` wave など既存の同型登録と同じ
  手続きに従う。
- 却下: `AI-Agent-Waiver` trailer による個別承認 (D105)。waiver は commit 時点で本人が
  付けるための仕組みであり、確定済み過去 commit への後付けは履歴書き換えを要するため
  本件には不適合と判断した。
- 実装 (`tools/check_ai_provenance.py` と対応テストという実装面の変更) は Codex author を
  要するため、本 rulings session では行わない。別 dev-wave が本記録を brief の入力として
  着手する。

## 次の一手差分

### 更新

- [T-1490] **P1・dev-wave 起票待ち**: `tools/check_ai_provenance.py` の
  `KNOWN_PROVENANCE_VIOLATIONS` へ commit `09ce607b` を kind=`missing-ai-agent` として
  登録する (ユーザー選択: known-violation 登録)。理由 note には pin bump の内容・AI
  非関与・登録の経緯を明記する。対応する `orchestrator/tests/test_check_ai_provenance.py`
  の literal 一致テストを更新し、`python3 tools/run_tests.py
  orchestrator/tests/test_check_ai_provenance.py` を全走させて確認する。rulings
  session からは直接投入しない。
  base: fcc4710ddcffc3ba583f114d3c0dc9061b9d6c410cd2c1a2663268ed194d4a1e
