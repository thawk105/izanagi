---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: dev-wave-cleanup-skill-revision
seq: 3
---

## 新規

### {{F:cleanup-skill-margin-under-h2-probe}}. cleanup Codex skill を予算余白 18 bytes まで伸ばし、25 bytes の H2 を足す負例テストが予算超過と SHA 不一致の 2 件で赤になった [手順漏れ] [テスト代表性]

- 事象: 2026-09-30、`/cleanup-branches` 改訂 wave の段 6 fix で `.agents/skills/cleanup-branches/SKILL.md` を 3,082 bytes (予算 3,100) にした。
  変異 probe の baseline で `orchestrator/tests/test_check_docs.py::test_cleanup_skill_additional_h2_is_rejected` が赤
  (`"\n## destructive override\n"` 25 bytes を足すと 3,107 > 3,100 になり、期待 1 件の SHA 不一致に予算超過が重なった)。受入前に捕まり、fix を 1 巡余分に要した。
- 根本原因: whole-file pin の「完成本文 + 余白 3」は command 側の 1 byte 追加の負例に合わせた値で、SKILL.md には 25 bytes を足す負例がある。
  親は SKILL.md の余白を負例の追加 bytes と照合しなかった。login では pytest が guard に拒否され、check_docs 緑だけでは気づけない。
- 恒久対応: memory `exact-pinned-leaf-sections-need-codex-and-fixture-placeholder` に「SKILL.md は予算 − 25 以下 (余白 26 以上)」を追記。
  本 wave は上限を変えず SKILL.md を 3,058 bytes に縮めた ({{D:cleanup-stale-delete-default}} の wave、commit 4bdda232e・6f4062b37)。
- 再発検知: 変異 harness の baseline 緑要件 (DW-C01) が同 test の赤で起動を止める。
