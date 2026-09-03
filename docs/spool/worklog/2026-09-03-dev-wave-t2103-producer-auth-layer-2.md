---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-t2103-producer-auth-layer
seq: 2
title: 段 8 — 実測した dev-wave 手順 3 件が byte 予算に収まらず裁定へ返す (docs のみ、branch worktree-dev-wave-t2103-producer-auth-layer)
---

## 本文

T-2103 の段 8。本 wave で実測した作法の欠陥 4 件を裁定した。

- submodule 初期化ツールの rc と実状態の食い違いは {{F:submodule-init-rc-contradicts-state}} へ送った。
- 残る 3 件は `docs/dev-wave/operations.md` へ統合しようとしたが、`tools/check_docs.py` が
  3 つの違反で拒否した。DW-O26 は節全体が exact 契約で pin されており文言を変えられない。
  DW-O27 は単節予算 1000 bytes を超え、`docs/dev-wave/**` の L1 footprint も
  10743 > 10625 bytes となった。main の現物は clean であり、超過は本 wave の追記が原因である。
  安全義務を削って予算を作らず、編集を撤回して裁定へ返した。
- 3 件はいずれも今回実際に踏んだもので、仮想的懸念ではない。land を 1 回落とし、
  受入の結果を 1 回誤読し、受入全走まで赤の発見が遅れた。

## 次の一手差分

### 新規

- {{T:dev-wave-land-cwd-requirement}} **P2・新規**: `tools/dev_wave_land.py` は対象 wave worktree を
  cwd にして起動しないと rc=22 `cwd must be the exact wave worktree` で拒否する。DW-O23 に記載がなく
  land を 1 回落とした。予算内へ統合する方法を決める (DW-O23 の既存文の縮約か、L1 予算の見直しか)。
- {{T:dev-wave-acceptance-log-path-reuse}} **P2・新規**: `dev_wave_wait.py acceptance` の
  `--log-file` は既存 file があると `acceptance-log-preflight` rc=2 で即停止する。前回の log が
  残るため、古い赤を今回の結果と誤読しうる (本 wave で実際に誤読しかけた)。再投入時に
  log/receipt を新 path にする義務を DW-O27 の予算内へ収める方法を決める。
- {{T:dev-wave-focus-inventory-tests}} **P2・新規**: DW-O26 の「新規 test file を足す走は file 集合
  列挙のメタテストも焦点走に含める」は範囲が狭い。subprocess を起動する module を足すと、
  process 起動一覧と subprocess guard も落ちる (本 wave の受入で 4 件中 3 件がこれ)。
  DW-O26 は節全体が exact 契約で pin されているため、契約側の更新とセットで行う必要がある。
