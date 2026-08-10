---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t741-failures-supersede
seq: 2
title: [T-741] supersede 文法 wave の逐語を insights へ凍結した — 段 7 の逐語凍結を land 後に補った (docs のみ、branch worktree-dev-wave-t741-failures-supersede)
---

## 本文

- 前エントリの wave で `DW-S07` の「insights の逐語・変異台帳」を落としており、land 後に補った
  (先例 = 2026-08-10 エントリ 375 の同型の補完)。凍結先は
  `output/insights/2026-08-11_t741-failures-supersede/`。内容は段 4 裁定、敵対レンズ 2 本、
  段 6 レビュー 2 本、fix 2 本、焦点再レビュー 2 本、段 2 プラン、段 1 brief の逐語 12 件と、
  変異 spec / ledger 2 組。
- **逐語の遅延採番 placeholder は defang しなかった。** それらは fragment 文法の説明として現れる。
  fold の placeholder gate は `docs/spool/` 配下の fragment だけを走査するため
  `output/insights/**` には発火せず、`python3 tools/check_docs.py` も rc=0 だった。
  なおこの gate の実在は本追補の執筆中に実測している — 本エントリの本文へ二重波括弧の
  placeholder 記法を literal で書いたところ `spool placeholder-malformed` で拒否され、
  記法を外して緑になった。
- **受入全走は行っていない。** 本追補は docs / insights のみで production 挙動を変えない。
  判定の証拠として、実 repo を走査するテストを実走した —
  `orchestrator/tests/test_artifact_admission.py`、`test_audit_dangling_commits.py`、
  `test_check_docs.py` の 3 file で **519 passed / rc=0**。
  `check_ai_provenance.py` は 2292 件・新規違反なし。

## 次の一手差分
