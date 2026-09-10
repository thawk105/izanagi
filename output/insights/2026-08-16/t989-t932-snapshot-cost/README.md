# [T-989] / [T-932] — snapshot 構築費の定数化と成長比例テストの恒久保留

- wave: `dev-wave-t989-t932-snapshot-cost` (2026-08-16)
- branch: `worktree-dev-wave-t989-t932-snapshot-cost`
- base: local main `518a87e1`

## 中身

| file | 内容 |
|---|---|
| `hold-list-for-user.md` | **D335 が要求するユーザー提示用の保留一覧** (追加 27 件 + 軸訂正 14 件) |
| `measurements.md` | 親の実測台帳 (前後値・段別内訳・erratum 2 件) |
| `mutation-spec.json` | 変異事前登録 (本走で使った 6 件) |
| `mutation-ledger-probe.json` | 変異 **probe 走** の台帳 (期待 node 再導出前、7 件登録) |
| `verbatim/s4-adjudication.md` | 段 4 裁定 (段 3 の 14 所見を real/refuted で裁いたもの) |
| `verbatim/s3-consult-*.md` | 段 3 敵対相談 2 本の逐語 |
| `verbatim/s6-review-*.md` | 段 6 敵対レビュー 2 本の逐語 |

## 主な数値 (静かな窓の 3 走中央値、D357)

| 量 | 前 | 後 |
|---|---|---|
| `benchmark_snapshots` fixture 全列 | 43.72 s | **20.83 s** |
| `_build_snapshot_base` | 35.02 s | **10.31 s** |
| root repository の seal | 26.30 s | **0.33 s** |
| submodule の seal 合計 | 2.82 s | 2.04 s (固定費) |
| `_derive_snapshot_from_base` x2 | 8.44 s | 8.02 s (変化なし) |

closure の不変条件は前後で完全一致した (reason 0 件 / object 8,209 / commit 834 /
`.git` 35,132 KB / commit-graph 不在 / 残留 pseudo ref 0 件)。

## 主張してよいこと・いけないこと

**書いてよい:** 「支配的な線形項 (全 object の `repack -Ad`) を除去した」。

**書いてはいけない:**

- 「commit 数から完全に切り離した」— `pack-objects` は source の object 数に弱く比例する
  (実測 0.32 s 対 0.065 s、object 数 6.1 倍に対し時間 4.8 倍)。
  正しくは「残る比例項は係数が約 100 分の 1」。
- 「受入 wall が N 秒短縮された」— `--dist loadgroup` で real-repo group は単一 worker へ
  集約されるが、別 worker が最長なら wall は動かない。worker 上限は 32。
- 「残る律速は copytree」— 逐次計時で copytree は 0.21〜0.24 s/case、
  実体は `verify_snapshot` の 3.62〜7.38 s/case である (`measurements.md` の erratum 2)。

## 保留の判断

`benchmark_snapshots` の consumer 17 本のうち 14 本は既に保留済みで、
残り 3 本は**保留しなかった**。保留すると `_one_git_closure_reasons` の reason 集合を守る
既定走行 node がゼロになるためである (規律 2)。詳細は `verbatim/s4-adjudication.md` の 5-1。
