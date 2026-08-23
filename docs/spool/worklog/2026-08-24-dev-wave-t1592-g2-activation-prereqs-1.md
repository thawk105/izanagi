---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-t1592-g2-activation-prereqs
seq: 1
title: [T-1592] pegasus g1→g2 activation の実測前提条件表を作った (docs のみ、branch worktree-dev-wave-t1592-g2-activation-prereqs)
---

## 本文

- `docs/env-contract-activation-prerequisites.md` を、条件を再定義しない日付・commit 付き readiness index
  として作った。g2 registry / 較正は充足済みだが、official candidate bytes、上位権限束の段 0、
  paired freeze、pre-X 段が未充足なので、総合結論は `未充足` である。
- 段 0 は `incomplete` (pending 5、applicable unresolved 2、blocking gate 4)。さらに「後続全段の
  前提」と「段 1 以降 owner の fixture assignment を段 0 blocker に数える」の開始順が未解決で、
  本 wave は解決方法や owner を発明せず `unassigned` と記録した。
- read-only prospective serial 2 は検証に通ったが transient calculation に留め、official candidate / record
  の代用にしなかった。D437/D444 の lockstep・人間 seal と規律 2 を維持し、activation は実施していない。
- member 2 / member 8 / member registry gate と rr80/rr20 登録は downstream / 独立入力へ分離した。
  rr80/rr20 の repo 外 bytes を再 hash し、D716 どおり g1→g2 activation 後まで tracked 登録しない。
- 段 3・6 の敵対 review で real finding 12 件を採用し、fix 後の焦点 review は 7/7 closed、
  partial / regressed / 新規 must-fix 0 件だった。
- 焦点テストは 696 passed / 3 skipped。起動時 base `768e9fe6` の全走は
  `test_cli_base_digest_real_corpus_resolves_active_and_rejects_completed` だけ赤
  (14832 passed / 67 skipped) で単独再現したが、並行で進んだ local main `26c8979f` では同 nodeid が
  1 passed。差分非到達の stale-base 赤として、main 取込み後の正式受入で再確認する。
- `check_codex_agents.py` は成功、`check_docs.py` は違反なし (既存 handoff 書式警告 2 件のみ)。

## 次の一手差分

### 完了

- [T-1592] activation の必要条件・現在値・証拠・未充足理由・owner を実測し、正本を二重化しない
  readiness index として canonical docs に置いた。activation、holdout 解禁、保存 bytes 登録は実施していない。
  remaining: none
  base: 2afc70f00431dd6afd56c6115dfae2ac5187938402c20e05685dcae8a0016bf7
