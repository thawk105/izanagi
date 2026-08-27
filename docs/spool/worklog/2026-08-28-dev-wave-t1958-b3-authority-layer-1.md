---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: dev-wave-t1958-b3-authority-layer
seq: 1
title: [T-1958] B-3 の 3 成果物を権威層に従属する下流症状として論文素材へ反映した (docs、branch worktree-dev-wave-t1958-b3-authority-layer、実装差分なし)
---

## 本文

- 起動時に T-1940 の記録 commit `da2b8a36f` が main の祖先で、専用 handoff が残っていないことを
  確認した。全 worktree の exact path を再走査し、`docs/paper-story/README.md`、後継本文、
  claim-evidence の所有競合は 0。T-2044 の一時差分は `figures/` だけだった。
- 凍結済み `2026-08-26.md` と `claim-evidence/2026-08-26.md` は 1 byte も変えず、README の
  「最新スナップショット以後に確定したこと」へ 1 hunk を追加した。一項目だけの新日付版は
  append-only 契約に反するため作っていない。
- 「両経路は事前登録 artifact 3 件の不在に阻まれる」を保持しつつ、3 件は独立した最上流 blocker
  ではなく、共有批准凍結の発効と成果物導出権威の実体配線の両方に従属する下流症状だと明記した。
  両上流条件の相互順序は canonical D から導出できないため新設せず、D930 の承認権限と
  claim-evidence の分類語 `[権威 bytes]` も成果物導出権威と同一視していない。
- plan 1 本、敵対相談 2 本、完成差分レビュー 2 本を Codex `gpt-5.6-sol` / xhigh で実施した。
  敵対相談 2 本は親初案の三段全順序を過大と独立に指摘し、部分順序へ訂正した。完成差分レビューは
  2 本とも must-fix 0。docs-only なので D95 author と変異 matrix は免除した。
- 受入 attempt 1 は `1 failed / 18464 passed / 62 skipped`。唯一の赤は
  `test_check_receipt_reads_v1_field_sets_with_explicit_skip_diagnostics[False]` の check subprocess が
  stdout 空となる `JSONDecodeError`。同一 tip の exact node 単独走は `1 passed in 5.60s`、
  attempt 2 は `18499 passed / 62 skipped` の `child-green`。赤時の login node load average は
  `133.54 / 92.32 / 60.27`、並行 Codex launcher は 4 本で、F273 の既知型と整合した。
- ユーザーは flake の known-violation hold と、後続での原因分析・修理・再導入を指示した。
  D95 author は registry 追加を試みたが、canonical F273 に exact function 名が無く validator が
  fail-closed した。台帳直書き・validator 緩和はせず、本 wave の F273 再発 fragment を先に fold し、
  次 wave で exact-node hold を登録する二段へ分けた。author の実装差分は 0、未実走。
- `git diff --check`、`check_codex_agents.py`、`check_docs.py`、commit 後の全史 provenance は緑。
  性能測定、新規数値導出、論文生成器、汎用 narrative system、追加安全機構は実施していない。

## 次の一手差分

### 完了

- [T-1958] B-3 の閂説明へ D959 / D1204 の権威層と従属関係を反映した。
  remaining: none
  base: d0bcd194144ef608860eabe34386a434ea1475e11b787700274075eae5caf3fc

### 新規

- {{T:codex-worker-v1-receipt-flake-hold}} **P1・新規**: F273 の再発が canonical へ fold された後、
  `test_check_receipt_reads_v1_field_sets_with_explicit_skip_diagnostics[False]` を
  `flaky_test_holds.py` へ exact node で登録する。他 node、timeout、失敗条件は変えない。
- {{T:codex-worker-v1-receipt-flake-reintroduction}} **P1・新規**: 上記 hold に従属して、check subprocess の
  stdout が高負荷下で空になる原因を分析し、根本修理を独立に実装・検証してから hold を外し、
  acceptance 母集団へ再導入する。負荷仮説を原因確定として先取りしない。

