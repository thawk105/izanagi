---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1218-floor-reseal-rulings
seq: 1
title: 床値 再封印の契約単位封鎖を裁定どおり撤去した — 案 3 の実行形が機械拒否されなくなり、実発行は consumer 配線より先に行ってはならないと実測で確定した (コード + docs、branch worktree-dev-wave-t1218-floor-reseal-rulings)
---

## 本文

- ユーザー裁定 (2026-08-16 /rulings 全件 第 3 回 #6) の実装。D444 決定 5 (contract 単位の 2 件目拒否) を
  issuer と index の両方から撤去し、組単位の発行前拒否へ置換した。判断の正本は
  {{D:floor-reseal-drop-per-contract-lock}}。
- **親の段 1 案 (P1) を段 4 で自ら撤回した。** resolver を「現行 (contract, HEAD pin) の組を優先し、
  無ければ現行 contract 単独一致へ fallback」へ変える案だったが、(i) D460 が「選択条件に ccbench pin を
  入れてはならない」と明記しており本裁定は D460 に触れていない、(ii) 実 driver が固定 legacy path を
  `--protocol` に渡すため authority 分裂が起こりうる、(iii) 配線は [T-419] (3)、実発行は [T-1255] の
  所有である、の 3 点による。段 3 レンズ A が (i)(ii) を blocker として提出し、親が一次資料で裏を取った。
- **段 6 の独立レビュー 2 本が同じ順序制約に到達した。** contract 単位封鎖の撤去により、
  同一 contract の record が 2 件ある状態が到達可能になる。その状態では
  `resolve_current_floor_protocol` が `count=2` で fail-closed になり床値 admission が止まる。
  したがって **実 artifact の発行 ([T-1255]) は、shell 層・driver 層・固定 path consumer の配線
  ([T-419] (3)) より先に行ってはならない**。fail-open は 1 件も見つからなかった。
- `FROZEN_MANIFEST` は不変 (23 key)。versioned artifact の登録を強制する scan・meta test・allowlist・
  checker が実在しないことを、`test_frozen_artifacts.py` / freeze allowlist / ratified freeze /
  oracle manifest / `tools/` の checker から実測して確認した。
- 実装は Codex author (D95)。親は brief・裁定・統合 commit・実測・記録のみ。
- 一次資料 = `output/insights/2026-08-17_floor-reseal-rulings/`。

## 次の一手差分

### 完了

- [T-1218] 契約単位封鎖を撤去し組単位の発行前拒否へ置換した。裁定の 3 点 (案 3 採用 /
  1 世代 1 床値の機械化なし / `FROZEN_MANIFEST` 非登録) をすべて実装し、実発行と consumer 配線は
  所有する後続タスクへ残した。
  remaining: none
  base: 9fa6e50f1c0d20aa365a59a6695a72b016c2589c2b150957c6fab04d9ecbf525

### 更新

- [T-1255] **P1・裁定済み (2026-08-17 /rulings 全件 第 4 回、AI 実行可能へ設計変更してから凍結)**:
  設計変更 (tty 防壁を明示 flag + AI provenance へ置換) に加えて、**実凍結は [T-419] (3) の
  shell 層・driver 層・固定 path consumer 配線より後に行う**。先に発行すると
  `resolve_current_floor_protocol` が `count=2` で fail-closed になり床値 submit の受理集合が空になる
  (dev-wave-t1218 の段 6 独立レビュー 2 本が実測で一致)。
  base: d75f802ec69972dbb7a49d0b870f850c7f35bcaf5aa0b6ee19eac87ca80369f7
