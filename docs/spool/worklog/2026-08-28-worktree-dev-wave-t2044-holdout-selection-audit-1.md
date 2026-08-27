---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: worktree-dev-wave-t2044-holdout-selection-audit
seq: 1
title: [T-2044] holdout 値の事後選択防壁を限定監査し、守られていないと主張上限を固定した (docs のみ、branch worktree-dev-wave-t2044-holdout-selection-audit、実装面差分 0)
---

## 本文

- 一回性撤去後の consumer 閉包を固定 commit `f34e19be94a3608099773ac6c1a12a98ae992048` で監査した。稼働 worktree / process / job artifact に T-2044 所有の別 wave は 0 件だった。
- **守られていない。** 現 commit は official 拒否と budget approval 未批准で到達不能だが、両者は使用 result を値を見る前に固定しない。独立 blocker 解消後は、適格な fresh A/B の値を見て B を最初の `--floor-result` に選ぶ経路が real である。
- `_assert_official_permitted` は production callsite 2、別 CLI 拒否 1。floor-result の `eligible_for_refreeze` direct production read は 4、structural schema contract 1、同名別 family 1。test textual reference は前者 10、後者 31 で、runtime 防壁に数えていない。
- candidate→ratified g1 の path/hash 自動束縛は 0、ratified `floor` と `floor_source.result.floors` の投影一致検査も 0。create-only は初回 B 選択後の上書きだけを防ぐ。
- floor 数値が s8b oracle winner/tie-break と s8c conclusion を直接変える経路は refuted。ただし選んだ artifact の binary receipt/store 再検証は oracle verdict の可用性へ影響し、s8c publish は path/hash provenance を使う。s8c 公開3関数の production callsite は 0。
- D893 は同一試行識別子の複製を対象とし、異なる fresh A/B は D1124 の禁止面である。T-469 は未実装なので防壁に数えない。
- 主張上限は {{D:t2044-holdout-selection-claim-cap}}。測定前固定の既存 proof が示されない floor-backed candidate・再凍結・主張は advisory / non-certifying。狭い floor 数値非干渉だけを別に維持する。
- 関連 test 6 file は `tools/run_tests.py` 経由で 621 passed / 2 skipped、rc=0、677.74 秒。skip 2 件は explicit-user-command-only growth hold。floor / oracle / 8c 本走と性能測定は 0 件で、未実走を緑と書いていない。
- read-only Codex は plan 1 本・敵対相談 2 本、全て output 検査 rc=0。実装面差分 0 のため段 5・6・変異 matrix を免除した。証拠索引は `output/insights/2026-08-28_t2044-holdout-selection-audit/README.md`。

## 次の一手差分

### 完了

- [T-2044] consumer 全数、A/B 経路、主張上限、scope 外を記録し、実装差分なしで限定監査を完了した。
  remaining: none
  base: a8247056d7431b8aad42b74e5c18f3deeca6495711c7e0614f1da2b02a0aa816

### 新規

- {{T:t2044-floor-source-authority-ruling}} **P1・ユーザー裁定待ち**: 将来 official 解禁後の強い floor-backed claim を許す前に、D1124 の「値を見る前の使用測定固定」をどの既存 authority が証明するかを裁定する。既存 authority で証明不能なら実装は別 waveへ分離し、D95 Codex author を必須とする。本 wave では新 guardrail、署名、台帳、nonce、one-shot 代替を設計・実装しない。
