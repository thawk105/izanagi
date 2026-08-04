# 2026-08-04 — [T-425] Pegasus floor scoping 安価測定と取得設計裁定パッケージ (逐語)

dev-wave (branch `worktree-wave-t425-floor-scoping`) の一次資料。裁定と要約は worklog 本エントリが
正本で、ここは加工前の資料だけを置く。**scoping 値は floor でも品質ゲートでもない**
((162) 裁定、D145 決定 1〜2)。JSON 自身が `eligible_for_compare=false` /
`time_window_clusters=1` を刻み、命名は consumer glob (`between_run_noise_*.json`) に不可視。

| ファイル | 出所 | 役割 |
|---|---|---|
| `00-parent-brief.md` | 親 (Claude) | 段 1 brief。(P1)〜(P4)。軽量版判定の根拠 (v1 原文 — K=8 等の誤りは 02 の v4 が訂正) |
| `01-s4-ruling.md` | 親 (Claude) | 段 4 裁定。プラン v2 と変異 M1〜M4 事前登録 (原文 — 「rr5 は分散最大側」は 03 の ADV-04 が反証) |
| `02-ruling-package.md` | 親 (Claude)、codex レンズ 3 巡で検証 | ユーザーへ返す取得設計裁定パッケージ **v4** (U-1〜U-7、推奨 = K=15 固定・逐次増補なし・層 C scalar 限定・実判定は calibration 既定)。可変の正本は `/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md` |
| `03-lens-review.md` | codex `gpt-5.6-sol` / reasoning=max / read-only | 段 6 敵対レンズ 1 巡目 (統計 + 台帳整合)。v1 に NO-GO (ADV-01〜10、全件 real 採用) |
| `04-lens2-focal-review.md` | 同上 (別 context) | 2 巡目焦点再検。closed 7 / partial 3 / regressed 0 + ADV2-01 → v3 で反映 |
| `05-lens3-final-check.md` | 同上 (別 context) | 3 巡目 (上限)。ADV-01/04/ADV2-01 closed、残 ADV3-01 は親が real 裁定し v4 (nominal 表の適用限定 + calibration 既定化) で閉じた |
| `scoping_between_run_t48_skew0p9_rr5_rmw0.json` | 計算ノード bnode138 | write-heavy 実測。同窓 between CV 0.786% / within 2.071% (abort 77.1% は within 代表 rep の値) |
| `scoping_between_run_t48_skew0p9_rr50_rmw0.json` | 同上 | balanced 実測。同窓 between CV 0.345% / within 0.964% (abort 67.3% は同上) |
| `mutation-ledger.json` | tools/mutation_harness.py (dispatch mode) | M1〜M4 = 4/4 KILLED、baseline PASSED @ 5bec729 |

## 取得条件

- request 887785.nqsv (gen_S、1 node、bnode138)、2026-08-04 21:33–21:39 (387 秒)、
  commit 5bec729 の committed bytes を repo 外 checkout
  (`/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/run/izanagi`) で実行。
- perf は preflight fallback が発火し `/usr/lib/linux-tools-5.15.0-100/perf`
  (version 5.15.143) を採用 — 割当ノードに kernel 一致の linux-tools が無い個体差があり、
  初回 885102.nqsv (bnode074) は perf 不在で全 rep 失敗 (43 秒で fail-fast)。
- 単一テナント検査は `_assert_single_tenant` (競合 bench pid) のみ。gen_S は Exclusive OFF
  で、他ユーザープロセス・fabric/電力の common-mode は捉えない (解釈制約、(162) レンズ A5)。

## 読みどころ

- 同窓 between < within が Pegasus でも再現 (linux 3 点と同構図)。事前規定 (U-5) どおり
  安定性の証明とは解釈しない。
- レンズ 3 巡が v1 の estimand 混線・検出力設計不在・算術誤り (「約 2 倍で逆転」→ 正 1.50 倍)・
  費用過大 (0.7 → 実測 0.08 node-hour/窓) を検出し、v4 で全訂正。**scoping 値は K 推薦の根拠に
  使わない** (署名間非転移、D145 決定 4) — K は設計感度 × 検出力の裁定 (χ² nominal 表) で選ぶ。
- 推奨 = K=15 固定 (設計感度 1.5% で検出力 0.976、約 1.3 node-hours)、逐次増補なし、
  estimand は consumer と同じ 1 session-median 周辺 CV、official 8b/8c per-pair には触れない
  (U-7)。裁定パッケージ v4 §2〜§3 が正本。
