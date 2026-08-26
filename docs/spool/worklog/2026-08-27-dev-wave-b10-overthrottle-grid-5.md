---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-b10-overthrottle-grid
seq: 5
title: 投入 script が実在しないコマンドを必須にしていたのを着地後の初回起動で見つけて直した (コード + テスト、branch worktree-dev-wave-b10-overthrottle-grid)
---

## 本文

前エントリで着地させた B-10 拡張格子の投入 script を実機で初めて起動したところ、
必須コマンド `quota` の不在で rc=2 になり**永久に起動できない**状態だった
({{F:submitter-required-command-absent}})。正しくは `check_quota` である。

**この型は受入全走では捕まらない。** script を実機で起動して初めて出る。しかも
新しい Pegasus 実行体は登録簿が main へ着地するまで hook に拒否されて起動できないので、
**着地後の初回起動でしか発見できない**構造になっていた。

並行 3 セッションとの相談で得た実測も記録しておく。

- `--landing-wave-tip-sha` の forward main merge 経路は**機械的に清潔な merge 限定**で、
  競合解消を 1 件でも伴うと `rc=23` で拒否され受入再走になる。受入緑を取ってから
  他 wave が同じ登録簿・在庫へ項目を足すと必ず競合するので、再走を見込む必要がある。
- 競合 file に `tools/pegasus/admission_registry.json` が含まれると、その working bytes が
  HEAD と一致しなくなり **codex 子が段を問わず起動できない**。「親が merge、子が競合解消」の
  分担がこの file が競合したときだけ機構的に成立しない。代行せず、merge 前の clean な木で
  取り込み後の最終内容を Codex `role=author` に書かせ、親が適用する形で解いた。
  親が独立に手で解消した結果と突き合わせ、5 file 中 3 file が byte 一致、
  2 file は並び順のみ相違 (ASCII 昇順の author 版を採用) だった。
- **両 wave が独立に同じ合計値を N から N+1 へ変えると、その行は競合せず実体だけが N+2 になる。**
  `test_campaign.py` の caller 在庫で実測。自動 merge が「競合なし」で通す型である。
- **「在庫を閉じる」変更が、稼働中 wave の refactor と食い違う型がある。**
  別 wave が spawn 在庫へ起動点を `measure` として追加した時点で、この wave は同じ起動を
  ヘルパへ移していた。記録と実体が別 file にあり、どちらの変更も相手の行に触れないので
  競合として現れず、受入全走で初めて出た。**記録を実体に合わせ、実体は戻さなかった**
  (ヘルパは単独性検査と bench lock を伴う正しい配置で、記録の都合で規律側を緩めない)。

## 次の一手差分

### 更新

- [T-1940] **P1**: B-10 拡張格子の実測を 3 workload 投入して回収する。
  投入 script の必須コマンドを直したので起動できる状態になった。
  `tools/pegasus/submit_b10_backoff_grid.sh --output-parent <repo 外の絶対 path>`。
  base: 14f44a6a3650803822164efec8a8123b4af6eda906406fb1a8a31e3711165e54
