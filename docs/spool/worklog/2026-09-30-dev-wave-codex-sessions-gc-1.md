---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-codex-sessions-gc
seq: 1
title: ~/.codex/sessions を 20G から 686M へ掃除した — izanagi の自動経路は古い rollout を読まないことを棚卸しと空 CODEX_HOME の実走で確かめ、2026/08/01〜09/27 を検証付きで /work へ退避してから削除した (docs + insight、branch worktree-dev-wave-codex-sessions-gc)
---

## 本文

- ユーザー依頼: 肥大した `~/.codex/sessions` をほぼ全部消したいが、izanagi が依存していて壊れる懸念がある。調べて依存があれば解消し、掃除する。
- 結論: 古い rollout に依存する自動経路 (dev-wave 各段・受入・land・provenance 監査・usage 集計・hooks) は無く、コード変更は不要。守るべきは走行中の codex 子の rollout だけ。詳細・退避先・復元手順は `output/insights/2026-09-30/codex-sessions-gc/README.md`。
- 挙動確認: `CODEX_HOME` を空 dir に向けた codex 系 5 test file の計算ノード走行で 1003 passed, 2 skipped (request 37539.nqsv)。
- 段 3 相当の Codex 2 レンズ相談 (sol 決定・luna 攻撃、read-only、両出力とも check_codex_output rc=0) を経て、段 4 で「実装しない」と裁定し段 5・6 を省いた。luna の成立攻撃 3 件 (開いている file の保護では走行中の子を守れない / tar の sha だけでは受領証の封印 rollout の退避を示せない / ledger は空でも rc=0 で 0 を出す) は、直近 2 日更新 0 件の確認と 9/28 以降の保持、受領証参照 52 件の照合 (一致 33・封印値なし 5・不一致 0・既欠損 14 は全て 2026/07)、退避物 README への注記で閉じた。
- 退避: `/work/1/SFC/tanab/archive/codex-sessions-2026-09-30/` に 11,918 file (19.8G) を zstd tar 1 本 (2.88G) にし、展開して全件 sha256 照合一致 (request 37665.nqsv)。削除直前に現物と退避一覧の完全一致を確かめてから削除し、`/home` 使用量は 36G → 18G。
- 変異 matrix・受入全走: 実装面の差分ゼロのため変異 matrix は免除。受入は land の縮小受入に委ねる。
- 定期剪定の機構化は起票しない: 今回の手作業 (直近 3 日を残し検証付き退避の後に削除) で足り、再び肥大するまで要求が無い (DW-G05)。再発時は insight の手順を繰り返す。

## 次の一手差分
