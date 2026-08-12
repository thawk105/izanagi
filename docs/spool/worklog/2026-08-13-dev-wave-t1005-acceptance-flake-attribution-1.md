---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t1005-acceptance-flake-attribution
seq: 1
title: 受入全走フレーク (F57 族) の機序を特定した — 予算の縁に張り付いた設計で、判定情報は保存されていなかった (docs のみ、branch worktree-dev-wave-t1005-acceptance-flake-attribution)
---

## 本文

- [T-1005] の診断 wave。**実装差分ゼロ。** 恒久対応の採否は裁定へ返した
  (`output/insights/2026-08-13_t1005-acceptance-flake-attribution/package.md` の R1〜R4)。
- **最重要の実測。** 2026-08-13 の受入走 A (`acceptance.log`、bnode130、request 908484) の
  失敗 21 件すべてに receipt の job 側 wall clock が残っており、実測は
  **3.0099 / 3.0460 / 3.1160 / 3.1369 / 3.2324 / 3.2650 …** 秒だった。
  テストが渡す予算は **3.0 秒ちょうど**で、超過幅は **0.010〜0.265 秒 (0.3%〜9%)** しかない。
  「多秒の停止」ではなく **48 並列下で所要が予算の縁に常時張り付いている**状態である。
  これで F57 の未説明の性質 (失敗 node の移動・単独走で非再現・loadavg 非相関・件数の振れ) が
  揃って説明できる。詳細は {{F:acceptance-flake-budget-margin}}。
- **一見矛盾した診断行の正体。** 「予算 3 秒に対し `wall_clock_s=0.716` で wall 超過」は、
  wall gate が **job clock** (`codex_worker_launch.py:1244`、起点 `:35` の module import) で判定し、
  失敗診断は **attempt clock** (`:1540`、起点 `:1347`) を印字するためである。
  段 3 レンズ A は attempt clock で wall 判定する経路を探索し、存在しないことを確認した。
- **段 3 の敵対 2 レンズは 16 所見を返し、全件 real・refuted ゼロ。うち 8 件が親の brief を
  直接壊した。** 親は全件を実装と一次資料で確認し、次を撤回した。
  (1) 「attempt clock の起点は `Popen` 直前」→ `:1347` で hook 検証より前。
  (2) 「job clock は receipt に残らない」→ `:1702-1704` で `actuals.wall_clock_s` を上書き。
  (3) 「`max_wall_clock_s` を立てるのは 3 箇所」→ `_latch_final_job_limit` (`:1954-1977`) が
  attempt 後にも設定する。(4) 「0.716 秒から前処理 2.28 秒以上が逆算できる」→ post-attempt
  監査を含むので逆算不能。(5) 「loadavg 完全一致 = 同時被弾」→ loadavg は pytest 側が
  診断を組む時点で読む (`test:372-400`)。(6) 「1 バースト 1 近接原因」→ 実装が `if/elif` で
  複数原因を単一 field へ縮約する (`:1461-1475`)。
  **撤回の代わりに得たのが上記の縁張り付きの実測である** (レンズ A が一次資料から掘り出した)。
- **規律 3 に従い判定不能を判定不能として残した。** 走 B / C の述語はコード経路としては実在するが、
  `codex_exit_code=-9` は外部 SIGKILL と識別不能、`evidence_forced_stop` は receipt に出ない、
  `residual=None` の出所は 4 つ以上あって区別されない。
  **F57 が 20 回以上「未確定」だったのは解析不足ではなく、判定に使った情報が保存されないため**である。
- **併発条件。** 計算ノードは gen_S で affinity 全数 48 = 実質専有なので co-tenancy ではない
  (3 バーストは別ノード)。**並行 codex 子は判別子でない** — 2026-08-13 の窓では codex 子は
  緑の走 (02:03・02:45) とも重なっていた。これは [T-139] land2 の K5
  (受入 lease を他 wave の codex 子まで広げるか) の**親推奨「現状維持」を支持する実測**である
  (K5 の裁定自体は scope 外につき触っていない)。「共有 Lustre が原因」までは分離できておらず、
  未分離として返した。
- **限界。** 併発 worktree の多くが既に撤去され dispatch receipt が残らないため、
  クラスタ横断の同時実行数は事後再構成できなかった (残存 log の完了時刻の重なりまで)。
- 起動時に {{F:landed-handoff-blocks-startup-check}} を踏んだ。記録のうえ続行した。
  **本 wave が 07:32 JST に踏んだ 36 分後、別セッションが独立に同じ赤へ当たり、main で直接
  当該 handoff を撤去している** (`a3168d85`、08:08 JST)。`DW-G03` の独立 2 例が成立するが、
  撤去は file 側だけで checker は直っていないため、次に wave が handoff を land すれば再発する。

## 次の一手差分

### carry

- [T-1005]
- [T-190]

### 新規

- {{T:startup-check-excludes-tracked-handoff}} **P2・ユーザー裁定待ち (R4)**:
  `tools/check_wave_startup.py` の `_check_worktree_handoff` が tracked file を除外せず、
  main に landed した handoff があると背景 job の wave がすべて起動時 rc=1 になる。
  checker 側で tracked file を除外する案を親推奨とする。
