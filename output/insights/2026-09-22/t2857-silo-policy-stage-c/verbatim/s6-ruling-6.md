# 段 6 裁定 6 巡目 — [T-2857] (2026-09-22 22:4x JST、親 = Claude manager)

入力: 焦点再レビュー 1 巡目 (`codex/s6-focus-1.md`、NO-GO must-fix 1・should 2、closed / partial 22 項目・regressed 0)。
coverage-4 (HEAD c7fc4846c) は待ち行列にあり、runbook §7.6 (待ち時間の短縮だけを理由に qdel しない) に従い取り消さずに走らせる。

| # | 内容 | 判定 | 扱い |
|---|---|---|---|
| K1 (must-fix) | prefix unlock の変異 patch `broken-silo-policy-no-prefix-unlock.patch` は action-abort 出口と上限出口の unlock を同時に消す。`abort0` でも lock を見ないまま CAS 失敗が 32 回続けば上限出口に届きうる (骨格は CAS 失敗も 1 周と数える) ので、action-abort 出口の検出を独立に言えない (単一理由性、DW-M01) | real | fix。出口ごとに変異 patch を分ける: 既存 `broken-silo-policy-no-prefix-unlock.patch` を action-abort 出口だけの版にし、上限出口だけの版を新しい `broken-silo-policy-no-prefix-unlock-limit.patch` として足す。各 patch はもう一方の出口の unlock を残す (1 site の `#if IZANAGI_BREAK_SILO_POLICY`)。case は conflict 側 = action-abort 出口の patch × `abort0`、limit 側 = 上限出口の patch × `retry` |
| K2 (should) | 上限出口の到達の証拠 `limit_aborts` は prefix を保持していない上限到達 (`itr == write_set_.begin()`) も数え、変異走そのものの到達でもない | real | fix。probe に「prefix を保持したままの上限出口」と「prefix を保持したままの action-abort 出口」の到達を別計数する。limit 側の変異の判定に同方策・同 workload の `focus/retry` の前者 > 0 を、conflict 側の変異の判定に同方策・同 workload の probe 走の後者 > 0 を要求する。conflict 側の到達証拠のため、焦点 case に `focus/abort0` (probe つき、`abort0`、legacy workload) を 1 本足す。別走を証拠に使う限界 (変異走そのものの到達ではない) は結果 JSON に明記する |
| K3 (should) | 記録の訂正: coverage-3 は 30 case ではなく 32 case (共有対照 5 件を含む)。`maxwait` が上限出口に届かなかったことは、probe 無効の走からは直接確かめておらず推定である | real | 記録 (insight・fragment) で訂正する。実装変更なし |

変異の事前登録の追加 (DW-M01、fix 前): M-PREFIX-REACH = limit 側の到達要件 (prefix 保持下の上限到達 > 0) を外す → prefix 保持下の到達 0 の観測が合格になる。kill 点 = fix 子が書く `test_prefix_limit_requires_prefix_held_limit_reach`。
